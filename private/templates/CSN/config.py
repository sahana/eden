# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *
from gluon.storage import Storage
from gluon.validators import IS_NULL_OR

from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
from s3.s3utils import S3DateTime, s3_auth_user_represent_name, s3_avatar_represent, s3_unicode
from s3.s3validators import IS_LOCATION
from s3.s3widgets import S3LocationAutocompleteWidget

T = current.T
settings = current.deployment_settings

"""
    Template settings for CSN
"""

# =============================================================================
# US Settings
# -----------------------------------------------------------------------------
# Uncomment to Hide the language toolbar
settings.L10n.display_toolbar = False
# Default timezone for users
settings.L10n.utc_offset = "UTC -0800"
# Uncomment these to use US-style dates in English (localisations can still convert to local format)
settings.L10n.date_format = T("%m-%d-%Y")
settings.L10n.time_format = T("%H:%M:%S")
settings.L10n.datetime_format = T("%m-%d-%Y %H:%M")
# Start week on Sunday
settings.L10n.firstDOW = 0
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","
# Default Country Code for telephone numbers
settings.L10n.default_country_code = 1
# Enable this to change the label for 'Mobile Phone'
settings.ui.label_mobile_phone = "Cell Phone"
# Enable this to change the label for 'Postcode'
settings.ui.label_postcode = "ZIP Code"
# PDF to Letter
settings.base.paper_size = T("Letter")

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

settings.auth.registration_roles = {"site_id": ["reader",
                                                ],
                                    }

# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 3 # Controllers
settings.security.map = True

# Owner Entity
settings.auth.person_realm_human_resource_site_then_org = False

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ["CSN"]

settings.base.system_name = T("Community Stakeholder Network")
settings.base.system_name_short = T("CSN")

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "CSN"
#settings.gis.map_height = 600
#settings.gis.map_width = 854

# Mouse Position: 'normal', 'mgrs' or None
settings.gis.mouse_position = None
# Uncomment to hide the Overview map
settings.gis.overview = False
# Uncomment to hide the permalink control
settings.gis.permalink = False
# Uncomment to hide the ScaleLine control
#settings.gis.scaleline = False
# Uncomment to modify the Simplify Tolerance
settings.gis.simplify_tolerance = 0.001
# Uncomment to hide the Zoom control
settings.gis.zoomcontrol = False

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
])
# Default Language
settings.L10n.default_language = "en"

# -----------------------------------------------------------------------------
# Finance settings
settings.fin.currencies = {
    "USD" : T("United States Dollars"),
}

# -----------------------------------------------------------------------------
# Enable this for a UN-style deployment
#settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
#settings.ui.camp = True

# -----------------------------------------------------------------------------
# Save Search Widget
settings.save_search.widget = False

# =============================================================================
# Module Settings

# -----------------------------------------------------------------------------
# Human Resource Management
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
def location_represent(id, row=None):
    """
        Custom Representation of Locations
    """

    if not row:
        if not id:
            return current.messages["NONE"]
        table = current.s3db.gis_location
        row = current.db(table.id == id).select(table.L3,
                                                table.L4,
                                                limitby=(0, 1)).first()

    represent = "%s | %s" % (s3_unicode(row.L3).upper() if row.L3 else "",
                             s3_unicode(row.L4).upper() if row.L4 else "",
                             )
    return represent

