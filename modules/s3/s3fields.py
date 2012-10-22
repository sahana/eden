# -*- coding: utf-8 -*-

""" S3 Extensions for gluon.dal.Field, reusable fields

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3ReusableField",
           "s3_uid",
           "s3_meta_deletion_status",
           "s3_meta_deletion_fk",
           "s3_meta_deletion_rb",
           "s3_deletion_status",
           "s3_timestamp",
           "s3_authorstamp",
           "s3_ownerstamp",
           "s3_meta_fields",
           "s3_all_meta_field_names",   # Used by GIS
           "s3_role_required",          # Used by GIS
           "s3_roles_permitted",        # Used by CMS (in future)
           "s3_lx_fields",
           "s3_lx_onvalidation",
           "s3_lx_update",
           "s3_address_fields",
           "s3_address_hide",
           "s3_address_onvalidation",
           "s3_address_update",
           "s3_comments",
           "s3_currency",
           "s3_date",
           "s3_datetime",
           ]

import datetime
from uuid import uuid4

from gluon import *
# Here are dependencies listed for reference:
#from gluon import current
#from gluon.dal import Field
#from gluon.html import *
#from gluon.validators import *
from gluon.dal import Query, SQLCustomType
from gluon.storage import Storage

from s3utils import S3DateTime, s3_auth_user_represent, s3_auth_group_represent
from s3validators import IS_ONE_OF, IS_UTC_DATETIME
from s3widgets import S3AutocompleteWidget, S3DateWidget, S3DateTimeWidget

try:
    db = current.db
except:
    # Running from 000_1st_run
    db = None

# =============================================================================
class FieldS3(Field):
    """
        S3 extensions of the gluon.sql.Field clas

        If Server Side Pagination is on, the proper CAST is needed to
        match the lookup table id
    """

    def __init__(self, fieldname,
                 type="string",
                 length=None,
                 default=None,
                 required=False,
                 requires="<default>",
                 ondelete="CASCADE",
                 notnull=False,
                 unique=False,
                 uploadfield=True,
                 widget=None,
                 label=None,
                 comment=None,
                 writable=True,
                 readable=True,
                 update=None,
                 authorize=None,
                 autodelete=False,
                 represent=None,
                 uploadfolder=None,
                 compute=None,
                 sortby=None):

        self.sortby = sortby

        Field.__init__(self,
                       fieldname,
                       type,
                       length,
                       default,
                       required,
                       requires,
                       ondelete,
                       notnull,
                       unique,
                       uploadfield,
                       widget,
                       label,
                       comment,
                       writable,
                       readable,
                       update,
                       authorize,
                       autodelete,
                       represent,
                       uploadfolder,
                       compute)

    def join_via(self, value):
        if self.type.find("reference") == 0:
            return Query(self, "=", value)
        else:
            return QueryS3(self, "join_via", value)

# =============================================================================
class QueryS3(Query):
    """
        S3 extensions of the gluon.sql.Query class

        If Server Side Pagination is on, the proper CAST is needed to match
        the string-typed id to lookup table id
    """

    def __init__(self, left, op=None, right=None):

        if op <> "join_via":
            Query.__init__(self, left, op, right)
        else:
            self.sql = "CAST(TRIM(%s,"|") AS INTEGER)=%s" % (left, right)

# =============================================================================
class S3ReusableField(object):
    """
        DRY Helper for reusable fields:

        This creates neither a Table nor a Field, but just
        an argument store. The field is created with the __call__
        method, which is faster than copying an existing field.
    """

    def __init__(self, name, type="string", **attr):

        self.name = name
        self.__type = type
        self.attr = Storage(attr)

    def __call__(self, name=None, **attr):

        if not name:
            name = self.name

        ia = Storage(self.attr)

        if attr:
            if not attr.get("empty", True):
                requires = ia.requires
                if requires:
                    if not isinstance(requires, (list, tuple)):
                        requires = [requires]
                    if requires:
                        r = requires[0]
                        if isinstance(r, IS_EMPTY_OR):
                            requires = r.other
                            ia.update(requires=requires)
            if "empty" in attr:
                del attr["empty"]
            ia.update(**attr)

        if "script" in ia:
            if ia.script:
                if ia.comment:
                    ia.comment = TAG[""](ia.comment, ia.script)
                else:
                    ia.comment = ia.script
            del ia["script"]

        if ia.sortby is not None:
            return FieldS3(name, self.__type, **ia)
        else:
            return Field(name, self.__type, **ia)

# =============================================================================
# Record identity meta-fields

# Use URNs according to http://tools.ietf.org/html/rfc4122
s3uuid = SQLCustomType(type = "string",
                       native = "VARCHAR(128)",
                       encoder = lambda x: "%s" % (uuid4().urn
                                    if x == ""
                                    else str(x.encode("utf-8"))),
                       decoder = lambda x: x)

if db and current.db._adapter.represent("X", s3uuid) != "'X'":
    # Old web2py DAL, must add quotes in encoder
    s3uuid = SQLCustomType(type = "string",
                           native = "VARCHAR(128)",
                           encoder = (lambda x: "'%s'" % (uuid4().urn
                                        if x == ""
                                        else str(x.encode("utf-8")).replace("'", "''"))),
                           decoder = (lambda x: x))

# Universally unique identifier for a record
s3_meta_uuid = S3ReusableField("uuid", type=s3uuid,
                               length=128,
                               notnull=True,
                               unique=True,
                               readable=False,
                               writable=False,
                               default="")

# Master-Copy-Index (for Sync)
s3_meta_mci = S3ReusableField("mci", "integer",
                              default=0,
                              readable=False,
                              writable=False)

def s3_uid():
    return (s3_meta_uuid(),
            s3_meta_mci())

# =============================================================================
# Record "soft"-deletion meta-fields

# "Deleted"-flag
s3_meta_deletion_status = S3ReusableField("deleted", "boolean",
                                          readable=False,
                                          writable=False,
                                          default=False)

# Parked foreign keys of a deleted record in JSON format
# => to be restored upon "un"-delete
s3_meta_deletion_fk = S3ReusableField("deleted_fk", #"text",
                                      readable=False,
                                      writable=False)

# ID of the record replacing this record
# => for record merger (de-duplication)
s3_meta_deletion_rb = S3ReusableField("deleted_rb", "integer",
                                      readable=False,
                                      writable=False)

def s3_deletion_status():
    return (s3_meta_deletion_status(),
            s3_meta_deletion_fk(),
            s3_meta_deletion_rb())

# =============================================================================
# Record timestamp meta-fields

s3_meta_created_on = S3ReusableField("created_on", "datetime",
                                     readable=False,
                                     writable=False,
                                     default=lambda: datetime.datetime.utcnow())

s3_meta_modified_on = S3ReusableField("modified_on", "datetime",
                                      readable=False,
                                      writable=False,
                                      default=lambda: datetime.datetime.utcnow(),
                                      update=lambda: datetime.datetime.utcnow())

def s3_timestamp():
    return (s3_meta_created_on(),
            s3_meta_modified_on())

# =========================================================================
# Record authorship meta-fields
def s3_authorstamp():
    """
        Record ownership meta-fields
    """

    auth = current.auth
    utable = auth.settings.table_user

    if auth.is_logged_in():
        current_user = current.session.auth.user.id
    else:
        current_user = None

    # Author of a record
    s3_meta_created_by = S3ReusableField("created_by", utable,
                                         readable=False,
                                         writable=False,
                                         requires=None,
                                         default=current_user,
                                         represent=s3_auth_user_represent,
                                         ondelete="RESTRICT")

    # Last author of a record
    s3_meta_modified_by = S3ReusableField("modified_by", utable,
                                          readable=False,
                                          writable=False,
                                          requires=None,
                                          default=current_user,
                                          update=current_user,
                                          represent=s3_auth_user_represent,
                                          ondelete="RESTRICT")

    return (s3_meta_created_by(),
            s3_meta_modified_by())

# =========================================================================
def s3_ownerstamp():
    """
        Record ownership meta-fields
    """

    auth = current.auth
    utable = auth.settings.table_user

    # Individual user who owns the record
    s3_meta_owned_by_user = S3ReusableField("owned_by_user", utable,
                                            readable=False,
                                            writable=False,
                                            requires=None,
                                            default=current.session.auth.user.id
                                                        if auth.is_logged_in()
                                                        else None,
                                            represent=lambda id: \
                                                id and s3_auth_user_represent(id) or \
                                                       current.messages.UNKNOWN_OPT,
                                            ondelete="RESTRICT")

    # Role of users who collectively own the record
    s3_meta_owned_by_group = S3ReusableField("owned_by_group", "integer",
                                             readable=False,
                                             writable=False,
                                             requires=None,
                                             default=None,
                                             represent=s3_auth_group_represent)

    # Person Entity controlling access to this record
    s3_meta_realm_entity = S3ReusableField("realm_entity", "integer",
                                              readable=False,
                                              writable=False,
                                              requires=None,
                                              default=None,
                                              # use a lambda here as we don't
                                              # want the model to be loaded yet
                                              represent=lambda val: \
                                                        current.s3db.pr_pentity_represent(val))
    return (s3_meta_owned_by_user(),
            s3_meta_owned_by_group(),
            s3_meta_realm_entity())

# =========================================================================
def s3_meta_fields():
    """
        Normal meta-fields added to every table
    """

    utable = current.auth.settings.table_user

    # Approver of a record
    s3_meta_approved_by = S3ReusableField("approved_by", "integer",
                                          readable=False,
                                          writable=False,
                                          requires=None,
                                          represent=s3_auth_user_represent)

    fields = (s3_meta_uuid(),
              s3_meta_mci(),
              s3_meta_deletion_status(),
              s3_meta_deletion_fk(),
              s3_meta_deletion_rb(),
              s3_meta_created_on(),
              s3_meta_modified_on(),
              s3_meta_approved_by(),
              )
    fields = (fields + s3_authorstamp() + s3_ownerstamp())
    return fields

def s3_all_meta_field_names():
    return [field.name for field in s3_meta_fields()]

# =========================================================================
# Reusable roles fields

def s3_role_required():
    """
        Role Required to access a resource
        - used by GIS for map layer permissions management
    """

    T = current.T
    gtable = current.auth.settings.table_group
    f = S3ReusableField("role_required", gtable,
            sortby="role",
            requires = IS_NULL_OR(
                        IS_ONE_OF(db, "auth_group.id",
                                  "%(role)s",
                                  zero=T("Public"))),
            widget = S3AutocompleteWidget("admin",
                                          "group",
                                          fieldname="role"),
            represent = s3_auth_group_represent,
            label = T("Role Required"),
            comment = DIV(_class="tooltip",
                          _title="%s|%s" % (T("Role Required"),
                                            T("If this record should be restricted then select which role is required to access the record here."))),
            ondelete = "RESTRICT")
    return f()


# -------------------------------------------------------------------------
def s3_roles_permitted(name="roles_permitted", **attr):
    """
        List of Roles Permitted to access a resource
        - used by CMS
    """

    from s3validators import IS_ONE_OF

    T = current.T
    if "label" not in attr:
        label = T("Roles Permitted")
    if "sortby" not in attr:
        sortby = "role"
    if "represent" not in attr:
        represent = s3_auth_group_represent
    if "requires" not in attr:
        requires = IS_NULL_OR(IS_ONE_OF(current.db,
                                        "auth_group.id",
                                        "%(role)s",
                                        multiple=True))
    if "comment" not in attr:
        comment = DIV(_class="tooltip",
                          _title="%s|%s" % (T("Roles Permitted"),
                                            T("If this record should be restricted then select which role(s) are permitted to access the record here.")))
    if "ondelete" not in attr:
        ondelete = "RESTRICT"

    f = S3ReusableField(name, "list:reference auth_group",
                        sortby = sortby,
                        requires = requires,
                        represent = represent,
                        # @ToDo
                        #widget = S3CheckboxesWidget(lookup_table_name = "auth_group",
                        #                            lookup_field_name = "role",
                        #                            multiple = True),
                        label = label,
                        comment = comment,
                        ondelete = ondelete)
    return f()

# =============================================================================
# Lx
#
# These fields are populated onaccept from location_id
# - for many reads to fewer writes, this is faster than Virtual Fields
# - @ToDO: No need for virtual fields - replace with simple joins
#
# Labels that vary by country are set by gis.update_table_hierarchy_labels()
#

address_L4 = S3ReusableField("L4",
                             readable=False,
                             writable=False)
address_L3 = S3ReusableField("L3",
                             readable=False,
                             writable=False)
address_L2 = S3ReusableField("L2",
                             readable=False,
                             writable=False)
address_L1 = S3ReusableField("L1",
                             readable=False,
                             writable=False)
address_L0 = S3ReusableField("L0",
                             readable=False,
                             writable=False)

def s3_lx_fields():
    """
        Return the fields used to report on resources by location
    """

    fields = (
            address_L4(),
            address_L3(),
            address_L2(),
            address_L1(),
            address_L0(label=current.messages.COUNTRY),
           )
    return fields

# -----------------------------------------------------------------------------
def s3_lx_onvalidation(form):
    """
        Write the Lx fields from the Location
        - used by pr_person, hrm_training, irs_ireport

        @ToDo: Allow the reverse operation.
        If these fields are populated then create/update the location
    """

    vars = form.vars
    if "location_id" in vars and vars.location_id:

        db = current.db
        table = current.s3db.gis_location
        query = (table.id == vars.location_id)
        location = db(query).select(table.name,
                                    table.level,
                                    table.parent,
                                    table.path,
                                    limitby=(0, 1)).first()
        if location:
            if location.level == "L0":
                vars.L0 = location.name
            elif location.level == "L1":
                vars.L1 = location.name
                if location.parent:
                    query = (table.id == location.parent)
                    country = db(query).select(table.name,
                                               limitby=(0, 1)).first()
                    if country:
                        vars.L0 = country.name
            else:
                # Get Names of ancestors at each level
                vars = current.gis.get_parent_per_level(vars,
                                                        vars.location_id,
                                                        feature=location,
                                                        ids=False,
                                                        names=True)

# -----------------------------------------------------------------------------
def s3_lx_update(table, record_id):
    """
        Write the Lx fields from the Location
        - used by hrm_human_resource & pr_address

        @ToDo: Allow the reverse operation.
        If these fields are populated then create/update the location
    """

    if "location_id" in table:

        db = current.db
        ltable = current.s3db.gis_location
        query = (table.id == record_id) & \
                (ltable.id == table.location_id)
        location = db(query).select(ltable.id,
                                    ltable.name,
                                    ltable.level,
                                    ltable.parent,
                                    ltable.path,
                                    limitby=(0, 1)).first()
        if location:
            vars = Storage()
            if location.level == "L0":
                vars.L0 = location.name
            elif location.level == "L1":
                vars.L1 = location.name
                if location.parent:
                    query = (ltable.id == location.parent)
                    country = db(query).select(ltable.name,
                                               limitby=(0, 1)).first()
                    if country:
                        vars.L0 = country.name
            else:
                # Get Names of ancestors at each level
                vars = current.gis.get_parent_per_level(vars,
                                                        location.id,
                                                        feature=location,
                                                        ids=False,
                                                        names=True)
            # Update record
            db(table.id == record_id).update(**vars)

# =============================================================================
# Addresses
#
# These fields are populated onaccept from location_id
#
# @ToDo: Add Postcode to gis.update_table_hierarchy_labels()
#

address_building_name = S3ReusableField("building_name",
                                        readable=False,
                                        writable=False)
address_address = S3ReusableField("address",
                                  readable=False,
                                  writable=False)
address_postcode = S3ReusableField("postcode",
                                   readable=False,
                                   writable=False)

def s3_address_fields():
    """
       Return the fields used to add an address to a site
    """

    T = current.T
    fields = (
            address_building_name(label=T("Building Name")),
            address_address(label=T("Address")),
            address_postcode(label=current.deployment_settings.get_ui_label_postcode()),
            address_L4(),
            address_L3(),
            address_L2(),
            address_L1(),
            address_L0(),
           )
    return fields

# -----------------------------------------------------------------------------
# Hide Address fields in Create forms
# inc list_create (list_fields over-rides)
def s3_address_hide(table):
    table.building_name.readable = False
    table.address.readable = False
    table.L4.readable = False
    table.L3.readable = False
    table.L2.readable = False
    table.L1.readable = False
    table.L0.readable = False
    table.postcode.readable = False
    return

# -----------------------------------------------------------------------------
def s3_address_onvalidation(form):
    """
        Write the Address fields from the Location
        - used by pr_address, org_office & cr_shelter

        @ToDo: Allow the reverse operation.
        If these fields are populated then create/update the location
    """

    vars = form.vars
    if "location_id" in vars and vars.location_id:

        db = current.db
        table = current.s3db.gis_location
        # Read Postcode & Street Address
        query = (table.id == vars.location_id)
        location = db(query).select(table.addr_street,
                                    table.addr_postcode,
                                    table.name,
                                    table.level,
                                    table.parent,
                                    table.path,
                                    limitby=(0, 1)).first()
        if location:
            vars.address = location.addr_street
            vars.postcode = location.addr_postcode
            if location.level == "L0":
                vars.L0 = location.name
            elif location.level == "L1":
                vars.L1 = location.name
                if location.parent:
                    query = (table.id == location.parent)
                    country = db(query).select(table.name,
                                               limitby=(0, 1)).first()
                    if country:
                        vars.L0 = country.name
            else:
                if location.level is None:
                    vars.building_name = location.name
                # Get Names of ancestors at each level
                vars = current.gis.get_parent_per_level(vars,
                                                        vars.location_id,
                                                        feature=location,
                                                        ids=False,
                                                        names=True)

# -----------------------------------------------------------------------------
def s3_address_update(table, record_id):
    """
        Write the Address fields from the Location
        - used by asset_asset & hrm_human_resource

        @ToDo: Allow the reverse operation.
        If these fields are populated then create/update the location
    """

    if "location_id" in table:

        db = current.db
        ltable = current.s3db.gis_location
        # Read Postcode & Street Address
        query = (table.id == record_id) & \
                (ltable.id == table.location_id)
        location = db(query).select(ltable.id,
                                    ltable.addr_street,
                                    ltable.addr_postcode,
                                    ltable.name,
                                    ltable.level,
                                    ltable.parent,
                                    ltable.path,
                                    limitby=(0, 1)).first()
        if location:
            vars = Storage()
            vars.address = location.addr_street
            vars.postcode = location.addr_postcode
            if location.level == "L0":
                vars.L0 = location.name
            elif location.level == "L1":
                vars.L1 = location.name
                if location.parent:
                    query = (ltable.id == location.parent)
                    country = db(query).select(ltable.name,
                                               limitby=(0, 1)).first()
                    if country:
                        vars.L0 = country.name
            else:
                if location.level is None:
                    vars.building_name = location.name
                # Get Names of ancestors at each level
                vars = current.gis.get_parent_per_level(vars,
                                                        location.id,
                                                        feature=location,
                                                        ids=False,
                                                        names=True)
            # Update record
            db(table.id == record_id).update(**vars)

# =============================================================================
# Comments
#
def s3_comments(name="comments", **attr):
    """
        Return a standard Comments field
    """

    from s3widgets import s3_comments_widget

    T = current.T
    if "label" not in attr:
        attr["label"] = T("Comments")
    if "represent" not in attr:
        attr["represent"] = lambda comments: comments or current.messages.NONE
    if "widget" not in attr:
        attr["widget"] = s3_comments_widget
    if "comment" not in attr:
        attr["comment"] = DIV(_class="tooltip",
                              _title="%s|%s" % \
            (T("Comments"),
             T("Please use this field to record any additional information, including a history of the record if it is updated.")))

    f = S3ReusableField(name, "text",
                        **attr)
    return f()

# =============================================================================
# Currency field
#
# @ToDo: Move to a Finance module
#

def s3_currency(name="currency", **attr):
    """
        Return a standard Currency field
    """

    settings = current.deployment_settings

    if "label" not in attr:
        attr["label"] = current.T("Currency")
    if "default" not in attr:
        attr["default"] = settings.get_fin_currency_default()
    if "requires" not in attr:
        currency_opts = settings.get_fin_currencies()
        attr["requires"] = IS_IN_SET(currency_opts.keys(),
                                     zero=None)
    if "writable" not in attr:
         attr["writable"] = settings.get_fin_currency_writable()

    f = S3ReusableField(name, length=3,
                        **attr)
    return f()

# =============================================================================
# Date field
#

def s3_date(name="date", **attr):
    """
        Return a standard Date field

        Additional options to normal S3ResuableField:
            default == "now" (in addition to usual meanings)
            past = x months
            future = x months
    """

    if "past" in attr:
        past = attr["past"]
        del attr["past"]
    else:
        past = None
    if "future" in attr:
        future = attr["future"]
        del attr["future"]
    else:
        future = None

    if "default" in attr and attr["default"] == "now":
        attr["default"] = current.request.utcnow
    if "label" not in attr:
        attr["label"] = current.T("Date")
    if "represent" not in attr:
        attr["represent"] = lambda d: S3DateTime.date_represent(d,
                                                                utc=True)
    if "requires" not in attr:
        if past is None and future is None:
            requires = IS_DATE(
                    format=current.deployment_settings.get_L10n_date_format()
                )
        else:
            now = current.request.utcnow.date()
            current_month = now.month
            if past is None:
                future_month = now.month + future
                if future_month <= 12:
                    max = now.replace(month=future_month)
                else:
                    current_year = now.year
                    years = int(future_month/12)
                    future_year = current_year + years
                    future_month = future_month - (years * 12)
                    max = now.replace(year=future_year,
                                      month=future_month)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        maximum=max,
                        error_message=current.T("Date must be %(max)s or earlier!")
                    )
            elif future is None:
                if past < current_month:
                    min = now.replace(month=current_month - past)
                else:
                    current_year = now.year
                    past_years = int(past/12)
                    past_months = past - (past_years * 12)
                    min = now.replace(year=current_year - past_years,
                                      month=current_month - past_months)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        minimum=min,
                        error_message=current.T("Date must be %(min)s or later!")
                    )
            else:
                future_month = now.month + future
                if future_month < 13:
                    max = now.replace(month=future_month)
                else:
                    current_year = now.year
                    years = int(future_month/12)
                    future_year = now.year + years
                    future_month = future_month - (years * 12)
                    max = now.replace(year=future_year,
                                      month=future_month)
                if past < current_month:
                    min = now.replace(month=current_month - past)
                else:
                    current_year = now.year
                    past_years = int(past/12)
                    past_months = past - (past_years * 12)
                    min = now.replace(year=current_year - past_years,
                                      month=current_month - past_months)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        maximum=max,
                        minimum=min,
                        error_message=current.T("Date must be between %(min)s and %(max)s!")
                    )
        if "empty" in attr:
            if attr["empty"] is False:
                attr["requires"] = requires
            else:
                attr["requires"] = IS_EMPTY_OR(requires)
            del attr["empty"]
        else:
            # Default
            attr["requires"] = IS_EMPTY_OR(requires)
    if "widget" not in attr:
        if past is None and future is None:
            attr["widget"] = S3DateWidget()
        elif past is None:
            attr["widget"] = S3DateWidget(future=future)
        elif future is None:
            attr["widget"] = S3DateWidget(past=past)
        else:
            attr["widget"] = S3DateWidget(past=past, future=future)

    f = S3ReusableField(name, "date", **attr)
    return f()

# =============================================================================
# Datetime field
#

def s3_datetime(name="date", **attr):
    """
        Return a standard Datetime field

        Additional options to normal S3ResuableField:
            default = "now" (in addition to usual meanings)
            represent = "date" (in addition to usual meanings)
            widget = "date" (in addition to usual meanings)
            past = x hours
            future = x hours
    """

    if "past" in attr:
        past = attr["past"]
        del attr["past"]
    else:
        past = None
    if "future" in attr:
        future = attr["future"]
        del attr["future"]
    else:
        future = None

    if "default" in attr and attr["default"] == "now":
        attr["default"] = current.request.utcnow
    if "label" not in attr:
        attr["label"] = current.T("Date")
    if "represent" not in attr:
        attr["represent"] = lambda dt: S3DateTime.datetime_represent(dt,
                                                                     utc=True)
    elif attr["represent"] == "date":
        attr["represent"] = lambda dt: S3DateTime.date_represent(dt,
                                                                 utc=True)

    if "widget" not in attr:
        if past is None and future is None:
            attr["widget"] = S3DateTimeWidget()
        elif past is None:
            attr["widget"] = S3DateTimeWidget(future=future)
        elif future is None:
            attr["widget"] = S3DateTimeWidget(past=past)
        else:
            attr["widget"] = S3DateTimeWidget(past=past, future=future)
    elif attr["widget"] == "date":
        if past is None and future is None:
            attr["widget"] = S3DateWidget()
            requires = IS_DATE(
                    format=current.deployment_settings.get_L10n_date_format()
                )
        else:
            now = current.request.utcnow.date()
            current_month = now.month
            if past is None:
                future = int(round(future/744.0, 0))
                attr["widget"] = S3DateWidget(future=future)
                future_month = now.month + future
                if future_month <= 12:
                    max = now.replace(month=future_month)
                else:
                    current_year = now.year
                    years = int(future_month/12)
                    future_year = current_year + years
                    future_month = future_month - (years * 12)
                    max = now.replace(year=future_year,
                                      month=future_month)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        maximum=max,
                        error_message=current.T("Date must be %(max)s or earlier!")
                    )
            elif future is None:
                past = int(round(past/744.0, 0))
                attr["widget"] = S3DateWidget(past=past)
                if past < current_month:
                    min = now.replace(month=current_month - past)
                else:
                    current_year = now.year
                    past_years = int(past/12)
                    past_months = past - (past_years * 12)
                    min = now.replace(year=current_year - past_years,
                                      month=current_month - past_months)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        minimum=min,
                        error_message=current.T("Date must be %(min)s or later!")
                    )
            else:
                future = int(round(future/744.0, 0))
                past = int(round(past/744.0, 0))
                attr["widget"] = S3DateWidget(past=past, future=future)
                future_month = now.month + future
                if future_month < 13:
                    max = now.replace(month=future_month)
                else:
                    current_year = now.year
                    years = int(future_month/12)
                    future_year = now.year + years
                    future_month = future_month - (years * 12)
                    max = now.replace(year=future_year,
                                      month=future_month)
                if past < current_month:
                    min = now.replace(month=current_month - past)
                else:
                    current_year = now.year
                    past_years = int(past/12)
                    past_months = past - (past_years * 12)
                    min = now.replace(year=current_year - past_years,
                                      month=current_month - past_months)
                requires = IS_DATE_IN_RANGE(
                        format=current.deployment_settings.get_L10n_date_format(),
                        maximum=max,
                        minimum=min,
                        error_message=current.T("Date must be between %(min)s and %(max)s!")
                    )
        if "empty" in attr:
            if attr["empty"] is False:
                attr["requires"] = requires
            else:
                attr["requires"] = IS_EMPTY_OR(requires)
            del attr["empty"]
        else:
            # Default
            attr["requires"] = IS_EMPTY_OR(requires)

    if "requires" not in attr:
        if past is None and future is None:
            requires = IS_UTC_DATETIME(
                    format=current.deployment_settings.get_L10n_datetime_format()
                )
        else:
            now = current.request.utcnow
            if past is None:
                max = now + datetime.timedelta(hours=future)
                requires = IS_UTC_DATETIME(
                        format=current.deployment_settings.get_L10n_datetime_format(),
                        maximum=max,
                        error_message=current.T("Date must be %(max)s or earlier!")
                    )
            elif future is None:
                min = now - datetime.timedelta(hours=past)
                requires = IS_UTC_DATETIME(
                        format=current.deployment_settings.get_L10n_datetime_format(),
                        minimum=min,
                        error_message=current.T("Date must be %(min)s or later!")
                    )
            else:
                min = now - datetime.timedelta(hours=past)
                max = now + datetime.timedelta(hours=future)
                requires = IS_UTC_DATETIME(
                        format=current.deployment_settings.get_L10n_datetime_format(),
                        maximum=max,
                        minimum=min,
                        error_message=current.T("Date must be between %(min)s and %(max)s!")
                    )
        if "empty" in attr:
            if attr["empty"] is False:
                attr["requires"] = requires
            else:
                attr["requires"] = IS_EMPTY_OR(requires)
            del attr["empty"]
        else:
            # Default
            attr["requires"] = IS_EMPTY_OR(requires)

    f = S3ReusableField(name, "datetime", **attr)
    return f()

# END =========================================================================
