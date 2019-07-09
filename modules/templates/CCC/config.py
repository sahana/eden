# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Cumbria County Council extensions to the Volunteer Management template
        - branding
        - support Donations
        - support Assessments
    """

    T = current.T

    settings.base.system_name = T("Support Cumbria")
    settings.base.system_name_short = T("Support Cumbria")

    # Theme
    settings.base.theme = "CCC"
    settings.base.theme_layouts = "CCC"
    settings.base.theme_config = "CCC"

    # PrePopulate data
    settings.base.prepopulate += ("CCC",)
    settings.base.prepopulate_demo = ("CCC/Demo",)

    # Authentication settings
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    # - varies by path (see customise_auth_user_controller)
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    settings.auth.registration_link_user_to = ["staff"]
    settings.auth.registration_link_user_to_default = ["staff"]

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages = OrderedDict([
        ("en-gb", "English"),
    ])
    # Default Language
    settings.L10n.default_language = "en-gb"
    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False

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

    settings.security.policy = 7 # Organisation-ACLs

    # Consent Tracking
    settings.auth.consent_tracking = True

    # Record Approval
    settings.auth.record_approval = True
    settings.auth.record_approval_required_for = ("org_organisation",
                                                  )

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    #settings.modules.update([
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
            module_type = None,
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = None,
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = None,
        )),
        ("hrm", Storage(
            name_nice = T("Personnel"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = None,
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
        #("cr", Storage(
        #    name_nice = T("Shelters"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #    restricted = True,
        #    module_type = 10
        #)),
        ("dc", Storage(
            name_nice = T("Assessments"),
            #description = "Data collection tool",
            restricted = True,
            module_type = None,
        )),
        ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tasks for Contacts",
            restricted = True,
            module_type = None,
        )),
        ("supply", Storage(
            name_nice = T("Supply Chain Management"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            restricted = True,
            module_type = None, # Not displayed
        )),
        #("inv", Storage(
        #    name_nice = T("Warehouses"),
        #    #description = "Receiving and Sending Items",
        #    restricted = True,
        #    module_type = None,
        #)),
        ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = None,
        )),
    ])

    settings.search.filter_manager = False
    settings.ui.filter_clear = False

    settings.cms.richtext = True

    settings.hrm.event_course_mandatory = False

    settings.project.task_priority_opts = {1: T("Low"),
                                           2: T("Medium"),
                                           3: T("High"),
                                           }
    settings.project.task_status_opts = {1: T("New"),
                                         2: T("In-Progress"),
                                         3: T("Closed"),
                                         }

    # Now using req_need, so unused:
    #settings.req.req_type = ("People",)

    def ccc_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        tablename = table._tablename

        if tablename in ("hrm_training_event",
                         "project_task",
                         "req_need",
                         ):
            # Use the Org of the Creator
            db = current.db
            new_row = db(table.id == row.id).select(table.created_by,
                                                    limitby = (0, 1),
                                                    ).first()
            user_id = new_row.created_by

            utable = db.auth_user
            otable = current.s3db.org_organisation
            query = (utable.id == user_id) & \
                    (utable.organisation_id == otable.id)
            org = db(query).select(otable.pe_id,
                                   limitby = (0, 1),
                                   ).first()
            if org:
                return org.pe_id

        # Use default rules
        return 0

    settings.auth.realm_entity = ccc_realm_entity

    # -------------------------------------------------------------------------
    def ccc_rheader(r):
        """
            Custom rheaders
        """

        if r.representation != "html":
            # RHeaders only used in interactive views
            return None

        # Need to use this format as otherwise req_match?viewing=org_office.x
        # doesn't have an rheader
        from s3 import s3_rheader_resource, s3_rheader_tabs
        tablename, record = s3_rheader_resource(r)

        if record is None:
            # List or Create form: rheader makes no sense here
            return None

        from gluon import DIV, TABLE, TR, TH

        T = current.T

        if tablename == "hrm_training_event":
            T = current.T
            tabs = [(T("Basic Details"), None),
                    (T("Participants"), "participant"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            location_id = table.location_id
            date_field = table.start_date
            rheader = DIV(TABLE(TR(TH("%s: " % T("Date")),
                                   date_field.represent(record.start_date),
                                   ),
                                TR(TH("%s: " % location_id.label),
                                   location_id.represent(record.location_id),
                                   )),
                          rheader_tabs)

        elif tablename == "pr_person":
            T = current.T
            tabs = [(T("Basic Details"), None),
                    (T("Address"), "address"),
                    (T("Contacts"), "contacts"),
                    (T("Skills"), "competency"),
                    ]
            if current.auth.s3_has_role("ORG_ADMIN"):
                tabs.insert(1, (T("Affiliation"), "human_resource"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            from s3 import s3_fullname

            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                   s3_fullname(record),
                                   )),
                          rheader_tabs)

        elif tablename == "req_need":
            T = current.T
            tabs = [(T("Basic Details"), None),
                    #(T("Items"), "need_item"),
                    (T("Skills"), "need_skill"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            location_id = table.location_id
            date_field = table.date
            rheader = DIV(TABLE(TR(TH("%s: " % date_field.label),
                                   date_field.represent(record.date),
                                   ),
                                TR(TH("%s: " % location_id.label),
                                   location_id.represent(record.location_id),
                                   )),
                          rheader_tabs)

        return rheader

    # -------------------------------------------------------------------------
    def customise_auth_user_controller(**attr):

        if current.request.args(0) == "register":
            # Not easy to tweak the URL in the login form's buttons
            from gluon import redirect, URL
            redirect(URL(c="default", f="index",
                         args="register",
                         vars=current.request.get_vars))

        return attr

    settings.customise_auth_user_controller = customise_auth_user_controller

    # -------------------------------------------------------------------------
    def customise_cms_post_resource(r, tablename):

        from gluon import URL
        from s3 import S3SQLCustomForm, S3TextFilter

        #from templates.CCC.controllers import cms_post_list_layout

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Information"),
        #    title_display = T("Guide Details"),
            title_list = "",
        #    title_update = T("Edit Guide"),
        #    #title_upload = T("Import Guides"),
        #    label_list_button = T("List Guides"),
        #    label_delete_button = T("Delete Guide"),
        #    msg_record_created = T("Guide added"),
        #    msg_record_modified = T("Guide updated"),
        #    msg_record_deleted = T("Guide deleted"),
        #    msg_list_empty = T("No Guides currently registered")
        )

        s3db = current.s3db
        #f = s3db.cms_post.series_id
        #f.label = T("Category")
        #f.readable = f.writable = True

        s3db.configure("cms_post",
                       create_next = URL(args="datalist"),
                       crud_form = S3SQLCustomForm(#"series_id",
                                                   "title",
                                                   "body",
                                                   ),
                       list_fields = [#"series_id",
                                      "title",
                                      "body",
                                      "date",
                                      ],
                       #list_layout = cms_post_list_layout,
                       filter_widgets = [S3TextFilter(["title",
                                                       #"series_id",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search"),
                                                      ),
                                         ],
                       )

    settings.customise_cms_post_resource = customise_cms_post_resource

    # -----------------------------------------------------------------------------
    def customise_cms_post_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.method == "datalist":
                # Filter out system posts
                from s3 import FS
                r.resource.add_filter(FS("post_module.module") == None)

            return result
        s3.prep = prep

        s3.dl_no_header = True
        #attr["dl_rowsize"] = 2

        return attr

    settings.customise_cms_post_controller = customise_cms_post_controller

    # -------------------------------------------------------------------------
    def customise_doc_document_resource(r, tablename):

        from gluon import URL
        from s3 import S3SQLCustomForm, S3TextFilter

        #from templates.CCC.controllers import doc_document_list_layout

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Document"),
        #    title_display = T("Guide Details"),
            title_list = "",
        #    title_update = T("Edit Guide"),
        #    #title_upload = T("Import Guides"),
        #    label_list_button = T("List Guides"),
        #    label_delete_button = T("Delete Guide"),
        #    msg_record_created = T("Guide added"),
        #    msg_record_modified = T("Guide updated"),
        #    msg_record_deleted = T("Guide deleted"),
        #    msg_list_empty = T("No Guides currently registered")
        )

        s3db = current.s3db

        f = s3db.doc_document.organisation_id
        user = current.auth.user
        organisation_id = user and user.organisation_id
        if organisation_id:
            f.default = organisation_id
        else:
            f.readable = f.writable = True

        s3db.configure("doc_document",
                       create_next = URL(args="datalist"),
                       crud_form = S3SQLCustomForm("organisation_id",
                                                   "name",
                                                   "file",
                                                   "comments",
                                                   ),
                       list_fields = ["organisation_id",
                                      "name",
                                      "file",
                                      "comments",
                                      ],
                       #list_layout = doc_document_list_layout,
                       filter_widgets = [S3TextFilter(["name",
                                                       "organisation_id",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search"),
                                                      ),
                                         ],
                       )

    settings.customise_doc_document_resource = customise_doc_document_resource

    # -----------------------------------------------------------------------------
    def customise_doc_document_controller(**attr):

        current.response.s3.dl_no_header = True

        return attr

    settings.customise_doc_document_controller = customise_doc_document_controller

    # -------------------------------------------------------------------------
    def customise_hrm_competency_resource(r, tablename):

        s3db = current.s3db

        table = s3db.hrm_competency
        table.competency_id.readable = table.competency_id.writable = False
        table.organisation_id.readable = table.organisation_id.writable = False

        s3db.configure("hrm_competency",
                       list_fields = ["skill_id",
                                      "comments",
                                      ],
                       )

    settings.customise_hrm_competency_resource = customise_hrm_competency_resource

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3TextFilter

        s3db = current.s3db

        table = s3db.hrm_human_resource

        if r.controller == "default":
            list_fields = ["job_title_id",
                           ]
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("New Affiliation"),
                title_display = T("Affiliation Details"),
                title_list = T("Affiliations"),
                title_update = T("Edit Affiliation"),
                #title_upload = T("Import Affiliations"),
                label_list_button = T("List Affiliations"),
                label_delete_button = T("Delete Affiliation"),
                msg_record_created = T("Affiliation added"),
                msg_record_modified = T("Affiliation updated"),
                msg_record_deleted = T("Affiliation deleted"),
                msg_list_empty = T("No Affiliations currently registered")
            )
        else:
            list_fields = ["person_id",
                           "job_title_id",
                           (T("Skills"), "person_id$competency.skill_id"),
                           (T("Email"), "email.value"),
                           (T("Mobile Phone"), "phone.value"),
                           ]
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("New Volunteer"),
                title_display = T("Volunteer Details"),
                title_list = T("Volunteers"),
                title_update = T("Edit Volunteer"),
                #title_upload = T("Import Volunteers"),
                label_list_button = T("List Volunteers"),
                label_delete_button = T("Delete Volunteer"),
                msg_record_created = T("Volunteer added"),
                msg_record_modified = T("Volunteer updated"),
                msg_record_deleted = T("Volunteer deleted"),
                msg_list_empty = T("No Volunteers currently registered")
            )
        filter_fields = ["person_id$first_name",
                         "person_id$middle_name",
                         "person_id$last_name",
                         "job_title_id$name",
                         "comments",
                         ]
        if current.auth.s3_has_role("ADMIN"):
            list_fields.insert(0, "organisation_id")
            filter_fields.insert(0, "organisation_id$name")
        else:
            table.organisation_id.writable = False
            table.organisation_id.comment = None # No Create
                       
        s3db.configure("hrm_human_resource",
                       crud_form = S3SQLCustomForm("organisation_id",
                                                   "job_title_id",
                                                   "person_id",
                                                   "comments",
                                                   ),
                       list_fields = list_fields,
                       filter_widgets = [S3TextFilter(filter_fields,
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search"),
                                                      ),
                                         ],
                       )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_resource(r, tablename):

        from s3 import S3LocationSelector, S3OptionsFilter, S3SQLCustomForm, S3TextFilter

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("New Event"),
            title_display = T("Event Details"),
            title_list = T("Events"),
            title_update = T("Edit Event"),
            #title_upload = T("Import Events"),
            label_list_button = T("List Events"),
            label_delete_button = T("Delete Event"),
            msg_record_created = T("Event added"),
            msg_record_modified = T("Event updated"),
            msg_record_deleted = T("Event deleted"),
            msg_list_empty = T("No Events currently registered")
        )

        s3db = current.s3db

        table = s3db.hrm_training_event
        table.name.readable = table.name.writable = True
        f = table.location_id
        f.readable = f.writable = True
        f.widget = S3LocationSelector(show_address = True)

        s3db.configure("hrm_training_event",
                       crud_form = S3SQLCustomForm("name",
                                                   "start_date",
                                                   #"end_date",
                                                   "location_id",
                                                   "comments",
                                                   ),
                       list_fields = ["start_date",
                                      "name",
                                      "location_id",
                                      ],
                       filter_widgets = [S3TextFilter(["name",
                                                       "comments",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search"),
                                                      ),
                                         ],
                       )

    settings.customise_hrm_training_event_resource = customise_hrm_training_event_resource

    # -----------------------------------------------------------------------------
    def customise_hrm_training_event_controller(**attr):

        attr["rheader"] = ccc_rheader

        return attr

    settings.customise_hrm_training_event_controller = customise_hrm_training_event_controller

    # -----------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            s3.crud_strings[r.tablename] = Storage(
                label_create = T("New Volunteer"),
                title_display = T("Volunteer Details"),
                title_list = T("Volunteers"),
                title_update = T("Edit Volunteer"),
                #title_upload = T("Import Volunteers"),
                label_list_button = T("List Volunteers"),
                label_delete_button = T("Delete Volunteer"),
                msg_record_created = T("Volunteer added"),
                msg_record_modified = T("Volunteer updated"),
                msg_record_deleted = T("Volunteer deleted"),
                msg_list_empty = T("No Volunteers currently registered")
            )

            return result
        s3.prep = prep
        
        attr["rheader"] = ccc_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def customise_project_task_resource(r, tablename):

        from s3 import S3OptionsFilter, S3SQLCustomForm, S3TextFilter

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("New Message"),
            title_display = T("Message Details"),
            title_list = T("Messages"),
            title_update = T("Edit Message"),
            #title_upload = T("Import Messages"),
            label_list_button = T("List Messages"),
            label_delete_button = T("Delete Message"),
            msg_record_created = T("Message added"),
            msg_record_modified = T("Message updated"),
            msg_record_deleted = T("Message deleted"),
            msg_list_empty = T("No Messages currently created")
        )

        s3db = current.s3db

        table = s3db.project_task
        table.name.label = T("Subject")
        table.description.label = T("Message")
        if current.auth.s3_has_role("ORG_ADMIN"):
            # @ToDo: Filter Assigned To to just OrgAdmins?
            pass
        else:
            f = table.priority
            f.default = 1
            f.readable = f.writable = False
            f = table.status
            f.default = 1
            f.readable = f.writable = False
            table.pe_id.readable = table.pe_id.writable = False
            table.comments.readable = table.comments.writable = False

        s3db.configure("project_task",
                       crud_form = S3SQLCustomForm("name",
                                                   "description",
                                                   "priority",
                                                   "status",
                                                   "pe_id",
                                                   "comments",
                                                   ),
                       list_fields = ["priority",
                                      "status",
                                      "pe_id",
                                      "created_by",
                                      "name",
                                      ],
                       filter_widgets = [S3TextFilter(["name",
                                                       "description",
                                                       "comments",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search"),
                                                      ),
                                         S3OptionsFilter("priority",
                                                         options = settings.get_project_task_priority_opts(),
                                                         cols = 3,
                                         ),
                                         S3OptionsFilter("status",
                                                         options = settings.get_project_task_status_opts(),
                                                         cols = 3,
                                         ),
                                        ],
                       )

    settings.customise_project_task_resource = customise_project_task_resource

    # -----------------------------------------------------------------------------
    def customise_project_task_controller(**attr):

        if current.auth.s3_has_role("ORG_ADMIN"):
            # @ToDo: Default filter to hide Closed messages
            pass
        else:
            s3 = current.response.s3

            # Custom prep
            standard_prep = s3.prep
            def prep(r):
                # Call standard prep
                if callable(standard_prep):
                    result = standard_prep(r)
                else:
                    result = True

                if r.method not in ("create", "read", "update"):
                    from gluon import redirect
                    redirect(r.url(method="create"))
                else:
                    current.messages.UPDATE = "Edit"
                    # Don't attempt to load comments
                    s3.rfooter = None

                return result
            s3.prep = prep

            # Custom postp
            standard_postp = s3.postp
            def postp(r, output):
                # Call standard postp
                if callable(standard_postp):
                    output = standard_postp(r, output)

                if r.method == "read" and "buttons" in output:
                    output["buttons"].pop("list_btn")

                return output
            s3.postp = postp

        attr["rheader"] = None

        return attr

    settings.customise_project_task_controller = customise_project_task_controller

    # -------------------------------------------------------------------------
    def customise_req_need_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3TextFilter

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("New Opportunity"),
            title_display = T("Opportunity Details"),
            title_list = T("Opportunities"),
            title_update = T("Edit Opportunity"),
            #title_upload = T("Import Opportunities"),
            label_list_button = T("List Opportunities"),
            label_delete_button = T("Delete Opportunity"),
            msg_record_created = T("Opportunity added"),
            msg_record_modified = T("Opportunity updated"),
            msg_record_deleted = T("Opportunity deleted"),
            msg_list_empty = T("No Opportunities currently registered")
        )

        s3db = current.s3db

        table = s3db.req_need

        s3db.configure("req_need",
                       crud_form = S3SQLCustomForm("date",
                                                   "location_id",
                                                   "name",
                                                   "comments",
                                                   ),
                       list_fields = ["date",
                                      "location_id",
                                      (T("Opportunity"), "name"),
                                      ],
                       filter_widgets = [S3TextFilter(["name",
                                                       "comments",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search"),
                                                      ),
                                         ],
                       )

    settings.customise_req_need_resource = customise_req_need_resource

    # -----------------------------------------------------------------------------
    def customise_req_need_controller(**attr):

        attr["rheader"] = ccc_rheader

        return attr

    settings.customise_req_need_controller = customise_req_need_controller

# END =========================================================================
