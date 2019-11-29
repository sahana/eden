# -*- coding: utf-8 -*-

""" Custom Validators

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2019 Sahana Software Foundation
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

__all__ = ("single_phone_number_pattern",
           "multi_phone_number_pattern",
           "s3_single_phone_requires",
           "s3_phone_requires",
           "IS_ACL",
           "IS_COMBO_BOX",
           "IS_DYNAMIC_FIELDNAME",
           "IS_DYNAMIC_FIELDTYPE",
           "IS_FLOAT_AMOUNT",
           "IS_HTML_COLOUR",
           "IS_INT_AMOUNT",
           "IS_IN_SET_LAZY",
           "IS_ISO639_2_LANGUAGE_CODE",
           "IS_JSONS3",
           "IS_LAT",
           "IS_LON",
           "IS_LAT_LON",
           "IS_LOCATION",
           "IS_ONE_OF",
           "IS_ONE_OF_EMPTY",
           "IS_ONE_OF_EMPTY_SELECT",
           "IS_NOT_ONE_OF",
           "IS_PERSON_GENDER",
           "IS_PHONE_NUMBER",
           "IS_PHONE_NUMBER_MULTI",
           "IS_PROCESSED_IMAGE",
           "IS_UTC_DATETIME",
           "IS_UTC_DATE",
           "IS_UTC_OFFSET",
           "JSONERRORS",
           "QUANTITY_INV_ITEM",
           )

import datetime
import json
import re

from gluon import current, IS_FLOAT_IN_RANGE, IS_INT_IN_RANGE, IS_IN_SET, \
                  IS_MATCH, IS_NOT_IN_DB
from gluon.storage import Storage
from gluon.validators import Validator

from s3compat import BytesIO, STRING_TYPES, basestring, reduce, unichr
from .s3datetime import S3DateTime
from .s3utils import s3_orderby_fields, s3_str, s3_unicode

DEFAULT = lambda: None
JSONERRORS = (NameError, TypeError, ValueError, AttributeError, KeyError)
SEPARATORS = (",", ":")

LAT_SCHEMA = re.compile(r"^([0-9]{,3})[d:°]{,1}\s*([0-9]{,3})[m:']{,1}\s*([0-9]{,3}(\.[0-9]+){,1})[s\"]{,1}\s*([N|S]{,1})$")
LON_SCHEMA = re.compile(r"^([0-9]{,3})[d:°]{,1}\s*([0-9]{,3})[m:']{,1}\s*([0-9]{,3}(\.[0-9]+){,1})[s\"]{,1}\s*([E|W]{,1})$")

def translate(text):
    if text is None:
        return None
    elif isinstance(text, STRING_TYPES):
        if hasattr(current, "T"):
            return str(current.T(text))
    return s3_str(text)

def options_sorter(x, y):
    return 1 if s3_unicode(x[1]).upper() > s3_unicode(y[1]).upper() else -1

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
phone_number_pattern = r"\+?\s*[\s\-\.\(\)\d]+(?:(?: x| ext)\s?\d{1,5})?"
single_phone_number_pattern = "%s$" % phone_number_pattern
multi_phone_number_pattern = r"%s(\s*(,|/|;)\s*%s)*$" % (phone_number_pattern,
                                                         phone_number_pattern)

s3_single_phone_requires = IS_MATCH(single_phone_number_pattern)
s3_phone_requires = IS_MATCH(multi_phone_number_pattern,
                             error_message="Invalid phone number!")

# =============================================================================
class IS_JSONS3(Validator):
    """
        Similar to web2py's IS_JSON validator, but extended to handle
        single quotes in dict keys (=invalid JSON) from CSV imports.

        Example:

            INPUT(_type='text', _name='name', requires=IS_JSONS3())

            >>> IS_JSONS3()('{"a": 100}')
            ({u'a': 100}, None)

            >>> IS_JSONS3()('spam1234')
            ('spam1234', 'invalid json')
    """

    def __init__(self,
                 native_json=False,
                 error_message="Invalid JSON"):
        """
            Constructor

            @param native_json: return the JSON string rather than
                                a Python object (e.g. when the field
                                is "string" type rather than "json")
            @param error_message: the error message
        """

        self.native_json = native_json
        self.error_message = error_message

    # -------------------------------------------------------------------------
    def __call__(self, value):
        """
            Validator, validates a string and converts it into db format
        """

        error = lambda v, e: (v, "%s: %s" % (current.T(self.error_message), e))

        if current.response.s3.bulk:
            # CSV import produces invalid JSON (single quotes),
            # which would still be valid Python though, so try
            # using ast to decode, then re-dumps as valid JSON:
            import ast
            try:
                value_ = json.dumps(ast.literal_eval(value),
                                    separators = SEPARATORS,
                                    )
            except JSONERRORS + (SyntaxError,) as e:
                return error(value, e)
            if self.native_json:
                return (value_, None)
            else:
                return (json.loads(value_), None)
        else:
            # Coming from UI, so expect valid JSON
            try:
                if self.native_json:
                    json.loads(value) # raises error in case of malformed JSON
                    return (value, None) #  the serialized value is not passed
                else:
                    return (json.loads(value), None)
            except JSONERRORS as e:
                return error(value, e)

    # -------------------------------------------------------------------------
    def formatter(self, value):
        """
            Formatter, converts the db format into a string
        """

        if value is None or \
           self.native_json and isinstance(value, basestring):
            return value
        else:
            return json.dumps(value, separators = SEPARATORS)

# =============================================================================
class IS_LAT(Validator):
    """
        example:

        INPUT(_type="text", _name="name", requires=IS_LAT())

        Latitude has to be in decimal degrees between -90 & 90
        - we attempt to convert DMS format into decimal degrees
    """

    def __init__(self,
                 error_message = "Latitude/Northing should be between -90 & 90!"
                 ):

        self.error_message = error_message

        # Tell s3_mark_required that this validator doesn't accept NULL values
        self.mark_required = True

        self.schema = LAT_SCHEMA
        self.minimum = -90
        self.maximum = 90

    # -------------------------------------------------------------------------
    def __call__(self, value):

        if value is None:
            return value, self.error_message
        try:
            value = float(value)
        except ValueError:
            # DMS format
            match = self.schema.match(value)
            if not match:
                return value, self.error_message
            else:
                try:
                    d = float(match.group(1))
                    m = float(match.group(2))
                    s = float(match.group(3))
                except (ValueError, TypeError):
                    return value, self.error_message

                h = match.group(5)
                sign = -1 if h in ("S", "W") else 1

                deg = sign * (d + m / 60 + s / 3600)
        else:
            deg = value

        if self.minimum <= deg <= self.maximum:
            return (deg, None)
        else:
            return (value, self.error_message)

# =============================================================================
class IS_LON(IS_LAT):
    """
        example:

        INPUT(_type="text", _name="name", requires=IS_LON())

        Longitude has to be in decimal degrees between -180 & 180
        - we attempt to convert DMS format into decimal degrees
    """

    def __init__(self,
                 error_message = "Longitude/Easting should be between -180 & 180!"
                 ):

        super(IS_LON, self).__init__(error_message=error_message)

        self.schema = LON_SCHEMA
        self.minimum = -180
        self.maximum = 180

# =============================================================================
class IS_LAT_LON(Validator):
    """
        Designed for use within the S3LocationLatLonWidget.
        For Create forms, this will create a new location from the additional fields
        For Update forms, this will check that we have a valid location_id FK and update any changes

        @ToDo: Audit
    """

    def __init__(self,
                 field,
                 ):

        self.field = field
        # Tell s3_mark_required that this validator doesn't accept NULL values
        self.mark_required = True

    # -------------------------------------------------------------------------
    def __call__(self, value):

        if current.response.s3.bulk:
            # Pointless in imports
            return (value, None)

        selector = str(self.field).replace(".", "_")
        post_vars = current.request.post_vars
        lat = post_vars.get("%s_lat" % selector, None)
        if lat == "":
            lat = None
        lon = post_vars.get("%s_lon" % selector, None)
        if lon == "":
            lon = None

        if lat is None or lon is None:
            # We don't accept None
            return (value, current.T("Latitude and Longitude are required"))

        # Check Lat
        lat, error = IS_LAT()(lat)
        if error:
            return (value, error)

        # Check Lon
        lon, error = IS_LON()(lon)
        if error:
            return (value, error)

        if value:
            # update
            db = current.db
            db(db.gis_location.id == value).update(lat=lat, lon=lon)
        else:
            # create
            value = current.db.gis_location.insert(lat=lat, lon=lon)

        # OK
        return (value, None)

# =============================================================================
class IS_NUMBER(object):
    """
        Used by s3data.py to wrap IS_INT_AMOUNT & IS_FLOAT_AMOUNT
    """

    # -------------------------------------------------------------------------
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
                 error_message=None,
                 ):

        IS_INT_IN_RANGE.__init__(self,
                                 minimum=minimum,
                                 maximum=maximum,
                                 error_message=error_message,
                                 )

    # -------------------------------------------------------------------------
    def __call__(self, value):

        thousands_sep = current.deployment_settings.get_L10n_thousands_separator()
        if thousands_sep:
            value = s3_str(value).replace(thousands_sep, "")

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
        except ValueError:
            intnumber = number

        settings = current.deployment_settings
        THOUSAND_SEPARATOR = settings.get_L10n_thousands_separator()
        NUMBER_GROUPING = settings.get_L10n_thousands_grouping()

        # The negative/positive sign for the number
        if float(number) < 0:
            sign = "-"
        else:
            sign = ""

        str_number = str(intnumber)

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
                 dot=None,
                 ):

        if dot is None:
            dot = current.deployment_settings.get_L10n_decimal_separator()

        IS_FLOAT_IN_RANGE.__init__(self,
                                   minimum=minimum,
                                   maximum=maximum,
                                   error_message=error_message,
                                   dot=dot,
                                   )

    # -------------------------------------------------------------------------
    def __call__(self, value):

        thousands_sep = current.deployment_settings.get_L10n_thousands_separator()
        if thousands_sep and isinstance(value, basestring):
            value = s3_str(s3_unicode(value).replace(thousands_sep, ""))

        return IS_FLOAT_IN_RANGE.__call__(self, value)

    # -------------------------------------------------------------------------
    @staticmethod
    def represent(number, precision=None, fixed=False):
        """
            Change the format of the number depending on the language
            Based on https://code.djangoproject.com/browser/django/trunk/django/utils/numberformat.py

            @param number: the number
            @param precision: the number of decimal places to show
            @param fixed: show decimal places even if the decimal part is 0
        """

        if number is None:
            return ""

        DECIMAL_SEPARATOR = current.deployment_settings.get_L10n_decimal_separator()

        if precision is not None:
            str_number = format(number, ".0%df" % precision)
        else:
            # Default to any precision
            str_number = format(number, "f").rstrip("0") \
                                            .rstrip(DECIMAL_SEPARATOR)

        if "." in str_number:
            int_part, dec_part = str_number.split(".")
        else:
            int_part, dec_part = str_number, ""

        if dec_part and int(dec_part) == 0 and not fixed:
            # Omit decimal part if zero
            dec_part = ""

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
                 error_message="must be a 6 digit hex code! (format: rrggbb)"
                ):
        IS_MATCH.__init__(self, "^[0-9a-fA-F]{6}$", error_message)

# =============================================================================
regex1 = re.compile(r"[\w_]+\.[\w_]+")
regex2 = re.compile(r"%\((?P<name>[^\)]+)\)s")

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
                 realms=None,
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
            @param realms: only include records belonging to the listed realms
                           (if None, all readable records will be included)
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
        elif hasattr(label, "bulk"):
            # S3Represent
            ks = [kfield]
            if label.custom_lookup:
                # Represent uses a custom lookup, so we only
                # retrieve the keys here
                fields = [kfield]
                if orderby is None:
                    orderby = field
            else:
                # Represent uses a standard field lookup, so
                # we can do that right here
                label._setup()
                fields = list(label.fields)
                if kfield not in fields:
                    fields.insert(0, kfield)
                # Unlikely, but possible: represent and validator
                # using different keys - commented for now for
                # performance reasons (re-enable if ever necessary)
                #key = label.key
                #if key and key not in fields:
                    #fields.insert(0, key)
        else:
            ks = [kfield]
            try:
                table = current.s3db[ktable]
                fields =[str(f) for f in table if f.name not in ("wkt", "the_geom")]
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

        self.realms = realms
        self.updateable = updateable
        self.instance_types = instance_types

    # -------------------------------------------------------------------------
    def set_self_id(self, record_id):
        if self._and:
            self._and.record_id = record_id

    # -------------------------------------------------------------------------
    def set_filter(self,
                   filterby = None,
                   filter_opts = None,
                   not_filterby = None,
                   not_filter_opts = None):
        """
            This can be called from prep to apply a filter based on
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
        """
            Look up selectable options from the database
        """

        dbset = self.dbset
        db = dbset._db

        ktablename = self.ktable
        if ktablename not in db:
            table = current.s3db.table(ktablename, db_only=True)
        else:
            table = db[ktablename]

        if table:
            if self.fields == "all":
                fields = [table[f] for f in table.fields if f not in ("wkt", "the_geom")]
            else:
                fieldnames = [f.split(".")[1] if "." in f else f for f in self.fields]
                fields = [table[k] for k in fieldnames if k in table.fields]

            if db._dbname not in ("gql", "gae"):

                orderby = self.orderby or reduce(lambda a, b: a|b, fields)
                groupby = self.groupby

                left = self.left

                dd = {"orderby": orderby, "groupby": groupby}
                query, qleft = self.query(table, fields=fields, dd=dd)
                if qleft is not None:
                    if left is not None:
                        if not isinstance(qleft, list):
                            qleft = [qleft]
                        ljoins = [str(join) for join in left]
                        for join in qleft:
                            ljoin = str(join)
                            if ljoin not in ljoins:
                                left.append(join)
                                ljoins.append(ljoin)
                    else:
                        left = qleft
                if left is not None:
                    dd["left"] = left

                # Make sure we have all ORDERBY fields in the query
                # - required with distinct=True (PostgreSQL)
                fieldnames = set(str(f) for f in fields)
                for f in s3_orderby_fields(table, dd.get("orderby")):
                    fieldname = str(f)
                    if fieldname not in fieldnames:
                        fields.append(f)
                        fieldnames.add(fieldname)

                records = dbset(query).select(distinct=True, *fields, **dd)

            else:
                # Note this does not support filtering.
                orderby = self.orderby or \
                          reduce(lambda a, b: a|b, (f for f in fields if f.type != "id"))
                records = dbset.select(table.ALL,
                                       # Caching breaks Colorbox dropdown refreshes
                                       #cache=(current.cache.ram, 60),
                                       orderby = orderby,
                                       )

            self.theset = [str(r[self.kfield]) for r in records]

            label = self.label
            try:
                # Is callable
                if hasattr(label, "bulk"):
                    # S3Represent => use bulk option
                    d = label.bulk(None,
                                   rows = records,
                                   list_type = False,
                                   show_link = False,
                                   )
                    labels = [d.get(r[self.kfield], d[None]) for r in records]
                else:
                    # Other representation function
                    labels = [label(r) for r in records]
            except TypeError:
                if isinstance(label, str):
                    labels = [label % dict(r) for r in records]
                elif isinstance(label, (list, tuple)):
                    labels = [" ".join([r[l] for l in label if l in r])
                              for r in records
                              ]
                elif "name" in table:
                    labels = [r.name for r in records]
                else:
                    labels = [r[self.kfield] for r in records]
            self.labels = labels

            if labels and self.sort:

                items = sorted(zip(self.theset, self.labels),
                               key = lambda item: s3_unicode(item[1]).lower(),
                               )
                self.theset, self.labels = zip(*items)

        else:
            self.theset = None
            self.labels = None

    # -------------------------------------------------------------------------
    def query(self, table, fields=None, dd=None):
        """
            Construct the query to lookup the options (separated from
            build_set so the query can be extracted and used in other
            lookups, e.g. filter options).

            @param table: the lookup table
            @param fields: fields (updatable list)
            @param dd: additional query options (updatable dict)
        """

        # Accessible-query
        method = "update" if self.updateable else "read"
        query, left = self.accessible_query(method, table,
                                            instance_types=self.instance_types)

        # Available-query
        if "deleted" in table:
            query &= (table["deleted"] != True)

        # Realms filter?
        if self.realms:
            auth = current.auth
            if auth.is_logged_in() and \
               auth.get_system_roles().ADMIN in auth.user.realms:
                # Admin doesn't filter
                pass
            else:
                query &= auth.permission.realm_query(table, self.realms)

        all_fields = [str(f) for f in fields] if fields is not None else []

        filterby = self.filterby
        if filterby and filterby in table:

            filter_opts = self.filter_opts

            if filter_opts:
                if None in filter_opts:
                    # Needs special handling (doesn't show up in 'belongs')
                    _query = (table[filterby] == None)
                    filter_opts = [f for f in filter_opts if f is not None]
                    if filter_opts:
                        _query = _query | (table[filterby].belongs(filter_opts))
                    query &= _query
                else:
                    query &= (table[filterby].belongs(filter_opts))

            if not self.orderby and \
               fields is not None and dd is not None:
                filterby_field = table[filterby]
                if dd is not None:
                    dd.update(orderby=filterby_field)
                if str(filterby_field) not in all_fields:
                    fields.append(filterby_field)
                    all_fields.append(str(filterby_field))

        not_filterby = self.not_filterby
        if not_filterby and not_filterby in table:

            not_filter_opts = self.not_filter_opts

            if not_filter_opts:
                if None in not_filter_opts:
                    # Needs special handling (doesn't show up in 'belongs')
                    _query = (table[not_filterby] == None)
                    not_filter_opts = [f for f in not_filter_opts if f is not None]
                    if not_filter_opts:
                        _query = _query | (table[not_filterby].belongs(not_filter_opts))
                    query &= (~_query)
                else:
                    query &= (~(table[not_filterby].belongs(not_filter_opts)))

            if not self.orderby and \
               fields is not None and dd is not None:
                filterby_field = table[not_filterby]
                if dd is not None:
                    dd.update(orderby=filterby_field)
                if str(filterby_field) not in all_fields:
                    fields.append(filterby_field)
                    all_fields.append(str(filterby_field))

        return query, left

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

            @return: tuple (query, left) where query is the query and left joins
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

        # Translate error message if string
        error_message = self.error_message
        if isinstance(error_message, basestring):
            error_message = current.T(error_message)

        try:
            dbset = self.dbset
            table = dbset._db[self.ktable]
            deleted_q = (table["deleted"] == False) if ("deleted" in table) else False
            filter_opts_q = False
            filterby = self.filterby
            if filterby and filterby in table:
                filter_opts = self.filter_opts
                if filter_opts:
                    if None in filter_opts:
                        # Needs special handling (doesn't show up in 'belongs')
                        filter_opts_q = (table[filterby] == None)
                        filter_opts = [f for f in filter_opts if f is not None]
                        if filter_opts:
                            filter_opts_q |= (table[filterby].belongs(filter_opts))
                    else:
                        filter_opts_q = (table[filterby].belongs(filter_opts))

            if self.multiple:
                if isinstance(value, list):
                    values = [str(v) for v in value]
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
                        return (value, error_message)
                else:
                    field = table[self.kfield]
                    query = None
                    for v in values:
                        q = (field == v)
                        query = (query | q) if query is not None else q
                    if filter_opts_q != False:
                        query = (filter_opts_q & (query)) \
                                if query is not None else filter_opts_q
                    if deleted_q != False:
                        query = (deleted_q & (query)) \
                                if query is not None else deleted_q
                    if dbset(query).count() < 1:
                        return (value, error_message)
                    return (values, None)
            elif self.theset:
                if str(value) in self.theset:
                    if self._and:
                        return self._and(value)
                    else:
                        return (value, None)
            else:
                values = [value]
                query = None
                for v in values:
                    q = (table[self.kfield] == v)
                    query = (query | q) if query is not None else q
                if filter_opts_q != False:
                    query = (filter_opts_q & (query)) \
                            if query is not None else filter_opts_q
                if deleted_q != False:
                    query = (deleted_q & (query)) \
                            if query is not None else deleted_q
                if dbset(query).count():
                    if self._and:
                        return self._and(value)
                    else:
                        return (value, None)
        except:
            pass

        return (value, error_message)


