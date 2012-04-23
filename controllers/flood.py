# -*- coding: utf-8 -*-

"""
    Flood Alerts module

    @see: http://eden.sahanafoundation.org/wiki/Pakistan
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
# Define the Model
# @ToDo: Move to modules/eden/flood.py
# - here it isn't visible to s3db.load_all_models() or Sync
# -----------------------------------------------------------------------------
location_id = s3db.gis_location_id

# -----------------------------------------------------------------------------
# Rivers
resourcename = "river"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("name"),
                        s3_comments(),
                        *s3_meta_fields())

table.name.requires = IS_NOT_EMPTY()

# CRUD strings
ADD_RIVER = T("Add River")
LIST_RIVERS = T("List Rivers")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_RIVER,
    title_display = T("River Details"),
    title_list = LIST_RIVERS,
    title_update = T("Edit River"),
    title_search = T("Search Rivers"),
    subtitle_create = T("Add New River"),
    subtitle_list = T("Rivers"),
    label_list_button = LIST_RIVERS,
    label_create_button = ADD_RIVER,
    msg_record_created = T("River added"),
    msg_record_modified = T("River updated"),
    msg_record_deleted = T("River deleted"),
    msg_list_empty = T("No Rivers currently registered"))

river_id = S3ReusableField("river_id", table,
                           requires = IS_NULL_OR(IS_ONE_OF(db, "flood_river.id", "%(name)s")),
                           represent = lambda id: (id and [db(db.flood_river.id == id).select(db.flood_river.name,
                                                                                              limitby=(0, 1)).first().name] or ["None"])[0],
                           label = T("River"),
                           comment=S3AddResourceLink(c="flood",
                                                     f="river",
                                                     title=ADD_RIVER),
                           ondelete = "RESTRICT")

# -----------------------------------------------------------------------------
# Flood Reports
resourcename = "freport"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        location_id(empty=False),
                        Field("datetime", "datetime",
                              widget=S3DateTimeWidget(future=0)),
                        #document_id(), # Better to have multiple Documents on a Tab
                        s3_comments(),
                        *s3_meta_fields())

#table.document.represent = lambda document, table=table: A(table.document.retrieve(document)[0], _href=URL(f="download", args=[document]))
table.datetime.requires = IS_UTC_DATETIME(allow_future=False)
table.datetime.represent = lambda val: s3_datetime_represent(val, utc=True),
table.datetime.label = T("Date/Time")
table.datetime.default = request.utcnow

# CRUD strings
ADD_FLOOD_REPORT = T("Add Flood Report")
LIST_FLOOD_REPORTS = T("List Flood Reports")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_FLOOD_REPORT,
    title_display = T("Flood Report Details"),
    title_list = LIST_FLOOD_REPORTS,
    title_update = T("Edit Flood Report"),
    title_search = T("Search Flood Reports"),
    subtitle_create = T("Add New Flood Report"),
    subtitle_list = T("Flood Reports"),
    label_list_button = LIST_FLOOD_REPORTS,
    label_create_button = ADD_FLOOD_REPORT,
    msg_record_created = T("Flood Report added"),
    msg_record_modified = T("Flood Report updated"),
    msg_record_deleted = T("Flood Report deleted"),
    msg_list_empty = T("No Flood Reports currently registered"))

freport_id = S3ReusableField("freport_id", table,
                             requires = IS_NULL_OR(IS_ONE_OF(db, "flood_freport.id", "%(datetime)s")),
                             represent = lambda id: (id and [db(db.flood_freport.id == id).select(db.flood_freport.datetime, limitby=(0, 1)).first().datetime] or ["None"])[0],
                             label = T("Flood Report"),
                             ondelete = "CASCADE")

# -----------------------------------------------------------------------------
# Locations
freport_flowstatus_opts = {
    1:T("Normal"),
    2:T("High"),
    3:T("Very High"),
    4:T("Low")
}
resourcename = "freport_location"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        freport_id(),
                        river_id(),
                        location_id(),
                        Field("discharge", "integer"),
                        Field("flowstatus", "integer"),
                        s3_comments(),
                        *s3_meta_fields())

table.discharge.label = T("Discharge (cusecs)")
table.flowstatus.label = T("Flow Status")
table.flowstatus.requires = IS_NULL_OR(IS_IN_SET(freport_flowstatus_opts))
table.flowstatus.represent = lambda opt: freport_flowstatus_opts.get(opt, opt)

# CRUD strings
LIST_LOCATIONS = T("List Locations")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_LOCATION,
    title_display = T("Location Details"),
    title_list = LIST_LOCATIONS,
    title_update = T("Edit Location"),
    title_search = T("Search Locations"),
    subtitle_create = T("Add New Location"),
    subtitle_list = T("Locations"),
    label_list_button = LIST_LOCATIONS,
    label_create_button = ADD_LOCATION,
    msg_record_created = T("Location added"),
    msg_record_modified = T("Location updated"),
    msg_record_deleted = T("Location deleted"),
    msg_list_empty = T("No Locations currently registered"))

s3mgr.model.add_component(table, flood_freport="freport_id")

# -----------------------------------------------------------------------------
# Controllers
# -----------------------------------------------------------------------------
def index():

    """ Custom View """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)


def river():

    """ Rivers, RESTful controller """

    # Post-processor
    def user_postp(r, output):
        s3_action_buttons(r, deletable=False)
        return output
    response.s3.postp = user_postp

    output = s3_rest_controller()
    return output


def freport():

    """ Flood Reports, RESTful controller """
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Disable legacy fields, unless updating, so the data can be manually transferred to new fields
    #if "update" not in request.args:
    #    table.document.readable = table.document.writable = False

    # Post-processor
    def postp(r, output):
        s3_action_buttons(r, deletable=False)
        return output
    response.s3.postp = postp

    rheader = lambda r: flood_rheader(r, tabs = [(T("Basic Details"), None),
                                                 (T("Locations"), "freport_location")
                                                ])
    output = s3_rest_controller(module, resourcename, rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def flood_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        if r.name == "freport":
            report = r.record
            if report:
                rheader_tabs = s3_rheader_tabs(r, tabs)
                location = report.location_id
                if location:
                    location = s3db.gis_location_represent(location)
                rheader = DIV(TABLE(
                                TR(
                                    TH(T("Location") + ": "), location,
                                    TH(T("Date") + ": "), report.datetime
                                  ),
                                ),
                              rheader_tabs)

                return rheader

    return None

