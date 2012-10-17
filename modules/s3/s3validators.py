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
           "IS_ONE_OF",
           "IS_ONE_OF_EMPTY",
           "IS_ONE_OF_EMPTY_SELECT",
           "IS_NOT_ONE_OF",
           "IS_LOCATION",
           "IS_LOCATION_SELECTOR",
           "IS_SITE_SELECTOR",
           "IS_ACL",
           "IS_ADD_PERSON_WIDGET",
           "IS_COMBO_BOX",
           "IS_IN_SET_LAZY",
           "QUANTITY_INV_ITEM",
           ]

import re
import time
from datetime import datetime, timedelta

from gluon import *
#from gluon import current
#from gluon.dal import Field
#from gluon.validators import IS_DATE_IN_RANGE, IS_MATCH, IS_NOT_IN_DB, IS_IN_SET, IS_INT_IN_RANGE, IS_FLOAT_IN_RANGE, IS_EMAIL
from gluon.languages import lazyT
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

# =============================================================================
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

    # -------------------------------------------------------------------------
    def __call__(self, value):
        try:
            value = float(value)
            if self.minimum <= value <= self.maximum:
                return (value, None)
        except ValueError:
            pass
        return (value, self.error_message)

# =============================================================================
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

    # -------------------------------------------------------------------------
    def __call__(self, value):
        try:
            value = float(value)
            if self.minimum <= value <= self.maximum:
                return (value, None)
        except ValueError:
            pass
        return (value, self.error_message)

# =============================================================================
class IS_NUMBER(object):
    @staticmethod
    def represent(number, precision=2):
        if number is None:
            return ""

        if isinstance(number, int):
            return IS_INT_AMOUNT.represent(number)
        elif isinstance(number, float):
            return IS_FLOAT_AMOUNT.represent(number, precision)
        else:
            return number

# =============================================================================
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

    # -------------------------------------------------------------------------
    def __call__(self, value):

        thousands_sep = ","
        value = str(value).replace(thousands_sep, "")
        return IS_INT_IN_RANGE.__call__(self, value)

    # -------------------------------------------------------------------------
    @staticmethod
    def represent(number):
        """
            Change the format of the number depending on the language
            Based on https://code.djangoproject.com/browser/django/trunk/django/utils/numberformat.py
        """

        if number is None:
            return ""
        try:
            intnumber = int(number)
        except:
            intnumber = number

        T = current.T
        settings = current.deployment_settings

        # We need to check that we actually get the separators
        # otherwise we use the ISO defaults
        THOUSAND_SEPARATOR = T("THOUSAND_SEPARATOR")
        if THOUSAND_SEPARATOR == "THOUSAND_SEPARATOR":
            THOUSAND_SEPARATOR = settings.L10n.get("thousands_separator", u"\u00A0")

        NUMBER_GROUPING = T("NUMBER_GROUPING")
        if NUMBER_GROUPING == "NUMBER_GROUPING":
            NUMBER_GROUPING = settings.L10n.get("thousands_grouping", 3)

        # The negative/positive sign for the number
        if float(number) < 0:
            sign = "-"
        else:
            sign = ""

        str_number = unicode(intnumber)

        if str_number[0] == "-":
            str_number = str_number[1:]

        # Walk backwards over the integer part, inserting the separator as we go
        int_part_gd = ""
        for cnt, digit in enumerate(str_number[::-1]):
            if cnt and not cnt % NUMBER_GROUPING:
                int_part_gd += THOUSAND_SEPARATOR
            int_part_gd += digit
        int_part = int_part_gd[::-1]

        return sign + int_part

    # -------------------------------------------------------------------------
    @staticmethod
    def widget(f, v, **attributes):
        from gluon.sqlhtml import StringWidget
        attr = Storage(attributes)
        classes = attr.get("_class", "").split(" ")
        classes = " ".join([c for c in classes if c != "integer"])
        _class = "%s int_amount" % classes
        attr.update(_class=_class)
        return StringWidget.widget(f, v, **attr)