# =============================================================================
class IS_ONE_OF(IS_ONE_OF_EMPTY):
    """
        Extends IS_ONE_OF_EMPTY by restoring the 'options' method.
    """

    def options(self, zero=True):

        self.build_set()
        theset, labels = self.theset, self.labels
        if theset is None or labels is None:
            items = []
        else:
            items = list(zip(theset, labels))
        if zero and self.zero is not None and not self.multiple:
            items.insert(0, ("", self.zero))
        return items

# =============================================================================
class IS_ONE_OF_EMPTY_SELECT(IS_ONE_OF_EMPTY):

    """
        Extends IS_ONE_OF_EMPTY by displaying an empty SELECT (instead of INPUT)
    """

    def options(self, zero=True):
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
            # Empty => error
            return (value, translate(self.error_message))

        if value in self.allowed_override:
            # Uniqueness-requirement overridden
            return (value, None)

        # Establish table and field
        (tablename, fieldname) = str(self.field).split(".")
        dbset = self.dbset
        table = dbset.db[tablename]
        field = table[fieldname]

        # Does the table allow archiving ("soft-delete")?
        archived = "deleted" in table

        # Does the table use multiple columns as key?
        record_id = self.record_id
        keys = list(record_id.keys()) if isinstance(record_id, dict) else None

        # Build duplicate query
        # => if the field has a unique-constraint, we must include
        #    archived ("soft-deleted") records, otherwise the
        #    validator will pass, but the DB-write will crash
        query = (field == value)
        if not field.unique and archived:
            query = (table["deleted"] == False) & query

        # Limit the fields we extract to just keys+deleted
        fields = []
        if keys:
            fields = [table[k] for k in keys]
        else:
            fields = [table._id]
        if archived:
            fields.append(table.deleted)

        # Find conflict
        row = dbset(query).select(limitby=(0, 1), *fields).first()
        if row:
            if keys:
                # Keyed table
                for f in keys:
                    if str(getattr(row, f)) != str(record_id[f]):
                        return (value, translate(self.error_message))

            elif str(row[table._id.name]) != str(record_id):

                if archived and row.deleted and field.type in ("string", "text"):
                    # Table supports archiving, and the conflicting
                    # record is "deleted" => try updating the archived
                    # record by appending a random tag to the field value
                    import random
                    tagged = "%s.[%s]" % (value,
                                         "".join(random.choice("abcdefghijklmnopqrstuvwxyz")
                                                 for _ in range(8))
                                         )
                    try:
                        row.update_record(**{fieldname: tagged})
                    except:
                        # Failed => nothing else we can try
                        return (value, translate(self.error_message))
                else:
                    return (value, translate(self.error_message))

        return (value, None)

