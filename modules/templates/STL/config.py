# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Settings for the SupportToLife deployment in Turkey
    """

    T = current.T

    settings.base.system_name = T("Sahana Refugee Case Management")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate += ("STL", "default/users", "STL/Demo")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "STL"

    # =========================================================================
    # Security/AAA Settings
    #
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    #settings.auth.registration_requests_organisation = True
    # Uncomment to have Person records owned by the Org they are an HR for
    settings.auth.person_realm_human_resource_site_then_org = True

     # Approval emails get sent to all admins
    #settings.mail.approver = "ADMIN"

    # Security Policy
    settings.security.policy = 7 # Hierarchical realms

    # =========================================================================
    # GIS Settings
    #
    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("TR",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # =========================================================================
    # L10n Settings
    #
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
        ("ar", "العربية"),
        ("en", "English"),
        ("tr", "Türkçe"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.utc_offset = "+0200"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = ","
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = "."
    # Uncomment this to Translate Layer Names
    settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    settings.L10n.translate_org_organisation = True

    # =========================================================================
    # Finance Settings
    #
    settings.fin.currencies = {
        "EUR" : "Euros",
        #"GBP" : "Great British Pounds",
        "TRY" : "Turkish Lira",
        "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "TRY"

    # =========================================================================
    # Person Registry
    #
    # Allow third gender
    settings.pr.hide_third_gender = False

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        s3db = current.s3db

        # Person tag for Family ID Number
        s3db.add_components("pr_person",
                            pr_person_tag = {"name": "family_id",
                                             "joinby": "person_id",
                                             "filterby": "tag",
                                             "filterfor": ("FAMILY_ID",),
                                             "multiple": False,
                                             },
                            )

        table = s3db.pr_person

        # Remove default tooltip for pe_label
        field = table.pe_label
        field.comment = None

        # Use "Gender" as label for gender field
        field = table.gender
        field.label = current.T("Gender")

        if r.controller == "dvr":
            # Default nationality for case beneficiaries is Syrian
            dtable = s3db.pr_person_details
            field = dtable.nationality
            field.default = "SY"

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.controller == "dvr" and not r.component:

                table = r.table
                ctable = s3db.dvr_case

                # Hierarchical Organisation Selector
                field = ctable.organisation_id
                from gluon import DIV
                from s3 import S3HierarchyWidget
                represent = s3db.org_OrganisationRepresent(parent=False)
                field.widget = S3HierarchyWidget(lookup="org_organisation",
                                                 represent=represent,
                                                 multiple=False,
                                                 leafonly=False,
                                                 )
                field.comment = DIV(_class = "tooltip",
                                    _title = "%s|%s" % (T("Organisation"),
                                                        T("The organisation/branch this case is assigned to"),
                                                        ),
                                    )

                # Individual staff assignment
                field = ctable.human_resource_id
                field.label = T("Person Responsible")
                field.readable = field.writable = True

                resource = r.resource
                if r.interactive:

                    from s3 import S3LocationSelector, \
                                   S3SQLCustomForm, \
                                   S3SQLInlineComponent, \
                                   S3TextFilter

                    # Custom CRUD form
                    crud_form = S3SQLCustomForm(
                                "dvr_case.date",
                                "dvr_case.organisation_id",
                                "dvr_case.human_resource_id",
                                "first_name",
                                "middle_name",
                                "last_name",
                                "person_details.nationality",
                                "date_of_birth",
                                "gender",
                                (T("Individual ID Number"), "pe_label"),
                                S3SQLInlineComponent(
                                        "family_id",
                                        fields = [("", "value"),
                                                  ],
                                        filterby = {"field": "tag",
                                                    "options": "FAMILY_ID",
                                                    },
                                        label = T("Family ID Number"),
                                        multiple = False,
                                        name = "family_id",
                                        ),
                                S3SQLInlineComponent(
                                        "address",
                                        label = T("Current Address"),
                                        fields = [("", "location_id"),
                                                  ],
                                        filterby = {"field": "type",
                                                    "options": "1",
                                                    },
                                        link = False,
                                        multiple = False,
                                        ),
                                S3SQLInlineComponent(
                                        "contact",
                                        fields = [("", "value"),
                                                  ],
                                        filterby = {"field": "contact_method",
                                                    "options": "SMS",
                                                    },
                                        label = T("Mobile Phone"),
                                        multiple = False,
                                        name = "phone",
                                        ),
                                "dvr_case.comments",
                                )

                    resource.configure(crud_form = crud_form,
                                       )
                    # Hide Postcode in addresses (not used)
                    atable = s3db.pr_address
                    location_id = atable.location_id
                    location_id.widget = S3LocationSelector(show_address=True,
                                                            show_postcode = False,
                                                            )

                    # Extend text filter with Family ID and case comments
                    filter_widgets = resource.get_config("filter_widgets")
                    for fw in filter_widgets:
                        if isinstance(fw, S3TextFilter):
                            fw.field.extend(("family_id.value",
                                             "dvr_case.comments",
                                             ))
                            break

                    # Inject script to toggle Head of Household form fields
                    #path = "/%s/static/themes/STL/js/dvr.js" % current.request.application
                    #if path not in s3.scripts:
                    #    s3.scripts.append(path)

                # Custom list fields (must be outside of r.interactive)
                list_fields = [(T("ID"), "pe_label"),
                               (T("Family ID"), "family_id.value"),
                               "first_name",
                               "middle_name",
                               "last_name",
                               "date_of_birth",
                               "gender",
                               "person_details.nationality",
                               "dvr_case.date",
                               ]
                resource.configure(list_fields = list_fields,
                                   )
            return result
        s3.prep = custom_prep

        # Custom rheader tabs
        if current.request.controller == "dvr":
            attr = dict(attr)
            attr["rheader"] = stl_dvr_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # =========================================================================
    # Staff Module
    #
    settings.hrm.staff_departments = False

    # =========================================================================
    # Organisation Registry
    #
    settings.org.branches = True

    # Uncomment this to make tree view the default for "Branches" tab
    #settings.org.branches_tree_view = True

    # =========================================================================
    # Modules
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
            module_type = 2,
        )),
        ("vol", Storage(
            name_nice = T("Volunteers"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        #("cms", Storage(
        #    name_nice = T("Content Management"),
        #    #description = "Content Management System",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        #("supply", Storage(
        #    name_nice = T("Supply Chain Management"),
        #    #description = "Used within Inventory Management, Request Management and Asset Management",
        #    restricted = True,
        #    module_type = None, # Not displayed
        #)),
        #("inv", Storage(
        #    name_nice = T("Warehouses"),
        #    #description = "Receiving and Sending Items",
        #    restricted = True,
        #    module_type = 4
        #)),
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
        #("req", Storage(
        #    name_nice = T("Requests"),
        #    #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #   restricted = True,
        #    module_type = 10,
        #)),
        #("project", Storage(
        #    name_nice = T("Projects"),
        #    #description = "Tracking of Projects, Activities and Tasks",
        #    restricted = True,
        #    module_type = 2
        #)),
        ("cr", Storage(
            name_nice = T("Camps"),
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
        ("dvr", Storage(
          name_nice = T("Case Management"),
          #description = "Allow affected individuals & households to register to receive compensation and distributions",
          restricted = True,
          module_type = 10,
        )),
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("tr", Storage(
        #   name_nice = "Turkish Extensions",
        #   restricted = True,
        #   module_type = None,
        #)),
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
def stl_dvr_rheader(r, tabs=[]):
    """ DVR custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, \
                   S3ResourceHeader, \
                   s3_fullname

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "pr_person":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

                case = resource.select(["first_name",
                                        "last_name",
                                        ],
                                        represent = True,
                                        raw_data = True,
                                        ).rows

                if case:
                    name = lambda row: s3_fullname(row)
                else:
                    return None

                rheader_fields = [[(T("ID"), "pe_label"),
                                   ],
                                  [(T("Name"), name),
                                   ],
                                  ["date_of_birth",
                                   ],
                                  ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )

    return rheader

# END =========================================================================
