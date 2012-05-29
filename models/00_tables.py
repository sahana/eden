# -*- coding: utf-8 -*-

"""
    Global tables and re-usable fields
"""

# =============================================================================
# Import models
#
from s3.s3model import S3Model
import eden as models
current.models = models
current.s3db = s3db = S3Model()

# Explicit import statements to have them reload automatically in debug mode
import eden.asset
import eden.auth
import eden.cms
import eden.cr
import eden.delphi
import eden.doc
import eden.dvi
import eden.dvr
import eden.event
import eden.fire
import eden.flood
import eden.gis
import eden.hms
import eden.hrm
import eden.inv
import eden.irs
import eden.member
import eden.msg
import eden.ocr
import eden.org
import eden.patient
import eden.pr
import eden.sit
import eden.proc
import eden.project
import eden.req
import eden.scenario
import eden.security
import eden.supply
import eden.support
import eden.survey
import eden.sync
import eden.vehicle

# =============================================================================
# Import S3 meta fields into global namespace
#
from s3.s3fields import *

# =============================================================================
# Record authorship meta-fields

# Author of a record
s3_meta_created_by = S3ReusableField("created_by", db.auth_user,
                                     readable=False,
                                     writable=False,
                                     requires=None,
                                     default=session.auth.user.id
                                                if auth.is_logged_in()
                                                else None,
                                     represent=s3_auth_user_represent,
                                     ondelete="RESTRICT")

# Last author of a record
s3_meta_modified_by = S3ReusableField("modified_by", db.auth_user,
                                      readable=False,
                                      writable=False,
                                      requires=None,
                                      default=session.auth.user.id
                                                if auth.is_logged_in()
                                                else None,
                                      update=session.auth.user.id
                                                if auth.is_logged_in()
                                                else None,
                                      represent=s3_auth_user_represent,
                                      ondelete="RESTRICT")

def s3_authorstamp():
    return (s3_meta_created_by(),
            s3_meta_modified_by())

# =============================================================================
# Record ownership meta-fields

# Individual user who owns the record
s3_meta_owned_by_user = S3ReusableField("owned_by_user", db.auth_user,
                                        readable=False,
                                        writable=False,
                                        requires=None,
                                        default=session.auth.user.id
                                                    if auth.is_logged_in()
                                                    else None,
                                        represent=lambda id: \
                                            id and s3_auth_user_represent(id) or \
                                                   UNKNOWN_OPT,
                                        ondelete="RESTRICT")

# Role of users who collectively own the record
s3_meta_owned_by_group = S3ReusableField("owned_by_group", "integer",
                                         readable=False,
                                         writable=False,
                                         requires=None,
                                         default=None,
                                         represent=s3_auth_group_represent)

# Person Entity owning the record
s3_meta_owned_by_entity = S3ReusableField("owned_by_entity", "integer",
                                          readable=False,
                                          writable=False,
                                          requires=None,
                                          default=None,
                                          # use a lambda here as we don't
                                          # want the model to be loaded yet
                                          represent=lambda val: \
                                                    s3db.pr_pentity_represent(val))

def s3_ownerstamp():
    return (s3_meta_owned_by_user(),
            s3_meta_owned_by_group(),
            s3_meta_owned_by_entity())

# Make available for S3Models
s3.ownerstamp = s3_ownerstamp

# =============================================================================
def s3_timestamp():
    return (s3_meta_created_on(),
            s3_meta_modified_on(),
            )

# Make available for S3Models
s3.timestamp = s3_timestamp

# =============================================================================
# Common meta-fields
# @todo: can this be moved into s3fields.py?
#
def s3_meta_fields():

    fields = (s3_meta_uuid(),
              s3_meta_mci(),
              s3_meta_deletion_status(),
              s3_meta_deletion_fk(),
              s3_meta_created_on(),
              s3_meta_modified_on(),
              s3_meta_created_by(),
              s3_meta_modified_by(),
              s3_meta_owned_by_user(),
              s3_meta_owned_by_group(),
              s3_meta_owned_by_entity())

    return fields

# Make available for S3Models
s3.meta_fields = s3_meta_fields