# =============================================================================
class IS_LOCATION(Validator):
    """
        Allow all locations, or locations by level.
    """

    def __init__(self,
                 level = None,
                 error_message = None
                 ):

        self.level = level # can be a List or a single element
        self.error_message = error_message
        # Make it like IS_ONE_OF to support AddResourceLink
        self.ktable = "gis_location"
        self.kfield = "id"
        # Tell s3_mark_required that this validator doesn't accept NULL values
        self.mark_required = True

    # -------------------------------------------------------------------------
    def __call__(self, value):

        level = self.level
        if level == "L0":
            # Use cached countries. This returns name if id is for a country.
            try:
                location_id = int(value)
            except ValueError:
                ok = False
            else:
                ok = current.gis.get_country(location_id)
        else:
            db = current.db
            table = db.gis_location
            query = (table.id == value) & (table.deleted == False)
            if level:
                if isinstance(level, (tuple, list)):
                    if None in level:
                        # None needs special handling
                        level = [l for l in level if l is not None]
                        query &= ((table.level.belongs(level)) | \
                                  (table.level == None))
                    else:
                        query &= (table.level.belongs(level))
                else:
                    query &= (table.level == level)
            ok = db(query).select(table.id, limitby=(0, 1)).first()
        if ok:
            return (value, None)
        else:
            return (value, self.error_message or current.T("Invalid Location!"))

# =============================================================================
class IS_PROCESSED_IMAGE(Validator):
    """
        Uses an S3ImageCropWidget to allow the user to crop/scale images and
        processes the results sent by the browser.

        @param file_cb: callback that returns the file for this field

        @param error_message: the error message to be returned

        @param image_bounds: the boundaries for the processed image

        @param upload_path: upload path for the image
    """

    def __init__(self,
                 field_name,
                 file_cb,
                 error_message="No image was specified!",
                 image_bounds=(300, 300),
                 upload_path=None,
                 ):

        self.field_name = field_name
        self.file_cb = file_cb
        self.error_message = error_message
        self.image_bounds = image_bounds
        self.upload_path = upload_path

    def __call__(self, value):

        if current.response.s3.bulk:
            # Pointless in imports
            return (value, None)

        r = current.request

        if r.env.request_method == "GET":
            return (value, None)

        post_vars = r.post_vars

        # If there's a newly uploaded file, accept it. It'll be processed in
        # the update form.
        # NOTE: A FieldStorage with data evaluates as False (odd!)
        uploaded_image = post_vars.get(self.field_name)
        if uploaded_image not in (b"", None): # Py 3.x it's b"", which is equivalent to "" in Py 2.x
            return (uploaded_image, None)

        cropped_image = post_vars.get("imagecrop-data")
        uploaded_image = self.file_cb()

        if not (cropped_image or uploaded_image):
            return value, current.T(self.error_message)

        # Decode the base64-encoded image from the client side image crop
        # process if, that worked.
        if cropped_image:
            import base64
            import uuid

            metadata, cropped_image = cropped_image.split(",")
            #filename, datatype, enctype = metadata.split(";")
            filename = metadata.split(";", 1)[0]

            f = Storage()
            f.filename = uuid.uuid4().hex + filename
            f.file = BytesIO(base64.b64decode(cropped_image))

            return (f, None)

        # Crop the image, if we've got the crop points.
        points = post_vars.get("imagecrop-points")
        if points and uploaded_image:
            import os
            points = [float(p) for p in points.split(",")]

            if not self.upload_path:
                path = os.path.join(r.folder, "uploads", "images", uploaded_image)
            else:
                path = os.path.join(self.upload_path, uploaded_image)

            
            current.s3task.run_async("crop_image",
                            args = [path] + points + [self.image_bounds[0]])

        return (None, None)

# =============================================================================
class IS_UTC_OFFSET(Validator):
    """
        Validates a given string value as UTC offset in the format +/-HHMM

        @param error_message:   the error message to be returned

        @note:
            all leading parts of the string (before the trailing offset specification)
            will be ignored and replaced by 'UTC ' in the return value, if the string
            passes through.
    """

    def __init__(self, error_message="invalid UTC offset!"):

        self.error_message = error_message

    # -------------------------------------------------------------------------
    def __call__(self, value):

        if value and isinstance(value, str):

            offset = S3DateTime.get_offset_value(value)
            if offset is not None:
                hours, seconds = divmod(abs(offset), 3600)
                minutes = int(seconds / 60)
                sign = "-" if offset < 0 else "+"
                return ("%s%02d%02d" % (sign, hours, minutes), None)

        return (value, self.error_message)

