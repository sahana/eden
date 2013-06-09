# -*- coding: utf-8 -*-

from gluon import current, URL
from gluon.html import *
from gluon.storage import Storage
from gluon.validators import IS_NULL_OR

from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3layouts import S3AddResourceLink
from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
from s3.s3fields import S3Represent
from s3.s3resource import S3FieldSelector
from s3.s3utils import S3DateTime, s3_auth_user_represent_name, s3_avatar_represent, s3_unicode
from s3.s3validators import IS_INT_AMOUNT, IS_LOCATION_SELECTOR2, IS_ONE_OF
from s3.s3widgets import S3LocationSelectorWidget2

T = current.T
s3 = current.response.s3
settings = current.deployment_settings

"""
    Template settings for DRM Portal
"""

datetime_represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)

# =============================================================================
# System Settings
# -----------------------------------------------------------------------------
# Authorization Settings
settings.auth.registration_requires_approval = True
settings.auth.registration_requires_verification = True
settings.auth.registration_requests_organisation = True
settings.auth.registration_organisation_required = True
settings.auth.registration_requests_site = False

settings.auth.registration_link_user_to = {"staff": T("Staff")}

settings.auth.record_approval = False

# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 3 # Controllers
settings.security.map = True

# Owner Entity
settings.auth.person_realm_human_resource_site_then_org = False

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ["DRMP"]

settings.base.system_name = T("Disaster Risk Management Portal")
settings.base.system_name_short = T("DRMP")

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "DRMP"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
#settings.gis.map_height = 600
#settings.gis.map_width = 854

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
    #("tet", "Tetum"),
])
# Default Language
settings.L10n.default_language = "en"
# Default timezone for users
settings.L10n.utc_offset = "UTC +0900"
# Unsortable 'pretty' date format
settings.L10n.date_format = "%d %b %y"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","

# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ["TL"]

# Until we add support to LocationSelector2 to set dropdowns from LatLons
settings.gis.check_within_parent_boundaries = False

# Hide unnecessary Toolbar items
settings.gis.nav_controls = False

# -----------------------------------------------------------------------------
# Finance settings
settings.fin.currencies = {
    "AUD" : T("Australian Dollars"),
    "EUR" : T("Euros"),
    "GBP" : T("Great British Pounds"),
    "USD" : T("United States Dollars"),
}

# -----------------------------------------------------------------------------
# Enable this for a UN-style deployment
#settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
settings.ui.camp = True

# -----------------------------------------------------------------------------
# Save Search Widget
settings.save_search.widget = False

# Uncomment to restrict the export formats available
settings.ui.export_formats = ["xls"]

settings.ui.update_label = "Edit"

# =============================================================================
# Module Settings

# -----------------------------------------------------------------------------
# Human Resource Management
settings.hrm.staff_label = "Contacts"
# Uncomment to allow Staff & Volunteers to be registered without an email address
settings.hrm.email_required = False
# Uncomment to show the Organisation name in HR represents
settings.hrm.show_organisation = True
# Uncomment to disable Staff experience
settings.hrm.staff_experience = False
# Uncomment to disable the use of HR Credentials
settings.hrm.use_credentials = False
# Uncomment to disable the use of HR Skills
settings.hrm.use_skills = False
# Uncomment to disable the use of HR Teams
settings.hrm.use_teams = False

# -----------------------------------------------------------------------------
# Org
settings.org.site_label = "Office"

# -----------------------------------------------------------------------------
# Project
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True

# -----------------------------------------------------------------------------
def currency_represent(v):
    """
        Custom Representation of Currencies
    """
    if v == "USD":
        return "$"
    elif v == "AUD":
        return "A$"
    elif v == "EUR":
        return "£"
    elif v == "GBP":
        return "£"
    else:
        return current.messages["NONE"]

# -----------------------------------------------------------------------------
def location_represent(id, row=None):
    """
        Custom Representation of Locations
    """

    if not row:
        if not id:
            return current.messages["NONE"]
        table = current.s3db.gis_location
        row = current.db(table.id == id).select(table.L1,
                                                table.L2,
                                                table.L3,
                                                limitby=(0, 1)).first()

    if row.L3:
        represent = "%s | %s | %s" % (s3_unicode(row.L1) if row.L1 else "",
                                      s3_unicode(row.L2) if row.L2 else "",
                                      s3_unicode(row.L3) if row.L3 else "",
                                      )
    elif row.L2:
        represent = "%s | %s" % (s3_unicode(row.L1) if row.L1 else "",
                                 s3_unicode(row.L2) if row.L2 else "",
                                 )
    elif row.L1:
        represent = row.L1
    else:
        represent = current.messages["NONE"]

    return represent

