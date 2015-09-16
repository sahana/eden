# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.html import A, URL, TR, TD
from gluon.storage import Storage

from s3 import s3_fullname, S3Represent, S3SQLInlineLink, S3SQLSubFormLayout

def config(settings):
    """ RefugeesWelcome Template """

    T = current.T

    settings.base.system_name = "#RefugeesWelcome"
    settings.base.system_name_short = "#RefugeesWelcome"

    # PrePopulate data
    settings.base.prepopulate = ("RW", "default/users")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "RW"

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
    settings.gis.countries = ("DE",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

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
    settings.L10n.default_language = "de"
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
    #settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    #settings.L10n.translate_org_organisation = True
    # Finance settings
    settings.fin.currencies = {
       "EUR" : T("Euros"),
       "GBP" : T("Great British Pounds"),
       "USD" : T("United States Dollars"),
    }
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
    def customise_org_organisation_resource(r, tablename):

        s3db = current.s3db

        # List fields
        list_fields = ["name",
                       "acronym",
                       "organisation_organisation_type.organisation_type_id",
                       "website",
                       "comments",
                       ]

        s3db.configure("org_organisation",
                       list_fields = list_fields,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

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
        from s3 import S3SQLCustomForm, S3SQLInlineLink
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
                             levels = ("L2", "L3", "L4"),
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
        field.label = T("inactive")

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from gluon.html import DIV, INPUT
        from s3 import s3_comments_widget, \
                       S3LocationSelector, \
                       S3MultiSelectWidget, \
                       S3SQLCustomForm, \
                       S3SQLInlineLink, \
                       S3SQLInlineComponent, \
                       S3SQLInlineComponentMultiSelectWidget

        s3db = current.s3db

        # Filtered component to access phone number and email
        s3db.add_components("org_organisation",
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
                       S3SQLInlineComponent(
                            "facility",
                            label = T("Main Facility"),
                            fields = ["name",
                                      "phone1",
                                      "phone2",
                                      "email",
                                      "location_id",
                                      ],
                            layout = FacilitySubFormLayout,
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
                             levels = ("L2", "L3", "L4"),
                             #hidden = True,
                             ),
            ]

        list_fields = ["name",
                       (T("Type"), "organisation_organisation_type.organisation_type_id"),
                       (T("Adresse"), "main_facility.location_id"),
                       (T("Phone #"), "main_facility.phone1"),
                       (T("Email"), "main_facility.email"),
                       (T("Facebook"), "main_facility.facebook"),
                       "website",
                       ]

        s3db.configure("org_organisation",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        tabs = [(T("Basic Details"), None),
                (T("Facilities"), "facility"),
                (T("Warehouses"), "warehouse"),
                (T("Offices"), "office"),
                (T("Staff & Volunteers"), "human_resource"),
                (T("Needs"), "needs"),
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
    def customise_req_site_needs_resource(r, tablename):

        if r.tablename == "req_site_needs":
            table = r.table
            field = table.site_id
            field.label = current.T("Facility")
            field.readable = field.writable = True

            # @todo: allow only facilities which do not have a req_site_needs yet
            # @todo: if there aren't any, set insertable=False

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
        #("cr", Storage(
        #    name_nice = T("Shelters"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #    restricted = True,
        #    module_type = 10
        #)),
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
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("stats", Storage(
           name_nice = T("Statistics"),
           #description = "Manages statistics",
           restricted = True,
           module_type = None,
        )),
    ])

# =============================================================================
class FacilitySubFormLayout(S3SQLSubFormLayout):
    """
        Custom layout for facility inline-component in org/organisation

        - allows embedding of multiple fields besides the location selector
        - renders an vertical layout for edit-rows
        - standard horizontal layout for read-rows
        - hiding header row if there are no visible read-rows
    """

    # -------------------------------------------------------------------------
    def headers(self, data, readonly=False):
        """
            Header-row layout: same as default, but non-static (i.e. hiding
            if there are no visible read-rows, because edit-rows have their
            own labels)
        """

        headers = super(FacilitySubFormLayout, self).headers

        header_row = headers(data, readonly = readonly)
        element = header_row.element('tr');
        if hasattr(element, "remove_class"):
            element.remove_class("static")
        return header_row

    # -------------------------------------------------------------------------
    def rowstyle_read(self, form, fields, *args, **kwargs):
        """
            Formstyle for subform read-rows, same as standard
            horizontal layout.
        """

        rowstyle = super(FacilitySubFormLayout, self).rowstyle
        return rowstyle(form, fields, *args, **kwargs)

    # -------------------------------------------------------------------------
    def rowstyle(self, form, fields, *args, **kwargs):
        """
            Formstyle for subform edit-rows, using a vertical
            formstyle because multiple fields combined with
            location-selector are too complex for horizontal
            layout.
        """

        # Use standard foundation formstyle
        from s3theme import formstyle_foundation as formstyle
        if args:
            col_id = form
            label = fields
            widget, comment = args
            hidden = kwargs.get("hidden", False)
            return formstyle(col_id, label, widget, comment, hidden)
        else:
            parent = TD(_colspan = len(fields))
            for col_id, label, widget, comment in fields:
                parent.append(formstyle(col_id, label, widget, comment))
            return TR(parent)

# END =========================================================================