# =============================================================================
class IS_UTC_DATETIME(Validator):
    """
        Validates a given date/time and returns it as timezone-naive
        datetime object in UTC. Accepted input types are strings (in
        local format), datetime.datetime and datetime.date.

        Example:
            - INPUT(_type="text", _name="name", requires=IS_UTC_DATETIME())

        @note: a date/time string must be in local format, and can have
               an optional trailing UTC offset specified as +/-HHMM
               (+ for eastern, - for western timezones)
        @note: dates stretch 8 hours West and 16 hours East of the current
               time zone, i.e. the most Eastern timezones are on the next
               day.
    """

    def __init__(self,
                 format=None,
                 error_message=None,
                 offset_error=None,
                 calendar=None,
                 minimum=None,
                 maximum=None):
        """
            Constructor

            @param format: strptime/strftime format template string, for
                           directives refer to your strptime implementation
            @param error_message: error message for invalid date/times
            @param offset_error: error message for invalid UTC offset
            @param calendar: calendar to use for string evaluation, defaults
                             to current.calendar
            @param minimum: the minimum acceptable date/time
            @param maximum: the maximum acceptable date/time
        """

        if format is None:
            self.format = str(current.deployment_settings.get_L10n_datetime_format())
        else:
            self.format = str(format)

        if isinstance(calendar, basestring):
            # Instantiate calendar by name
            from .s3datetime import S3Calendar
            calendar = S3Calendar(calendar)
        elif calendar == None:
            calendar = current.calendar
        self.calendar = calendar

        self.minimum = minimum
        self.maximum = maximum

        # Default error messages
        T = current.T
        if error_message is None:
            if minimum is None and maximum is None:
                error_message = T("Date/Time is required!")
            elif minimum is None:
                error_message = T("Date/Time must be %(max)s or earlier!")
            elif maximum is None:
                error_message = T("Date/Time must be %(min)s or later!")
            else:
                error_message = T("Date/Time must be between %(min)s and %(max)s!")
        if offset_error is None:
            offset_error = T("Invalid UTC offset!")

        # Localized minimum/maximum
        mindt = self.formatter(minimum) if minimum else ""
        maxdt = self.formatter(maximum) if maximum else ""

        # Store error messages
        self.error_message = error_message % {"min": mindt, "max": maxdt}
        self.offset_error = offset_error

    # -------------------------------------------------------------------------
    def __call__(self, value):
        """
            Validate a value, and convert it into a timezone-naive
            datetime.datetime object as necessary

            @param value: the value to validate
            @return: tuple (value, error)
        """

        if isinstance(value, basestring):

            val = value.strip()

            # Split date/time and UTC offset
            if len(val) > 5 and val[-5] in ("+", "-") and val[-4:].isdigit():
                dtstr, utc_offset = val[0:-5].strip(), val[-5:]
            else:
                dtstr, utc_offset = val, None

            # Convert into datetime object
            dt = self.calendar.parse_datetime(dtstr,
                                              dtfmt=self.format,
                                              local=True,
                                              )
            if dt is None:
                # Try parsing as date
                dt_ = self.calendar.parse_date(dtstr)
                if dt_ is None:
                    return(value, self.error_message)
                dt = datetime.datetime.combine(dt_, datetime.datetime.min.time())
        elif isinstance(value, datetime.datetime):
            dt = value
            utc_offset = None
        elif isinstance(value, datetime.date):
            # Default to 8:00 hours in the current timezone
            dt = datetime.datetime.combine(value, datetime.time(8, 0, 0))
            utc_offset = None
        else:
            # Invalid type
            return value, self.error_message

        # Convert to UTC and make tz-naive
        if not dt.tzinfo and utc_offset:
            offset = S3DateTime.get_offset_value(utc_offset)
            if not -86340 < offset < 86340:
                return (val, self.offset_error)
            offset = datetime.timedelta(seconds=offset)
            dt_utc = (dt - offset).replace(tzinfo=None)
        else:
            dt_utc = S3DateTime.to_utc(dt)

        # Validate
        if self.minimum and dt_utc < self.minimum or \
           self.maximum and dt_utc > self.maximum:
            return (dt_utc, self.error_message)

        return (dt_utc, None)

    # -------------------------------------------------------------------------
    def formatter(self, value):
        """
            Format a datetime as string.

            @param value: the value
        """

        if not value:
            return current.messages["NONE"]

        result = self.calendar.format_datetime(S3DateTime.to_local(value),
                                               dtfmt=self.format,
                                               local=True,
                                               )
        return result

# =============================================================================
class IS_UTC_DATE(IS_UTC_DATETIME):
    """
        Validates a given date and returns the corresponding datetime.date
        object in UTC. Accepted input types are strings (in local format),
        datetime.datetime and datetime.date.

        Example:
            - INPUT(_type="text", _name="name", requires=IS_UTC_DATE())

        @note: dates stretch 8 hours West and 16 hours East of the current
               time zone, i.e. the most Eastern timezones are on the next
               day.
    """

    def __init__(self,
                 format=None,
                 error_message=None,
                 offset_error=None,
                 calendar=None,
                 minimum=None,
                 maximum=None):
        """
            Constructor

            @param format: strptime/strftime format template string, for
                           directives refer to your strptime implementation
            @param error_message: error message for invalid date/times
            @param offset_error: error message for invalid UTC offset
            @param calendar: calendar to use for string evaluation, defaults
                             to current.calendar
            @param minimum: the minimum acceptable date (datetime.date)
            @param maximum: the maximum acceptable date (datetime.date)
        """

        if format is None:
            self.format = str(current.deployment_settings.get_L10n_date_format())
        else:
            self.format = str(format)

        if isinstance(calendar, basestring):
            # Instantiate calendar by name
            from .s3datetime import S3Calendar
            calendar = S3Calendar(calendar)
        elif calendar == None:
            calendar = current.calendar
        self.calendar = calendar

        self.minimum = minimum
        self.maximum = maximum

        # Default error messages
        T = current.T
        if error_message is None:
            if minimum is None and maximum is None:
                error_message = T("Date is required!")
            elif minimum is None:
                error_message = T("Date must be %(max)s or earlier!")
            elif maximum is None:
                error_message = T("Date must be %(min)s or later!")
            else:
                error_message = T("Date must be between %(min)s and %(max)s!")
        if offset_error is None:
            offset_error = T("Invalid UTC offset!")

        # Localized minimum/maximum
        mindt = self.formatter(minimum) if minimum else ""
        maxdt = self.formatter(maximum) if maximum else ""

        # Store error messages
        self.error_message = error_message % {"min": mindt, "max": maxdt}
        self.offset_error = offset_error

    # -------------------------------------------------------------------------
    def __call__(self, value):
        """
            Validate a value, and convert it into a datetime.date object
            as necessary

            @param value: the value to validate
            @return: tuple (value, error)
        """

        is_datetime = False

        if isinstance(value, basestring):
            # Convert into date object
            dt = self.calendar.parse_date(value.strip(),
                                          dtfmt=self.format,
                                          local=True,
                                          )
            if dt is None:
                return(value, self.error_message)
        elif isinstance(value, datetime.datetime):
            dt = value
            is_datetime = True
        elif isinstance(value, datetime.date):
            # Default to 0:00 hours in the current timezone
            dt = value
        else:
            # Invalid type
            return (value, self.error_message)

        # Convert to UTC
        if is_datetime:
            dt_utc = S3DateTime.to_utc(dt)
        else:
            # Convert to standard time 08:00 hours
            dt = datetime.datetime.combine(dt, datetime.time(8, 0, 0))
            dt_utc = S3DateTime.to_utc(dt)
        dt_utc = dt_utc.date()

        # Validate
        if self.minimum and dt_utc < self.minimum or \
           self.maximum and dt_utc > self.maximum:
            return (value, self.error_message)

        return (dt_utc, None)

    # -------------------------------------------------------------------------
    def formatter(self, value):
        """
            Format a date as string.

            @param value: the value
        """

        if not value:
            return current.messages["NONE"]

        #value = datetime.datetime.combine(value, datetime.time(8, 0, 0))
        value = S3DateTime.to_local(value)

        #offset = self.delta()
        #if offset:
            #delta = datetime.timedelta(seconds=offset)
            #if not isinstance(value, datetime.datetime):
                #combine = datetime.datetime.combine
                ## Compute the break point
                #bp = (combine(value, datetime.time(8, 0, 0)) - delta).time()
                #value = combine(value, bp)
            #value += delta

        result = self.calendar.format_date(value,
                                           dtfmt=self.format,
                                           local=True,
                                           )

        return result

