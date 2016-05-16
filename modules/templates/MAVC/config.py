# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.html import A, DIV, LI, URL, TAG, TD, TR, UL
from gluon.storage import Storage

from s3 import S3SQLSubFormLayout, s3_unicode

def config(settings):
    """
        Template settings for MAVC
    """

    T = current.T

    settings.base.system_name = T("Map the Philippines")
    #settings.base.system_name_short = T("MAVC")

    # PrePopulate data
    settings.base.prepopulate += ("MAVC", "default/users", "MAVC/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "MAVC"

    # =========================================================================
    # Authentication settings
    #
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True

    # Terms of Service to be able to Register on the system
    # uses <template>/views/tos.html
    settings.auth.terms_of_service = True

    # Approval emails get sent to all admins
    #settings.mail.approver = "ADMIN"

    # =========================================================================
    # GIS Settings
    #
    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("PH",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # =========================================================================
    # L10n settings
    #
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
    #    ("ar", "العربية"),
    #    ("bs", "Bosanski"),
        ("en", "English"),
    #    ("fr", "Français"),
    #    ("de", "Deutsch"),
    #    ("el", "ελληνικά"),
    #    ("es", "Español"),
    #    ("it", "Italiano"),
    #    ("ja", "日本語"),
    #    ("km", "ភាសាខ្មែរ"),
    #    ("ko", "한국어"),
    #    ("ne", "नेपाली"),          # Nepali
    #    ("prs", "دری"), # Dari
    #    ("ps", "پښتو"), # Pashto
    #    ("pt", "Português"),
    #    ("pt-br", "Português (Brasil)"),
    #    ("ru", "русский"),
    #    ("tet", "Tetum"),
        ("tl", "Tagalog"),
    #    ("tr", "Türkçe"),
    #    ("ur", "اردو"),
    #    ("vi", "Tiếng Việt"),
    #    ("zh-cn", "中文 (简体)"),
    #    ("zh-tw", "中文 (繁體)"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
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
        "EUR" : "Euros",
        "GBP" : "Great British Pounds",
        "PHP" : "Philippine Pesos",
        "USD" : "United States Dollars",
    }
    #settings.fin.currency_default = "USD"

    # =========================================================================
    # Security Policy
    #
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations

    settings.security.policy = 6 # Organisation-ACLs

    # Record Approval
    #settings.auth.record_approval = True
    #settings.auth.record_approval_required_for = ("org_organisation",
    #                                              "org_facility",
    #                                              "hrm_human_resource",
    #                                              "req_req",
    #                                              "inv_send",
    #                                              )

    # =========================================================================
    # UI settings
    #
    settings.ui.formstyle_read = "default_inline"

    settings.search.filter_manager = False
    settings.ui.label_postcode = "Postal Code"
    settings.ui.summary = ({"common": True,
                            "name": "add",
                            "widgets": [{"method": "create"}],
                            },
                           {"name": "table",
                            "label": "Table",
                            "widgets": [{"method": "datatable"}],
                            },
                           {"name": "charts",
                            "label": "Report",
                            "widgets": [{"method": "report", "ajax_init": True}],
                            },
                           {"name": "map",
                            "label": "Map",
                            "widgets": [{"method": "map", "ajax_init": True}],
                            },
                           )

    # =========================================================================
    # CMS Options
    #
    settings.cms.filter_open = True
    settings.cms.location_click_filters = True

    settings.cms.hide_index = True

    # =========================================================================
    # Documents
    #
    def customise_doc_document_resource(r, tablename):

        s3db = current.s3db
        table = s3db.doc_document

        # Document date defaults to today
        field = table.date
        field.default = current.request.utcnow.date()

        # Label name as "Title"
        field = table.name
        field.label = T("Title")

        # CRUD Form
        if r.interactive:
            from s3 import S3SQLCustomForm
            crud_form = S3SQLCustomForm("name",
                                        "file",
                                        "url",
                                        "date",
                                        "comments",
                                        )
        else:
            crud_form = None

        list_fields = ["name",
                       "file",
                       "url",
                       "date",
                       "comments",
                       ]
        s3db.configure("doc_document",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_doc_document_resource = customise_doc_document_resource

    # =========================================================================
    # Organisations
    #
    settings.org.sector = True

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        s3db = current.s3db

        # Use comments field for org description
        table = s3db.org_organisation
        field = table.comments
        from gluon import DIV
        field.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("About"),
                                              T("Describe the organisation, e.g. mission, history and other relevant details")))

        if not current.auth.is_logged_in():
            field = table.logo
            field.readable = field.writable = False
            # User can create records since we need this during registration,
            # but we don't want to let the user do this from the list view
            s3db.configure("org_organisation",
                           listadd = False,
                           )

        # Custom filters to match the information provided
        from s3 import S3LocationFilter, \
                       S3OptionsFilter, \
                       S3TextFilter, \
                       s3_get_filter_opts

        filter_widgets = [
            S3TextFilter(["name",
                          "acronym",
                          #"website",
                          #"comments",
                          ],
                         label = T("Search"),
                         comment = T("Search by organization name or acronym. You can use * as wildcard."),
                         ),
            S3OptionsFilter("organisation_organisation_type.organisation_type_id",
                            label = T("Type"),
                            ),
            S3OptionsFilter("service_location.service_location_service.service_id",
                            options = s3_get_filter_opts("org_service",
                                                         translate = True,
                                                         ),
                            ),
            S3OptionsFilter("sector_organisation.sector_id",
                            options = s3_get_filter_opts("org_sector",
                                                         translate = True,
                                                         ),
                            hidden = True,
                            ),
            ]

        # CRUD Form
        from s3 import S3SQLCustomForm, \
                       S3SQLInlineComponent, \
                       S3SQLInlineLink, \
                       S3SQLVerticalSubFormLayout
        multitype = settings.get_org_organisation_types_multiple()
        crud_form = S3SQLCustomForm("name",
                                    "acronym",
                                    S3SQLInlineLink(
                                            "organisation_type",
                                            field = "organisation_type_id",
                                            filter = False,
                                            label = T("Type"),
                                            multiple = multitype,
                                            ),
                                    "country",
                                    S3SQLInlineLink("sector",
                                            cols = 3,
                                            label = T("Sectors"),
                                            field = "sector_id",
                                            #required = True,
                                            ),
                                    (T("About"), "comments"),
                                    "website",
                                    S3SQLInlineComponent(
                                            "contact",
                                            name = "email",
                                            label = T("Email"),
                                            #multiple = False,
                                            fields = [("", "value"),
                                                      ],
                                            filterby = [{"field": "contact_method",
                                                         "options": "EMAIL",
                                                         },
                                                        ],
                                            ),
                                    S3SQLInlineComponent(
                                            "facility",
                                            label = T("Main Office"),
                                            fields = ["name",
                                                      "phone1",
                                                      "phone2",
                                                      #"email",
                                                      "location_id",
                                                      ],
                                            layout = S3SQLVerticalSubFormLayout,
                                            filterby = {"field": "main_facility",
                                                        "options": True,
                                                        },
                                            multiple = False,
                                            ),
                                    S3SQLInlineComponent(
                                        "document",
                                        fields = [(T("Title"), "name"),
                                                  "file",
                                                  ],
                                        filterby = {"field": "file",
                                                    "options": "",
                                                    "invert": True,
                                                    },
                                        label = T("Files"),
                                        name = "file",
                                        ),
                                    S3SQLInlineComponent(
                                        "document",
                                        fields = [(T("Title"), "name"),
                                                  "url",
                                                  ],
                                        filterby = {"field": "url",
                                                    "options": None,
                                                    "invert": True,
                                                    },
                                        label = T("Links"),
                                        name = "url",
                                        ),
                                    )

        s3db.configure("org_organisation",
                       filter_widgets = filter_widgets,
                       crud_form = crud_form,
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        # Custom rheader and tabs
        attr = dict(attr)
        attr["rheader"] = mavc_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        s3db = current.s3db

        # Custom filter widgets
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

        # Custom list fields
        list_fields = ["name",
                       "site_facility_type.facility_type_id",
                       "organisation_id",
                       "location_id",
                       "opening_times",
                       "contact",
                       "phone1",
                       "phone2",
                       "email",
                       #"website",
                       "obsolete",
                       #"comments",
                       ]

        s3db.configure(tablename,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

        # Customise fields
        table = s3db.org_facility

        # Main facility flag visible and in custom crud form
        field = table.main_facility
        field.readable = field.writable = True
        crud_form = s3db.get_config(tablename, "crud_form")
        crud_form.insert(-2, "main_facility")

        # "Obsolete" labeled as "inactive"
        field = table.obsolete
        field.label = T("Inactive")
        field.represent = lambda opt: T("Inactive") \
                                      if opt else current.messages["NONE"]
        field.readable = field.writable = True

        # Not using facility code
        field = table.code
        field.readable = field.writable = False

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_location_resource(r, tablename):

        table = current.s3db.org_organisation_location

        # Use location selector for "Areas served"
        from s3 import S3LocationSelector
        field = table.location_id
        field.widget = S3LocationSelector(levels = ["L1", "L2", "L3", "L4"],
                                          show_postcode = False,
                                          show_map = False,
                                          )

    settings.customise_org_organisation_location_resource = customise_org_organisation_location_resource
    # -------------------------------------------------------------------------
    def customise_org_service_location_resource(r, tablename):

        table = current.s3db.org_service_location

        # Hide site_id
        field = table.site_id
        field.readable = field.writable = False

        # Enable location_id
        from s3 import S3LocationSelector
        field = table.location_id
        field.readable = field.writable = True
        #field.widget = S3LocationSelector(levels = ["L1", "L2", "L3", "L4"],
        #                                  show_postcode = False,
        #                                  show_map = False,
        #                                  )

        # Custom CRUD form
        from s3 import S3SQLCustomForm, S3SQLInlineLink
        crud_form = S3SQLCustomForm(
                        "organisation_id",
                        "location_id",
                        S3SQLInlineLink("service",
                                        label = T("Services"),
                                        field = "service_id",
                                        ),
                        #"description",
                        "status",
                        "start_date",
                        #"end_date",
                        "comments",
                        )

        # List fields
        list_fields = ["organisation_id",
                       "location_id",
                       "service_location_service.service_id",
                       #"description",
                       "status",
                       "start_date",
                       #"end_date",
                       "comments",
                       ]

        # Configure
        current.s3db.configure("org_service_location",
                               crud_form = crud_form,
                               list_fields = list_fields,
                               )

    settings.customise_org_service_location_resource = customise_org_service_location_resource

    # =========================================================================
    # Contacts
    #
    settings.pr.request_dob = False
    settings.pr.contacts_tabs = None
    settings.pr.hide_third_gender = False

    # Uncomment to change the label for 'Staff'
    settings.hrm.staff_label = "Contacts"
    # Uncomment to disable Staff experience
    settings.hrm.staff_experience = False
    # Uncomment to disable the use of HR Credentials
    settings.hrm.use_credentials = False
    # Uncomment to disable the use of HR Skills
    settings.hrm.use_skills = False
    # Uncomment to disable the use of HR Teams
    settings.hrm.teams = False

    settings.hrm.use_id = False
    settings.hrm.use_description = None
    settings.hrm.use_address = False
    settings.hrm.use_trainings = False
    settings.hrm.use_certificates = False
    settings.hrm.record_tab = False

    settings.hrm.compose_button = False

    human_resource_list_fields = ["person_id",
                                  "job_title_id",
                                  "department_id",
                                  (T("Email"), "person_id$email.value"),
                                  (T("Mobile Phone"), "person_id$phone.value"),
                                  ]

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        s3db = current.s3db

        if r.interactive:
            # Custom CRUD form
            from s3 import S3SQLCustomForm
            crud_form = S3SQLCustomForm("organisation_id",
                                        "person_id",
                                        "job_title_id",
                                        "department_id",
                                        )

            # Custom filter widgets
            from s3 import S3TextFilter, S3OptionsFilter, s3_get_filter_opts
            filter_widgets = [
                S3TextFilter(["person_id$first_name",
                              "person_id$middle_name",
                              "person_id$last_name",
                              "person_id$email.value",
                              ],
                              label = T("Search"),
                              comment = T("You can search by name or email address."),
                             ),
                S3OptionsFilter("organisation_id",
                                filter = True,
                                header = "",
                                ),
                S3OptionsFilter("job_title_id",
                                options = s3_get_filter_opts("hrm_job_title"),
                                hidden = True,
                                ),
                ]

            s3db.configure("hrm_human_resource",
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           )

        # Configure table
        s3db.configure("hrm_human_resource",
                       list_fields = human_resource_list_fields,
                       )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -------------------------------------------------------------------------
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

            list_fields = ["organisation_id"] + human_resource_list_fields

            s3db.configure("hrm_human_resource",
                           list_fields = list_fields,
                           )

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        settings = current.deployment_settings

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            resource = r.resource

            if r.controller == "hrm":

                if r.interactive and not r.component:

                    MOBILE = settings.get_ui_label_mobile_phone()

                    # Custom form for contacts
                    from s3 import S3SQLCustomForm, \
                                   S3SQLInlineComponent, \
                                   S3SQLVerticalSubFormLayout
                    crud_form = S3SQLCustomForm(
                                    "first_name",
                                    "last_name",
                                    S3SQLInlineComponent(
                                            "human_resource",
                                            name = "human_resource",
                                            label = "",
                                            multiple = False,
                                            fields = ["organisation_id",
                                                      "job_title_id",
                                                      "department_id",
                                                      ],
                                            layout = S3SQLVerticalSubFormLayout,
                                            ),
                                    S3SQLInlineComponent(
                                            "contact",
                                            name = "email",
                                            label = T("Email"),
                                            #multiple = False,
                                            fields = [("", "value"),
                                                      ],
                                            filterby = [{"field": "contact_method",
                                                         "options": "EMAIL",
                                                         },
                                                        ],
                                            ),
                                    S3SQLInlineComponent(
                                            "contact",
                                            name = "phone",
                                            label = MOBILE,
                                            #multiple = False,
                                            fields = [("", "value"),
                                                      ],
                                            filterby = [{"field": "contact_method",
                                                         "options": "SMS",
                                                         },
                                                        ],
                                            ),
                                    )
                    resource.configure(crud_form = crud_form)
            return result
        s3.prep = custom_prep

        # Custom rheader and tabs
        attr = dict(attr)
        attr["rheader"] = mavc_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # =========================================================================
    # Inventory
    settings.inv.direct_stock_edits = True

    # =========================================================================
    # Projects
    #
    settings.project.mode_3w = True
    settings.project.mode_drr = True
    settings.project.hazards = True
    settings.project.themes = False
    settings.project.hfa = False
    settings.project.activities = True

    settings.project.multiple_organisations = True

    # Custom label for project organisation
    settings.project.organisation_roles = {1: T("Implementing Organization"),
                                           2: T("Partner Organization"),
                                           3: T("Donor"),
                                           }

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        s3db = current.s3db

        table = s3db.project_project

        # Make project description mandatory
        field = table.description
        from gluon import IS_NOT_EMPTY
        field.requires = IS_NOT_EMPTY(
                            error_message = T("Enter a project description"),
                            )

        if r.interactive:

            # Custom filter widgets
            LEAD_ROLE = settings.get_project_organisation_lead_role()
            org_label = settings.get_project_organisation_roles()[LEAD_ROLE]
            from s3 import S3DateFilter, \
                           S3LocationFilter, \
                           S3OptionsFilter, \
                           S3TextFilter
            filter_widgets = [
                S3TextFilter(["name",
                              "description",
                              ],
                              label = T("Search"),
                              comment = T("Search for a Project by name or description."),
                              ),
                S3LocationFilter("location.location_id",
                                 ),
                S3OptionsFilter("sector_project.sector_id",
                                label = T("Sector"),
                                location_filter = True,
                                none = True,
                                ),
                S3OptionsFilter("hazard_project.hazard_id",
                                label = T("Hazard"),
                                help_field = s3db.project_hazard_help_fields,
                                cols = 4,
                                hidden = True,
                                ),
                S3OptionsFilter("status_id",
                                label = T("Status"),
                                cols = 4,
                                hidden = True,
                                ),
                S3DateFilter("start_date",
                             hidden = True,
                             ),
                S3DateFilter("end_date",
                             hidden = True,
                             ),
                S3OptionsFilter("organisation_id",
                                label = org_label,
                                hidden = True,
                                ),
                ]

            # Custom CRUD form
            from s3 import S3SQLCustomForm, \
                           S3SQLInlineComponent, \
                           S3SQLInlineLink
            crud_form = S3SQLCustomForm(
                "organisation_id",
                "name",
                "description",
                "status_id",
                "start_date",
                "end_date",
                S3SQLInlineLink(
                    "hazard",
                    label = T("Hazards"),
                    field = "hazard_id",
                    help_field = s3db.project_hazard_help_fields,
                    cols = 4,
                    translate = True,
                ),
                S3SQLInlineLink(
                    "sector",
                    label = T("Sectors"),
                    field = "sector_id",
                    cols = 4,
                    translate = True,
                ),
                "objectives",
                (T("Funds available"), "budget"),
                "project_needs.funding",
                "currency",
                "project_needs.funding_details",
                #"project_needs.vol",
                #"project_needs.vol_details",
                "human_resource_id",
                S3SQLInlineComponent(
                    "document",
                    fields = [(T("Title"), "name"),
                              "file",
                              ],
                    filterby = {"field": "file",
                                "options": "",
                                "invert": True,
                                },
                    label = T("Files"),
                    name = "file",
                    ),
                S3SQLInlineComponent(
                    "document",
                    fields = [(T("Title"), "name"),
                              "url",
                              ],
                    filterby = {"field": "url",
                                "options": None,
                                "invert": True,
                                },
                    label = T("Links"),
                    name = "url",
                    ),
                "comments",
                )

            s3db.configure("project_project",
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           )

        # Custom list fields
        list_fields = ["name",
                       "location.location_id",
                       "organisation_id",
                       (T("Sectors"), "sector_project.sector_id"),
                       (T("Hazards"), "hazard_project.hazard_id"),
                       "status_id",
                       "start_date",
                       "end_date",
                       ]

        s3db.configure("project_project",
                       list_fields = list_fields,
                       )


    settings.customise_project_project_resource = customise_project_project_resource

    # -------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        # Custom rheader and tabs
        attr = dict(attr)
        attr["rheader"] = mavc_rheader

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

    # -------------------------------------------------------------------------
    def customise_project_location_resource(r, tablename):

        s3db = current.s3db
        table = s3db.project_location

        # Hide name in create-form
        field = table.name
        if r.tablename == tablename and not r.id or \
           r.component.tablename == tablename and not r.component_id:
            field.readable = False

        # Hide budget percentage
        field = table.percentage
        field.readable = field.writable = False

        # Use location selector
        field = table.location_id
        from s3 import S3LocationSelector
        field.widget = S3LocationSelector(show_address = False,
                                          show_postcode = False,
                                          show_map = False,
                                          )

        # Custom list fields
        list_fields = ["project_id",
                       "location_id",
                       "comments",
                       ]

        s3db.configure("project_location",
                       # Don't redirect to beneficiaries after create:
                       create_next = None,
                       list_fields = list_fields,
                       )


    settings.customise_project_location_resource = customise_project_location_resource

    # -------------------------------------------------------------------------
    def customise_project_activity_resource(r, tablename):

        s3db = current.s3db
        table = s3db.project_activity

        # Hide unwanted fields
        field = table.person_id
        field.readable = field.writable = False

        # Custom CRUD form
        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        if r.controller == "org":
            organisation_id = None
        else:
            organisation_id = S3SQLInlineLink("organisation",
                                              field = "organisation_id",
                                              multiple = False,
                                              )

        crud_form = S3SQLCustomForm("project_id",
                                    organisation_id,
                                    "name",
                                    #S3SQLInlineLink("activity_type",
                                    #                field = "activity_type_id",
                                    #                label = T("Activity Types"),
                                    #                ),
                                    S3SQLInlineComponent("distribution",
                                                         fields = ["parameter_id",
                                                                   "value",
                                                                   "comments",
                                                                   ],
                                                         label = T("Distributed Supplies"),
                                                         ),
                                    "location_id",
                                    "date",
                                    "end_date",
                                    "status_id",
                                    "comments",
                                    )

        # Custom list fields
        list_fields = ["project_id",
                       "name",
                       "location_id",
                       "date",
                       "end_date",
                       "status_id",
                       ]

        if organisation_id is not None:
            list_fields.insert(1, "activity_organisation.organisation_id")

        s3db.configure("project_activity",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )


    settings.customise_project_activity_resource = customise_project_activity_resource

    # -------------------------------------------------------------------------
    def customise_project_activity_controller(**attr):

        # Custom rheader and tabs
        attr = dict(attr)
        attr["rheader"] = mavc_rheader

        return attr

    settings.customise_project_activity_controller = customise_project_activity_controller

    # =========================================================================
    # Requests
    settings.req.req_type = ["Stock"]
    # Uncomment to disable the Commit step in the workflow & simply move direct to Ship
    settings.req.use_commit = False
    settings.req.requester_label = "Contact"
    # Uncomment if the User Account logging the Request is NOT normally the Requester
    settings.req.requester_is_author = False
    # Uncomment to have Donations include a 'Value' field
    settings.req.commit_value = True
    # Uncomment if the User Account logging the Commitment is NOT normally the Committer
    #settings.req.comittter_is_author = False
    # Uncomment to allow Donations to be made without a matching Request
    #settings.req.commit_without_request = True
    # Set the Requester as being an HR for the Site if no HR record yet & as Site contact if none yet exists
    settings.req.requester_to_site = True

    # =========================================================================
    # Comment/uncomment modules here to disable/enable them
    #
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
            module_type = 4,     # 4th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Stakeholder Network"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        ("hrm", Storage(
            name_nice = T("Contacts"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 0, # Accessed via org
        )),
        #("vol", Storage(
        #    name_nice = T("Volunteers"),
        #    #description = "Human Resources Management",
        #    restricted = True,
        #    module_type = 2,
        #)),
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
            module_type = None,
        )),
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        ("supply", Storage(
            name_nice = T("Supply Chain Management"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            restricted = True,
            module_type = None, # Not displayed
        )),
        ("inv", Storage(
            name_nice = T("Aid Delivery"),
            #description = "Receiving and Sending Items",
            restricted = True,
            module_type = 3
        )),
        ("req", Storage(
            name_nice = T("Requests for Aid"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = 2,
        )),
        ("project", Storage(
           name_nice = T("Projects"),
           #description = "Tracking of Projects, Activities and Tasks",
           restricted = True,
           module_type = 2
        )),
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("stats", Storage(
           name_nice = T("Statistics"),
           #description = "Manages statistics",
           restricted = True,
           module_type = None,
        )),
    ])