# =============================================================================
class IS_FLOAT_AMOUNT(IS_FLOAT_IN_RANGE):
    """
        Validation, widget and representation of
        float-values with thousands-separators
    """

    def __init__(self,
                 minimum=None,
                 maximum=None,
                 error_message=None,
                 dot="."):

        IS_FLOAT_IN_RANGE.__init__(self,
                                   minimum=minimum,
                                   maximum=maximum,
                                   error_message=error_message,
                                   dot=dot)

    # -------------------------------------------------------------------------
    def __call__(self, value):

        thousands_sep = ","
        value = str(value).replace(thousands_sep, "")
        return IS_FLOAT_IN_RANGE.__call__(self, value)

    # -------------------------------------------------------------------------
    @staticmethod
    def represent(number, precision=None):
        """
            Change the format of the number depending on the language
            Based on https://code.djangoproject.com/browser/django/trunk/django/utils/numberformat.py
        """

        if number is None:
            return ""

        # We need to check that we actually get the separators
        # otherwise we use the ISO defaults
        DECIMAL_SEPARATOR = current.T("DECIMAL_SEPARATOR")
        if DECIMAL_SEPARATOR == "DECIMAL_SEPARATOR":
            DECIMAL_SEPARATOR = current.deployment_settings.L10n.get("decimal_separator", ",")

        str_number = unicode(number)

        if "." in str_number:
            int_part, dec_part = str_number.split(".")
            if precision is not None:
                dec_part = dec_part[:precision]
        else:
            int_part, dec_part = str_number, ""
        if int(dec_part) == 0:
            dec_part = ""
        elif precision is not None:
            dec_part = dec_part + ("0" * (precision - len(dec_part)))
        if dec_part:
            dec_part = DECIMAL_SEPARATOR + dec_part

        int_part = IS_INT_AMOUNT.represent(int(int_part))

        return int_part + dec_part

    # -------------------------------------------------------------------------
    @staticmethod
    def widget(f, v, **attributes):
        from gluon.sqlhtml import StringWidget
        attr = Storage(attributes)
        classes = attr.get("_class", "").split(" ")
        classes = " ".join([c for c in classes if c != "double"])
        _class = "%s float_amount" % classes
        attr.update(_class=_class)
        return StringWidget.widget(f, v, **attr)

# =============================================================================
class IS_HTML_COLOUR(IS_MATCH):
    """
        example::

        INPUT(_type="text", _name="name", requires=IS_HTML_COLOUR())
    """

    def __init__(self,
                 error_message="must be a 6 digit hex code!"
                ):
        IS_MATCH.__init__(self, "^[0-9a-fA-F]{6}$", error_message)

