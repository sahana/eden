# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent

T = current.T
s3 = current.response.s3
settings = current.deployment_settings

"""
    UN OCHA Regional Office of Caucasus and Central Asia (ROCCA) Humanitarian Data Platform Template settings

    All settings which are to configure a specific template are located here

    Deployers should ideally not need to edit any other files outside of their template folder
"""

# Levels for the LocationSelector
levels = ("L1", "L2", "L3")

# =============================================================================
# System Settings
# -----------------------------------------------------------------------------
# Authorization Settings
# Users can self-register
#settings.security.self_registration = False
# Users need to verify their email
settings.auth.registration_requires_verification = True
# Users don't need to be approved
settings.auth.registration_requires_approval = True
#settings.auth.registration_requests_organisation = True
#settings.auth.registration_organisation_required = True

# Approval emails get sent to all admins
settings.mail.approver = "ADMIN"

settings.auth.registration_link_user_to = {"staff": T("Staff")}
settings.auth.registration_link_user_to_default = ["staff"]
settings.auth.registration_roles = {"organisation_id": ["USER"],
                                    }

settings.auth.show_utc_offset = False
settings.auth.show_link = False

# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 5 # Apply Controller, Function and Table ACLs
settings.security.map = True

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ["OCHAROCCA"]

settings.base.system_name = T("OCHA Regional Office of Caucasus and Central Asia (ROCCA) Humanitarian Data Platform")
settings.base.system_name_short = T("Humanitarian Data Platform")

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "OCHAROCCA"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
settings.ui.filter_formstyle = "bootstrap"
#settings.gis.map_height = 600
#settings.gis.map_width = 854

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
    # Only needed to import the l10n names
    ("ky", "Kyrgyz"),
    ("ru", "Russian"),
])
# Default Language
settings.L10n.default_language = "en"
# Default timezone for users
settings.L10n.utc_offset = "UTC +0600"
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
settings.gis.countries = ["AM",
                          "AZ",
                          "GE",
                          "KZ",
                          "KG",
                          "TJ",
                          "TM",
                          "UZ",
                          ]

# Until we add support to LocationSelector2 to set dropdowns from LatLons
#settings.gis.check_within_parent_boundaries = False
# Uncomment to hide Layer Properties tool
#settings.gis.layer_properties = False
# Hide unnecessary Toolbar items
settings.gis.nav_controls = False
# Uncomment to display the Map Legend as a floating DIV
settings.gis.legend = "float"
# Uncomment to Hide the Toolbar from the main Map
settings.gis.toolbar = False

# Use PCodes for Locations import
settings.gis.lookup_code = "PCode"

# -----------------------------------------------------------------------------
# Enable this for a UN-style deployment
#settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
#settings.ui.camp = True

# -----------------------------------------------------------------------------
# Uncomment to restrict the export formats available
#settings.ui.export_formats = ["xls"]

settings.ui.update_label = "Edit"

# -----------------------------------------------------------------------------
# Summary Pages
settings.ui.summary = [#{"common": True,
                       # "name": "cms",
                       # "widgets": [{"method": "cms"}]
                       # },
                       {"name": "table",
                        "label": "Table",
                        "widgets": [{"method": "datatable"}]
                        },
                       {"name": "map",
                        "label": "Map",
                        "widgets": [{"method": "map", "ajax_init": True}],
                        },
                       {"name": "charts",
                        "label": "Reports",
                        "widgets": [{"method": "report", "ajax_init": True}]
                        },
                       ]

settings.search.filter_manager = False

# =============================================================================
# Menu
current.response.menu = [
    {"name": T("Places"),
     "c": "gis", 
     "f": "location",
     "icon": "globe",
     "count": 312
     },
    {"name": T("Demographics"),
     "c": "stats", 
     "f": "demographic_data",
     "icon": "group",
     "count": 4656
     },
    {"name": T("Baseline Data"),
     "c": "stats", 
     "f": "demographic_data",
     "icon": "signal",
     "count": 0
     
     },
#    {"name": T("Stakeholders"),
#     "c": "org", 
#     "f": "organisation",
#     "icon": "sitemap",
#     "count": 0
#     },
    {"name": T("Disasters"),
     "c": "event", 
     "f": "event",
     "icon": "bolt",
     "count": 0
     },
    ]
for item in current.response.menu:
    item["url"] = URL(item["c"], 
                      item["f"], 
                      args = ["summary" if item["f"] not in ["organisation"]
                                        else "datalist"])
    
current.response.countries = [
    {"name": T("Armenia"),
     "code": "am"
     },
    {"name": T("Azerbaijan"),
     "code": "az"
     },
    {"name": T("Georgia"),
     "code": "ge"
     },
    {"name": T("Kazakhstan"),
     "code": "kz"
     },
    {"name": T("Kyrgyzstan"),
     "code": "kg"
     },
    {"name": T("Tajikistan"),
     "code": "tj"
     },
    {"name": T("Turkmenistan"),
     "code": "tm"
     },
    {"name": T("Uzbekistan"),
     "code": "uz"
     }
    ]

# =============================================================================
# Custom Controllers

