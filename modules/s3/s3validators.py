# -*- coding: utf-8 -*-

""" Custom Validators

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2012 Sahana Software Foundation
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

__all__ = ["single_phone_number_pattern",
           "multi_phone_number_pattern",
           "s3_single_phone_requires",
           "s3_phone_requires",
           "IS_LAT",
           "IS_LON",
           "IS_INT_AMOUNT",
           "IS_FLOAT_AMOUNT",
           "IS_HTML_COLOUR",
           "IS_UTC_OFFSET",
           "IS_UTC_DATETIME",
           "IS_UTC_DATETIME_IN_RANGE",
           "IS_ONE_OF",
           "IS_ONE_OF_EMPTY",
           "IS_ONE_OF_EMPTY_SELECT",
           "IS_NOT_ONE_OF",
           "IS_LOCATION",
           "IS_LOCATION_SELECTOR",
           "IS_SITE_SELECTOR",
           "IS_ADD_PERSON_WIDGET",
           "IS_ACL",
           "QUANTITY_INV_ITEM",
           "IS_IN_SET_LAZY"]

import time
import re
from datetime import datetime, timedelta
from gluon import current, Field,  IS_MATCH, IS_NOT_IN_DB, IS_IN_SET, IS_INT_IN_RANGE, IS_FLOAT_IN_RANGE
from gluon.validators import Validator
from gluon.storage import Storage

def translate(text):
    if text is None:
        return None
    elif isinstance(text, (str, unicode)):
        from globals import current
        if hasattr(current, "T"):
            return str(current.T(text))
    return str(text)

def options_sorter(x, y):
    return (str(x[1]).upper() > str(y[1]).upper() and 1) or -1

# -----------------------------------------------------------------------------
# Phone number requires
# Multiple phone numbers can be separated by comma, slash, semi-colon.
# (Semi-colon appears in Brazil OSM data.)
# @ToDo: Need to beware of separators used inside phone numbers
# (e.g. 555-1212, ext 9), so may need fancier validation if we see that.
# @ToDo: Add tooltip giving list syntax, and warning against above.
# (Current use is in importing OSM files, so isn't interactive.)
# @ToDo: Code that should only have a single # should use
# s3_single_phone_requires. Check what messaging assumes.
phone_number_pattern = "\+?\s*[\s\-\.\(\)\d]+(?:(?: x| ext)\s?\d{1,5})?"
single_phone_number_pattern = "%s$" % phone_number_pattern
multi_phone_number_pattern = "%s(\s*(,|/|;)\s*%s)*$" % (phone_number_pattern,
                                                        phone_number_pattern)

s3_single_phone_requires = IS_MATCH(single_phone_number_pattern)
s3_phone_requires = IS_MATCH(multi_phone_number_pattern,
                             error_message=current.T("Invalid phone number!"))

# -----------------------------------------------------------------------------
class IS_LAT(object):
    """
        example:

        INPUT(_type="text", _name="name", requires=IS_LAT())

        latitude has to be in degrees between -90 & 90
    """
    def __init__(self,
                 error_message = "Latitude/Northing should be between -90 & 90!"
                ):
        self.minimum = -90
        self.maximum = 90
        self.error_message = error_message

    def __call__(self, value):
        try:
            value = float(value)
            if self.minimum <= value <= self.maximum:
                return (value, None)
        except ValueError:
            pass
        return (value, self.error_message)

class IS_LON(object):
    """
        example:

        INPUT(_type="text", _name="name", requires=IS_LON())

        longitude has to be in degrees between -180 & 180
    """
    def __init__(self,
                 error_message = "Longitude/Easting should be between -180 & 180!"
                ):
        self.minimum = -180
        self.maximum = 180
        self.error_message = error_message

    def __call__(self, value):
        try:
            value = float(value)
            if self.minimum <= value <= self.maximum:
                return (value, None)
        except ValueError:
            pass
        return (value, self.error_message)


# -----------------------------------------------------------------------------
class IS_INT_AMOUNT(IS_INT_IN_RANGE):
    """
        Validation, widget and representation of
        integer-values with thousands-separators
    """

    def __init__(self,
                 minimum=None,
                 maximum=None,
                 error_message=None):

        IS_INT_IN_RANGE.__init__(self,
                                 minimum=minimum,
                                 maximum=maximum,
                                 error_message=error_message)

    def __call__(self, value):

        thousands_sep = ","
        value = str(value).replace(thousands_sep, "")
        return IS_INT_IN_RANGE.__call__(self, value)

    @staticmethod
    def represent(value):
        if value is None:
            return ""
        ts = current.deployment_settings.get_L10n_thousands_separator()
        if not ts:
            thousands_separator = ""
        else:
            thousands_separator = ","
        return format(int(value), "%sd" % thousands_separator)

    @staticmethod
    def widget(f, v, **attributes):
        from gluon.sqlhtml import StringWidget
        attr = Storage(attributes)
        classes = attr.get("_class", "").split(" ")
        classes = " ".join([c for c in classes if c != "integer"])
        _class = "%s int_amount" % classes
        attr.update(_class=_class)
        return StringWidget.widget(f, v, **attr)

# -----------------------------------------------------------------------------
class IS_FLOAT_AMOUNT(IS_FLOAT_IN_RANGE):
    """
        Validation, widget and representation of
        float-values with thousands-separators
    """

    def __init__(self,
                 minimum=None,
                 maximum=None,
                 error_message=None,
                 dot='.'):

        IS_FLOAT_IN_RANGE.__init__(self,
                                   minimum=minimum,
                                   maximum=maximum,
                                   error_message=error_message,
                                   dot=dot)

    def __call__(self, value):

        thousands_sep = ","
        value = str(value).replace(thousands_sep, "")
        return IS_FLOAT_IN_RANGE.__call__(self, value)

    @staticmethod
    def represent(value, precision=None):
        if value is None:
            return ""
        ts = current.deployment_settings.get_L10n_thousands_separator()
        if not ts:
            thousands_separator = ""
        else:
            thousands_separator = ","
        if precision is not None:
            fl = format(float(value), "%s.%df" % (thousands_separator, precision))
        else:
            fl = format(float(value), "%sf" % thousands_separator).rstrip("0")
            if fl[-1] == ".":
                fl += "0"
        return fl

    @staticmethod
    def widget(f, v, **attributes):
        from gluon.sqlhtml import StringWidget
        attr = Storage(attributes)
        classes = attr.get("_class", "").split(" ")
        classes = " ".join([c for c in classes if c != "double"])
        _class = "%s float_amount" % classes
        attr.update(_class=_class)
        return StringWidget.widget(f, v, **attr)

# -----------------------------------------------------------------------------
class IS_HTML_COLOUR(IS_MATCH):
    """
        example::

        INPUT(_type="text", _name="name", requires=IS_HTML_COLOUR())
    """

    def __init__(self,
                 error_message="must be a 6 digit hex code!"
                ):
        IS_MATCH.__init__(self, "^[0-9a-fA-F]{6}$", error_message)


# -----------------------------------------------------------------------------
regex1 = re.compile("[\w_]+\.[\w_]+")
regex2 = re.compile("%\((?P<name>[^\)]+)\)s")

class IS_ONE_OF_EMPTY(Validator):
    """
        Filtered version of IS_IN_DB():

        validates a given value as key of another table, filtered by the
        'filterby' field for one of the 'filter_opts' options
        (=a selective IS_IN_DB())

        NB Filtering isn't active in GQL.

        For the dropdown representation:

            'label' can be a string template for the record, or a set of field
            names of the fields to be used as option labels, or a function or
            lambda to create an option label from the respective record (which
            has to return a string, of course). The function will take the
            record as an argument.

            No 'options' method as designed to be called next to an
            Autocomplete field so don't download a large dropdown
            unnecessarily.
    """

    def __init__(self,
                 dbset,
                 field,
                 label=None,
                 filterby=None,
                 filter_opts=None,
                 not_filterby=None,
                 not_filter_opts=None,
                 error_message="invalid value!",
                 orderby=None,
                 groupby=None,
                 left=None,
                 multiple=False,
                 zero="",
                 sort=False,
                 _and=None,
                ):

        if hasattr(dbset, "define_table"):
            self.dbset = dbset()
        else:
            self.dbset = dbset
        (ktable, kfield) = str(field).split(".")
        if not label:
            label = "%%(%s)s" % kfield
        if isinstance(label, str):
            if regex1.match(str(label)):
                label = "%%(%s)s" % str(label).split(".")[-1]
            ks = regex2.findall(label)
            if not kfield in ks:
                ks += [kfield]
            fields = ["%s.%s" % (ktable, k) for k in ks]
        else:
            ks = [kfield]
            fields =[str(f) for f in self.dbset._db[ktable]]
        self.fields = fields
        self.label = label
        self.ktable = ktable
        if not kfield or not len(kfield):
            self.kfield = "id"
        else:
            self.kfield = kfield
        self.ks = ks
        self.error_message = error_message
        self.theset = None
        self.orderby = orderby
        self.groupby = groupby
        self.left = left
        self.multiple = multiple
        self.zero = zero
        self.sort = sort
        self._and = _and

        self.filterby = filterby
        self.filter_opts = filter_opts
        self.not_filterby = not_filterby
        self.not_filter_opts = not_filter_opts

    def set_self_id(self, id):
        if self._and:
            self._and.record_id = id

    def set_filter(self,
                   filterby = None,
                   filter_opts = None,
                   not_filterby = None,
                   not_filter_opts = None):
        """
            This can be called from prep to apply a filter base on
            data in the record or the primary resource id.
        """
        if filterby:
            self.filterby = filterby
        if filter_opts:
            self.filter_opts = filter_opts
        if not_filterby:
            self.not_filterby = not_filterby
        if not_filter_opts:
            self.not_filter_opts = not_filter_opts

    def build_set(self):

        dbset = self.dbset
        db = dbset._db
        if self.ktable in db:

            table = db[self.ktable]
            auth = current.auth

            if self.fields == "all":
                fields = [f for f in table if isinstance(f, Field)]
            else:
                fieldnames = [f.split(".")[1] if "." in f else f for f in self.fields]
                fields = [table[k] for k in fieldnames if k in table.fields]
            if db._dbname not in ("gql", "gae"):
                orderby = self.orderby or reduce(lambda a, b: a|b, fields)
                groupby = self.groupby
                # Caching breaks Colorbox dropdown refreshes
                #dd = dict(orderby=orderby, groupby=groupby, cache=(current.cache.ram, 60))
                dd = dict(orderby=orderby, groupby=groupby)
                query = auth.s3_accessible_query("read", table)
                if "deleted" in table:
                    query = ((table["deleted"] == False) & query)
                if self.filterby and self.filterby in table:
                    if self.filter_opts:
                        query = query & (table[self.filterby].belongs(self.filter_opts))
                    if not self.orderby:
                        dd.update(orderby=table[self.filterby])
                if self.not_filterby and self.not_filterby in table and self.not_filter_opts:
                    query = query & (~(table[self.not_filterby].belongs(self.not_filter_opts)))
                    if not self.orderby:
                        dd.update(orderby=table[self.filterby])
                if self.left is not None:
                    dd.update(left=self.left)
                records = dbset(query).select(*fields, **dd)
            else:
                # Note this does not support filtering.
                orderby = self.orderby or \
                          reduce(lambda a, b: a|b, (f for f in fields
                                                    if not f.name == "id"))
                #dd = dict(orderby=orderby, cache=(current.cache.ram, 60))
                dd = dict(orderby=orderby)
                records = dbset.select(db[self.ktable].ALL, **dd)
            self.theset = [str(r[self.kfield]) for r in records]
            #labels = []
            label = self.label
            try:
                labels = map(label, records)
            except TypeError:
                if isinstance(label, str):
                    labels = map(lambda r: label % dict(r), records)
                elif isinstance(label, (list, tuple)):
                    labels = map(lambda r: \
                                 " ".join([r[l] for l in label if l in r]),
                                 records)
                elif callable(label):
                    # Is a function
                    labels = map(label, records)
                elif "name" in table:
                    labels = map(lambda r: r.name, records)
                else:
                    labels = map(lambda r: r[self.kfield], records)
            self.labels = labels
        else:
            self.theset = None
            self.labels = None

    # Removed as we don't want any options downloaded unnecessarily
    #def options(self):

    def __call__(self, value):

        try:
            table = self.dbset._db[self.ktable]
            deleted_q = ("deleted" in table) and (table["deleted"] == False) or False
            filter_opts_q = False
            if self.filterby and self.filterby in table:
                if self.filter_opts:
                    filter_opts_q = table[self.filterby].belongs(self.filter_opts)

            if self.multiple:
                if isinstance(value, list):
                    values = value
                elif isinstance(value, basestring) and \
                     value[0] == "|" and value[-1] == "|":
                    values = value[1:-1].split("|")
                elif value:
                    values = [value]
                else:
                    values = []

                if self.theset:
                    if not [x for x in values if not x in self.theset]:
                        return (values, None)
                    else:
                        return (value, self.error_message)
                else:
                    for v in values:
                        q = (table[self.kfield] == v)
                        query = query is not None and query | q or q
                    if filter_opts_q != False:
                        query = query is not None and \
                                (filter_opts_q & (query)) or filter_opts_q
                    if deleted_q != False:
                        query = query is not None and \
                                (deleted_q & (query)) or deleted_q
                    if self.dbset(query).count() < 1:
                        return (value, self.error_message)
                    return (values, None)
            elif self.theset:
                if value in self.theset:
                    if self._and:
                        return self._and(value)
                    else:
                        return (value, None)
            else:
                values = [value]
                query = None
                for v in values:
                    q = (table[self.kfield] == v)
                    query = query is not None and query | q or q
                if filter_opts_q != False:
                    query = query is not None and \
                            (filter_opts_q & (query)) or filter_opts_q
                if deleted_q != False:
                    query = query is not None and \
                            (deleted_q & (query)) or deleted_q
                if self.dbset(query).count():
                    if self._and:
                        return self._and(value)
                    else:
                        return (value, None)
        except:
            pass

        return (value, self.error_message)


# -----------------------------------------------------------------------------
class IS_ONE_OF(IS_ONE_OF_EMPTY):

    """
        Extends IS_ONE_OF_EMPTY by restoring the 'options' method.
    """

    def options(self):

        self.build_set()
        items = [(k, self.labels[i]) for (i, k) in enumerate(self.theset)]
        if self.sort:
            items.sort(options_sorter)
        if self.zero != None and not self.multiple:
            items.insert(0, ("", self.zero))
        return items


# -----------------------------------------------------------------------------
class IS_ONE_OF_EMPTY_SELECT(IS_ONE_OF_EMPTY):

    """
        Extends IS_ONE_OF_EMPTY by displaying an empty SELECT (instead of INPUT)
    """

    def options(self):
        return [("", "")]

# -----------------------------------------------------------------------------
class IS_NOT_ONE_OF(IS_NOT_IN_DB):

    """
        Filtered version of IS_NOT_IN_DB()
            - understands the 'deleted' field.
            - makes the field unique (amongst non-deleted field)

        Example:
            - INPUT(_type="text", _name="name", requires=IS_NOT_ONE_OF(db, db.table))
    """

    def __call__(self, value):
        value = str(value)
        if not value.strip():
            return (value, translate(self.error_message))
        if value in self.allowed_override:
            return (value, None)
        (tablename, fieldname) = str(self.field).split(".")
        dbset = self.dbset
        table = dbset.db[tablename]
        field = table[fieldname]
        query = (field == value)
        rows = dbset(query,
                     ignore_common_filters = self.ignore_common_filters).select(limitby=(0, 1))
        if "deleted" in table:
            query = (table["deleted"] == False) & query
        if len(rows) > 0:
            if isinstance(self.record_id, dict):
                for f in self.record_id:
                    if str(getattr(rows[0], f)) != str(self.record_id[f]):
                        return (value, translate(self.error_message))
            elif str(rows[0][table._id.name]) != str(self.record_id):
                    return (value, translate(self.error_message))
        return (value, None)

# -----------------------------------------------------------------------------
class IS_LOCATION(Validator):
    """
        Allow all locations, or locations by level.

        Optimized for use within the S3LocationSelectorWidget's L0 Dropdown.
    """

    def __init__(self,
                 level = None,
                 error_message = None
                ):
        T = current.T
        self.level = level # can be a List or a single element
        self.error_message = error_message or T("Invalid Location!")

    def __call__(self, value):
        db = current.db
        table = db.gis_location
        level = self.level

        if level and level == "L0":
            # Use cached countries. This returns name if id is for a country.
            have_location = gis.get_country(value)
        else:
            query = (table.id == value) & (table.deleted == False)
            if level:
                if isinstance(level, list):
                    query = query & (table.level.belongs(level))
                else:
                    query = query & (table.level == level)
            have_location = db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if have_location:
            return (value, None)
        else:
            return (value, self.error_message)

# -----------------------------------------------------------------------------
class IS_LOCATION_SELECTOR(Validator):
    """
        Designed for use within the S3LocationSelectorWidget.
        For Create forms, this will create a new location from the additional fields
        For Update forms, this will normally just check that we have a valid location_id FK
        - although there is the option to create a new location there too, in which case it acts as-above.

        @ToDo: Audit
    """

    def __init__(self,
                 error_message = None,
                ):
        T = current.T
        self.error_message = error_message or T("Invalid Location!")
        self.no_parent = T("Need to have all levels filled out in mode strict!")
        auth = current.auth
        self.no_permission = auth.messages.access_denied

    def __call__(self, value):
        db = current.db
        auth = current.auth
        gis = current.gis
        table = db.gis_location

        try:
            # Is this an ID?
            value = int(value)
            # Yes: This must be an Update form
            if not auth.s3_has_permission("update", table, record_id=value):
                return (value, self.no_permission)
            # Check that this is a valid location_id
            query = (table.id == value) & \
                    (table.deleted == False) & \
                    (table.level == None) # NB Specific Locations only
            location = db(query).select(table.id,
                                        limitby=(0, 1)).first()
            if location:
                # Update the record, in case changes have been made
                location = self._process_values()
                # onvalidation
                form = Storage()
                form.vars = location
                gis.wkt_centroid(form)
                db(table.id == value).update(name = location.name,
                                             lat = location.lat,
                                             lon = location.lon,
                                             addr_street = location.street,
                                             addr_postcode = location.postcode,
                                             parent = location.parent)
                # onaccept
                gis.update_location_tree(value, location.parent)
                return (value, None)
        except:
            # Create form
            if not auth.s3_has_permission("create", table):
                return (None, self.no_permission)
            location = self._process_values()
            strict = gis.get_strict_hierarchy(location)
            if strict and not location.parent:
                return (value, self.no_parent)
            if location.name or location.lat or location.lon or \
               location.street or location.postcode or location.parent:
                # onvalidation
                form = Storage()
                form.vars = location
                gis.wkt_centroid(form)
                value = table.insert(name = location.name,
                                     lat = location.lat,
                                     lon = location.lon,
                                     addr_street = location.street,
                                     addr_postcode = location.postcode,
                                     parent = location.parent,
                                     wkt = form.vars.wkt,
                                     lon_min = form.vars.lon_min,
                                     lon_max = form.vars.lon_max,
                                     lat_min = form.vars.lat_min,
                                     lat_max = form.vars.lat_max
                                     )
                # onaccept
                gis.update_location_tree(value, location.parent)
                return (value, None)
            else:
                return (None, None)

        return (value, self.error_message)

    def _process_values(self):
        """
            Read the request.vars & prepare for a record insert/update

            Note: This is also used by IS_SITE_SELECTOR()
        """

        db = current.db
        s3db = current.s3db
        auth = current.auth
        gis = current.gis
        response = current.response
        session = current.session

        table = s3db.gis_location

        vars = current.request.vars
        L0 = vars.get("gis_location_L0", None)

        # Are we allowed to create Locations?
        if not auth.s3_has_permission("create", table):
            return (None, self.no_permission)
        # What level of hierarchy are we allowed to edit?
        if auth.s3_has_role(session.s3.system_roles.MAP_ADMIN):
            # 'MapAdmin' always has permission to edit hierarchy locations
            L1_allowed = True
            L2_allowed = True
            L3_allowed = True
            L4_allowed = True
            L5_allowed = True
        else:
            if L0:
                ctable = s3db.gis_config
                query = (ctable.region_location_id == L0)
                config = db(query).select(ctable.edit_L1,
                                          ctable.edit_L2,
                                          ctable.edit_L3,
                                          ctable.edit_L4,
                                          ctable.edit_L5,
                                          limitby=(0, 1)).first()
            if L0 and config:
                # Lookup each level individually
                L1_allowed = config.edit_L1
                L2_allowed = config.edit_L2
                L3_allowed = config.edit_L3
                L4_allowed = config.edit_L4
                L5_allowed = config.edit_L5
            else:
                # default is deployment_setting
                L1_allowed = current.deployment_settings.get_gis_edit_lx()
                L2_allowed = L1_allowed
                L3_allowed = L1_allowed
                L4_allowed = L1_allowed
                L5_allowed = L1_allowed

        # We don't need to do onvalidation of the Location Hierarchy records
        # separately as we don't have anything extra to validate than we have
        # done already

        # We don't use the full onaccept as we don't need to
        onaccept = gis.update_location_tree

        L1 = vars.get("gis_location_L1", None)
        L2 = vars.get("gis_location_L2", None)
        L3 = vars.get("gis_location_L3", None)
        L4 = vars.get("gis_location_L4", None)
        L5 = vars.get("gis_location_L5", None)

        # Check if we have parents to create
        # L1
        if L1:
            try:
                # Is this an ID?
                int(L1)
                # Do we need to update it's parent?
                if L0:
                    parent = L0
                    query = (table.id == L1)
                    location = db(query).select(table.parent,
                                                limitby=(0, 1)).first()
                    if location and (location.parent != parent):
                        db(query).update(parent=parent)
                        onaccept(L1, parent)
            except:
                # Name
                # Test for duplicates
                query = (table.name == L1) & (table.level == "L1")
                if L0:
                    query = query & (table.parent == L0)
                location = db(query).select(table.id,
                                            limitby=(0, 1)).first()
                if location:
                    # Use Existing record
                    L1 = location.id
                elif L0 and L1_allowed:
                    parent = L0
                    L1 = table.insert(name=L1, level="L1", parent=parent)
                    onaccept(L1, parent)
                elif L1_allowed:
                    L1 = table.insert(name=L1, level="L1")
                    onaccept(L1)
                else:
                    L1 = None
        # L2
        if L2:
            try:
                # Is this an ID?
                int(L2)
                # Do we need to update it's parent?
                if L1:
                    parent = L1
                    query = (table.id == L2)
                    location = db(query).select(table.parent,
                                                limitby=(0, 1)).first()
                    if location and (location.parent != parent):
                        db(query).update(parent=parent)
                        onaccept(L2, parent)
            except:
                # Name
                # Test for duplicates
                # @ToDo: Also check for L2 parenting direct to L0
                query = (table.name == L2) & (table.level == "L2")
                if L1:
                    query = query & (table.parent == L1)
                location = db(query).select(table.id,
                                            limitby=(0, 1)).first()
                if location:
                    # Use Existing record
                    L2 = location.id
                elif L1 and L2_allowed:
                    parent = L1
                    L2 = table.insert(name=L2, level="L2", parent=parent)
                    onaccept(L2, parent)
                elif L0 and L2_allowed:
                    parent = L0
                    L2 = table.insert(name=L2, level="L2", parent=parent)
                    onaccept(L2, parent)
                elif L2_allowed:
                    L2 = table.insert(name=L2, level="L2")
                    onaccept(L2)
                else:
                    L2 = None
        # L3
        if L3:
            try:
                # Is this an ID?
                int(L3)
                # Do we need to update it's parent?
                if L2:
                    parent = L2
                    query = (table.id == L3)
                    location = db(query).select(table.parent,
                                                limitby=(0, 1)).first()
                    if location and (location.parent != parent):
                        db(query).update(parent=parent)
                        onaccept(L3, parent)
            except:
                # Name
                # Test for duplicates
                # @ToDo: Also check for L3 parenting direct to L0/1
                query = (table.name == L3) & (table.level == "L3")
                if L2:
                    query = query & (table.parent == L2)
                location = db(query).select(table.id,
                                            limitby=(0, 1)).first()
                if location:
                    # Use Existing record
                    L3 = location.id
                elif L2 and L3_allowed:
                    parent = L2
                    L3 = table.insert(name=L3, level="L3", parent=parent)
                    onaccept(L3, parent)
                elif L1 and L3_allowed:
                    parent = L1
                    L3 = table.insert(name=L3, level="L3", parent=parent)
                    onaccept(L3, parent)
                elif L0 and L3_allowed:
                    parent = L0
                    L3 = table.insert(name=L3, level="L3", parent=parent)
                    onaccept(L3, parent)
                elif L3_allowed:
                    L3 = table.insert(name=L3, level="L3")
                    onaccept(L3)
                else:
                    L3 = None
        # L4
        if L4:
            try:
                # Is this an ID?
                int(L4)
                # Do we need to update it's parent?
                if L3:
                    parent = L3
                    query = (table.id == L4)
                    location = db(query).select(table.parent,
                                                limitby=(0, 1)).first()
                    if location and (location.parent != parent):
                        db(query).update(parent=parent)
                        onaccept(L4, parent)
            except:
                # Name
                # Test for duplicates
                # @ToDo: Also check for L4 parenting direct to L0/1/2
                query = (table.name == L4) & (table.level == "L4")
                if L3:
                    query = query & (table.parent == L3)
                location = db(query).select(table.id,
                                            limitby=(0, 1)).first()
                if location:
                    # Use Existing record
                    L4 = location.id
                elif L3 and L4_allowed:
                    parent = L3
                    L4 = table.insert(name=L4, level="L4", parent=parent)
                    onaccept(L4, parent)
                elif L2 and L4_allowed:
                    parent = L2
                    L4 = table.insert(name=L4, level="L4", parent=parent)
                    onaccept(L4, parent)
                elif L1 and L4_allowed:
                    parent = L1
                    L4 = table.insert(name=L4, level="L4", parent=parent)
                    onaccept(L4, parent)
                elif L0 and L4_allowed:
                    parent = L0
                    L4 = table.insert(name=L4, level="L4", parent=parent)
                    onaccept(L4, parent)
                elif L4_allowed:
                    L4 = table.insert(name=L4, level="L4")
                    onaccept(L4)
                else:
                    L4 = None
        # L5
        if L5:
            try:
                # Is this an ID?
                int(L5)
                # Do we need to update it's parent?
                if L4:
                    parent = L4
                    query = (table.id == L5)
                    location = db(query).select(table.parent,
                                                limitby=(0, 1)).first()
                    if location and (location.parent != parent):
                        db(query).update(parent=parent)
                        onaccept(L5, parent)
            except:
                # Name
                # Test for duplicates
                # @ToDo: Also check for L5 parenting direct to L0/1/2/3
                query = (table.name == L5) & (table.level == "L5")
                if L4:
                    query = query & (table.parent == L4)
                location = db(query).select(table.id,
                                            limitby=(0, 1)).first()
                if location:
                    # Use Existing record
                    L5 = location.id
                elif L4 and L5_allowed:
                    parent = L4
                    L5 = table.insert(name=L5, level="L5", parent=parent)
                    onaccept(L5, parent)
                elif L3 and L5_allowed:
                    parent = L3
                    L5 = table.insert(name=L5, level="L5", parent=parent)
                    onaccept(L5, parent)
                elif L2 and L5_allowed:
                    parent = L2
                    L5 = table.insert(name=L5, level="L5", parent=parent)
                    onaccept(L5, parent)
                elif L1 and L5_allowed:
                    parent = L1
                    L5 = table.insert(name=L5, level="L5", parent=parent)
                    onaccept(L5, parent)
                elif L0 and L5_allowed:
                    parent = L0
                    L5 = table.insert(name=L5, level="L5", parent=parent)
                    onaccept(L5, parent)
                elif L5_allowed:
                    L5 = table.insert(name=L5, level="L5")
                    onaccept(L5)
                else:
                    L5 = None

        # Check if we have a specific location to create
        name = vars.get("gis_location_name", None)
        lat = vars.get("gis_location_lat", None)
        lon = vars.get("gis_location_lon", None)
        street = vars.get("gis_location_street", None)
        postcode = vars.get("gis_location_postcode", None)
        parent = L5 or L4 or L3 or L2 or L1 or L0 or None

        # Move vars into form.
        form = Storage()
        form.vars = Storage()
        vars = form.vars
        vars.lat = lat
        vars.lon = lon
        # onvalidation
        gis.wkt_centroid(form)
        return Storage(
                        name=name,
                        lat=lat, lon=lon,
                        street=street,
                        postcode=postcode,
                        parent=parent,
                        wkt = vars.wkt,
                        lon_min = vars.lon_min,
                        lon_max = vars.lon_max,
                        lat_min = vars.lat_min,
                        lat_max = vars.lat_max
                      )

# -----------------------------------------------------------------------------
class IS_SITE_SELECTOR(IS_LOCATION_SELECTOR):
    """
        Extends the IS_LOCATION_SELECTOR() validator to transparently support
        Sites of the specified type.
        Note that these cannot include any other mandatory fields other than Name & location_id

        Designed for use within the ???S3LocationSelectorWidget.
        For Create forms, this will create a new site & location from the additional fields
        For Update forms, this will normally just check that we have a valid site_id FK
        - although there is the option to create a new location there too, in which case it acts as-above.

        @ToDo: Audit
    """

    def __init__(self,
                 site_type = "project_site",
                 error_message = None,
                ):
        T = current.T
        self.error_message = error_message or T("Invalid Site!")
        self.no_parent = T("Need to have all levels filled out in mode strict!")
        auth = current.auth
        self.no_permission = auth.messages.access_denied
        self.site_type = site_type

    def __call__(self, value):
        db = current.db
        auth = current.auth
        gis = current.gis
        table = db.gis_location
        stable = db[self.site_type]

        try:
            # Is this an ID?
            value = int(value)
            # Yes: This must be an Update form
            if not auth.s3_has_permission("update", stable, record_id=value):
                return (value, self.no_permission)
            # Check that this is a valid site_id
            query = (stable.id == value) & \
                    (stable.deleted == False)
            site = db(query).select(stable.id,
                                    stable.name,
                                    stable.location_id,
                                    limitby=(0, 1)).first()
            if site and site.location_id:
                # Update the location, in case changes have been made
                location = self._process_values()
                # Location onvalidation
                form = Storage()
                form.vars = location
                gis.wkt_centroid(form)
                # Location update
                lquery = (table.id == site.location_id)
                db(lquery).update(name = location.name,
                                  lat = location.lat,
                                  lon = location.lon,
                                  addr_street = location.street,
                                  addr_postcode = location.postcode,
                                  parent = location.parent)
                # Location onaccept
                gis.update_location_tree(site.location_id, location.parent)

                if stable.name != location.name:
                    # Site Name has changed
                    db(query).update(name = location.name)
                return (value, None)
        except:
            # Create form
            if not auth.s3_has_permission("create", stable):
                return (None, self.no_permission)
            location = self._process_values()
            strict = gis.get_strict_hierarchy(location)
            if strict and not location.parent:
                return (value, self.no_parent)
            if location.name or location.lat or location.lon or \
               location.street or location.postcode or location.parent:
                # Location onvalidation
                form = Storage()
                form.vars = location
                gis.wkt_centroid(form)
                # Location creation
                location_id = table.insert(name = location.name,
                                           lat = location.lat,
                                           lon = location.lon,
                                           addr_street = location.street,
                                           addr_postcode = location.postcode,
                                           parent = location.parent,
                                           wkt = form.vars.wkt,
                                           lon_min = form.vars.lon_min,
                                           lon_max = form.vars.lon_max,
                                           lat_min = form.vars.lat_min,
                                           lat_max = form.vars.lat_max
                                           )
                # Location onaccept
                gis.update_location_tree(location_id, location.parent)
                # Site creation
                value = stable.insert(name = location.name,
                                      location_id = location_id)
                return (value, None)
            else:
                return (None, None)

        return (value, self.error_message)

# -----------------------------------------------------------------------------
class IS_ADD_PERSON_WIDGET(Validator):

    def __init__(self,
                 error_message=None,
                 mark_required=True):

        self.error_message = error_message or \
                             current.T("Could not add person record")

        self.mark_required = mark_required

    def __call__(self, value):

        db = current.db
        manager = current.manager
        request = current.request
        T = current.T

        try:
            person_id = int(value)
        except:
            person_id = None

        ptable = db.pr_person
        table = db.pr_contact
        def email_validate(value, person_id):
            error_message = T("This email-address is already registered.")
            if not value:
                return (value, None)
            value = value.strip()
            query = (table.deleted != True) & \
                    (table.contact_method == "EMAIL") & \
                    (table.value == value)
            if person_id:
                query = query & \
                        (table.pe_id == ptable.pe_id) & \
                        (ptable.id != person_id)
            email = db(query).select(table.id, limitby=(0, 1)).first()
            if email:
                return value, error_message
            return value, None

        if request.env.request_method == "POST":
            _vars = request.post_vars
            mobile = _vars["mobile_phone"]
            # Validate the phone number
            if _vars.mobile_phone:
                regex = re.compile(single_phone_number_pattern)
                if not regex.match(_vars.mobile_phone):
                    error = T("Invalid phone number")
                    return (person_id, error)
            if person_id:
                # update the person record
                # Values are hard coded, but it looks to work ;)
                data = Storage()
                fields = ["first_name",
                          "middle_name",
                          "last_name",
                          "date_of_birth",
                          "gender",
                          "occupation"]
                for f in fields:
                    if f in _vars and _vars[f]:
                        data[f] = _vars[f]
                if data:
                    db(ptable.id == person_id).update(**data)

                # Now check the contact information
                record = ptable(person_id)
                pe_id = record.pe_id
                if pe_id:
                    # Check to see if the contact details have been set up
                    # First Email
                    record = table(pe_id=pe_id,
                                   contact_method="EMAIL",
                                  )
                    email = _vars["email"]
                    if record and email: # update
                        if email != record.value:
                            db(table.id == record.id).update(value=email)
                    else: # insert
                        table.insert(pe_id=pe_id,
                                             contact_method="EMAIL",
                                             value=email
                                             )
                    # Now mobile phone
                    record = table(pe_id=pe_id,
                                   contact_method="SMS",
                                  )
                    if record: # update
                        if mobile != record.value:
                            db(table.id == record.id).update(value=mobile)
                    else: # insert
                        if mobile: # Don't insert an empty number
                            table.insert(pe_id=pe_id,
                                         contact_method="SMS",
                                         value=mobile
                                        )
                pass
            else:
                # Filter out location_id (location selector form values
                # being processed only after this widget has been validated)
                _vars = Storage([(k, _vars[k])
                                 for k in _vars
                                    if k != "location_id"])
                # Validate the email
                email, error = email_validate(_vars.email, None)
                if error:
                    return (person_id, error)
                # Validate and add the person record
                table = db.pr_person
                for f in table._filter_fields(_vars):
                    value, error = manager.validate(table, None, f, _vars[f])
                    if error:
                        return (None, None)
                person_id = table.insert(**table._filter_fields(_vars))
                # Need to update post_vars here,
                # for some reason this doesn't happen through validation alone
                request.post_vars.update(person_id=str(person_id))
                if person_id:
                    # Update the super-entity
                    manager.model.update_super(table, dict(id=person_id))
                    person = table[person_id]
                    # Add contact information as provided
                    table = db.pr_contact
                    table.insert(pe_id=person.pe_id,
                                contact_method="EMAIL",
                                value=_vars.email)
                    if _vars.mobile_phone:
                        table.insert(pe_id=person.pe_id,
                                    contact_method="SMS",
                                    value=_vars.mobile_phone)
                else:
                    return (person_id, self.error_message)

        return (person_id, None)

# -----------------------------------------------------------------------------
class IS_UTC_OFFSET(Validator):
    """
        Validates a given string value as UTC offset in the format +/-HHMM

        @author: nursix

        @param error_message:   the error message to be returned

        @note:
            all leading parts of the string (before the trailing offset specification)
            will be ignored and replaced by 'UTC ' in the return value, if the string
            passes through.
    """

    def __init__(self,
                 error_message="invalid UTC offset!"
                ):
        self.error_message = error_message

    @staticmethod
    def get_offset_value(offset_str):
        if offset_str and len(offset_str) >= 5 and \
            (offset_str[-5] == "+" or offset_str[-5] == "-") and \
            offset_str[-4:].isdigit():
            offset_hrs = int(offset_str[-5] + offset_str[-4:-2])
            offset_min = int(offset_str[-5] + offset_str[-2:])
            offset = 3600*offset_hrs + 60*offset_min
            return offset
        else:
            return None

    def __call__(self, value):

        if value and isinstance(value, str):
            _offset_str = value.strip()

            offset = self.get_offset_value(_offset_str)

            if offset is not None and offset > -86340 and offset < 86340:
                # Add a leading 'UTC ',
                # otherwise leading '+' and '0' will be stripped away by web2py
                return ("UTC " + _offset_str[-5:], None)

        return (value, self.error_message)


# -----------------------------------------------------------------------------
#
class IS_UTC_DATETIME(Validator):
    """
        Validates a given value as datetime string and returns the
        corresponding UTC datetime.

        Example:
            - INPUT(_type="text", _name="name", requires=IS_UTC_DATETIME())

        @author: nursix

        @param format:          strptime/strftime format template string, for
                                directives refer to your strptime implementation
        @param error_message:   dict of error messages to be returned
        @param utc_offset:      offset to UTC in seconds, if not specified, the
                                value is considered to be UTC
        @param allow_future:    whether future date/times are allowed or not,
                                if set to False, all date/times beyond
                                now+max_future will fail
        @type allow_future:     boolean
        @param max_future:      the maximum acceptable future time interval in
                                seconds from now for unsynchronized local clocks

        @note:
            datetime has to be in the ISO8960 format YYYY-MM-DD hh:mm:ss,
            with an optional trailing UTC offset specified as +/-HHMM
            (+ for eastern, - for western timezones)
    """

    def __init__(self,
                 format=None,
                 error_message=None,
                 utc_offset=None,
                 allow_future=True,
                 max_future=900
                ):

        if format is None:
            self.format = current.deployment_settings.get_L10n_datetime_format()
        else:
            self.format = format

        self.error_message = dict(
            format = "Required format: %s!" % self.format,
            offset = "Invalid UTC offset!",
            future = "Future times not allowed!")

        if error_message and isinstance(error_message, dict):
            self.error_message["format"] = error_message.get("format", None) or self.error_message["format"]
            self.error_message["offset"] = error_message.get("offset", None) or self.error_message["offset"]
            self.error_message["future"] = error_message.get("future", None) or self.error_message["future"]
        elif error_message:
            self.error_message["format"] = error_message

        if utc_offset is None:
            utc_offset = current.session.s3.utc_offset

        validate = IS_UTC_OFFSET()
        offset, error = validate(utc_offset)

        if error:
            self.utc_offset = "UTC +0000" # fallback to UTC
        else:
            self.utc_offset = offset

        self.allow_future = allow_future
        self.max_future = max_future

    def __call__(self, value):

        _dtstr = value.strip()

        if len(_dtstr) > 6 and \
            (_dtstr[-6:-4] == " +" or _dtstr[-6:-4] == " -") and \
            _dtstr[-4:].isdigit():
            # UTC offset specified in dtstr
            dtstr = _dtstr[0:-6]
            _offset_str = _dtstr[-5:]
        else:
            # use default UTC offset
            dtstr = _dtstr
            _offset_str = self.utc_offset

        offset_hrs = int(_offset_str[-5] + _offset_str[-4:-2])
        offset_min = int(_offset_str[-5] + _offset_str[-2:])
        offset = 3600 * offset_hrs + 60 * offset_min

        # Offset must be in range -1439 to +1439 minutes
        if offset < -86340 or offset > 86340:
            return (dt, self.error_message["offset"])

        try:
            (y, m, d, hh, mm, ss, t0, t1, t2) = time.strptime(dtstr, str(self.format))
            dt = datetime(y, m, d, hh, mm, ss)
        except:
            try:
                (y, m, d, hh, mm, ss, t0, t1, t2) = time.strptime(dtstr+":00", str(self.format))
                dt = datetime(y, m, d, hh, mm, ss)
            except:
                return(value, self.error_message["format"])

        if self.allow_future:
            return (dt, None)
        else:
            latest = datetime.utcnow() + timedelta(seconds=self.max_future)
            dt_utc = dt - timedelta(seconds=offset)
            if dt_utc > latest:
                return (dt_utc, self.error_message["future"])
            else:
                return (dt_utc, None)

    def formatter(self, value):

        format = self.format
        offset = IS_UTC_OFFSET.get_offset_value(self.utc_offset)

        if not value:
            return "-"
        elif offset:
            dt = value + timedelta(seconds=offset)
            return dt.strftime(str(format))
        else:
            dt = value
            return dt.strftime(str(format)) + " +0000"


# -----------------------------------------------------------------------------
class IS_UTC_DATETIME_IN_RANGE(Validator):

    def __init__(self,
                 format=None,
                 error_message=None,
                 utc_offset=None,
                 minimum=None,
                 maximum=None):

        if format is None:
            self.format = current.deployment_settings.get_L10n_datetime_format()
        else:
            self.format = format

        self.utc_offset = utc_offset

        self.minimum = minimum
        self.maximum = maximum
        delta = timedelta(seconds=self.delta())
        min_local = minimum and minimum + delta or None
        max_local = maximum and maximum + delta or None

        if error_message is None:
            if minimum is None and maximum is None:
                error_message = "enter date and time"
            elif minimum is None:
                error_message = "enter date and time on or before %(max)s"
            elif maximum is None:
                error_message = "enter date and time on or after %(min)s"
            else:
                error_message = "enter date and time in range %(min)s %(max)s"

        d = dict(min = min_local, max = max_local)
        self.error_message = error_message % d

    def delta(self, utc_offset=None):

        if utc_offset is not None:
            self.utc_offset = utc_offset
        if self.utc_offset is None:
            self.utc_offset = current.session.s3.utc_offset
        validate = IS_UTC_OFFSET()
        offset, error = validate(self.utc_offset)
        if error:
            self.utc_offset = "UTC +0000" # fallback to UTC
        else:
            self.utc_offset = offset
        delta = IS_UTC_OFFSET.get_offset_value(self.utc_offset)
        return delta

    def __call__(self, value):

        val = value.strip()

        # Get UTC offset
        if len(val) > 5 and val[-5] in ("+", "-") and val[-4:].isdigit():
            # UTC offset specified in dtstr
            dtstr = val[0:-5].strip()
            utc_offset = "UTC %s" % val[-5:]
        else:
            # use default UTC offset
            dtstr = val
            utc_offset = self.utc_offset

        # Offset must be in range -2359 to +2359
        offset = self.delta(utc_offset=utc_offset)
        if offset < -86340 or offset > 86340:
            return (val, self.error_message)

        # Convert into datetime object
        try:
            (y, m, d, hh, mm, ss, t0, t1, t2) = \
                time.strptime(dtstr, str(self.format))
            dt = datetime(y, m, d, hh, mm, ss)
        except:
            try:
                (y, m, d, hh, mm, ss, t0, t1, t2) = \
                    time.strptime(dtstr+":00", str(self.format))
                dt = datetime(y, m, d, hh, mm, ss)
            except:
                return(value, self.error_message)

        # Validate
        dt_utc = dt - timedelta(seconds=offset)
        if self.minimum and dt_utc < self.minimum or \
           self.maximum and dt_utc > self.maximum:
            return (dt_utc, self.error_message)
        else:
            return (dt_utc, None)

    def formatter(self, value):

        format = self.format
        offset = self.delta()

        if not value:
            return "-"
        elif offset:
            dt = value + timedelta(seconds=offset)
            return dt.strftime(str(format))
        else:
            dt = value
            return dt.strftime(str(format)) + "+0000"

# -----------------------------------------------------------------------------
class IS_ACL(IS_IN_SET):

    """
        Validator for ACLs

        @attention: Incomplete! Does not validate yet, but just convert.

        @author: Dominic König <dominic@aidiq.com>
    """

    def __call__(self, value):
        """
            Validation

            @param value: the value to validate
        """

        if not isinstance(value, (list, tuple)):
            value = [value]

        acl = 0x0000
        for v in value:
            try:
                flag = int(v)
            except (ValueError, TypeError):
                flag = 0x0000
            else:
                acl |= flag

        return (acl, None)

# -----------------------------------------------------------------------------
class QUANTITY_INV_ITEM(object):
    """
        For Inv module
        by Michael Howden
    """
    def __init__(self,
                 db,
                 inv_item_id,
                 item_pack_id
                ):

        self.inv_item_id = inv_item_id
        self.item_pack_id = item_pack_id
        current.db = db

    def __call__(self, value):

        db = current.db

        error = "Invalid Quantity" # @todo: better error catching
        query = (db.inv_inv_item.id == self.inv_item_id) & \
                (db.inv_inv_item.item_pack_id == db.supply_item_pack.id)
        inv_item_record = db(query).select(db.inv_inv_item.quantity,
                                           db.supply_item_pack.quantity,
                                           db.supply_item_pack.name,
                                           limitby = (0, 1)).first() # @todo: this should be a virtual field
        if inv_item_record and value:
            query = (db.supply_item_pack.id == self.item_pack_id)
            send_quantity = float(value) * db(query).select(db.supply_item_pack.quantity,
                                                            limitby=(0, 1)).first().quantity
            inv_quantity = inv_item_record.inv_inv_item.quantity * \
                             inv_item_record.supply_item_pack.quantity
            if send_quantity > inv_quantity:
                return (value,
                        "Only %s %s (%s) in the Inventory." %
                        (inv_quantity,
                         inv_item_record.supply_item_pack.name,
                         inv_item_record.supply_item_pack.quantity)
                        )
            else:
                return (value, None)
        else:
            return (value, error)

    def formatter(self, value):
        return value

# -----------------------------------------------------------------------------
class IS_IN_SET_LAZY(Validator):
    """
        Like IS_IN_SET but with options obtained from a supplied function.

        Options are instantiated when the validator or its options() method is
        called, so don't need to be generated until it's used.  Useful if the
        field is not needed on every request, and does significant processing
        to construct its options, or generates a large collection.  If the
        options are just from a database query, one can use IS_ONE_OF instead.

        Raises an exception if an options collection is passed rather than a
        callable as this is a programming error, e.g. accidentally *calling*
        the options function in the constructor instead of passing the
        function.  That would not get lazy options instantiation.

        The options collection (theset) and labels collection parameters to
        IS_IN_SET are replaced by:

        @param theset_fn: Function of no arguments that returns a collection
        of options and (optionally) labels. Both options and labels can be
        supplied via a dict or OrderedDict (options are keys, values are
        labels), list (or tuple) of two-element lists (or tuples) (element 0 in
        each pair is an option, element 1 is it's label). Otherwise, labels
        are obtained either by calling the supplied represent function on each
        item produced by theset_fn, or (if no represent is supplied), the items
        themselves are used as labels.

        @param represent: Function of one argument that returns the label for
        a given option.

        If there is a function call that returns the collection, just put
        "lambda:" in front of the call.  E.g.:

        Field("nationality",
            requires = IS_NULL_OR(IS_IN_SET_LAZY(
                lambda: gis.get_countries(key_type="code"))),
            label = T("Nationality"),
            represent = lambda code: gis.get_country(code, key_type="code") or UNKNOWN_OPT)

        Keyword parameters are same as for IS_IN_SET, except for labels, which
        is not replaced by a function that parallels theset_fn, since ordering
        is problematic if theset_fn returns a dict.
    """

    def __init__(
        self,
        theset_fn,
        represent=None,
        error_message="value not allowed",
        multiple=False,
        zero="",
        sort=False,
        ):
        self.multiple = multiple
        if not callable(theset_fn):
            raise TypeError("Argument must be a callable.")
        self.theset_fn = theset_fn
        self.theset = None
        self.labels = None
        self.error_message = error_message
        self.zero = zero
        self.sort = sort

    def _make_theset(self):
        theset = self.theset_fn()
        if theset:
            if isinstance(theset, dict):
                self.theset = [str(item) for item in theset]
                self.labels = theset.values()
            elif isinstance(theset, (tuple,list)):  # @ToDo: Can this be a Rows?
                if isinstance(theset[0], (tuple,list)) and len(theset[0])==2:
                    self.theset = [str(item) for item,label in theset]
                    self.labels = [str(label) for item,label in theset]
                else:
                    self.theset = [str(item) for item in theset]
                    if represent:
                        self.labels = [represent(item) for item in theset]
            else:
                self.theset = theset

    def options(self):
        if not self.theset:
            self._make_theset()
        if not self.labels:
            items = [(k, k) for (i, k) in enumerate(self.theset)]
        else:
            items = [(k, self.labels[i]) for (i, k) in enumerate(self.theset)]
        if self.sort:
            items.sort(options_sorter)
        if self.zero != None and not self.multiple:
            items.insert(0, ("", self.zero))
        return items

    def __call__(self, value):
        if not self.theset:
            self._make_theset()
        if self.multiple:
            ### if below was values = re.compile("[\w\-:]+").findall(str(value))
            if isinstance(value, (str,unicode)):
                values = [value]
            elif isinstance(value, (tuple, list)):
                values = value
            elif not value:
                values = []
        else:
            values = [value]
        failures = [x for x in values if not x in self.theset]
        if failures and self.theset:
            if self.multiple and (value == None or value == ""):
                return ([], None)
            return (value, self.error_message)
        if self.multiple:
            if isinstance(self.multiple,(tuple,list)) and \
                    not self.multiple[0]<=len(values)<self.multiple[1]:
                return (values, self.error_message)
            return (values, None)
        return (value, None)

# -----------------------------------------------------------------------------
class IS_TIME_INTERVAL_WIDGET(Validator):
    """
        Simple validator for the S3TimeIntervalWidget, returns
        the selected time interval in seconds
    """

    def __init__(self, field):
        self.field = field

    def __call__(self, value):

        try:
            val = int(value)
        except ValueError:
            return (0, None)
        request = current.request
        _vars = request.post_vars
        try:
            mul = int(_vars[("%s_multiplier" % self.field).replace(".", "_")])
        except ValueError:
            return (0, None)
        seconds = val * mul
        return (seconds, None)

# END -------------------------------------------------------------------------