# =============================================================================
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
                 updateable=False,
                 instance_types=None,
                 error_message="invalid value!",
                 orderby=None,
                 groupby=None,
                 left=None,
                 multiple=False,
                 zero="",
                 sort=True,
                 _and=None,
                ):
        """
            Validator for foreign keys.

            @param dbset: a Set of records like db(query), or db itself
            @param field: the field in the referenced table
            @param label: lookup method for the label corresponding a value,
                          alternatively a string template to be filled with
                          values from the record
            @param filterby: a field in the referenced table to filter by
            @param filter_opts: values for the filterby field which indicate
                                records to include
            @param not_filterby: a field in the referenced table to filter by
            @param not_filter_opts: values for not_filterby field which indicate
                                    records to exclude
            @param updateable: only include records in the referenced table which
                               can be updated by the user (if False, all readable
                               records will be included)
            @param instance_types: if the referenced table is a super-entity, then
                                   only include these instance types (this parameter
                                   is required for super entity lookups!)
            @param error_message: the error message to return for failed validation
            @param orderby: orderby for the options
            @param groupby: groupby for the options
            @param left: additional left joins required for the options lookup
                         (super-entity instance left joins will be included
                         automatically)
            @param multiple: allow multiple values (for list:reference types)
            @param zero: add this as label for the None-option (allow selection of "None")
            @param sort: sort options alphabetically by their label
            @param _and: internal use
        """

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
            try:
                table = current.s3db[ktable]
                fields =[str(f) for f in table]
            except RuntimeError:
                fields = "all"
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

        self.updateable = updateable
        self.instance_types = instance_types

    # -------------------------------------------------------------------------
    def set_self_id(self, id):
        if self._and:
            self._and.record_id = id

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def build_set(self):

        dbset = self.dbset
        db = dbset._db
        if self.ktable in db:

            table = db[self.ktable]

            if self.fields == "all":
                fields = [table[f] for f in table.fields]
            else:
                fieldnames = [f.split(".")[1] if "." in f else f for f in self.fields]
                fields = [table[k] for k in fieldnames if k in table.fields]
            if db._dbname not in ("gql", "gae"):
                orderby = self.orderby or reduce(lambda a, b: a|b, fields)
                groupby = self.groupby
                # Caching breaks Colorbox dropdown refreshes
                #dd = dict(orderby=orderby, groupby=groupby, cache=(current.cache.ram, 60))
                dd = dict(orderby=orderby, groupby=groupby)

                method = "update" if self.updateable else "read"
                query, left = self.accessible_query(method, table,
                                                    instance_types=self.instance_types)

                if "deleted" in table:
                    query = ((table["deleted"] == False) & query)

                filterby = self.filterby
                if filterby and filterby in table:
                    filter_opts = self.filter_opts
                    if filter_opts:
                        if None in filter_opts:
                            # Needs special handling (doesn't show up in 'belongs')
                            _query = (table[filterby]== None)
                            filter_opts = [f for f in filter_opts if f is not None]
                            if filter_opts:
                                _query = _query | (table[filterby].belongs(filter_opts))
                            query &= _query
                        else:
                            query &= (table[filterby].belongs(filter_opts))
                    if not self.orderby:
                        dd.update(orderby=table[filterby])

                not_filterby = self.not_filterby
                if not_filterby and not_filterby in table:
                    not_filter_opts = self.not_filter_opts
                    if not_filter_opts:
                        query &= (~(table[not_filterby].belongs(not_filter_opts)))
                    if not self.orderby:
                        dd.update(orderby=table[filterby])

                if self.left is not None:
                    self.left.append(left)
                else:
                    self.left = left
                if self.left is not None:
                    dd.update(left=self.left)
                records = dbset(query).select(distinct=True, *fields, **dd)
            else:
                # Note this does not support filtering.
                orderby = self.orderby or \
                          reduce(lambda a, b: a|b, (f for f in fields
                                                    if not f.name == "id"))
                # Caching breaks Colorbox dropdown refreshes
                #dd = dict(orderby=orderby, cache=(current.cache.ram, 60))
                dd = dict(orderby=orderby)
                records = dbset.select(db[self.ktable].ALL, **dd)
            self.theset = [str(r[self.kfield]) for r in records]
            label = self.label
            try:
                # Is a function
                labels = map(label, records)
            except TypeError:
                if isinstance(label, str):
                    labels = map(lambda r: label % dict(r), records)
                elif isinstance(label, (list, tuple)):
                    labels = map(lambda r: \
                                 " ".join([r[l] for l in label if l in r]),
                                 records)
                elif "name" in table:
                    labels = map(lambda r: r.name, records)
                else:
                    labels = map(lambda r: r[self.kfield], records)
            self.labels = labels

            if labels and self.sort:
                orig_labels = self.labels
                orig_theset = self.theset

                labels = []
                theset = []

                for label in orig_labels:
                    try:
                        labels.append(label.flatten())
                    except:
                        labels.append(label)
                orig_labels = list(labels)
                labels.sort()

                for label in labels:
                     orig_index = orig_labels.index(label)
                     theset.append(orig_theset[orig_index])

                self.labels = labels
                self.theset = theset

        else:
            self.theset = None
            self.labels = None

    # -------------------------------------------------------------------------
    @classmethod
    def accessible_query(cls, method, table, instance_types=None):
        """
            Returns an accessible query (and left joins, if necessary) for
            records in table the user is permitted to access with method

            @param method: the method (e.g. "read" or "update")
            @param table: the table
            @param instance_types: list of instance tablenames, if table is
                                   a super-entity (required in this case!)

            @returns: tuple (query, left) where query is the query and left joins
                      is the list of left joins required for the query

            @note: for higher security policies and super-entities with many
                   instance types this can give a very complex query. Try to
                   always limit the instance types to what is really needed
        """

        DEFAULT = (table._id > 0)

        left = None

        if "instance_type" in table:
            # Super-entity
            if not instance_types:
                return DEFAULT, left
            query = None
            auth = current.auth
            s3db = current.s3db
            for instance_type in instance_types:
                itable = s3db.table(instance_type)
                if itable is None:
                    continue

                join = itable.on(itable[table._id.name] == table._id)
                if left is None:
                    left = [join]
                else:
                    left.append(join)

                q = (itable._id != None) & \
                    auth.s3_accessible_query(method, itable)
                if "deleted" in itable:
                    q &= itable.deleted != True
                if query is None:
                    query = q
                else:
                    query |= q

            if query is None:
                query = DEFAULT
        else:
            query = current.auth.s3_accessible_query(method, table)

        return query, left

    # -------------------------------------------------------------------------
    # Removed as we don't want any options downloaded unnecessarily
    #def options(self):

    # -------------------------------------------------------------------------
    def __call__(self, value):

        try:
            dbset = self.dbset
            table = dbset._db[self.ktable]
            deleted_q = ("deleted" in table) and (table["deleted"] == False) or False
            filter_opts_q = False
            filterby = self.filterby
            if filterby and filterby in table:
                if self.filter_opts:
                    filter_opts_q = table[filterby].belongs(self.filter_opts)

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
                    field = table[self.kfield]
                    for v in values:
                        q = (field == v)
                        query = query is not None and query | q or q
                    if filter_opts_q != False:
                        query = query is not None and \
                                (filter_opts_q & (query)) or filter_opts_q
                    if deleted_q != False:
                        query = query is not None and \
                                (deleted_q & (query)) or deleted_q
                    if dbset(query).count() < 1:
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
                if dbset(query).count():
                    if self._and:
                        return self._and(value)
                    else:
                        return (value, None)
        except:
            pass

        return (value, self.error_message)


# =============================================================================
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


# =============================================================================
class IS_ONE_OF_EMPTY_SELECT(IS_ONE_OF_EMPTY):

    """
        Extends IS_ONE_OF_EMPTY by displaying an empty SELECT (instead of INPUT)
    """

    def options(self):
        return [("", "")]

# =============================================================================
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
        if "deleted" in table:
            query = (table["deleted"] == False) & query
        rows = dbset(query).select(limitby=(0, 1))
        if len(rows) > 0:
            if isinstance(self.record_id, dict):
                for f in self.record_id:
                    if str(getattr(rows[0], f)) != str(self.record_id[f]):
                        return (value, translate(self.error_message))
            elif str(rows[0][table._id.name]) != str(self.record_id):
                    return (value, translate(self.error_message))
        return (value, None)

# =============================================================================
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

    # -------------------------------------------------------------------------
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

