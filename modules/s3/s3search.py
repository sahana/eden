# -*- coding: utf-8 -*-

"""
    RESTful Search Methods

    @author: Fran Boon <fran[at]aidiq.com>
    @author: Dominic König <dominic[at]aidiq.com>
    @author: Pratyush Nigam <pratyush.nigam@gmail.com>

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2011 (c) Sahana Software Foundation
    @license: MIT

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

import re
import gluon.contrib.simplejson as jsonlib
import cPickle

from gluon.storage import Storage
from gluon import *
from gluon.serializers import json

from s3crud import S3CRUD
from s3validators import *
from s3utils import s3_debug
from s3widgets import CheckboxesWidgetS3

__all__ = ["S3SearchWidget",
           "S3SearchSimpleWidget",
           "S3SearchMinMaxWidget",
           "S3SearchOptionsWidget",
           "S3SearchLocationHierarchyWidget",
           "S3SearchLocationWidget",
           "S3SearchSkillsWidget",
           "S3Search",
           "S3LocationSearch",
           "S3OrganisationSearch",
           "S3PersonSearch",
           "S3PentitySearch"]

MAX_RESULTS = 1000
MAX_SEARCH_RESULTS = 200

SHAPELY = False
try:
    import shapely
    import shapely.geometry
    from shapely.wkt import loads as wkt_loads
    SHAPELY = True
except ImportError:
    s3_debug("WARNING: %s: Shapely GIS library not installed" % __name__)

# =============================================================================

class S3SearchWidget(object):
    """
        Search Widget for interactive search (base class)
    """

    def __init__(self, field=None, name=None, **attr):
        """
            Configures the search option

            @param field: name(s) of the fields to search in

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
                if cname not in resource.components:
                    continue
                else:
                    component = resource.components[cname]
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
                ftype = str(ktable[rkey].type)
                if ftype[:9] == "reference":
                    reference = ftype[10:]
                elif ftype[:14] == "list:reference":
                    reference = ftype[15:]
                    multiple = True
                else:
                    continue
                rtable = ktable
                rtablename = ktablename
                ktable = db[reference]
                ktablename = reference
                # Do not add queries for empty tables
                if not db(ktable.id > 0).select(ktable.id,
                                                limitby=(0, 1)).first():
                    continue

            # Master queries
            # @todo: update this for new QueryBuilder (S3ResourceFilter)
            if ktable and ktablename not in master_query:
                query = (resource.accessible_query("read", ktable))
                if "deleted" in ktable.fields:
                    query = (query & (ktable.deleted == "False"))
                join = None
                if reference:
                    if ktablename != rtablename:
                        q = (resource.accessible_query("read", rtable))
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
                        q = (resource.accessible_query("read", table))
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
               vars,
               name = None,
               value = None,
               autocomplete = None):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        # SearchAutocomplete must set name depending on the field
        if name:
            self.attr.update(_name=name)

        if "_size" not in self.attr:
            self.attr.update(_size="40")
        if "_name" not in self.attr:
            self.attr.update(_name="%s_search_simple" % resource.name)
        if autocomplete:
            self.attr.update(_autocomplete=autocomplete)
        self.attr.update(_type="text")

        self.name = self.attr._name


        # Search Autocomplete - Display current value
        self.attr["_value"] = value

        return INPUT(**self.attr)

    # -------------------------------------------------------------------------
    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """

        prefix = resource.prefix
        name = resource.name
        table = resource.table

        db = current.db
        model = current.manager.model

        DEFAULT = (table.id == None)

        # Get master query and search fields
        self.build_master_query(resource)
        master_query = self.master_query
        search_field = self.search_field

        # No search fields?
        if not search_field:
            return DEFAULT

        # Default search (wildcard)
        if not value:
            return None

        # Build search query
        if value and isinstance(value, str):
            values = value.split()
            squery = None

            for v in values:
                wc = "%"
                _v = "%s%s%s" % (wc, v.lower(), wc)
                query = None
                for tablename in search_field:
                    hq = master_query[tablename]
                    fq = None
                    fields = search_field[tablename]
                    for f in fields:
                        if fq:
                            fq = (f.lower().like(_v)) | fq
                        else:
                            fq = (f.lower().like(_v))
                    q = hq & fq
                    if query is None:
                        query = q
                    else:
                        query = query | q
                if squery is not None:
                    squery = squery & query
                else:
                    squery = query

            return squery
        else:
            return DEFAULT

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

        self.names = []

        T = current.T
        settings = current.deployment_settings

        self.method = self.attr.get("method", "range")
        select_min = self.method in ("min", "range")
        select_max = self.method in ("max", "range")

        if len(self.field) > 1:
            raise SyntaxError("Only one search field allowed")

        if not self.search_field:
            self.build_master_query(resource)

        search_field = self.search_field.values()
        if not search_field:
            raise SyntaxError("No valid search field specified")

        search_field = search_field[0][0]

        ftype = str(search_field.type)
        input_min = input_max = None
        if ftype == "integer":
            requires = IS_EMPTY_OR(IS_INT_IN_RANGE())
        elif ftype == "date":
            self.attr.update(_class="date")
            requires = IS_EMPTY_OR(IS_DATE(format=settings.get_L10n_date_format()))
        elif ftype == "time":
            self.attr.update(_class="time")
            requires = IS_EMPTY_OR(IS_TIME())
        elif ftype == "datetime":
            self.attr.update(_class="datetime")
            requires = IS_EMPTY_OR(IS_DATETIME(format=settings.get_L10n_datetime_format()))
        else:
            raise SyntaxError("Unsupported search field type")

        self.attr.update(_type="text")
        if select_min:
            name = "min_%s" % search_field.name
            self.attr.update(_name=name, _id=name)
            self.names.append(name)
            input_min = INPUT(requires=requires, **self.attr)
        if select_max:
            name = "max_%s" % search_field.name
            self.attr.update(_name=name, _id=name)
            self.names.append(name)
            input_max = INPUT(requires=requires, **self.attr)
        trl = TR(_class="sublabels")
        tri = TR()
        if input_min is not None:
            trl.append(T("min"))
            tri.append(input_min)
        if input_max is not None:
            trl.append(T("max"))
            tri.append(input_max)
        w = DIV(TABLE(trl, tri))
        return w

    # -------------------------------------------------------------------------
    def validate(self, resource, value):
        """
            Validate the input values of the widget
        """

        errors = dict()

        T = current.T

        tablename = self.search_field.keys()[0]
        search_field = self.search_field[tablename][0]
        select_min = self.method in ("min", "range")
        select_max = self.method in ("max", "range")

        if select_min and select_max:
            vmin = value.get("min_%s" % search_field.name, None)
            vmax = value.get("max_%s" % search_field.name, None)
            if vmax is not None and vmin is not None and vmin > vmax:
                errors["max_%s" % search_field.name] = \
                     T("Maximum must be greater than minimum")

        return errors or None

    # -------------------------------------------------------------------------
    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """

        db = resource.db

        tablename = self.search_field.keys()[0]
        search_field = self.search_field[tablename][0]

        select_min = self.method in ("min", "range")
        select_max = self.method in ("max", "range")

        min_query = max_query = None
        if select_min:
            v = value.get("min_%s" % search_field.name, None)
            if v is not None and str(v):
                min_query = (search_field >= v)
        if select_max:
            v = value.get("max_%s" % search_field.name, None)
            if v is not None and str(v):
                max_query = (search_field <= v)
        query = self.master_query[tablename]
        if min_query is not None or max_query is not None:
            if min_query is not None:
                query = query & min_query
            if max_query is not None:
                query = query & max_query
        else:
            query = None
        return (query)

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

    def _get_reference_resource(self, resource):
        """
            If the field is entered as kfield$field, will search field in the
            the referenced resource.
        """
        field = self.field[0]
        kfield = None

        if field.find("$") != -1:
            is_component = True
            kfield, field = field.split("$")
            tablename = resource.table[kfield].type[10:]
            prefix, resource_name = tablename.split("_", 1)
            resource = current.manager.define_resource(prefix,
                                                       resource_name)
        return resource, field, kfield

    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        resource, field, kfield = self._get_reference_resource(resource)

        T = current.T

        if "_name" not in self.attr:
            self.attr.update(_name="%s_search_select_%s" % (resource.name,
                                                            field))
        self.name = self.attr._name
        msg = self.attr._no_opts

        if vars and self.name in vars:
            value = vars[self.name]
        else:
            value = None

        field_type = str(resource.table[field].type)
        if field_type == "boolean":
            opt_keys = (True, False)
        else:
            # Find unique values of options for that field
            rows = resource.select(resource.table[field], groupby = resource.table[field])
            if field_type.startswith("list"):
                opt_keys = []
                for row in rows:
                    if row[field] != None:
                        try:
                            _opt_keys = row[field].split("|")
                        except:
                            _opt_keys = row[field]
                        for opt_key in _opt_keys:
                            opt_keys.append(opt_key)
            else:
                opt_keys = [row[field] for row in rows if row[field] != None]
            if opt_keys == []:
                msg = self.attr._no_opts
                if msg is None:
                    msg = T("no options available")
                if msg:
                    return SPAN(msg,
                                _style="color:#AAA; font-style:italic;")
                else:
                    return None

        # Always use the represent of the widget, if present
        represent = self.attr.represent
        # Fallback to the field's represent
        if not represent or field_type[:9] != "reference":
            represent = resource.table[field].represent

        # Execute, if callable
        if callable(represent):
            opt_list = [(opt_key, represent(opt_key)) for opt_key in opt_keys]
        # Otherwise, feed the format string
        elif isinstance(represent, str) and field_type[:9] == "reference":
            # Use the represent string to reduce db calls
            # Find the fields which are needed to represent:
            db = current.db
            ktable = db[field_type[10:]]
            fieldnames = ["id"]
            fieldnames += re.findall("%\(([a-zA-Z0-9_]*)\)s", represent)
            represent_fields = [ktable[fieldname] for fieldname in fieldnames]
            query = (ktable.id.belongs(opt_keys)) & (ktable.deleted == False)
            represent_rows = db(query).select(*represent_fields).as_dict(key=represent_fields[0].name)
            opt_list = []
            for opt_key in opt_keys:
                opt_represent = represent % represent_rows[opt_key]
                if opt_represent:
                    opt_list.append([opt_key, opt_represent])
        else:
            opt_list = [(opt_key, "%s" % opt_key) for opt_key in opt_keys if opt_key]

        # Alphabetise (this will not work as it is converted to a dict),
        # look at IS_IN_SET validator or CheckboxesWidget to ensure
        # that the list opt_list.sort()

        options = dict(opt_list)
        #for opt in opt_list:
        #    options[opt[1]] = opt[0]

        # Dummy field
        opt_field = Storage(name = self.name,
                            requires = IS_IN_SET(options,
                                                 multiple=True))
        MAX_OPTIONS = 20
        if len(opt_list) > MAX_OPTIONS:
            # Collapse list Alphabetically into letter headers
            # Could this functionality be implemented in a custom
            # CheckboxesWidget?

            # Split opt_list into a dict with the letter as keys
            # letter_options = { "A" : [ ( n, "A..."),
            #                            ( n, "A..."),
            #                            ...
            #                            ],
            #                    "B" : [ ( n, "B..."),
            #                            ( n, "B..."),
            #                            ...
            #                            ],
            #                     ...
            #                    }
            # and create a list of letters
            letters = []
            letter_options = {}
            for key, label in opt_list:
                letter = label[0].upper()
                if letter not in letter_options:
                    letters.append(letter)
                    letter_options[letter] = [(key, label)]
                else:
                    letter_options[letter].append((key, label))

            # Ensure that letters contains A & Z
            # (For usability to ensure that the complete range is displayed)
            letters.sort()
            if letters[0] != "A":
                letters.insert(0,"A")
            if letters[-1] != "Z":
                letters.append("Z")

            # Build widget
            widget = DIV()
            count = 0
            options = []
            requires = IS_IN_SET(opt_list, multiple=True)

            from_letter = None
            to_letter = None
            for letter in letters:
                if not from_letter:
                    from_letter = letter
                letter_option = letter_options.get(letter, [])
                count += len(letter_option)
                # Check if the number of options is > MAX_OPTIONS
                if count > MAX_OPTIONS or letter == "Z":
                    if not options:
                        options = letter_option
                    # Are these options for a single letter or a range?
                    if to_letter != from_letter:
                        letter = "%s - %s" % (from_letter, to_letter)
                    # Letter Label
                    widget.append(DIV( letter,
                                       _id = "%s_search_select_%s_label_%s" %
                                                (resource.name,
                                                 field,
                                                 from_letter),
                                       _class = "search_select_letter_label",

                                      ),
                                  )
                    opt_field = Storage(name = self.name,
                                        requires = IS_IN_SET(options,
                                                             multiple=True))
                    if self.attr.cols:
                        letter_widget = CheckboxesWidgetS3.widget(opt_field,
                                                                  value,
                                                                  cols=self.attr.cols,
                                                                  requires = requires)
                    else:
                        letter_widget = CheckboxesWidgetS3.widget(opt_field, value)
                    widget.append(DIV( letter_widget,
                                       _id = "%s_search_select_%s_widget_%s" %
                                                (resource.name,
                                                 field,
                                                 from_letter),
                                       _class = "search_select_letter_widget",
                                       _style = "display:none;",
                                      )
                                  )
                    count = 0
                    options = []
                    from_letter = None
                options += letter_option
                to_letter = letter

        else:
            try:
                if self.attr.cols:
                    widget = CheckboxesWidgetS3.widget(opt_field, value,
                                                       cols=self.attr.cols)
                else:
                    widget = CheckboxesWidgetS3.widget(opt_field, value)
            except:
                # Some versions of gluon/sqlhtml.py don't support
                # non-integer keys
                return None
        return widget

    # -------------------------------------------------------------------------
    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget
        """
        s_resource = resource

        resource, field, kfield = self._get_reference_resource(resource)

        if value:
            if not isinstance(value, (list, tuple)):
                value = [value]
            field_type = str(resource.table[field].type)
            if field_type.startswith("list"):
                query = (resource.table[field].contains(value))
            else:
                query = (resource.table[field].belongs(value))
            if kfield:
                # This is searching a referenced resource
                # Add join query
                query  = query & \
                         (s_resource.table[kfield] == resource.table.id)
            return query
        else:
            return None

# =============================================================================

class S3SearchLocationHierarchyWidget(S3SearchOptionsWidget):
    """
        Displays a search widget which allows the user to search for records
        by selecting a location from a specified level in the hierarchy.
    """

    def __init__(self, name=None, **attr):
        """
            Configures the search option

            @param field: name(s) of the fields to search in

            @keyword comment: a comment for the search widget
        """

        gis = current.gis

        self.other = None

        config = gis.get_config()
        field = config.search_level or "L0"
        self.field = [field]

        label = gis.get_location_hierarchy(field)

        self.attr = Storage(attr)
        self.attr["label"] = label
        if name is not None:
            self.attr["_name"] = name

        self.master_query = None
        self.search_field = None

# =============================================================================

class S3SearchLocationWidget(S3SearchWidget):
    """
        Interactive location search widget
        - allows the user to select a BBOX & have only results from within
          that BBOX returned

        @ToDo: Have an option to use a Circular Radius
               http://openlayers.org/dev/examples/regular-polygons.html
        @ToDo: Have an option to use a full Polygon
               Hard to process this as a resource filter
    """

    def __init__(self,
                 field=["location_id"],
                 name=None, # Needs to be specified by caller
                 **attr):
        """
            Initialise parent class & make any necessary modifications
        """

        S3SearchWidget.__init__(self, field, name, **attr)

        #

    # -------------------------------------------------------------------------
    def widget(self, resource, vars):
        """
            Returns the widget

            @param resource: the resource to search in
            @param vars: the URL GET variables as dict
        """

        if not SHAPELY:
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
                              _class="hidden")

        # Button to open the Map
        OPEN_MAP = T("Open Map")
        map_button = A(OPEN_MAP,
                       _style="cursor:pointer; cursor:hand",
                       _id="gis_search_map-btn")

        # Map Popup
        # - reuse the one that comes with dataTables

        # Settings to be read by static/scripts/S3/s3.gis.js
        js_location_search = """S3.gis.draw_polygon = true;"""

        # The overall layout of the components
        return TAG[""](
                        polygon_input,
                        map_button,
                        #map_popup,
                        SCRIPT(js_location_search)
                      )

    # -------------------------------------------------------------------------
    def query(self, resource, value):
        """
            Returns a sub-query for this search option

            @param resource: the resource to search in
            @param value: the value returned from the widget: WKT format
        """

        #gis = current.gis
        table = resource.table
        s3db = current.s3db
        locations = s3db.gis_location

        # Get master query and search fields
        #self.build_master_query(resource)
        #master_query = self.master_query

        if value:
            # @ToDo: Turn this into a Resource filter
            #features = gis.get_features_in_polygon(value,
            #                                       tablename=resource.tablename)

            # @ToDo: A PostGIS routine, where-available
            #        - requires a Spatial DAL?
            try:
                shape = wkt_loads(value)
            except:
                s3_debug("WARNING: s3search: Invalid WKT")
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
            filter = (table[self.field[0]] == locations.id) & \
                     (locations.lat_min <= lat_max) & \
                     (locations.lat_max >= lat_min) & \
                     (locations.lon_min <= lon_max) & \
                     (locations.lon_max >= lon_min)
            return filter
        else:
            return None

# =============================================================================

class S3SearchCredentialsWidget(S3SearchOptionsWidget):
    """
        Options Widge to search for HRMs with specified Credentials
    """

    def widget(self, resource, vars):
        manager = current.manager
        c = manager.define_resource("hrm", "credential")
        return S3SearchOptionsWidget.widget(self, c, vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def query(resource, value):
        if value:
            db = current.db
            htable = db.hrm_human_resource
            ptable = db.pr_person
            ctable = db.hrm_credential
            query = (htable.person_id == ptable.id) & \
                    (htable.deleted != True) & \
                    (ctable.person_id == ptable.id) & \
                    (ctable.deleted != True) & \
                    (ctable.job_role_id.belongs(value))
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

    def widget(self, resource, vars):
        manager = current.manager
        c = manager.define_resource("hrm", "competency")
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
        names = []
        self.__simple = []
        if not isinstance(simple, (list, tuple)):
            simple = [simple]
        for widget in simple:
            if widget is not None:
                name = widget.attr._name
                if name in names:
                    raise SyntaxError("Duplicate widget: %s") % name
                # Widgets should be able to have default names
                # elif not name:
                #     raise SyntaxError("Widget with no name")
                else:
                    self.__simple.append((name, widget))
                    names.append(name)

        names = []
        self.__advanced = []
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
                    self.__advanced.append((name, widget))
                    names.append(name)

        self.__any = any

        if self.__simple or self.__advanced:
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

        if r.component and self != self.resource.search:
            output = self.resource.search(r, **attr)

        # Autocomplete-Widget
        elif "is_autocomplete" in attr:
            output = self.search_autocomplete(r, **attr)

        # Save search
        elif "save" in r.vars :
            r.interactive = False
            output = self.save_search(r, **attr)

        # Interactive or saved search
        elif "load" in r.vars or \
             r.interactive and self.__interactive:
            output = self.search_interactive(r, **attr)

        # SSPag response => CRUD native
        elif format == "aadata" and self.__interactive:
            output = self.select(r, **attr)

        # JSON search
        elif format == "json":
            output = self.search_json(r, **attr)

        # Autocomplete-JSON search
        elif format == "acjson":
            output = self.search_json_autocomplete(r, **attr)

        # Not supported
        else:
            r.error(501, current.manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def _build_widget_query(resource, name, widget, form, query):
        """
            @todo: docstring
        """

        errors = None
        if hasattr(widget, "names"):
            value = Storage([(name, form.vars[name])
                             for name in widget.names
                             if name in form.vars])
        elif name in form.vars:
            value = form.vars[name]
        else:
            value = None
        if hasattr(widget, "validate"):
            errors = widget.validate(resource, value)
        else:
            q = widget.query(resource, value)
            if q is not None:
                if query is None:
                    query = q
                else:
                    query = query & q
        return (query, errors)

    # -------------------------------------------------------------------------
    def save_search_widget(self, r, search_vars, **attr):
        """
            @todo: docstring
        """

        request = self.request

        db = current.db
        s3db = current.s3db

        user_id = current.session.auth.user.id
        save_search_btn_id = "save_my_filter_btn_%s" % str(request.utcnow.microsecond)
        save_search_processing_id = "save_search_processing_%s" % str(request.utcnow.microsecond)
        save_search_a_id  = "save_search_a_%s" % str(request.utcnow.microsecond)
        arg = str(user_id) + "/save_search"
        save_search_a = DIV("View and Subscribe to Saved Searches ",
                            A("Here",
                          _href = URL(r=request, c="pr", f="person", args=[arg]),
                        _target = "_blank"
                        ),
                        ".",
                        _id = save_search_a_id,
                        _class = "save_search_a"
                        )
        search_vars["prefix"] = r.prefix
        search_vars["function"] = r.function

        table = s3db.pr_save_search
        if len (db(table.user_id == user_id).select(table.id,
                                                    limitby = (0,1))):
            rows = db(table.user_id == user_id).select(table.ALL)
            for row in rows:
                pat = "_"
                s_v = cPickle.loads(row.search_vars)
                if ((search_vars["prefix"] == s_v["prefix"]) and \
                    (search_vars["function"] == s_v["function"])):
                    s_dict = s_v["criteria"]
                    if "criteria" in search_vars:
                        c_dict = search_vars["criteria"]
                    else:
                        break
                    diff = [ k for k in c_dict if k not in s_dict ]
                    if not len(diff):
                        flag = 1
                        for j in s_dict.iterkeys():
                           if not re.match(pat,j):
                               if c_dict[j] != s_dict[j]:
                                   flag = 0
                                   break
                        if flag == 1:
                            return DIV(save_search_a,
                                       _style = "font-size:12px; padding:5px 0px 5px 90px;",
                                       _id = "save_search"
                                       )

        save_search_btn = A("Save Search",
                                    _class = "save_search_btn",
                                    _id = save_search_btn_id,
                                    _href = "#",
                                    _title = "Save this search")
        save_search_a["_style"] = "display:none;"
        save_search_processing = IMG(_src = "/" + request.application + "/static/img/ajax-loader.gif",
                                    _id = save_search_processing_id,
                                    _class = "save_search_processing_id",
                                    _style = "display:none;"
                                    )
        s_var = {}
        s_var["save"] = True
        jurl = URL(r=request, c=r.prefix, f=r.function, args=["search"], vars = s_var)
        save_search_script = SCRIPT("".join("""
                                        $("#%s").live( 'click', function () {
                                            $("#%s").show();
                                            $("#%s").hide();
                                            $.ajax({
                                                url: '%s',
                                                data: '%s',
                                                success: function(data) {
                                                                    $("#%s").show();
                                                                    $("#%s").hide();
                                                                    },
                                                type: 'POST'
                                                });
                                            return false;
                                            });
                                        """%
                                        (save_search_btn_id,
                                         save_search_processing_id,
                                         save_search_btn_id,
                                         jurl,
                                         jsonlib.dumps(search_vars),
                                         save_search_a_id,
                                         save_search_processing_id)))
        save_search  = DIV(save_search_processing,
                                save_search_a,
                                save_search_btn,
                                save_search_script,
                                _style = "font-size:12px; padding:5px 0px 5px 90px;",
                                _id = "save_search"
                                )
        return save_search

    # -------------------------------------------------------------------------
    def search_interactive(self, r, **attr):
        """
            Interactive search

            @param r: the S3Request instance
            @param attr: request parameters
        """

        # Get environment
        session = current.session
        request = self.request
        response = current.response
        s3 = response.s3
        resource = self.resource
        settings = current.deployment_settings
        db = current.db
        s3db = current.s3db
        manager = current.manager
        table = self.table
        tablename = self.tablename
        gis = current.gis
        T = current.T

        vars = request.get_vars

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
        form = DIV(_class="search_form form-container")

        # Build the search forms
        simple_form, advanced_form = self.build_forms(r)

        # Check for Load Search
        if "load" in r.get_vars:
            search_id = r.get_vars.get("load", None)
            if not search_id:
                r.error(400, manager.ERROR.BAD_RECORD)
            r.post_vars = r.vars
            manager.load("pr_save_search")
            search_table = s3db.pr_save_search
            _query = (search_table.id == search_id)
            record = db(_query).select(limitby=(0, 1)).first()
            if not record:
                r.error(400, manager.ERROR.BAD_RECORD)
            s_vars = cPickle.loads(record.search_vars)
            r.post_vars = Storage(s_vars["criteria"])
            r.http = "POST"

        # Process the search forms
        query, errors = self.process_forms(r,
                                           simple_form,
                                           advanced_form)
        if r.http == "POST" and not errors:
            resource.add_filter(query)
            search_vars = dict(simple=simple,
                               advanced=not simple,
                               criteria=r.post_vars)
        else:
            search_vars = dict()

        if s3.simple_search:
            form.append(DIV(_id="search-mode", _mode="simple"))
        else:
            form.append(DIV(_id="search-mode", _mode="advanced"))

        # Save Search Widget
        if r.http == "POST" and \
           session.auth and settings.get_save_search_widget():
            save_search = self.save_search_widget(r, search_vars, **attr)
        else:
            save_search  = DIV()

        # Complete the output form-DIV()
        if simple_form is not None:
            simple_form.append(save_search)
            form.append(simple_form)
        if advanced_form is not None:
            advanced_form.append(save_search)
            form.append(advanced_form)
        output["form"] = form

        # Build session filter (for SSPag)
        if not s3.no_sspag:
            limit = 1
            ids = resource.get_id()
            if ids:
                if not isinstance(ids, list):
                    ids = str(ids)
                else:
                    ids = ",".join([str(i) for i in ids])
                session.s3.filter = {"%s.id" % resource.name: ids}
        else:
            limit = None

        # List fields
        linkto = self._linkto(r)
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
        if not orderby:
            orderby = fields[0]

        # Truncate long texts
        if r.interactive or r.representation == "aadata":
            for f in table:
                if str(f.type) == "text" and not f.represent:
                    f.represent = self.truncate

        # Get the result table
        items = resource.sqltable(fields=list_fields,
                                  limit=limit,
                                  orderby=orderby,
                                  distinct=True,
                                  linkto=linkto,
                                  download_url=self.download_url,
                                  format=representation)

        # Remove the dataTables search box to avoid confusion
        s3.dataTable_NobFilter = True

        if items:
            if not s3.no_sspag:
                # Pre-populate SSPag cache (avoids the 1st Ajax request)
                totalrows = resource.count(distinct=True)
                if totalrows:
                    if s3.dataTable_iDisplayLength:
                        limit = 2 * s3.dataTable_iDisplayLength
                    else:
                        limit = 50
                    sqltable = resource.sqltable(fields=list_fields,
                                                 start=0,
                                                 limit=limit,
                                                 orderby=orderby,
                                                 distinct=True,
                                                 linkto=linkto,
                                                 download_url=self.download_url,
                                                 as_page=True,
                                                 format=representation)
                    aadata = dict(aaData = sqltable or [])
                    aadata.update(iTotalRecords=totalrows,
                                  iTotalDisplayRecords=totalrows)
                    response.aadata = json(aadata)
                    s3.start = 0
                    s3.limit = limit

            if r.http == "POST" and not errors:
                query = None
                if "location_id" in r.target()[2]:
                    query = (table.location_id == s3db.gis_location.id)
                elif "site_id" in r.target()[2]:
                    stable = s3db.org_site
                    query = (table.site_id == stable.id) & \
                            (stable.location_id == s3db.gis_location.id)
                if query:
                    resource.add_filter(query)
                    features = resource.select()
                    # @ToDo: Check if we need to calculate this per-record when we have differential markers
                    marker = gis.get_marker(tablename=tablename)

                    for feature in features:
                        # @ToDo: Add popup_label to each row (DRY'd from xml.gis_encode())
                        # Add a popup_url per feature
                        feature.popup_url = "%s.plain" % URL(r.prefix,r.name,
                                                             args=feature[tablename].id)
                        # @ToDo: Differential Markers
                        #feature.marker = marker

                    feature_queries = [{"name"   : T("Search results"),
                                        "query"  : features,
                                        "marker" : marker}]
                    # Calculate an appropriate BBox
                    bounds = gis.get_bounds(features=features)

        elif not items:
            items = self.crud_string(tablename, "msg_no_match")

        output["items"] = items
        output["sortby"] = sortby

        if "location_id" in r.target()[2] or "site_id" in r.target()[2]:
            # Add a map for search results
            # (this same map is also used by the Map Search Widget, if-present)
            if bounds:
                # We have some features returned
                map_popup = gis.show_map(
                                        feature_queries = feature_queries,
                                        toolbar = True,
                                        collapsed = True,
                                        bbox = bounds,
                                        #search = True,
                                        window = True,
                                        window_hide = True
                                        )
            else:
                # We have no features returned
                # Load the Map anyway for the Search Widget
                map_popup = gis.show_map(
                                        # Added by search widget onClick in s3.dataTables.js
                                        #add_polygon = True,
                                        #add_polygon_active = True,
                                        toolbar = True,
                                        collapsed = True,
                                        #search = True,
                                        window = True,
                                        window_hide = True
                                        )
            s3.dataTableMap = map_popup

        # Title and subtitle
        output["title"] = self.crud_string(tablename, "title_search")
        output["subtitle"] = self.crud_string(tablename, "msg_match")

        # View
        response.view = self._view(r, "search.html")
        return output

    # -------------------------------------------------------------------------
    def process_forms(self, r, simple_form, advanced_form):
        """
            @todo: docstring
        """

        session = current.session
        response = current.response

        query = None
        errors = None

        # Process the simple search form:
        simple = simple_form is not None
        if simple_form is not None:
            if simple_form.accepts(r.post_vars, session,
                                   formname="search_simple",
                                   keepvalues=True) or \
               "load" in r.get_vars and \
                simple_form.accepts(r.post_vars,
                                    formname="search_simple",
                                    keepvalues=True):
                for name, widget in self.__simple:
                    query, errors = self._build_widget_query(self.resource,
                                                             name,
                                                             widget,
                                                             simple_form,
                                                             query)
                    if errors:
                        simple_form.errors.update(errors)
                errors = simple_form.errors
            elif simple_form.errors:
                errors = simple_form.errors
                return query, errors, simple

        # Process the advanced search form:
        if advanced_form is not None:
            if advanced_form.accepts(r.post_vars, session,
                                     formname="search_advanced",
                                     keepvalues=True) or \
               "load" in r.get_vars and \
               advanced_form.accepts(r.post_vars,
                                     formname="search_advanced",
                                     keepvalues=True):
                simple = False
                for name, widget in self.__advanced:
                    query, errors = self._build_widget_query(self.resource,
                                                             name,
                                                             widget,
                                                             advanced_form,
                                                             query)
                    if errors:
                        advanced_form.errors.update(errors)

                errors = advanced_form.errors
            elif advanced_form.errors:
                simple = False

        response.s3.simple_search = simple
        return (query, errors)

    # -------------------------------------------------------------------------
    def build_forms(self, r):
        """
            @todo: docstring
        """

        T = current.T
        tablename = self.tablename
        representation = r.representation

        simple_form = None
        advanced_form = None

        # Add-link (common to all forms)
        ADD = self.crud_string(tablename, "label_create_button")
        href_add = r.url(method="create", representation=representation)
        insertable = self._config("insertable", True)
        authorised = self.permit("create", tablename)
        if authorised and insertable:
            add_link = self.crud_button(ADD, _href=href_add,
                                        _id="add-btn", _class="action-lnk")
        else:
            add_link = ""

        # Simple search form
        if self.__simple:
            # Switch-link
            if self.__advanced:
                switch_link = A(T("Advanced Search"), _href="#",
                                _class="action-lnk advanced-lnk")
            else:
                switch_link = ""
            simple_form = self._build_form(self.__simple,
                                           add=add_link,
                                           switch=switch_link,
                                           _class="simple-form")

        # Advanced search form
        if self.__advanced:
            if self.__simple:
                switch_link = A(T("Simple Search"), _href="#",
                                _class="action-lnk simple-lnk")
                _class = "%s hide"
            else:
                switch_link = ""
                _class = "%s"
            advanced_form = self._build_form(self.__advanced,
                                             add=add_link,
                                             switch=switch_link,
                                             _class=_class % "advanced-form")

        return (simple_form, advanced_form)

    # -------------------------------------------------------------------------
    def _build_form(self, widgets, add="", switch="", **attr):
        """
            @todo: docstring
        """

        T = current.T
        request = self.request
        resource = self.resource

        vars = request.get_vars

        trows = []
        for name, widget in widgets:

            _widget = widget.widget(resource, vars)
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
            tr = TR(TD("%s: " % label, _class="w2p_fl"),
                    widget.widget(resource, vars))

            if comment:
                tr.append(DIV(DIV(_class="tooltip",
                                  _title="%s|%s" % (label, comment))))
            trows.append(tr)

        trows.append(TR("", TD(INPUT(_type="submit", _value=T("Search")),
                               switch, add)))
        form = FORM(TABLE(trows), **attr)
        return form

    # -------------------------------------------------------------------------
    def search_json(self, r, **attr):
        """
            JSON search method for S3AutocompleteWidget

            @param r: the S3Request
            @param attr: request attributes
        """

        db = current.db
        manager = current.manager
        xml = manager.xml

        request = self.request
        response = current.response

        resource = self.resource
        table = self.table

        _vars = request.vars

        limit = int(_vars.limit or 0)

        output = None

        # JQueryUI Autocomplete uses "term" instead of "value"
        # (old JQuery Autocomplete uses "q" instead of "value")
        value = _vars.value or _vars.term or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = value.lower()

        if _vars.field and _vars.filter and value:
            fieldname = str.lower(_vars.field)
            field = table[fieldname]

            # Default fields to return
            fields = [table.id, field]
            if table == current.db.org_site:
                # Simpler to provide an exception case than write a whole new class
                fields.append(table.instance_type)

            filter = _vars.filter
            if filter == "~":
                # Normal single-field Autocomplete
                query = (field.lower().like("%" + value + "%"))

            elif filter == "=":
                if field.type.split(" ")[0] in \
                    ["reference", "id", "float", "integer"]:
                    # Numeric, e.g. Organizations' offices_by_org
                    query = (field == value)
                else:
                    # Text
                    query = (field.lower() == value)

            elif filter == "<":
                query = (field < value)

            elif filter == ">":
                query = (field > value)

            else:
                output = xml.json_message(False,
                                          400,
                                          "Unsupported filter! Supported filters: ~, =, <, >")
                raise HTTP(400, body=output)

            # Exclude records which are already linked:
            #      ?link=<linktablename>.<leftkey>.<id>.<rkey>.<fkey>
            # e.g. ?link=project_organisation.organisation_id.5.project_id.id
            if "link" in _vars:
                try:
                    link, lkey, _id, rkey, fkey = _vars.link.split(".")
                    manager.load(link)
                    linktable = db[link]
                    fq = (linktable[rkey] == table[fkey]) & \
                         (linktable[lkey] == _id)
                    linked = db(fq).select(table._id)
                    exclude = (~(table._id.belongs([r[table._id.name]
                                                    for r in linked])))
                except Exception, e:
                    pass # ignore
                else:
                    query &= exclude

            # Select only or exclude template records:
            # to only select templates:
            #           ?template=<fieldname>.<value>,
            #      e.g. ?template=template.true
            # to exclude templates:
            #           ?template=~<fieldname>.<value>
            #      e.g. ?template=~template.true
            if "template" in _vars:
                try:
                    flag, val = _vars.template.split(".", 1)
                    if flag[0] == "~":
                        exclude = True
                        flag = flag[1:]
                    else:
                        exclude = False
                    ffield = table[flag]
                except:
                    pass # ignore
                else:
                    if str(ffield.type) == "boolean":
                        if val.lower() == "true":
                            val = True
                        else:
                            val = False
                    if exclude:
                        templates = (ffield != val)
                    else:
                        templates = (ffield == val)
                    resource.add_filter(templates)

            resource.add_filter(query)

            if filter == "~":
                if (not limit or limit > MAX_SEARCH_RESULTS) and resource.count() > MAX_SEARCH_RESULTS:
                   output = json([dict(id="",
                                       name="Search results are over %d. Please input more characters." \
                                       % MAX_SEARCH_RESULTS)])

            if output is None:
                output = resource.exporter.json(resource,
                                                start=0,
                                                limit=limit,
                                                fields=fields,
                                                orderby=field)
            response.headers["Content-Type"] = "application/json"

        else:
            output = xml.json_message(False,
                                      400,
                                      "Missing options! Require: field, filter & value")
            raise HTTP(400, body=output)

        return output

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
        request = self.request
        resource = self.resource
        T = current.T

        vars = request.get_vars

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
                         _prefix = resource.prefix,
                         _resourcename = resource.name,
                         _fieldname = fieldname,
                         )
        if get_fieldname:
            form_attr["_get_fieldname"] = get_fieldname
            # Otherwise default get_fieldname is "id"

        form = DIV(**form_attr)

        # Append the simple search form
        if self.__simple:
            simple = True
            if self.__advanced:
                switch_link = A(T("Advanced Search"), _href="#",
                                _class="action-lnk advanced-lnk %s",
                                _fieldname = fieldname)
            else:
                switch_link = ""
            # Only display the S3SearchSimpleWidget (should be first)
            name, widget = self.__simple[0]

            self._check_search_autcomplete_search_simple_widget( widget)
            name = "%s_search_simple_simple" % fieldname

            autocomplete_widget =  widget.widget(resource,
                                                 vars,
                                                 name = name,
                                                 value = value,
                                                 autocomplete = "off")

            simple_form = DIV( TABLE( autocomplete_widget,
                                      switch_link
                                     ),
                              _class="simple-form")
            form.append(simple_form)

        # Append the advanced search form
        if self.__advanced:
            trows = []
            first_widget = True
            for name, widget in self.__advanced:
                _widget = widget.widget(resource, vars)
                if _widget is None:
                    # Skip this widget as we have nothing but the label
                    continue
                label = widget.field
                if first_widget:
                    self._check_search_autcomplete_search_simple_widget( widget)
                    name = "%s_search_simple_advanced" % fieldname
                    autocomplete_widget =  widget.widget(resource,
                                                         vars,
                                                         name = name,
                                                         value = value,
                                                         autocomplete = "off")
                    first_widget = False
                else:
                    if isinstance(label, (list, tuple)) and len(label):
                        label = label[0]
                    if hasattr(widget, "attr"):
                        label = widget.attr.get("label", label)
                    tr = TR(TD("%s: " % label, _class="w2p_fl"), _widget)
                    trows.append(tr)

            if self.__simple:
                switch_link = A(T("Simple Search"), _href="#",
                                _class="action-lnk simple-lnk",
                                _fieldname = fieldname)
            else:
                switch_link = ""

            if simple:
                _class = "hide"
            else:
                _class = None
            advanced_form = DIV(autocomplete_widget,
                                TABLE(trows),
                                TABLE(TR(switch_link)),
                                _class="%s advanced-form" % _class,
                                #_resourcename = resource.name
                                )
            form.append(advanced_form)

        output.update(form=form)
        return output

    # -------------------------------------------------------------------------
    def search_json_autocomplete(self, r, **attr):
        """
            @todo: docstring
        """

        query = None
        errors = True

        request = self.request
        resource = self.resource
        response = current.response

        response.headers["Content-Type"] = "application/json"

        # Process the simple search form:
        if self.__simple and request.vars.simple_form:
            for name, widget in self.__simple:
                # Pass request instead of form - it contains the vars
                query, errors = self._build_widget_query(self.resource,
                                                         name,
                                                         widget,
                                                         request,
                                                         query)
                if errors:
                    break
        # Process the advanced search form:
        elif self.__advanced:
            for name, widget in self.__advanced:
                # Pass request instead of form - it contains the vars
                query, errors = self._build_widget_query(self.resource,
                                                         name,
                                                         widget,
                                                         request,
                                                         query)
                if errors:
                    break
        else:
            errors = True

        resource.add_filter(query)
        try:
            get_fieldname = request.vars.get("get_fieldname", "id")
            field = resource.table[get_fieldname]
        except:
            errors = True

        # How can this be done more elegantly?
        resource_represent = { "human_resource":
                               lambda id: \
                                response.s3.hrm_human_resource_represent(id,
                                                                         show_link = True)
                              }
        if get_fieldname == "id":
            represent = resource_represent[resource.name]
        else:
            represent = field.represent

        #output = resource.exporter.json(resource,
        #                                start=0,
        #                                limit=10,
        #                                fields = [field],
        #                                orderby = field)


        attributes = dict(orderby=field,
                          limitby = resource.limitby(start=0, limit=11),
                          distinct = True)

        # Get the rows
        rows = resource.select(field, **attributes)

        if not errors:
            output =[{ "id"   : row[get_fieldname],
                       "represent" : str(represent( row[get_fieldname] ) )
                       } for row in rows ]
        else:
            json("{}")

        return json(output)

    # -------------------------------------------------------------------------
    @staticmethod
    def save_search(r, **attr):
        """
            @todo: docstring
        """

        # r contains the resource name:
        tablename = r.tablename
        component = r.component_name
        s3mgr = current.manager
        db = current.db
        s3db = current.s3db
        session = current.session
        auth =  current.auth

        user_id = auth.user.id
        search_vars = jsonlib.load(r.body)
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
        search_str = cPickle.dumps(s_vars)
        table = s3db.pr_save_search
        query = (table.user_id == user_id) & \
                (table.search_vars == search_str)
        if len (db(query).select(table.id)) == 0:
            new_search = {}
            new_search["search_vars"] = search_str
            _id = table.insert(**new_search)
        msg = "success"
        return msg

# =============================================================================

class S3LocationSearch(S3Search):
    """
        Search method with specifics for Location records (hierarchy search)
    """

    def search_json(self, r, **attr):
        """
            JSON search method for S3LocationAutocompleteWidget

            @param r: the S3Request
            @param attr: request attributes
        """

        xml = current.manager.xml
        gis = current.manager.gis

        output = None
        request = self.request
        response = current.response
        resource = self.resource
        table = self.table

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = request.vars

        limit = int(_vars.limit or 0)

        # JQueryUI Autocomplete uses "term" instead of "value"
        # (old JQuery Autocomplete uses "q" instead of "value")
        value = _vars.value or _vars.term or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        if value:
            value = value.lower()

        query = None
        fields = []
        field = table.id

        if _vars.field and _vars.filter and value:
            fieldname = str.lower(_vars.field)
            field = table[fieldname]

            # Default fields to return
            fields = [table.id,
                      table.name,
                      table.level,
                      table.parent,
                      table.path,
                      table.uuid,
                      table.lat,
                      table.lon,
                      table.addr_street,
                      table.addr_postcode]

            # Optional fields
            if "level" in _vars and _vars.level:
                if _vars.level == "null":
                    level = None
                elif "|" in _vars.level:
                    level = _vars.level.split("|")
                else:
                    level = str.upper(_vars.level)
            else:
                level = None

            if "parent" in _vars and _vars.parent:
                if _vars.parent == "null":
                    parent = None
                else:
                    parent = int(_vars.parent)
            else:
                parent = None

            if "children" in _vars and _vars.children:
                if _vars.children == "null":
                    children = None
                else:
                    children = int(_vars.children)
            else:
                children = None

            if "field2" in _vars and _vars.field2:
                fieldname = str.lower(_vars.field2)
                field2 = table[fieldname]
            else:
                field2 = None

            if "exclude_field" in _vars:
                exclude_field = str.lower(_vars.exclude_field)
                if "exclude_value" in _vars:
                    exclude_value = str.lower(_vars.exclude_value)
                else:
                    exclude_value = None
            else:
                exclude_field = None
                exclude_value = None

            filter = _vars.filter
            if filter == "~":
                if children:
                    # New LocationSelector
                    children = gis.get_children(children, level=level)
                    #children = children.find(lambda row: \
                    #                         value in str.lower(row.name))
                    output = children.json()
                    response.headers["Content-Type"] = "application/json"
                    return output

                if exclude_field and exclude_value:
                    # Old LocationSelector
                    # Filter out poor-quality data, such as from Ushahidi
                    query = (field.lower().like("%" + value + "%")) & \
                            ((table[exclude_field].lower() != exclude_value) | \
                             (table[exclude_field] == None))

                elif field2:
                    # New LocationSelector
                    query = ((field.lower().like("%" + value + "%")) | \
                             (field2.lower().like("%" + value + "%")))

                else:
                    # Normal single-field
                    query = (field.lower().like("%" + value + "%"))

                if level:
                    resource.add_filter(query)
                    # New LocationSelector or Autocomplete
                    if isinstance(level, list):
                        query = (table.level.belongs(level))
                    elif str.upper(level) == "NULLNONE":
                        level = None
                        query = (table.level == level)
                    else:
                        query = (table.level == level)

                if parent:
                    # New LocationSelector
                    resource.add_filter(query)
                    query = (table.parent == parent)

            elif filter == "=":
                if field.type.split(" ")[0] in \
                   ["reference", "id", "float", "integer"]:
                    # Numeric, e.g. Organizations' offices_by_org
                    query = (field == value)
                else:
                    # Text
                    if value == "nullnone":
                        # i.e. old Location Selector
                        query = (field == None)
                    else:
                        query = (field.lower() == value)

                if parent:
                    # i.e. gis_location hierarchical search
                    resource.add_filter(query)
                    query = (table.parent == parent)

                fields = [table.id,
                          table.name,
                          table.level,
                          table.uuid,
                          table.parent,
                          table.lat,
                          table.lon,
                          table.addr_street,
                          table.addr_postcode]
            else:
                output = xml.json_message(False,
                                          400,
                                          "Unsupported filter! Supported filters: ~, =")
                raise HTTP(400, body=output)


        if not fields:
            for field in table.fields:
                fields.append(table[field])

        resource.add_filter(query)

        if filter == "~":
            if (not limit or limit > MAX_SEARCH_RESULTS) and resource.count() > MAX_SEARCH_RESULTS:
               output = json([dict(id="",
                                   name="Search results are over %d. Please input more characters." \
                                   % MAX_SEARCH_RESULTS)])
        elif not parent:
           if (not limit or limit > MAX_RESULTS) and resource.count() > MAX_RESULTS:
               output = json([])

        if output is None:
            output = resource.exporter.json(resource,
                                            start=0,
                                            limit=limit,
                                            fields=fields,
                                            orderby=field)

        response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================

class S3OrganisationSearch(S3Search):
    """
        Search method with specifics for Organisation records
        - searches name & acronym
    """

    def search_json(self, r, **attr):
        """
            JSON search method for S3OrganisationAutocompleteWidget

            @param r: the S3Request
            @param attr: request attributes
        """

        xml = current.manager.xml

        output = None
        request = self.request
        response = current.response
        resource = self.resource
        table = self.table

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = request.vars # should be request.get_vars?

        # JQueryUI Autocomplete uses "term" instead of "value"
        # (old JQuery Autocomplete uses "q" instead of "value")
        value = _vars.value or _vars.term or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = value.lower()

        filter = _vars.filter
        limit = int(_vars.limit or 0)

        if filter and value:

            field = table.name
            field2 = table.acronym

            # Fields to return
            fields = [table.id, field, field2]

            if filter == "~":
                # pr_person Autocomplete
                if " " in value:
                    value1, value2 = value.split(" ", 1)
                    query = (field.lower().like("%" + value1 + "%")) & \
                            (field2.lower().like("%" + value2 + "%"))
                else:
                    query = (field.lower().like("%" + value + "%")) | \
                            (field2.lower().like("%" + value + "%"))

            else:
                output = xml.json_message(False,
                                          400,
                                          "Unsupported filter! Supported filters: ~")
                raise HTTP(400, body=output)

        resource.add_filter(query)

        if filter == "~":
            if (not limit or limit > MAX_SEARCH_RESULTS) and resource.count() > MAX_SEARCH_RESULTS:
               output = json([dict(id="",
                                   name="Search results are over %d. Please input more characters." \
                                   % MAX_SEARCH_RESULTS)])

        if output is None:
            output = resource.exporter.json(resource,
                                            start=0,
                                            limit=limit,
                                            fields=fields,
                                            orderby=field)

        response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================

class S3PersonSearch(S3Search):
    """
        Search method with specifics for Person records (full name search)
    """

    def search_json(self, r, **attr):
        """
            JSON search method for S3PersonAutocompleteWidget

            @param r: the S3Request
            @param attr: request attributes
        """

        xml = current.manager.xml

        output = None
        request = self.request
        response = current.response
        resource = self.resource
        table = self.table

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = request.vars # should be request.get_vars?

        # JQueryUI Autocomplete uses "term" instead of "value"
        # (old JQuery Autocomplete uses "q" instead of "value")
        value = _vars.value or _vars.term or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = value.lower()

        filter = _vars.filter
        limit = int(_vars.limit or 0)

        if filter and value:

            field = table.first_name
            field2 = table.middle_name
            field3 = table.last_name

            # Fields to return
            fields = [table.id, field, field2, field3]

            if filter == "~":
                # pr_person Autocomplete
                if " " in value:
                    value1, value2 = value.split(" ", 1)
                    query = (field.lower().like("%" + value1 + "%")) & \
                            (field2.lower().like("%" + value2 + "%")) | \
                            (field3.lower().like("%" + value2 + "%"))
                else:
                    query = ((field.lower().like("%" + value + "%")) | \
                            (field2.lower().like("%" + value + "%")) | \
                            (field3.lower().like("%" + value + "%")))

            else:
                output = xml.json_message(False,
                                          400,
                                          "Unsupported filter! Supported filters: ~")
                raise HTTP(400, body=output)

        resource.add_filter(query)

        if filter == "~":
            if (not limit or limit > MAX_SEARCH_RESULTS) and resource.count() > MAX_SEARCH_RESULTS:
               output = json([dict(id="",
                                   name="Search results are over %d. Please input more characters." \
                                   % MAX_SEARCH_RESULTS)])

        if output is None:
            output = resource.exporter.json(resource,
                                            start=0,
                                            limit=limit,
                                            fields=fields,
                                            orderby=field)

        response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================

class S3PentitySearch(S3Search):
    """
        Search method with specifics for Pentity records (full name search)
    """

    def search_json(self, r, **attr):
        """
            Legacy JSON search method (for autocomplete-widgets)

            @param r: the S3Request
            @param attr: request attributes
        """


        xml = current.manager.xml

        output = None
        request = self.request
        response = current.response
        resource = self.resource
        table = self.table

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = request.vars # should be request.get_vars?

        # JQueryUI Autocomplete uses "term" instead of "value"
        # (old JQuery Autocomplete uses "q" instead of "value")
        value = _vars.value or _vars.term or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = value.lower()

        filter = _vars.filter
        limit = int(_vars.limit or 0)

        # Fields to return
        if filter and value:

            field = current.db.pr_person.first_name
            field2 = current.db.pr_person.middle_name
            field3 = current.db.pr_person.last_name

            if filter == "~":
                # pr_person Autocomplete
                if " " in value:
                    value1, value2 = value.split(" ", 1)
                    query = (field.lower().like("%" + value1 + "%")) & \
                            (field2.lower().like("%" + value2 + "%")) | \
                            (field3.lower().like("%" + value2 + "%"))
                else:
                    query = ((field.lower().like("%" + value + "%")) | \
                            (field2.lower().like("%" + value + "%")) | \
                            (field3.lower().like("%" + value + "%")))
            else:
                output = xml.json_message(False,
                                          400,
                                          "Unsupported filter! Supported filters: ~")
                raise HTTP(400, body=output)

        resource.add_filter(query)
        resource.add_filter(current.db.pr_person.pe_id == table.pe_id)

        output = resource.exporter.json(resource, start=0, limit=limit,
                                        fields=[table.pe_id], orderby=field)
        items = jsonlib.loads(output)

        # AT: group
        if filter and value:
            field = current.db.pr_group.name
            query = field.lower().like("%" + value + "%")
            resource.clear_query()
            resource.add_filter(query)
            resource.add_filter(current.db.pr_group.pe_id == table.pe_id)
            output = resource.exporter.json(resource,
                                            start=0,
                                            limit=limit,
                                            fields=[table.pe_id],
                                            orderby=field)
            items += jsonlib.loads(output)

        items = [ { "id" : item[u'pe_id'],
                    "name" : self.pentity_represent(item[u'pe_id']) }
                  for item in items ]
        output = jsonlib.dumps(items)

        response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================
