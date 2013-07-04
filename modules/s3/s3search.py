# -*- coding: utf-8 -*-

""" RESTful Search Methods

    @copyright: 2009-2013 (c) Sahana Software Foundation
    @license: MIT

    @requires: U{B{I{gluon}} <http://web2py.com>}

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

import datetime
import re
import string

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.html import BUTTON
from gluon.serializers import json as jsons
from gluon.sqlhtml import MultipleOptionsWidget
from gluon.storage import Storage

from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3crud import S3CRUD
from s3navigation import s3_search_tabs
from s3resource import S3FieldSelector
from s3utils import s3_get_foreign_key, s3_unicode, S3DateTime
from s3validators import *
from s3widgets import S3DateTimeWidget, S3MultiSelectWidget, S3OrganisationHierarchyWidget, s3_grouped_checkboxes_widget

# =============================================================================
class S3SearchWidget(object):
    """
        Search Widget for interactive search (base class)
    """

    def __init__(self, field=None, name=None, **attr):
        """
            Configures the search option

            @param field: name(s) of the fields to search in
            @param name: ?

            @keyword label: a label for the search widget
            @keyword comment: a comment for the search widget
        """
        self.other = None
        self.field = field

        if not self.field:
            raise SyntaxError("No search field specified.")

        self.attr = Storage(attr)
        if name is not None:
            self.attr["_name"] = name

        self.master_query = None
        self.search_field = None

    # -------------------------------------------------------------------------
    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        self.attr = Storage(attr)

        raise NotImplementedError

    # -------------------------------------------------------------------------
    @staticmethod
    def query(resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def build_master_query(self, resource):
        """
            Get the master query for the specified field(s)
        """

        db = current.db
        table = resource.table
        components = resource.components
        accessible_query = resource.accessible_query

        master_query = Storage()
        search_field = Storage()

        fields = self.field
        if fields and not isinstance(fields, (list, tuple)):
            fields = [fields]

        # Find the tables, joins and fields to search in
        for f in fields:
            ktable = None
            rtable = None
            component = None
            reference = None
            multiple = False

            if f.find(".") != -1: # Component
                cname, f = f.split(".", 1)
                if cname not in components:
                    continue
                else:
                    component = components[cname]
                ktable = component.table
                ktablename = component.tablename
                pkey = component.pkey
                fkey = component.fkey
                # Do not add queries for empty tables
                if not db(ktable.id > 0).select(ktable.id,
                                                limitby=(0, 1)).first():
                    continue
            else: # this resource
                ktable = table
                ktablename = table._tablename

            if f.find("$") != -1: # Referenced object
                rkey, f = f.split("$", 1)
                if not rkey in ktable.fields:
                    continue
                rtable = ktable
                rtablename = ktablename
                ktablename, key, multiple = s3_get_foreign_key(ktable[rkey])
                if not ktablename:
                    continue
                else:
                    ktable = db[ktablename]
                # Do not add queries for empty tables
                if not db(ktable.id > 0).select(ktable.id,
                                                limitby=(0, 1)).first():
                    continue

            # Master queries
            # @todo: update this for new QueryBuilder (S3ResourceFilter)
            if ktable and ktablename not in master_query:
                query = (accessible_query("read", ktable))
                if "deleted" in ktable.fields:
                    query = (query & (ktable.deleted == "False"))
                join = None
                if reference:
                    if ktablename != rtablename:
                        q = (accessible_query("read", rtable))
                        if "deleted" in rtable.fields:
                            q = (q & (rtable.deleted == "False"))
                    else:
                        q = None
                    if multiple:
                        j = (rtable[rkey].contains(ktable.id))
                    else:
                        j = (rtable[rkey] == ktable.id)
                    if q is not None:
                        join = q & j
                    else:
                        join = j
                j = None
                if component:
                    if reference:
                        q = (accessible_query("read", table))
                        if "deleted" in table.fields:
                            q = (q & (table.deleted == "False"))
                        j = (q & (table[pkey] == rtable[fkey]))
                    else:
                        j = (table[pkey] == ktable[fkey])
                if j is not None and join is not None:
                    join = (join & j)
                elif j:
                    join = j
                if join is not None:
                    query = (query & join)
                master_query[ktable._tablename] = query

            # Search fields
            if ktable and f in ktable.fields:
                if ktable._tablename not in search_field:
                    search_field[ktablename] = [ktable[f]]
                else:
                    search_field[ktablename].append(ktable[f])

        self.master_query = master_query
        self.search_field = search_field

# =============================================================================
class S3SearchSimpleWidget(S3SearchWidget):
    """
        Simple full-text search widget
    """

    def widget(self,
               resource,
               vars=None,
               name=None,
               value=None,
               autocomplete=None):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        attr = self.attr
        # SearchAutocomplete must set name depending on the field
        if name:
            attr.update(_name=name)

        if "_size" not in attr:
            attr.update(_size="40")
        if "_name" not in attr:
            attr.update(_name="%s_search_simple" % resource.name)
        if "_id" not in attr:
            attr.update(_id="%s_search_simple" % resource.name)
        if autocomplete:
            attr.update(_autocomplete=autocomplete)
        attr.update(_type="text")

        self.name = attr._name

        # Search Autocomplete - Display current value
        attr["_value"] = vars.get(self.name, value) if vars else value

        return INPUT(**attr)

    # -------------------------------------------------------------------------
    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """

        # Build the query
        if value and isinstance(value, str):
            values = value.split()

            final_query = None

            # Create a set of queries for each value
            for value in values:
                field_queries = None

                # Create a set of queries that test the current
                # value against each field
                for field in self.field:
                    s = S3FieldSelector(field).lower()
                    field_query = s.like("%%%s%%" % value.lower())

                    # We want a match against any field
                    if field_queries:
                        field_queries = field_query | field_queries
                    else:
                        field_queries = field_query

                # We want all values to be matched
                if final_query:
                    final_query = field_queries & final_query
                else:
                    final_query = field_queries

            return final_query
        else:
            return None