# =============================================================================
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
        self.error_message = error_message
        self.errors = Storage()
        self.id = None

    # -------------------------------------------------------------------------
    def __call__(self, value):
        db = current.db
        table = db.gis_location

        if value == "dummy":
            # Create form
            if not current.auth.s3_has_permission("create", table):
                return (None, current.auth.messages.access_denied)
            location = self._process_values()
            if self.errors:
                errors = self.errors
                error = ""
                for e in errors:
                    error = "%s\n%s" % (error, errors[e]) if error else errors[e]
                return (None, error)
            if location.name or location.lat or location.lon or \
               location.street or location.postcode or location.parent:
                vars = dict(name = location.name,
                            lat = location.lat,
                            lon = location.lon,
                            addr_street = location.street,
                            addr_postcode = location.postcode,
                            parent = location.parent,
                            wkt = location.wkt,
                            lon_min = location.lon_min,
                            lon_max = location.lon_max,
                            lat_min = location.lat_min,
                            lat_max = location.lat_max
                            )

                if vars["wkt"] and current.deployment_settings.get_gis_spatialdb():
                    # Also populate the spatial field
                    vars["the_geom"] = vars["wkt"]

                value = table.insert(**vars)
                # onaccept
                vars["id"] = value
                current.gis.update_location_tree(vars)
                return (value, None)
            else:
                return (None, None)

        else:
            # This must be an Update form
            if not current.auth.s3_has_permission("update", table, record_id=value):
                return (value, current.auth.messages.access_denied)
            # Check that this is a valid location_id
            query = (table.id == value) & \
                    (table.deleted == False) & \
                    (table.level == None) # NB Specific Locations only
            location = db(query).select(table.id,
                                        limitby=(0, 1)).first()
            if location:
                # Update the record, in case changes have been made
                self.id = value
                location = self._process_values()
                if self.errors:
                    errors = self.errors
                    error = ""
                    for e in errors:
                        error = "%s\n%s" % (error, errors[e]) if error else errors[e]
                    return (value, error)
                vars = dict(name = location.name,
                            lat = location.lat,
                            lon = location.lon,
                            inherited = location.inherited,
                            addr_street = location.street,
                            addr_postcode = location.postcode,
                            parent = location.parent,
                            wkt = location.wkt,
                            lon_min = location.lon_min,
                            lon_max = location.lon_max,
                            lat_min = location.lat_min,
                            lat_max = location.lat_max
                            )

                if vars["wkt"] and current.deployment_settings.get_gis_spatialdb():
                    # Also populate the spatial field
                    vars["the_geom"] = vars["wkt"]

                db(table.id == value).update(**vars)
                # onaccept
                vars["id"] = value
                current.gis.update_location_tree(vars)
                return (value, None)
            else:
                return (value, self.error_message or current.T("Invalid Location!"))

    # -------------------------------------------------------------------------
    def _process_values(self):
        """
            Read the request.vars & prepare for a record insert/update

            Note: This is also used by IS_SITE_SELECTOR()
        """

        # Rough check for valid Lat/Lon (detailed later)
        vars = current.request.vars
        lat = vars.get("gis_location_lat", None)
        lon = vars.get("gis_location_lon", None)
        if lat:
            try:
                lat = float(lat)
            except ValueError:
                self.errors["lat"] = current.T("Latitude is Invalid!")
        if lon:
            try:
                lon = float(lon)
            except ValueError:
                self.errors["lon"] = current.T("Longitude is Invalid!")
        if self.errors:
            return None

        L0 = vars.get("gis_location_L0", None)

        db = current.db
        table = db.gis_location
        # Are we allowed to create Locations?
        auth = current.auth
        if not auth.s3_has_permission("create", table):
            self.errors["location_id"] = auth.messages.access_denied
            return None
        # What level of hierarchy are we allowed to edit?
        s3db = current.s3db
        if auth.s3_has_role(current.session.s3.system_roles.MAP_ADMIN):
            # 'MapAdmin' always has permission to edit hierarchy locations
            L1_allowed = True
            L2_allowed = True
            L3_allowed = True
            L4_allowed = True
            L5_allowed = True
        else:
            if L0:
                htable = s3db.gis_hierarchy
                query = (htable.location_id == L0)
                config = db(query).select(htable.edit_L1,
                                          htable.edit_L2,
                                          htable.edit_L3,
                                          htable.edit_L4,
                                          htable.edit_L5,
                                          limitby=(0, 1)).first()
            if L0 and config:
                # Lookup each level individually
                L1_allowed = config.edit_L1
                L2_allowed = config.edit_L2
                L3_allowed = config.edit_L3
                L4_allowed = config.edit_L4
                L5_allowed = config.edit_L5
            else:
                # default is True
                L1_allowed = True
                L2_allowed = True
                L3_allowed = True
                L4_allowed = True
                L5_allowed = True

        # We don't need to do onvalidation of the Location Hierarchy records
        # separately as we don't have anything extra to validate than we have
        # done already

        onaccept = current.gis.update_location_tree

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
                L1 = int(L1)
                # Do we need to update it's parent?
                if L0:
                    location = db(table.id == L1).select(table.name,
                                                         table.parent,
                                                         limitby=(0, 1)).first()
                    if location and (location.parent != int(L0)):
                        db(query).update(parent = L0)
                        location["level"] = "L1"
                        location["id"] = L1
                        onaccept(location)
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
                elif L1_allowed:
                    if L0:
                        f = dict(name = L1,
                                 level = "L1",
                                 parent = L0,
                                 )
                        L1 = table.insert(**f)
                        f["id"] = L1
                        onaccept(f)
                    else:
                        f = dict(name=L1,
                                 level="L1",
                                 )
                        L1 = table.insert(**f)
                        f["id"] = L1
                        onaccept(f)
                else:
                    L1 = None
        # L2
        if L2:
            try:
                # Is this an ID?
                L2 = int(L2)
                # Do we need to update it's parent?
                if L1:
                    location = db(table.id == L2).select(table.name,
                                                         table.parent,
                                                         limitby=(0, 1)).first()
                    if location and (location.parent != L1):
                        db(query).update(parent=L1)
                        location["level"] = "L2"
                        location["id"] = L2
                        onaccept(location)
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
                elif L2_allowed:
                    if L1:
                        f = dict(name=L2,
                                 level="L2",
                                 parent=L1,
                                 )
                        L2 = table.insert(**f)
                        f["id"] = L2
                        onaccept(f)
                    elif L0:
                        f = dict(name=L2,
                                 level="L2",
                                 parent=L0,
                                 )
                        L2 = table.insert(**f)
                        f["id"] = L2
                        onaccept(f)
                    else:
                        f = dict(name=L2,
                                 level="L2",
                                 )
                        L2 = table.insert(**f)
                        f["id"] = L2
                        onaccept(f)
                else:
                    L2 = None
        # L3
        if L3:
            try:
                # Is this an ID?
                L3 = int(L3)
                # Do we need to update it's parent?
                if L2:
                    location = db(table.id == L3).select(table.name,
                                                         table.parent,
                                                         limitby=(0, 1)).first()
                    if location and (location.parent != L2):
                        db(query).update(parent=L2)
                        location["level"] = "L3"
                        location["id"] = L3
                        onaccept(location)
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
                elif L3_allowed:
                    if L2:
                        f = dict(name=L3,
                                 level="L3",
                                 parent=L2,
                                 )
                        L3 = table.insert(**f)
                        f["id"] = L3
                        onaccept(f)
                    elif L1:
                        f = dict(name=L3,
                                 level="L3",
                                 parent=L1,
                                 )
                        L3 = table.insert(**f)
                        f["id"] = L3
                        onaccept(f)
                    elif L0:
                        f = dict(name=L3,
                                 level="L3",
                                 parent=L0,
                                 )
                        L3 = table.insert(**f)
                        f["id"] = L3
                        onaccept(f)
                    else:
                        f = dict(name=L3,
                                 level="L3",
                                 )
                        L3 = table.insert(**f)
                        f["id"] = L3
                        onaccept(f)
                else:
                    L3 = None
        # L4
        if L4:
            try:
                # Is this an ID?
                L4 = int(L4)
                # Do we need to update it's parent?
                if L3:
                    location = db(table.id == L4).select(table.name,
                                                         table.parent,
                                                         limitby=(0, 1)).first()
                    if location and (location.parent != L3):
                        db(query).update(parent=L3)
                        location["level"] = "L4"
                        location["id"] = L4
                        onaccept(location)
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
                elif L4_allowed:
                    if L3:
                        f = dict(name=L4,
                                 level="L4",
                                 parent=L3,
                                 )
                        L4 = table.insert(**f)
                        f["id"] = L4
                        onaccept(f)
                    elif L2:
                        f = dict(name=L4,
                                 level="L4",
                                 parent=L2,
                                 )
                        L4 = table.insert(**f)
                        f["id"] = L4
                        onaccept(f)
                    elif L1:
                        f = dict(name=L4,
                                 level="L4",
                                 parent=L1,
                                 )
                        L4 = table.insert(**f)
                        f["id"] = L4
                        onaccept(f)
                    elif L0:
                        f = dict(name=L4,
                                 level="L4",
                                 parent=L0,
                                 )
                        L4 = table.insert(**f)
                        f["id"] = L4
                        onaccept(f)
                    else:
                        f = dict(name=L4,
                                 level="L4",
                                 )
                        L4 = table.insert(**f)
                        f["id"] = L4
                        onaccept(f)
                else:
                    L4 = None
        # L5
        if L5:
            try:
                # Is this an ID?
                L5 = int(L5)
                # Do we need to update it's parent?
                if L4:
                    location = db(table.id == L5).select(table.name,
                                                         table.parent,
                                                         limitby=(0, 1)).first()
                    if location and (location.parent != L4):
                        db(query).update(parent=L4)
                        location["level"] = "L5"
                        location["id"] = L5
                        onaccept(location)
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
                elif L5_allowed:
                    if L4:
                        f = dict(name=L5,
                                 level="L5",
                                 parent=L4,
                                 )
                        L5 = table.insert(**f)
                        f["id"] = L5
                        onaccept(f)
                    elif L3:
                        f = dict(name=L5,
                                 level="L5",
                                 parent=L3,
                                 )
                        L5 = table.insert(**f)
                        f["id"] = L5
                        onaccept(f)
                    elif L2:
                        f = dict(name=L5,
                                 level="L5",
                                 parent=L2,
                                 )
                        L5 = table.insert(**f)
                        f["id"] = L5
                        onaccept(f)
                    elif L1:
                        f = dict(name=L5,
                                 level="L5",
                                 parent=L1,
                                 )
                        L5 = table.insert(**f)
                        f["id"] = L5
                        onaccept(f)
                    elif L0:
                        f = dict(name=L5,
                                 level="L5",
                                 parent=L1,
                                 )
                        L5 = table.insert(**f)
                        f["id"] = L5
                        onaccept(f)
                    else:
                        f = dict(name=L5,
                                 level="L5",
                                 )
                        L5 = table.insert(**f)
                        f["id"] = L5
                        onaccept(f)
                else:
                    L5 = None

        # Check if we have a specific location to create
        name = vars.get("gis_location_name", None)
        street = vars.get("gis_location_street", None)
        postcode = vars.get("gis_location_postcode", None)
        parent = L5 or L4 or L3 or L2 or L1 or L0 or None

        # Move vars into form.
        form = Storage()
        form.errors = dict()
        form.vars = Storage()
        vars = form.vars
        vars.lat = lat
        vars.lon = lon
        vars.parent = parent
        if self.id:
            # Provide the old record to check inherited
            form.record = db(table.id == self.id).select(table.inherited,
                                                         table.lat,
                                                         table.lon,
                                                         limitby=(0, 1)).first()
        # onvalidation
        s3db.gis_location_onvalidation(form)
        if form.errors:
            self.errors = form.errors
            return None
        location = Storage(
                        name=name,
                        lat=lat, lon=lon,
                        inherited=vars.inherited,
                        street=street,
                        postcode=postcode,
                        parent=parent,
                        wkt = vars.wkt,
                        lon_min = vars.lon_min,
                        lon_max = vars.lon_max,
                        lat_min = vars.lat_min,
                        lat_max = vars.lat_max
                      )

        return location