# =============================================================================
class IS_ACL(IS_IN_SET):

    """
        Validator for ACLs

        @attention: Incomplete! Does not validate yet, but just convert.
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
class QUANTITY_INV_ITEM(Validator):
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
            track_item_id = args[2]
            # @ToDo: Optimise with limitby=(0,1)
            track_record = current.s3db.inv_track_item[track_item_id]
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
            requires = IS_EMPTY_OR(IS_IN_SET_LAZY(
                lambda: gis.get_countries(key_type="code"))),
            label = T("Nationality"),
            represent = lambda code: gis.get_country(code, key_type="code") or UNKNOWN_OPT)

        Keyword parameters are same as for IS_IN_SET, except for labels, which
        is not replaced by a function that parallels theset_fn, since ordering
        is problematic if theset_fn returns a dict.
    """

    def __init__(self,
                 theset_fn,
                 represent = None,
                 error_message = "value not allowed",
                 multiple = False,
                 zero = "",
                 sort = False,
                 ):

        self.multiple = multiple
        if not callable(theset_fn):
            raise TypeError("Argument must be a callable.")
        self.theset_fn = theset_fn
        self.theset = None
        self.labels = None
        self.represent = represent
        self.error_message = error_message
        self.zero = zero
        self.sort = sort

    # -------------------------------------------------------------------------
    def _make_theset(self):

        theset = self.theset_fn()
        if theset:
            if isinstance(theset, dict):
                self.theset = [str(item) for item in theset]
                self.labels = list(theset.values())
            elif isinstance(theset, (tuple, list)):  # @ToDo: Can this be a Rows?
                if isinstance(theset[0], (tuple, list)) and len(theset[0])==2:
                    self.theset = [str(item) for item, label in theset]
                    self.labels = [str(label) for item, label in theset]
                else:
                    self.theset = [str(item) for item in theset]
                    represent = self.represent
                    if represent:
                        self.labels = [represent(item) for item in theset]
            else:
                self.theset = theset
        else:
            self.theset = []

    # -------------------------------------------------------------------------
    def options(self, zero=True):

        if not self.theset:
            self._make_theset()
        if not self.labels:
            items = [(k, k) for (i, k) in enumerate(self.theset)]
        else:
            items = [(k, self.labels[i]) for (i, k) in enumerate(self.theset)]
        if self.sort:
            items.sort(options_sorter)
        if zero and not self.zero is None and not self.multiple:
            items.insert(0, ("", self.zero))
        return items

    # -------------------------------------------------------------------------
    def __call__(self, value):

        if not self.theset:
            self._make_theset()
        if self.multiple:
            ### if below was values = re.compile("[\w\-:]+").findall(str(value))
            if isinstance(value, STRING_TYPES):
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
            if isinstance(self.multiple, (tuple, list)) and \
               not self.multiple[0] <= len(values) < self.multiple[1]:
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

# =============================================================================
class IS_PERSON_GENDER(IS_IN_SET):
    """
        Special validator for pr_person.gender and derivates,
        accepts the "O" option even if it's not in the set.
    """

    def __call__(self, value):

        if value == 4:
            # 4 = other, always accepted even if hidden
            return value, None
        else:
            return super(IS_PERSON_GENDER, self).__call__(value)

# =============================================================================
class IS_PHONE_NUMBER(Validator):
    """
        Validator for single phone numbers with option to
        enforce E.123 international notation (with leading +
        and no punctuation or spaces).
    """

    def __init__(self,
                 international = False,
                 error_message = None):
        """
            Constructor

            @param international: enforce E.123 international notation,
                                  no effect if turned off globally in
                                  deployment settings
            @param error_message: alternative error message
        """

        self.international = international
        self.error_message = error_message

    def __call__(self, value):
        """
            Validation of a value

            @param value: the value
            @return: tuple (value, error), where error is None if value
                     is valid. With international=True, the value returned
                     is converted into E.123 international notation.
        """

        if isinstance(value, basestring):
            value = value.strip()
            if value and value[0] == unichr(8206):
                # Strip the LRM character
                value = value[1:]
            number = s3_str(value)
            number, error = s3_single_phone_requires(number)
        else:
            error = True

        if not error:
            if self.international and \
               current.deployment_settings \
                      .get_msg_require_international_phone_numbers():

                # Configure alternative error message
                error_message = self.error_message
                if not error_message:
                    error_message = current.T("Enter phone number in international format like +46783754957")

                # Require E.123 international format
                number = "".join(re.findall(r"[\d+]+", number))
                match = re.match(r"(\+)([1-9]\d+)$", number)
                #match = re.match("(\+|00|\+00)([1-9]\d+)$", number)

                if match:
                    number = "+%s" % match.groups()[1]
                    return (number, None)
            else:
                return (number, None)

        error_message = self.error_message
        if not error_message:
            error_message = current.T("Enter a valid phone number")

        return (value, error_message)

# =============================================================================
class IS_PHONE_NUMBER_MULTI(Validator):
    """
        Validator for multiple phone numbers.
    """

    def __init__(self,
                 error_message = None):
        """
            Constructor

            @param error_message: alternative error message
        """

        self.error_message = error_message

    def __call__(self, value):
        """
            Validation of a value

            @param value: the value
            @return: tuple (value, error), where error is None if value
                     is valid.
        """

        value = value.strip()
        if value[0] == unichr(8206):
            # Strip the LRM character
            value = value[1:]
        number = s3_str(value)
        number, error = s3_phone_requires(number)
        if not error:
            return (number, None)

        error_message = self.error_message
        if not error_message:
            error_message = current.T("Enter a valid phone number")

        return (value, error_message)

# =============================================================================
class IS_DYNAMIC_FIELDNAME(Validator):
    """ Validator for field names in dynamic tables """

    PATTERN = re.compile("^[a-z]+[a-z0-9_]*$")

    def __init__(self,
                 error_message = "Invalid field name",
                 ):
        """
            Constructor

            @param error_message: the error message for invalid values
        """

        self.error_message = error_message

    # -------------------------------------------------------------------------
    def __call__(self, value):
        """
            Validation of a value

            @param value: the value
            @return: tuple (value, error)
        """

        if value:

            name = str(value).lower().strip()

            from .s3fields import s3_all_meta_field_names

            if name != "id" and \
               name not in s3_all_meta_field_names() and \
               self.PATTERN.match(name):
                return (name, None)

        return (value, self.error_message)

# =============================================================================
class IS_DYNAMIC_FIELDTYPE(Validator):
    """ Validator for field types in dynamic tables """

    SUPPORTED_TYPES = ("boolean",
                       "date",
                       "datetime",
                       "double",
                       "integer",
                       "reference",
                       "string",
                       "text",
                       "upload",
                       "json",
                       "list:integer",
                       "list:string",
                       )

    def __init__(self,
                 error_message = "Unsupported field type",
                 ):
        """
            Constructor

            @param error_message: the error message for invalid values
        """

        self.error_message = error_message

    # -------------------------------------------------------------------------
    def __call__(self, value):
        """
            Validation of a value

            @param value: the value
            @return: tuple (value, error)
        """

        if value:

            field_type = str(value).lower().strip()

            items = field_type.split(" ")
            base_type = items[0]

            if base_type == "reference":

                # Verify that referenced table is specified and exists
                if len(items) > 1:
                    ktablename = items[1].split(".")[0]
                    ktable = current.s3db.table(ktablename, db_only=True)
                    if ktable:
                        return (field_type, None)

            elif base_type in self.SUPPORTED_TYPES:
                return (field_type, None)

        return (value, self.error_message)