# =============================================================================
class S3SearchMinMaxWidget(S3SearchWidget):
    """
        Min/Max search widget for numeric fields
    """

    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
       	"""

        T = current.T
        settings = current.deployment_settings

        self.names = []
        attr = self.attr
        self.method = attr.get("method", "range")
        select_min = self.method in ("min", "range")
        select_max = self.method in ("max", "range")

        self.widmin = Storage()
        self.widmax = Storage()

        if not self.search_field:
            self.build_master_query(resource)

        search_field = self.search_field.values()
        if not search_field:
            return SPAN(T("no options available"),
                        _class="no-options-available")

        search_field = search_field[0][0]

        ftype = str(search_field.type)
        input_min = input_max = None
        if ftype == "integer":
            attr.update(_type="text")
            requires = IS_EMPTY_OR(IS_INT_IN_RANGE())
        elif ftype == "date":
            attr.update(_type="date")
            attr.update(_class="date")
            requires = IS_EMPTY_OR(IS_DATE(format=settings.get_L10n_date_format()))
        elif ftype == "time":
            attr.update(_type="time")
            attr.update(_class="time")
            requires = IS_EMPTY_OR(IS_TIME())
        elif ftype == "datetime":
            attr.update(_type="text")
            attr.update(_class="anytime")
            requires = IS_EMPTY_OR(IS_DATETIME(format=settings.get_L10n_datetime_format()))
            calendar_widget = S3DateTimeWidget()
            calendar_widget.inject_script("id-" + self.attr["_name"] + "_min", None)
            calendar_widget.inject_script("id-" + self.attr["_name"] + "_max", None)
	    
        else:
            raise SyntaxError("Unsupported search field type")

        trl = TR(_class="sublabels")
        tri = TR()

        # dictionaries for storing details of the input elements
        name = attr["_name"]

        
        fname = "%s_min" % attr["_name"]
        
        if fname in vars:
            min_value = vars[fname]
        else:
            min_value = ""
        
        fname = "%s_max" % attr["_name"]
        
        if fname in vars:
            max_value = vars[fname]
        else:
            max_value = ""

        attr.update(_value = min_value)

        self.widmin = dict(name="%s_min" % name,
                           label=T("Min"),
                           requires=requires,
                           attributes=attr)

        if select_min:
            min_label = self.widget_label(self.widmin)
            min_input = self.widget_input(self.widmin)

            self.names.append(self.widmin["name"])
            trl.append(min_label)
            tri.append(min_input)
        
        attr.update(_value=max_value)

        self.widmax = dict(name="%s_max" % name,
                           label=T("Max"),
                           requires=requires,
                           attributes=attr)

        if select_max:
            max_label = self.widget_label(self.widmax)
            max_input = self.widget_input(self.widmax)

            self.names.append(self.widmax["name"])
            trl.append(max_label)
            tri.append(max_input)

        w = TABLE(trl, tri, _class="s3searchminmaxwidget")

        return w

    # -------------------------------------------------------------------------
    @staticmethod
    def widget_label(widget):
        """
            @param widget: dict with the name, label, requires and
                            attributes for the input element
            @return: LABEL
        """
        return LABEL(widget["label"], _for="id-%s" % widget["name"])

    # -------------------------------------------------------------------------
    @staticmethod
    def widget_input(widget):
        """
            @param widget: dict with the name, label, requires and
                            attributes for the input element
            @return: INPUT
        """
        attr = widget["attributes"].copy()
        attr.update(_name=widget["name"],
                    _id="id-%s" % widget["name"])
        return INPUT(requires=widget["requires"], **attr)

    # -------------------------------------------------------------------------
    def validate(self, resource, value):
        """
            Validate the input values of the widget
        """
        T = current.T
        errors = dict()

        select_min = self.method in ("min", "range")
        select_max = self.method in ("max", "range")

        if select_min and select_max:
            vmin = value.get(self.widmin["name"], None)
            vmax = value.get(self.widmax["name"], None)

            if vmax is not None and vmin is not None and vmin > vmax:
                errors[self.widmax["name"]] = \
                     T("Maximum must be greater than minimum")

        return errors or None

    # -------------------------------------------------------------------------
    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """
        select_min = self.method in ("min", "range")
        select_max = self.method in ("max", "range")

        min_query = max_query = query = None

        if select_min:
            v = value.get(self.widmin["name"], None)
            if v is not None and str(v):
                min_query = S3FieldSelector(self.field) >= v

        if select_max:
            v = value.get(self.widmax["name"], None)
            if v is not None and str(v):
                max_query = S3FieldSelector(self.field) <= v

        if min_query is not None:
            query = min_query

            if max_query is not None:
                query = query & max_query
        else:
            query = max_query

        return query