# =============================================================================
def mavc_rheader(r, tabs=None):
    """ Custom rheaders """

    if r.representation != "html":
        return None

    from s3 import s3_rheader_resource, s3_rheader_tabs
    from gluon import A, DIV, H1, H2, TAG

    tablename, record = s3_rheader_resource(r)
    if record is None:
        return None

    T = current.T
    s3db = current.s3db

    if tablename != r.tablename:
        resource = s3db.resource(tablename,
                                 id = record.id if record else None,
                                 )
    else:
        resource = r.resource

    rheader = ""

    if tablename == "org_organisation":

        # Tabs
        if not tabs:
            INDIVIDUALS = current.deployment_settings.get_hrm_staff_label()

            tabs = [(T("About"), None),
                    (INDIVIDUALS, "human_resource"),
                    (T("Services"), "service_location"),
                    (T("Facilities"), "facility"),
                    (T("Activities"), "activity"),
                    (T("Projects"), "project"),
                    (T("Attachments"), "document"),
                    ]

        # Use OrganisationRepresent for title to get L10n name if available
        represent = s3db.org_OrganisationRepresent(acronym=False,
                                                   parent=False,
                                                   )
        title = represent(record.id)

        # Retrieve details for the rheader
        data = resource.select(["organisation_organisation_type.organisation_type_id",
                                "country",
                                "website",
                                ],
                               raw_data = True,
                               represent = True,
                               )
        row = data.rows[0]
        raw = row["_row"]

        # Construct subtitle
        subtitle_fields = ("org_organisation_organisation_type.organisation_type_id",
                           "org_organisation.country",
                           )
        items = []
        for fname in subtitle_fields:
            if raw[fname]:
                items.append(s3_unicode(row[fname]))
        subtitle = ", ".join(items)

        # Website
        website = row["org_organisation.website"]

        # Compose the rheader
        rheader = DIV(DIV(H1(title),
                          H2(subtitle),
                          website if record.website else "",
                          _class="rheader-details",
                          ),
                      )

    elif tablename == "project_activity":

        if not tabs:
            tabs = [(T("Activity"), None),
                    (T("Attachments"), "document"),
                    ]

        # Retrieve details for the rheader
        data = resource.select(["activity_organisation.organisation_id",
                                "location_id",
                                ],
                               represent = True,
                               )
        row = data.rows[0]

        # Title and Subtitle
        title = row["project_activity_organisation.organisation_id"]
        subtitle = row["project_activity.location_id"]

        # Compose the rheader
        rheader = DIV(DIV(H1(title),
                          H2(subtitle),
                          _class="rheader-details",
                          ),
                      )

    elif tablename == "project_project":

        if not tabs:
            tabs = [(T("About"), None),
                    (T("Locations"), "location"),
                    (T("Partners and Donors"), "organisation"),
                    (T("Activities"), "activity"),
                    (T("Attachments"), "document"),
                    ]

        # Retrieve details for the rheader
        data = resource.select(["name",
                                "organisation_id",
                                ],
                               represent = True,
                               )
        row = data.rows[0]

        # Title and Subtitle
        title = row["project_project.name"]
        subtitle = row["project_project.organisation_id"]

        # Compose the rheader
        rheader = DIV(DIV(H1(title),
                          H2(subtitle),
                          _class="rheader-details",
                          ),
                      )

    elif tablename == "pr_person":

        if not tabs:
            tabs = [(T("Person Details"), None),
                    ]

        from s3 import s3_fullname
        title = s3_fullname(record)

        # Link organisation_id representation to staff tab
        linkto = URL(c = "org",
                     f = "organisation",
                     args = ["[id]", "human_resource"],
                     )
        htable = s3db.hrm_human_resource
        field = htable.organisation_id
        field.represent = s3db.org_OrganisationRepresent(show_link = True,
                                                         linkto = linkto,
                                                         )

        # Retrieve details for the rheader
        data = resource.select(["human_resource.job_title_id",
                                "human_resource.organisation_id",
                                ],
                               raw_data = True,
                               represent = True,
                               )
        row = data.rows[0]
        raw = row["_row"]

        # Construct subtitle
        organisation_id = raw["hrm_human_resource.organisation_id"]
        if organisation_id:
            subtitle = row["hrm_human_resource.organisation_id"]
            job_title_id = raw["hrm_human_resource.job_title_id"]
            if job_title_id:
                subtitle = TAG[""]("%s, " % row["hrm_human_resource.job_title_id"],
                                   subtitle,
                                   )

        # Compose the rheader
        rheader = DIV(DIV(H1(title),
                          H2(subtitle),
                          _class="rheader-details",
                          ),
                      )

    if tabs:
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader.append(rheader_tabs)

    return rheader

# END =========================================================================