# -----------------------------------------------------------------------------
def customize_cms_post(**attr):
    """
        Customize cms_post controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    table = s3db.cms_post

    field = table.series_id
    field.label = T("Type")
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
    field = table.location_id
    field.represent = location_represent
    field.requires = IS_NULL_OR(IS_LOCATION(level="L4"))
    field.widget = S3LocationAutocompleteWidget(level="L4")
    table.created_by.represent = s3_auth_user_represent_name
    field = table.body
    field.label = T("Text")
    field.widget = None
    #table.comments.readable = table.comments.writable = False

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

    # Return to List view after create/update/delete
    url_next = URL(c="default", f="index", args=None)

    list_fields = ["series_id",
                   "location_id",
                   "created_on",
                   "body",
                   "created_by",
                   "created_by$organisation_id",
                   "document.file",
                   "comments", # Needed for YouTube URLs
                   ]

    s3db.configure("cms_post",
                   create_next = url_next,
                   delete_next = url_next,
                   update_next = url_next,
                   crud_form = crud_form,
                   list_fields = list_fields,
                   )

    crud_settings = s3.crud
    crud_settings.formstyle = "bootstrap"
    crud_settings.submit_button = T("Save changes")
    # Done already within Bootstrap formstyle (& anyway fails with this formstyle)
    #crud_settings.submit_style = "btn btn-primary"

    # Custom PostP
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.representation == "plain" and \
           r.method != "search":
            # Map Popups - styled like dataList
            auth = current.auth
            db = current.db
            record = r.record
            record_id = record.id

            item_class = "thumbnail"
            item_id = "popup-%s" % record_id

            table = s3db.cms_post
            series = table.series_id.represent(record.series_id)
            date = S3DateTime.date_represent(record.created_on, utc=True)
            body = record.body
            location_id = record.location_id
            location = table.location_id.represent(location_id)
            location_url = URL(c="gis", f="location", args=[location_id])

            # Attachment(s)?
            table = s3db.doc_document
            row = db(table.doc_id == record.doc_id).select(table.file,
                                                           limitby=(0, 1)
                                                           ).first()
            if row:
                doc_url = URL(c="default", f="download",
                              args=[row.file]
                              )
                doc_link = A(I(_class="icon icon-paper-clip fright"),
                             _href=doc_url)
            else:
                doc_link = ""

            if series not in ("News", "Twitter", "Ushahidi", "YouTube"):
                # We expect an Author
                author_id = record.created_by
                author = table.created_by.represent(author_id)
                utable = auth.settings.table_user
                user = db(utable.id == author_id).select(utable.organisation_id,
                                                         limitby=(0, 1)
                                                         ).first()
                organisation_id = user.organisation_id
                organisation = s3db.org_organisation_id.attr["represent"](organisation_id)
                org_url = URL(c="org", f="organisation", args=[organisation_id])
                # @ToDo: Optimise by not doing DB lookups (especially duplicate) within render, but doing these in the bulk query
                avatar = s3_avatar_represent(author_id,
                                             _class="media-object",
                                             _style="width:50px;padding:5px;padding-top:0px;")
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
                avatar = A(avatar,
                           _href=person_url,
                           _class="pull-left",
                           )
                card_person = DIV(author,
                                  " - ",
                                  A(organisation,
                                    _href=org_url,
                                    _class="card-organisation",
                                    ),
                                  doc_link,
                                  _class="card-person",
                                  )
            else:
                # No Author
                card_person = DIV(doc_link,
                                  _class="card-person",
                                  )
                avatar = None
                if series == "News":
                    icon = URL(c="static", f="img",
                               args=["markers", "gis_marker.image.News.png"])
                elif series == "Twitter":
                    icon = URL(c="static", f="img", args=["social", "twitter.png"])
                elif series == "Ushahidi":
                    icon = URL(c="static", f="img",
                               args=["markers", "gis_marker.image.Ushahidi.png"])
                elif series == "YouTube":
                    #icon = URL(c="static", f="img", args=["social", "YouTube.png"])
                    avatar = DIV(IFRAME(_width=320,
                                        _height=180,
                                        _src=record.comments,
                                        _frameborder=0),
                                 _class="pull-left"
                                 )
                if not avatar:
                    avatar = DIV(IMG(_src=icon,
                                     _class="media-object",
                                     _style="width:50px;padding:5px;padding-top:0px;",
                                     ),
                                 _class="pull-left")

            # Edit Bar
            permit = auth.s3_has_permission
            if permit("update", table, record_id=record_id):
                edit_btn = A(I(" ", _class="icon icon-edit"),
                             _href=URL(c="cms", f="post",
                             args=[record_id, "update"]),
                             )
            else:
                edit_btn = ""
            # delete_btn looks too much like popup close!
            #if permit("delete", table, record_id=record_id):
            #    delete_btn = A(I(" ", _class="icon icon-remove-sign"),
            #                   _href=URL(c="cms", f="post",
            #                   args=[record_id, "delete"]),
            #                   )
            #else:
            delete_btn = ""
            edit_bar = DIV(edit_btn,
                           delete_btn,
                           _class="edit-bar fright",
                           )

            # Overall layout
            output = DIV(DIV(I(SPAN(" %s" % T(series),
                                    _class="card-title",
                                    ),
                               _class="icon icon-%s" % series.lower(),
                               ),
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
                                     card_person,
                                     _class="media",
                                     ),
                                 _class="media-body",
                                 ),
                             _class="media",
                             ),
                         _class=item_class,
                         _id=item_id,
                         )
        elif callable(standard_postp):
            # Call standard postp
            output = standard_postp(r, output)
        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_cms_post = customize_cms_post

# -----------------------------------------------------------------------------
def org_office_marker_fn(record):
    """
        Function to decide which Marker to use for Offices
        @ToDo: Legend
        @ToDo: Use Symbology
    """

    db = current.db
    otable = db.org_organisation
    organisation = db(otable.id == record.organisation_id).select(otable.name,
                                                                  limitby=(0, 1)).first()
    
    if organisation:
        name = organisation.name
        if name == "City National Bank":
            name = "CNB"
        elif name == "Dorchester Collection":
            name = "hotel"
        else:
            name = name.replace(" ", "")
        marker = name

    mtable = db.gis_marker
    try:
        marker = db(mtable.name == marker).select(mtable.image,
                                                  mtable.height,
                                                  mtable.width,
                                                  cache=current.s3db.cache,
                                                  limitby=(0, 1)
                                                  ).first()
    except:
        marker = None
    return marker

# -----------------------------------------------------------------------------
def customize_org_office(**attr):
    """
        Customize org_office controller
        - Marker fn
    """

    current.s3db.configure("org_office",
                           marker_fn = org_office_marker_fn,
                           )

    return attr

settings.ui.customize_org_office = customize_org_office
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
            name_nice = T("Events"),
            #description = "Events",
            restricted = True,
            module_type = None
        )),
    ("irs", Storage(
            name_nice = "Ushahidi Reports",
            #description = "Incident Reports",
            restricted = True,
            module_type = None
        )),
    ("transport", Storage(
            name_nice = T("Transport"),
            restricted = True,
            module_type = None
        )),
    ("hms", Storage(
            name_nice = T("Hospitals"),
            restricted = True,
            module_type = None
        )),
    ("fire", Storage(
            name_nice = T("Fire"),
            restricted = True,
            module_type = None
        )),
])
