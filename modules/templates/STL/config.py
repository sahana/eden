# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL
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

    settings.auth.admin_sees_organisation = True
    settings.auth.registration_organisation_default = "Support To Life"
    settings.auth.registration_link_user_to = ["staff"]
    settings.auth.registration_link_user_to_default = "staff"

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
    # UI Settings
    #
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["STL", "img", "stl_menu_logo.png"],
                                )

    # =========================================================================
    # DVR Case Management
    #
    def customise_dvr_case_resource(r, tablename):

        s3db = current.s3db
        s3 = current.response.s3

        if r.component_name == "dvr_case":

            table = r.component.table
            field = table.human_resource_id
            field.label = T("Person Responsible")
            field.readable = field.writable = True
            field.widget = None
            field.comment = None

            # Custom form
            from s3 import S3SQLCustomForm
            crud_form = S3SQLCustomForm("person_id",
                                        "date",
                                        "organisation_id",
                                        "human_resource_id",
                                        "status_id",
                                        )

            # Filter staff by organisation
            script = '''$.filterOptionsS3({
 'trigger':'organisation_id',
 'target':'human_resource_id',
 'lookupPrefix':'hrm',
 'lookupResource':'human_resource',
 'lookupKey':'organisation_id',
 'fncRepresent': function(record){return record.person_id},
 'optional': true
})'''
            s3.jquery_ready.append(script)

            s3db.configure("dvr_case",
                           crud_form = crud_form,
                           )

        # Deleting cases is not allowed
        s3db.configure("dvr_case",
                       deletable = False,
                       )

    settings.customise_dvr_case_resource = customise_dvr_case_resource

    # =========================================================================
    # Person Registry
    #
    # Allow third gender
    settings.pr.hide_third_gender = False

    # -------------------------------------------------------------------------
    def customise_pr_contact_resource(r, tablename):

        table = current.s3db.pr_contact

        field = table.contact_description
        field.readable = field.writable = False

        field = table.value
        field.label = current.T("Number or Address")

        field = table.contact_method
        from gluon import IS_IN_SET
        all_opts = current.msg.CONTACT_OPTS
        subset = ("SMS",
                  "EMAIL",
                  "HOME_PHONE",
                  "WORK_PHONE",
                  "FACEBOOK",
                  "TWITTER",
                  "SKYPE",
                  "OTHER",
                  )
        contact_methods = [(k, all_opts[k]) for k in subset if k in all_opts]
        field.requires = IS_IN_SET(contact_methods, zero=None)
        field.default = "SMS"

    settings.customise_pr_contact_resource = customise_pr_contact_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        s3db = current.s3db

        # Person tag for Family ID Number
        s3db.add_components("pr_person",
                            pr_person_tag = {"name": "family_id",
                                             "joinby": "person_id",
                                             "filterby": {
                                                 "tag": "FAMILY_ID",
                                                 },
                                             "multiple": False,
                                             },
                            )

        # Add contacts-method
        if r.controller == "dvr":
            s3db.set_method("pr", "person",
                            method = "contacts",
                            action = s3db.pr_Contacts,
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

            controller = r.controller

            if controller == "dvr" and not r.component:

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
                user = current.auth.user
                if user:
                    field.default = user.organisation_id

                # Individual staff assignment
                field = ctable.human_resource_id
                field.label = T("Person Responsible")
                field.readable = field.writable = True
                field.widget = None
                field.comment = None

                # Filter staff by organisation
                script = '''$.filterOptionsS3({
 'trigger':'sub_dvr_case_organisation_id',
 'target':'sub_dvr_case_human_resource_id',
 'lookupPrefix':'hrm',
 'lookupResource':'human_resource',
 'lookupKey':'organisation_id',
 'fncRepresent': function(record){return record.person_id},
 'optional': true
})'''
                s3.jquery_ready.append(script)

                # Custom label for registered-flag
                dtable = s3db.dvr_case_details
                field = dtable.registered
                field.default = False
                field.label = T("Registered with Turkish Authorities")
                field.comment = DIV(_class="tooltip",
                                    _title="%s|%s" % (T("Registered with Turkish Authorities"),
                                                      T("Is the client officially registered with AFAD/DGMM?"),
                                                      ),
                                    )

                resource = r.resource
                if r.interactive:

                    from s3 import S3DateFilter, \
                                   S3LocationSelector, \
                                   S3SQLCustomForm, \
                                   S3SQLInlineComponent, \
                                   S3TextFilter

                    # Custom CRUD form
                    crud_form = S3SQLCustomForm(
                                "dvr_case.date",
                                "dvr_case.organisation_id",
                                "dvr_case.human_resource_id",
                                "first_name",
                                #"middle_name",
                                "last_name",
                                "person_details.nationality",
                                "date_of_birth",
                                "gender",
                                "case_details.registered",
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

                    # Add filter for date of birth
                    dob_filter = S3DateFilter("date_of_birth",
                                              hidden=True,
                                              )
                    filter_widgets.append(dob_filter)

                    # Add filter for registration date
                    reg_filter = S3DateFilter("dvr_case.date",
                                                hidden = True,
                                                )
                    filter_widgets.append(reg_filter)

                    # Inject script to toggle Head of Household form fields
                    #path = "/%s/static/themes/STL/js/dvr.js" % current.request.application
                    #if path not in s3.scripts:
                    #    s3.scripts.append(path)

                # Custom list fields (must be outside of r.interactive)
                list_fields = [(T("ID"), "pe_label"),
                               (T("Family ID"), "family_id.value"),
                               "first_name",
                               #"middle_name",
                               "last_name",
                               "date_of_birth",
                               "gender",
                               "person_details.nationality",
                               "dvr_case.date",
                               "dvr_case.status_id",
                               ]
                resource.configure(list_fields = list_fields,
                                   )

            elif controller == "hrm":

                if not r.component:

                    table = s3db.pr_person_details
                    field = table.marital_status
                    field.readable = field.writable = False
                    field = table.religion
                    field.readable = field.writable = False

                elif r.method == "record" or \
                     r.component_name == "human_resource":

                    table = s3db.hrm_human_resource
                    field = table.site_id
                    field.readable = field.writable = False

            return result
        s3.prep = custom_prep

        standard_postp = s3.postp
        def custom_postp(r, output):

            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            # Remove subtitle on case tab
            if r.component_name == "dvr_case" and \
               isinstance(output, dict) and "subtitle" in output:
                output["subtitle"] = None

            return output
        s3.postp = custom_postp

        # Custom rheader tabs
        if current.request.controller == "dvr":
            attr = dict(attr)
            attr["rheader"] = stl_dvr_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # =========================================================================
    # Staff Module
    #
    settings.hrm.use_skills = False
    settings.hrm.use_address = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_id = False
    settings.hrm.use_trainings = False

    settings.hrm.staff_departments = False
    settings.hrm.teams = False
    settings.hrm.staff_experience = False

    def customise_hrm_human_resource_controller(**attr):

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

            if r.controller == "hrm":

                resource = r.resource

                # Hide "Facility" from form (unused)
                table = resource.table
                field = table.site_id
                field.readable = field.writable = False

                # Don't need Location/Facility filters either
                std_filters = resource.get_config("filter_widgets")
                filter_widgets = []
                for filter_widget in std_filters:
                    if filter_widget.field in ("location_id", "site_id"):
                        continue
                    filter_widgets.append(filter_widget)

                # Custom list fields
                list_fields = ["person_id",
                               "job_title_id",
                               "organisation_id",
                               (T("Email"), "email.value"),
                               (settings.get_ui_label_mobile_phone(), "phone.value"),
                               ]

                # Update resource config
                resource.configure(list_fields = list_fields,
                                   filter_widgets = filter_widgets,
                                   )
            return result
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # =========================================================================
    # Organisation Registry
    #
    settings.org.branches = True

    # Uncomment this to make tree view the default for "Branches" tab
    #settings.org.branches_tree_view = True

    def customise_org_organisation_controller(**attr):

        tabs = [(T("Basic Details"), None),
                (T("Staff & Volunteers"), "human_resource"),
                ]

        if settings.get_org_branches():
            if settings.get_org_branches_tree_view():
                branches = "hierarchy"
            else:
                branches = "branch"
            tabs.insert(1, (T("Branches"), branches))

        org_rheader = lambda r, tabs=tabs: current.s3db.org_rheader(r, tabs=tabs)

        attr = dict(attr)
        attr["rheader"] = org_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # =========================================================================
    # Project Module
    #
    settings.project.mode_3w = True
    settings.project.codes = True
    settings.project.sectors = False
    settings.project.assign_staff_tab = False

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        s3db = current.s3db

        from s3 import S3SQLCustomForm, \
                       S3TextFilter

        # Simplified form
        crud_form = S3SQLCustomForm("organisation_id",
                                    "code",
                                    "name",
                                    "description",
                                    "comments",
                                    )

        # Custom list fields
        list_fields = ["code",
                       "name",
                       "organisation_id",
                       ]

        # Custom filter widgets
        filter_widgets = [S3TextFilter(["name",
                                        "code",
                                        "description",
                                        "organisation_id$name",
                                        "comments",
                                        ],
                                        label = current.T("Search"),
                                       ),
                          ]

        s3db.configure("project_project",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_project_project_resource = customise_project_project_resource

    # -------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        T = current.T
        s3db = current.db
        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            # Customise fields
            table = s3db.project_project
            field = table.code
            field.label = T("Code")

            return result
        s3.prep = custom_prep


        # Custom rheader
        attr = dict(attr)
        attr["rheader"] = stl_project_rheader

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

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
        ("project", Storage(
           name_nice = T("Projects"),
           #description = "Tracking of Projects, Activities and Tasks",
           restricted = True,
           module_type = 2
        )),
        #("cr", Storage(
        #    name_nice = T("Camps"),
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
                        (T("Case Information"), "dvr_case"),
                        (T("Contact"), "contacts"),
                        ]

                case = resource.select(["family_id.value",
                                        "dvr_case.organisation_id",
                                        ],
                                        represent = True,
                                        raw_data = True,
                                        ).rows

                if case:
                    case = case[0]
                    family_id = lambda row: case["pr_family_id_person_tag.value"]
                    organisation_id = lambda row: case["dvr_case.organisation_id"]
                else:
                    return None
                name = lambda row: s3_fullname(row)

                rheader_fields = [[(T("ID"), "pe_label"),
                                   (T("Family ID"), family_id),
                                   ],
                                  [(T("Name"), name),
                                   (T("Organisation"), organisation_id),
                                   ],
                                  ["date_of_birth",
                                   ],
                                  ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )

    return rheader

# =============================================================================
def stl_project_rheader(r, tabs=[]):
    """ PROJECT custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, \
                   S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "project_project":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

                rheader_fields = [[(T("Code"), "code"),
                                   ],
                                  [(T("Name"), "name"),
                                   ],
                                  [(T("Organisation"), "organisation_id"),
                                   ],
                                  ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )

    return rheader

# END =========================================================================