# =============================================================================
response.s3.all_meta_field_names = [field.name for field in
    [s3_meta_uuid(),
     s3_meta_mci(),
     s3_meta_deletion_status(),
     s3_meta_deletion_fk(),
     s3_meta_created_on(),
     s3_meta_modified_on(),
     s3_meta_created_by(),
     s3_meta_modified_by(),
     s3_meta_owned_by_user(),
     s3_meta_owned_by_group(),
     s3_meta_owned_by_entity(),
    ]]

# =============================================================================
# Reusable field for scheduler task links
#
scheduler_task_id = S3ReusableField("scheduler_task_id",
                                    "reference %s" % s3base.S3Task.TASK_TABLENAME,
                                    ondelete="CASCADE")
s3.scheduler_task_id = scheduler_task_id

# =============================================================================
# Reusable roles fields for map layer permissions management (GIS)

role_required = S3ReusableField("role_required", db.auth_group,
                                sortby="role",
                                requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                "auth_group.id",
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

roles_permitted = S3ReusableField("roles_permitted", 'list:reference auth_group',
                                  sortby="role",
                                  requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                  "auth_group.id",
                                                                  "%(role)s",
                                                                  multiple=True)),
                                  # @ToDo
                                  #widget = S3CheckboxesWidget(lookup_table_name = "auth_group",
                                  #                            lookup_field_name = "role",
                                  #                            multiple = True),
                                  represent = s3_auth_group_represent,
                                  label = T("Roles Permitted"),
                                  comment = DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Roles Permitted"),
                                                                  T("If this record should be restricted then select which role(s) are permitted to access the record here."))),
                                  ondelete = "RESTRICT")

# Make available for S3Models
s3.role_required = role_required
s3.roles_permitted = roles_permitted

# =============================================================================
# Other reusable fields

# -----------------------------------------------------------------------------
# Reusable comments field to include in other table definitions
s3_comments = S3ReusableField("comments", "text",
                              label = T("Comments"),
                              widget = s3_comments_widget,
                              comment = DIV(_class="tooltip",
                                            _title="%s|%s" % (T("Comments"),
                                                              T("Please use this field to record any additional information, including a history of the record if it is updated."))))

s3.comments = s3_comments

# -----------------------------------------------------------------------------
# Reusable currency field to include in other table definitions
#
# @ToDo: Move to a Finance module
#
currency_type_opts = deployment_settings.get_fin_currencies()
default_currency = deployment_settings.get_fin_currency_default()

currency_type = S3ReusableField("currency_type", "string",
                                length = 3,
                                #notnull=True,
                                requires = IS_IN_SET(currency_type_opts.keys(),
                                                     zero=None),
                                default = default_currency,
                                label = T("Currency"),
                                #represent = lambda opt: \
                                #    currency_type_opts.get(opt, UNKNOWN_OPT),
                                writable = deployment_settings.get_fin_currency_writable())

response.s3.currency_type = currency_type

# =============================================================================
# Lx
#
# These fields are populated onaccept from location_id
# - for many reads to fewer writes, this is faster than Virtual Fields
#
# Labels that vary by country are set by gis.update_table_hierarchy_labels()
#

address_L4 = S3ReusableField("L4",
                             #label=gis.get_location_hierarchy("L4"),
                             readable=False,
                             writable=False)
address_L3 = S3ReusableField("L3",
                             #label=gis.get_location_hierarchy("L3"),
                             readable=False,
                             writable=False)
address_L2 = S3ReusableField("L2",
                             #label=gis.get_location_hierarchy("L2"),
                             readable=False,
                             writable=False)
address_L1 = S3ReusableField("L1",
                             #label=gis.get_location_hierarchy("L1"),
                             readable=False,
                             writable=False)
address_L0 = S3ReusableField("L0",
                             # L0 Location Name never varies except with a Translation
                             label=T("Country"),
                             readable=False,
                             writable=False)

# -----------------------------------------------------------------------------
def lx_fields():
    # return multiple reusable fields
    fields = (
            address_L4(),
            address_L3(),
            address_L2(),
            address_L1(),
            address_L0(),
           )
    return fields

s3.lx_fields = lx_fields

# -----------------------------------------------------------------------------
# Hide Lx fields in Create forms
# inc list_create (list_fields over-rides)
def lx_hide(table):
    table.L4.readable = False
    table.L3.readable = False
    table.L2.readable = False
    table.L1.readable = False
    table.L0.readable = False
    return

s3.lx_hide = lx_hide