# =============================================================================
class S3SearchOptionsWidget(S3SearchWidget):
    """
        Option select widget for option or boolean fields

        Displays a search widget which allows the user to search for records
        with fields matching a certain criteria.

        Field must be an integer or reference to work on all versions of
        gluon/sqlhtml.py

        @param represent: If the field is a reference, represent can pass a
                          formatting string with mapping fields to the
                          referenced record.
        @param cols: The number of columns which the options will be
                     displayed in
    """

    def __init__(self, field=None, name=None, options=None, null=False, **attr):
        """
            Configures the search option

            @param field: name(s) of the fields to search in
            @param name: used to build the HTML ID of the widget
            @param options: either a value:label dictionary to populate the
                            search widget or a callable to create this
            @param null: False if no null value to be included in the options,
                         otherwise a LazyT for the label

            @keyword label: a label for the search widget
            @keyword location_level: If-specified then generate a label when
                                     rendered based on the current hierarchy
            @keyword comment: a comment for the search widget
        """

        super(S3SearchOptionsWidget, self).__init__(field, name, **attr)
        self.options = options
        self.null = null

    # -------------------------------------------------------------------------
    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        T = current.T

        field_name = self.field

        attr = self.attr
        name = attr.pop("_name",
                        "%s_search_select_%s" % (resource.name,
                                                 field_name))
        self.name = name

        if "location_level" in attr:
            # This is searching a Location Hierarchy, so lookup the label now
            level = attr["location_level"]
            hierarchy = current.gis.get_location_hierarchy()
            if level in hierarchy:
                label = hierarchy[level]
            else:
                label = level
            attr["label"] = label

        # Populate the field value from the GET parameter
        if vars and name in vars:
            value = vars[name]
        else:
            value = None

        fs = S3FieldSelector(field_name)
        fl = fs.resolve(resource)
        field = fl.field

        # Check the field type
        if field is not None:
            field_type = str(field.type)
        else:
            field_type = "virtual"

        if self.options is not None:
            # Custom dict of options {value: label} or callable
            if isinstance(self.options, dict):
                options = self.options
            elif callable(self.options):
                options = self.options()

            opt_values = options.keys()
        else:
            options = None
            if field_type == "boolean":
                opt_values = (True, False)
            else:
                multiple = field_type[:5] == "list:"
                groupby = field if field and not multiple else None
                virtual = field is None
                rows = resource.fast_select([field_name],
                                            limit=None,
                                            orderby=field,
                                            groupby=groupby,
                                            virtual=virtual,
                                            as_rows=True)
                opt_values = []
                if rows:
                    colname = fl.colname
                    opt_extend = opt_values.extend
                    opt_append = opt_values.append
                    if multiple:
                        for row in rows:
                            values = row[colname]
                            if values:
                                opt_extend([v for v in values
                                            if v not in opt_values])
                    else:
                        for row in rows:
                            v = row[colname]
                            if v not in opt_values:
                                opt_append(v)

        # Translate empty-option
        EMPTY = T("Unspecified")

        # Append empty-option if field can be empty
        #if field:
            #requires = field.requires
            #if not isinstance(requires, (tuple, list)):
                #requires = [requires]
        #else:
            #requires = [None]
        #if None not in opt_values and "" not in opt_values and \
           #isinstance(requires[0], IS_EMPTY_OR):
            #opt_values.append(None)
            #if options is not None and None not in options:
                #options[None] = EMPTY

        if len(opt_values) < 1 or \
           len(opt_values) == 1 and not opt_values[0]:
            msg = attr.get("_no_opts", T("No options available"))
            return SPAN(msg, _class="no-options-available")

        if self.options is None:
            opt_list = []

            # Always use the represent of the widget, if present
            represent = attr.represent

            # Fallback to the field's represent
            if not represent or field_type[:9] != "reference":
                represent = field.represent

            if callable(represent):
                if hasattr(represent, "bulk"):
                    # S3Represent => use bulk option
                    opt_dict = represent.bulk(opt_values,
                                              list_type=False,
                                              show_link=False)
                    if None in opt_values:
                        opt_dict[None] = EMPTY
                    elif None in opt_dict:
                        del opt_dict[None]
                    if "" in opt_values:
                        opt_dict[""] = EMPTY
                    opt_list = opt_dict.items()
                else:
                    # Standard represent function
                    args = {"show_link": False} \
                           if "show_link" in represent.func_code.co_varnames else {}
                    if multiple:
                        repr_opt = lambda opt: opt in (None, "") and (opt, EMPTY) or \
                                               (opt, represent([opt], **args))
                    else:
                        repr_opt = lambda opt: opt in (None, "") and (opt, EMPTY) or \
                                               (opt, represent(opt, **args))
                    opt_list = map(repr_opt, opt_values)

            elif isinstance(represent, str) and field_type[:9] == "reference":
                # Feed the format string
                # Use the represent string to reduce db calls
                # Find the fields which are needed to represent:
                db = current.db
                ktable = db[field_type[10:]]
                fieldnames = ["id"]
                fieldnames += re.findall("%\(([a-zA-Z0-9_]*)\)s", represent)
                represent_fields = [ktable[fieldname] for fieldname in fieldnames]
                query = (ktable.id.belongs([k for k in opt_values if str(k).isdigit()])) & \
                        (ktable.deleted == False)
                represent_rows = db(query).select(*represent_fields).as_dict(key=represent_fields[0].name)
                opt_list = []
                ol_append = opt_list.append
                for opt_value in opt_values:
                    if opt_value not in represent_rows:
                        continue
                    else:
                        opt_represent = represent % represent_rows[opt_value]
                    if opt_represent:
                        ol_append([opt_value, opt_represent])
            else:
                # Straight string representations of the values
                opt_list = [(opt_value, s3_unicode(opt_value))
                            for opt_value in opt_values if opt_value]

            options = OrderedDict([("__NONE__" if o is None else o, v)
                                   for o, v in opt_list])
        else:
            options = OrderedDict([("__NONE__" if o is None else o, v)
                                   for o, v in options.items()])

        # Dummy field
        dummy_field = Storage(name=name,
                              type=field_type,
                              requires=IS_IN_SET(options,
                                                 multiple=True))

        # For many-to-many fields the user can search for records containing
        # all the options or any of the options.
        self.filter_type = vars.get("%s_filter" % name, "any")
        if len(options) > 1 and field_type[:4] == "list":
            any_all = DIV(
                T("Filter type "),
                INPUT(_name="%s_filter" % name,
                      _id="%s_filter_any" % name,
                      _type="radio",
                      _value="any",
                      value=self.filter_type),
                LABEL(T("Any"),
                      _for="%s_filter_any" % name),
                INPUT(_name="%s_filter" % name,
                      _id="%s_filter_all" % name,
                      _type="radio",
                      _value="all",
                      value=self.filter_type),
                LABEL(T("All"),
                      _for="%s_filter_all" % name),

                _class="s3-checkboxes-widget-filter"
            )
        else:
            any_all = ""

        return TAG[""](any_all,
                       s3_grouped_checkboxes_widget(dummy_field,
                                                    value,
                                                    **attr))

    # -------------------------------------------------------------------------
    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """

        field_name = self.field

        if value:
            if not isinstance(value, (list, tuple)):
                value = [value]

            fs = S3FieldSelector(field_name)
            rfield = fs.resolve(resource)
            try:
                table_field = rfield.field
            except:
                table_field = None

            query = None
            if "__NONE__" in value:
                if rfield.ftype in ("string", "text", "virtual") and \
                   "" not in value:
                    value.append("")
                query = (fs == None)
                value = [v for v in value if v not in ("__NONE__", None)]

            if table_field and rfield.ftype.startswith("list"):
                if query is not None:
                    query |= (fs == [])
                if value:
                    if self.filter_type == "any":
                        q = fs.anyof(value)
                    else:
                        q = fs.contains(value)
                else:
                    q = None
            else:
                q = fs.belongs(value)
            if q is not None:
                if query is not None:
                    query |= q
                else:
                    query = q
            return query
        else:
            return None

# =============================================================================
class S3SearchLocationWidget(S3SearchWidget):
    """
        Interactive location search widget
        - allows the user to select a BBOX & have only results from within
          that BBOX returned

        @ToDo: Get this working within a Report (no map currently available there)
        @ToDo: Have an option to use a Circular Radius
               http://openlayers.org/dev/examples/regular-polygons.html
        @ToDo: Have an option to use a full Polygon
               Hard to process this as a resource filter
    """

    def __init__(self,
                 field="location_id",
                 name=None, # Needs to be specified by caller
                 **attr):
        """
            Initialise parent class & make any necessary modifications
        """

        S3SearchWidget.__init__(self, field, name, **attr)

    # -------------------------------------------------------------------------
    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        format = current.auth.permission.format
        if format == "plain":
            return None

        try:
            from shapely.wkt import loads as wkt_loads
        except ImportError:
            from s3utils import s3_debug
            s3_debug("WARNING: %s: Shapely GIS library not installed" % __name__)
            return None

        T = current.T

        # Components

        if "comment" not in self.attr:
            self.attr.update(comment=T("Draw a square to limit the results to just those within the square."))
            #self.attr.update(comment="%s|%s|%s" % (T("Draw a Polygon around the area to which you wish to restrict your search."),
            #                                       T("Click on the map to add the points that make up your polygon. Double-click to finish drawing."),
            #                                       T("To activate Freehand mode, hold down the shift key.")))
        self.comment = self.attr.comment

        # Hidden Field to store the Polygon value in
        polygon_input = INPUT(_id="gis_search_polygon_input",
                              _name=self.attr._name,
                              _class="hide")

        # Map Popup
        # - not added as we reuse the one that comes with dataTables

        # Button to open the Map
        OPEN_MAP = T("Open Map")
        CLEAR_MAP = T("Clear selection")
        map_buttons = TAG[""](BUTTON(OPEN_MAP,
                                     _id="gis_search_map-btn",
                                     # If we need to support multiple maps
                                     #_map="default",
                                     ),
                              BUTTON(CLEAR_MAP,
                                     _id="gis_search_polygon_input_clear"))

        # The overall layout of the components
        return TAG[""](polygon_input,
                       map_buttons,
                       )

    # -------------------------------------------------------------------------
    @staticmethod
    def query(resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget: WKT format
        """

        if value:
            # @ToDo:
            # if current.deployment_settings.get_gis_spatialdb():
            #     # Use PostGIS-optimised routine
            #     query = (S3FieldSelector("location_id$the_geom").st_intersects(value))
            # else:
            from shapely.wkt import loads as wkt_loads
            try:
                shape = wkt_loads(value)
            except:
                from s3utils import s3_debug
                s3_debug("WARNING: S3Search: Invalid WKT")
                return None

            bounds = shape.bounds
            lon_min = bounds[0]
            lat_min = bounds[1]
            lon_max = bounds[2]
            lat_max = bounds[3]

            # Return all locations which have a part of themselves inside the BBOX
            # This requires the locations to have their bounds set properly
            # This can be done globally using:
            # gis.update_location_tree()
            query = (S3FieldSelector("location_id$lat_min") <= lat_max) & \
                    (S3FieldSelector("location_id$lat_max") >= lat_min) & \
                    (S3FieldSelector("location_id$lon_min") <= lon_max) & \
                    (S3FieldSelector("location_id$lon_max") >= lon_min)
            return query
        else:
            return None

