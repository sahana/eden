# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from datetime import timedelta

from gluon import current, Field, URL
from gluon.html import *
from gluon.storage import Storage

from s3 import S3Represent, S3DateTime, s3_avatar_represent

T = current.T
s3 = current.response.s3
settings = current.deployment_settings

datetime_represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)

"""
    Template settings for IFRC MENA 4W Portal
"""

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ("Syria", "default/users")

settings.base.system_name = T("IFRC MENA 4W Portal")
settings.base.system_name_short = T("IFRC MENA 4W")

# =============================================================================
# System Settings
# -----------------------------------------------------------------------------
# Authorization Settings
# Should users be allowed to register themselves?
settings.security.self_registration = False
settings.auth.registration_requires_approval = True
settings.auth.registration_requires_verification = False
#settings.auth.registration_requests_organisation = True
#settings.auth.registration_organisation_required = True
settings.auth.registration_requests_site = False

# Approval emails get sent to all admins
settings.mail.approver = "ADMIN"

settings.auth.registration_link_user_to = {"staff": T("Staff")}
settings.auth.registration_link_user_to_default = ["staff"]
#settings.auth.registration_roles = {"organisation_id": ["USER"],
#                                    }

# Terms of Service to be able to Register on the system
# uses <template>/views/tos.html
#settings.auth.terms_of_service = True

settings.auth.show_utc_offset = False

settings.auth.show_link = False

# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 3 # Controller ACLs
settings.security.map = True

# Owner Entity
settings.auth.person_realm_human_resource_site_then_org = False

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "Syria"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
settings.gis.map_height = 400
#settings.gis.map_width = 854
# Use a non-default fillColor for Clustered points
settings.gis.cluster_fill = "ee3224"
# Disable the label for clustered points
settings.gis.cluster_label = False
# Use a non-default strokeColor for Clustered points
settings.gis.cluster_stroke = "7a1600"
# Use a non-default fillColor for Selected points
settings.gis.select_fill = "ddbe7e"
# Use a non-default strokeColor for Selected points
settings.gis.select_stroke = "e5b53b"

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    #("ar", "العربية"), # Needed to import Arabic placenames
    ("en", "English"),
])
# Default Language
settings.L10n.default_language = "en"
# Default timezone for users
settings.L10n.utc_offset = "UTC +0200"
# Unsortable 'pretty' date format
settings.L10n.date_format = "%d %b %Y"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","

# Uncomment this to Translate CMS Series Names
# - we want this on when running s3translate but off in normal usage as we use the English names to lookup icons in render_posts
#settings.L10n.translate_cms_series = True
# Uncomment this to Translate Location Names
#settings.L10n.translate_gis_location = True

# Restrict the Location Selector to just certain countries
#settings.gis.countries = ("SY",)
settings.gis.countries = ("SY", "IQ", "LB", "TR", "JO") #, "EG", "DZ"

# Disable toolbar
settings.gis.toolbar = False
# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"