# =============================================================================
def customise_gis_location_controller(**attr):
    """
        Customise org_organisation resource
        - List Fields
        - Form
        - Filter
        - Report 
        Runs after controller customisation
        But runs before prep
    """
    
    from s3.s3widgets import S3MultiSelectWidget

    s3db = current.s3db

    s3db.add_components("gis_location",
                        gis_location_name = {"name": "name_ru",
                                             "joinby": "location_id",
                                             "filterby": "language",
                                             "filterfor": ["ru"],
                                             },
                        gis_location_tag = {"name": "pcode",
                                            "joinby": "location_id",
                                            "filterby": "tag",
                                            "filterfor": ["PCode"],
                                            },
                        )

    s3db.gis_location.parent.widget = S3MultiSelectWidget(multiple=False)
    
    s3db.gis_location_name.name_l10n.label = ""
    s3db.gis_location_tag.value.label = ""

    crud_form = S3SQLCustomForm(
        "name",
        #"name_ru.name_l10n",
        S3SQLInlineComponent(
            "name_ru",
            label = T("Russian Name"),
            multiple = False,
            fields = ["name_l10n"],
        ),
        "level",
        S3SQLInlineComponent(
            "pcode",
            label = T("PCode"),
            multiple = False,
            fields = ["value"],
        ),
        #"pcode.value",
        "parent",
    )

    s3db.gis_location.inherited.label =  T("Mapped?")
    s3db.gis_location.inherited.reprent =  lambda inherited: "No" if inherited else "Yes"

    filter_widgets = s3db.get_config("gis_location", 
                                     "filter_widgets")

    # Remove L2 & L3 filters 
    # (fragile dependent on filters defined in gis/location controller)
    filter_widgets.pop()
    filter_widgets.pop()



    current.s3db.configure("gis_location",
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           list_fields = ["name",
                                          #(T("Russian Name"), "name.name_l10n?location_name.language=ru"),
                                          #("PCode", "tag.value?location_tag.tag=PCode"),
                                          (T("Russian Name"), "name_ru.name_l10n"),
                                          "level", ("PCode", "pcode.value"),
                                          "L0", "L1", "L2",
                                          "inherited",
                                          ]
                           )
    return attr

settings.customise_gis_location_controller = customise_gis_location_controller

# -----------------------------------------------------------------------------
def customise_event_event_resource(r, tablename):
    """
        Customise event_event resource
        - List Fields
        - CRUD Strings
        - Form
        - Filter
        Runs after controller customisation
        But runs before prep
    """

    s3db = current.s3db
    table = r.table

    table.zero_hour.label = T("Start Date")

    from s3.s3validators import IS_LOCATION_SELECTOR2
    from s3.s3widgets import S3LocationSelectorWidget2
    location_field = s3db.event_event_location.location_id
    location_field.requires = IS_LOCATION_SELECTOR2(levels=levels)
    location_field.widget = S3LocationSelectorWidget2(levels=levels)
    location_field.label = ""

    s3db.event_event_tag.value.label = ""
    tag_fields = OrderedDict(killed = "Killed",
                             total_affected = "Total Affected",
                             est_damage = "Estimated Damage (US$ Million)",
                             disaster_number = "Disaster Number")

    tag_crud_form_fields = []
    tag_list_fields = []
    for tag, label  in tag_fields.items():
        s3db.add_components("event_event",
                            event_event_tag = {"name": tag,
                                               "joinby": "event_id",
                                               "filterby": "tag",
                                               "filterfor": [label],
                                                },
                            )
        tag_crud_form_fields.append(S3SQLInlineComponent(tag,
                                                         label = T(label),
                                                         multiple = False,
                                                         fields = ["value"],
                                                         )
                                    )
        tag_list_fields.append((T(label), "%s.value" % tag))
      
    crud_form = S3SQLCustomForm(
        "name",
        "event_type_id",
        "zero_hour",
        "end_date",
        #"event_location.location_id",
        S3SQLInlineComponent("event_location",
                             label = T("Location"),
                             multiple = False,
                             fields = ["location_id"],
                             ),
        *tag_crud_form_fields
    )

    list_fields = ["name",
                   "event_type_id",
                   (T("Location"), "location.name"),
                   "zero_hour",
                   "end_date",
                   #(T("Killed"), "killed.value"),
                  ] + tag_list_fields

    s3db.configure("event_event",
                   crud_form = crud_form,
                   list_fields = list_fields,
                   )

    if r.interactive:
        # Labels
        table.comments.label = T("Description")

        s3.crud_strings["event_event"] = Storage(
            label_create = T("Record Disaster"),
            title_display = T("Disaster Details"),
            title_list = T("Disasters"),
            title_update = T("Edit Disaster"),
            label_list_button = T("List Disasters"),
            label_delete_button = T("Delete Disaster"),
            msg_record_created = T("Disaster added"),
            msg_record_modified = T("Disaster updated"),
            msg_record_deleted = T("Disaster deleted"),
            msg_list_empty = T("No Disasters currently registered"))

settings.customise_event_event_resource = customise_event_event_resource
# =============================================================================
# Modules
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
#    ("errors", Storage(
#        name_nice = "Ticket Viewer",
#        #description = "Needed for Breadcrumbs",
#        restricted = False,
#        module_type = None  # No Menu
#    )),
#    ("sync", Storage(
#        name_nice = "Synchronization",
#        #description = "Synchronization",
#        restricted = True,
#        access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
#        module_type = None  # This item is handled separately for the menu
#    )),
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
#    ("pr", Storage(
#        name_nice = "Persons",
        #description = "Central point to record details on People",
#        restricted = True,
#        access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
#        module_type = None
#    )),
    ("org", Storage(
        name_nice = "Organizations",
        #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
        restricted = True,
        module_type = None
    )),
    # All modules below here should be possible to disable safely
#    ("hrm", Storage(
#        name_nice = "Contacts",
        #description = "Human Resources Management",
#        restricted = True,
#        module_type = None,
#    )),
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
    ("event", Storage(
        name_nice = "Disasters",
        #description = "Events",
        restricted = True,
        module_type = None
    )),
    ("stats", Storage(
        name_nice = "Statistics",
        restricted = True,
        module_type = None
    )),
])