# =============================================================================
class S3SearchCredentialsWidget(S3SearchOptionsWidget):
    """
        Options Widget to search for HRMs with specified Credentials
    """

    def widget(self, resource, vars):
        c = current.s3db.resource("hrm_credential")
        return S3SearchOptionsWidget.widget(self, c, vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def query(resource, value):
        if value:
            s3db = current.s3db
            htable = s3db.hrm_human_resource
            ptable = s3db.pr_person
            ctable = s3db.hrm_credential
            query = (htable.person_id == ptable.id) & \
                    (htable.deleted != True) & \
                    (ctable.person_id == ptable.id) & \
                    (ctable.deleted != True) & \
                    (ctable.job_title_id.belongs(value))
            return query
        else:
            return None

# =============================================================================
class S3SearchSkillsWidget(S3SearchOptionsWidget):
    """
        Options Widget to search for HRMs with specified Skills

        @ToDo: Provide a filter for confirmed/unconfirmed only
               (latter useful to see who needs confirming)

        @ToDo: Provide a filter for level of competency
               - meanwhile at least sort by level of competency
    """

    # -------------------------------------------------------------------------
    def widget(self, resource, vars):
        c = current.s3db.resource("hrm_competency")
        return S3SearchOptionsWidget.widget(self, c, vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def query(resource, value):
        if value:
            s3db = current.s3db
            htable = s3db.hrm_human_resource
            ptable = s3db.pr_person
            ctable = s3db.hrm_competency
            query = (htable.person_id == ptable.id) & \
                    (htable.deleted != True) & \
                    (ctable.person_id == ptable.id) & \
                    (ctable.deleted != True) & \
                    (ctable.skill_id.belongs(value))
            return query
        else:
            return None

# =============================================================================
class S3Search(S3CRUD):
    """
        RESTful Search Method for S3Resources
        
        See also: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Search
    """

    def __init__(self, simple=None, advanced=None, any=False, **args):
        """
            Constructor

            @param simple: the widgets for the simple search form as list
            @param advanced: the widgets for the advanced search form as list
            @param any: match "any of" (True) or "all of" (False) the options
                        in advanced search
        """

        S3CRUD.__init__(self)

        args = Storage(args)
        if simple is None:
            if "field" in args:
                if "name" in args:
                    name = args.name
                elif "_name" in args:
                    name = args._name
                else:
                    name = "search_simple"
                simple = S3SearchSimpleWidget(field=args.field,
                                              name=name,
                                              label=args.label,
                                              comment=args.comment)

        # Create a list of Simple search form widgets, by name,
        # and throw an error if a duplicate is found
        names = []
        self.simple = []
        if not isinstance(simple, (list, tuple)):
            simple = [simple]
        for widget in simple:
            if widget is not None:
                name = widget.attr._name
                if name in names:
                    raise SyntaxError("Duplicate widget: %s" % name)
                # Widgets should be able to have default names
                # elif not name:
                #     raise SyntaxError("Widget with no name")
                else:
                    self.simple.append((name, widget))
                    names.append(name)

        # Create a list of Advanced search form widgets, by name,
        # and throw an error if a duplicate is found
        names = []
        self.advanced = []
        if advanced:
            append = self.advanced.append
            if not isinstance(advanced, (list, tuple)):
                advanced = [advanced]
            for widget in advanced:
                if widget is not None:
                    name = widget.attr._name
                    if name in names:
                        raise SyntaxError("Duplicate widget: %s" % name)
                    # Widgets should be able to have default names
                    # elif not name:
                    #    raise SyntaxError("Widget with no name")
                    else:
                        append((name, widget))
                        names.append(name)

        self.__any = any

        if self.simple or self.advanced:
            self.__interactive = True
        else:
            self.__interactive = False

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point to apply search method to S3Requests

            @param r: the S3Request
            @param attr: request attributes
        """

        format = r.representation
        output = dict()

        if r.component:
            search_method = self.resource.search_method()
            if self != search_method:
                output = search_method(r, **attr)

        # Interactive or saved search
        elif r.interactive and self.__interactive:
            output = self.search_interactive(r, **attr)

        # SSPag response => CRUD native
        elif format == "aadata" and self.__interactive:
            output = self.select(r, **attr)

        # Search form for popup on Map Layers
        elif format == "plain":
            output = self.search_interactive(r, **attr)

        elif format == "email":
            output = self.email(r, **attr)

        # Not supported
        else:
            r.error(501, current.manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def _build_widget_query(resource, name, widget, form, dq=None, vq=None):
        """
            @todo: docstring
        """

        errors = None
        if hasattr(widget, "names"):
            value = Storage([(name, form.vars[name])
                             for name in widget.names if name in form.vars])
        elif name in form.vars:
            value = form.vars[name]
        else:
            value = None
        if hasattr(widget, "validate"):
            errors = widget.validate(resource, value)

        if not errors:
            q = widget.query(resource, value)

            if q:
                if q.query(resource) is not None:
                    if dq is None:
                        dq = q
                    else:
                        dq &= q
                else:
                    if vq is None:
                        vq = q
                    else:
                        vq &= q

        return (dq, vq, errors)

    # -------------------------------------------------------------------------
    def save_search_widget(self, r, query, **attr):
        """
            Add a widget to a Search form to allow saving this search to the
            user's profile, to which they can subscribe
        """

        import urllib

        T = current.T

        person_id = current.auth.s3_logged_in_person()
        resource = self.resource

        if hasattr(query, "serialize_url"):
            vars = query.serialize_url(resource)
        else:
            vars = None

        save_options = {
            "url": URL(c="pr", f="saved_search", vars={"format": "s3json"}),
            "url_detail": URL(c="default", f="person", args=[person_id, "saved_search", "<id>", "update"]),
            "data": json.dumps({
                "$_pr_saved_search": [
                    {
                        "name": "TEMP",
                        "controller": r.controller,
                        "function": r.function,
                        "prefix": resource.prefix,
                        "resource_name": resource.name,
                        "url": r.url(
                            # Can't use the search method handler because then
                            # we can't get different formats
                            method = "search", # want to see search form
                            vars = vars,
                        ),
                        "filters": urllib.urlencode(vars) if vars else None,
                    },
                ],
            }),
        }

        widget = TAG[""](BUTTON(T("Save this search"),
                                _id="save-search",
                                _class="save-search-button"
                                ),
                         SCRIPT('''
S3.search.saveOptions=%s
i18n.edit_saved_search="%s"
''' % (json.dumps(save_options),
       T("Edit saved search"))))

        return widget

    # -------------------------------------------------------------------------
    def email(self, r, **kwargs):
        """
            Take a search request and render it through a template
            to format it for email notifications.

            @param r: S3Request object
        """

        represent = current.manager.represent

        # Saved search is optional, but used to filter results and
        # put save search name into the output
        search_subscription = current.request.get_vars.get("search_subscription", None)
        if search_subscription:
            search = current.db(current.s3db.pr_saved_search.auth_token == search_subscription).select().first()
        else:
            search = None

        if search:
            controller = search.controller
            function = search.function
            last_checked = search.last_checked

        list_fields = self._config("list_fields")

        # Create a list of the names, not labels, from list_fields
        field_names = []
        for f in list_fields:
            if f != "id":
                if isinstance(f, tuple):
                    field_names.append(f[1]) # (label, name)
                else:
                    field_names.append(f)

        # Get the field objects based on list_fields
        fields = self.resource.readable_fields(field_names)

        # We don't want to show the "id" field at all
        head_row = TR([TH(f.label) for f in fields if f.name != "id"])
        new_rows = []
        nappend = new_rows.append
        mod_rows = []
        mappend = mod_rows.append

        for row in self.resource.load():
            first_cell = True # disabled
            row_cells = []
            rappend = row_cells.append

            for f in fields:
                rep_value = represent(f, record=row)

                # Hyperlink the text in the first
                # cell to the record page
                if first_cell and search:
                    url = URL(c=controller, f=function, args=row["id"],
                              scheme=True)
                    rep_value = A(rep_value, _href=url)
                    first_cell = False

                rappend(TD(XML(rep_value)))

            if row_cells:
                tr = TR(*row_cells)

                if search and row.created_on >= last_checked:
                    # Records are either "new" or "modified"
                    nappend(tr)
                else:
                    mappend(tr)

        if not new_rows and not mod_rows:
            return ""

        # Generate a table for the new records
        if new_rows:
            new_table = TABLE(THEAD(head_row),
                              TBODY(*new_rows))
        else:
            new_table = None

        # Generate a table for updated records
        if mod_rows:
            mod_table = TABLE(THEAD(head_row),
                              TBODY(*mod_rows))
        else:
            mod_table = None

        if search:
            search_name = search.name
        else:
            search_name = ""

        response = current.response
        crud_strings = response.s3.crud_strings[self.resource.tablename]

        if crud_strings:
            resource_name = crud_strings.title_list
        else:
            resource_name = string.capwords(self.resource.name, "_")

        # Render the records via a template
        message = response.render(
            "msg/notification_email.html",
            {
                "search_name": search_name,
                "new_table": new_table,
                "mod_table": mod_table,
                "system_name": current.deployment_settings.get_system_name(),
                "resource_name": resource_name,
            }
        )

        return message

    # -------------------------------------------------------------------------
    def search_interactive(self, r, **attr):
        """
            Interactive search

            @param r: the S3Request instance
            @param attr: request parameters
        """

        T = current.T
        session = current.session
        request = self.request
        response = current.response
        s3 = response.s3
        resource = self.resource
        settings = current.deployment_settings
        db = current.db
        s3db = current.s3db
        table = self.table
        tablename = self.tablename

        representation = r.representation

        # Initialize output
        output = dict()

        # Get table-specific parameters
        config = self._config
        sortby = config("sortby", [[1, "asc"]])
        orderby = config("orderby", None)
        list_fields = config("list_fields")
        insertable = config("insertable", True)

        # Initialize the form
        form = DIV(_class="search_form form-container")

        # Figure out which set of form values to use
        # POST > GET > session > unfiltered
        if r.http == "POST":
            # POST
            form_values = r.post_vars
        else:
            url_options = Storage([(k, v)
                                   for k, v in r.get_vars.iteritems() if v])
            if url_options:
                # GET
                form_values = url_options
            else:
                session_options = session.s3.search_options
                if session_options and tablename in session_options:
                    # session
                    if "clear_opts" in r.get_vars:
                        session_options = Storage()
                    else:
                        session_options = session_options[tablename] or Storage()
                else:
                    # unfiltered
                    session_options = Storage()
                form_values = session_options
            if "clear_opts" in r.get_vars:
                del r.get_vars["clear_opts"]
            if "clear_opts" in r.vars:
                del r.vars["clear_opts"]

        # Remove the existing session filter if this is a new search
        if r.http == "GET" and r.representation != "aadata" and \
           "filter" in session.s3:
            del session.s3["filter"]

        # Build the search forms
        simple_form, advanced_form = self.build_forms(r, form_values)

        # Process the search forms
        dq, vq, errors = self.process_forms(r,
                                            simple_form,
                                            advanced_form,
                                            form_values)
        search_url = None
        search_url_vars = Storage()
        save_search = ""
        if not errors:
            if (dq is None or hasattr(dq, "serialize_url")) and \
               (vq is None or hasattr(vq, "serialize_url")):
                query = dq
                if vq is not None:
                    if query is not None:
                        query &= vq
                    else:
                        query = vq
                if query is not None:
                    search_url_vars = query.serialize_url(resource)
                search_url = r.url(method = "", vars = search_url_vars)

                if query and settings.get_search_save_widget():
                    # Create a Save Search widget
                    save_search = self.save_search_widget(r, query, **attr)

            # Add sub-queries
            resource.add_filter(dq)
            resource.add_filter(vq)

            search_vars = dict(simple=False,
                               advanced=True,
                               criteria=form_values)
        else:
            search_vars = dict()

        if representation == "plain":
            # Map popup filter
            # Return just the advanced form, no results
            form.append(advanced_form)
            output["item"] = form
            response.view = self._view(r, "plain.html")
            return output

        # Complete the output form-DIV()
        if simple_form is not None:
            if save_search:
                # Insert the save button next to the submit button
                simple_form[0][-1][1].insert(1, save_search)
            form.append(simple_form)
        if advanced_form is not None:
            if save_search:
                # Insert the save button next to the submit button
                advanced_form[0][-1][1].insert(1, save_search)
            form.append(advanced_form)
        output["form"] = form

        # Store format URLs
        formats = s3.formats
        format_url = r.url(method="", vars=search_url_vars)
        for f in ("pdf", "xls", "rss", "xml"):
            formats[f] = format_url
        for f in table.fields:
            if f in ["location_id", "site_id"]:
                formats["kml"] = format_url
                break

        # List fields
        if not list_fields:
            fields = resource.readable_fields()
            list_fields = [f.name for f in fields]
        else:
            fields = [table[f] for f in list_fields if f in table.fields]
        if not fields:
            fields = []
        if fields[0].name != table.fields[0]:
            fields.insert(0, table[table.fields[0]])
        if list_fields[0] != table.fields[0]:
            list_fields.insert(0, table.fields[0])

        # How many records per page?
        if s3.dataTable_iDisplayLength:
            display_length = s3.dataTable_iDisplayLength
        else:
            display_length = attr.get("dt_displayLength", 25)
        # Server-side pagination?
        if not s3.no_sspag:
            dt_pagination = "true"
            limit = 2 * display_length
            if orderby is None:
                dt_sorting = {
                    "iSortingCols": "1",
                    "sSortDir_0": "asc"
                }

                if len(list_fields) > 1:
                    dt_sorting["bSortable_0"] = "false"
                    dt_sorting["iSortCol_0"] = "1"
                else:
                    dt_sorting["bSortable_0"] = "true"
                    dt_sorting["iSortCol_0"] = "0"

                q, orderby, left = resource.datatable_filter(list_fields, dt_sorting)
	    else:
                left = None
        else:
            dt_pagination = "false"
            limit = None
            left = None

        # Truncate long texts
        if r.interactive or representation == "aadata":
            for f in table:
                if str(f.type) == "text" and not f.represent:
                    f.represent = self.truncate

        # Get the results
        if not orderby:
            orderby = fields[0]
        dt, totalrows, ids = resource.datatable(fields=list_fields,
                                                start=None,
                                                limit=limit,
                                                orderby=orderby,
                                                getids=True,
                                                left=left)
        displayrows = totalrows

        # Remove the dataTables search box to avoid confusion
        dt_bFilter = False

        # Render the datatable and add it to the output
        if not s3.no_sspag and ids:
            # Session filter for datatable's Ajax-requests
            ids = ",".join([str(i) for i in ids])
            session.s3.filter = {"%s.id" % resource.name: ids}
        if dt is None:
            # No results
            datatable = self.crud_string(tablename, "msg_no_match")
            s3.no_formats = True
        else:
            # Data table
            dt_config = {}
            dt_sDom = s3.get("dataTable_sDom")
            if dt_sDom:
                dt_config["dt_sDom"] = dt_sDom
            dt_length_menu = attr.get("dt_lengthMenu")
            if dt_length_menu:
                dt_config["dt_lengthMenu"] = dt_length_menu
            datatable = dt.html(totalrows, displayrows, "datatable",
                                dt_pagination=dt_pagination,
                                dt_displayLength=display_length,
                                dt_permalink=search_url,
                                dt_bFilter = dt_bFilter,
                                **dt_config)
        output["items"] = datatable
        output["sortby"] = sortby

        # Construct list|map|msg tabs as appropriate
        tabs = []
        try :
            if query is None:
                # Do nothing
                query = None
        except :
            dt = None

        if dt is not None:
            filter = session.s3.filter
            app = request.application

            if "location_id" in table or "site_id" in table:
                # Add a map-tab for search results
                # (this same map is also used by the Map Search Widget, if-present)

                tabs.append((T("Map"), "map"))
                app = request.application

                # Build URL to load the features onto the map
                if query:
                    vars = search_url_vars #query.serialize_url(resource=resource)
                else:
                    vars = None
                url = URL(extension="geojson", args=None, vars=vars)
                gis = current.gis
                marker_fn = s3db.get_config(tablename, "marker_fn")
                if marker_fn:
                    # Per-feature markers added in get_location_data()
                    marker = None
                else:
                    # Single Marker for the layer
                    request = self.request
                    marker = gis.get_marker(request.controller,
                                            request.function)

                feature_resources = [{
                        "name"      : T("Search Results"),
                        "id"        : "search_results",
                        "tablename" : tablename,
                        "url"       : url,
                        "active"    : False, # Gets activated when the Map is opened up
                        "marker"    : marker
                    }]
                map_popup = gis.show_map(feature_resources=feature_resources,
                                         # Added by search widget onClick in s3.dataTables.js
                                         #add_polygon = True,
                                         #add_polygon_active = True,
                                         catalogue_layers=True,
                                         legend=True,
                                         toolbar=True,
                                         collapsed=True,
                                         #search = True,
                                         window=True,
                                         window_hide=True
                                         )
                # To be read in views/dataTables.html
                s3.dataTableMap = map_popup

            if settings.has_module("msg") and \
               ("pe_id" in table or "person_id" in table) and \
               current.auth.permission.has_permission("update", c="msg"):
                # Add a msg-tab to provide the ability to send messages to
                # all person entities in the search result
                tabs.append((T("Message"), "compose"))

            if tabs:
                # If we have tabs, then "List" becomes the first one
                tabs.insert(0, ((T("List"), None)))

        output["search_tabs"] = s3_search_tabs(r, tabs)

        # Title and subtitle
        output["title"] = self.crud_string(tablename, "title_search")
        output["subtitle"] = self.crud_string(tablename, "msg_match")

        # Store search options in session (do this only here after the
        # search has successfully returned a result - prevent re-run of
        # unsuccessful options whenever the user opens the search page)
        if "search_options" not in session.s3:
            session.s3.search_options = Storage()
        session.s3.search_options[tablename] = s3.search_options[tablename]

        # View
        response.view = self._view(r, "search.html")
        return output

    # -------------------------------------------------------------------------
    def process_forms(self, r, simple_form, advanced_form, form_values):
        """
            Validate the form values against the forms. If valid, generate
            and return a query object. Otherwise return an empty query and
            the errors.

        """

        s3 = current.response.s3

        dq, vq = None, None
        errors = None

        # Create a container in the session to saves search options
        if "search_options" not in s3:
            s3.search_options = Storage()

        # Process the simple search form:
        simple = simple_form is not None
        if simple_form is not None:
            if simple_form.accepts(form_values,
                                   formname="search_simple"):
                for name, widget in self.simple:
                    dq, vq, errors = self._build_widget_query(self.resource,
                                                              name,
                                                              widget,
                                                              simple_form,
                                                              dq, vq)
                    if errors:
                        simple_form.errors.update(errors)
                errors = simple_form.errors

                # Remember the form values
                s3.search_options[self.tablename] = \
                    Storage([(k, v) for k, v in form_values.iteritems() if v])
            elif simple_form.errors:
                errors = simple_form.errors
                return dq, vq, errors

        # Process the advanced search form:
        if advanced_form is not None:
            if advanced_form.accepts(form_values,
                                     formname="search_advanced"):
                simple = False
                resource = self.resource
                for name, widget in self.advanced:
                    dq, vq, errors = self._build_widget_query(resource,
                                                              name,
                                                              widget,
                                                              advanced_form,
                                                              dq, vq)
                    if errors:
                        advanced_form.errors.update(errors)

                errors = advanced_form.errors

                # Remember the form values
                s3.search_options[self.tablename] = \
                    Storage([(k, v) for k, v in form_values.iteritems() if v])
            elif advanced_form.errors:
                simple = False

        s3.simple_search = simple
        return dq, vq, errors

    # -------------------------------------------------------------------------
    def build_forms(self, r, form_values=None):
        """
            Builds a form customised to the module/resource.
        """

        simple = self.simple
        advanced = self.advanced

        T = current.T
        tablename = self.tablename
        representation = r.representation

        simple_form = None
        advanced_form = None

        opts = Storage(r.get_vars)
        opts["clear_opts"] = "1"
        clear_opts = A(T("Clear"), _href=r.url(vars=opts), _class="action-lnk")

        # Simple search form
        if simple:
            attr = {}
            if advanced:
                switch_link = A(T("Advanced Search"), _href="#",
                                _class="action-lnk advanced-lnk")
                # Hide if the advanced form has been submitted
                if r.http == "POST" and \
                   r.post_vars.get("advanced_submit", False):
                    attr["_style"] = "display:none;"
            else:
                switch_link = ""
            simple_form = self._build_form(simple,
                                           form_values=form_values,
                                           clear=clear_opts,
                                           switch=switch_link,
                                           submit="simple_submit",
                                           _class="simple-form",
                                           **attr)

        # Advanced search form
        if advanced:
            attr = {}
            if simple and not r.representation == "plain":
                switch_link = A(T("Basic Search"), _href="#",
                                _class="action-lnk simple-lnk")
                # Hide for initial GET or if simple form has been submitted
                if r.http == "GET" or \
                   r.http == "POST" and \
                   r.post_vars.get("simple_submit", False):
                    attr["_style"] = "display:none;"
            else:
                switch_link = ""
            advanced_form = self._build_form(advanced,
                                             form_values=form_values,
                                             clear=clear_opts,
                                             switch=switch_link,
                                             submit="advanced_submit",
                                             _class="advanced-form",
                                             **attr)

        return (simple_form, advanced_form)

    # -------------------------------------------------------------------------
    def _build_form(self, widgets,
                    form_values=None,
                    clear="",
                    switch="",
                    submit="search_submit",
                    **attr):
        """
            Render a search form.

            @param widgets: the widgets
            @param form_values: the form values (as dict) to pass to the
                                widgets
            @param clear: the clear-values action link
            @param switch: the switch-forms action link
            @param submit: the HTML name attribute for the submit button
            @param attr: HTML attributes for the form

            @return: a FORM instance
        """

        T = current.T
        request = self.request
        resource = self.resource

        trows = []
        for name, widget in widgets:

            _widget = widget.widget(resource, form_values)
            if _widget is None:
                # Skip this widget as we have nothing but the label
                continue

            label = widget.field
            if isinstance(label, (list, tuple)) and len(label):
                label = label[0]
            comment = ""

            if hasattr(widget, "attr"):
                label = widget.attr.get("label", label)
                comment = widget.attr.get("comment", comment)

            tr = TR(TD("%s: " % label, _class="w2p_fl"), _widget)

            if comment:
                tr.append(DIV(DIV(_class="tooltip",
                                  _title="%s|%s" % (label, comment))))
            trows.append(tr)

        if switch:
            trows.append(TR("", switch))

        submit_class = current.deployment_settings.get_ui_search_submit_button()
        trows.append(
                     TR("",
                        TD(INPUT(_type="submit",
                                 _name=submit,
                                 _value=T("Search"),
                                 _class=submit_class
                                 ),
                           clear
                          )
                        )
                     )

        form = FORM(TABLE(trows), **attr)
        return form

    # -------------------------------------------------------------------------
    @staticmethod
    def _check_search_autcomplete_search_simple_widget(widget):
        """
            @todo: docstring
        """
        if not isinstance(widget, S3SearchSimpleWidget):
            raise SyntaxError("First simple widget for Search AutoComplete must be S3SearchSimpleWidget")

    # -------------------------------------------------------------------------
    def search_autocomplete(self, r, **attr):
        """
            Interactive search

            @param r: the S3Request instance
            @param attr: request parameters
        """

        # Get environment
        T = current.T
        resource = self.resource
        vars = self.request.get_vars

        resource.clear_query()

        # Fieldname of the value for the autocomplete (default to id)
        get_fieldname = attr.get("get_fieldname")
        fieldname = attr.get("fieldname")
        value = attr.get("value")

        # Get representation
        representation = r.representation

        # Initialize output
        feature_queries = []
        bounds = None
        output = dict()
        simple = False

        # Get table-specific parameters
        sortby = self._config("sortby", [[1, "asc"]])
        orderby = self._config("orderby", None)
        list_fields = self._config("list_fields")
        insertable = self._config("insertable", True)

        # Initialize the form
        form_attr = dict(_class="search_form form-container",
                         _prefix=resource.prefix,
                         _resourcename=resource.name,
                         _fieldname=fieldname,
                         )
        if get_fieldname:
            form_attr["_get_fieldname"] = get_fieldname
            # Otherwise default get_fieldname is "id"

        form = DIV(**form_attr)

        # Append the simple search form
        if self.simple:
            simple = True
            if self.advanced:
                switch_link = A(T("Advanced Search"), _href="#",
                                _class="action-lnk advanced-lnk %s",
                                _fieldname=fieldname)
            else:
                switch_link = ""
            # Only display the S3SearchSimpleWidget (should be first)
            name, widget = self.simple[0]

            self._check_search_autcomplete_search_simple_widget(widget)
            name = "%s_search_simple_simple" % fieldname

            autocomplete_widget = widget.widget(resource,
                                                 vars,
                                                 name=name,
                                                 value=value,
                                                 autocomplete="off")

            simple_form = DIV(TABLE(autocomplete_widget,
                                      switch_link
                                     ),
                              _class="simple-form")
            form.append(simple_form)

        # Append the advanced search form
        if self.advanced:
            trows = []
            first_widget = True
            for name, widget in self.advanced:
                _widget = widget.widget(resource, vars)
                if _widget is None:
                    # Skip this widget as we have nothing but the label
                    continue
                label = widget.field
                if first_widget:
                    self._check_search_autcomplete_search_simple_widget(widget)
                    name = "%s_search_simple_advanced" % fieldname
                    autocomplete_widget = widget.widget(resource,
                                                         vars,
                                                         name=name,
                                                         value=value,
                                                         autocomplete="off")
                    first_widget = False
                else:
                    if isinstance(label, (list, tuple)) and len(label):
                        label = label[0]
                    if hasattr(widget, "attr"):
                        label = widget.attr.get("label", label)
                    tr = TR(TD("%s: " % label, _class="w2p_fl"), _widget)
                    trows.append(tr)

            if self.simple:
                switch_link = A(T("Simple Search"), _href="#",
                                _class="action-lnk simple-lnk",
                                _fieldname=fieldname)
            else:
                switch_link = ""

            if simple:
                atrr = {}
            else:
                attr["_style"] = "display:none;"
            advanced_form = DIV(autocomplete_widget,
                                TABLE(trows),
                                TABLE(TR(switch_link)),
                                _class="advanced-form",
                                #_resourcename = resource.name
                                **attr
                                )
            form.append(advanced_form)

        output.update(form=form)
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def save_search(r, **attr):
        """
            Save a Search Filter in the user's profile
            - db.pr_save_search
        """

        search_vars = json.load(r.body)
        s_vars = {}

        for i in search_vars.iterkeys():
            if str(i) == "criteria" :
                s_dict = {}
                c_dict = search_vars[i]
                for j in c_dict.iterkeys():
                    key = str(j)
                    s_dict[key] = str(c_dict[j])
                s_vars[str(i)] = s_dict
            else:
                key = str(i)
                s_vars[key] = str(search_vars[i])

        import cPickle
        search_str = cPickle.dumps(s_vars)
        table = current.s3db.pr_save_search
        query = (table.user_id == current.auth.user_id) & \
                (table.search_vars == search_str)
        if len(current.db(query).select(table.id)) == 0:
            new_search = {}
            new_search["search_vars"] = search_str
            _id = table.insert(**new_search)
        msg = "success"
        return msg

# =============================================================================
class S3SearchOrgHierarchyWidget(S3SearchOptionsWidget):

    def widget(self, resource, vars):
        field_name = self.field

        # check the field type
        try:
            field = resource.table[field_name]
        except:
            field_type = "virtual"
        else:
            field_type = str(field.type)

        return S3OrganisationHierarchyWidget()(field, {}, **self.attr)

# END =========================================================================