# -----------------------------------------------------------------------------
def lx_onvalidation(form):
    """
        Write the Lx fields from the Location
        - used by pr_person, hrm_training, irs_ireport

        @ToDo: Allow the reverse operation.
        If these fields are populated then create/update the location
    """

    vars = form.vars
    if "location_id" in vars and vars.location_id:
        table = s3db.gis_location
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
                vars = gis.get_parent_per_level(vars,
                                                vars.location_id,
                                                feature=location,
                                                ids=False,
                                                names=True)

s3.lx_onvalidation = lx_onvalidation

# -----------------------------------------------------------------------------
def lx_update(table, record_id):
    """
        Write the Lx fields from the Location
        - used by hrm_human_resource & pr_address

        @ToDo: Allow the reverse operation.
        If these fields are populated then create/update the location
    """

    if "location_id" in table:

        ltable = s3db.gis_location
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
                vars = gis.get_parent_per_level(vars,
                                                location.id,
                                                feature=location,
                                                ids=False,
                                                names=True)
            # Update record
            db(table.id == record_id).update(**vars)

s3.lx_update = lx_update

# =============================================================================
# Addresses
#
# These fields are populated onaccept from location_id
#
# @ToDo: Add Postcode to gis.update_table_hierarchy_labels()
#

address_building_name = S3ReusableField("building_name",
                                        label=T("Building Name"),
                                        readable=False,
                                        writable=False)
address_address = S3ReusableField("address",
                                  label=T("Address"),
                                  readable=False,
                                  writable=False)
address_postcode = S3ReusableField("postcode",
                                   label=deployment_settings.get_ui_label_postcode(),
                                   readable=False,
                                   writable=False)

# -----------------------------------------------------------------------------
def address_fields():
    # return multiple reusable fields
    fields = (
            address_building_name(),
            address_address(),
            address_postcode(),
            address_L4(),
            address_L3(),
            address_L2(),
            address_L1(),
            address_L0(),
           )
    return fields

s3.address_fields = address_fields

# -----------------------------------------------------------------------------
# Hide Address fields in Create forms
# inc list_create (list_fields over-rides)
def address_hide(table):
    table.building_name.readable = False
    table.address.readable = False
    table.L4.readable = False
    table.L3.readable = False
    table.L2.readable = False
    table.L1.readable = False
    table.L0.readable = False
    table.postcode.readable = False
    return

s3.address_hide = address_hide

# -----------------------------------------------------------------------------
def address_onvalidation(form):
    """
        Write the Address fields from the Location
        - used by pr_address, org_office & cr_shelter

        @ToDo: Allow the reverse operation.
        If these fields are populated then create/update the location
    """

    vars = form.vars
    if "location_id" in vars and vars.location_id:
        table = s3db.gis_location
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
                vars = gis.get_parent_per_level(vars,
                                                vars.location_id,
                                                feature=location,
                                                ids=False,
                                                names=True)

s3.address_onvalidation = address_onvalidation

# -----------------------------------------------------------------------------
def address_update(table, record_id):
    """
        Write the Address fields from the Location
        - used by asset_asset

        @ToDo: Allow the reverse operation.
        If these fields are populated then create/update the location
    """

    if "location_id" in table:

        ltable = s3db.gis_location
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
                vars = gis.get_parent_per_level(vars,
                                                location.id,
                                                feature=location,
                                                ids=False,
                                                names=True)
            # Update record
            db(table.id == record_id).update(**vars)

s3.address_update = address_update

# =============================================================================
# Default CRUD strings
#
ADD_RECORD = T("Add Record")
LIST_RECORDS = T("List Records")
s3.crud_strings = Storage(
    title_create = ADD_RECORD,
    title_display = T("Record Details"),
    title_list = LIST_RECORDS,
    title_update = T("Edit Record"),
    title_search = T("Search Records"),
    subtitle_create = T("Add New Record"),
    subtitle_list = T("Available Records"),
    label_list_button = LIST_RECORDS,
    label_create_button = ADD_RECORD,
    label_delete_button = T("Delete Record"),
    msg_record_created = T("Record added"),
    msg_record_modified = T("Record updated"),
    msg_record_deleted = T("Record deleted"),
    msg_list_empty = T("No Records currently available"),
    msg_match = T("Matching Records"),
    msg_no_match = T("No Matching Records"),
    name_nice = T("Record"),
    name_nice_plural = T("Records"))

# END =========================================================================
