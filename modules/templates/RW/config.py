# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.html import A, DIV, LI, URL, TAG, TD, TR, UL
from gluon.storage import Storage

from s3 import s3_fullname, S3Represent, S3SQLInlineLink

def config(settings):
    """ RefugeesWelcome Template """

    T = current.T

    settings.base.system_name = "#RefugeesWelcome"
    settings.base.system_name_short = "#RefugeesWelcome"

    # PrePopulate data
    settings.base.prepopulate += ("RW", "default/users")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "RW"

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_link_user_to_default = "staff"

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("DE",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True
    # Show Lat/Lon fields in Location Selector
    settings.gis.latlon_selector = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
       ("ar", "العربية"),
       ("en", "English"),
       ("fr", "Français"),
       ("de", "Deutsch"),
       ("el", "ελληνικά"),
       ("es", "Español"),
       ("it", "Italiano"),
       ("pt", "Português"),
       ("ru", "русский"),
       ("tr", "Türkçe"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "de"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    #settings.L10n.utc_offset = "+0100"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    settings.L10n.translate_org_organisation = True
    # Uncomment this to Translate Site Names
    settings.L10n.translate_org_site = True
    # Finance settings
    #settings.fin.currencies = {
    #   "EUR" : "Euros",
    #   "GBP" : "Great British Pounds",
    #   "USD" : "United States Dollars",
    #}
    settings.fin.currency_default = "EUR"

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    #
    settings.security.policy = 7 # Organisation-ACLs

    # Represent user IDs by names rather than email
    settings.ui.auth_user_represent = "name"

    # -------------------------------------------------------------------------
    # Custom icon classes
    settings.ui.custom_icons = {
        "news": "icon-info",
        "needs": "icon-list",
        "organisations": "icon-group",
    }

    # -------------------------------------------------------------------------
    # CMS
    # Uncomment to use Bookmarks in Newsfeed
    settings.cms.bookmarks = True
    # Uncomment to use have Filter form in Newsfeed be open by default
    settings.cms.filter_open = True
    # Uncomment to adjust filters in Newsfeed when clicking on locations instead of opening the profile page
    settings.cms.location_click_filters = True
    # Uncomment to use organisation_id instead of created_by in Newsfeed
    settings.cms.organisation = "post_organisation.organisation_id"
    # Uncomment to use org_group_id in Newsfeed
    #settings.cms.organisation_group = "post_organisation_group.group_id"
    # Uncomment to use person_id instead of created_by in Newsfeed
    settings.cms.person = "person_id"
    # Uncomment to use Rich Text editor in Newsfeed
    settings.cms.richtext = True
    # Uncomment to show Links in Newsfeed
    settings.cms.show_links = True
    # Uncomment to show Tags in Newsfeed
    settings.cms.show_tags = True
    # Uncomment to show post Titles in Newsfeed
    settings.cms.show_titles = True

    # -------------------------------------------------------------------------
    # Organisations
    settings.org.tags = True
    settings.org.service_locations = True

    # -------------------------------------------------------------------------
    # Human Resources
    settings.hrm.skill_types = True
    settings.hrm.org_required = False

    # -------------------------------------------------------------------------
    # Project Module
    settings.project.projects = True
    settings.project.mode_3w = True
    settings.project.activities = True
    settings.project.activity_types = True
    settings.project.sectors = True

    settings.project.multiple_organisations = True

    settings.project.assign_staff_tab = False

    # -------------------------------------------------------------------------
    # Requests Module
    #
    settings.req.recurring = False
    settings.req.use_req_number = False
    settings.req.requester_optional = True
    settings.req.summary = True

    settings.req.use_commit = False
    settings.req.ask_transport = True
    settings.req.req_type = ("Stock",)

    # -------------------------------------------------------------------------
    # Shelters
    settings.cr.tags = True

    # -------------------------------------------------------------------------
    def customise_cms_post_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            table = r.table

            # Simple Location Represent
            #table.location_id.represent = S3Represent(lookup="gis_location")

            # We only use a single type so hard-code it
            table.series_id.readable = table.series_id.writable = False
            if not r.record:
               stable = current.s3db.cms_series
               row = current.db(stable.name == "News").select(stable.id,
                                                              limitby=(0, 1)
                                                              ).first()
               try:
                   table.series_id.default = row.id
               except:
                   # Prepop not done
                   # Undo the readable/writable so as not to mask the error
                   table.series_id.readable = table.series_id.writable = True

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_cms_post_controller = customise_cms_post_controller

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        s3db = current.s3db
        # Load Model
        s3db.hrm_human_resource
        # Retrieve CRUD fields
        crud_fields = current.response.s3.hrm.crud_fields
        crud_fields.append("comments")
        from s3 import S3SQLCustomForm
        crud_form = S3SQLCustomForm(*crud_fields)
        s3db.configure("hrm_human_resource",
                       crud_form = crud_form,
                       )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -------------------------------------------------------------------------
    def customise_project_location_resource(r, tablename):

        s3db = current.s3db

        table = s3db.project_location

        # Allow editing of names
        field = table.name
        field.readable = field.writable = True

        # Hide percentage field (not needed)
        field = table.percentage
        field.readable = field.writable = False

        # Use location selector
        from s3 import S3LocationSelector
        field = table.location_id
        field.widget = S3LocationSelector(show_address=True)

        # List fields
        list_fields = ["project_id",
                       "name",
                       "location_id",
                       "location_id$addr_street",
                       "activity_type_location.activity_type_id",
                        ]

        # CRUD Form
        from s3 import S3SQLCustomForm
        crud_form = S3SQLCustomForm("project_id",
                                    "name",
                                    "location_id",
                                    S3SQLInlineLink("activity_type",
                                                    field = "activity_type_id",
                                                    multiple = True,
                                                    ),
                                    "comments",
                                    )

        # Reconfigure resource
        s3db.configure("project_location",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       create_next = None,
                       onaccept = None,
                       )

    settings.customise_project_location_resource = customise_project_location_resource

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        from s3 import S3LocationFilter, S3OptionsFilter, S3TextFilter

        filter_widgets = [
            S3TextFilter(["name"],
                         label = T("Search"),
                         comment = T("Search by facility name. You can use * as wildcard."),
                         ),
            S3OptionsFilter("site_facility_type.facility_type_id",
                            ),
            S3OptionsFilter("organisation_id",
                            ),
            S3LocationFilter("location_id",
                             ),
            ]

        s3db = current.s3db

        s3db.configure(tablename,
                       filter_widgets = filter_widgets,
                       )

        # Customize fields
        table = s3db.org_facility

        # Main facility flag visible and in custom crud form
        field = table.main_facility
        field.readable = field.writable = True
        crud_form = s3db.get_config(tablename, "crud_form")
        crud_form.insert(-2, "main_facility")

        # "Obsolete" labeled as "inactive"
        field = table.obsolete
        field.label = T("Inactive")

        # Show Last Updated field in list view
        list_fields = s3db.get_config(tablename, "list_fields")
        list_fields.append((T("Last Updated"), "modified_on"))

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from gluon.html import DIV, INPUT
        from s3 import s3_comments_widget, \
                       S3LocationSelector, \
                       S3MultiSelectWidget, \
                       S3SQLCustomForm, \
                       S3SQLInlineComponent, \
                       S3SQLInlineComponentMultiSelectWidget, \
                       S3SQLVerticalSubFormLayout

        s3db = current.s3db

        # Filtered component to access phone number and email
        s3db.add_components(tablename,
                            org_facility = {"name": "main_facility",
                                            "joinby": "organisation_id",
                                            "filterby": "main_facility",
                                            "filterfor": True,
                                            },
                            )

        s3db.org_organisation_location.location_id.widget = S3LocationSelector(levels=("L2", "L3", "L4"),
                                                                               show_map=False,
                                                                               labels=False,
                                                                               )

        crud_fields = ["name",
                       "acronym",
                       S3SQLInlineLink("organisation_type",
                                       field = "organisation_type_id",
                                       label = T("Type"),
                                       multiple = False,
                                       ),
                       S3SQLInlineLink(
                            "service",
                            label = T("Services"),
                            field = "service_id",
                            ),
                       S3SQLInlineComponent(
                            "facility",
                            label = T("Main Facility"),
                            fields = ["name",
                                      "phone1",
                                      "phone2",
                                      "email",
                                      "location_id",
                                      ],
                            layout = S3SQLVerticalSubFormLayout,
                            filterby = {"field": "main_facility",
                                        "options": True,
                                        },
                            multiple = False,
                            ),
                       "website",
                       S3SQLInlineComponent(
                            "contact",
                            name = "twitter",
                            label = T("Twitter"),
                            multiple = False,
                            fields = [("", "value")],
                            filterby = dict(field = "contact_method",
                                            options = "TWITTER",
                                            ),
                            ),
                       S3SQLInlineComponent(
                            "contact",
                            name = "facebook",
                            label = T("Facebook"),
                            multiple = False,
                            fields = [("", "value")],
                            filterby = dict(field = "contact_method",
                                            options = "FACEBOOK",
                                            ),
                            ),
                       "comments",
                       ]

        crud_form = S3SQLCustomForm(*crud_fields)

        from s3 import S3LocationFilter, S3OptionsFilter, S3TextFilter#, S3HierarchyFilter
        filter_widgets = [
            S3TextFilter(["name", "acronym"],
                         label = T("Search"),
                         comment = T("Search by organization name or acronym. You can use * as wildcard."),
                         _class = "filter-search",
                         ),
            S3LocationFilter("org_facility.location_id",
                             label = T("Location"),
                             #hidden = True,
                             ),
            S3OptionsFilter("organisation_organisation_type.organisation_type_id",
                            label = T("Type"),
                            #hidden = True,
                            ),
            S3OptionsFilter("service_organisation.service_id",
                            #hidden = True,
                            ),
            ]

        list_fields = ["name",
                       (T("Type"), "organisation_organisation_type.organisation_type_id"),
                       (T("Services"), "service.name"),
                       (T("Adresse"), "main_facility.location_id"),
                       (T("Phone #"), "main_facility.phone1"),
                       (T("Email"), "main_facility.email"),
                       (T("Facebook"), "facebook.value"),
                       "website",
                       (T("Last Updated"), "modified_on"),
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        tabs = [(T("Basic Details"), None),
                (T("Service Locations"), "service_location"),
                (T("Needs"), "needs"),
                (T("Facilities"), "facility"),
                (T("Warehouses"), "warehouse"),
                (T("Offices"), "office"),
                (T("Staff & Volunteers"), "human_resource"),
                #(T("Assets"), "asset"),
                #(T("Projects"), "project"),
                #(T("User Roles"), "roles"),
                #(T("Tasks"), "task"),
                ]
        rheader = lambda r: current.s3db.org_rheader(r, tabs=tabs)
        attr["rheader"] = rheader
        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_req_organisation_needs_resource(r, tablename):

        s3db = current.s3db
        table = current.s3db.req_organisation_needs

        CASH = T("Cash Donations needed")

        if r.tablename == "req_organisation_needs":

            from s3 import IS_ONE_OF, S3DateTime

            # Allow only organisations which do not have a needs record
            # yet (single component):
            field = table.organisation_id
            dbset = current.db(table.id == None)
            left = table.on(table.organisation_id == current.s3db.org_organisation.id)
            field.requires = IS_ONE_OF(dbset, "org_organisation.id",
                                       field.represent,
                                       left = left,
                                       orderby = "org_organisation.name",
                                       sort = True,
                                       )

            # Format modified_on as date
            field = table.modified_on
            field.represent = lambda d: S3DateTime.date_represent(d, utc=True)

        if r.representation in ("html", "aadata", "iframe"):

            # Structured lists for interactive views
            from gluon import Field
            table.needs_skills = Field.Method(lambda row: \
                                    organisation_needs(row, need_type="skills"))
            table.needs_items = Field.Method(lambda row: \
                                    organisation_needs(row, need_type="items"))
            current.response.s3.stylesheets.append("../themes/RW/needs.css")

            needs_skills = (T("Volunteers needed"), "needs_skills")
            needs_items = (T("Supplies needed"), "needs_items")

            # Filter widgets
            from s3 import S3LocationFilter, S3OptionsFilter, S3TextFilter
            filter_widgets = [#S3TextFilter(["organisation_id$name",
                              #              ],
                              #              label = T("Search"),
                              #             ),
                              S3OptionsFilter("organisation_id"),
                              S3OptionsFilter("organisation_needs_skill.skill_id",
                                              label = T("Skills sought"),
                                              ),
                              S3OptionsFilter("organisation_needs_item.item_id",
                                              label = T("Supplies sought"),
                                              ),
                              S3LocationFilter("organisation_id$active_service_location.site_id$location_id",
                                               ),
                              ]

            # CRUD form
            from s3 import S3SQLCustomForm, S3SQLInlineComponent
            crud_form = S3SQLCustomForm(
                            "organisation_id",
                            S3SQLInlineComponent("organisation_needs_skill",
                                                label = T("Volunteers needed"),
                                                fields = ["skill_id",
                                                        "demand",
                                                        "comments",
                                                        ],
                                                ),
                            S3SQLInlineComponent("organisation_needs_item",
                                                label = T("Supplies needed"),
                                                fields = ["item_id",
                                                        "demand",
                                                        "comments",
                                                        ],
                                                ),
                            (CASH, "money"),
                            "money_details",
                            #"vol",
                            #"vol_details",
                            )

            next_page = r.url(method="") \
                        if r.tablename == "req_organisation_needs" else None

            s3db.configure("req_organisation_needs",
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           create_next = next_page,
                           update_next = next_page,
                           )
        else:
            # Simple fields for exports
            needs_skills = (T("Volunteers needed"),
                            "organisation_needs_skill.skill_id")
            needs_items = (T("Supplies needed"),
                           "organisation_needs_item.item_id")

        # List fields (all formats)
        list_fields = ["organisation_id",
                       needs_skills,
                       needs_items,
                       (CASH, "money"),
                       (T("Cash Donation Details"), "money_details"),
                       (T("Last Update"), "modified_on"),
                       ]

        s3db.configure("req_organisation_needs",
                       list_fields = list_fields,
                       )

    settings.customise_req_organisation_needs_resource = customise_req_organisation_needs_resource

    # -------------------------------------------------------------------------
    def customise_req_site_needs_resource(r, tablename):

        if r.tablename == "req_site_needs":
            table = r.table
            field = table.site_id
            field.label = current.T("Facility")
            field.readable = field.writable = True

            # Allow only facilities which do not have a req_site_needs
            # yet (single component), and filter out obsolete facilities
            from s3 import IS_ONE_OF, FS
            dbset = current.db(table.id == None)
            left = table.on(table.site_id == current.s3db.org_site.id)
            field.requires = IS_ONE_OF(dbset, "org_site.site_id",
                                       field.represent,
                                       left = left,
                                       not_filterby = "obsolete",
                                       not_filter_opts = (True,),
                                       orderby = "org_site.name",
                                       sort = True,
                                       )
            if not r.record:
                query = FS("site_id$obsolete") != True
                r.resource.add_filter(query)

            # Allow adding of facilities in popup
            from s3layouts import S3PopupLink
            field.comment = S3PopupLink(c = "org",
                                        f = "facility",
                                        vars = {"child": "site_id",
                                                "parent": "site_needs",
                                                },
                                        title = T("Add New Facility"),
                                        )

        # Filters
        from s3 import S3LocationFilter, S3TextFilter
        filter_widgets = [S3TextFilter(["site_id$name",
                                        "vol_details",
                                        "goods_details",
                                        ],
                                        label = T("Search"),
                                       ),
                          S3LocationFilter("site_id$location_id",
                                           ),
                          ]

        # List fields
        list_fields = [(T("Facility"), "site_id$name"),
                       "site_id$location_id",
                       ("%s?" % T("Volunteers"), "vol"),
                       (T("Help Wanted"), "vol_details"),
                       ("%s?" % T("Donations"), "goods"),
                       (T("Donations Needed"), "goods_details"),
                       "modified_on",
                       ]

        current.s3db.configure("req_site_needs",
                               filter_widgets = filter_widgets,
                               list_fields = list_fields,
                               )

    settings.customise_req_site_needs_resource = customise_req_site_needs_resource

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
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
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        ("hrm", Storage(
           name_nice = T("Staff"),
           #description = "Human Resources Management",
           restricted = True,
           module_type = 10,
        )),
        ("vol", Storage(
           name_nice = T("Volunteers"),
           #description = "Human Resources Management",
           restricted = True,
           module_type = 10,
        )),
        ("cms", Storage(
         name_nice = T("Content Management"),
         #description = "Content Management System",
         restricted = True,
         module_type = 10,
        )),
        ("doc", Storage(
           name_nice = T("Documents"),
           #description = "A library of digital resources, such as photos, documents and reports",
           restricted = True,
           module_type = 10,
        )),
        #("msg", Storage(
        #    name_nice = T("Messaging"),
        #    #description = "Sends & Receives Alerts via Email & SMS",
        #    restricted = True,
        #    # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        #    module_type = None,
        #)),
        ("supply", Storage(
           name_nice = T("Supply Chain Management"),
           #description = "Used within Inventory Management, Request Management and Asset Management",
           restricted = True,
           module_type = None, # Not displayed
        )),
        ("inv", Storage(
           name_nice = T("Warehouses"),
           #description = "Receiving and Sending Items",
           restricted = True,
           module_type = 4
        )),
        #("asset", Storage(
        #    name_nice = T("Assets"),
        #    #description = "Recording and Assigning Assets",
        #    restricted = True,
        #    module_type = 5,
        #)),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = T("Vehicles"),
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("req", Storage(
           name_nice = T("Requests"),
           #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
           restricted = True,
           module_type = 10,
        )),
        ("project", Storage(
           name_nice = T("Projects"),
           #description = "Tracking of Projects, Activities and Tasks",
           restricted = True,
           module_type = 2
        )),
        ("cr", Storage(
            name_nice = T("Shelters"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            module_type = 10
        )),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("dvr", Storage(
        #   name_nice = T("Disaster Victim Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("mpr", Storage(
          name_nice = T("Missing Persons"),
          #description = "Helps to report and search for missing persons",
          restricted = True,
          module_type = 10,
        )),
        ("event", Storage(
           name_nice = T("Events"),
           #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
           restricted = True,
           module_type = 10,
        )),
        ("transport", Storage(
           name_nice = T("Transport"),
           restricted = True,
           module_type = 10,
        )),
        ("stats", Storage(
           name_nice = T("Statistics"),
           #description = "Manages statistics",
           restricted = True,
           module_type = None,
        )),
    ])

# =============================================================================
demand_options = {1: "Low Demand",
                  2: "Moderate Demand",
                  3: "High Demand",
                  4: "Urgently needed",
                  }

# =============================================================================
def organisation_needs(row, need_type=None):
    """
        Field.Method to render structured organisation needs (list views)

        @param row: the row (passed from Field.Method)
        @param need_type: the need type (skills|items)
    """

    NONE = current.messages["NONE"]

    try:
        needs = getattr(row, "req_organisation_needs")
    except AttributeError:
        return NONE
    needs_id = needs.id

    s3db = current.s3db
    if need_type == "skills":
        ltable = s3db.req_organisation_needs_skill
        stable = s3db.hrm_skill
        left = stable.on(stable.id == ltable.skill_id)
    elif need_type == "items":
        ltable = s3db.req_organisation_needs_item
        stable = s3db.supply_item
        left = stable.on(stable.id == ltable.item_id)

    query = (ltable.organisation_needs_id == needs_id)
    rows = current.db(query).select(ltable.demand,
                                    stable.name,
                                    left = left,
                                    )
    if not rows:
        return NONE

    needs = {}
    dfield = str(ltable.demand)
    nfield = str(stable.name)
    for row in rows:
        demand = row[dfield]
        if demand not in needs:
            needs[demand] = [row[nfield]]
        else:
            needs[demand].append(row[nfield])

    T = current.T
    output = DIV(_class="org-needs")
    for demand in (4, 3, 2, 1):
        if demand not in needs:
            continue
        title = "%s:" % T(demand_options[demand])
        items = UL([LI(T(need))
                    for need in needs[demand] if need is not None])
        output.append(TAG[""](title, items))
    return output

# END =========================================================================