# -----------------------------------------------------------------------------
# Finance settings
settings.fin.currencies = {
    "CHF" : T("Swiss Francs"),
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
# Uncomment to restrict the export formats available
#settings.ui.export_formats = ["xls"]

settings.ui.update_label = "Edit"

# -----------------------------------------------------------------------------
# Summary Pages
settings.ui.summary = [{"common": True,
                        "name": "common",
                        "label": "",
                        "widgets": [{"method": "map", "ajax_init": True},
                                    {"method": "report", "ajax_init": True}],
                        },
                       #{"name": "map",
                       # "label": "Map",
                       # "widgets": [{"method": "map", "ajax_init": True}],
                       # },
                       #{"name": "charts",
                       # "label": "Charts",
                       # "widgets": [{"method": "report", "ajax_init": True}]
                       # },
                       ]

settings.search.filter_manager = False

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
settings.hrm.teams = False

# Uncomment to hide fields in S3AddPersonWidget[2]
settings.pr.request_dob = False
settings.pr.request_gender = False

# -----------------------------------------------------------------------------
# Org
settings.org.site_label = "Office"

# -----------------------------------------------------------------------------
# Project
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True

# Uncomment this to link Activities to Projects
settings.project.projects = True

# Uncomment this to use Project Themes
settings.project.themes = False

# Links to Filtered Components for Donors & Partners
#settings.project.organisation_roles = {
#    1: T("Host National Society"),
#    2: T("Partner"),
#    3: T("Donor"),
#    #4: T("Customer"), # T("Beneficiary")?
#    #5: T("Supplier"),
#    9: T("Partner National Society"),
#}

# -----------------------------------------------------------------------------
# Notifications
# Template for the subject line in update notifications
#settings.msg.notify_subject = "$S %s" % T("Notification")
settings.msg.notify_subject = "$S Notification"

# -----------------------------------------------------------------------------
def currency_represent(v):
    """
        Custom Representation of Currencies
    """

    if v == "USD":
        return "$"
    elif v == "EUR":
        return "€"
    elif v == "GBP":
        return "£"
    else:
        # e.g. CHF
        return v

# -----------------------------------------------------------------------------
def render_contacts(list_id, item_id, resource, rfields, record):
    """
        Custom dataList item renderer for Contacts on the Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["hrm_human_resource.id"]
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
        vars = {"refresh": list_id,
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
def render_locations(list_id, item_id, resource, rfields, record):
    """
        Custom dataList item renderer for Locations on the Selection Page

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["gis_location.id"]
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
                               # vars={"refresh": list_id,
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

    # Build the icon, if it doesn't already exist
    filename = "%s.svg" % record_id
    import os
    filepath = os.path.join(current.request.folder, "static", "cache", "svg", filename)
    if not os.path.exists(filepath):
        gtable = db.gis_location
        loc = db(gtable.id == record_id).select(gtable.wkt,
                                                limitby=(0, 1)
                                                ).first()
        if loc:
            from s3.s3codecs.svg import S3SVG
            S3SVG.write_file(filename, loc.wkt)

    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static",
                                  f="cache",
                                  args=["svg", filename],
                                  )
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
                   DIV(P(T("Projects"),
                         SPAN(tally_projects,
                              _class="badge",
                              ),
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
def customise_gis_location_controller(**attr):
    """
        Customise gis_location controller
        - Profile Page, used as main Homepage for this template
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        if r.interactive:
            s3db = current.s3db
            table = s3db.gis_location

            if r.method == "datalist":
                # Country selection page
                s3.crud_strings["gis_location"].title_list = T("Countries")

                # 2-column datalist, 6 rows per page
                s3.dl_pagelength = 12
                s3.dl_rowsize = 2

                # Just show specific Countries
                s3.filter = (table.name.belongs("Syrian Arab Republic", "Jordan", "Iraq", "Lebanon", "Turkey"))
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
                #customise_cms_post_fields()
                #customise_project_project_fields()

                # gis_location table (Sub-Locations)
                table.parent.represent = s3db.gis_LocationRepresent(sep=" | ")

                list_fields = ["name",
                               "id",
                               ]

                location = r.record
                record_id = location.id
                default = "~.(location)=%s" % record_id
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
                #                        #label_create = "Create Location",
                #                        type = "datalist",
                #                        tablename = "gis_location",
                #                        context = "location",
                #                        icon = "icon-globe",
                #                        # @ToDo: Show as Polygons?
                #                        show_on_map = False,
                #                        list_layout = render_locations_profile,
                #                        )
                beneficiaries_widget = dict(label = "Beneficiaries",
                                            #label_create = "Add New Beneficiary",
                                            type = "report",
                                            tablename = "project_beneficiary",
                                            ajaxurl = URL(c="project",
                                                          f="beneficiary",
                                                          args="report.json",
                                                          ),
                                            context = "location",
                                            default = default,
                                            icon = "icon-contact",
                                            layer = "Beneficiaries",
                                            )
                distributions_widget = dict(label = "Distributions",
                                            #label_create = "Add New Distribution",
                                            type = "report",
                                            tablename = "supply_distribution",
                                            ajaxurl = URL(c="supply",
                                                          f="distribution",
                                                          args="report.json",
                                                          ),
                                            context = "location",
                                            default = default,
                                            icon = "icon-truck",
                                            layer = "Distributions",
                                            )

                profile_title = ""
                profile_header = DIV(A(IMG(_class="media-object",
                                           _src=URL(c="static",
                                                    f="themes",
                                                    args=["Syria", "img", "IFRC.png"],
                                                    ),
                                           _style="height:38px;width:65px",
                                           ),
                                       _class="pull-left",
                                       #_href=location_url,
                                       ),
                                     H2(settings.get_system_name()),
                                     _class="profile-header",
                                     )
                s3db.configure("gis_location",
                               list_fields = list_fields,
                               profile_title = profile_title,
                               profile_header = profile_header,
                               profile_widgets = [#locations_widget,
                                                  map_widget,
                                                  beneficiaries_widget,
                                                  distributions_widget,
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

settings.customise_gis_location_controller = customise_gis_location_controller
# -----------------------------------------------------------------------------
def customise_hrm_human_resource_fields():
    """
        Customise hrm_human_resource for Profile widgets and 'more' popups
    """

    s3db = current.s3db
    table = s3db.hrm_human_resource
    table.site_id.represent = S3Represent(lookup="org_site")
    s3db.org_site.location_id.represent = s3db.gis_LocationRepresent(sep=" | ")
    #from s3 import s3_auth_user_represent_name
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
def customise_hrm_human_resource_controller(**attr):
    """
        Customise hrm_human_resource controller
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
            customise_hrm_human_resource_fields()
            current.s3db.configure("hrm_human_resource",
                                   # Don't include a Create form in 'More' popups
                                   listadd = False,
                                   list_layout = render_contacts,
                                   )

        return True
    s3.prep = custom_prep

    return attr

settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

# -----------------------------------------------------------------------------
def customise_hrm_job_title_controller(**attr):

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
            db = current.db
            auth = current.auth
            has_permission = auth.s3_has_permission
            ownership_required = auth.permission.ownership_required
            s3_accessible_query = auth.s3_accessible_query
            if has_permission("update", table):
                action = dict(label=str(T("Edit")),
                              _class="action-btn",
                              url=URL(c="hrm", f="job_title",
                                      args=["[id]", "update"]),
                              )
                if ownership_required("update", table):
                    # Check which records can be updated
                    query = s3_accessible_query("update", table)
                    rows = db(query).select(table._id)
                    restrict = []
                    rappend = restrict.append
                    for row in rows:
                        row_id = row.get("id", None)
                        if row_id:
                            rappend(str(row_id))
                    action["restrict"] = restrict
                actions.append(action)
            if has_permission("delete", table):
                action = dict(label=str(T("Delete")),
                              _class="action-btn",
                              url=URL(c="hrm", f="job_title",
                                      args=["[id]", "delete"]),
                              )
                if ownership_required("delete", table):
                    # Check which records can be deleted
                    query = s3_accessible_query("delete", table)
                    rows = db(query).select(table._id)
                    restrict = []
                    rappend = restrict.append
                    for row in rows:
                        row_id = row.get("id", None)
                        if row_id:
                            rappend(str(row_id))
                    action["restrict"] = restrict
                actions.append(action)
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

settings.customise_hrm_job_title_controller = customise_hrm_job_title_controller

# -----------------------------------------------------------------------------
def customise_org_organisation_controller(**attr):
    """
        Customise org_organisation controller
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
                #customise_cms_post_fields()
                customise_hrm_human_resource_fields()
                #customise_org_office_fields()
                customise_project_project_fields()

                from s3 import FS
                contacts_widget = dict(label = "Contacts",
                                       label_create = "Create Contact",
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
                #offices_widget = dict(label = "Offices",
                #                      label_create = "Create Office",
                #                      type = "datalist",
                #                      tablename = "org_office",
                #                      context = "organisation",
                #                      icon = "icon-home",
                #                      layer = "Offices",
                #                      # provided by Catalogue Layer
                #                      #marker = "office",
                #                      list_layout = render_offices,
                #                      )
                projects_widget = dict(label = "Projects",
                                       label_create = "Create Project",
                                       type = "datalist",
                                       tablename = "project_project",
                                       context = "organisation",
                                       icon = "icon-project",
                                       show_on_map = False, # No Marker yet & only show at L1-level anyway
                                       #list_layout = render_projects,
                                       )
                reports_widget = dict(label = "Reports",
                                      label_create = "Create Report",
                                      type = "datalist",
                                      tablename = "cms_post",
                                      context = "organisation",
                                      filter = FS("series_id$name") == "Report",
                                      icon = "icon-report",
                                      layer = "Reports",
                                      # provided by Catalogue Layer
                                      #marker = "report",
                                      list_layout = render_profile_posts,
                                      )
                assessments_widget = dict(label = "Assessments",
                                          label_create = "Create Assessment",
                                          type = "datalist",
                                          tablename = "cms_post",
                                          context = "organisation",
                                          filter = FS("series_id$name") == "Assessment",
                                          icon = "icon-assessment",
                                          layer = "Assessments",
                                          # provided by Catalogue Layer
                                          #marker = "assessment",
                                          list_layout = render_profile_posts,
                                          )
                # @ToDo: Renderer
                #distributions_widget = dict(label = "Distributions",
                #                            label_create = "Create Distribution",
                #                            type = "datalist",
                #                            tablename = "supply_distribution",
                #                            context = "location",
                #                            default = default,
                #                            icon = "icon-resource",
                #                            list_layout = render_distributions,
                #                            )
                record = r.record
                s3db.configure("org_organisation",
                               profile_title = "%s : %s" % (s3.crud_strings["org_organisation"].title_list,
                                                            record.name),
                               profile_header = DIV(A(IMG(_class="media-object",
                                                          _src=URL(c="default", f="download",
                                                                   args=[record.logo]),
                                                          ),
                                                      _class="pull-left",
                                                      #_href=org_url,
                                                      ),
                                                    H2(record.name),
                                                    _class="profile-header",
                                                    ),
                               profile_widgets = [contacts_widget,
                                                  map_widget,
                                                  #offices_widget,
                                                  projects_widget,
                                                  #activities_widget,
                                                  reports_widget,
                                                  assessments_widget,
                                                  #distributions_widget,
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
                s3db.add_components("org_organisation",
                                    org_office={"name": "nat_office",
                                                "joinby": "organisation_id",
                                                "filterby": "office_type_id",
                                                "filterfor": [national],
                                               },
                                   )
                list_fields.append("nat_office.location_id$addr_street")

            # Represent used in rendering
            current.auth.settings.table_user.organisation_id.represent = s3db.org_organisation_represent

            # Load normal Model
            table = s3db.org_organisation

            # Hide fields
            field = s3db.org_organisation_organisation_type.organisation_type_id
            field.readable = field.writable = False
            table.region_id.readable = table.region_id.writable = False
            table.country.readable = table.country.writable = False
            table.year.readable = table.year.writable = False

            # Return to List view after create/update/delete (unless done via Modal)
            #url_next = URL(c="org", f="organisation", args="datalist")

            s3db.configure("org_organisation",
                           #create_next = url_next,
                           #delete_next = url_next,
                           #update_next = url_next,
                           list_fields = list_fields,
                           )

        return True
    s3.prep = custom_prep

    return attr

settings.customise_org_organisation_controller = customise_org_organisation_controller

# -----------------------------------------------------------------------------
def customise_pr_person_controller(**attr):

    s3db = current.s3db
    request = current.request
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
            if request.controller != "default":
                # CRUD Strings
                ADD_CONTACT = T("Create Contact")
                s3.crud_strings[tablename] = Storage(
                    label_create = T("Create Contact"),
                    title_display = T("Contact Details"),
                    title_list = T("Contact Directory"),
                    title_update = T("Edit Contact Details"),
                    label_list_button = T("List Contacts"),
                    label_delete_button = T("Delete Contact"),
                    msg_record_created = T("Contact added"),
                    msg_record_modified = T("Contact details updated"),
                    msg_record_deleted = T("Contact deleted"),
                    msg_list_empty = T("No Contacts currently registered"))

            MOBILE = settings.get_ui_label_mobile_phone()
            EMAIL = T("Email")

            from s3 import IS_ONE_OF

            htable = s3db.hrm_human_resource
            htable.organisation_id.widget = None
            site_field = htable.site_id
            represent = S3Represent(lookup="org_site")
            site_field.represent = represent
            site_field.requires = IS_ONE_OF(current.db, "org_site.site_id",
                                            represent,
                                            orderby = "org_site.name")

            from s3layouts import S3AddResourceLink
            site_field.comment = S3AddResourceLink(c="org", f="office",
                                                   vars={"child": "site_id"},
                                                   label=T("Create Office"),
                                                   title=T("Office"),
                                                   tooltip=T("If you don't see the Office in the list, you can add a new one by clicking link 'Create Office'."))

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
                organisation_id = request.get_vars.get("(organisation)", None)
                if organisation_id:
                    field = s3db.hrm_human_resource.organisation_id
                    field.default = organisation_id
                    field.readable = field.writable = False
                    hr_fields.remove("organisation_id")

            from s3 import S3SQLCustomForm, S3SQLInlineComponent
            s3_sql_custom_fields = [
                    "first_name",
                    #"middle_name",
                    "last_name",
                    S3SQLInlineComponent(
                        "human_resource",
                        name = "human_resource",
                        label = "",
                        multiple = False,
                        fields = hr_fields,
                    ),
                    S3SQLInlineComponent(
                        "image",
                        name = "image",
                        label = T("Photo"),
                        multiple = False,
                        fields = ["image"],
                        filterby = dict(field = "profile",
                                        options=[True]
                                        )
                    ),
                ]

            list_fields = [(current.messages.ORGANISATION, "human_resource.organisation_id"),
                           "first_name",
                           #"middle_name",
                           "last_name",
                           (T("Job Title"), "human_resource.job_title_id"),
                           (T("Office"), "human_resource.site_id"),
                           ]

            # Don't include Email/Phone for unauthenticated users
            if current.auth.is_logged_in():
                list_fields += [(MOBILE, "phone.value"),
                                (EMAIL, "email.value"),
                                ]
                s3_sql_custom_fields.insert(3,
                                            S3SQLInlineComponent(
                                            "contact",
                                            name = "phone",
                                            label = MOBILE,
                                            multiple = False,
                                            fields = ["value"],
                                            filterby = dict(field = "contact_method",
                                                            options = "SMS")),
                                            )
                s3_sql_custom_fields.insert(3,
                                            S3SQLInlineComponent(
                                            "contact",
                                            name = "email",
                                            label = EMAIL,
                                            multiple = False,
                                            fields = ["value"],
                                            filterby = dict(field = "contact_method",
                                                            options = "EMAIL")),
                                            )

            crud_form = S3SQLCustomForm(*s3_sql_custom_fields)

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
            #s3.scripts.append('/%s/static/themes/DRMP/js/contacts.js' % request.application)

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive and isinstance(output, dict):
            output["rheader"] = ""
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="pr", f="person",
                                    args=["[id]", "read"]))
                       ]
            # All users just get "Open"
            #db = current.db
            #auth = current.auth
            #has_permission = auth.s3_has_permission
            #ownership_required = auth.permission.ownership_required
            #s3_accessible_query = auth.s3_accessible_query
            #if has_permission("update", table):
            #    action = dict(label=str(T("Edit")),
            #                  _class="action-btn",
            #                  url=URL(c="pr", f="person",
            #                          args=["[id]", "update"]),
            #                  )
            #    if ownership_required("update", table):
            #        # Check which records can be updated
            #        query = s3_accessible_query("update", table)
            #        rows = db(query).select(table._id)
            #        restrict = []
            #        rappend = restrict.append
            #        for row in rows:
            #            row_id = row.get("id", None)
            #            if row_id:
            #                rappend(str(row_id))
            #        action["restrict"] = restrict
            #    actions.append(action)
            #if has_permission("delete", table):
            #    action = dict(label=str(T("Delete")),
            #                  _class="action-btn",
            #                  url=URL(c="pr", f="person",
            #                          args=["[id]", "delete"]),
            #                  )
            #    if ownership_required("delete", table):
            #        # Check which records can be deleted
            #        query = s3_accessible_query("delete", table)
            #        rows = db(query).select(table._id)
            #        restrict = []
            #        rappend = restrict.append
            #        for row in rows:
            #            row_id = row.get("id", None)
            #            if row_id:
            #                rappend(str(row_id))
            #        action["restrict"] = restrict
            #    actions.append(action)
            s3.actions = actions
            if "form" in output:
                output["form"].add_class("pr_person")
            elif "item" in output and hasattr(output["item"], "add_class"):
                output["item"].add_class("pr_person")

        return output
    s3.postp = custom_postp

    return attr

settings.customise_pr_person_controller = customise_pr_person_controller

# -----------------------------------------------------------------------------
def customise_project_activity_controller(**attr):
    """
        Customise project_activity controller

        This is the main page for this Template
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)

        s3db = current.s3db
        tablename = "project_activity"
        table = s3db[tablename]

        table.name.label = T("Activity")

        levels = ("L0", "L1", "L2", "L3")
        location_field = table.location_id
        location_field.represent = s3db.gis_LocationRepresent(sep=", ")

        #s3db.project_theme_activity.theme_id.label = T("Beneficiary Type")
        #s3db.project_beneficiary.parameter_id.label = T("Beneficiaries")
        s3db.supply_distribution.parameter_id.label = T("Distribution")

        list_fields = ["activity_organisation.organisation_id",
                       "location_id$L0",
                       "location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "sector_activity.sector_id",
                       "name",
                       "distribution.parameter_id",
                       (T("Beneficiaries"), "beneficiary.value"),
                       #"status_id",
                       "date",
                       "end_date",
                       #"comments",
                       ]

        # Custom Form (Read/Create/Update)
        if r.method in ("create", "update"):
            editable = True
            # Custom Widgets/Validators
            from s3 import IS_LOCATION, S3LocationSelector #, S3MultiSelectWidget
            location_field.label = "" # Gets replaced by widget
            location_field.requires = IS_LOCATION()
            location_field.widget = S3LocationSelector(levels=levels)
            # Doesn't work Inline yet
            #s3db.project_activity_organisation.organisation_id.widget = S3MultiSelectWidget(multiple=False)
        else:
            editable = False

        # Hide Labels when just 1 column in inline form
        #s3db.doc_document.file.label = ""
        #s3db.project_activity_activity_type.activity_type_id.label = ""
        s3db.project_activity_organisation.organisation_id.label = ""

        # Custom Crud Form
        from s3 import S3SQLCustomForm, S3SQLInlineComponent
        #bttable = s3db.project_beneficiary_type
        #total = current.db(bttable.name == "Total").select(bttable.parameter_id,
        #                                                   limitby=(0, 1)).first()
        #if total:
        #    parameter_id = total.parameter_id
        #else:
        #    parameter_id = None
        crud_form = S3SQLCustomForm(
            #S3SQLInlineComponent(
            #    "activity_activity_type",
            #    label = T("Activity Type"),
            #    fields = ["activity_type_id"],
            #    multiple = False,
            #),
            S3SQLInlineComponent(
                "activity_organisation",
                label = T("Organization"),
                fields = ["organisation_id"],
                #multiple = False,
            ),
            "location_id",
            "name",
            S3SQLInlineComponent(
                "beneficiary",
                label = T("Beneficiaries"),
                link = False,
                #multiple = False,
                fields = ["value",
                          "parameter_id",
                          ],
                #filterby = dict(field = "parameter_id",
                #                options = parameter_id
                #                ),
            ),
            S3SQLInlineComponent(
                "distribution",
                label = T("Distributions"),
                link = False,
                #multiple = False,
                fields = ["value",
                          "parameter_id",
                          ],
            ),
            #S3SQLInlineComponent(
            #    "document",
            #    name = "file",
            #    label = T("Files"),
            #    fields = ["file",
            #              #"comments",
            #              ],
            #),
            #"status_id",
            "date",
            "end_date",
            #"comments",
            )

        from s3 import S3LocationFilter, S3OptionsFilter#, S3DateFilter
        filter_widgets = [
            S3LocationFilter("location_id",
                             #levels = levels,
                             levels = ("L0", "L1"),
                             ),
            S3OptionsFilter("sector_activity.sector_id",
                            # Doesn't support translation
                            #represent = "%(name)s",
                            ),
            #S3OptionsFilter("distribution.parameter_id",
            #                # Doesn't support translation
            #                #represent = "%(name)s",
            #                ),
            #S3OptionsFilter("theme_activity.theme_id",
            #                # Doesn't support translation
            #                #represent = "%(name)s",
            #                ),
            #S3OptionsFilter("beneficiary.parameter_id",
            #                # Doesn't support translation
            #                #represent = "%(name)s",
            #                ),
            S3OptionsFilter("activity_organisation.organisation_id",
                            label = T("National Society"),
                            ),
            # @ToDo: Widget to handle Start & End in 1!
            #S3DateFilter("date",
            #             label=T("Start Date"),
            #             hide_time=True,
            #             ),
            #S3DateFilter("end_date",
            #             label=T("End Date"),
            #             hide_time=True,
            #             ),
            S3OptionsFilter("year",
                            label = T("Year"),
                            options = s3db.project_activity_year_options,
                            ),
            ]

        settings.ui.hide_report_options = False

        s3db.configure(tablename,
                       crud_form = crud_form,
                       # Hide Open & Delete dataTable action buttons
                       deletable = editable,
                       editable = editable,
                       filter_widgets = filter_widgets,
                       filter_formstyle = filter_formstyle,
                       listadd = False,
                       list_fields = list_fields,
                       report_formstyle = True,
                       )

        return True
    s3.prep = custom_prep

    # Custom PostP
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.method == "summary" and r.interactive and isinstance(output, dict):
            output["title"] = ""
            # Move Report Options under Filters (but keep hidden field within .pt-container)
            # Style Filters like Report Options
            script = \
'''$('#filter-form fieldset').appendTo($('#summary-filter-form'))
$('#summary-filter-form div').appendTo($('#filter-form fieldset'))
$('#filter-form').show()
$('.pt-table-contents').show()
$('.pt-form-container').appendTo($('.span3')).show()
$('.pt-form input[name="pivotdata"]').appendTo($('.pt-container'))'''
            s3.jquery_ready.append(script)

        return output
    s3.postp = custom_postp

    # Remove rheader
    attr["rheader"] = None

    return attr

settings.customise_project_activity_controller = customise_project_activity_controller

# -----------------------------------------------------------------------------
def customise_project_project_fields():
    """
        Customise project_project fields for Profile widgets and 'more' popups
    """

    format = "%d/%m/%y"
    date_represent = lambda d: S3DateTime.date_represent(d, format=format)

    s3db = current.s3db

    s3db.project_location.location_id.represent = s3db.gis_LocationRepresent(sep=" | ")
    table = s3db.project_project
    table.start_date.represent = date_represent
    table.end_date.represent = date_represent
    from s3 import s3_auth_user_represent_name
    table.modified_by.represent = s3_auth_user_represent_name
    table.modified_on.represent = datetime_represent

    list_fields = [#"name",
                   "organisation_id",
                   "location.location_id",
                   "organisation_id$logo",
                   "start_date",
                   "end_date",
                   #"human_resource_id",
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
def customise_project_project_controller(**attr):

    s3 = current.response.s3

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

        s3db = current.s3db
        table = s3db.project_project

        if r.method == "datalist":
            customise_project_project_fields()
            s3db.configure("project_project",
                           # Don't include a Create form in 'More' popups
                           listadd = False,
                           #list_layout = render_projects,
                           )
        elif r.interactive or r.representation == "aadata":
            # Filter from a Profile page?
            # If so, then default the fields we know
            get_vars = current.request.get_vars
            organisation_id = get_vars.get("~.(organisation)", None)
            if not organisation_id:
                user = current.auth.user
                if user:
                    organisation_id = user.organisation_id

            # Configure fields
            table.objectives.readable = table.objectives.writable = True
            table.human_resource_id.label = T("Focal Person")
            s3db.hrm_human_resource.organisation_id.default = organisation_id
            table.budget.label = "%s (USD)" % T("Budget")
            # Better in column label & otherwise this construction loses thousands separators
            #table.budget.represent = lambda value: "%d USD" % value

            s3db.doc_document.file.label = ""

            from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentCheckbox
            crud_form_fields = [
                    "name",
                    S3SQLInlineComponentCheckbox(
                        "theme",
                        label = T("Themes"),
                        field = "theme_id",
                        option_help = "comments",
                        cols = 3,
                    ),
                    S3SQLInlineComponent(
                        "location",
                        label = T("Districts"),
                        fields = ["location_id"],
                        orderby = "location_id$name",
                        render_list = True
                    ),
                    "description",
                    "human_resource_id",
                    "start_date",
                    "end_date",
                    # Partner Orgs
                    S3SQLInlineComponent(
                        "organisation",
                        name = "partner",
                        label = T("Partner Organizations"),
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
                    #"objectives",
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
                    ]
            if organisation_id:
                org_field = table.organisation_id
                org_field.default = organisation_id
                org_field.readable = org_field.writable = False
            else:
                location_field = s3db.project_location.location_id
                location_id = get_vars.get("~.(location)", None)
                if location_id:
                    # Default to this Location, but allow selection of others
                    location_field.default = location_id
                location_field.label = ""
                location_field.represent = S3Represent(lookup="gis_location")
                # Project Locations must be districts
                from s3 import IS_ONE_OF

                location_field.requires = IS_ONE_OF(current.db, "gis_location.id",
                                                    S3Represent(lookup="gis_location"),
                                                    sort = True,
                                                    filterby = "level",
                                                    filter_opts = ("L1",)
                                                    )
                # Don't add new Locations here
                location_field.comment = None
                # Simple dropdown
                location_field.widget = None
                crud_form_fields.insert(1, "organisation_id")

            crud_form = S3SQLCustomForm(*crud_form_fields)

            list_fields = [#"name",
                           "organisation_id",
                           "human_resource_id",
                           (T("Districts"), "location.location_id"),
                           "start_date",
                           "end_date",
                           #"budget",
                           ]

            # Return to List view after create/update/delete (unless done via Modal)
            url_next = URL(c="project", f="project")

            from s3 import S3LocationFilter, S3TextFilter, S3OptionsFilter
            filter_widgets = [
                S3TextFilter(["name",
                              "description",
                              "location.location_id",
                              #"theme.name",
                              #"objectives",
                              "comments"
                              ],
                             label = T("Search Projects"),
                             ),
                S3OptionsFilter("organisation_id",
                                label = T("Lead Organization"),
                                ),
                S3LocationFilter("location.location_id",
                                 levels = ("L0", "L1", "L2", "L3"),
                                 ),
                S3OptionsFilter("partner.organisation_id",
                                label = T("Partners"),
                                ),
                S3OptionsFilter("donor.organisation_id",
                                label = T("Donors"),
                                )
                ]

            s3db.configure("project_project",
                           create_next = url_next,
                           delete_next = url_next,
                           update_next = url_next,
                           crud_form = crud_form,
                           list_fields = list_fields,
                           filter_widgets = filter_widgets,
                           )

            # This is awful in Popups & inconsistent in dataTable view (People/Documents don't have this & it breaks the styling of the main Save button)
            #s3.cancel = URL(c="project", f="project")

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
            # All users just get "Open"
            #db = current.db
            #auth = current.auth
            #has_permission = auth.s3_has_permission
            #ownership_required = auth.permission.ownership_required
            #s3_accessible_query = auth.s3_accessible_query
            #if has_permission("update", table):
            #    action = dict(label=str(T("Edit")),
            #                  _class="action-btn",
            #                  url=URL(c="project", f="project",
            #                          args=["[id]", "update"]),
            #                  )
            #    if ownership_required("update", table):
            #        # Check which records can be updated
            #        query = s3_accessible_query("update", table)
            #        rows = db(query).select(table._id)
            #        restrict = []
            #        rappend = restrict.append
            #        for row in rows:
            #            row_id = row.get("id", None)
            #            if row_id:
            #                rappend(str(row_id))
            #        action["restrict"] = restrict
            #    actions.append(action)
            #if has_permission("delete", table):
            #    action = dict(label=str(T("Delete")),
            #                  _class="action-btn",
            #                  url=URL(c="project", f="project",
            #                          args=["[id]", "delete"]),
            #                  )
            #    if ownership_required("delete", table):
            #        # Check which records can be deleted
            #        query = s3_accessible_query("delete", table)
            #        rows = db(query).select(table._id)
            #        restrict = []
            #        rappend = restrict.append
            #        for row in rows:
            #            row_id = row.get("id", None)
            #            if row_id:
            #                rappend(str(row_id))
            #        action["restrict"] = restrict
            #    actions.append(action)
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

settings.customise_project_project_controller = customise_project_project_controller

# -----------------------------------------------------------------------------
def customise_supply_distribution_controller(**attr):

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
            from s3 import IS_LOCATION, S3LocationSelector
            location_field = r.table.location_id
            levels = ("L0", "L1", "L2", "L3")
            location_field.requires = IS_LOCATION()
            location_field.widget = S3LocationSelector(levels=levels)

        return True
    s3.prep = custom_prep

    return attr

settings.customise_supply_distribution_controller = customise_supply_distribution_controller

# -----------------------------------------------------------------------------
# Filter forms - style for Summary pages
def filter_formstyle(row_id, label, widget, comment, hidden=False):
    return DIV(label, widget, comment,
               _id=row_id,
               _class="horiz_filter_form")

# =============================================================================
# Template Modules
# Comment/uncomment modules here to disable/enable them
settings.modules = OrderedDict([
    # Core modules which shouldn't be disabled
    ("default", Storage(
        name_nice = "Home",
        restricted = False, # Use ACLs to control access to this module
        access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
        module_type = None  # This item is not shown in the menu
    )),
    ("admin", Storage(
        name_nice = "Administration",
        #description = "Site Administration",
        restricted = True,
        access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        module_type = None  # This item is handled separately for the menu
    )),
    ("appadmin", Storage(
        name_nice = "Administration",
        #description = "Site Administration",
        restricted = True,
        module_type = None  # No Menu
    )),
    ("errors", Storage(
        name_nice = "Ticket Viewer",
        #description = "Needed for Breadcrumbs",
        restricted = False,
        module_type = None  # No Menu
    )),
    ("sync", Storage(
        name_nice = "Synchronization",
        #description = "Synchronization",
        restricted = True,
        access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        module_type = None  # This item is handled separately for the menu
    )),
    ("translate", Storage(
        name_nice = "Translation Functionality",
        #description = "Selective translation of strings based on module.",
        module_type = None,
    )),
    ("gis", Storage(
        name_nice = "Map",
        #description = "Situation Awareness & Geospatial Analysis",
        restricted = True,
        module_type = 1,     # 1st item in the menu
    )),
    ("pr", Storage(
        name_nice = "Persons",
        #description = "Central point to record details on People",
        restricted = True,
        access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
        module_type = None
    )),
    ("org", Storage(
        name_nice = "Organizations",
        #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
        restricted = True,
        module_type = None
    )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
        name_nice = "Contacts",
        #description = "Human Resources Management",
        restricted = True,
        module_type = None,
    )),
    ("cms", Storage(
            name_nice = "Content Management",
            restricted = True,
            module_type = None,
        )),
    ("doc", Storage(
        name_nice = "Documents",
        #description = "A library of digital resources, such as photos, documents and reports",
        restricted = True,
        module_type = None,
    )),
    ("msg", Storage(
        name_nice = "Messaging",
        #description = "Sends & Receives Alerts via Email & SMS",
        restricted = True,
        # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        module_type = None,
    )),
    #("event", Storage(
    #    name_nice = "Disasters",
    #    #description = "Events",
    #    restricted = True,
    #    module_type = None
    #)),
    ("project", Storage(
        name_nice = "Projects",
        restricted = True,
        module_type = None
    )),
    ("stats", Storage(
        name_nice = "Statistics",
        restricted = True,
        module_type = None
    )),
    #("vulnerability", Storage(
    #    name_nice = "Vulnerability",
    #    restricted = True,
    #    module_type = None
    #)),
    #("transport", Storage(
    #    name_nice = "Transport",
    #    restricted = True,
    #    module_type = None
    #)),
    #("hms", Storage(
    #    name_nice = "Hospitals",
    #    restricted = True,
    #    module_type = None
    #)),
    #("cr", Storage(
    #    name_nice = "Shelters",
    #    restricted = True,
    #    module_type = None
    #)),
    ("supply", Storage(
        name_nice = "Supply Chain Management",
        restricted = True,
        module_type = None
    )),
])