# =============================================================================
class IS_ISO639_2_LANGUAGE_CODE(IS_IN_SET):
    """
        Validate ISO639-2 Alpha-2/Alpha-3 language codes
    """

    def __init__(self,
                 error_message = "Invalid language code",
                 multiple = False,
                 select = DEFAULT,
                 sort = False,
                 translate = False,
                 zero = "",
                 ):
        """
            Constructor

            @param error_message: alternative error message
            @param multiple: allow selection of multiple options
            @param select: dict of options for the selector,
                           defaults to settings.L10n.languages,
                           set explicitly to None to allow all languages
            @param sort: sort options in selector
            @param translate: translate the language options into
                              the current UI language
            @param zero: use this label for the empty-option (default="")
        """

        super(IS_ISO639_2_LANGUAGE_CODE, self).__init__(
                                                self.language_codes(),
                                                error_message = error_message,
                                                multiple = multiple,
                                                zero = zero,
                                                sort = sort,
                                                )

        if select is DEFAULT:
            self._select = current.deployment_settings.get_L10n_languages()
        else:
            self._select = select
        self.translate = translate

    # -------------------------------------------------------------------------
    def options(self, zero=True):
        """
            Get the options for the selector. This could be only a subset
            of all valid options (self._select), therefore overriding
            superclass function here.
        """

        language_codes = self.language_codes()

        if self._select:
            language_codes_dict = dict(language_codes)
            if self.translate:
                T = current.T
                items = ((k, T(v)) for k, v in self._select.items()
                                   if k in language_codes_dict)
            else:
                items = ((k, v) for k, v in self._select.items()
                                if k in language_codes_dict)
        else:
            if self.translate:
                T = current.T
                items = ((k, T(v)) for k, v in language_codes)
            else:
                items = language_codes

        if self.sort:
            items = sorted(items, key=lambda s: s3_unicode(s[1]).lower())
        else:
            items = list(items)

        if zero and not self.zero is None and not self.multiple:
            items.insert(0, ("", self.zero))

        return items

    # -------------------------------------------------------------------------
    def represent(self, code):
        """
            Represent a language code by language name, uses the
            representation from deployment_settings if available
            (to allow overrides).

            @param code: the language code
        """

        if not code:
            return current.messages["NONE"]

        l10n_languages = current.deployment_settings.get_L10n_languages()
        name = l10n_languages.get(code)
        if not name:
            name = dict(self.language_codes()).get(code.split("-")[0])
            if name is None:
                return current.messages.UNKNOWN_OPT

        if self.translate:
            name = current.T(name)

        return name

    # -------------------------------------------------------------------------
    @classmethod
    def represent_local(cls, code):
        """
            Represent a language code by the name of the language in that
            language. e.g. for Use in a Language dropdown

            @param code: the language code
        """

        if not code:
            return current.messages["NONE"]

        l10n_languages = current.deployment_settings.get_L10n_languages()
        name = l10n_languages.get(code)
        if not name:
            name = dict(cls.language_codes()).get(code.split("-")[0])
            if name is None:
                return current.messages.UNKNOWN_OPT

        T = current.T
        name = s3_str(T(name, language=code))

        return name

    # -------------------------------------------------------------------------
    @staticmethod
    def language_codes():
        """
            Returns a list of tuples of ISO639-1 alpha-2 language
            codes, can also be used to look up the language name

            Just the subset which are useful for Translations
            - 2 letter code preferred, 3-letter code where none exists,
              no 'families' or Old
        """

        lang = [#("aar", "Afar"),
                ("aa", "Afar"),
                #("abk", "Abkhazian"),
                ("ab", "Abkhazian"),
                ("ace", "Achinese"),
                ("ach", "Acoli"),
                ("ada", "Adangme"),
                ("ady", "Adyghe; Adygei"),
                #("afa", "Afro-Asiatic languages"),
                ("afh", "Afrihili"),
                #("afr", "Afrikaans"),
                ("af", "Afrikaans"),
                ("ain", "Ainu"),
                #("aka", "Akan"),
                ("ak", "Akan"),
                ("akk", "Akkadian"),
                #("alb", "Albanian"),
                ("sq", "Albanian"),
                ("ale", "Aleut"),
                #("alg", "Algonquian languages"),
                ("alt", "Southern Altai"),
                #("amh", "Amharic"),
                ("am", "Amharic"),
                #("ang", "English, Old (ca.450-1100)"),
                ("anp", "Angika"),
                #("apa", "Apache languages"),
                #("ara", "Arabic"),
                ("ar", "Arabic"),
                #("arc", "Official Aramaic (700-300 BCE); Imperial Aramaic (700-300 BCE)"),
                #("arg", "Aragonese"),
                ("an", "Aragonese"),
                #("arm", "Armenian"),
                ("hy", "Armenian"),
                ("arn", "Mapudungun; Mapuche"),
                ("arp", "Arapaho"),
                #("art", "Artificial languages"),
                ("arw", "Arawak"),
                #("asm", "Assamese"),
                ("as", "Assamese"),
                ("ast", "Asturian; Bable; Leonese; Asturleonese"),
                #("ath", "Athapascan languages"),
                #("aus", "Australian languages"),
                #("ava", "Avaric"),
                ("av", "Avaric"),
                #("ave", "Avestan"),
                ("ae", "Avestan"),
                ("awa", "Awadhi"),
                #("aym", "Aymara"),
                ("ay", "Aymara"),
                #("aze", "Azerbaijani"),
                ("az", "Azerbaijani"),
                #("bad", "Banda languages"),
                #("bai", "Bamileke languages"),
                #("bak", "Bashkir"),
                ("ba", "Bashkir"),
                ("bal", "Baluchi"),
                #("bam", "Bambara"),
                ("bm", "Bambara"),
                ("ban", "Balinese"),
                #("baq", "Basque"),
                ("eu", "Basque"),
                ("bas", "Basa"),
                #("bat", "Baltic languages"),
                ("bej", "Beja; Bedawiyet"),
                #("bel", "Belarusian"),
                ("be", "Belarusian"),
                ("bem", "Bemba"),
                #("ben", "Bengali"),
                ("bn", "Bengali"),
                #("ber", "Berber languages"),
                ("bho", "Bhojpuri"),
                #("bih", "Bihari languages"),
                #("bh", "Bihari languages"),
                ("bik", "Bikol"),
                ("bin", "Bini; Edo"),
                #("bis", "Bislama"),
                ("bi", "Bislama"),
                ("bla", "Siksika"),
                #("bnt", "Bantu (Other)"),
                #("bos", "Bosnian"),
                ("bs", "Bosnian"),
                ("bra", "Braj"),
                #("bre", "Breton"),
                ("br", "Breton"),
                #("btk", "Batak languages"),
                ("bua", "Buriat"),
                ("bug", "Buginese"),
                #("bul", "Bulgarian"),
                ("bg", "Bulgarian"),
                #("bur", "Burmese"),
                ("my", "Burmese"),
                ("byn", "Blin; Bilin"),
                ("cad", "Caddo"),
                #("cai", "Central American Indian languages"),
                ("car", "Galibi Carib"),
                #("cat", "Catalan; Valencian"),
                ("ca", "Catalan; Valencian"),
                #("cau", "Caucasian languages"),
                ("ceb", "Cebuano"),
                #("cel", "Celtic languages"),
                #("cha", "Chamorro"),
                ("ch", "Chamorro"),
                ("chb", "Chibcha"),
                #("che", "Chechen"),
                ("ce", "Chechen"),
                ("chg", "Chagatai"),
                #("chi", "Chinese"),
                ("zh", "Chinese"),
                ("chk", "Chuukese"),
                ("chm", "Mari"),
                ("chn", "Chinook jargon"),
                ("cho", "Choctaw"),
                ("chp", "Chipewyan; Dene Suline"),
                ("chr", "Cherokee"),
                #("chu", "Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic"),
                ("cu", "Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic"),
                #("chv", "Chuvash"),
                ("cv", "Chuvash"),
                ("chy", "Cheyenne"),
                #("cmc", "Chamic languages"),
                ("cop", "Coptic"),
                #("cor", "Cornish"),
                ("kw", "Cornish"),
                #("cos", "Corsican"),
                ("co", "Corsican"),
                #("cpe", "Creoles and pidgins, English based"),
                #("cpf", "Creoles and pidgins, French-based"),
                #("cpp", "Creoles and pidgins, Portuguese-based"),
                #("cre", "Cree"),
                ("cr", "Cree"),
                ("crh", "Crimean Tatar; Crimean Turkish"),
                #("crp", "Creoles and pidgins"),
                ("csb", "Kashubian"),
                ("cus", "Cushitic languages"),
                #("cze", "Czech"),
                ("cs", "Czech"),
                ("dak", "Dakota"),
                #("dan", "Danish"),
                ("da", "Danish"),
                ("dar", "Dargwa"),
                #("day", "Land Dayak languages"),
                ("del", "Delaware"),
                ("den", "Slave (Athapascan)"),
                ("dgr", "Dogrib"),
                ("din", "Dinka"),
                #("div", "Divehi; Dhivehi; Maldivian"),
                ("dv", "Divehi; Dhivehi; Maldivian"),
                ("doi", "Dogri"),
                #("dra", "Dravidian languages"),
                ("dsb", "Lower Sorbian"),
                ("dua", "Duala"),
                #("dum", "Dutch, Middle (ca.1050-1350)"),
                #("dut", "Dutch; Flemish"),
                ("nl", "Dutch; Flemish"),
                ("dyu", "Dyula"),
                #("dzo", "Dzongkha"),
                ("dz", "Dzongkha"),
                ("efi", "Efik"),
                #("egy", "Egyptian (Ancient)"),
                ("eka", "Ekajuk"),
                ("elx", "Elamite"),
                #("eng", "English"),
                ("en", "English"),
                #("enm", "English, Middle (1100-1500)"),
                #("epo", "Esperanto"),
                ("eo", "Esperanto"),
                #("est", "Estonian"),
                ("et", "Estonian"),
                #("ewe", "Ewe"),
                ("ee", "Ewe"),
                ("ewo", "Ewondo"),
                ("fan", "Fang"),
                #("fao", "Faroese"),
                ("fo", "Faroese"),
                ("fat", "Fanti"),
                #("fij", "Fijian"),
                ("fj", "Fijian"),
                ("fil", "Filipino; Pilipino"),
                #("fin", "Finnish"),
                ("fi", "Finnish"),
                #("fiu", "Finno-Ugrian languages"),
                ("fon", "Fon"),
                #("fre", "French"),
                ("fr", "French"),
                #("frm", "French, Middle (ca.1400-1600)"),
                #("fro", "French, Old (842-ca.1400)"),
                ("frr", "Northern Frisian"),
                ("frs", "Eastern Frisian"),
                #("fry", "Western Frisian"),
                ("fy", "Western Frisian"),
                #("ful", "Fulah"),
                ("ff", "Fulah"),
                ("fur", "Friulian"),
                ("gaa", "Ga"),
                ("gay", "Gayo"),
                ("gba", "Gbaya"),
                #("gem", "Germanic languages"),
                #("geo", "Georgian"),
                ("ka", "Georgian"),
                #("ger", "German"),
                ("de", "German"),
                ("gez", "Geez"),
                ("gil", "Gilbertese"),
                #("gla", "Gaelic; Scottish Gaelic"),
                ("gd", "Gaelic; Scottish Gaelic"),
                #("gle", "Irish"),
                ("ga", "Irish"),
                #("glg", "Galician"),
                ("gl", "Galician"),
                #("glv", "Manx"),
                ("gv", "Manx"),
                #("gmh", "German, Middle High (ca.1050-1500)"),
                #("goh", "German, Old High (ca.750-1050)"),
                ("gon", "Gondi"),
                ("gor", "Gorontalo"),
                ("got", "Gothic"),
                ("grb", "Grebo"),
                #("grc", "Greek, Ancient (to 1453)"),
                #("gre", "Greek, Modern (1453-)"),
                ("el", "Greek"), # "Greek, Modern (1453-)"
                #("grn", "Guarani"),
                ("gn", "Guarani"),
                ("gsw", "Swiss German; Alemannic; Alsatian"),
                #("guj", "Gujarati"),
                ("gu", "Gujarati"),
                ("gwi", "Gwich'in"),
                ("hai", "Haida"),
                #("hat", "Haitian; Haitian Creole"),
                ("ht", "Haitian; Haitian Creole"),
                #("hau", "Hausa"),
                ("ha", "Hausa"),
                ("haw", "Hawaiian"),
                #("heb", "Hebrew"),
                ("he", "Hebrew"),
                #("her", "Herero"),
                ("hz", "Herero"),
                ("hil", "Hiligaynon"),
                #("him", "Himachali languages; Western Pahari languages"),
                #("hin", "Hindi"),
                ("hi", "Hindi"),
                ("hit", "Hittite"),
                ("hmn", "Hmong; Mong"),
                #("hmo", "Hiri Motu"),
                ("ho", "Hiri Motu"),
                #("hrv", "Croatian"),
                ("hr", "Croatian"),
                ("hsb", "Upper Sorbian"),
                #("hun", "Hungarian"),
                ("hu", "Hungarian"),
                ("hup", "Hupa"),
                ("iba", "Iban"),
                #("ibo", "Igbo"),
                ("ig", "Igbo"),
                #("ice", "Icelandic"),
                ("is", "Icelandic"),
                #("ido", "Ido"),
                ("io", "Ido"),
                #("iii", "Sichuan Yi; Nuosu"),
                ("ii", "Sichuan Yi; Nuosu"),
                #("ijo", "Ijo languages"),
                #("iku", "Inuktitut"),
                ("iu", "Inuktitut"),
                #("ile", "Interlingue; Occidental"),
                ("ie", "Interlingue; Occidental"),
                ("ilo", "Iloko"),
                #("ina", "Interlingua (International Auxiliary Language Association)"),
                ("ia", "Interlingua (International Auxiliary Language Association)"),
                #("inc", "Indic languages"),
                #("ind", "Indonesian"),
                ("id", "Indonesian"),
                #("ine", "Indo-European languages"),
                ("inh", "Ingush"),
                #("ipk", "Inupiaq"),
                ("ik", "Inupiaq"),
                #("ira", "Iranian languages"),
                #("iro", "Iroquoian languages"),
                #("ita", "Italian"),
                ("it", "Italian"),
                #("jav", "Javanese"),
                ("jv", "Javanese"),
                ("jbo", "Lojban"),
                #("jpn", "Japanese"),
                ("ja", "Japanese"),
                #("jpr", "Judeo-Persian"),
                #("jrb", "Judeo-Arabic"),
                ("kaa", "Kara-Kalpak"),
                ("kab", "Kabyle"),
                ("kac", "Kachin; Jingpho"),
                #("kal", "Kalaallisut; Greenlandic"),
                ("kl", "Kalaallisut; Greenlandic"),
                ("kam", "Kamba"),
                #("kan", "Kannada"),
                ("kn", "Kannada"),
                #("kar", "Karen languages"),
                #("kas", "Kashmiri"),
                ("ks", "Kashmiri"),
                #("kau", "Kanuri"),
                ("kr", "Kanuri"),
                ("kaw", "Kawi"),
                #("kaz", "Kazakh"),
                ("kk", "Kazakh"),
                ("kbd", "Kabardian"),
                ("kha", "Khasi"),
                #("khi", "Khoisan languages"),
                #("khm", "Central Khmer"),
                ("km", "Central Khmer"),
                ("kho", "Khotanese; Sakan"),
                #("kik", "Kikuyu; Gikuyu"),
                ("ki", "Kikuyu; Gikuyu"),
                #("kin", "Kinyarwanda"),
                ("rw", "Kinyarwanda"),
                #("kir", "Kirghiz; Kyrgyz"),
                ("ky", "Kirghiz; Kyrgyz"),
                ("kmb", "Kimbundu"),
                ("kok", "Konkani"),
                #("kom", "Komi"),
                ("kv", "Komi"),
                #("kon", "Kongo"),
                ("kg", "Kongo"),
                #("kor", "Korean"),
                ("ko", "Korean"),
                ("kos", "Kosraean"),
                ("kpe", "Kpelle"),
                ("krc", "Karachay-Balkar"),
                ("krl", "Karelian"),
                #("kro", "Kru languages"),
                ("kru", "Kurukh"),
                #("kua", "Kuanyama; Kwanyama"),
                ("kj", "Kuanyama; Kwanyama"),
                ("kum", "Kumyk"),
                #("kur", "Kurdish"),
                ("ku", "Kurdish"),
                ("kut", "Kutenai"),
                ("lad", "Ladino"),
                ("lah", "Lahnda"),
                ("lam", "Lamba"),
                #("lao", "Lao"),
                ("lo", "Lao"),
                #("lat", "Latin"),
                ("la", "Latin"),
                #("lav", "Latvian"),
                ("lv", "Latvian"),
                ("lez", "Lezghian"),
                #("lim", "Limburgan; Limburger; Limburgish"),
                ("li", "Limburgan; Limburger; Limburgish"),
                #("lin", "Lingala"),
                ("ln", "Lingala"),
                #("lit", "Lithuanian"),
                ("lt", "Lithuanian"),
                ("lol", "Mongo"),
                ("loz", "Lozi"),
                #("ltz", "Luxembourgish; Letzeburgesch"),
                ("lb", "Luxembourgish; Letzeburgesch"),
                ("lua", "Luba-Lulua"),
                #("lub", "Luba-Katanga"),
                ("lu", "Luba-Katanga"),
                #("lug", "Ganda"),
                ("lg", "Ganda"),
                ("lui", "Luiseno"),
                ("lun", "Lunda"),
                ("luo", "Luo (Kenya and Tanzania)"),
                ("lus", "Lushai"),
                #("mac", "Macedonian"),
                ("mk", "Macedonian"),
                ("mad", "Madurese"),
                ("mag", "Magahi"),
                #("mah", "Marshallese"),
                ("mh", "Marshallese"),
                ("mai", "Maithili"),
                ("mak", "Makasar"),
                #("mal", "Malayalam"),
                ("ml", "Malayalam"),
                ("man", "Mandingo"),
                #("mao", "Maori"),
                ("mi", "Maori"),
                #("map", "Austronesian languages"),
                #("mar", "Marathi"),
                ("mr", "Marathi"),
                ("mas", "Masai"),
                #("may", "Malay"),
                ("ms", "Malay"),
                ("mdf", "Moksha"),
                ("mdr", "Mandar"),
                ("men", "Mende"),
                #("mga", "Irish, Middle (900-1200)"),
                ("mic", "Mi'kmaq; Micmac"),
                ("min", "Minangkabau"),
                #("mis", "Uncoded languages"),
                #("mkh", "Mon-Khmer languages"),
                #("mlg", "Malagasy"),
                ("mg", "Malagasy"), # Madagascar
                ("mlt", "Maltese"),
                ("mt", "Maltese"),
                ("mnc", "Manchu"),
                ("mni", "Manipuri"),
                #("mno", "Manobo languages"),
                ("moh", "Mohawk"),
                #("mon", "Mongolian"),
                ("mn", "Mongolian"),
                ("mos", "Mossi"),
                #("mul", "Multiple languages"),
                #("mun", "Munda languages"),
                ("mus", "Creek"),
                ("mwl", "Mirandese"),
                ("mwr", "Marwari"),
                #("myn", "Mayan languages"),
                ("myv", "Erzya"),
                #("nah", "Nahuatl languages"),
                #("nai", "North American Indian languages"),
                ("nap", "Neapolitan"),
                #("nau", "Nauru"),
                ("na", "Nauru"),
                #("nav", "Navajo; Navaho"),
                ("nv", "Navajo; Navaho"),
                #("nbl", "Ndebele, South; South Ndebele"),
                ("nr", "Ndebele, South; South Ndebele"),
                #("nde", "Ndebele, North; North Ndebele"),
                ("nd", "Ndebele, North; North Ndebele"),
                #("ndo", "Ndonga"),
                ("ng", "Ndonga"),
                ("nds", "Low German; Low Saxon; German, Low; Saxon, Low"),
                #("nep", "Nepali"),
                ("ne", "Nepali"),
                ("new", "Nepal Bhasa; Newari"),
                ("nia", "Nias"),
                #("nic", "Niger-Kordofanian languages"),
                ("niu", "Niuean"),
                #("nno", "Norwegian Nynorsk; Nynorsk, Norwegian"),
                ("nn", "Norwegian Nynorsk; Nynorsk, Norwegian"),
                #("nob", "Bokmål, Norwegian; Norwegian Bokmål"),
                ("nb", "Bokmål, Norwegian; Norwegian Bokmål"),
                ("nog", "Nogai"),
                #("non", "Norse, Old"),
                #("nor", "Norwegian"),
                ("no", "Norwegian"),
                ("nqo", "N'Ko"),
                ("nso", "Pedi; Sepedi; Northern Sotho"),
                #("nub", "Nubian languages"),
                #("nwc", "Classical Newari; Old Newari; Classical Nepal Bhasa"),
                #("nya", "Chichewa; Chewa; Nyanja"),
                ("ny", "Chichewa; Chewa; Nyanja"),
                ("nym", "Nyamwezi"),
                ("nyn", "Nyankole"),
                ("nyo", "Nyoro"),
                ("nzi", "Nzima"),
                #("oci", "Occitan (post 1500); Provençal"),
                ("oc", "Occitan (post 1500); Provençal"),
                #("oji", "Ojibwa"),
                ("oj", "Ojibwa"),
                #("ori", "Oriya"),
                ("or", "Oriya"),
                #("orm", "Oromo"),
                ("om", "Oromo"),
                ("osa", "Osage"),
                #("oss", "Ossetian; Ossetic"),
                ("os", "Ossetian; Ossetic"),
                #("ota", "Turkish, Ottoman (1500-1928)"),
                #("oto", "Otomian languages"),
                #("paa", "Papuan languages"),
                ("pag", "Pangasinan"),
                ("pal", "Pahlavi"),
                ("pam", "Pampanga; Kapampangan"),
                #("pan", "Panjabi; Punjabi"),
                ("pa", "Panjabi; Punjabi"),
                ("pap", "Papiamento"),
                ("pau", "Palauan"),
                #("peo", "Persian, Old (ca.600-400 B.C.)"),
                #("per", "Persian"),
                ("fa", "Persian"),
                #("phi", "Philippine languages"),
                ("phn", "Phoenician"),
                #("pli", "Pali"),
                ("pi", "Pali"),
                #("pol", "Polish"),
                ("pl", "Polish"),
                ("pon", "Pohnpeian"),
                #("por", "Portuguese"),
                ("pt", "Portuguese"),
                #("pra", "Prakrit languages"),
                #("pro", "Provençal, Old (to 1500)"),
                ("prs", "Dari"),
                #("pus", "Pushto; Pashto"),
                ("ps", "Pushto; Pashto"),
                #("qaa-qtz", "Reserved for local use"),
                #("que", "Quechua"),
                ("qu", "Quechua"),
                ("raj", "Rajasthani"),
                ("rap", "Rapanui"),
                ("rar", "Rarotongan; Cook Islands Maori"),
                #("roa", "Romance languages"),
                #("roh", "Romansh"),
                ("rm", "Romansh"),
                ("rom", "Romany"),
                #("rum", "Romanian; Moldavian; Moldovan"),
                ("ro", "Romanian; Moldavian; Moldovan"),
                #("run", "Rundi"),
                ("rn", "Rundi"),
                ("rup", "Aromanian; Arumanian; Macedo-Romanian"),
                #("rus", "Russian"),
                ("ru", "Russian"),
                ("sad", "Sandawe"),
                #("sag", "Sango"),
                ("sg", "Sango"),
                ("sah", "Yakut"),
                #("sai", "South American Indian (Other)"),
                #("sal", "Salishan languages"),
                ("sam", "Samaritan Aramaic"),
                #("san", "Sanskrit"),
                ("sa", "Sanskrit"),
                ("sas", "Sasak"),
                ("sat", "Santali"),
                ("scn", "Sicilian"),
                ("sco", "Scots"),
                ("sel", "Selkup"),
                #("sem", "Semitic languages"),
                #("sga", "Irish, Old (to 900)"),
                ("sgn", "Sign Languages"),
                ("shn", "Shan"),
                ("sid", "Sidamo"),
                #("sin", "Sinhala; Sinhalese"),
                ("si", "Sinhala; Sinhalese"),
                #("sio", "Siouan languages"),
                #("sit", "Sino-Tibetan languages"),
                #("sla", "Slavic languages"),
                #("slo", "Slovak"),
                ("sk", "Slovak"),
                #("slv", "Slovenian"),
                ("sl", "Slovenian"),
                ("sma", "Southern Sami"),
                #("sme", "Northern Sami"),
                ("se", "Northern Sami"),
                #("smi", "Sami languages"),
                ("smj", "Lule Sami"),
                ("smn", "Inari Sami"),
                #("smo", "Samoan"),
                ("sm", "Samoan"),
                ("sms", "Skolt Sami"),
                #("sna", "Shona"),
                ("sn", "Shona"),
                #("snd", "Sindhi"),
                ("sd", "Sindhi"),
                ("snk", "Soninke"),
                ("sog", "Sogdian"),
                #("som", "Somali"),
                ("so", "Somali"),
                #("son", "Songhai languages"),
                #("sot", "Sotho, Southern"),
                ("st", "Sotho, Southern"), # Sesotho
                #("spa", "Spanish; Castilian"),
                ("es", "Spanish; Castilian"),
                #("srd", "Sardinian"),
                ("sc", "Sardinian"),
                ("srn", "Sranan Tongo"),
                #("srp", "Serbian"),
                ("sr", "Serbian"),
                ("srr", "Serer"),
                #("ssa", "Nilo-Saharan languages"),
                #("ssw", "Swati"),
                ("ss", "Swati"),
                ("suk", "Sukuma"),
                #("sun", "Sundanese"),
                ("su", "Sundanese"),
                ("sus", "Susu"),
                ("sux", "Sumerian"),
                #("swa", "Swahili"),
                ("sw", "Swahili"),
                #("swe", "Swedish"),
                ("sv", "Swedish"),
                #("syc", "Classical Syriac"),
                ("syr", "Syriac"),
                #("tah", "Tahitian"),
                ("ty", "Tahitian"),
                #("tai", "Tai languages"),
                #("tam", "Tamil"),
                ("ta", "Tamil"),
                #("tat", "Tatar"),
                ("tt", "Tatar"),
                #("tel", "Telugu"),
                ("te", "Telugu"),
                ("tem", "Timne"),
                ("ter", "Tereno"),
                ("tet", "Tetum"),
                #("tgk", "Tajik"),
                ("tg", "Tajik"),
                #("tgl", "Tagalog"),
                ("tl", "Tagalog"),
                #("tha", "Thai"),
                ("th", "Thai"),
                #("tib", "Tibetan"),
                ("bo", "Tibetan"),
                ("tig", "Tigre"),
                #("tir", "Tigrinya"),
                ("ti", "Tigrinya"),
                ("tiv", "Tiv"),
                ("tkl", "Tokelau"),
                #("tlh", "Klingon; tlhIngan-Hol"),
                ("tli", "Tlingit"),
                ("tmh", "Tamashek"),
                ("tog", "Tonga (Nyasa)"),
                #("ton", "Tonga (Tonga Islands)"),
                ("to", "Tonga (Tonga Islands)"),
                ("tpi", "Tok Pisin"),
                ("tsi", "Tsimshian"),
                #("tsn", "Tswana"),
                ("tn", "Tswana"),
                #("tso", "Tsonga"),
                ("ts", "Tsonga"),
                #("tuk", "Turkmen"),
                ("tk", "Turkmen"),
                ("tum", "Tumbuka"),
                #("tup", "Tupi languages"),
                #("tur", "Turkish"),
                ("tr", "Turkish"),
                #("tut", "Altaic languages"),
                ("tvl", "Tuvalu"),
                #("twi", "Twi"),
                ("tw", "Twi"),
                ("tyv", "Tuvinian"),
                ("udm", "Udmurt"),
                ("uga", "Ugaritic"),
                #("uig", "Uighur; Uyghur"),
                ("ug", "Uighur; Uyghur"),
                #("ukr", "Ukrainian"),
                ("uk", "Ukrainian"),
                ("umb", "Umbundu"),
                #("und", "Undetermined"),
                #("urd", "Urdu"),
                ("ur", "Urdu"),
                #("uzb", "Uzbek"),
                ("uz", "Uzbek"),
                ("vai", "Vai"),
                #("ven", "Venda"),
                ("ve", "Venda"),
                #("vie", "Vietnamese"),
                ("vi", "Vietnamese"),
                #("vol", "Volapük"),
                ("vo", "Volapük"),
                ("vot", "Votic"),
                #("wak", "Wakashan languages"),
                ("wal", "Walamo"),
                ("war", "Waray"),
                ("was", "Washo"),
                #("wel", "Welsh"),
                ("cy", "Welsh"),
                #("wen", "Sorbian languages"),
                #("wln", "Walloon"),
                ("wa", "Walloon"),
                #("wol", "Wolof"),
                ("wo", "Wolof"),
                ("xal", "Kalmyk; Oirat"),
                #("xho", "Xhosa"),
                ("xh", "Xhosa"),
                ("yao", "Yao"),
                ("yap", "Yapese"),
                #("yid", "Yiddish"),
                ("yi", "Yiddish"),
                #("yor", "Yoruba"),
                ("yo", "Yoruba"),
                #("ypk", "Yupik languages"),
                ("zap", "Zapotec"),
                #("zbl", "Blissymbols; Blissymbolics; Bliss"),
                ("zen", "Zenaga"),
                ("zgh", "Standard Moroccan Tamazight"),
                #("zha", "Zhuang; Chuang"),
                ("za", "Zhuang; Chuang"),
                #("znd", "Zande languages"),
                #("zul", "Zulu"),
                ("zu", "Zulu"),
                ("zun", "Zuni"),
                #("zxx", "No linguistic content; Not applicable"),
                ("zza", "Zaza; Dimili; Dimli; Kirdki; Kirmanjki; Zazaki"),
                ]

        settings = current.deployment_settings

        l10n_languages = settings.get_L10n_languages()
        lang += l10n_languages.items()

        extra_codes = settings.get_L10n_extra_codes()
        if extra_codes:
            lang += extra_codes

        return list(set(lang)) # Remove duplicates

# END =========================================================================
