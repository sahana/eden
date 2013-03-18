# -*- coding: utf-8 -*-

from gluon import current, URL
from gluon.html import *
from gluon.storage import Storage
from gluon.validators import IS_NULL_OR

from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
from s3.s3resource import S3FieldSelector
from s3.s3utils import s3_auth_user_represent_name, s3_avatar_represent, s3_unicode
from s3.s3validators import IS_LOCATION
from s3.s3widgets import S3LocationAutocompleteWidget

T = current.T
settings = current.deployment_settings

"""
    Template settings for DRM Portal
"""
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
settings.base.prepopulate = ["DRMP"]

settings.base.system_name = T("Disaster Risk Management Portal")
settings.base.system_name_short = T("DRMP")

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "DRMP"
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
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","

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
        row = current.db(table.id == id).select(table.L1,
                                                table.L2,
                                                table.L3,
                                                limitby=(0, 1)).first()

    represent = "%s | %s | %s" % (s3_unicode(row.L1) if row.L1 else "",
                                  s3_unicode(row.L2) if row.L2 else "",
                                  s3_unicode(row.L3) if row.L3 else "",
                                  )
    return represent

# -----------------------------------------------------------------------------
def customize_cms_post(**attr):
    """
        Customize cms_post controller
    """

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
    field.requires = IS_NULL_OR(IS_LOCATION(level="L3"))
    field.widget = S3LocationAutocompleteWidget(level="L3")
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
            "event_post",
            label = T("Disaster(s)"),
            fields = ["event_id"],
            orderby = "event_id$name"
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
    url_next = URL(c="default", f="index", args=None)

    list_fields = ["series_id",
                   "location_id",
                   "created_on",
                   "body",
                   "created_by",
                   "created_by$organisation_id",
                   "document.file",
                   ]

    s3db.configure("cms_post",
                   create_next = url_next,
                   delete_next = url_next,
                   update_next = url_next,
                   crud_form = crud_form,
                   list_fields = list_fields,
                   )

    crud_settings = current.response.s3.crud
    crud_settings.formstyle = "bootstrap"
    crud_settings.submit_button = T("Save changes")
    # Done already within Bootstrap formstyle (& anyway fails with this formstyle)
    #crud_settings.submit_style = "btn btn-primary"

    return attr

settings.ui.customize_cms_post = customize_cms_post

# -----------------------------------------------------------------------------
def render_profile_posts(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for CMS Posts on the Profile pages

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

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
    org_url = URL(c="org", f="organisation", args=[organisation_id])
    # @ToDo: Optimise by not doing DB lookups (especially duplicate) within render, but doing these in the bulk query
    avatar = s3_avatar_represent(author_id,
                                 _class="media-object")
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
    avatar = A(avatar,
               _href=person_url,
               _class="pull-left",
               )
    permit = current.auth.s3_has_permission
    table = db.cms_post
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="cms", f="post",
                               args=[record_id, "update.popup"],
                               vars={"refresh": listid,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.cms_post.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        #delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       #_href=URL(c="cms", f="post", args=[record_id, "delete"]),
                       #)
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                      )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )
    document = raw["doc_document.file"]
    if document:
        doc_url = URL(c="default", f="download",
                      args=[document]
                      )
        doc_link = A(I(_class="icon icon-paper-clip fright"),
                     _href=doc_url)
    else:
        doc_link = ""

    # Render the item
    class SMALL(DIV):
        tag = "small"

    item = DIV(DIV(DIV(avatar,
                       P(SMALL(" ", author, " ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               ),
                         _class="citation"),
                       _class="span1"),
                   DIV(SPAN(A(location,
                              _href=location_url,
                              ),
                            _class="location-title"),
                        " ",
                        SPAN(date,
                             _class="date-title"),
                        edit_bar,
                        P(body,
                          _class="card_comments"),
                        doc_link,
                       _class="span5 card-details"),
                   _class="row",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def customize_event_event(**attr):
    """
        Customize event_event controller
        - Profile Page
    """

    s3db = current.s3db

    # Customise the cms_post table as that is used for the widgets
    customize_cms_post()

    # Represent used in rendering
    current.auth.settings.table_user.organisation_id.represent = s3db.org_organisation_represent

    table = s3db.event_event

    alerts_widget = dict(label = "Alerts",
                         type = "datalist",
                         tablename = "cms_post",
                         filter = S3FieldSelector("series_id$name") == "Alert",
                         icon = "icon-alert",
                         list_layout = render_profile_posts,
                         )
    map_widget = dict(label = "Location",
                      type = "map",
                      icon = "icon-map-marker",
                      )
    incidents_widget = dict(label = "Incidents",
                            type = "datalist",
                            tablename = "cms_post",
                            filter = S3FieldSelector("series_id$name") == "Incident",
                            icon = "icon-warning-sign",
                            list_layout = render_profile_posts,
                            )
    assessments_widget = dict(label = "Assessments",
                              type = "datalist",
                              tablename = "cms_post",
                              filter = S3FieldSelector("series_id$name") == "Assessment",
                              icon = "icon-info-sign",
                              list_layout = render_profile_posts,
                              )
    activities_widget = dict(label = "Activities",
                             type = "datalist",
                             tablename = "cms_post",
                             filter = S3FieldSelector("series_id$name") == "Activity",
                             icon = "icon-activity",
                             list_layout = render_profile_posts,
                             )
    reports_widget = dict(label = "Reports",
                          type = "datalist",
                          tablename = "cms_post",
                          filter = S3FieldSelector("series_id$name") == "Report",
                          icon = "icon-report",
                          list_layout = render_profile_posts,
                          )
    comments_widget = dict(label = "Comments",
                           type = "comments",
                           icon = "icon-comments-alt",
                           colspan = 2,
                           )
    s3db.configure("event_event",
                   profile_widgets=[alerts_widget,
                                    map_widget,
                                    incidents_widget,
                                    assessments_widget,
                                    activities_widget,
                                    reports_widget,
                                    #comments_widget,
                                    ],
                   )

    crud_settings = current.response.s3.crud
    crud_settings.formstyle = "bootstrap"
    crud_settings.submit_button = T("Save changes")
    # Done already within Bootstrap formstyle (& anyway fails with this formstyle)
    #crud_settings.submit_style = "btn btn-primary"

    return attr

settings.ui.customize_event_event = customize_event_event

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
])
