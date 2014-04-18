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

T = current.T
s3 = current.response.s3
settings = current.deployment_settings

"""
    UN OCHA Regional Office of Caucasus and Central Asia (ROCCA) Humanitarian Data Platform Template settings
"""

# Levels for the LocationSelector
gis_levels = ("L0", "L1", "L2", "L3")

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
    #("hy", "Armenian"),
    #("az", "Azerbaijani"),
    #("ka", "Georgian"),
    #("kk", "Kazakh"),
    #("ky", "Kyrgyz"),
    #("ru", "Russian"),
    #("tg",  "Tajik"),
    #("tk",  "Turkmen"),
    #("uz", "Uzbek"),
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
# Events
# Make Event Types Hierarchical
settings.event.types_hierarchical = True

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
    {"name": T("Vulnerability"),
     "c": "vulnerability", 
     "f": "data",
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
    
    s3db = current.s3db

    # Custom filtered components for custom list_fields
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

    from s3.s3widgets import S3MultiSelectWidget

    s3db.gis_location.parent.widget = S3MultiSelectWidget(multiple=False)
    
    s3db.gis_location_name.name_l10n.label = ""
    s3db.gis_location_tag.value.label = ""

    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent

    crud_form = S3SQLCustomForm("name",
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

    field = s3db.gis_location.inherited
    field.label =  T("Mapped?")
    field.represent =  lambda inherited: T("No") if inherited else T("Yes")

    filter_widgets = s3db.get_config("gis_location", 
                                     "filter_widgets")

    # Remove L2 & L3 filters 
    # NB Fragile: dependent on filters defined in gis/location controller
    filter_widgets.pop()
    filter_widgets.pop()

    s3db.configure("gis_location",
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   list_fields = ["name",
                                  # @ToDo: Investigate whether we can support this style & hence not need to define custom components
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
def customise_event_event_controller(**attr):

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False
        r.table.start_date.writable = True
        return True
    s3.prep = custom_prep

    # Remove rheader
    attr["rheader"] = None
    return attr

settings.customise_event_event_controller = customise_event_event_controller

# -----------------------------------------------------------------------------
def customise_event_event_resource(r, tablename):
    """
        Customise event_event resource
        - List Fields
        - CRUD Strings
        - Form
        - Filter
        - Report 
        Runs after controller customisation
        But runs before prep
        
        @ToDo: Move some of this into the model as defaults
    """

    from s3.s3filter import S3DateFilter, S3HierarchyFilter, S3LocationFilter, S3OptionsFilter
    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
    from s3.s3validators import IS_LOCATION_SELECTOR2
    from s3.s3widgets import S3LocationSelectorWidget2

    db = current.db
    s3db = current.s3db
    table = r.table
    table.name.label = T("Disaster Number")

    location_field = s3db.event_event_location.location_id
    location_field.requires = IS_LOCATION_SELECTOR2(levels=gis_levels)
    location_field.widget = S3LocationSelectorWidget2(levels=gis_levels)
    location_field.label = ""

    impact_fields = OrderedDict(killed = "Killed",
                                total_affected = "Total Affected",
                                est_damage = "Estimated Damage (US$ Million)",
                                )

    ptable = s3db.stats_impact_type
    rows = db(ptable.name.belongs(impact_fields.values())).select(ptable.id,
                                                                  ptable.name,
                                                                  )
    parameters = rows.as_dict(key="name")

    impact_crud_form_fields = []
    impact_list_fields = []
    add_components = s3db.add_components
    for tag, label  in impact_fields.items():
        parameter = parameters[label]["id"]
        add_components("event_event",
                       stats_impact = {"name": tag,
                                       "link": "event_impact",
                                       "joinby": "event_id",
                                       "key": "impact_id",
                                       "filterby": "parameter_id",
                                       "filterfor": (parameter,),
                                       },
                       )
        # These aren't yet working
        impact_crud_form_fields.append(S3SQLInlineComponent(tag,
                                                            label = T(label),
                                                            multiple = False,
                                                            fields = ["value"],
                                                            #filterby = dict(field = "parameter_id",
                                                            #                options = parameter
                                                            #                )
                                                            ))
        impact_list_fields.append((T(label), "%s.value" % tag))

    # Hide label in CRUD form
    db.stats_impact.value.label = ""
    crud_form = S3SQLCustomForm("name",
                                "event_type_id",
                                "start_date",
                                "end_date",
                                # @ToDo: Inline location_id field
                                #S3SQLInlineComponent("event_location",
                                #                     label = T("Location"),
                                #                     multiple = False,
                                #                     fields = ["location_id"],
                                #                     ),
                                *impact_crud_form_fields
                                )

    filter_widgets = [S3HierarchyFilter("event_type_id",
                                        label = T("Type"),
                                        # Not translateable
                                        #represent = "%(name)s",
                                        multiple = False,
                                        ),
                      S3LocationFilter("event_location.location_id",
                                       levels = gis_levels,
                                       ),
                      S3DateFilter("date",
                                   label = None,
                                   hide_time = True,
                                   input_labels = {"ge": "From", "le": "To"}
                                   ),
                      ]

    list_fields = ["name",
                   "event_type_id",
                   ]
    lappend = list_fields.append

    report_fields = ["event_type_id",
                     ]
    rappend = report_fields.append
    
    for level in gis_levels:
        location_level = "event_location.location_id$%s" % level
        lappend(location_level)
        rappend(location_level)

    list_fields.extend(("start_date",
                        "end_date",
                        ))
    list_fields.extend(impact_list_fields)

    # @ToDo: start_date -> Report on Year only.. @flavour ;)
    rappend("start_date")

    report_options = Storage(rows=report_fields,
                             cols=report_fields,
                             fact=[(T("Number of Disasters"), "count(id)"),
                                   (T("Total Killed"), "sum(value)"),
                                   (T("Total Affected"), "sum(value)"),
                                   (T("Number of Disasters"), "sum(value)"),
                                   ],# +\
                                   # @ToDo: Fix to produce sum instead of only count of string field
                                   #[(label, "sum(%s)" % value) for label, value in tag_list_fields],
                             defaults=Storage(rows="event_type_id",
                                              cols="event_location.location_id$L0",
                                              fact="count(id)",
                                              totals=True,
                                              chart = "breakdown:rows",
                                              table = "collapse",
                                              ),
                             )

    s3db.configure("event_event",
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   list_fields = list_fields,
                   report_options = report_options,
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
    ("vulnerability", Storage(
        name_nice = "Vulnerability",
        restricted = True,
        module_type = None
    )),
])