# -----------------------------------------------------------------------------
def render_contacts(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Contacts on the Profile pages

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "hrm_human_resource.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    #author = record["hrm_human_resource.modified_by"]
    date = record["hrm_human_resource.modified_on"]
    fullname = record["hrm_human_resource.person_id"]
    job_title = raw["hrm_human_resource.job_title_id"] or ""
    if job_title:
        job_title = "- %s" % record["hrm_human_resource.job_title_id"]
    #organisation = record["hrm_human_resource.organisation_id"]
    organisation_id = raw["hrm_human_resource.organisation_id"]
    #org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    pe_id = raw["pr_person.pe_id"]
    person_id = raw["hrm_human_resource.person_id"]
    location = record["org_site.location_id"]
    location_id = raw["org_site.location_id"]
    location_url = URL(c="gis", f="location",
                       args=[location_id, "profile"])
    address = raw["gis_location.addr_street"] or T("no office assigned")
    email = raw["pr_email_contact.value"] or T("no email address")
    if isinstance(email, list):
        email = email[0]
    phone = raw["pr_phone_contact.value"] or T("no phone number")
    if isinstance(phone, list):
        phone = phone[0]

    db = current.db
    s3db = current.s3db
    ltable = s3db.pr_person_user
    query = (ltable.pe_id == pe_id)
    row = db(query).select(ltable.user_id,
                           limitby=(0, 1)
                           ).first()
    if row:
        # Use Personal Avatar
        # @ToDo: Optimise by not doing DB lookups (especially duplicate) within render, but doing these in the bulk query
        avatar = s3_avatar_represent(row.user_id,
                                     _class="media-object")
    else:
        avatar = IMG(_src=URL(c="static", f="img", args="blank-user.gif"),
                     _class="media-object")

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = db.pr_person
    if permit("update", table, record_id=person_id):
        vars = {"refresh": listid,
                "record": record_id,
                }
        f = current.request.function
        if f == "organisation" and organisation_id:
            vars["(organisation)"] = organisation_id
        edit_url = URL(c="hrm", f="person",
                       args=[person_id, "update.popup"],
                       vars=vars)
        title_update = current.response.s3.crud_strings.hrm_human_resource.title_update
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=edit_url,
                     _class="s3_modal",
                     _title=title_update,
                     )
    else:
        edit_btn = ""
        edit_url = "#"
        title_update = ""
    # Deletions failing due to Integrity Errors
    #if permit("delete", table, record_id=person_id):
    #    delete_btn = A(I(" ", _class="icon icon-remove-sign"),
    #                   _class="dl-item-delete",
    #                   )
    #else:
    delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    avatar = A(avatar,
               _href=edit_url,
               _class="pull-left s3_modal",
               _title=title_update,
               )

    # Render the item
    body = TAG[""](P(fullname,
                     " ",
                     SPAN(job_title),
                     _class="person_pos",
                     ),
                   P(I(_class="icon-phone"),
                     " ",
                     SPAN(phone),
                     " ",
                     I(_class="icon-envelope-alt"),
                     " ",
                     SPAN(email),
                     _class="main_contact_ph",
                     ),
                   P(I(_class="icon-home"),
                     " ",
                     address,
                     _class="main_office-add",
                     ))

    item = DIV(DIV(SPAN(" ", _class="card-title"),
                   SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(body,
                           # Organisation only needed if displaying elsewhere than org profile
                           # Author confusing with main contact record
                           #DIV(#author,
                           #    #" - ",
                           #    A(organisation,
                           #      _href=org_url,
                           #      _class="card-organisation",
                           #      ),
                           #    _class="card-person",
                           #    ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def render_events(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Events on the Disaster Selection Page

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "event_event.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    name = record["event_event.name"]
    date = record["event_event.zero_hour"]
    closed = raw["event_event.closed"]
    event_type = record["event_event_type.name"]
    event_url = URL(c="event", f="event",
                    args=[record_id, "profile"])
    comments = raw["event_event.comments"] or ""

    if closed:
        edit_bar = DIV()
    else:
        item_class = "%s disaster" % item_class

        permit = current.auth.s3_has_permission
        table = resource.table
        if permit("update", table, record_id=record_id):
            edit_btn = A(I(" ", _class="icon icon-edit"),
                         _href=URL(c="event", f="event",
                                   args=[record_id, "update.popup"],
                                   vars={"refresh": listid,
                                         "record": record_id}),
                         _class="s3_modal",
                         _title=current.response.s3.crud_strings.event_event.title_update,
                         )
        else:
            edit_btn = ""
        if permit("delete", table, record_id=record_id):
            delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                           _class="dl-item-delete",
                          )
        else:
            delete_btn = ""
        edit_bar = DIV(edit_btn,
                       delete_btn,
                       _class="edit-bar fright",
                       )

    # Tallies
    tally_alerts = 0
    tally_incidents = 0
    tally_assessments = 0
    tally_activities = 0
    tally_reports = 0
    db = current.db
    s3db = current.s3db
    ltable = s3db.event_event_post
    table = db.cms_post
    stable = db.cms_series
    types = ["Alert", "Incident", "Assessment", "Activity", "Report"]
    query = (table.deleted == False) & \
            (ltable.event_id == record_id) & \
            (ltable.post_id == table.id) & \
            (stable.id == table.series_id) & \
            (stable.name.belongs(types))
    rows = db(query).select(stable.name)
    for row in rows:
        series = row.name
        if series == "Alert":
            tally_alerts += 1
        elif series == "Incident":
            tally_incidents += 1
        elif series == "Assessment":
            tally_assessments += 1
        elif series == "Activity":
            tally_activities += 1
        elif series == "Report":
            tally_reports += 1

    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static",
                                  f="themes",
                                  args=["DRMP", "img", "%s.png" % event_type]),
                         ),
                     _class="pull-left",
                     _href=event_url,
                     ),
  		           DIV(SPAN(A(name,
                              _href=event_url,
                              _class="media-heading"
                              ),
                            ),
                       SPAN(date,
                            _class="date-title",
                            ),
                       edit_bar,
                       _class="card-header-select",
                       ),
                   DIV(P(comments),
                       P(T("Alerts"),
                         SPAN(tally_alerts,
                              _class="badge badge-warning",
                              ),
                         T("Incidents"),
                         SPAN(tally_incidents,
                              _class="badge",
                              ),
                         T("Assessments"),
                         SPAN(tally_assessments,
                              _class="badge",
                              ),
                         T("Activities"),
                         SPAN(tally_activities,
                              _class="badge",
                              ),
                         T("Reports"),
                         SPAN(tally_reports,
                              _class="badge",
                              ),
                         _class="tally",
                         ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def render_locations(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Locations on the Selection Page

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "gis_location.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    name = raw["gis_location.name"]
    level = raw["gis_location.level"]
    L1 = raw["gis_location.L1"]
    L2 = raw["gis_location.L2"]
    L3 = raw["gis_location.L3"]
    location_url = URL(c="gis", f="location",
                       args=[record_id, "profile"])

    if level == "L1":
        represent = name
    if level == "L2":
        represent = "%s (%s)" % (name, L1)
    elif level == "L3":
        represent = "%s (%s, %s)" % (name, L2, L1)
    else:
        # L0 or specific
        represent = name

    # Users don't edit locations
    # permit = current.auth.s3_has_permission
    # table = current.db.gis_location
    # if permit("update", table, record_id=record_id):
        # edit_btn = A(I(" ", _class="icon icon-edit"),
                     # _href=URL(c="gis", f="location",
                               # args=[record_id, "update.popup"],
                               # vars={"refresh": listid,
                                     # "record": record_id}),
                     # _class="s3_modal",
                     # _title=current.response.s3.crud_strings.gis_location.title_update,
                     # )
    # else:
        # edit_btn = ""
    # if permit("delete", table, record_id=record_id):
        # delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       # _class="dl-item-delete",
                      # )
    # else:
        # delete_btn = ""
    # edit_bar = DIV(edit_btn,
                   # delete_btn,
                   # _class="edit-bar fright",
                   # )

    # Tallies
    # NB We assume that all records are readable here
    # Search all sub-locations
    locations = current.gis.get_children(record_id)
    locations = [l.id for l in locations]
    locations.append(record_id)
    db = current.db
    s3db = current.s3db
    ltable = s3db.project_location
    table = db.project_project
    query = (table.deleted == False) & \
            (ltable.deleted == False) & \
            (ltable.project_id == table.id) & \
            (ltable.location_id.belongs(locations))
    rows = db(query).select(table.id, distinct=True)
    tally_projects = len(rows)
    tally_incidents = 0
    tally_activities = 0
    tally_reports = 0
    table = s3db.cms_post
    stable = db.cms_series
    types = ["Incident", "Activity", "Report"]
    query = (table.deleted == False) & \
            (table.location_id.belongs(locations)) & \
            (stable.id == table.series_id) & \
            (stable.name.belongs(types))
    rows = db(query).select(stable.name)
    for row in rows:
        series = row.name
        if series == "Incident":
            tally_incidents += 1
        elif series == "Activity":
            tally_activities += 1
        elif series == "Report":
            tally_reports += 1
    
    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static",
                                  f="themes",
                                  args=["DRMP", "img", "%s.png" % s3_unicode(name)]),
                         ),
                     _class="pull-left",
                     _href=location_url,
                     ),
                   DIV(SPAN(A(represent,
                              _href=location_url,
                              _class="media-heading"
                              ),
                            ),
                       #edit_bar,
                       _class="card-header-select",
                       ),
                   DIV(P(T("Incidents"),
                         SPAN(tally_incidents,
                              _class="badge",
                              ),
                         T("Reports"),
                         SPAN(tally_reports,
                              _class="badge",
                              ),
                         T("Projects"),
                         SPAN(tally_projects,
                              _class="badge",
                              ),
                         T("Activities"),
                         SPAN(tally_activities,
                              _class="badge",
                              ),
                         _class="tally",
                         ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def render_locations_profile(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Locations on the Profile Page
        - UNUSED

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "gis_location.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    name = record["gis_location.name"]
    location_url = URL(c="gis", f="location",
                       args=[record_id, "profile"])

    # Placeholder to maintain style
    #logo = DIV(IMG(_class="media-object"),
    #               _class="pull-left")

    # We don't Edit Locations
    # Edit Bar
    # permit = current.auth.s3_has_permission
    # table = current.db.gis_location
    # if permit("update", table, record_id=record_id):
        # vars = {"refresh": listid,
                # "record": record_id,
                # }
        # f = current.request.function
        # if f == "organisation" and organisation_id:
            # vars["(organisation)"] = organisation_id
        # edit_btn = A(I(" ", _class="icon icon-edit"),
                     # _href=URL(c="gis", f="location",
                               # args=[record_id, "update.popup"],
                               # vars=vars),
                     # _class="s3_modal",
                     # _title=current.response.s3.crud_strings.gis_location.title_update,
                     # )
    # else:
        # edit_btn = ""
    # if permit("delete", table, record_id=record_id):
        # delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       # _class="dl-item-delete",
                       # )
    # else:
        # delete_btn = ""
    # edit_bar = DIV(edit_btn,
                   # delete_btn,
                   # _class="edit-bar fright",
                   # )

    # Render the item
    item = DIV(DIV(DIV(#SPAN(A(name,
                       #       _href=location_url,
                       #       ),
                       #     _class="location-title"),
                       #" ",
                       #edit_bar,
                       P(A(name,
                           _href=location_url,
                           ),
                         _class="card_comments"),
                       _class="span5"), # card-details
                   _class="row",
                   ),
               )

    return item

# -----------------------------------------------------------------------------
def render_offices(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Offices on the Profile pages

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "org_office.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    name = record["org_office.name"]
    author = record["org_office.modified_by"]
    date = record["org_office.modified_on"]
    organisation = record["org_office.organisation_id"]
    organisation_id = raw["org_office.organisation_id"]
    location = record["org_office.location_id"]
    location_id = raw["org_office.location_id"]
    location_url = URL(c="gis", f="location",
                       args=[location_id, "profile"])
    address = raw["gis_location.addr_street"]
    office_type = record["org_office.office_type_id"]
    logo = raw["org_organisation.logo"]

    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    if logo:
        logo = A(IMG(_src=URL(c="default", f="download", args=[logo]),
                     _class="media-object",
                     ),
                 _href=org_url,
                 _class="pull-left",
                 )
    else:
        logo = DIV(IMG(_class="media-object"),
                   _class="pull-left")

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.db.org_office
    if permit("update", table, record_id=record_id):
        vars = {"refresh": listid,
                "record": record_id,
                }
        f = current.request.function
        if f == "organisation" and organisation_id:
            vars["(organisation)"] = organisation_id
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="org", f="office",
                               args=[record_id, "update.popup"],
                               vars=vars),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.org_office.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    avatar = logo
    body = TAG[""](P(name),
                   P(I(_class="icon-flag"),
                     " ",
                     SPAN(office_type),
                     " ",
                     _class="main_contact_ph",
                     ),
                   P(I(_class="icon-home"),
                     " ",
                     address,
                     _class="main_office-add",
                     ))

    item = DIV(DIV(SPAN(" ", _class="card-title"),
                   SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(body,
                           DIV(author,
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def render_organisations(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Organisations on the Stakeholder Selection Page

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "org_organisation.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail span6"

    raw = record._row
    name = record["org_organisation.name"]
    logo = raw["org_organisation.logo"]
    # @ToDo: Just take National offices
    addresses = raw["gis_location.addr_street"]
    if addresses:
        if isinstance(addresses, list):
            address = addresses[0]
        else:
            address = addresses
    else:
        address = ""
    phone = raw["org_organisation.phone"] or ""

    org_url = URL(c="org", f="organisation", args=[record_id, "profile"])
    if logo:
        logo = A(IMG(_src=URL(c="default", f="download", args=[logo]),
                     _class="media-object",
                     ),
                 _href=org_url,
                 _class="pull-left",
                 )
    else:
        logo = DIV(IMG(_class="media-object"),
                   _class="pull-left")

    permit = current.auth.s3_has_permission
    table = current.db.org_organisation
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="org", f="organisation",
                               args=[record_id, "update.popup"],
                               vars={"refresh": listid,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.org_organisation.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                      )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Tallies
    # NB We assume that all records are readable here
    db = current.db
    s3db = current.s3db
    table = s3db.project_project
    query = (table.deleted == False) & \
            (table.organisation_id == record_id)
    tally_projects = db(query).count()
    tally_assessments = 0
    tally_activities = 0
    tally_reports = 0
    table = s3db.cms_post
    atable = db.auth_user
    stable = db.cms_series
    types = ["Assessment", "Activity", "Report"]
    query = (table.deleted == False) & \
            (table.created_by == atable.id) & \
            (atable.organisation_id == record_id) & \
            (stable.id == table.series_id) & \
            (stable.name.belongs(types))
    rows = db(query).select(stable.name)
    for row in rows:
        series = row.name
        if series == "Assessment":
            tally_assessments += 1
        elif series == "Activity":
            tally_activities += 1
        elif series == "Report":
            tally_reports += 1
    
    # Render the item
    item = DIV(DIV(logo,
                   DIV(SPAN(A(name,
                              _href=org_url,
                              _class="media-heading"
                              ),
                            ),
                       edit_bar,
                       _class="card-header-select",
                       ),
                   DIV(P(I(_class="icon icon-phone"),
                         " ",
                         phone,
                         _class="main_contact_ph",
                         ),
                       P(I(_class="icon icon-home"),
                         " ",
                         address,
                         _class="main_office-add",
                         ),
                       P(T("Projects"),
                         SPAN(tally_projects,
                              _class="badge",
                              ),
                         T("Activities"),
                         SPAN(tally_activities,
                              _class="badge",
                              ),
                         T("Reports"),
                         SPAN(tally_reports,
                              _class="badge",
                              ),
                         T("Assessments"),
                         SPAN(tally_assessments,
                              _class="badge",
                              ),
                         _class="tally",
                         ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def render_posts(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for CMS Posts on the Home & Updates pages

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    T = current.T
    pkey = "cms_post.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    series = record["cms_post.series_id"]
    date = record["cms_post.created_on"]
    body = record["cms_post.body"]
    location = record["cms_post.location_id"]
    location_id = raw["cms_post.location_id"]
    location_url = URL(c="gis", f="location", args=[location_id])
    author = record["cms_post.created_by"]
    author_id = raw["cms_post.created_by"]
    organisation = record["auth_user.organisation_id"]
    organisation_id = raw["auth_user.organisation_id"]
    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])

    db = current.db
    s3db = current.s3db
    ltable = s3db.pr_person_user
    ptable = db.pr_person
    query = (ltable.user_id == author_id) & \
            (ltable.pe_id == ptable.pe_id)
    row = db(query).select(ptable.id,
                           limitby=(0, 1)
                           ).first()
    if row:
        person_url = URL(c="hrm", f="person", args=[row.id])
    else:
        person_url = "#"
    author = A(author,
               _href=person_url,
               )

    # Use Personal Avatar
    # @ToDo: Optimise by not doing DB lookups (especially duplicate) within render, but doing these in the bulk query
    #avatar = s3_avatar_represent(author_id,
    #                             _class="media-object")
    #avatar = A(avatar,
    #           _href=person_url,
    #           _class="pull-left",
    #           )

    # Use Organisation Logo
    otable = db.org_organisation
    row = db(otable.id == organisation_id).select(otable.logo,
                                                  limitby=(0, 1)
                                                  ).first()
    if row and row.logo:
        logo = URL(c="default", f="download", args=[row.logo])
    else:
        logo = ""
    avatar = IMG(_src=logo,
                 _height=50,
                 _width=50,
                 _style="padding-right:5px;",
                 _class="media-object")
    avatar = A(avatar,
               _href=org_url,
               _class="pull-left",
               )

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = db.cms_post
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="cms", f="post",
                               args=[record_id, "update.popup"],
                               vars={"refresh": listid,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=T("Edit %(type)s") % dict(type=T(series)),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Dropdown of available documents
    documents = raw["doc_document.file"]
    if documents:
        if not isinstance(documents, list):
            documents = [documents]
        doc_list = UL(_class="dropdown-menu",
                      _role="menu",
                      )
        retrieve = db.doc_document.file.retrieve
        for doc in documents:
            try:
                doc_name = retrieve(doc)[0]
            except IOError:
                doc_name = current.messages["NONE"]
            doc_url = URL(c="default", f="download",
                          args=[doc])
            doc_item = LI(A(I(_class="icon-file"),
                            " ",
                            doc_name,
                            _href=doc_url,
                            ),
                          _role="menuitem",
                          )
            doc_list.append(doc_item)
        docs = DIV(A(I(_class="icon-paper-clip"),
                     SPAN(_class="caret"),
                     _class="btn dropdown-toggle",
                     _href="#",
                     **{"_data-toggle": "dropdown"}
                     ),
                   doc_list,
                   _class="btn-group attachments dropdown pull-right",
                   )
    else:
        docs = ""

    if current.request.controller == "default":
        # Mixed resource lists (Home, Updates)
        icon = series.lower().replace(" ", "_")
        card_label = TAG[""](I(_class="icon icon-%s" % icon),
                             SPAN(" %s" % T(series),
                                  _class="card-title"))
        # Type cards
        if series == "Alert": 
            # Apply additional highlighting for Alerts
            item_class = "%s disaster" % item_class
    else:
        card_label = SPAN(" ", _class="card-title")

    # Render the item
    item = DIV(DIV(card_label,
                   SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(body,
                           DIV(author,
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               docs,
               _class=item_class,
               _id=item_id,
               )

    return item

s3.render_posts = render_posts

# -----------------------------------------------------------------------------
def render_projects(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Projects on the Profile pages

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "project_project.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    name = record["project_project.name"]
    author = record["project_project.modified_by"]
    author_id = raw["project_project.modified_by"]
    contact = record["project_project.human_resource_id"]
    date = record["project_project.modified_on"]
    organisation = record["project_project.organisation_id"]
    organisation_id = raw["project_project.organisation_id"]
    location = record["project_location.location_id"]
    location_ids = raw["project_location.location_id"]
    if isinstance(location_ids, list):
        locations = location.split(",")
        locations_list = []
        length = len(location_ids)
        i = 0
        for location_id in location_ids:
            location_url = URL(c="gis", f="location",
                               args=[location_id, "profile"])
            locations_list.append(A(locations[i], _href=location_url))
            i += 1
            if i != length:
                locations_list.append(",")
    else:
        location_url = URL(c="gis", f="location",
                           args=[location_ids, "profile"])
        locations_list = [A(location, _href=location_url)]

    logo = raw["org_organisation.logo"]
    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    if logo:
        avatar = A(IMG(_src=URL(c="default", f="download", args=[logo]),
                       _class="media-object",
                       ),
                   _href=org_url,
                   _class="pull-left",
                   )
    else:
        avatar = DIV(IMG(_class="media-object"),
                     _class="pull-left")

    db = current.db
    s3db = current.s3db
    ltable = s3db.pr_person_user
    ptable = db.pr_person
    query = (ltable.user_id == author_id) & \
            (ltable.pe_id == ptable.pe_id)
    row = db(query).select(ptable.id,
                           limitby=(0, 1)
                           ).first()
    if row:
        person_url = URL(c="hrm", f="person", args=[row.id])
    else:
        person_url = "#"
    author = A(author,
               _href=person_url,
               )

    start_date = raw["project_project.start_date"] or ""
    if start_date:
        start_date = record["project_project.start_date"]
    end_date = raw["project_project.end_date"] or ""
    if end_date:
        end_date = record["project_project.end_date"]
    budget = record["project_project.budget"]
    if budget:
        budget = "USD %s" % budget

    partner = record["project_partner_organisation.organisation_id"]
    partner_ids = raw["project_partner_organisation.organisation_id"]
    if isinstance(partner_ids, list):
        partners = partner.split(",")
        partners_list = []
        length = len(partner_ids)
        i = 0
        for partner_id in partner_ids:
            partner_url = URL(c="org", f="organisation",
                              args=[partner_id, "profile"])
            partners_list.append(A(partners[i], _href=partner_url))
            i += 1
            if i != length:
                partners_list.append(",")
    elif partner_ids:
        partner_url = URL(c="org", f="organisation",
                          args=[partner_ids, "profile"])
        partners_list = [A(partner, _href=partner_url)]
    else:
        partners_list = [current.messages["NONE"]]

    donor = record["project_donor_organisation.organisation_id"]
    donor_ids = raw["project_donor_organisation.organisation_id"]
    if isinstance(donor_ids, list):
        donors = donor.split(",")
        amounts = raw["project_donor_organisation.amount"]
        if not isinstance(amounts, list):
            amounts = [amounts for donor_id in donor_ids]
        currencies = raw["project_donor_organisation.currency"]
        if not isinstance(currencies, list):
            currencies = [currencies for donor_id in donor_ids]
        amount_represent = IS_INT_AMOUNT.represent
        donors_list = []
        length = len(donor_ids)
        i = 0
        for donor_id in donor_ids:
            if donor_id:
                donor_url = URL(c="org", f="organisation",
                                args=[donor_id, "profile"])
                donor = A(donors[i], _href=donor_url)
                amount = amounts[i]
                if amount:
                    donor = TAG[""](donor,
                                    " - ",
                                    currency_represent(currencies[i]),
                                    amount_represent(amount))
            else:
                donor = current.messages["NONE"]
            donors_list.append(donor)
            i += 1
            if i != length:
                donors_list.append(",")
    elif donor_ids:
        donor_url = URL(c="org", f="organisation",
                      args=[donor_ids, "profile"])
        donors_list = [A(donor, _href=donor_url)]
    else:
        donors_list = [current.messages["NONE"]]

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.db.project_project
    if permit("update", table, record_id=record_id):
        vars = {"refresh": listid,
                "record": record_id,
                }
        f = current.request.function
        if f == "organisation" and organisation_id:
            vars["(organisation)"] = organisation_id
        # "record not found" since multiples here
        #elif f == "location" and location_ids:
        #    vars["(location)"] = location_ids
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="project", f="project",
                               args=[record_id, "update.popup"],
                               vars=vars),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.project_project.title_update,
                     )
    else:
        # Read in Popup
        edit_btn = A(I(" ", _class="icon icon-search"),
                     _href=URL(c="project", f="project",
                               args=[record_id, "read.popup"]),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.project_project.title_display,
                     )
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Dropdown of available documents
    documents = raw["doc_document.file"]
    if documents:
        if not isinstance(documents, list):
            documents = [documents]
        doc_list = UL(_class="dropdown-menu",
                      _role="menu",
                      )
        retrieve = db.doc_document.file.retrieve
        for doc in documents:
            try:
                doc_name = retrieve(doc)[0]
            except IOError:
                doc_name = current.messages["NONE"]
            doc_url = URL(c="default", f="download",
                          args=[doc])
            doc_item = LI(A(I(_class="icon-file"),
                            " ",
                            doc_name,
                            _href=doc_url,
                            ),
                          _role="menuitem",
                          )
            doc_list.append(doc_item)
        docs = DIV(A(I(_class="icon-paper-clip"),
                     SPAN(_class="caret"),
                     _class="btn dropdown-toggle",
                     _href="#",
                     **{"_data-toggle": "dropdown"}
                     ),
                   doc_list,
                   _class="btn-group attachments dropdown pull-right",
                   )
    else:
        docs = ""

    # Render the item,
    body = TAG[""](P(I(_class="icon-user"),
                     " ",
                     STRONG("%s:" % T("Focal Point")),
                     " ",
                     contact,
                     _class="main_contact_ph"),
                   P(I(_class="icon-calendar"),
                     " ",
                     STRONG("%s:" % T("Start & End Date")),
                     " ",
                     T("%(start_date)s to %(end_date)s") % \
                            dict(start_date=start_date,
                            end_date = end_date),
                     _class="main_contact_ph"),
                   P(I(_class="icon-link"),
                     " ",
                     STRONG("%s:" % T("Partner")),
                     " ",
                     *partners_list,
                     _class="main_contact_ph"),
                   P(I(_class="icon-money"),
                     " ",
                     STRONG("%s:" % T("Donor")),
                     " ",
                     *donors_list,
                     _class="main_office-add")
                   )

    item = DIV(DIV(SPAN(" ", _class="card-title"),
                   SPAN(*locations_list,
                        _class="location-title"
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(body,
                           DIV(author,
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def render_resources(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Resources on the Profile pages

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "org_resource.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    author = record["org_resource.modified_by"]
    date = record["org_resource.modified_on"]
    quantity = record["org_resource.value"]
    resource_type = record["org_resource.parameter_id"]
    body = "%s %s" % (quantity, resource_type)
    comments = raw["org_resource.comments"]
    organisation = record["org_resource.organisation_id"]
    organisation_id = raw["org_resource.organisation_id"]
    location = record["org_resource.location_id"]
    location_id = raw["org_resource.location_id"]
    location_url = URL(c="gis", f="location",
                       args=[location_id, "profile"])
    logo = raw["org_organisation.logo"]

    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    if logo:
        logo = A(IMG(_src=URL(c="default", f="download", args=[logo]),
                     _class="media-object",
                     ),
                 _href=org_url,
                 _class="pull-left",
                 )
    else:
        logo = DIV(IMG(_class="media-object"),
                   _class="pull-left")

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.db.org_resource
    if permit("update", table, record_id=record_id):
        vars = {"refresh": listid,
                "record": record_id,
                }
        f = current.request.function
        if f == "organisation" and organisation_id:
            vars["(organisation)"] = organisation_id
        elif f == "location" and location_id:
            vars["(location)"] = location_id
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="org", f="resource",
                               args=[record_id, "update.popup"],
                               vars=vars),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.org_resource.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    avatar = logo
    body = TAG[""](body, BR(), comments)

    item = DIV(DIV(SPAN(" ", _class="card-title"),
                   SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(body,
                           DIV(author,
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def customize_cms_post_fields():
    """
        Customize cms_post fields for it's own controller & for Profile pages
    """

    s3db = current.s3db
    table = s3db.cms_post

    field = table.location_id
    field.label = ""
    field.represent = location_represent
    field.requires = IS_NULL_OR(
                        IS_LOCATION_SELECTOR2(levels=["L1", "L2", "L3"])
                     )
    field.widget = S3LocationSelectorWidget2(levels=["L1", "L2", "L3"])

    table.created_by.represent = s3_auth_user_represent_name
    table.created_on.represent = datetime_represent

    list_fields = ["series_id",
                   "location_id",
                   "created_on",
                   "body",
                   "created_by",
                   "created_by$organisation_id",
                   "document.file",
                   "event_post.event_id",
                   ]

    s3db.configure("cms_post",
                   list_fields = list_fields,
                   )

    return table
    
# -----------------------------------------------------------------------------
def customize_cms_post(**attr):
    """
        Customize cms_post controller
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            # Called first so that we can unhide the Type field
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive:
            table = customize_cms_post_fields()

            get_vars = current.request.get_vars

            field = table.series_id
            field.label = T("Type")
            refresh = get_vars.get("refresh", None)
            if refresh == "datalist":
                # We must be coming from the Updates page so can change the type on-the-fly
                field.readable = field.writable = True
            #field.requires = field.requires.other
            #field = table.name
            #field.readable = field.writable = False
            #field = table.title
            #field.readable = field.writable = False
            field = table.avatar
            field.default = True
            #field.readable = field.writable = False
            field = table.replies
            field.default = False
            #field.readable = field.writable = False
            
            field = table.body
            field.label = T("Description")
            field.widget = None
            #table.comments.readable = table.comments.writable = False

            if current.request.controller == "default":
                # Don't override card layout for Updates/Homepage
                return True

            # Filter from a Profile page?
            # If so, then default the fields we know
            s3db = current.s3db
            location_id = get_vars.get("~.(location)", None)
            if location_id:
                table.location_id.default = location_id
            event_id = get_vars.get("~.(event)", None)
            if event_id:
                crud_form = S3SQLCustomForm(
                    "series_id",
                    "body",
                    "location_id",
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                )
                def create_onaccept(form):
                    table = current.s3db.event_event_post
                    table.insert(event_id=event_id, post_id=form.vars.id)

                s3db.configure("cms_post",
                               create_onaccept = create_onaccept, 
                               )
            else:
                crud_form = S3SQLCustomForm(
                    "series_id",
                    "body",
                    "location_id",
                    S3SQLInlineComponent(
                        "event_post",
                        #label = T("Disaster(s)"),
                        label = T("Disaster"),
                        multiple = False,
                        fields = ["event_id"],
                        orderby = "event_id$name",
                    ),
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                )

            # Return to List view after create/update/delete
            # We now do all this in Popups
            #url_next = URL(c="default", f="index", args="updates")

            s3db.configure("cms_post",
                           #create_next = url_next,
                           #delete_next = url_next,
                           #update_next = url_next,
                           crud_form = crud_form,
                           # Don't include a Create form in 'More' popups
                           listadd = False,
                           list_layout = render_posts,
                           )

            s3.cancel = True

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive and isinstance(output, dict):
            if "form" in output:
                output["form"].add_class("cms_post")
            elif "item" in output and hasattr(output["item"], "add_class"):
                output["item"].add_class("cms_post")

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_cms_post = customize_cms_post

# -----------------------------------------------------------------------------
def customize_event_event(**attr):
    """
        Customize event_event controller
        - Profile Page
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        if r.interactive:
            db = current.db
            s3db = current.s3db

            # Load normal Model
            table = s3db.event_event

            if r.method == "profile":
                # Customise the cms_post table as that is used for the widgets
                customize_cms_post_fields()

                # Represent used in rendering
                current.auth.settings.table_user.organisation_id.represent = s3db.org_organisation_represent

                gtable = db.gis_location
                ltable = db.event_event_location
                query = (ltable.event_id == r.id) & \
                        (ltable.location_id == gtable.id)
                location = db(query).select(gtable.id,
                                            gtable.lat_max,
                                            gtable.lon_max,
                                            gtable.lat_min,
                                            gtable.lon_min,
                                            limitby=(0, 1)).first()
                if location:
                    bbox = {"lat_max" : location.lat_max,
                            "lon_max" : location.lon_max,
                            "lat_min" : location.lat_min,
                            "lon_min" : location.lon_min
                            }
                    default = "~.(location)=%s" % location.id
                else:
                    # Default bounds
                    bbox = {}
                    # No default Location
                    default = None
                map_widget = dict(label = "Map",
                                  type = "map",
                                  context = "event",
                                  icon = "icon-map",
                                  height = 383,
                                  width = 568,
                                  bbox = bbox,
                                  )
                alerts_widget = dict(label = "Alerts",
                                     title_create = "Add New Alert",
                                     type = "datalist",
                                     tablename = "cms_post",
                                     context = "event",
                                     default = default,
                                     filter = S3FieldSelector("series_id$name") == "Alert",
                                     icon = "icon-alert",
                                     layer = "Alerts",
                                     # provided by Catalogue Layer
                                     #marker = "alert",
                                     list_layout = render_posts,
                                     )
                incidents_widget = dict(label = "Incidents",
                                        title_create = "Add New Incident",
                                        type = "datalist",
                                        tablename = "cms_post",
                                        context = "event",
                                        default = default,
                                        filter = S3FieldSelector("series_id$name") == "Incident",
                                        icon = "icon-incident",
                                        layer = "Incidents",
                                        # provided by Catalogue Layer
                                        #marker = "incident",
                                        list_layout = render_posts,
                                        )
                assessments_widget = dict(label = "Assessments",
                                          title_create = "Add New Assessment",
                                          type = "datalist",
                                          tablename = "cms_post",
                                          context = "event",
                                          default = default,
                                          filter = S3FieldSelector("series_id$name") == "Assessment",
                                          icon = "icon-assessment",
                                          layer = "Assessments",
                                          # provided by Catalogue Layer
                                          #marker = "assessment",
                                          list_layout = render_posts,
                                          )
                activities_widget = dict(label = "Activities",
                                         title_create = "Add New Activity",
                                         type = "datalist",
                                         tablename = "cms_post",
                                         context = "event",
                                         default = default,
                                         filter = S3FieldSelector("series_id$name") == "Activity",
                                         icon = "icon-activity",
                                         layer = "Activities",
                                         # provided by Catalogue Layer
                                         #marker = "activity",
                                         list_layout = render_posts,
                                         )
                reports_widget = dict(label = "Reports",
                                      title_create = "Add New Report",
                                      type = "datalist",
                                      tablename = "cms_post",
                                      context = "event",
                                      default = default,
                                      filter = S3FieldSelector("series_id$name") == "Report",
                                      icon = "icon-report",
                                      layer = "Reports",
                                      # provided by Catalogue Layer
                                      #marker = "report",
                                      list_layout = render_posts,
                                      )
                #comments_widget = dict(label = "Comments",
                #                       type = "comments",
                #                       icon = "icon-comments-alt",
                #                       colspan = 2,
                #                       )
                record = r.record
                ttable = db.event_event_type
                event_type = db(ttable.id == record.event_type_id).select(ttable.name,
                                                                          limitby=(0, 1),
                                                                          ).first().name
                s3db.configure("event_event",
                               profile_header = DIV(A(IMG(_class="media-object",
                                                          _src=URL(c="static",
                                                                   f="themes",
                                                                   args=["DRMP", "img",
                                                                         "%s.png" % event_type]),
                                                          ),
                                                      _class="pull-left",
                                                      #_href=event_url,
                                                      ),
                                                    H2(record.name),
                                                    #P(record.comments),
                                                    _class="profile_header",
                                                    ),
                               profile_widgets = [alerts_widget,
                                                  map_widget,
                                                  incidents_widget,
                                                  assessments_widget,
                                                  activities_widget,
                                                  reports_widget,
                                                  #comments_widget,
                                                  ])

            # Include a Location inline
            location_field = s3db.event_event_location.location_id
            # Don't label a single field InlineComponent
            location_field.label = ""
            represent = S3Represent(lookup="gis_location")
            location_field.represent = represent
            # L1s only
            location_field.requires = IS_NULL_OR(
                                        IS_ONE_OF(db, "gis_location.id",
                                                  represent,
                                                  sort = True,
                                                  filterby = "level",
                                                  filter_opts = ["L1"]
                                                  )
                                        )
            # Don't add new Locations here
            location_field.comment = None
            # Simple dropdown
            location_field.widget = None

            crud_form = S3SQLCustomForm(
                    "name",
                    "event_type_id",
                    "exercise",
                    "zero_hour",
                    "closed",
                    S3SQLInlineComponent(
                        "event_location",
                        label = T("Location"),
                        multiple = False,
                        fields = ["location_id"],
                    ),
                    "comments",
                )
            
            s3db.configure("event_event",
                           create_next = URL(c="event", f="event",
                                             args=["[id]", "profile"]),
                           crud_form = crud_form,
                           # We want the Create form to be in a modal, not inline, for consistency
                           listadd = False,
                           list_layout = render_events,
                           )

            ADD_EVENT = T("New Disaster")
            s3.crud_strings["event_event"] = Storage(
                title_create = ADD_EVENT,
                title_display = T("Disaster Details"),
                title_list = T("Disasters"),
                title_update = T("Edit Disaster"),
                title_search = T("Search Disasters"),
                subtitle_create = T("Add New Disaster"),
                label_list_button = T("List Disasters"),
                label_create_button = ADD_EVENT,
                label_delete_button = T("Delete Disaster"),
                msg_record_created = T("Disaster added"),
                msg_record_modified = T("Disaster updated"),
                msg_record_deleted = T("Disaster deleted"),
                msg_list_empty = T("No Disasters currently registered"))

        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive and \
           current.auth.s3_has_permission("create", r.table):
            # Insert a Button to Create New in Modal
            output["showadd_btn"] = A(I(_class="icon icon-plus-sign big-add"),
                                      _href=URL(c="event", f="event",
                                                args=["create.popup"],
                                                vars={"refresh":"datalist"}),
                                      _class="btn btn-primary s3_modal",
                                      _role="button",
                                      _title=T("Add New Disaster"),
                                      )

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_event_event = customize_event_event

# -----------------------------------------------------------------------------
def customize_gis_location(**attr):
    """
        Customize gis_location controller
        - Profile Page
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        if r.interactive:
            s3db = current.s3db
            table = s3db.gis_location
            if r.method == "datalist":
                # Just show L1s (Districts)
                s3.filter = (table.level == "L1")
                # Default 5 triggers an AJAX call, we should load all by default
                s3.dl_pagelength = 13

                list_fields = ["name",
                               "level",
                               "L1",
                               "L2",
                               "L3",
                               ]
                s3db.configure("gis_location",
                               list_fields = list_fields,
                               list_layout = render_locations,
                               )

            elif r.method == "profile":
        
                # Customise tables used by widgets
                customize_cms_post_fields()
                customize_org_resource_fields("profile")
                customize_project_project_fields()

                # gis_location table (Sub-Locations)
                table.parent.represent = location_represent

                list_fields = ["name",
                               "id",
                               ]

                # Represent used in rendering
                current.auth.settings.table_user.organisation_id.represent = s3db.org_organisation_represent

                location = r.record
                default = "~.(location)=%s" % location.id
                map_widget = dict(label = "Map",
                                  type = "map",
                                  context = "location",
                                  icon = "icon-map",
                                  height = 383,
                                  width = 568,
                                  bbox = {"lat_max" : location.lat_max,
                                          "lon_max" : location.lon_max,
                                          "lat_min" : location.lat_min,
                                          "lon_min" : location.lon_min
                                          },
                                  )
                #locations_widget = dict(label = "Locations",
                #                        insert = False,
                #                        #title_create = "Add New Location",
                #                        type = "datalist",
                #                        tablename = "gis_location",
                #                        context = "location",
                #                        icon = "icon-globe",
                #                        # @ToDo: Show as Polygons?
                #                        show_on_map = False,
                #                        list_layout = render_locations_profile,
                #                        )
                resources_widget = dict(label = "Resources",
                                        title_create = "Add New Resource",
                                        type = "datalist",
                                        tablename = "org_resource",
                                        context = "location",
                                        default = default,
                                        icon = "icon-resource",
                                        show_on_map = False, # No Marker yet & only show at L1-level anyway
                                        list_layout = render_resources,
                                        )
                incidents_widget = dict(label = "Incidents",
                                        title_create = "Add New Incident",
                                        type = "datalist",
                                        tablename = "cms_post",
                                        context = "location",
                                        default = default,
                                        filter = (S3FieldSelector("series_id$name") == "Incident") & (S3FieldSelector("expired") == False),
                                        icon = "icon-incident",
                                        layer = "Incidents",
                                        # provided by Catalogue Layer
                                        #marker = "incident",
                                        list_layout = render_posts,
                                        )
                reports_widget = dict(label = "Reports",
                                      title_create = "Add New Report",
                                      type = "datalist",
                                      tablename = "cms_post",
                                      context = "location",
                                      default = default,
                                      filter = S3FieldSelector("series_id$name") == "Report",
                                      icon = "icon-report",
                                      layer = "Reports",
                                      # provided by Catalogue Layer
                                      #marker = "report",
                                      list_layout = render_posts,
                                      )
                projects_widget = dict(label = "Projects",
                                       title_create = "Add New Project",
                                       type = "datalist",
                                       tablename = "project_project",
                                       context = "location",
                                       default = default,
                                       icon = "icon-project",
                                       show_on_map = False, # No Marker yet & only show at L1-level anyway
                                       list_layout = render_projects,
                                       )
                activities_widget = dict(label = "Activities",
                                         title_create = "Add New Activity",
                                         type = "datalist",
                                         tablename = "cms_post",
                                         context = "location",
                                         default = default,
                                         filter = S3FieldSelector("series_id$name") == "Activity",
                                         icon = "icon-activity",
                                         layer = "Activities",
                                         # provided by Catalogue Layer
                                         #marker = "activity",
                                         list_layout = render_posts,
                                         )
                name = location.name
                s3db.configure("gis_location",
                               list_fields = list_fields,
                               profile_header = DIV(A(IMG(_class="media-object",
                                                          _src=URL(c="static",
                                                                   f="themes",
                                                                   args=["DRMP", "img",
                                                                         "%s.png" % s3_unicode(name)]),
                                                          ),
                                                      _class="pull-left",
                                                      #_href=location_url,
                                                      ),
                                                    H2(name),
                                                    _class="profile_header",
                                                    ),
                               profile_widgets = [#locations_widget,
                                                  resources_widget,
                                                  map_widget,
                                                  incidents_widget,
                                                  reports_widget,
                                                  projects_widget,
                                                  activities_widget,
                                                  ],
                               )

        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        return True
    s3.prep = custom_prep

    return attr

settings.ui.customize_gis_location = customize_gis_location

# -----------------------------------------------------------------------------
def customize_hrm_human_resource_fields():
    """
        Customize hrm_human_resource for Profile widgets and 'more' popups
    """

    s3db = current.s3db
    table = s3db.hrm_human_resource
    table.site_id.represent = S3Represent(lookup="org_site")
    s3db.org_site.location_id.represent = location_represent
    #table.modified_by.represent = s3_auth_user_represent_name
    table.modified_on.represent = datetime_represent

    list_fields = ["person_id",
                   "person_id$pe_id",
                   "organisation_id",
                   "site_id$location_id",
                   "site_id$location_id$addr_street",
                   "job_title_id",
                   "email.value",
                   "phone.value",
                   #"modified_by",
                   "modified_on",
                   ]

    s3db.configure("hrm_human_resource",
                   list_fields = list_fields,
                   )

# -----------------------------------------------------------------------------
def customize_hrm_human_resource(**attr):
    """
        Customize hrm_human_resource controller
        - used for 'more' popups
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.method == "datalist":
            customize_hrm_human_resource_fields()
            current.s3db.configure("hrm_human_resource",
                                   # Don't include a Create form in 'More' popups
                                   listadd = False,
                                   list_layout = render_contacts,
                                   )

        return True
    s3.prep = custom_prep

    return attr

settings.ui.customize_hrm_human_resource = customize_hrm_human_resource

# -----------------------------------------------------------------------------
def customize_hrm_job_title(**attr):
    """
        Customize hrm_job_title controller
    """

    s3 = current.response.s3

    table = current.s3db.hrm_job_title
    
    # Configure fields
    field = table.organisation_id
    field.readable = field.writable = False
    field.default = None
    
    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive:
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="hrm", f="job_title",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="hrm", f="job_title",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="hrm", f="job_title",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if isinstance(output, dict):
                if "form" in output:
                    output["form"].add_class("hrm_job_title")
                elif "item" in output and hasattr(output["item"], "add_class"):
                    output["item"].add_class("hrm_job_title")

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_hrm_job_title = customize_hrm_job_title

# -----------------------------------------------------------------------------
def customize_org_office_fields():
    """
        Customize org_office for Profile widgets and 'more' popups
    """

    s3db = current.s3db
    table = s3db.org_office
    table.location_id.represent = location_represent
    table.modified_by.represent = s3_auth_user_represent_name
    table.modified_on.represent = datetime_represent

    list_fields = ["name",
                   "organisation_id",
                   "office_type_id",
                   "location_id",
                   "location_id$addr_street",
                   "modified_by",
                   "modified_on",
                   "organisation_id$logo",
                   ]

    s3db.configure("org_office",
                   list_fields = list_fields,
                   )

# -----------------------------------------------------------------------------
def customize_org_office(**attr):
    """
        Customize org_office controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.org_office
    
    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.method == "datalist":
            customize_org_office_fields()
            s3db.configure("org_office",
                           # Don't include a Create form in 'More' popups
                           listadd = False,
                           list_layout = render_offices,
                           )

        elif r.interactive or r.representation == "aadata":
            # Configure fields
            table.code.readable = table.code.writable = False
            #table.office_type_id.readable = table.office_type_id.writable = False
            table.phone1.readable = table.phone1.writable = False
            table.phone2.readable = table.phone2.writable = False
            table.email.readable = table.email.writable = False
            table.fax.readable = table.fax.writable = False
            location_field = table.location_id

            # Filter from a Profile page?
            # If so, then default the fields we know
            get_vars = current.request.get_vars
            location_id = get_vars.get("~.(location)", None)
            organisation_id = get_vars.get("~.(organisation)", None)
            if organisation_id:
                org_field = table.organisation_id
                org_field.default = organisation_id
                org_field.readable = org_field.writable = False
            if location_id:
                location_field.default = location_id
                location_field.readable = location_field.writable = False
            else:
                # Don't add new Locations here
                location_field.comment = None
                # L1s only
                location_field.requires = IS_LOCATION_SELECTOR2(levels=["L1"])
                location_field.widget = S3LocationSelectorWidget2(levels=["L1"],
                                                                  show_address=True,
                                                                  show_map=False)
            s3.cancel = True

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive:
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="org", f="office",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="org", f="office",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="org", f="office",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if isinstance(output, dict):
                if "form" in output:
                    output["form"].add_class("org_office")
                elif "item" in output and hasattr(output["item"], "add_class"):
                    output["item"].add_class("org_office")

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_org_office = customize_org_office

# -----------------------------------------------------------------------------
def customize_org_organisation(**attr):
    """
        Customize org_organisation controller
        - Profile Page
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive:

            list_fields = ["id",
                           "name",
                           "logo",
                           "phone",
                           ]

            s3db = current.s3db
            if r.method == "profile":
                # Customise tables used by widgets
                customize_cms_post_fields()
                customize_hrm_human_resource_fields()
                customize_org_office_fields()
                customize_org_resource_fields("profile")
                customize_project_project_fields()

                contacts_widget = dict(label = "Contacts",
                                       title_create = "Add New Contact",
                                       type = "datalist",
                                       tablename = "hrm_human_resource",
                                       context = "organisation",
                                       create_controller = "pr",
                                       create_function = "person",
                                       icon = "icon-contact",
                                       show_on_map = False, # Since they will show within Offices
                                       list_layout = render_contacts,
                                       )
                map_widget = dict(label = "Map",
                                  type = "map",
                                  context = "organisation",
                                  icon = "icon-map",
                                  height = 383,
                                  width = 568,
                                  )
                offices_widget = dict(label = "Offices",
                                      title_create = "Add New Office",
                                      type = "datalist",
                                      tablename = "org_office",
                                      context = "organisation",
                                      icon = "icon-home",
                                      layer = "Offices",
                                      # provided by Catalogue Layer
                                      #marker = "office",
                                      list_layout = render_offices,
                                      )
                resources_widget = dict(label = "Resources",
                                        title_create = "Add New Resource",
                                        type = "datalist",
                                        tablename = "org_resource",
                                        context = "organisation",
                                        icon = "icon-resource",
                                        show_on_map = False, # No Marker yet & only show at L1-level anyway
                                        list_layout = render_resources,
                                        )
                projects_widget = dict(label = "Projects",
                                       title_create = "Add New Project",
                                       type = "datalist",
                                       tablename = "project_project",
                                       context = "organisation",
                                       icon = "icon-project",
                                       show_on_map = False, # No Marker yet & only show at L1-level anyway
                                       list_layout = render_projects,
                                       )
                activities_widget = dict(label = "Activities",
                                         title_create = "Add New Activity",
                                         type = "datalist",
                                         tablename = "cms_post",
                                         context = "organisation",
                                         filter = S3FieldSelector("series_id$name") == "Activity",
                                         icon = "icon-activity",
                                         layer = "Activities",
                                         # provided by Catalogue Layer
                                         #marker = "activity",
                                         list_layout = render_posts,
                                         )
                reports_widget = dict(label = "Reports",
                                      title_create = "Add New Report",
                                      type = "datalist",
                                      tablename = "cms_post",
                                      context = "organisation",
                                      filter = S3FieldSelector("series_id$name") == "Report",
                                      icon = "icon-report",
                                      layer = "Reports",
                                      # provided by Catalogue Layer
                                      #marker = "report",
                                      list_layout = render_posts,
                                      )
                assessments_widget = dict(label = "Assessments",
                                          title_create = "Add New Assessment",
                                          type = "datalist",
                                          tablename = "cms_post",
                                          context = "organisation",
                                          filter = S3FieldSelector("series_id$name") == "Assessment",
                                          icon = "icon-assessment",
                                          layer = "Assessments",
                                          # provided by Catalogue Layer
                                          #marker = "assessment",
                                          list_layout = render_posts,
                                          )
                record = r.record
                s3db.configure("org_organisation",
                               profile_header = DIV(A(IMG(_class="media-object",
                                                          _src=URL(c="default", f="download",
                                                                   args=[record.logo]),
                                                          ),
                                                      _class="pull-left",
                                                      #_href=org_url,
                                                      ),
                                                    H2(record.name),
                                                    _class="profile_header",
                                                    ),
                               profile_widgets = [contacts_widget,
                                                  map_widget,
                                                  offices_widget,
                                                  resources_widget,
                                                  projects_widget,
                                                  activities_widget,
                                                  reports_widget,
                                                  assessments_widget,
                                                  ]
                               )
            elif r.method == "datalist":
                # Stakeholder selection page
                # 2-column datalist, 6 rows per page
                s3.dl_pagelength = 12
                s3.dl_rowsize = 2

                # Add a component of just National offices for the Org address
                ottable = s3db.org_office_type
                query = (ottable.name == "National")
                national = current.db(query).select(ottable.id,
                                                    limitby=(0, 1)
                                                    ).first().id
                s3db.add_component("org_office",
                                   org_organisation=dict(name="nat_office",
                                                         joinby="organisation_id",
                                                         filterby="office_type_id",
                                                         filterfor=[national],
                                                         ))
                list_fields.append("nat_office.location_id$addr_street")

            # Represent used in rendering
            current.auth.settings.table_user.organisation_id.represent = s3db.org_organisation_represent

            # Load normal Model
            table = s3db.org_organisation

            # Hide fields
            table.organisation_type_id.readable = table.organisation_type_id.writable = False
            table.multi_sector_id.readable = table.multi_sector_id.writable = False
            table.region.readable = table.region.writable = False
            table.country.readable = table.country.writable = False
            table.year.readable = table.year.writable = False
            table.twitter.readable = table.twitter.writable = False
            table.donation_phone.readable = table.donation_phone.writable = False
            
            # Return to List view after create/update/delete (unless done via Modal)
            url_next = URL(c="org", f="organisation", args="datalist")

            s3db.configure("org_organisation",
                           create_next = url_next,
                           delete_next = url_next,
                           update_next = url_next,
                           # We want the Create form to be in a modal, not inline, for consistency
                           listadd = False,
                           list_fields = list_fields,
                           list_layout = render_organisations,
                           )

            ADD_ORGANISATION = T("New Stakeholder")
            s3.crud_strings["org_organisation"] = Storage(
                title_create = ADD_ORGANISATION,
                title_display = T("Stakeholder Details"),
                title_list = T("Stakeholders"),
                title_update = T("Edit Stakeholder"),
                title_search = T("Search Stakeholders"),
                subtitle_create = T("Add New Stakeholder"),
                label_list_button = T("List Stakeholders"),
                label_create_button = ADD_ORGANISATION,
                label_delete_button = T("Delete Stakeholder"),
                msg_record_created = T("Stakeholder added"),
                msg_record_modified = T("Stakeholder updated"),
                msg_record_deleted = T("Stakeholder deleted"),
                msg_list_empty = T("No Stakeholders currently registered"))

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive and \
           current.auth.s3_has_permission("create", r.table):
            # Insert a Button to Create New in Modal
            output["showadd_btn"] = A(I(_class="icon icon-plus-sign big-add"),
                                      _href=URL(c="org", f="organisation",
                                                args=["create.popup"],
                                                vars={"refresh":"datalist"}),
                                      _class="btn btn-primary s3_modal",
                                      _role="button",
                                      _title=T("Add New Organization"),
                                      )

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_org_organisation = customize_org_organisation

# -----------------------------------------------------------------------------
def customize_org_resource_fields(method):
    """
        Customize org_resource fields for Profile widgets and 'more' popups
    """

    s3db = current.s3db

    table = s3db.org_resource
    table.location_id.represent = location_represent

    list_fields = ["organisation_id",
                   "location_id",
                   "parameter_id",
                   "value",
                   "comments",
                   ]
    if method in ("datalist", "profile"):
        table.modified_by.represent = s3_auth_user_represent_name
        table.modified_on.represent = datetime_represent
        append = list_fields.append
        append("modified_by")
        append("modified_on")
        append("organisation_id$logo")

    s3db.configure("org_resource",
                   list_fields = list_fields,
                   )

# -----------------------------------------------------------------------------
def customize_org_resource(**attr):
    """
        Customize org_resource controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.org_resource

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive or r.representation == "aadata":
            customize_org_resource_fields(r.method)
    
            # Configure fields
            #table.site_id.readable = table.site_id.readable = False
            location_field = table.location_id
            location_field.label = T("District")

            # Filter from a Profile page?
            # If so, then default the fields we know
            get_vars = current.request.get_vars
            location_id = get_vars.get("~.(location)", None)
            organisation_id = get_vars.get("~.(organisation)", None)
            if organisation_id:
                org_field = table.organisation_id
                org_field.default = organisation_id
                org_field.readable = org_field.writable = False
            if location_id:
                location_field.default = location_id
                location_field.readable = location_field.writable = False
            else:
                # L1s only
                location_field.requires = IS_ONE_OF(current.db, "gis_location.id",
                                                    S3Represent(lookup="gis_location"),
                                                    sort = True,
                                                    filterby = "level",
                                                    filter_opts = ["L1"]
                                                    )
                # Don't add new Locations here
                location_field.comment = None
                # Simple dropdown
                location_field.widget = None

            # Return to List view after create/update/delete (unless done via Modal)
            url_next = URL(c="org", f="resource")

            s3db.configure("org_resource",
                           create_next = url_next,
                           delete_next = url_next,
                           update_next = url_next,
                           # Don't include a Create form in 'More' popups
                           listadd = False if r.method=="datalist" else True,
                           list_layout = render_resources,
                           )

            s3.cancel = True

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive:
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="org", f="resource",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="org", f="resource",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="org", f="resource",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if isinstance(output, dict):
                if "form" in output:
                    output["form"].add_class("org_resource")
                elif "item" in output and hasattr(output["item"], "add_class"):
                    output["item"].add_class("org_resource")

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_org_resource = customize_org_resource

# -----------------------------------------------------------------------------
def customize_pr_person(**attr):
    """
        Customize pr_person controller
    """

    s3db = current.s3db
    s3 = current.response.s3

    tablename = "pr_person"
    table = s3db.pr_person

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.method == "validate":
            # Can't validate image without the file
            image_field = s3db.pr_image.image
            image_field.requires = None

        if r.interactive or r.representation == "aadata":
            # CRUD Strings
            ADD_CONTACT = T("Add New Contact")
            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Contact"),
                title_display = T("Contact Details"),
                title_list = T("Contacts"),
                title_update = T("Edit Contact Details"),
                title_search = T("Search Contacts"),
                subtitle_create = ADD_CONTACT,
                label_list_button = T("List Contacts"),
                label_create_button = ADD_CONTACT,
                label_delete_button = T("Delete Contact"),
                msg_record_created = T("Contact added"),
                msg_record_modified = T("Contact details updated"),
                msg_record_deleted = T("Contact deleted"),
                msg_list_empty = T("No Contacts currently registered"))

            MOBILE = settings.get_ui_label_mobile_phone()
            EMAIL = T("Email")

            htable = s3db.hrm_human_resource
            htable.organisation_id.widget = None
            site_field = htable.site_id
            represent = S3Represent(lookup="org_site")
            site_field.represent = represent
            site_field.requires = IS_ONE_OF(current.db, "org_site.site_id",
                                            represent,
                                            orderby = "org_site.name")
            site_field.comment = S3AddResourceLink(c="org", f="office",
                                                   vars={"child": "site_id"},
                                                   label=T("Add New Office"),
                                                   title=T("Office"),
                                                   tooltip=T("If you don't see the Office in the list, you can add a new one by clicking link 'Add New Office'."))

            # Best to have no labels when only 1 field in the row
            s3db.pr_contact.value.label = ""
            image_field = s3db.pr_image.image
            image_field.label = ""
            # ImageCrop widget doesn't currently work within an Inline Form
            image_field.widget = None

            hr_fields = ["organisation_id",
                         "job_title_id",
                         "site_id",
                         ]
            if r.method in ("create", "update"):
                # Context from a Profile page?"
                organisation_id = current.request.get_vars.get("(organisation)", None)
                if organisation_id:
                    field = s3db.hrm_human_resource.organisation_id
                    field.default = organisation_id
                    field.readable = field.writable = False
                    hr_fields.remove("organisation_id")

            crud_form = S3SQLCustomForm(
                    "first_name",
                    #"middle_name",
                    "last_name",
                    S3SQLInlineComponent(
                        "human_resource",
                        name = "human_resource",
                        label = "",
                        multiple = False,
                        fields = hr_fields,
                        filterby = dict(field = "contact_method",
                                        options = "SMS"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "contact",
                        name = "phone",
                        label = MOBILE,
                        multiple = False,
                        fields = ["value"],
                        filterby = dict(field = "contact_method",
                                        options = "SMS"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "contact",
                        name = "email",
                        label = EMAIL,
                        multiple = False,
                        fields = ["value"],
                        filterby = dict(field = "contact_method",
                                        options = "EMAIL"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "image",
                        name = "image",
                        label = T("Photo"),
                        multiple = False,
                        fields = ["image"],
                    ),
                )

            list_fields = [(current.messages.ORGANISATION, "human_resource.organisation_id"),
                           "first_name",
                           #"middle_name",
                           "last_name",
                           (T("Job Title"), "human_resource.job_title_id"),
                           (T("Office"), "human_resource.site_id"),
                           (MOBILE, "phone.value"),
                           (EMAIL, "email.value"),
                           ]

            # Return to List view after create/update/delete (unless done via Modal)
            url_next = URL(c="pr", f="person")

            s3db.configure(tablename,
                           create_next = url_next,
                           delete_next = url_next,
                           update_next = url_next,
                           crud_form = crud_form,
                           list_fields = list_fields,
                           # Don't include a Create form in 'More' popups
                           listadd = False if r.method=="datalist" else True,
                           list_layout = render_contacts,
                           )

            # Move fields to their desired Locations
            # Disabled as breaks submission of inline_component
            #i18n = []
            #iappend = i18n.append
            #iappend('''i18n.office="%s"''' % T("Office"))
            #iappend('''i18n.organisation="%s"''' % T("Organization"))
            #iappend('''i18n.job_title="%s"''' % T("Job Title"))
            #i18n = '''\n'''.join(i18n)
            #s3.js_global.append(i18n)
            #s3.scripts.append('/%s/static/themes/DRMP/js/contacts.js' % current.request.application)

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive:
            output["rheader"] = ""
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="pr", f="person",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="pr", f="person",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="pr", f="person",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if isinstance(output, dict):
                if "form" in output:
                    output["form"].add_class("pr_person")
                elif "item" in output and hasattr(output["item"], "add_class"):
                    output["item"].add_class("pr_person")

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_pr_person = customize_pr_person

# -----------------------------------------------------------------------------
def customize_project_project_fields():
    """
        Customize project_project fields for Profile widgets and 'more' popups
    """

    format = "%d/%m/%y"
    date_represent = lambda d: S3DateTime.date_represent(d, format=format)

    s3db = current.s3db

    s3db.project_location.location_id.represent = location_represent
    table = s3db.project_project
    table.start_date.represent = date_represent
    table.end_date.represent = date_represent
    table.modified_by.represent = s3_auth_user_represent_name
    table.modified_on.represent = datetime_represent

    list_fields = ["name",
                   "organisation_id",
                   "location.location_id",
                   "organisation_id$logo",
                   "start_date",
                   "end_date",
                   "human_resource_id",
                   "budget",
                   "partner.organisation_id",
                   "donor.organisation_id",
                   "donor.amount",
                   "donor.currency",
                   "modified_by",
                   "modified_on",
                   "document.file",
                   ]

    s3db.configure("project_project",
                   list_fields = list_fields,
                   )

# -----------------------------------------------------------------------------
def customize_project_project(**attr):
    """
        Customize project_project controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.project_project

    # Remove rheader
    attr["rheader"] = None

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.method == "datalist":
            customize_project_project_fields()
            s3db.configure("project_project",
                           # Don't include a Create form in 'More' popups
                           listadd = False,
                           list_layout = render_projects,
                           )
        elif r.interactive  or r.representation == "aadata":
            # Configure fields 
            table.human_resource_id.label = T("Focal Person")
            table.budget.label = "%s (USD)" % T("Budget")
            # Better in column label & otherwise this construction loses thousands separators
            #table.budget.represent = lambda value: "%d USD" % value

            # Filter from a Profile page?
            # If so, then default the fields we know
            get_vars = current.request.get_vars
            organisation_id = get_vars.get("~.(organisation)", None)
            if organisation_id:
                org_field = table.organisation_id
                org_field.default = organisation_id
                org_field.readable = org_field.writable = False
                crud_form = S3SQLCustomForm(
                    "name",
                    S3SQLInlineComponent(
                        "location",
                        label = T("Districts"),
                        fields = ["location_id"],
                        orderby = "location_id$name",
                        render_list = True
                    ),
                    "human_resource_id",
                    "start_date",
                    "end_date",
                    # Partner Orgs
                    S3SQLInlineComponent(
                        "organisation",
                        name = "partner",
                        label = T("Partner Organisations"),
                        fields = ["organisation_id",
                                  ],
                        filterby = dict(field = "role",
                                        options = "2"
                                        )
                    ),
                    # Donors
                    S3SQLInlineComponent(
                        "organisation",
                        name = "donor",
                        label = T("Donor(s)"),
                        fields = ["organisation_id", "amount", "currency"],
                        filterby = dict(field = "role",
                                        options = "3"
                                        )
                    ),
                    "budget",
                    # Files
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments"
                                  ],
                    ),
                    "comments",
                )
            else:
                location_field = s3db.project_location.location_id
                location_id = get_vars.get("~.(location)", None)
                if location_id:
                    # Default to this Location, but allow selection of others
                    location_field.default = location_id
                location_field.label = ""
                location_field.represent = S3Represent(lookup="gis_location")
                # Project Locations must be districts
                location_field.requires = IS_ONE_OF(current.db, "gis_location.id",
                                                    S3Represent(lookup="gis_location"),
                                                    sort = True,
                                                    filterby = "level",
                                                    filter_opts = ["L1"]
                                                    )
                # Don't add new Locations here
                location_field.comment = None
                # Simple dropdown
                location_field.widget = None
                
                crud_form = S3SQLCustomForm(
                    "name",
                    "organisation_id",
                    S3SQLInlineComponent(
                        "location",
                        label = T("Districts"),
                        fields = ["location_id"],
                        orderby = "location_id$name",
                        render_list = True
                    ),
                    "human_resource_id",
                    "start_date",
                    "end_date",
                    # Partner Orgs
                    S3SQLInlineComponent(
                        "organisation",
                        name = "partner",
                        label = T("Partner Organisations"),
                        fields = ["organisation_id",
                                  ],
                        filterby = dict(field = "role",
                                        options = "2"
                                        )
                    ),
                    # Donors
                    S3SQLInlineComponent(
                        "organisation",
                        name = "donor",
                        label = T("Donor(s)"),
                        fields = ["organisation_id", "amount", "currency"],
                        filterby = dict(field = "role",
                                        options = "3"
                                        )
                    ),
                    "budget",
                    # Files
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments"
                                  ],
                    ),
                    "comments",
                )

            list_fields = ["name",
                           "organisation_id",
                           "human_resource_id",
                           "start_date",
                           "end_date",
                           "budget",
                           ]

            # Return to List view after create/update/delete (unless done via Modal)
            url_next = URL(c="project", f="project")

            s3db.configure("project_project",
                           create_next = url_next,
                           delete_next = url_next,
                           update_next = url_next,
                           crud_form = crud_form,
                           list_fields = list_fields,
                           )

            s3.cancel = True

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive:
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="project", f="project",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="project", f="project",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="project", f="project",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if isinstance(output, dict):
                if "form" in output:
                    output["form"].add_class("project_project")
                elif "item" in output and hasattr(output["item"], "add_class"):
                    output["item"].add_class("project_project")

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_project_project = customize_project_project

# =============================================================================
# Template Modules
# Comment/uncomment modules here to disable/enable them
settings.modules = OrderedDict([
    # Core modules which shouldn't be disabled
    ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
    ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
    ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
    ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
    ("sync", Storage(
            name_nice = T("Synchronization"),
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
    ("translate", Storage(
            name_nice = T("Translation Functionality"),
            #description = "Selective translation of strings based on module.",
            module_type = None,
        )),
    ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 1,     # 1st item in the menu
        )),
    ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = None
        )),
    ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = None
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = None,
        )),
    ("cms", Storage(
            name_nice = T("Content Management"),
            restricted = True,
            module_type = None,
        )),
    ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = None,
        )),
    ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
    ("event", Storage(
            name_nice = T("Disasters"),
            #description = "Events",
            restricted = True,
            module_type = None
        )),
    ("project", Storage(
            name_nice = T("Projects"),
            restricted = True,
            module_type = None
        )),
    ("stats", Storage(
            name_nice = T("Statistics"),
            restricted = True,
            module_type = None
        )),
#    ("asset", Storage(
#            name_nice = T("Assets"),
#            restricted = True,
#            module_type = None
#        )),
#    ("supply", Storage(
#            name_nice = "Supply",
#            restricted = True,
#            module_type = None
#        )),
])
