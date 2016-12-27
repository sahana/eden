# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, DIV, H3, IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY, SPAN, URL
from gluon.storage import Storage

def config(settings):
    """
        Settings for the SupportToLife deployment in Turkey
    """

    T = current.T

    settings.base.system_name = T("Beneficiary Data Management")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate += ("STL", "default/users", "STL/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "STL"

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
    settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
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
    # Case activities use service types
    settings.dvr.activity_use_service_type = True

    # Needs differentiated by service type, and hierarchical
    settings.dvr.needs_use_service_type = True
    settings.dvr.needs_hierarchical = True

    # Service type names
    INDIVIDUAL_SUPPORT = "Individual Support"
    MENTAL_HEALTH = "Mental Health"

    # Set DVR Default Label
    settings.dvr.label = "Beneficiary"

    # -------------------------------------------------------------------------
    def customise_dvr_home():
        """ Redirect dvr/index to dvr/person?closed=0 """

        from s3 import s3_redirect_default

        s3_redirect_default(URL(f="person", vars={"closed": "0"}))

    settings.customise_dvr_home = customise_dvr_home

    # -------------------------------------------------------------------------
    def customise_dvr_activity_controller(**attr):

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        T = current.T

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            table = r.table
            crud_strings = s3.crud_strings[r.tablename]

            from s3 import IS_ONE_OF, S3HierarchyWidget, FS, S3SQLCustomForm

            service_type = r.get_vars.get("service_type")
            if service_type == "MH":

                crud_strings["title_list"] = T("MH Group/Family Sessions")

                # Get service type ID
                stable = s3db.org_service
                query = (stable.parent == None) & \
                        (stable.name == MENTAL_HEALTH) & \
                        (stable.deleted != True)
                service = db(query).select(stable.id, limitby=(0, 1)).first()
                root_service_id = service.id if service else None

                # Filter activities
                query = (FS("service_id$root_service") == root_service_id)
                r.resource.add_filter(query)

                # Filter service selector
                field = table.service_id
                field.requires = IS_ONE_OF(db, "org_service.id",
                                           field.represent,
                                           filterby = "root_service",
                                           filter_opts = (root_service_id,),
                                           sort=True,
                                           )
                field.widget = S3HierarchyWidget(multiple = False,
                                                 leafonly = False,
                                                 filter = (FS("root_service") == root_service_id),
                                                 )

                # Adapt label for "facilitator"
                field = table.facilitator
                field.label = T("Counselor")

                # Expose gender type
                field = table.gender
                field.readable = field.writable = True

                # Custom list fields
                list_fields = ["name",
                               "service_id",
                               (T("Type of Group"), "group_type_id"),
                               "gender",
                               "age_group_id",
                               "facilitator",
                               "site_id",
                               "room_id",
                               ]

                # Custom form
                crud_form = S3SQLCustomForm("name",
                                            "service_id",
                                            (T("Type of Group"), "group_type_id"),
                                            "gender",
                                            "age_group_id",
                                            "facilitator",
                                            "site_id",
                                            "room_id",
                                            "comments",
                                            )

                s3db.configure("dvr_activity",
                               crud_form = crud_form,
                               list_fields = list_fields,
                               )

            elif service_type == "PSS":

                crud_strings["title_list"] = T("Group Activities")

                # Get service root types
                stable = s3db.org_service
                query = (stable.parent == None) & \
                        (stable.name != INDIVIDUAL_SUPPORT) & \
                        (stable.name != MENTAL_HEALTH) & \
                        (stable.deleted != True)
                rows = db(query).select(stable.id)
                root_service_ids = [row.id for row in rows]

                # Filter activities
                query = (FS("service_id$root_service").belongs(root_service_ids))
                if r.representation == "json":
                    today = r.utcnow.date()
                    start_date = FS("start_date")
                    end_date = FS("end_date")
                    query &= ((start_date == None) | (start_date <= today)) & \
                             ((end_date == None) | (end_date >= today))
                r.resource.add_filter(query)

                # Filter service selector
                field = table.service_id
                field.requires = IS_ONE_OF(db, "org_service.id",
                                           field.represent,
                                           filterby = "root_service",
                                           filter_opts = root_service_ids,
                                           sort=True,
                                           )
                field.widget = S3HierarchyWidget(multiple = False,
                                                 leafonly = False,
                                                 filter = (FS("root_service").belongs(root_service_ids)),
                                                 )

                # Expose gender type
                field = table.gender
                field.readable = field.writable = True

                # Custom list fields
                list_fields = ["service_id",
                               "start_date",
                               "end_date",
                               "period",
                               "gender",
                               "age_group_id",
                               "facilitator",
                               ]

                # Custom form
                crud_form = S3SQLCustomForm("service_id",
                                            "start_date",
                                            "end_date",
                                            "period",
                                            "gender",
                                            "age_group_id",
                                            "facilitator",
                                            "comments",
                                            )

                s3db.configure("dvr_activity",
                               crud_form = crud_form,
                               list_fields = list_fields,
                               )

            return result
        s3.prep = custom_prep

        # Make sure action buttons retain the service_type
        s3.crud.keep_vars = ("service_type",)

        return attr

    settings.customise_dvr_activity_controller = customise_dvr_activity_controller

    # -------------------------------------------------------------------------
    def customise_dvr_case_activity_resource(r, tablename):

        from s3 import FS, \
                       IS_ONE_OF, \
                       S3HierarchyWidget, \
                       S3Represent, \
                       S3SQLCustomForm, \
                       S3SQLInlineComponent, \
                       s3_comments_widget

        db = current.db
        s3db = current.s3db

        s3 = current.response.s3

        T = current.T

        component_name = r.component_name

        def expose_project_id(table):

            field = table.project_id
            field.readable = field.writable = True
            represent = S3Represent(lookup = "project_project",
                                    fields = ["code"],
                                    )
            field.represent = represent
            field.requires = IS_EMPTY_OR(IS_ONE_OF(db, "project_project.id",
                                                   represent,
                                                   ))
            field.comment = None
            field.label = T("Project Code")

        def expose_human_resource_id(table):

            field = table.human_resource_id
            field.label = T("Person Responsible")
            field.widget = None
            field.comment = None
            field.readable = field.writable = True

        if r.tablename == "dvr_activity":
            # "Cases" tab (activity perspective)

            # Show person_id as link
            catable = s3db.dvr_case_activity
            field = catable.person_id
            field.represent = s3db.pr_PersonRepresent(show_link=True)

            expose_project_id(catable)

            # Custom list fields
            list_fields = ["person_id$pe_label",
                           "person_id",
                           "need_id",
                           "project_id",
                           "followup",
                           "followup_date",
                           ]

            crud_form = S3SQLCustomForm("person_id",
                                        "need_id",
                                        "need_details",
                                        "project_id",
                                        "followup",
                                        "followup_date",
                                        "comments",
                                        )

            s3db.configure("dvr_case_activity",
                           insertable = False,
                           )

        elif r.component_name == "case_activity" or r.function == "due_followups":
            # "Individual Support" tab or "Due Follow-ups"

            # CRUD Strings use "Intervention"
            s3.crud_strings["dvr_case_activity"] = Storage(
                label_create = T("Create Intervention"),
                title_display = T("Intervention Details"),
                title_list = T("Interventions"),
                title_update = T("Edit Intervention"),
                label_list_button = T("List Interventions"),
                label_delete_button = T("Delete Intervention"),
                msg_record_created = T("Intervention added"),
                msg_record_modified = T("Intervention updated"),
                msg_record_deleted = T("Intervention deleted"),
                msg_list_empty = T("No Interventions currently registered"),
                )

            # Get service root type
            stable = s3db.org_service
            query = (stable.parent == None) & \
                    (stable.name == INDIVIDUAL_SUPPORT) & \
                    (stable.deleted != True)
            service = db(query).select(stable.id, limitby=(0, 1)).first()
            root_service_id = service.id if service else None

            if r.function == "due_followups":
                table = r.table
                # Filter activities by root service
                query = (FS("service_id$root_service") == root_service_id)
                r.resource.add_filter(query)
            else:
                table = r.component.table
                component = r.component

            expose_project_id(table)
            expose_human_resource_id(table)

            # Adjust validator and widget for service_id
            field = table.service_id
            field.requires = IS_ONE_OF(db, "org_service.id",
                                       field.represent,
                                       filterby = "root_service",
                                       filter_opts = (root_service_id,),
                                       sort=True,
                                       )
            field.widget = S3HierarchyWidget(multiple = False,
                                             leafonly = False,
                                             filter = (FS("root_service") == root_service_id),
                                             )

            # Filter need types
            ntable = s3db.dvr_need
            left = stable.on(stable.id == ntable.service_id)
            query = (stable.root_service == root_service_id) & \
                    (stable.deleted != True)

            field = table.need_id
            field.label = T("Sector for DS/IS")
            field.comment = None
            field.requires = IS_ONE_OF(db(query), "dvr_need.id",
                                       field.represent,
                                       left = left,
                                       )
            field.widget = S3HierarchyWidget(multiple = False,
                                             leafonly = False,
                                             filter = (FS("service_id$root_service") == root_service_id),
                                             )

            # Customise Need Details
            field = table.need_details
            field.label = T("DS/IS Case Explanation")
            field.readable = field.writable = True

            # Customise date fields
            field = table.start_date
            field.label = T("Opened on")
            field = table.end_date
            field.label = T("Closed on")
            field.readable = True

            # Customise "completed" flag
            # => label as "Status" and use drop-down for open/closed
            field = table.completed
            field.label = T("Status")
            field.represent = lambda v, row=None: T("Closed") if v else T("Open")
            field.requires = [IS_IN_SET([(False, T("Open")),
                                         (True, T("Closed")),
                                         ],
                                        zero=None,
                                        ),
                              # Form option is a str => convert to boolean
                              lambda v: (str(v) == "True", None),
                              ]
            from gluon.sqlhtml import OptionsWidget
            field.widget = OptionsWidget.widget

            # Customise SNF fields
            ftable = s3db.dvr_activity_funding
            field = ftable.funding_required
            field.label = T("Need for SNF")
            field = ftable.reason_id
            field.label = T("Justification for SNF")
            field.comment = None
            field = ftable.proposal
            field.label = T("Proposed Assistance for SNF")
            field.widget = s3_comments_widget

            # Custom CRUD form
            crud_form = S3SQLCustomForm("person_id",
                                        "service_id",
                                        "human_resource_id",
                                        "project_id",
                                        "need_id",
                                        "need_details",
                                        "start_date",
                                        "followup",
                                        "followup_date",
                                        "completed",
                                        "end_date",
                                        "activity_funding.funding_required",
                                        "activity_funding.reason_id",
                                        "activity_funding.proposal",
                                        S3SQLInlineComponent(
                                            "document",
                                            name = "file",
                                            label = T("Attachments"),
                                            fields = ["file", "comments"],
                                            filterby = {"field": "file",
                                                        "options": "",
                                                        "invert": True,
                                                        },
                                            ),
                                        "comments",
                                        )
            list_fields = ["person_id",
                           "service_id",
                           "human_resource_id",
                           "project_id",
                           "need_id",
                           "start_date",
                           "followup",
                           "followup_date",
                           "completed",
                           "end_date",
                           ]

        elif r.component_name == "pss_activity":
            # "PSS" tab
            table = r.component.table

            expose_project_id(table)

            # Get service root types
            stable = s3db.org_service
            query = (stable.parent == None) & \
                    (stable.name != INDIVIDUAL_SUPPORT) & \
                    (stable.name != MENTAL_HEALTH) & \
                    (stable.deleted != True)
            rows = db(query).select(stable.id)
            root_service_ids = [row.id for row in rows]

            # Filter service types
            field = table.service_id
            field.requires = IS_ONE_OF(db, "org_service.id",
                                       field.represent,
                                       filterby = "root_service",
                                       filter_opts = root_service_ids,
                                       sort=True,
                                       )
            field.widget = S3HierarchyWidget(multiple = False,
                                             leafonly = True,
                                             filter = (FS("root_service").belongs(root_service_ids)),
                                             )

            # Filter activities
            field = table.activity_id
            field.readable = field.writable = True
            today = r.utcnow.date()
            atable = s3db.dvr_activity
            stable = s3db.org_service
            left = stable.on(stable.id == atable.service_id)
            query = (stable.root_service.belongs(root_service_ids)) & \
                    ((atable.start_date == None) | (atable.start_date <= today)) & \
                    ((atable.end_date == None) | (atable.end_date >= today))
            field.requires = IS_EMPTY_OR(IS_ONE_OF(db(query), "dvr_activity.id",
                                                   field.represent,
                                                   left = left,
                                                   ))

            if r.interactive:
               script = '''$.filterOptionsS3({
'trigger':'service_id',
'target':'activity_id',
'lookupURL': S3.Ap.concat('/dvr/activity.json?service_type=PSS&~.service_id='),
'fncRepresent': function(r){return r.service_id+' ('+(r.start_date||'..')+' - '+(r.end_date||'..')+')'},
'optional': true
})'''
               s3.jquery_ready.append(script)

            # No follow-ups for PSS
            table.followup.default = False
            table.followup_date.default = None

            # Custom CRUD form
            crud_form = S3SQLCustomForm("person_id",
                                        "project_id",
                                        "service_id",
                                        "activity_id",
                                        "comments",
                                        )
            # Custom list fields
            list_fields = ["person_id",
                           "project_id",
                           "service_id",
                           "activity_id",
                           ]


        elif r.component_name == "mh_activity":
            # "Mental Health" tab
            table = r.component.table

            expose_project_id(table)
            expose_human_resource_id(table)

            # Get service root type
            stable = s3db.org_service
            query = (stable.parent == None) & \
                    (stable.name == MENTAL_HEALTH) & \
                    (stable.deleted != True)
            service = db(query).select(stable.id, limitby=(0, 1)).first()
            root_service_id = service.id if service else None

            # Filter service types
            field = table.service_id
            field.requires = IS_ONE_OF(db, "org_service.id",
                                       field.represent,
                                       filterby = "root_service",
                                       filter_opts = (root_service_id,),
                                       sort=True,
                                       )
            field.widget = S3HierarchyWidget(multiple = False,
                                            leafonly = True,
                                            filter = (FS("root_service") == root_service_id),
                                            )

            # Filter need types
            ntable = s3db.dvr_need
            left = stable.on(stable.id == ntable.service_id)
            query = (stable.root_service == root_service_id) & \
                    (stable.deleted != True)
            field = table.need_id
            field.label = T("MH Complaint Type")
            field.comment = None
            field.requires = IS_ONE_OF(db(query), "dvr_need.id",
                                       field.represent,
                                       left = left,
                                       )
            field.widget = S3HierarchyWidget(multiple = False,
                                             leafonly = False,
                                             filter = (FS("service_id$root_service") == root_service_id),
                                             )

            # Filter activities
            field = table.activity_id
            field.readable = field.writable = True
            atable = s3db.dvr_activity
            stable = s3db.org_service
            left = stable.on(stable.id == atable.service_id)
            query = (stable.root_service == root_service_id)
            field.requires = IS_EMPTY_OR(IS_ONE_OF(db(query), "dvr_activity.id",
                                                   field.represent,
                                                   left = left,
                                                   ))

            # Filter options for activity when service type selected
            if r.interactive:
                script = '''$.filterOptionsS3({
'trigger':'service_id',
'target':'activity_id',
'lookupURL': S3.Ap.concat('/dvr/activity.json?service_type=MH&~.service_id='),
'fncRepresent': function(r){return r.name||r.service_id},
'optional': true
})'''
                s3.jquery_ready.append(script)

            # No follow-ups for MH
            table.followup.default = False
            table.followup_date.default = None

            # Custom CRUD form
            crud_form = S3SQLCustomForm("person_id",
                                        "need_id",
                                        "service_id",
                                        "human_resource_id",
                                        "project_id",
                                        "activity_id",
                                        "comments",
                                        )

            # Custom list fields
            list_fields = ["person_id",
                           "need_id",
                           "service_id",
                           "human_resource_id",
                           "project_id",
                           "activity_id",
                           ]

        else:
            # Activity list
            expose_project_id(s3db.dvr_case_activity)

            crud_form = S3SQLCustomForm("person_id",
                                        "project_id",
                                        "service_id",
                                        "need_id",
                                        "followup",
                                        "followup_date",
                                        "activity_funding.funding_required",
                                        "activity_funding.reason_id",
                                        "activity_funding.proposal",
                                        "comments",
                                        )
            # Custom list fields
            list_fields = ["person_id",
                           "project_id",
                           "service_id",
                           "followup",
                           "followup_date",
                           ]

        s3db.configure("dvr_case_activity",
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_dvr_case_activity_resource = customise_dvr_case_activity_resource

    # -------------------------------------------------------------------------
    def customise_dvr_case_activity_controller(**attr):

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

            if r.function == "due_followups":

                crud_strings = s3.crud_strings["dvr_case_activity"]
                crud_strings["title_list"] = T("Interventions to follow-up")

                # Show person_id as link to case
                table = r.resource.table
                table.person_id.represent = s3db.pr_PersonRepresent(show_link=True)

                # Custom list fields
                list_fields = [(T("ID"), "person_id$pe_label"),
                               "person_id",
                               (T("Sector for DS/IS"), "need_id"),
                               "service_id",
                               "followup_date",
                               ]

                # Custom filter widgets
                from s3 import S3TextFilter, S3DateFilter
                filter_widgets = [S3TextFilter(["person_id$pe_label",
                                                "person_id$first_name",
                                                "person_id$last_name",
                                                "need_id$name",
                                                "service_id$name",
                                                ],
                                                label = T("Search"),
                                                ),
                                  S3DateFilter("followup_date",
                                               cols = 2,
                                               hidden = True,
                                               ),
                                  ]

                r.resource.configure(filter_widgets = filter_widgets,
                                     list_fields = list_fields,
                                     )


            return result
        s3.prep = custom_prep

        return attr

    settings.customise_dvr_case_activity_controller = customise_dvr_case_activity_controller

    # -------------------------------------------------------------------------
    def customise_dvr_activity_funding_reason_resource(r, tablename):

        T = current.T

        table = current.s3db.dvr_activity_funding_reason

        field = table.name
        field.label = T("SNF Justification")

        crud_strings = current.response.s3.crud_strings

        # CRUD Strings
        crud_strings["dvr_activity_funding_reason"] = Storage(
            label_create = T("Create SNF Justification"),
            title_display = T("SNF Justification"),
            title_list = T("SNF Justifications"),
            title_update = T("Edit SNF Justification"),
            label_list_button = T("List SNF Justifications"),
            label_delete_button = T("Delete SNF Justification"),
            msg_record_created = T("SNF Justification created"),
            msg_record_modified = T("SNF Justification updated"),
            msg_record_deleted = T("SNF Justification deleted"),
            msg_list_empty = T("No SNF Justifications currently defined"),
        )


    settings.customise_dvr_activity_funding_reason_resource = customise_dvr_activity_funding_reason_resource

    # -------------------------------------------------------------------------
    def customise_dvr_activity_funding_resource(r, tablename):

        T = current.T

        table = current.s3db.dvr_activity_funding
        field = table.funding_required
        field.label = T("Need for SNF")
        field = table.reason_id
        field.label = T("Justification for SNF")
        field = table.proposal
        field.label = T("Proposed Assistance for SNF")

    settings.customise_dvr_activity_funding_resource = customise_dvr_activity_funding_resource

    # -------------------------------------------------------------------------
    def customise_dvr_economy_resource(r, tablename):

        table = current.s3db.dvr_economy
        field = table.monthly_costs

        field.label = current.T("Monthly Rent Expense")

    settings.customise_dvr_economy_resource = customise_dvr_economy_resource

    # -------------------------------------------------------------------------
    def customise_dvr_household_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineComponent

        crud_form = S3SQLCustomForm("hoh_relationship",
                                    "hoh_name",
                                    "hoh_date_of_birth",
                                    "hoh_gender",
                                    S3SQLInlineComponent("beneficiary_data",
                                                         fields = [(T("Age Group"), "beneficiary_type_id"),
                                                                   "female",
                                                                   "male",
                                                                   "other",
                                                                   "out_of_school",
                                                                   (T("Number Working"), "employed"),
                                                                   ],
                                                         label = T("Household Members"),
                                                         explicit_add = T("Add Household Members"),
                                                         ),
                                    "comments",
                                    )

        current.s3db.configure("dvr_household",
                               crud_form = crud_form,
                               )

    settings.customise_dvr_household_resource = customise_dvr_household_resource

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

        if r.controller == "dvr":

            from s3 import IS_PERSON_GENDER

            table = s3db.pr_person

            # ID label is required, remove tooltip
            field = table.pe_label
            field.comment = None
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # Last name is required
            field = table.last_name
            field.requires = IS_NOT_EMPTY()

            # Date of Birth is required
            field = table.date_of_birth
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

            # Gender is required, remove "unknown" option, adjust label
            field = table.gender
            field.label = current.T("Gender")
            field.default = None
            options = dict(s3db.pr_gender_opts)
            del options[1] # Remove "unknown"
            field.requires = IS_PERSON_GENDER(options, sort=True)

            dtable = s3db.pr_person_details

            # Nationality is required, default is Syrian
            field = dtable.nationality
            field.default = "SY"
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        # Get service IDs
        stable = s3db.org_service
        query = (stable.deleted != True)
        rows = db(query).select(stable.id,
                                stable.name,
                                stable.parent,
                                stable.root_service,
                                cache = s3db.cache,
                                orderby = stable.root_service,
                                )

        # Group service IDs by root service
        mh_service_ids = []
        is_service_ids = []
        pss_service_ids = []
        service_ids = pss_service_ids
        group = set()
        root_service = None
        for row in rows:
            if row.parent is None:
                name = row.name
                if name == INDIVIDUAL_SUPPORT:
                    service_ids = is_service_ids
                elif name == MENTAL_HEALTH:
                    service_ids = mh_service_ids
                else:
                    # Everything else is PSS
                    service_ids = pss_service_ids
            if row.root_service != root_service:
                if group:
                    service_ids.extend(group)
                group = set()
                root_service = row.root_service
            group.add(row.id)
        service_ids.extend(group)

        # Custom activity components (differentiated by service type)
        s3db.add_components("pr_person",
                            dvr_case_activity = (
                                {"name": "case_activity",
                                    "joinby": "person_id",
                                    "filterby": {
                                        "service_id": is_service_ids,
                                        },
                                },
                                {"name": "mh_activity",
                                    "joinby": "person_id",
                                    "filterby": {
                                        "service_id": mh_service_ids,
                                        },
                                },
                                {"name": "pss_activity",
                                    "joinby": "person_id",
                                    "filterby": {
                                        "service_id": pss_service_ids,
                                        },
                                },
                               ),
                            )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            controller = r.controller

            archived = r.get_vars.get("archived")
            if archived in ("1", "true", "yes"):
                crud_strings = s3.crud_strings["pr_person"]
                crud_strings["title_list"] = T("Invalid Cases")

            if controller == "dvr":
                if not r.component:

                    from s3 import IS_ONE_OF, S3HierarchyWidget

                    ctable = s3db.dvr_case

                    # Remove empty option from case status selector
                    field = ctable.status_id
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires = requires.other
                        requires.zero = None

                    # Hierarchical Organisation Selector
                    field = ctable.organisation_id
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires.other
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

                    # Visibility and tooltip for consent flag, make mandatory
                    field = ctable.disclosure_consent
                    field.readable = field.writable = True
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires.other
                    field.comment = DIV(_class="tooltip",
                                        _title="%s|%s" % (T("Consenting to Data Disclosure"),
                                                          T("Is the client consenting to disclosure of their data towards partner organisations and authorities?"),
                                                          ),
                                        )

                    dtable = s3db.dvr_case_details

                    # Custom label for registered-flag
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
                                        "dvr_case.status_id",
                                        "dvr_case.date",
                                        "dvr_case.organisation_id",
                                        "dvr_case.human_resource_id",
                                        "first_name",
                                        #"middle_name",
                                        "last_name",
                                        "person_details.nationality",
                                        "case_details.arrival_date",
                                        "date_of_birth",
                                        "gender",
                                        "person_details.marital_status",
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
                                                required = True,
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
                                        "dvr_case.disclosure_consent",
                                        "dvr_case.comments",
                                        (T("Invalid Record"), "dvr_case.archived"),
                                        )

                        resource.configure(crud_form = crud_form,
                                           )

                        # Extend text filter with Family ID and case comments
                        filter_widgets = resource.get_config("filter_widgets")
                        extend_text_filter = True
                        for fw in filter_widgets:
                            if fw.field == "dvr_case.status_id":
                                if fw.field == "dvr_case.status_id" and "closed" in r.get_vars:
                                    fw.opts.default = None
                                    fw.opts.hidden = True
                            if extend_text_filter and isinstance(fw, S3TextFilter):
                                fw.field.extend(("family_id.value",
                                                 "dvr_case.comments",
                                                 ))
                                fw.opts.comment = T("You can search by name, ID, family ID and comments")
                                extend_text_filter = False

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

                elif r.component_name == "evaluation":

                    s3.stylesheets.append("../themes/STL/evaluation.css")

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
    settings.org.services_hierarchical = True

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

    # -------------------------------------------------------------------------
    def customise_org_facility_controller(**attr):

        s3db = current.s3db

        s3db.add_components("org_facility",
                            org_room = "site_id",
                            )

        # Custom rheader
        attr = dict(attr)
        attr["rheader"] = stl_org_rheader

        return attr

    settings.customise_org_facility_controller = customise_org_facility_controller

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

            # "Invalid Case" warning
            hint = lambda record: H3(T("Invalid Case"),
                                     _class="alert label",
                                     )

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Contact"), "contacts"),
                        (T("Household"), "household"),
                        (T("Economy"), "economy"),
                        (T("Individual Case Management"), "case_activity"),
                        (T("Group Activities"), "pss_activity"),
                        (T("Mental Health"), "mh_activity"),
                        (T("Evaluation"), "evaluation"),
                        ]

                case = resource.select(["family_id.value",
                                        "dvr_case.status_id",
                                        "dvr_case.archived",
                                        "dvr_case.organisation_id",
                                        "dvr_case.disclosure_consent",
                                        ],
                                        represent = True,
                                        raw_data = True,
                                        ).rows

                if not case:
                    return None

                case = case[0]

                case_status = lambda row: case["dvr_case.status_id"]
                archived = case["_row"]["dvr_case.archived"]
                family_id = lambda row: case["pr_family_id_person_tag.value"]
                organisation_id = lambda row: case["dvr_case.organisation_id"]
                name = lambda row: s3_fullname(row)

                raw = case._row

                # Render disclosure consent flag as colored label
                consent = raw["dvr_case.disclosure_consent"]
                labels = {"Y": "success", "N/A": "warning", "N": "alert"}
                def disclosure(row):
                    _class = labels.get(consent, "secondary")
                    return SPAN(case["dvr_case.disclosure_consent"],
                                _class = "%s label" % _class,
                                )

                rheader_fields = [[(T("ID"), "pe_label"),
                                   (T("Case Status"), case_status),
                                   (T("Data Disclosure"), disclosure),
                                   ],
                                  [(T("Family ID"), family_id),
                                   (T("Organisation"), organisation_id),
                                   ],
                                  [(T("Name"), name),
                                   ],
                                  ["date_of_birth",
                                   ],
                                  ]

                if archived:
                    rheader_fields.insert(0, [(None, hint)])

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

# =============================================================================
def stl_org_rheader(r, tabs=[]):
    """ ORG custom resource headers """

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

        if tablename == "org_facility":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Rooms"), "room"),
                        ]

                def facility_type_lookup(record):
                    db = current.db
                    ltable = db.org_site_facility_type
                    ttable = db.org_facility_type
                    query = (ltable.site_id == record.site_id) & \
                            (ltable.facility_type_id == ttable.id)
                    rows = db(query).select(ttable.name)
                    if rows:
                        return ", ".join([row.name for row in rows])
                    else:
                        return current.messages["NONE"]

                rheader_fields = [["name", "organisation_id", "email"],
                                  [(T("Facility Type"), facility_type_lookup),
                                   "location_id", "phone1"],
                                  ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )

    return rheader

# END =========================================================================
