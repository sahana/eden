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
    # - varies by path (see register() in controllers.py)
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

    settings.pr.hide_third_gender = False

    #settings.project.task_priority_opts = {1: T("Low"),
    #                                       2: T("Medium"),
    #                                       3: T("High"),
    #                                       }
    #settings.project.task_status_opts = {1: T("New"),
    #                                     2: T("In-Progress"),
    #                                     3: T("Closed"),
    #                                     }

    # Now using req_need, so unused:
    #settings.req.req_type = ("People",)

    # -------------------------------------------------------------------------
    def ccc_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        if current.auth.s3_has_role("ADMIN"):
            # Use default rules
            return 0

        tablename = table._tablename

        if tablename in (#"hrm_training_event",
                         "project_task",
                         #"req_need",
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

        elif tablename == "org_organisation":
            T = current.T
            tabs = [(T("Basic Details"), None),
                    (T("Offices"), "office"),
                    (T("Locations Served"), "location"),
                    (T("Volunteers"), "human_resource"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            from s3 import s3_fullname

            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                   record.name,
                                   )),
                          rheader_tabs)

        elif tablename == "pr_group":
            T = current.T
            tabs = [(T("Basic Details"), None),
                    # 'Person' allows native tab breakout
                    #(T("Members"), "group_membership"),
                    (T("Members"), "person"),
                    #(T("Locations"), "group_location"),
                    #(T("Skills"), "competency"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            from s3 import s3_fullname

            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                   record.name,
                                   )),
                          rheader_tabs)

        elif tablename == "pr_person":
            T = current.T
            tabs = [(T("Basic Details"), None),
                    (T("Address"), "address"),
                    (T("Contacts"), "contacts"),
                    # Included in Contacts tab:
                    #(T("Emergency Contacts"), "contact_emergency"),
                    ]
            get_vars_get = r.get_vars.get
            has_role = current.auth.s3_has_role
            if get_vars_get("donors") or \
               has_role("DONOR", include_admin=False):
                # Better on main form using S3SQLInlineLink
                #tabs.append((T("Goods / Services"), "item"))
                pass
            elif get_vars_get("groups") or \
                 has_role("GROUP_ADMIN", include_admin=False):
                # Better as menu item, to be able to access tab(s)
                #tabs.append((T("Group"), "group"))
                pass
            else:
                tabs.append((T("Additional Information"), "additional"))
                # Better on main form using S3SQLInlineLink  
                #tabs.append((T("Skills"), "competency"))
                if has_role("ORG_ADMIN"):
                    tabs.insert(1, (T("Affiliation"), "human_resource"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            from s3 import s3_fullname

            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                   s3_fullname(record),
                                   )),
                          rheader_tabs)

        elif tablename == "req_need":
            if not current.auth.s3_has_role("ORG_ADMIN"):
                # @ToDo: Button to Apply (rheader or rfooter)
                return None
            T = current.T
            tabs = [(T("Basic Details"), None),
                    #(T("Items"), "need_item"),
                    #(T("Skills"), "need_skill"),
                    (T("People"), "need_person"),
                    (T("Invite"), "assign"),
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
    def customise_auth_user_resource(r, tablename):
        """
            Hook in custom auth_user_register_onaccept for use when Agency/Existing Users are Approved
        """

        from templates.CCC.controllers import auth_user_register_onaccept

        current.s3db.configure("auth_user",
                               register_onaccept = auth_user_register_onaccept,
                               )

    settings.customise_auth_user_resource = customise_auth_user_resource

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
        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3TextFilter

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
                                                   S3SQLInlineComponent(
                                                        "document",
                                                        label = T("Attachment"),
                                                        #multiple = False,
                                                        fields = [("", "file")],
                                                        ),
                                                   ),
                       list_fields = [#"series_id",
                                      "title",
                                      "body",
                                      "date",
                                      "document.file",
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

        from gluon import IS_IN_SET, URL
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

        # Filtered components
        s3db.add_components("doc_document",
                            doc_document_tag = ({"name": "document_type",
                                                 "joinby": "document_id",
                                                 "filterby": {"tag": "document_type"},
                                                 "multiple": False,
                                                 },
                                                ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        document_type = components_get("document_type")
        f = document_type.table.value
        f.requires = IS_IN_SET(["Emergency Plan",
                                "Contact Information",
                                "Risk Assessment",
                                "Guidance Document",
                                "Map",
                                "Other",
                                ])

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
                                                   (T("Type"), "document_type.value"),
                                                   (T("Document Name"), "name"),
                                                   "file",
                                                   "date",
                                                   "comments",
                                                   ),
                       list_fields = ["organisation_id",
                                      "document_type.value",
                                      "name",
                                      "file",
                                      "date",
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

        from s3 import S3OptionsFilter, S3SQLCustomForm, S3TextFilter
        from s3layouts import S3PopupLink

        s3db = current.s3db

        # Filtered components
        s3db.add_components("hrm_human_resource",
                            hrm_human_resource_tag = ({"name": "job_title",
                                                       "joinby": "human_resource_id",
                                                       "filterby": {"tag": "job_title"},
                                                       "multiple": False,
                                                       },
                                                      ),
                            )

        table = s3db.hrm_human_resource
        #f = table.job_title_id
        #f.label = T("Role")
        #f.comment = S3PopupLink(c = "hrm",
        #                        f = "job_title",
        #                        label = T("New Job Title"),
        #                        title = T("Role"),
        #                        tooltip = T("The volunteer's role"),
        #                        )

        if r.controller == "default":
            # Personal Profile
            list_fields = ["job_title.value",
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
                           (T("Role"), "job_title.value"),
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
                         "job_title.value",
                         "comments",
                         "person_id$competency.skill_id$name",
                         ]

        gtable = s3db.gis_location
        districts = current.db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                         gtable.name,
                                                                                         cache = s3db.cache)
        districts = {d.id:d.name for d in districts}

        filter_widgets = [S3TextFilter(filter_fields,
                                       #formstyle = text_filter_formstyle,
                                       label = "",
                                       _placeholder = T("Search"),
                                       ),
                          S3OptionsFilter("person_id$person_location.location_id",
                                          label = T("Locations Served"),
                                          options = districts,
                                          ),
                          S3OptionsFilter("person_id$competency.skill_id"),
                          ]

        if current.auth.s3_has_role("ADMIN"):
            filter_fields.insert(0, "organisation_id$name")
            filter_widgets.append(S3OptionsFilter("organisation_id"))
            list_fields.insert(0, "organisation_id")
        else:
            f = table.organisation_id
            f.readable = f.writable = False
            f.comment = None # No Create
                       
        s3db.configure("hrm_human_resource",
                       crud_form = S3SQLCustomForm("organisation_id",
                                                   (T("Role"), "job_title.value"),
                                                   "person_id",
                                                   "comments",
                                                   ),
                       list_fields = list_fields,
                       filter_widgets = filter_widgets,
                       )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -------------------------------------------------------------------------
    #def customise_hrm_job_title_resource(r, tablename):

    #    current.response.s3.crud_strings[tablename] = Storage(
    #        label_create = T("New Role"),
    #        title_display = T("Role Details"),
    #        title_list = T("Roles"),
    #        title_update = T("Edit Role"),
    #        #title_upload = T("Import Roles"),
    #        label_list_button = T("List Roles"),
    #        label_delete_button = T("Delete Role"),
    #        msg_record_created = T("Role added"),
    #        msg_record_modified = T("Role updated"),
    #        msg_record_deleted = T("Role deleted"),
    #        msg_list_empty = T("No Roles currently registered")
    #    )

    #settings.customise_hrm_job_title_resource = customise_hrm_job_title_resource

    # -------------------------------------------------------------------------
    def hrm_training_event_postprocess(form):
        """
            Create Site based on other fields
        """

        training_event_id = form.vars.id

        db = current.db
        s3db = current.s3db

        etable = s3db.hrm_training_event
        ettable = s3db.hrm_event_tag
        ftable = s3db.org_facility

        # Load record
        left = ettable.on((ettable.training_event_id == training_event_id) & \
                          (ettable.tag == "venue_name")
                          )
        training_event = db(etable.id == training_event_id).select(etable.location_id,
                                                                   etable.site_id,
                                                                   ettable.value,
                                                                   left = left,
                                                                   limitby = (0, 1)
                                                                   ).first()
        venue_name = training_event[ettable.value]
        location_id = training_event[etable.location_id]
        site_id = training_event[etable.site_id]

        if site_id:
            facility = db(ftable.site_id == site_id).select(ftable.id,
                                                            limitby = (0, 1)
                                                            ).first()
            facility.update_record(name = venue_name,
                                   location_id = location_id,
                                   )
        else:
            record = {"name": venue_name,
                      "location_id": location_id,
                      }
            facility_id = ftable.insert(**record)
            record["id"] = facility_id
            s3db.update_super(ftable, record)
            db(etable.id == training_event_id).update(site_id = record["site_id"])

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_resource(r, tablename):

        from gluon import IS_EMAIL, IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY, IS_URL
        from s3 import IS_UTC_DATETIME, \
                       S3SQLInlineLink, S3LocationSelector, \
                       S3OptionsFilter, S3SQLCustomForm, S3TextFilter, \
                       s3_phone_requires

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

        # Filtered components
        s3db.add_components("hrm_training_event",
                            hrm_event_tag = ({"name": "venue_name",
                                              "joinby": "training_event_id",
                                              "filterby": {"tag": "venue_name"},
                                              "multiple": False,
                                              },
                                             {"name": "contact_name",
                                              "joinby": "training_event_id",
                                              "filterby": {"tag": "contact_name"},
                                              "multiple": False,
                                              },
                                             {"name": "contact_tel",
                                              "joinby": "training_event_id",
                                              "filterby": {"tag": "contact_tel"},
                                              "multiple": False,
                                              },
                                             {"name": "contact_email",
                                              "joinby": "training_event_id",
                                              "filterby": {"tag": "contact_email"},
                                              "multiple": False,
                                              },
                                             {"name": "contact_web",
                                              "joinby": "training_event_id",
                                              "filterby": {"tag": "contact_web"},
                                              "multiple": False,
                                              },
                                             ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        venue_name = components_get("venue_name")
        f = venue_name.table.value
        f.requires = IS_NOT_EMPTY()

        contact_tel = components_get("contact_tel")
        f = contact_tel.table.value
        f.requires = IS_EMPTY_OR(s3_phone_requires)

        contact_email = components_get("contact_email")
        f = contact_email.table.value
        f.requires = IS_EMAIL()

        contact_web = components_get("contact_web")
        f = contact_web.table.value
        f.requires = IS_EMPTY_OR(IS_URL())

        table = s3db.hrm_training_event
        table.name.readable = table.name.writable = True
        table.comments.comment = None
        table.start_date.requires = IS_UTC_DATETIME()
        table.site_id.represent = s3db.org_SiteRepresent(show_type = False)
        f = table.location_id
        f.readable = f.writable = True
        f.widget = S3LocationSelector(levels = ("L3"),
                                      required_levels = ("L3"),
                                      show_address = True)

        #gtable = s3db.gis_location
        #districts = current.db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
        #                                                                                 gtable.name,
        #                                                                                 cache = s3db.cache)
        #districts = {d.id:d.name for d in districts}
        #f = s3db.hrm_event_location.location_id
        #f.requires = IS_IN_SET(districts)
        #f.widget = None

        list_fields = ["start_date",
                       "name",
                       "site_id",
                       "location_id$L3",
                       "location_id$addr_street",
                       ]

        filter_widgets = [S3TextFilter(["name",
                                        "comments",
                                        ],
                                       #formstyle = text_filter_formstyle,
                                       label = "",
                                       _placeholder = T("Search"),
                                       ),
                          ]

        auth = current.auth
        if auth.s3_has_role("ADMIN"):
            filter_widgets.append(S3OptionsFilter("organisation_id",
                                                  label = T("Organization")))
            list_fields.insert(0, (T("Organization"), "organisation_id"))
        else:
            f = table.organisation_id
            f.default = auth.user.organisation_id
            f.readable = f.writable = False

        s3db.configure("hrm_training_event",
                       crud_form = S3SQLCustomForm((T("Event name"), "name"),
                                                   (T("Event description"), "comments"),
                                                   (T("Starts"), "start_date"),
                                                   (T("Ends"), "end_date"),
                                                   (T("Lead Organization"), "organisation_id"),
                                                   #S3SQLInlineLink("location",
                                                   #                field = "location_id",
                                                   #                label = T("Tick the area(s) which this event relates to"),
                                                   #                ),
                                                   (T("Venue name"), "venue_name.value"),
                                                   "location_id",
                                                   (T("Contact Name"), "contact_name.value"),
                                                   (T("Telephone"), "contact_tel.value"),
                                                   (T("Email"), "contact_email.value"),
                                                   (T("Website"), "contact_web.value"),
                                                   postprocess = hrm_training_event_postprocess,
                                                   ),
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       subheadings = {"name": T("Event Information"),
                                      #"link_defaultlocation": T("Event Coverage"),
                                      "venue_name_value": T("Venue"),
                                      "contact_name_value": T("Contact Information"),
                                      },
                       )

    settings.customise_hrm_training_event_resource = customise_hrm_training_event_resource

    # -----------------------------------------------------------------------------
    def customise_hrm_training_event_controller(**attr):

        attr["rheader"] = ccc_rheader

        return attr

    settings.customise_hrm_training_event_controller = customise_hrm_training_event_controller

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from s3 import S3OptionsFilter, S3SQLCustomForm, S3SQLInlineLink, S3TextFilter

        s3db = current.s3db

        #table = s3db.org_organisation

        s3db.configure("org_organisation",
                       crud_form = S3SQLCustomForm((T("Name of Organization"), "name"),
                                                   S3SQLInlineLink("organisation_type",
                                                                   field = "organisation_type_id",
                                                                   label = T("Type"),
                                                                   ),
                                                   #"email.value",
                                                   #"facebook.value",
                                                   #"twitter.value",
                                                   #"sm_other.value",
                                                   #"sm_details.value",
                                                   "website",
                                                   "comments",
                                                   ),
                       list_fields = ["name",
                                      (T("Type"), "organisation_organisation_type.organisation_type_id"),
                                      ],
                       filter_widgets = [S3TextFilter(["name",
                                                       "comments",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search"),
                                                      ),
                                         S3OptionsFilter("organisation_organisation_type.organisation_type_id",
                                                         label = T("Type"),
                                                         ),
                                         S3OptionsFilter("organisation_location.location_id",
                                                         label = T("Locations Served"),
                                                         ),
                                        ],
                       )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -----------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        attr["rheader"] = ccc_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_org_organisation_location_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET

        s3db = current.s3db
        gtable = s3db.gis_location
        districts = current.db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                         gtable.name,
                                                                                         cache = s3db.cache)
        districts = {d.id:d.name for d in districts}

        f = s3db.org_organisation_location.location_id
        f.requires = IS_EMPTY_OR(IS_IN_SET(districts))
        f.widget = None

    settings.customise_org_organisation_location_resource = customise_org_organisation_location_resource

    # -------------------------------------------------------------------------
    def customise_pr_group_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_INT_IN_RANGE, IS_NOT_EMPTY
        from s3 import IS_INT_AMOUNT, S3OptionsFilter, S3SQLCustomForm, S3SQLInlineLink, S3TextFilter, s3_phone_requires

        s3db = current.s3db

        # Filtered components
        s3db.add_components("pr_group",
                            pr_group_tag = ({"name": "volunteers",
                                             "joinby": "group_id",
                                             "filterby": {"tag": "volunteers"},
                                             "multiple": False,
                                             },
                                            {"name": "transport",
                                             "joinby": "group_id",
                                             "filterby": {"tag": "transport"},
                                             "multiple": False,
                                             },
                                            {"name": "skills_details",
                                             "joinby": "group_id",
                                             "filterby": {"tag": "skills_details"},
                                             "multiple": False,
                                             },
                                            {"name": "contact_name",
                                             "joinby": "group_id",
                                             "filterby": {"tag": "contact_name"},
                                             "multiple": False,
                                             },
                                            {"name": "contact_number",
                                             "joinby": "group_id",
                                             "filterby": {"tag": "contact_number"},
                                             "multiple": False,
                                             },
                                            ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        integer_represent = IS_INT_AMOUNT.represent

        volunteers = components_get("volunteers")
        f = volunteers.table.value
        f.represent = integer_represent
        f.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))

        contact_name = components_get("contact_name")
        f = contact_name.table.value
        f.requires = IS_NOT_EMPTY()
        f.comment = T("Contact must not be listed as a leader")

        contact_number = components_get("contact_number")
        f = contact_number.table.value
        f.requires = s3_phone_requires

        s3db.configure("pr_group",
                       crud_form = S3SQLCustomForm("name",
                                                   (T("Approximate Number of Volunteers"), "volunteers.value"),
                                                   (T("Mode of Transport"), "transport.value"),
                                                   S3SQLInlineLink("skill",
                                                                   field = "skill_id",
                                                                   label = T("Volunteer Offer"),
                                                                   ),
                                                   (T("Please specify details"), "skills_details.value"),
                                                   S3SQLInlineLink("location",
                                                                   field = "location_id",
                                                                   label = T("Where would you be willing to volunteer?"),
                                                                   ),
                                                   (T("Emergency Contact Name"), "contact_name.value"),
                                                   (T("Emergency Contact Number"), "contact_number.value"),
                                                   "comments",
                                                   ),
                       list_fields = ["name",
                                      (T("# Volunteers"), "volunteers.value"),
                                      (T("Mode of Transport"), "transport.value"),
                                      # Not working:
                                      #(T("Leaders"), "group_membership.person_id"),
                                      (T("Locations"), "group_location.location_id"),
                                      (T("Skills"), "group_competency.skill_id"),
                                      (T("Skills Details"), "skill_details.value"),
                                      "comments",
                                      ],
                       filter_widgets = [S3TextFilter(["name",
                                                       "group_membership.person_id$first_name",
                                                       "group_membership.person_id$middle_name",
                                                       "group_membership.person_id$last_name",
                                                       "group_location.location_id",
                                                       "group_competency.skill_id",
                                                       "skills_details.value",
                                                       "comments",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search"),
                                                      ),
                                         S3OptionsFilter("group_location.location_id",
                                                         label = T("Locations Served"),
                                                         ),
                                         S3OptionsFilter("group_competency.skill_id",
                                                         label = T("Skill"),
                                                         ),
                                         ],
                       )

    settings.customise_pr_group_resource = customise_pr_group_resource

    # -----------------------------------------------------------------------------
    def customise_pr_group_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component_name == "person":
                s3.crud_strings["pr_person"] = Storage(
                    label_create = T("New Member"),
                    title_display = T("Member Details"),
                    title_list = T("Members"),
                    title_update = T("Edit Member"),
                    #title_upload = T("Import Members"),
                    label_list_button = T("List Members"),
                    label_delete_button = T("Delete Member"),
                    msg_record_created = T("Member added"),
                    msg_record_modified = T("Member updated"),
                    msg_record_deleted = T("Member deleted"),
                    msg_list_empty = T("No Members currently registered")
                    )

                r.component.configure(list_fields = ["first_name",
                                                     "middle_name",
                                                     "last_name",
                                                     (T("Email"), "email.value"),
                                                     (T("Mobile Phone"), "phone.value"),
                                                     "comments",
                                                     ],
                                      )

            return result
        s3.prep = prep

        attr["rheader"] = ccc_rheader

        # Allow components with components (i.e. persons) to breakout from tabs
        #attr["native"] = True

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.component_name == "person":
                # Include get_vars on Action Buttons to configure crud_form/crud_strings appropriately
                from gluon import URL
                from s3 import S3CRUD

                read_url = URL(c="pr", f="person", args=["[id]", "read"],
                               vars = {"groups": 1})

                update_url = URL(c="pr", f="person", args=["[id]", "update"],
                                 vars = {"groups": 1})

                S3CRUD.action_buttons(r,
                                      read_url = read_url,
                                      update_url = update_url,
                                      )

            return output
        s3.postp = postp

        return attr

    settings.customise_pr_group_controller = customise_pr_group_controller

    # -------------------------------------------------------------------------
    def customise_pr_group_location_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET

        s3db = current.s3db
        gtable = s3db.gis_location
        districts = current.db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                         gtable.name,
                                                                                         cache = s3db.cache)
        districts = {d.id:d.name for d in districts}

        f = s3db.pr_group_location.location_id
        f.requires = IS_EMPTY_OR(IS_IN_SET(districts))
        f.widget = None

    settings.customise_pr_group_location_resource = customise_pr_group_location_resource

    # -------------------------------------------------------------------------
    def customise_pr_group_membership_resource(r, tablename):

        from s3 import S3AddPersonWidget, S3SQLCustomForm

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Leader"),
            title_display = T("Leader Details"),
            title_list = T("Leaders"),
            title_update = T("Edit Leader"),
            #title_upload = T("Import Leaders"),
            label_list_button = T("List Leaders"),
            label_delete_button = T("Delete Leader"),
            msg_record_created = T("Leader added"),
            msg_record_modified = T("Leader updated"),
            msg_record_deleted = T("Leader deleted"),
            msg_list_empty = T("No Leaders currently registered")
        )

        s3db = current.s3db

        table = s3db.pr_group_membership
        table.person_id.widget = S3AddPersonWidget(controller="pr")

        s3db.configure("pr_group_membership",
                       crud_form = S3SQLCustomForm("person_id",
                                                   "comments",
                                                   ),
                       list_fields = ["person_id",
                                      (T("Phone"), "person_id$phone.value"),
                                      (T("Email"), "person_id$email.value"),
                                      "comments",
                                      ],
                       )

    settings.customise_pr_group_membership_resource = customise_pr_group_membership_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET
        from s3 import S3SQLCustomForm, S3SQLInlineLink

        s3db = current.s3db

        # Filtered components
        s3db.add_components("pr_person",
                            pr_person_tag = ({"name": "organisation",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "organisation"},
                                              "multiple": False,
                                              },
                                             {"name": "organisation_type",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "organisation_type"},
                                              "multiple": False,
                                              },
                                             {"name": "items_details",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "items_details"},
                                              "multiple": False,
                                              },
                                             {"name": "skills_details",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "skills_details"},
                                              "multiple": False,
                                              },
                                             {"name": "delivery",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "delivery"},
                                              "multiple": False,
                                              },
                                             {"name": "availability",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "availability"},
                                              "multiple": False,
                                              },
                                             ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        organisation_type = components_get("organisation_type")
        f = organisation_type.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET([T("Business Donor"),
                                            T("Individual Donor"),
                                            T("Public Sector Organization"),
                                            T("Voluntary Sector Organization"),
                                            ]))

        delivery = components_get("delivery")
        f = delivery.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"

        get_vars_get = r.get_vars.get
        has_role = current.auth.s3_has_role
        if get_vars_get("donors") or \
           has_role("DONOR", include_admin=False):
            # Donor
            crud_fields = ["first_name",
                           "middle_name",
                           "last_name",
                           "date_of_birth",
                           (T("Gender"), "gender"),
                           (T("Name of Organization"), "organisation.value"),
                           (T("Type of Organization"), "organisation_type.value"),
                           S3SQLInlineLink("item",
                                           field = "item_id",
                                           label = T("Goods / Services"),
                                           ),
                           (T("Details"), "items_details.value"),
                           (T("Are you able to Deliver?"), "delivery.value"),
                           S3SQLInlineLink("location",
                                           field = "location_id",
                                           label = T("Where would you be willing to deliver?"),
                                           ),
                           (T("Length of time the offer is available?"), "availability.value"),
                           "comments",
                           ]
        elif get_vars_get("groups") or \
             r.function == "group" or \
             has_role("GROUP_ADMIN", include_admin=False):
            # Group Admin
            # Skills are recorded at the Group level
            crud_fields = ["first_name",
                           "middle_name",
                           "last_name",
                           "date_of_birth",
                           (T("Gender"), "gender"),
                           "comments",
                           ]
        else:
            # Individual Volunteer: Reserve or Organisation
            crud_fields = ["first_name",
                           "middle_name",
                           "last_name",
                           "date_of_birth",
                           (T("Gender"), "gender"),
                           S3SQLInlineLink("skill",
                                           field = "skill_id",
                                           label = T("Volunteer Offer"),
                                           ),
                           (T("Skills Details"), "skills_details.value"),
                           S3SQLInlineLink("location",
                                           field = "location_id",
                                           label = T("Where would you be willing to operate?"),
                                           ),
                           "comments",
                           ]

        s3db.configure("pr_person",
                       crud_form = S3SQLCustomForm(*crud_fields),
                       )

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -----------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db

        # Custom Component
        s3db.add_components("pr_person",
                            pr_group = {"link": "pr_group_membership",
                                        "joinby": "person_id",
                                        "key": "group_id",
                                        "actuate": "replace",
                                        "multiple": False,
                                        },
                            )

        # Custom Method
        from templates.CCC.controllers import personAdditional
        s3db.set_method("pr", "person",
                        method = "additional",
                        action = personAdditional)

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component_name == "group_membership":
                r.resource.components._components["group_membership"].configure(listadd = False,
                                                                                list_fields = [(T("Name"), "group_id$name"),
                                                                                               "group_id$comments",
                                                                                               ],
                                                                                )

            get_vars_get = r.get_vars.get
            has_role = current.auth.s3_has_role
            if get_vars_get("reserves") or \
               has_role("RESERVE", include_admin=False):
                # Reserve Volunteers
                from s3 import FS, S3OptionsFilter, S3TextFilter
                resource = r.resource
                # Only include Reserves
                db = current.db
                mtable = db.auth_membership
                gtable = db.auth_group
                query = (gtable.uuid == "RESERVE") & \
                        (gtable.id == mtable.group_id)
                reserves = db(query).select(mtable.user_id)
                reserves = [m.user_id for m in reserves]
                resource.add_filter(FS("user.id").belongs(reserves))

                gtable = s3db.gis_location
                districts = current.db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                                 gtable.name,
                                                                                                 cache = s3db.cache)
                districts = {d.id:d.name for d in districts}

                resource.configure(list_fields = ["first_name",
                                                  "middle_name",
                                                  "last_name",
                                                  (T("Skills"), "competency.skill_id"),
                                                  (T("Email"), "email.value"),
                                                  (T("Mobile Phone"), "phone.value"),
                                                  ],
                                   filter_widgets = [S3TextFilter(["first_name",
                                                                   "middle_name",
                                                                   "last_name",
                                                                   "comments",
                                                                   "competency.skill_id$name",
                                                                   ],
                                                                  #formstyle = text_filter_formstyle,
                                                                  label = "",
                                                                  _placeholder = T("Search"),
                                                                  ),
                                                     S3OptionsFilter("person_location.location_id",
                                                                     label = T("Locations Served"),
                                                                     options = districts,
                                                                     ),
                                                     S3OptionsFilter("competency.skill_id",
                                                                     ),
                                                     ],
                                   )
                s3.crud_strings[r.tablename] = Storage(
                    label_create = T("New Reserve Volunteer"),
                    title_display = T("Reserve Volunteer Details"),
                    title_list = T("Reserve Volunteers"),
                    title_update = T("Edit Reserve Volunteer"),
                    #title_upload = T("Import Reserve Volunteers"),
                    label_list_button = T("List Reserve Volunteers"),
                    label_delete_button = T("Delete Reserve Volunteer"),
                    msg_record_created = T("Reserve Volunteer added"),
                    msg_record_modified = T("Reserve Volunteer updated"),
                    msg_record_deleted = T("Reserve Volunteer deleted"),
                    msg_list_empty = T("No Reserve Volunteers currently registered")
                    )   
            elif get_vars_get("donors") or \
                 has_role("DONOR", include_admin=False):
                # Donors
                from s3 import FS, S3OptionsFilter, S3TextFilter
                resource = r.resource
                # Only include Donors
                db = current.db
                mtable = db.auth_membership
                gtable = db.auth_group
                query = (gtable.uuid == "DONOR") & \
                        (gtable.id == mtable.group_id)
                donors = db(query).select(mtable.user_id)
                donors = [d.user_id for d in donors]
                resource.add_filter(FS("user.id").belongs(donors))

                resource.configure(list_fields = [# @ToDo: Add Organisation freetext
                                                  "first_name",
                                                  "middle_name",
                                                  "last_name",
                                                  (T("Goods / Services"), "person_item.item_id"),
                                                  (T("Email"), "email.value"),
                                                  (T("Mobile Phone"), "phone.value"),
                                                  ],
                                   filter_widgets = [S3TextFilter(["first_name",
                                                                   "middle_name",
                                                                   "last_name",
                                                                   "comments",
                                                                   # @ToDo: Add Items
                                                                   #"competency.skill_id$name",
                                                                   ],
                                                                  #formstyle = text_filter_formstyle,
                                                                  label = "",
                                                                  _placeholder = T("Search"),
                                                                  ),
                                                     S3OptionsFilter("person_item.item_id",
                                                                     ),
                                                     ],
                                   )
                s3.crud_strings[r.tablename] = Storage(
                    label_create = T("New Donor"),
                    title_display = T("Donor Details"),
                    title_list = T("Donors"),
                    title_update = T("Edit Donor"),
                    #title_upload = T("Import Donors"),
                    label_list_button = T("List Donors"),
                    label_delete_button = T("Delete Donor"),
                    msg_record_created = T("Donor added"),
                    msg_record_modified = T("Donor updated"),
                    msg_record_deleted = T("Donor deleted"),
                    msg_list_empty = T("No Donors currently registered")
                    ) 
            elif get_vars_get("groups") or \
                 has_role("GROUP_ADMIN", include_admin=False):
                # Group Members
                s3.crud_strings[r.tablename] = Storage(
                    label_create = T("New Member"),
                    title_display = T("Member Details"),
                    title_list = T("Members"),
                    title_update = T("Edit Member"),
                    #title_upload = T("Import Members"),
                    label_list_button = T("List Members"),
                    label_delete_button = T("Delete Member"),
                    msg_record_created = T("Member added"),
                    msg_record_modified = T("Member updated"),
                    msg_record_deleted = T("Member deleted"),
                    msg_list_empty = T("No Members currently registered")
                    )
            else:
                # Organisation Volunteers
                # (only used for hrm/person profile)
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

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            # Include get_vars on Action Buttons to configure crud_form/crud_strings appropriately
            from gluon import URL
            from s3 import S3CRUD

            read_url = URL(c="pr", f="person", args=["[id]", "read"],
                           vars = r.get_vars)

            update_url = URL(c="pr", f="person", args=["[id]", "update"],
                             vars = r.get_vars)

            S3CRUD.action_buttons(r,
                                  read_url = read_url,
                                  update_url = update_url,
                                  )

            return output
        s3.postp = postp
        
        # Hide the search box on component tabs, as confusing & not useful
        attr["dtargs"] = {"dt_searching": False,
                          }
        attr["rheader"] = ccc_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def customise_pr_person_location_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET
        from s3 import S3Represent

        s3db = current.s3db
        gtable = s3db.gis_location
        districts = current.db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                         gtable.name,
                                                                                         cache = s3db.cache)
        districts = {d.id:d.name for d in districts}

        f = s3db.pr_person_location.location_id
        f.represent = S3Represent(options = districts)
        f.requires = IS_EMPTY_OR(IS_IN_SET(districts))
        f.widget = None

    settings.customise_pr_person_location_resource = customise_pr_person_location_resource

    # -------------------------------------------------------------------------
    def project_task_create_onaccept(form):
        """
            When a Task is created:
                * Notify OrgAdmins
        """

        from gluon import URL
        from s3 import s3_fullname

        form_vars_get = form.vars.get
        task_id = form_vars_get("id")

        # Lookup the Author details
        db = current.db
        s3db = current.s3db
        ttable = s3db.project_task
        otable = s3db.org_organisation
        utable = db.auth_user
        query = (ttable.id == task_id) & \
                (ttable.created_by == utable.id)
        user = db(query).select(utable.first_name,
                                utable.last_name,
                                utable.organisation_id,
                                limitby = (0, 1)
                                ).first()
        fullname = s3_fullname(user)

        # Lookup the ORG_ADMINs
        gtable = db.auth_group
        mtable = db.auth_membership
        query = (gtable.uuid == "ORG_ADMIN") & \
                (gtable.id == mtable.group_id) & \
                (mtable.user_id == utable.id) & \
                (utable.organisation_id == user.organisation_id)
        org_admins = db(query).select(utable.email)

        # Construct Email message
        system_name = settings.get_system_name_short()
        subject = "%s: Message sent from %s" % \
            (system_name,
             fullname,
             )
        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="project", f="task", args=[task_id]))

        message = "%s has sent you a Message on %s\n\nSubject: %s\nMessage: %s\n\nYou can view the message here: %s" % \
            (fullname,
             system_name,
             form_vars_get("name"),
             form_vars_get("description") or "",
             url,
             )

        # Send message to each
        send_email = current.msg.send_email
        for admin in org_admins:
            send_email(to = admin.email,
                       subject = subject,
                       message = message,
                       )

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
        #    f = table.priority
        #    f.default = 1
        #    f.readable = f.writable = False
        #    f = table.status
        #    f.default = 1
        #    f.readable = f.writable = False
        #    table.pe_id.readable = table.pe_id.writable = False
            table.comments.readable = table.comments.writable = False

        s3db.configure("project_task",
                       # Can simply replace the default one
                       create_onaccept = project_task_create_onaccept,
                       crud_form = S3SQLCustomForm("name",
                                                   "description",
                                                   #"priority",
                                                   #"status",
                                                   #"pe_id",
                                                   "comments",
                                                   ),
                       list_fields = [#"priority",
                                      #"status",
                                      #"pe_id",
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
                                         #S3OptionsFilter("priority",
                                         #                options = settings.get_project_task_priority_opts(),
                                         #                cols = 3,
                                         #                ),
                                         #S3OptionsFilter("status",
                                         #                options = settings.get_project_task_status_opts(),
                                         #                cols = 3,
                                         #                ),
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
    def req_need_organisation_onaccept(form):
        """
            Set the realm of the parent req_need to that of the organisation
        """

        db = current.db
        s3db = current.s3db
        rntable = s3db.req_need
        otable = s3db.org_organisation

        form_vars_get = form.vars.get

        need_id = form_vars_get("need_id")
        organisation_id = form_vars_get("organisation_id")
        if not need_id or not organisation_id:
            rnotable = s3db.req_need_organisation
            record_id = form_vars_get("id")
            record = db(rnotable.id == record_id).select(rnotable.need_id,
                                                         rnotable.organisation_id,
                                                         limitby = (0, 1),
                                                         ).first()
            need_id = record.need_id
            organisation_id = record.organisation_id

        org = db(otable.id == organisation_id).select(otable.pe_id,
                                                      limitby = (0, 1),
                                                      ).first()
        realm_entity = org.pe_id

        db(rntable.id == need_id).update(realm_entity = realm_entity)

    # -------------------------------------------------------------------------
    def customise_req_need_resource(r, tablename):

        from s3 import IS_ONE_OF, IS_UTC_DATETIME, S3CalendarWidget, S3DateTime, \
                       S3LocationSelector, S3SQLCustomForm, S3SQLInlineComponent, \
                       S3OptionsFilter, S3TextFilter, s3_comments_widget

        s3db = current.s3db

        # Filtered components
        s3db.add_components("req_need",
                            req_need_tag = ({"name": "age_restrictions",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "age_restrictions"},
                                             "multiple": False,
                                             },
                                            {"name": "practical_info",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "practical_info"},
                                             "multiple": False,
                                             },
                                            {"name": "parking",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "parking"},
                                             "multiple": False,
                                             },
                                            {"name": "bring",
                                             "joinby": "need_id",
                                             "filterby": {"tag": "bring"},
                                             "multiple": False,
                                             },
                                            ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        practical_info = components_get("practical_info")
        f = practical_info.table.value
        f.widget = lambda f, v: \
            s3_comments_widget(f, v, _placeholder = "including directions to location of the opportunity")

        table = s3db.req_need
        table.name.label = T("Description")
        f = table.date
        f.label = T("Start Date")
        f.represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)
        f.requires = IS_UTC_DATETIME()
        f.widget = S3CalendarWidget(timepicker = True)
        table.end_date.readable = table.end_date.writable = True
        table.location_id.widget = S3LocationSelector(levels = ("L3"),
                                                      required_levels = ("L3"),
                                                      show_address = True)

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

        person_id = s3db.req_need_contact.person_id
        person_id.comment = None # No Create

        filter_widgets = [S3TextFilter(["name",
                                        "comments",
                                        ],
                                       #formstyle = text_filter_formstyle,
                                       label = "",
                                       _placeholder = T("Search"),
                                       ),
                          S3OptionsFilter("location_id$L3",
                                          label = T("District"),
                                          ),
                          S3OptionsFilter("need_skill.skill_id"),
                          ]
                       
        list_fields = ["date",
                       "end_date",
                       "location_id",
                       #(T("Opportunity"), "name"),
                       "name",
                       "need_contact.person_id",
                       #(T("Phone"), "need_contact.person_id$phone.value"),
                       #(T("Email"), "need_contact.person_id$email.value"),
                       "need_skill.skill_id",
                       "need_skill.quantity",
                       ]

        auth = current.auth
        if auth.s3_has_role("ADMIN"):
            filter_widgets.insert(-2, S3OptionsFilter("need_organisation.organisation_id"))
            list_fields.insert(0, "need_organisation.organisation_id")
        else:
            organisation_id = auth.user.organisation_id
            f = s3db.req_need_organisation.organisation_id
            f.default = organisation_id
            # Needs to be in the form
            #f.readable = f.writable = False
            f.requires = s3db.org_organisation_requires(updateable=True)
            f.comment = None # No Create

            # Dropdown, not Autocomplete
            person_id.widget = None
            # Filtered to people affiliated with this Org
            db = current.db
            hrtable = s3db.hrm_human_resource
            persons = db(hrtable.organisation_id == organisation_id).select(hrtable.person_id)
            persons = [p.person_id for p in persons]
            person_id.requires = IS_ONE_OF(db, "pr_person.id",
                                           person_id.represent,
                                           orderby = "pr_person.first_name",
                                           sort = True,
                                           filterby = "id",
                                           filter_opts = persons,
                                           )

        s3db.configure("req_need",
                       # Needs a custom handler as default handler only supports default forms
                       #copyable = True,
                       crud_form = S3SQLCustomForm("need_organisation.organisation_id",
                                                   "date",
                                                   "end_date",
                                                   "location_id",
                                                   "name",
                                                   "need_contact.person_id",
                                                   S3SQLInlineComponent("need_skill",
                                                                        label = "",
                                                                        fields = ["skill_id", "quantity"],
                                                                        multiple = False,
                                                                        ),
                                                   (T("Age Restrictions"), "age_restrictions.value"),
                                                   (T("Practical Information"), "practical_info.value"),
                                                   (T("Parking Options"), "parking.value"),
                                                   (T("What to Bring"), "bring.value"),
                                                   "comments",
                                                   ),
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

        s3db.configure("req_need_organisation",
                       onaccept = req_need_organisation_onaccept,
                       )

    settings.customise_req_need_resource = customise_req_need_resource

    # -----------------------------------------------------------------------------
    def customise_req_need_controller(**attr):

        #s3 = current.response.s3

        # Custom prep
        #standard_prep = s3.prep
        #def prep(r):
        #    # Call standard prep
        #    if callable(standard_prep):
        #        result = standard_prep(r)
        #    else:
        #        result = True

        #    if r.method == "read":
        #        # Show the Contact's Phone & Email
        #        # @ToDo: Do this only for Vols whose Application has been succesful
        #        # @ToDo: Create custom version of this which bypasses ACLs since
        #        #        - Will fail for normal Vols as they can't see other Vols anyway
        #        #        - Also failing for OrgAdmin as the user-added Phone is in the Personal PE not the Org's
        #        s3db = current.s3db
        #        s3db.req_need_contact.person_id.represent = s3db.pr_PersonRepresentContact(show_email = True,
        #                                                                                   show_link = False,
        #                                                                                   )

        #    return result
        #s3.prep = prep
        
        attr["rheader"] = ccc_rheader

        return attr

    settings.customise_req_need_controller = customise_req_need_controller

    # -------------------------------------------------------------------------
    def customise_req_need_person_resource(r, tablename):

        current.response.s3.crud_labels["DELETE"] = "Remove"

        s3db = current.s3db

        s3db.req_need_person.person_id.represent = s3db.pr_PersonRepresent(show_link=True)

        s3db.configure("req_need_person",
                       # Don't add people here (they are either invited or apply)
                       listadd = False,
                       )

    settings.customise_req_need_person_resource = customise_req_need_person_resource

    # -------------------------------------------------------------------------
    def customise_supply_person_item_resource(r, tablename):

        s3db = current.s3db
        f = s3db.supply_person_item.item_id
        # No Hyperlink for Items (don't have permissions anyway)
        f.represent = s3db.supply_ItemRepresent()
        # Dropdown, not Autocomplete
        f.widget = None

    settings.customise_supply_person_item_resource = customise_supply_person_item_resource

# END =========================================================================