# =============================================================================
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
        self.error_message = error_message
        self.errors = Storage()
        self.id = None
        self.site_type = site_type

    # -------------------------------------------------------------------------
    def __call__(self, value):
        db = current.db
        auth = current.auth
        gis = current.gis
        table = db.gis_location
        stable = db[self.site_type]

        if value == "dummy":
            # Create form
            if not auth.s3_has_permission("create", stable):
                return (None, auth.messages.access_denied)
            location = self._process_values()
            if self.errors:
                errors = self.errors
                error = ""
                for e in errors:
                    error = "%s\n%s" % (error, errors[e]) if error else errors[e]
                return (None, error)
            if location.name or location.lat or location.lon or \
               location.street or location.postcode or location.parent:
                # Location creation
                vars = dict(name = location.name,
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
                location_id = table.insert(**vars)
                # Location onaccept
                vars["id"] = location_id
                gis.update_location_tree(vars)
                # Site creation
                value = stable.insert(name = location.name,
                                      location_id = location_id)
                return (value, None)
            else:
                return (None, None)
        else:
            # This must be an Update form
            if not auth.s3_has_permission("update", stable, record_id=value):
                return (value, auth.messages.access_denied)
            # Check that this is a valid site_id
            query = (stable.id == value) & \
                    (stable.deleted == False)
            site = db(query).select(stable.id,
                                    stable.name,
                                    stable.location_id,
                                    limitby=(0, 1)).first()
            location_id = site.location_id if site else None
            if location_id:
                # Update the location, in case changes have been made
                self.id = value
                location = self._process_values()
                if self.errors:
                    errors = self.errors
                    error = ""
                    for e in errors:
                        error = "%s\n%s" % (error, errors[e]) if error else errors[e]
                    return (value, error)
                # Location update
                name = location.name
                vars = dict(name = name,
                            lat = location.lat,
                            lon = location.lon,
                            addr_street = location.street,
                            addr_postcode = location.postcode,
                            parent = location.parent
                            )
                lquery = (table.id == location_id)
                db(lquery).update(**vars)
                # Location onaccept
                vars["id"] = location_id
                gis.update_location_tree(vars)

                if stable.name != name:
                    # Site Name has changed
                    db(query).update(name = name)
                return (value, None)

        return (value, self.error_message or current.T("Invalid Site!"))

# =============================================================================
class IS_ADD_PERSON_WIDGET(Validator):

    def __init__(self,
                 error_message=None,
                 mark_required=True):

        self.error_message = error_message
        self.mark_required = mark_required

    # -------------------------------------------------------------------------
    def __call__(self, value):

        T = current.T
        db = current.db
        s3db = current.s3db
        request = current.request
        settings = current.deployment_settings

        try:
            person_id = int(value)
        except:
            person_id = None

        ptable = db.pr_person
        ctable = db.pr_contact

        def email_validate(value, person_id):
            """ Validate the email address """

            error_message = T("Please enter a valid email address.")

            if value is not None:
                value = value.strip()

            # No email?
            if not value:
                email_required = settings.get_hrm_email_required()
                if email_required:
                    return (value, error_message)
                return (value, None)

            # Valid email?
            value, error = IS_EMAIL()(value)
            if error:
                return value, error_message

            # Unique email?
            query = (ctable.deleted != True) & \
                    (ctable.contact_method == "EMAIL") & \
                    (ctable.value == value)
            if person_id:
                query = query & \
                        (ctable.pe_id == ptable.pe_id) & \
                        (ptable.id != person_id)
            email = db(query).select(ctable.id, limitby=(0, 1)).first()
            if email:
                error_message = T("This email-address is already registered.")
                return value, error_message

            # Ok!
            return value, None

        if request.env.request_method == "POST":
            _vars = request.post_vars
            mobile = _vars["mobile_phone"]
            if mobile:
                # Validate the phone number
                regex = re.compile(single_phone_number_pattern)
                if not regex.match(mobile):
                    error = T("Invalid phone number")
                    return (person_id, error)

            validate = current.manager.validate
            if person_id:
                # Validate and update the person record
                query = (ptable.id == person_id)
                data = Storage()
                for f in ptable._filter_fields(_vars):
                    value, error = validate(ptable, None, f, _vars[f])
                    if error:
                        return (None, None)
                    elif f == "date_of_birth" and \
                         value:
                        data[f] = value.isoformat()
                if data:
                    db(query).update(**data)

                # Update the contact information & details
                record = db(query).select(ptable.pe_id, limitby=(0, 1)).first()
                if record:
                    pe_id = record.pe_id

                    r = ctable(pe_id=pe_id, contact_method="EMAIL")
                    email = _vars["email"]
                    if email:
                        query = (ctable.pe_id == pe_id) & \
                                (ctable.contact_method == "EMAIL") &\
                                (ctable.deleted != True)
                        r = db(query).select(ctable.value,
                                             limitby=(0, 1)).first()
                        if r: # update
                            if email != r.value:
                                db(query).update(value=email)
                        else: # insert
                            ctable.insert(pe_id=pe_id,
                                          contact_method="EMAIL",
                                          value=email)

                    if mobile:
                        query = (ctable.pe_id == pe_id) & \
                                (ctable.contact_method == "SMS") &\
                                (ctable.deleted != True)
                        r = db(query).select(ctable.value,
                                             limitby=(0, 1)).first()
                        if r: # update
                            if mobile != r.value:
                                db(query).update(value=mobile)
                        else: # insert
                            ctable.insert(pe_id=pe_id,
                                          contact_method="SMS",
                                          value=mobile)

                    occupation = _vars["occupation"]
                    if occupation:
                        pdtable = s3db.pr_person_details
                        query = (pdtable.person_id == person_id) & \
                                (pdtable.deleted != True)
                        r = db(query).select(pdtable.occupation,
                                             limitby=(0, 1)).first()
                        if r: # update
                            if occupation != r.occupation:
                                db(query).update(occupation=occupation)
                        else: # insert
                            pdtable.insert(person_id=person_id,
                                           occupation=occupation)

            else:
                # Create a new person record

                # Filter out location_id (location selector form values
                # being processed only after this widget has been validated)
                _vars = Storage([(k, _vars[k])
                                 for k in _vars if k != "location_id"])

                # Validate the email
                email, error = email_validate(_vars.email, None)
                if error:
                    return (person_id, error)

                # Validate and add the person record
                for f in ptable._filter_fields(_vars):
                    value, error = validate(ptable, None, f, _vars[f])
                    if error:
                        return (None, None)
                    elif f == "date_of_birth" and \
                        value:
                        _vars[f] = value.isoformat()
                person_id = ptable.insert(**ptable._filter_fields(_vars))

                # Need to update post_vars here,
                # for some reason this doesn't happen through validation alone
                request.post_vars.update(person_id=str(person_id))

                if person_id:
                    # Update the super-entities
                    s3db.update_super(ptable, dict(id=person_id))
                    # Read the created pe_id
                    query = (ptable.id == person_id)
                    person = db(query).select(ptable.pe_id,
                                              limitby=(0, 1)).first()

                    # Add contact information as provided
                    if _vars.email:
                        ctable.insert(pe_id=person.pe_id,
                                      contact_method="EMAIL",
                                      value=_vars.email)
                    if mobile:
                        ctable.insert(pe_id=person.pe_id,
                                      contact_method="SMS",
                                      value=_vars.mobile_phone)
                    if _vars.occupation:
                        s3db.pr_person_details.insert(person_id = person_id,
                                                      occupation = occupation)
                else:
                    # Something went wrong
                    return (person_id, self.error_message or \
                                       T("Could not add person record"))

        return (person_id, None)

# =============================================================================
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

    # -------------------------------------------------------------------------
    @staticmethod
    def get_offset_value(offset_str):
        if offset_str and len(offset_str) >= 5 and \
            (offset_str[-5] == "+" or offset_str[-5] == "-") and \
            offset_str[-4:].isdigit():
            offset_hrs = int(offset_str[-5] + offset_str[-4:-2])
            offset_min = int(offset_str[-5] + offset_str[-2:])
            offset = 3600 * offset_hrs + 60 * offset_min
            return offset
        else:
            return None

    # -------------------------------------------------------------------------
    def __call__(self, value):

        if value and isinstance(value, str):
            _offset_str = value.strip()

            offset = self.get_offset_value(_offset_str)

            if offset is not None and offset > -86340 and offset < 86340:
                # Add a leading 'UTC ',
                # otherwise leading '+' and '0' will be stripped away by web2py
                return ("UTC " + _offset_str[-5:], None)

        return (value, self.error_message)

# =============================================================================
class IS_UTC_DATETIME(Validator):
    """
        Validates a given value as datetime string and returns the
        corresponding UTC datetime.

        Example:
            - INPUT(_type="text", _name="name", requires=IS_UTC_DATETIME())

        @param format:          strptime/strftime format template string, for
                                directives refer to your strptime implementation
        @param error_message:   error message to be returned
        @param utc_offset:      offset to UTC in seconds, if not specified, the
                                value is considered to be UTC
        @param minimum:         the minimum acceptable datetime
        @param maximum:         the maximum acceptable datetime

        @note:
            datetime has to be in the ISO8960 format YYYY-MM-DD hh:mm:ss,
            with an optional trailing UTC offset specified as +/-HHMM
            (+ for eastern, - for western timezones)
    """

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

        self.error_message = error_message % dict(min = min_local,
                                                  max = max_local)

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

# =============================================================================
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

# =============================================================================
class IS_COMBO_BOX(Validator):
    """
        Designed for use with an Autocomplete.
        - catches any new entries & creates the appropriate record
        @ToDo: Audit
    """

    def __init__(self,
                 tablename,
                 requires,  # The normal validator
                 error_message = None,
                ):
        self.tablename = tablename
        self.requires = requires
        self.error_message = error_message

    # -------------------------------------------------------------------------
    def __call__(self, value):

        if not value:
            # Do the normal validation
            return self.requires(value)
        elif isinstance(value, int):
            # If this is an ID then this is an update form
            # @ToDo: Can we assume that?

            # Do the normal validation
            return self.requires(value)
        else:
            # Name => create form
            tablename = self.tablename
            db = current.db
            table = db[tablename]

            # Test for duplicates
            query = (table.name == value)
            r = db(query).select(table.id,
                                 limitby=(0, 1)).first()
            if r:
                # Use Existing record
                value = r.id
                return (value, None)
            if not current.auth.s3_has_permission("create", table):
                return (None, current.auth.messages.access_denied)
            value = table.insert(name=value)
            # onaccept
            onaccept = current.s3db.get_config(tablename, "onaccept")
            if onaccept:
                onaccept(form=Storage(vars=Storage(id=value)))
            return (value, None)

# =============================================================================
class QUANTITY_INV_ITEM(object):
    """
        For Inventory module
    """
    def __init__(self,
                 db,
                 inv_item_id,
                 item_pack_id
                ):

        self.inv_item_id = inv_item_id
        self.item_pack_id = item_pack_id
        current.db = db

    # -------------------------------------------------------------------------
    def __call__(self, value):

        db = current.db
        args = current.request.args
        track_quantity = 0
        if args[1] == "track_item" and len(args) > 2:
            # look to see if we already have a quantity stored in the track item
            id = args[2]
            track_record = current.s3db.inv_track_item[id]
            track_quantity = track_record.quantity
            if track_quantity >= float(value):
                # value reduced or unchanged
                return (value, None)
        error = "Invalid Quantity" # @todo: better error catching
        query = (db.inv_inv_item.id == self.inv_item_id) & \
                (db.inv_inv_item.item_pack_id == db.supply_item_pack.id)
        inv_item_record = db(query).select(db.inv_inv_item.quantity,
                                           db.supply_item_pack.quantity,
                                           db.supply_item_pack.name,
                                           limitby = (0, 1)).first() # @todo: this should be a virtual field
        if inv_item_record and value:
            query = (db.supply_item_pack.id == self.item_pack_id)
            send_record = db(query).select(db.supply_item_pack.quantity,
                                           limitby=(0, 1)).first()
            send_quantity = (float(value) - track_quantity) * send_record.quantity
            inv_quantity = inv_item_record.inv_inv_item.quantity * \
                             inv_item_record.supply_item_pack.quantity
            if send_quantity > inv_quantity:
                return (value,
                        "Only %s %s (%s) in the Warehouse Stock." %
                        (inv_quantity,
                         inv_item_record.supply_item_pack.name,
                         inv_item_record.supply_item_pack.quantity)
                        )
            else:
                return (value, None)
        else:
            return (value, error)

    # -------------------------------------------------------------------------
    def formatter(self, value):
        return value

# =============================================================================
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

    # -------------------------------------------------------------------------
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
        else:
            self.theset = []

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

# =============================================================================
class IS_TIME_INTERVAL_WIDGET(Validator):
    """
        Simple validator for the S3TimeIntervalWidget, returns
        the selected time interval in seconds
    """

    def __init__(self, field):
        self.field = field

    # -------------------------------------------------------------------------
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

# END =========================================================================
