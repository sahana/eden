# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Support Cumbria
        - supported by Cumbria County Council
        - manage Volunteers
        - manage Donations
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
    settings.auth.realm_entity_types = ("org_organisation",
                                        #"org_office",
                                        "pr_forum", # Donors & Reserves
                                        "pr_group", # Volunteer Groups
                                        "pr_person", # Donors
                                        )

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

    # Which page to go to after login?
    def login_next():
        """
            @ToDo: This function won't work once we update s3aaa.py login to 2-factor auth
                   since roles not yet assigned when this function is called
        """
        from gluon import URL
        has_role = current.auth.s3_has_role
        if has_role("ADMIN"):
            _next = current.request.vars._next or URL(c="default", f="index")
        elif has_role("VOLUNTEER") or has_role("RESERVE"):
            _next = URL(c="cms", f="post", args="datalist")
        elif has_role("DONOR"):
            _next = URL(c="default", f="index", args="donor")
        else:
            _next = current.request.vars._next or URL(c="default", f="index")
        return _next

    settings.auth.login_next = login_next
    settings.auth.login_next_always = True

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

    # Now done in project_task_create_onaccept:
    # -------------------------------------------------------------------------
    #def ccc_realm_entity(table, row):
    #    """
    #        Assign a Realm Entity to records
    #    """

    #    if table._tablename in (#"hrm_training_event", # Default is fine
    #                            "project_task",
    #                            #"req_need",           # Default is fine
    #                            ):
    #        db = current.db
    #        otable = current.s3db.org_organisation
    #        organisation_id = current.request.get_vars.get("organisation_id")
    #        if organisation_id:
    #            # Use this Org
    #            query = (otable.id == organisation_id)
    #        else:
    #            # Use the Org of the Creator
    #            new_row = db(table.id == row.id).select(table.created_by,
    #                                                    limitby = (0, 1),
    #                                                    ).first()
    #            user_id = new_row.created_by

    #            utable = db.auth_user
    #            query = (utable.id == user_id) & \
    #                    (utable.organisation_id == otable.id)
    #        org = db(query).select(otable.pe_id,
    #                               limitby = (0, 1),
    #                               ).first()
    #        try:
    #            return org.pe_id
    #        except AttributeError:
    #            pass

    #    # Use default rules
    #    return 0

    #settings.auth.realm_entity = ccc_realm_entity

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
            auth = current.auth
            has_role = auth.s3_has_role
            if has_role("ADMIN") or \
               (record.organisation_id == auth.user.organisation_id and \
                (has_role("ORG_ADMIN") or \
                 has_role("AGENCY"))):
                tabs = [(T("Basic Details"), None),
                        (T("Participants"), "training"),
                        (T("Invite"), "assign"),
                        ]
                from gluon import A, URL
                from s3 import ICON
                reminder_btn = DIV(A(ICON("mail"),
                                     " ",
                                     T("Send Reminder"),
                                     _class="action-btn",
                                     _href = URL(args = [record.id, "remind"]),
                                     ),
                                   )
            elif has_role("RESERVE"):
                # Reserves can only see Events that they have been invited to
                tabs = [(T("Basic Details"), None),
                        (T("Participation"), "training"),
                        ]
                reminder_btn = ""
            else:
                record_id = record.id
                ltable = current.s3db.hrm_training
                query = (ltable.training_event_id == record_id) & \
                        (ltable.person_id == auth.s3_logged_in_person())
                training = current.db(query).select(ltable.id,
                                                    limitby = (0, 1)
                                                    ).first()
                if training:
                    tabs = [(T("Basic Details"), None),
                            (T("Participation"), "training"),
                            ]
                    reminder_btn = ""
                else:
                    from gluon import A, URL
                    apply_btn = DIV(A(T("Apply"),
                                      _class="action-btn",
                                      _href = URL(args = [record_id, "apply"]),
                                      ),
                                    )
                    tabs = None

            if tabs is None:
                rheader = DIV(apply_btn)
            else:
                rheader_tabs = s3_rheader_tabs(r, tabs)

                table = r.table
                location_id = table.location_id
                date_field = table.start_date
                rheader = DIV(TABLE(TR(TH("%s: " % T("Event name")),
                                       record.name,
                                       ),
                                    TR(TH("%s: " % T("Date")),
                                       date_field.represent(record.start_date),
                                       ),
                                    TR(TH("%s: " % location_id.label),
                                       location_id.represent(record.location_id),
                                       ),
                                    reminder_btn,
                                    ),
                              rheader_tabs)

        elif tablename == "org_organisation":
            T = current.T
            tabs = [(T("Basic Details"), None),
                    #(T("Offices"), "office"),
                    (T("Key Locations"), "facility"),
                    #(T("Locations Served"), "location"),
                    (T("Volunteers"), "human_resource"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            from s3 import s3_fullname

            if current.auth.s3_has_role("ADMIN"):

                from gluon import A, URL
                from s3 import ICON

                script = """
$('.copy-link').click(function(e){
 var t = document.createElement('textarea');
 document.body.appendChild(t);
 t.value = '%s' + $(this).attr('href');
 t.focus();
 t.select();
 try{
  document.execCommand('copy');
 }catch(e){
  console.log('Copy failed');
 }
 document.body.removeChild(t);
 e.preventDefault();
})""" % settings.get_base_public_url()
                current.response.s3.jquery_ready.append(script)

                registration_link = DIV(A(ICON("copy"),
                                          " ",
                                          T("Registration Link"),
                                          _class="action-btn copy-link",
                                          _href = URL(c = "default",
                                                      f = "index",
                                                      args = ["register"],
                                                      vars = {"org": record.id},
                                                      ),
                                          ),
                                        )
            else:
                registration_link = ""

            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                                   record.name,
                                   ),
                                registration_link,
                                ),
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
            T = current.T
            auth = current.auth
            db = current.db
            s3db = current.s3db
            has_role = auth.s3_has_role
            record_id = r.id
            ltable = s3db.req_need_organisation
            query = (ltable.need_id == record_id)
            need_org = db(query).select(ltable.organisation_id,
                                        limitby = (0, 1)
                                        ).first()
            if has_role("ADMIN") or \
               (need_org.organisation_id == auth.user.organisation_id and \
                (has_role("ORG_ADMIN") or \
                 has_role("AGENCY"))):
                tabs = [(T("Basic Details"), None),
                        #(T("Items"), "need_item"),
                        #(T("Skills"), "need_skill"),
                        (T("Participants"), "need_person"),
                        (T("Invite"), "assign"),
                        ]
                from gluon import A, URL
                from s3 import ICON
                reminder_btn = DIV(A(ICON("mail"),
                                     " ",
                                     T("Send Reminder"),
                                     _class="action-btn",
                                     _href = URL(args = [record_id, "remind"]),
                                     ),
                                   )
            elif has_role("RESERVE"):
                # Reserves can only see Opportunities that they have been invited to
                tabs = [(T("Basic Details"), None),
                        (T("Participation"), "need_person"),
                        ]
                reminder_btn = ""
            else:
                ltable = s3db.req_need_person
                query = (ltable.need_id == record_id) & \
                        (ltable.person_id == auth.s3_logged_in_person())
                need_person = db(query).select(ltable.id,
                                               limitby = (0, 1)
                                               ).first()
                if need_person:
                    tabs = [(T("Basic Details"), None),
                            (T("Participation"), "need_person"),
                            ]
                    reminder_btn = ""
                else:
                    from gluon import A, URL
                    apply_btn = DIV(A(T("Apply"),
                                      _class="action-btn",
                                      _href = URL(args = [record_id, "apply"]),
                                      ),
                                    )
                    tabs = None

            if tabs is None:
                rheader = DIV(apply_btn)
            else:
                rheader_tabs = s3_rheader_tabs(r, tabs)

                table = r.table
                location_id = table.location_id
                date_field = table.date
                rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                                       record.name,
                                       ),
                                    TR(TH("%s: " % date_field.label),
                                       date_field.represent(record.date),
                                       ),
                                    TR(TH("%s: " % location_id.label),
                                       location_id.represent(record.location_id),
                                       ),
                                    reminder_btn,
                                    ),
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

        args = current.request.args
        if not len(args):
            auth = current.auth
            if not auth.s3_has_role("ADMIN"):
                # ORG_ADMIN
                # - show link to allow users to register for this Org

                from gluon import A, DIV, URL
                from s3 import ICON

                s3 = current.response.s3
                script = """
$('.copy-link').click(function(e){
 var t = document.createElement('textarea');
 document.body.appendChild(t);
 t.value = '%s' + $(this).attr('href');
 t.focus();
 t.select();
 try{
  document.execCommand('copy');
 }catch(e){
  console.log('Copy failed');
 }
 document.body.removeChild(t);
 e.preventDefault();
})""" % settings.get_base_public_url()
                s3.jquery_ready.append(script)

                s3.rfooter = DIV(A(ICON("copy"),
                                   " ",
                                   T("Registration Link"),
                                   _class="action-btn copy-link",
                                   _href = URL(c = "default",
                                               f = "index",
                                               args = ["register"],
                                               vars = {"org": auth.user.organisation_id},
                                               ),
                                   ),
                                 )
        elif args(0) == "register":
            # Not easy to tweak the URL in the login form's buttons
            from gluon import redirect, URL
            redirect(URL(c="default", f="index",
                         args = "register",
                         vars = current.request.get_vars))

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

            # Twitter script
            s3.scripts.append("https://platform.twitter.com/widgets.js")

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
        #from s3layouts import S3PopupLink

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
        # We use job_title tag instead for freetext rather than dropdown
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

        auth = current.auth
        if auth.s3_has_role(auth.get_system_roles().ADMIN):
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
    def hrm_training_create_onaccept(form):
        """
            Ensure record owned by the invitee
        """

        db = current.db
        s3db = current.s3db
        table = s3db.hrm_training
        record = db(table.id == form.vars.get("id")).select(table.id,
                                                            table.person_id,
                                                            limitby = (0, 1),
                                                            ).first()
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (ptable.id == record.person_id) & \
                (ptable.pe_id == ltable.pe_id)
        link = db(query).select(ltable.user_id,
                                limitby = (0, 1)
                                ).first()
        try:
            record.update_record(owned_by_user = link.user_id)
        except AttributeError:
            pass

    # -------------------------------------------------------------------------
    def hrm_training_update_onaccept(form):
        """
            Inform applicant if they have been Approved/Declined
            tbc?: Inform OrgAdmins if they have been Accepted/Rejected
        """

        form_vars_get = form.vars.get
        if form.record.status in (1, 2) and \
           form_vars_get("status") == "3":
            # Rejected
            approved_or_rejected = "rejected"
        elif form.record.status in (1, 3) and \
             form_vars_get("status") == "2":
            # Approved
            approved_or_rejected = "approved"
        else:
            return

        db = current.db
        s3db = current.s3db
        table = s3db.hrm_training
        training_id = form_vars_get("id")

        record = db(table.id == training_id).select(table.person_id,
                                                    table.training_event_id,
                                                    limitby = (0, 1)
                                                    ).first()

        # Message
        utable = db.auth_user
        ltable = s3db.pr_person_user
        ptable = s3db.pr_person
        query = (ptable.id == record.person_id) & \
                (ptable.pe_id == ltable.pe_id) & \
                (ltable.user_id == utable.id)
        user = db(query).select(utable.email,
                                limitby = (0, 1)
                                ).first()

        # Construct Email message
        subject = "%s: You have been %s to participate in an Event" % \
            (settings.get_system_name_short(),
             approved_or_rejected,
             )

        etable = s3db.hrm_training_event
        training_event = db(etable.id == record.training_event_id).select(etable.name,
                                                                          limitby = (0, 1)
                                                                          ).first().name

        message = "You have been %s to participate in an Event:\n%s" % \
            (approved_or_rejected,
             training_event,
             )

        # Send message to each
        current.msg.send_email(to = user.email,
                               subject = subject,
                               message = message,
                               )

    # -------------------------------------------------------------------------
    def customise_hrm_training_resource(r, tablename):

        from s3 import S3SQLCustomForm

        s3db = current.s3db

        table = s3db.hrm_training

        table.status.readable = table.status.writable = True
        f = table.person_id
        f.comment = None
        f.writable = False
        f.represent = s3db.pr_PersonRepresent(show_link = True)

        current.response.s3.crud_strings.hrm_training = Storage(
            label_create = T("Add Participant"),
            title_display = T("Participant Details"),
            title_list = T("Participants"),
            title_update = T("Edit Participant"),
            title_upload = T("Import Participants"),
            label_list_button = T("List Participants"),
            label_delete_button = T("Remove Participant"),
            msg_record_created = T("Participant added"),
            msg_record_modified = T("Participant updated"),
            msg_record_deleted = T("Participant removed"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Participants registered"))

        deletable = True
        if r.component_id:
            record = current.db(table.id == r.component_id).select(table.status,
                                                                   limitby = (0, 1)
                                                                   ).first()
            if current.auth.s3_has_role("ORG_ADMIN"):
                from gluon import IS_IN_SET
                if record.status in (1, 2, 3):
                    deletable = False
                    table.status.requires = IS_IN_SET({1: T("Applied"),
                                                       2: T("Approved"),
                                                       3: T("Rejected"),
                                                       })
                else:
                    table.status.requires = IS_IN_SET({4: T("Invited"),
                                                       5: T("Accepted"),
                                                       6: T("Declined"),
                                                       })
            else:
                if record.status in (4, 5, 6):
                    deletable = False
                    from gluon import IS_IN_SET
                    if r.method == "update":
                        table.status.requires = IS_IN_SET({5: T("Accepted"),
                                                           6: T("Declined"),
                                                           })
                    else:
                        table.status.requires = IS_IN_SET({4: T("Invited"),
                                                           5: T("Accepted"),
                                                           6: T("Declined"),
                                                           })
                else:
                    current.response.s3.crud_strings.hrm_training.label_delete_button = T("Withdraw Application")
                    table.status.writable = False
        elif r.component:
            if current.auth.s3_has_role("ORG_ADMIN"):
                current.response.s3.crud_labels["DELETE"] = "Remove"
            else:
                current.response.s3.crud_labels["DELETE"] = "Withdraw"

        s3db.configure("hrm_training",
                       crud_form = S3SQLCustomForm("person_id",
                                                   "status",
                                                   "comments",
                                                   ),
                       deletable = deletable,
                       # Done in customise_hrm_training_event_controller prep
                       #list_fields = ["person_id",
                       #               "person_id$human_resource.organisation_id",
                       #               "status",
                       #               "comments",
                       #               ],
                       # Don't add people here (they are either invited or apply)
                       listadd = False,
                       update_onaccept = hrm_training_update_onaccept,
                       )

    settings.customise_hrm_training_resource = customise_hrm_training_resource

    # -------------------------------------------------------------------------
    def hrm_training_event_apply(r, **attr):
        """
            Custom S3Method to Apply to an Event
        """

        db = current.db

        record_id = r.id
        auth = current.auth
        user_id = auth.user.id

        training_id = current.s3db.hrm_training.insert(training_event_id = record_id,
                                                       person_id = auth.s3_logged_in_person(),
                                                       status = 1,
                                                       owned_by_user = user_id,
                                                       )
        # NB This is just an Application so do NOT call onaccept

        # Message OrgAdmins
        from gluon import redirect, URL
        from s3 import s3_fullname

        # Lookup the Author details
        utable = db.auth_user
        user = db(utable.id == user_id).select(utable.first_name,
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
        subject = "%s: %s has applied to participate in your Event" % \
            (settings.get_system_name_short(),
             fullname,
             )

        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="hrm", f="training_event", args=[record_id, "training", training_id]))
        message = "%s has applied to participate in your Event: %s\n\nYou can approve or decline this here: %s" % \
            (fullname,
             r.record.name,
             url,
             )

        # Send message to each
        send_email = current.msg.send_email
        for admin in org_admins:
            send_email(to = admin.email,
                       subject = subject,
                       message = message,
                       )

        # Redirect
        redirect(URL(args = [record_id, "training", training_id]))

    # -------------------------------------------------------------------------
    def hrm_training_event_notification(record, selected):
        """
            Send notification to selected Invitees
        """

        from gluon import URL
        from s3compat import basestring

        if isinstance(selected, basestring):
            # Deserialize the vars from s3task
            import json
            record = json.loads(record)
            selected = json.loads(selected)

        record_id = record.get("id")

        # Construct Email message
        event_name = record.get("name")
        system_name = settings.get_system_name_short()
        subject = "%s: You have been invited to an Event: %s" % \
            (system_name,
             event_name,
             )

        db = current.db
        s3db = current.s3db
        etable = s3db.hrm_training_event
        gtable = s3db.gis_location
        location = db(gtable.id == record.get("location_id")).select(gtable.L3,
                                                                     gtable.addr_street,
                                                                     gtable.addr_postcode,
                                                                     limitby = (0, 1)
                                                                     ).first()
        ttable = s3db.hrm_event_tag
        tags = db(ttable.training_event_id == record_id).select(ttable.tag,
                                                                ttable.value,
                                                                ).as_dict(key = "tag")

        base_url = "%s%s" % (settings.get_base_public_url(),
            URL(c="hrm", f="training_event", args=[record_id, "training"]))

        date = record.get("start_date")
        if isinstance(date, basestring):
            from s3 import s3_parse_datetime
            date = s3_parse_datetime(date, "%Y-%m-%d %H:%M:%S")

        message = "You have been invited to an Event:\n\nEvent name: %s\nEvent description: %s\nStarts: %s\nLead Organisation: %s\nVenue name: %s\nDistrict: %s\nStreet Address: %s\nPostcode: %s\nContact Name: %s\nTelephone: %s\nEmail: %s\nWebsite: %s\n\nYou can respond to the invite here: %s" % \
            (event_name,
             record.get("comments") or "",
             etable.start_date.represent(date),
             etable.organisation_id.represent(record.get("organisation_id"), show_link=False),
             tags.get("venue_name")["value"],
             location.L3,
             location.addr_street or "",
             location.addr_postcode or "",
             tags.get("contact_name")["value"] or "",
             tags.get("contact_tel")["value"] or "",
             tags.get("contact_email")["value"],
             tags.get("contact_web")["value"] or "",
             base_url,
             )

        # Send message to each
        ctable = s3db.pr_contact
        ptable = s3db.pr_person
        query = (ptable.id.belongs(selected)) & \
                (ptable.pe_id == ctable.pe_id) & \
                (ctable.contact_method == "EMAIL") & \
                (ctable.deleted == False)
        contacts = db(query).select(ptable.id,
                                    ctable.value,
                                    )
        contacts = {c["pr_person.id"]: c["pr_contact.value"] for c in contacts}

        send_email = current.msg.send_email
        for person_id in selected:
            send_email(to = contacts.get(int(person_id)),
                       subject = subject,
                       message = "%s/%s" % (message, person_id),
                       )

    settings.tasks.hrm_training_event_notification = hrm_training_event_notification

    # -------------------------------------------------------------------------
    def hrm_training_event_reminder(r, **attr):
        """
            Send reminder notification to Invitees who are Invited, Accepted or Approved
            - interactive
        """

        import json
        from gluon import redirect, URL

        ttable = current.s3db.hrm_training
        query = (ttable.training_event_id == r.id) & \
                (ttable.status.belongs(2, 4, 5)) & \
                (ttable.deleted == False)
        trainings = current.db(query).select(ttable.person_id)
        selected = [t.person_id for t in trainings]

        # Sent Reminders async as it may take some time to run
        current.s3task.run_async("settings_task",
                                 args = ["hrm_training_event_notification"],
                                 vars = {"record": r.record.as_json(),
                                         "selected": json.dumps(selected),
                                         })

        current.session.confirmation = T("Reminder sent")
        redirect(URL(args=None))

    # -------------------------------------------------------------------------
    def hrm_training_event_reminder_day(record_id):
        """
            Send reminder notification to Invitees who are Invited, Accepted or Approved
            - automated 1 day before Opportunity
        """

        db = current.db
        s3db = current.s3db

        table = s3db.hrm_training_event
        record = db(table.id == record_id).select(table.id,
                                                  table.name,
                                                  table.start_date,
                                                  table.comments,
                                                  table.location_id,
                                                  table.organisation_id,
                                                  limitby = (0, 1)
                                                  ).first()

        ttable = s3db.hrm_training
        query = (ttable.training_event_id == record_id) & \
                (ttable.status.belongs(2, 4, 5)) & \
                (ttable.deleted == False)
        trainings = db(query).select(ttable.person_id)
        selected = [t.person_id for t in trainings]

        req_need_notification(record, selected)

    settings.tasks.hrm_training_event_reminder_day = hrm_training_event_reminder_day

    # -------------------------------------------------------------------------
    def hrm_training_event_postprocess(form):
        """
            * Create Site based on other fields
            * Schedule Reminder
        """

        form_vars_get = form.vars.get

        training_event_id = form_vars_get("id")


        # Create Site based on other fields

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
                                                                   etable.organisation_id,
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
                      "organisation_id": training_event[etable.organisation_id],
                      }
            facility_id = ftable.insert(**record)
            record["id"] = facility_id
            s3db.update_super(ftable, record)
            callback = s3db.get_config("org_facility", "create_onaccept")
            if callback is None:
                callback = s3db.get_config("org_facility", "onaccept")
            if callable(callback):
                callback(Storage(vars = record))
            set_realm_entity = current.auth.set_realm_entity
            set_realm_entity(ftable, facility_id, force_update=True)
            db(etable.id == training_event_id).update(site_id = record["site_id"])
            set_realm_entity(etable, training_event_id, force_update=True)

        # Schedule Reminder

        from dateutil.relativedelta import relativedelta
        start_time = form_vars_get("start_date") - relativedelta(days = 1)
        if start_time < current.request.utcnow:
            return

        import json
        ttable = s3db.scheduler_task
        task_name = "settings_task"
        args = ["hrm_training_event_reminder_day"]
        vars = {"record_id": training_event_id}
        query = (ttable.task_name == task_name) & \
                (ttable.args == json.dumps(args)) & \
                (ttable.vars == json.dumps(vars))
        exists = db(query).select(ttable.id,
                                  ttable.start_time,
                                  limitby = (0, 1)
                                  ).first()
        if exists:
            if exists.start_time != start_time:
                exists.update_record(start_time = start_time)
        else:
            current.s3task.schedule_task("settings_task",
                                 args = ["hrm_training_event_reminder_day"],
                                 vars = {"record_id": training_event_id},
                                 start_time = start_time,
                                 #period = 300,  # seconds
                                 timeout = 300, # seconds
                                 repeats = 1    # run once
                                 )

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
                          S3OptionsFilter("location_id$L3",
                                          label = T("District"),
                                          ),
                          ]

        auth = current.auth
        if auth.s3_has_role("ADMIN"):
            filter_widgets.append(S3OptionsFilter("organisation_id",
                                                  label = T("Organization")))
            list_fields.insert(0, (T("Organization"), "organisation_id"))
            requires = table.organisation_id.requires
            if hasattr(requires, "other"):
                table.organisation_id.requires = requires.other
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

        from gluon import URL

        auth = current.auth
        s3db = current.s3db

        s3 = current.response.s3
        s3.crud.assign_button = "Invite"

        set_method = s3db.set_method

        # Ensure Tab is shown
        set_method("hrm", "training_event",
                   method = "assign",
                   action = s3db.pr_AssignMethod(component = "training"))

        set_method("hrm", "training_event",
                   method = "remind",
                   action = hrm_training_event_reminder)

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if auth.s3_has_role("RESERVE", include_admin=False):
                # Filter to just those they are invited to
                from s3 import FS
                #r.resource.add_filter(FS("participant.id") == auth.s3_logged_in_person())
                table = s3db.hrm_training
                trainings = current.db(table.person_id == auth.s3_logged_in_person()).select(table.training_event_id)
                events_invited = [t.training_event_id for t in trainings]
                r.resource.add_filter(FS("id").belongs(events_invited))
            else:
                set_method("hrm", "training_event",
                           method = "apply",
                           action = hrm_training_event_apply)

            if not r.component:
                r.resource.configure(create_next = URL(c="hrm", f="training_event",
                                                       args = ["[id]", "assign"]))
            elif r.component_name == "training":

                s3db.configure("hrm_training",
                               list_fields = ["person_id",
                                              "person_id$human_resource.organisation_id",
                                              "status",
                                              "comments",
                                              ],
                               )

            if r.method == "assign":

                from s3 import S3OptionsFilter, S3Represent, s3_str

                db = current.db

                # Filter out Donors
                gtable = db.auth_group
                #DONOR = db(gtable.uuid == "DONOR").select(gtable.id,
                #                                          limitby = (0, 1)
                #                                          ).first().id
                #s3.filter = ~(FS("user.membership.group_id") == DONOR)
                mtable = db.auth_membership
                ltable = s3db.pr_person_user
                ptable = s3db.pr_person
                query = (gtable.uuid == "DONOR") & \
                        (gtable.id == mtable.group_id) & \
                        (mtable.user_id == ltable.user_id) & \
                        (ltable.pe_id == ptable.pe_id)
                donors = db(query).select(ptable.id)
                donors = [p.id for p in donors]
                s3.filter = ~(ptable.id.belongs(donors))

                # Filtered components
                s3db.add_components("hrm_human_resource",
                                    hrm_human_resource_tag = ({"name": "job_title",
                                                               "joinby": "human_resource_id",
                                                               "filterby": {"tag": "job_title"},
                                                               "multiple": False,
                                                               },
                                                              ),
                                    )

                gtable = s3db.gis_location
                districts = db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                         gtable.name,
                                                                                         cache = s3db.cache)
                districts = {d.id:d.name for d in districts}

                s3db.pr_group_membership.group_id.represent = S3Represent(lookup = "pr_group",
                                                                          show_link = True)

                actions = [{"label": s3_str(T("Open")),
                            "url": URL(c = "pr",
                                       f = "person",
                                       args = ["[id]", "redirect"],
                                       ),
                            "_class": "action-btn",
                            },
                           ]

                filter_widgets = [S3OptionsFilter("human_resource.organisation_id"),
                                  S3OptionsFilter("person_location.location_id",
                                                  label = T("Location"),
                                                  options = districts,
                                                  ),
                                  #S3OptionsFilter("competency.skill_id"),
                                  ]

                list_fields = ["id",
                               "first_name",
                               "last_name",
                               "human_resource.organisation_id",
                               "group_membership.group_id",
                               (T("Role"), "human_resource.job_title.value"),
                               (T("Skills"), "competency.skill_id"),
                               ]

                set_method("hrm", "training_event",
                           method = "assign",
                           action = s3db.pr_AssignMethod(component = "training",
                                                         actions = actions,
                                                         filter_widgets = filter_widgets,
                                                         list_fields = list_fields,
                                                         postprocess = "hrm_training_event_notification",
                                                         title = T("Invite People"),
                                                         ))

                # Replace Callback rather than extend
                #s3db.add_custom_callback("hrm_training",
                #                         "onaccept",
                #                         hrm_training_create_onaccept,
                #                         method = "create",
                #                         )
                s3db.configure("hrm_training",
                               create_onaccept = hrm_training_create_onaccept,
                               )

            return result
        s3.prep = prep

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.component_name == "training" and \
               not auth.s3_has_role("ORG_ADMIN"):

                #from gluon import URL
                from s3 import s3_str, S3CRUD

                # Normal Action Buttons
                S3CRUD.action_buttons(r, deletable = False)

                # Custom Action Buttons
                table = s3db.hrm_training
                rows = current.db(table.status.belongs((1, 2))).select(table.id)
                restrict = [str(row.id) for row in rows]
                s3.actions += [{"label": s3_str(T("Withdraw")),
                                "url": URL(c = "hrm",
                                           f = "training_event",
                                           args = [r.id,
                                                   "training",
                                                   "[id]",
                                                   "delete",
                                                   ],
                                           ),
                                "restrict": restrict,
                                "_class": "delete-btn",
                                },
                               ]

            return output
        s3.postp = postp

        attr["rheader"] = ccc_rheader

        return attr

    settings.customise_hrm_training_event_controller = customise_hrm_training_event_controller

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineLink

        s3db = current.s3db

        s3db.org_site_facility_type.facility_type_id.label = T("Type")

        crud_form = S3SQLCustomForm("name",
                                    "code",
                                    S3SQLInlineLink(
                                          "facility_type",
                                          label = T("Type"),
                                          field = "facility_type_id",
                                          #widget = "groupedopts",
                                          cols = 3,
                                    ),
                                    #"organisation_id",
                                    "location_id",
                                    "opening_times",
                                    "contact",
                                    "phone1",
                                    "phone2",
                                    "email",
                                    "website",
                                    #S3SQLInlineComponent(
                                    #    "status",
                                    #    label = T("Status"),
                                    #    fields = ["last_contacted"],
                                    #    multiple = False,
                                    #),
                                    "obsolete",
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from gluon import IS_EMAIL, IS_EMPTY_OR, IS_IN_SET, IS_URL

        from s3 import S3OptionsFilter, S3Represent, S3SQLCustomForm, \
                       S3SQLInlineComponent, S3SQLInlineLink, S3TextFilter

        s3db = current.s3db

        # Filtered components
        s3db.add_components("org_organisation",
                            pr_contact = ({"name": "email",
                                           "joinby": "pe_id",
                                           "multiple": False,
                                           "filterby": {"contact_method": "EMAIL",
                                                        },
                                           },
                                          {"name": "facebook",
                                           "joinby": "pe_id",
                                           "multiple": False,
                                           "filterby": {"contact_method": "FACEBOOK",
                                                        },
                                           },
                                          {"name": "twitter",
                                           "joinby": "pe_id",
                                           "multiple": False,
                                           "filterby": {"contact_method": "TWITTER",
                                                        },
                                           },
                                          {"name": "sm_other",
                                           "joinby": "pe_id",
                                           "multiple": False,
                                           "filterby": {"contact_method": "OTHER",
                                                        },
                                           },
                                          ),
                            org_organisation_tag = ({"name": "sm_other_type",
                                                     "joinby": "organisation_id",
                                                     "multiple": False,
                                                     "filterby": {"tag": "sm_other_type",
                                                                  },
                                                     },
                                                    ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        email = components_get("email")
        f = email.table.value
        f.requires = IS_EMPTY_OR(IS_EMAIL())

        facebook = components_get("facebook")
        f = facebook.table.value
        f.requires = IS_EMPTY_OR(IS_URL())

        #twitter = components_get("twitter")
        #f = twitter.table.value
        #f.requires = IS_EMPTY_OR(None)

        #sm_other = components_get("sm_other")
        #f = sm_other.table.value
        #f.requires = IS_EMPTY_OR(None)

        gtable = s3db.gis_location
        districts = current.db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                         gtable.name,
                                                                                         cache = s3db.cache)
        districts = {d.id:d.name for d in districts}

        f = s3db.org_organisation_location.location_id
        f.represent = S3Represent(lookup = "gis_location")
        f.requires = IS_EMPTY_OR(IS_IN_SET(districts))
        f.widget = None

        s3db.configure("org_organisation",
                       crud_form = S3SQLCustomForm((T("Name of Organization"), "name"),
                                                   S3SQLInlineLink("organisation_type",
                                                                   field = "organisation_type_id",
                                                                   label = T("Type"),
                                                                   ),
                                                   S3SQLInlineLink("location",
                                                                   field = "location_id",
                                                                   label = T("District"),
                                                                   ),
                                                   S3SQLInlineComponent(
                                                        "email",
                                                        name = "email",
                                                        label = T("Email"),
                                                        multiple = False,
                                                        fields = [("", "value")],
                                                        #filterby = {"field": "contact_method",
                                                        #            "options": "EMAIL",
                                                        #            },
                                                        ),
                                                   S3SQLInlineComponent(
                                                        "facebook",
                                                        name = "facebook",
                                                        label = T("Facebook"),
                                                        multiple = False,
                                                        fields = [("", "value")],
                                                        #filterby = {"field": "contact_method",
                                                        #            "options": "FACEBOOK",
                                                        #            },
                                                        ),
                                                   S3SQLInlineComponent(
                                                        "twitter",
                                                        name = "twitter",
                                                        label = T("Twitter"),
                                                        multiple = False,
                                                        fields = [("", "value")],
                                                        #filterby = {"field": "contact_method",
                                                        #            "options": "TWITTER",
                                                        #            },
                                                        ),
                                                   S3SQLInlineComponent(
                                                        "sm_other",
                                                        name = "sm_other",
                                                        label = T("SM Other"),
                                                        multiple = False,
                                                        fields = [("", "value")],
                                                        #filterby = {"field": "contact_method",
                                                        #            "options": "OTHER",
                                                        #            },
                                                        ),
                                                   (T("Please Specify"), "sm_other_type.value"),
                                                   "website",
                                                   "comments",
                                                   ),
                       list_fields = ["name",
                                      (T("Type"), "organisation_organisation_type.organisation_type_id"),
                                      (T("Locations Served"), "organisation_location.location_id"),
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

        s3 = current.response.s3

        #current.s3db.set_method("org", "organisation",
        #                        method = "message",
        #                        action = org_organisation_message)

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if not r.id and r.http == "POST":
                # Bulk Action 'Message' has been selected
                post_vars = r.post_vars
                selected = post_vars.selected
                if selected:
                    selected = selected.split(",")
                else:
                    selected = []

                # Handle exclusion filter
                if post_vars.mode == "Exclusive":
                    if "filterURL" in post_vars:
                        from s3 import S3URLQuery
                        filters = S3URLQuery.parse_url(post_vars.filterURL)
                    else:
                        filters = None
                    from s3 import FS
                    query = ~(FS("id").belongs(selected))
                    resource = current.s3db.resource("org_organisation",
                                                     filter = query,
                                                     vars = filters)
                    rows = resource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

                # NB This method of passing selected to the next page is limited by GET URL lengths
                #    but this should be OK for this usecase
                from gluon import redirect, URL
                redirect(URL(c="project", f="task",
                             args = "create",
                             vars = {"o": ",".join(selected)}))

            return result
        s3.prep = prep

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive and not r.component:

                from gluon import URL
                from s3 import s3_str, S3CRUD

                # Normal Action Buttons
                S3CRUD.action_buttons(r)

                # Custom Action Buttons
                s3.actions += [{"label": s3_str(T("Message")),
                                "url": URL(c = "project",
                                           f = "task",
                                           args = "create",
                                           vars = {"organisation_id": "[id]"}
                                           ),
                                "_class": "action-btn",
                                },
                               ]

            return output
        s3.postp = postp

        attr["dtargs"] = {"dt_bulk_actions": [(T("Message"), "message")],
                          }
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
    def pr_group_postprocess(form):
        """
            Sync Location & Skills to Leaders
        """

        group_id = form.vars.id

        db = current.db
        s3db = current.s3db

        # Lookup Leaders
        mtable = s3db.pr_group_membership
        members = db(mtable.group_id == group_id).select(mtable.person_id)
        members = [m.person_id for m in members]

        # Read Group's current Values
        ltable = s3db.pr_group_location
        stable = s3db.pr_group_competency
        locations = db(ltable.group_id == group_id).select(ltable.location_id)
        locations = [l.location_id for l in locations]
        skills = db(stable.group_id == group_id).select(stable.skill_id)
        skills = [s.skill_id for s in skills]

        # Clear old Values from Leaders
        ltable = s3db.pr_person_location
        stable = s3db.hrm_competency
        db(ltable.person_id.belongs(members)).delete()
        db(stable.person_id.belongs(members)).delete()

        # Add new Values to Leaders
        linsert = ltable.insert
        sinsert = stable.insert
        for person_id in members:
            for location_id in locations:
                linsert(person_id = person_id,
                        location_id = location_id,
                        )
            for skill_id in skills:
                sinsert(person_id = person_id,
                        skill_id = skill_id,
                        )

    # -------------------------------------------------------------------------
    def customise_pr_group_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_IN_SET, IS_INT_IN_RANGE, IS_NOT_EMPTY, \
                          SQLFORM
        from s3 import IS_INT_AMOUNT, S3OptionsFilter, S3Represent, \
                       S3SQLCustomForm, S3SQLInlineLink, S3TextFilter, \
                       s3_phone_requires

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
                                            {"name": "faith_requirements",
                                             "joinby": "group_id",
                                             "filterby": {"tag": "faith_requirements"},
                                             "multiple": False,
                                             },
                                            {"name": "faith_requirements_details",
                                             "joinby": "group_id",
                                             "filterby": {"tag": "faith_requirements_details"},
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

        faith_requirements = components_get("faith_requirements")
        f = faith_requirements.table.value
        f.requires = IS_IN_SET({"0": T("No"),
                                "1": T("Yes"),
                                })
        f.widget = lambda f, v: \
                        SQLFORM.widgets.radio.widget(f, v,
                                                     style="divs")

        contact_name = components_get("contact_name")
        f = contact_name.table.value
        f.requires = IS_NOT_EMPTY()
        f.comment = T("Contact must not be listed as a leader")

        contact_number = components_get("contact_number")
        f = contact_number.table.value
        f.requires = s3_phone_requires

        s3db.pr_group_location.location_id.represent = S3Represent(lookup = "gis_location")

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
                                                   (T("Do you have any faith requirements that you would like help with if you are coming to Support Cumbria?"), "faith_requirements.value"),
                                                   (T("If Yes please outline"), "faith_requirements_details.value"),
                                                   (T("Emergency Contact Name"), "contact_name.value"),
                                                   (T("Emergency Contact Number"), "contact_number.value"),
                                                   "comments",
                                                   postprocess = pr_group_postprocess,
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
        table.person_id.widget = S3AddPersonWidget(controller = "pr")

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
        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        s3db = current.s3db

        # Filtered components
        s3db.add_components("pr_person",
                            pr_person_tag = ({"name": "organisation",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "organisation"},
                                              "multiple": False,
                                              },
                                             #{"name": "organisation_type",
                                             # "joinby": "person_id",
                                             # "filterby": {"tag": "organisation_type"},
                                             # "multiple": False,
                                             # },
                                             #{"name": "items_details",
                                             # "joinby": "person_id",
                                             # "filterby": {"tag": "items_details"},
                                             # "multiple": False,
                                             # },
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

        #organisation_type = components_get("organisation_type")
        #f = organisation_type.table.value
        #f.requires = IS_EMPTY_OR(IS_IN_SET([T("Business Donor"),
        #                                    T("Individual Donor"),
        #                                    T("Public Sector Organization"),
        #                                    T("Voluntary Sector Organization"),
        #                                    ]))

        delivery = components_get("delivery")
        f = delivery.table.value
        f.requires = IS_EMPTY_OR(IS_IN_SET(("Y", "N")))
        f.represent = lambda v: T("yes") if v == "Y" else T("no")
        from s3 import S3TagCheckboxWidget
        f.widget = S3TagCheckboxWidget(on="Y", off="N")
        f.default = "N"
        f.comment = T("Please indicate if you can deliver the item/s at no cost?")

        get_vars_get = r.get_vars.get
        has_role = current.auth.s3_has_role
        if get_vars_get("donors") or \
           has_role("DONOR", include_admin=False):
            # Donor
            stable = s3db.supply_person_item_status
            status = current.db(stable.name == "Available").select(stable.id,
                                                                   limitby = (0, 1)
                                                                   ).first()
            if status:
                s3db.supply_person_item.status_id.default = status.id
            crud_fields = ["first_name",
                           "middle_name",
                           "last_name",
                           "date_of_birth",
                           (T("Gender"), "gender"),
                           (T("Name of Organization"), "organisation.value"),
                           #(T("Type of Organization"), "organisation_type.value"),
                           #S3SQLInlineLink("item",
                           #                field = "item_id",
                           #                label = T("Goods / Services"),
                           #                ),
                           #(T("Details"), "items_details.value"),
                           S3SQLInlineComponent("person_item",
                                                label = "",
                                                fields = [(T("Goods / Services"), "item_id"),
                                                          (T("Details"), "comments"),
                                                          (T("Status"), "status_id"),
                                                          (T("Requested By"), "organisation_id"),
                                                          ],
                                                ),
                           (T("Are you able to Deliver?"), "delivery.value"),
                           S3SQLInlineLink("location",
                                           field = "location_id",
                                           label = T("Where would you be willing to deliver?"),
                                           ),
                           (T("Please indicate if the offer is only available for a period of time (please state) or an open ended offer. Household items, such as furniture, are normally not required for some months but very gratefully received at the right time"), "availability.value"),
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
    def affiliation_create_onaccept(form):
        """
            If a RESERVE Volunteer is affiliated to an Organisation, update their user/roles accordingly
        """

        auth = current.auth
        db = current.db
        s3db = current.s3db
        human_resource_id = form.vars.get("id")

        hrtable = s3db.hrm_human_resource
        hr = db(hrtable.id == human_resource_id).select(hrtable.person_id,
                                                        hrtable.organisation_id,
                                                        limitby = (0, 1)
                                                        ).first()

        ptable = s3db.pr_person
        putable = s3db.pr_person_user
        query = (ptable.id == hr.person_id) & \
                (ptable.pe_id == putable.pe_id)
        link = db(query).select(putable.user_id,
                                limitby = (0, 1)
                                ).first()
        user_id = link.user_id

        utable = db.auth_user
        user = db(utable.id == user_id).select(utable.id,
                                               utable.organisation_id,
                                               limitby = (0, 1)
                                               ).first()
        if not user.organisation_id:
            user.update_record(organisation_id = hr.organisation_id)

        gtable = db.auth_group
        mtable = db.auth_membership
        query = (mtable.user_id == user_id) & \
                (mtable.group_id == gtable.id)
        roles = db(query).select(gtable.uuid)
        roles = [r.uuid for r in roles]

        if "RESERVE" in roles:
            auth.s3_withdraw_role(user_id, "RESERVE", for_pe=[])

        auth.s3_assign_role(user_id, "VOLUNTEER")

    # -----------------------------------------------------------------------------
    def pr_person_redirect(r, **attr):
        """
            Redirect to the person page with the relevant get_vars active
        """

        from gluon import redirect, URL

        person_id = r.id

        db = current.db
        s3db = current.s3db

        # Is this person a member of a Group?
        mtable = s3db.pr_group_membership
        member = db(mtable.person_id == person_id).select(mtable.id,
                                                          limitby = (0, 1)
                                                          ).first()
        if member:
            redirect(URL(c="pr", f="person", args=[person_id], vars={"groups": 1}))

        pe_id = r.record.pe_id

        # Is this person a Reserve Volunteer?
        gtable = db.auth_group
        mtable = db.auth_membership
        ltable = s3db.pr_person_user
        query = (ltable.pe_id == pe_id) & \
                (ltable.user_id == mtable.user_id) & \
                (mtable.group_id == gtable.id) & \
                (gtable.uuid == "RESERVE")
        reserve = db(query).select(ltable.id,
                                   limitby = (0, 1)
                                   ).first()
        if reserve:
            redirect(URL(c="pr", f="person", args=[person_id], vars={"reserves": 1}))

        # Is this person a Donor?
        #query = (ltable.pe_id == pe_id) & \
        #        (ltable.user_id == mtable.user_id) & \
        #        (mtable.group_id == gtable.id) & \
        #        (gtable.uuid == "DONOR")
        #donor = db(query).select(ltable.id,
        #                         limitby = (0, 1)
        #                         ).first()
        #if donor:
        #    redirect(URL(c="pr", f="person", args=[person_id], vars={"donors": 1}))

        # Redirect to Normal person profile
        redirect(URL(c="pr", f="person", args=[person_id]))

    # -----------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db

        # Custom Component
        s3db.add_components("pr_person",
                            hrm_human_resource = {"joinby": "person_id",
                                                  "multiple": False,
                                                  },
                            pr_group = {"link": "pr_group_membership",
                                        "joinby": "person_id",
                                        "key": "group_id",
                                        "actuate": "replace",
                                        "multiple": False,
                                        },
                            )

        # Custom Methods
        from templates.CCC.controllers import personAdditional
        set_method = s3db.set_method
        set_method("pr", "person",
                   method = "additional",
                   action = personAdditional)
        set_method("pr", "person",
                   method = "redirect",
                   action = pr_person_redirect)

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component_name == "human_resource":

                s3.crud_strings["hrm_human_resource"] = Storage(
                    label_create = T("New Affiliation"),
                    #title_display = T("Affiliation Details"),
                    #title_list = T("Affiliations"),
                    title_update = T("Edit Affiliation"),
                    #title_upload = T("Import Affiliations"),
                    #label_list_button = T("List Affiliations"),
                    label_delete_button = T("Delete Affiliation"),
                    msg_record_created = T("Affiliation added"),
                    msg_record_modified = T("Affiliation updated"),
                    msg_record_deleted = T("Affiliation deleted"),
                    #msg_list_empty = T("No Affiliations currently registered")
                    )

                s3db.add_custom_callback("hrm_human_resource",
                                         "onaccept",
                                         affiliation_create_onaccept,
                                         method = "create",
                                         )

                # Only needed if multiple=True
                #list_fields = ["organisation_id",
                #               (T("Role"), "job_title.value"),
                #               "comments",
                #               ]
                #r.component.configure(list_fields = list_fields)

            elif r.component_name == "group_membership":
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

            if not r.component:
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
                * Duplicate Message if sending to multiple Organisations
                * Set Realm Entity
                * Notify OrgAdmins
        """

        from gluon import URL
        from s3 import s3_fullname

        form_vars_get = form.vars.get
        task_id = form_vars_get("id")

        # Lookup the Author details
        db = current.db
        s3db = current.s3db
        otable = s3db.org_organisation
        ttable = s3db.project_task
        utable = db.auth_user
        query = (ttable.id == task_id) & \
                (ttable.created_by == utable.id)
        user = db(query).select(utable.first_name,
                                utable.last_name,
                                utable.organisation_id,
                                limitby = (0, 1)
                                ).first()
        fullname = s3_fullname(user)

        # Construct Email message
        system_name = settings.get_system_name_short()
        subject = "%s: Message sent from %s" % \
            (system_name,
             fullname,
             )

        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="project", f="task"))
        message = "%s has sent you a Message on %s\n\nSubject: %s\nMessage: %s\n\nYou can view the message here: %s" % \
            (fullname,
             system_name,
             form_vars_get("name"),
             form_vars_get("description") or "",
             url,
             )

        get_vars_get = current.request.get_vars.get
        organisation_ids = get_vars_get("o")
        if organisation_ids is not None:
            # Sending to a list of Organisations from the Bulk Action

            organisation_ids = organisation_ids.split(",")

            # Lookup the ORG_ADMINs
            gtable = db.auth_group
            mtable = db.auth_membership
            query = (gtable.uuid == "ORG_ADMIN") & \
                    (gtable.id == mtable.group_id) & \
                    (mtable.user_id == utable.id) & \
                    (utable.organisation_id.belongs(organisation_ids))
            org_admins = db(query).select(utable.organisation_id,
                                          utable.email)
            orgs = {organisation_id: {"emails": []} for organisation_id in organisation_ids}
            for admin in org_admins:
                orgs[str(admin.organisation_id)]["emails"].append(admin.email)

            # Create a clone of Message (Task) per Org
            task = db(ttable.id == task_id).select(ttable.name,
                                                   ttable.description,
                                                   #ttable.created_by,
                                                   limitby = (0, 1)
                                                   ).first()
            name = task.name
            description = task.description
            #created_by = task.created_by

            first = True
            for organisation_id in organisation_ids:
                if first:
                    orgs[organisation_id]["task_id"] = task_id
                    first = False
                    continue
                task_id = ttable.insert(name = name,
                                        description = description,
                                        #created_by = created_by,
                                        )
                orgs[organisation_id]["task_id"] = task_id

            # Set Realm Entities
            # Send email to each OrgAdmin
            send_email = current.msg.send_email
            for organisation_id in orgs:
                task_id = orgs[organisation_id]["task_id"]

                # Set the Realm Entity
                org = db(otable.id == organisation_id).select(otable.pe_id,
                                                              limitby = (0, 1)
                                                              ).first()
                try:
                    db(ttable.id == task_id).update(realm_entity = org.pe_id)
                except AttributeError:
                    pass

                # Send Emails
                this_message = "%s/%s" % (message, task_id)
                org_admins = orgs[organisation_id]["emails"]
                for email in org_admins:
                    send_email(to = email,
                               subject = subject,
                               message = this_message,
                               )

        else:
            person_item_id = current.request.get_vars.get("person_item_id")
            if person_item_id:
                # Sending to a Donor

                # Lookup the person_id
                stable = s3db.supply_person_item
                person_item = db(stable.id == person_item_id).select(stable.person_id,
                                                                     limitby = (0, 1)
                                                                     ).first()
                try:
                    person_id = person_item.person_id
                except AttributeError:
                    return

                # Lookup the pe_id
                ptable = s3db.pr_person
                person = db(ptable.id == person_id).select(ptable.pe_id,
                                                           limitby = (0, 1)
                                                           ).first()
                try:
                    pe_id = person.pe_id
                except AttributeError:
                    return

                # Set the Realm Entity
                db(ttable.id == task_id).update(realm_entity = pe_id)

                # Append the task_id to the URL
                message = "%s/%s" % (message, task_id)

                # Lookup the Donor's Email
                ctable = s3db.pr_contact
                query = (ctable.pe_id == pe_id) & \
                        (ctable.contact_method == "EMAIL") & \
                        (ctable.deleted == False)
                donor = db(query).select(ctable.value,
                                         limitby = (0, 1)
                                         ).first()
                try:
                    email = donor.value
                except AttributeError:
                    return

                # Send message
                current.msg.send_email(to = email,
                                       subject = subject,
                                       message = message,
                                       )
                
            else:
                # Use the Organisation we request or fallback to the User's Organisation
                organisation_id = get_vars_get("organisation_id", user.organisation_id)

                # Set the Realm Entity
                org = db(otable.id == organisation_id).select(otable.pe_id,
                                                              limitby = (0, 1)
                                                              ).first()
                try:
                    db(ttable.id == task_id).update(realm_entity = org.pe_id)
                except AttributeError:
                    pass

                # Append the task_id to the URL
                message = "%s/%s" % (message, task_id)

                # Lookup the ORG_ADMINs
                gtable = db.auth_group
                mtable = db.auth_membership
                query = (gtable.uuid == "ORG_ADMIN") & \
                        (gtable.id == mtable.group_id) & \
                        (mtable.user_id == utable.id) & \
                        (utable.organisation_id == organisation_id)
                org_admins = db(query).select(utable.email)

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
        if r.method == "create":
            table.comments.readable = table.comments.writable = False
        else:
            has_role = current.auth.s3_has_role
            if has_role("ORG_ADMIN") or \
               has_role("DONOR"):
                table.created_by.readable = True
                table.created_by.label = T("From")
                table.created_by.represent = s3db.auth_UserRepresent(show_phone = True,
                                                                     show_link = False)
                table.created_on.readable = True
                table.created_on.label = T("Date Sent")
                table.realm_entity.readable = True
                table.realm_entity.label = T("To")
                table.realm_entity.represent = s3db.pr_PersonEntityRepresent(show_label = False,
                                                                             show_type = False)
                table.name.writable = False
                table.description.writable = False
                table.description.comment = None

        s3db.configure("project_task",
                       # Can simply replace the default one
                       create_onaccept = project_task_create_onaccept,
                       crud_form = S3SQLCustomForm("created_by",
                                                   "created_on",
                                                   "realm_entity",
                                                   "name",
                                                   "description",
                                                   #"priority",
                                                   #"status",
                                                   #"pe_id",
                                                   "comments",
                                                   ),
                       listadd = False,
                       list_fields = [#"priority",
                                      #"status",
                                      #"pe_id",
                                      "created_on",
                                      "created_by",
                                      "realm_entity",
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

        s3 = current.response.s3

        auth = current.auth
        has_role = auth.s3_has_role
        if has_role("ORG_ADMIN") or \
           has_role("DONOR"):
            READER = True
        else:
            # Can only send messages
            READER = False

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            person_item_id = r.get_vars.get("person_item_id")
            if person_item_id:
                # Donor being messaged about an Item
                db = current.db
                s3db = current.s3db
                pitable = s3db.supply_person_item
                if r.http == "POST":
                    pistable = s3db.supply_person_item_status
                    query = (pitable.id == person_item_id) & \
                            (pistable.id == pitable.status_id)
                    status = db(query).select(pistable.name,
                                              limitby = (0, 1)
                                              ).first()
                    if status.name == "Available":
                        status = db(pistable.name == "Requested").select(pistable.id,
                                                                         limitby = (0, 1)
                                                                         ).first()
                        try:
                            REQUESTED = status.id
                        except:
                            # Status has been deleted or not prepopped
                            pass
                        else:
                            db(pitable.id == person_item_id).update(status_id = REQUESTED,
                                                                    organisation_id = auth.user.organisation_id,
                                                                    )
                else:
                    itable = s3db.supply_item
                    query = (pitable.id == person_item_id) & \
                            (itable.id == pitable.item_id)
                    item = db(query).select(itable.name,
                                            limitby = (0, 1)
                                            ).first()
                    try:
                        s3db.project_task.name.default = "re: %s" % item.name
                    except:
                        pass

            if r.method == "create":
                s3.crud.submit_button = "Send" # T() Happens in s3forms.py
            elif not READER:
                #if r.method not in ("create", "read", "update"):
                if r.method not in ("read", "update"):
                    from gluon import redirect
                    redirect(r.url(method = "create"))
                else:
                    #s3.crud.submit_button = "Send" # T() Happens in s3forms.py
                    current.messages.UPDATE = "Edit"
                    # Don't attempt to load comments
                    s3.rfooter = None

            return result
        s3.prep = prep

        if not READER:
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
    def req_need_onaccept(form):
        """
            Schedule Reminder
        """

        form_vars_get = form.vars.get

        from dateutil.relativedelta import relativedelta
        start_time = form_vars_get("date") - relativedelta(days = 1)
        if start_time < current.request.utcnow:
            return

        need_id = form_vars_get("id")

        import json
        ttable = current.s3db.scheduler_task
        task_name = "settings_task"
        start_time = form_vars_get("date") - relativedelta(days = 1)
        args = ["req_need_reminder_day"]
        vars = {"record_id": need_id}
        query = (ttable.task_name == task_name) & \
                (ttable.args == json.dumps(args)) & \
                (ttable.vars == json.dumps(vars))
        exists = current.db(query).select(ttable.id,
                                          ttable.start_time,
                                          limitby = (0, 1)
                                          ).first()
        if exists:
            if exists.start_time != start_time:
                exists.update_record(start_time = start_time)
        else:
            current.s3task.schedule_task("settings_task",
                                 args = ["req_need_reminder_day"],
                                 vars = {"record_id": need_id},
                                 start_time = start_time,
                                 #period = 300,  # seconds
                                 timeout = 300, # seconds
                                 repeats = 1    # run once
                                 )

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
    def req_need_apply(r, **attr):
        """
            Custom S3Method to Apply to an Opportunity
        """

        db = current.db

        record_id = r.id
        auth = current.auth
        user_id = auth.user.id

        need_person_id = current.s3db.req_need_person.insert(need_id = record_id,
                                                             person_id = auth.s3_logged_in_person(),
                                                             status = 1,
                                                             owned_by_user = user_id,
                                                             )
        # No onaccept needed

        # Message OrgAdmins
        from gluon import redirect, URL
        from s3 import s3_fullname

        # Lookup the Author details
        utable = db.auth_user
        user = db(utable.id == user_id).select(utable.first_name,
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
        subject = "%s: %s has applied to participate in your Opportunity" % \
            (settings.get_system_name_short(),
             fullname,
             )

        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="req", f="need",
                            args=[record_id, "need_person", need_person_id],
                            )
                        )
        message = "%s has applied to participate in your Opportunity: %s\n\nYou can approve or decline this here: %s" % \
            (fullname,
             r.record.name,
             url,
             )

        # Send message to each
        send_email = current.msg.send_email
        for admin in org_admins:
            send_email(to = admin.email,
                       subject = subject,
                       message = message,
                       )

        # Redirect
        redirect(URL(args = [record_id, "need_person", need_person_id]))

    # -------------------------------------------------------------------------
    def req_need_notification(record, selected):
        """
            Send notification to selected Invitees
        """

        from gluon import URL
        from s3compat import basestring

        if isinstance(selected, basestring):
            # Deserialize the vars from s3task
            import json
            record = json.loads(record)
            selected = json.loads(selected)

        record_id = record.get("id")

        # Construct Email message
        event_name = record.get("name")
        system_name = settings.get_system_name_short()
        subject = "%s: You have been invited to an Opportunity: %s" % \
            (system_name,
             event_name,
             )

        db = current.db
        s3db = current.s3db
        ntable = s3db.req_need
        notable = s3db.req_need_organisation
        otable = s3db.org_organisation
        query = (notable.need_id == record_id) & \
                (notable.organisation_id == otable.id)
        organisation = db(query).select(otable.name,
                                        limitby = (0, 1)
                                        ).first().name
        gtable = s3db.gis_location
        location = db(gtable.id == record.get("location_id")).select(gtable.L3,
                                                                     gtable.addr_street,
                                                                     gtable.addr_postcode,
                                                                     limitby = (0, 1)
                                                                     ).first()
        nctable = s3db.req_need_contact
        contact = db(nctable.need_id == record_id).select(nctable.person_id,
                                                          limitby = (0, 1)
                                                          ).first()
        contact = s3db.pr_PersonRepresentContact(show_email = True,
                                                 show_link = False)(contact.person_id)
        stable = s3db.hrm_skill
        nstable = s3db.req_need_skill
        query = (nstable.need_id == record_id) & \
                (nstable.skill_id == stable.id)
        skill = db(query).select(stable.name,
                                 limitby = (0, 1)
                                 ).first()
        if skill:
            skill = skill.name
        else:
            skill = ""
        ttable = s3db.req_need_tag
        tags = db(ttable.need_id == record_id).select(ttable.tag,
                                                      ttable.value,
                                                      ).as_dict(key = "tag")

        base_url = "%s%s" % (settings.get_base_public_url(),
            URL(c="req", f="need", args=[record_id, "need_person"]))

        date = record.get("date")
        if isinstance(date, basestring):
            from s3 import s3_parse_datetime
            date = s3_parse_datetime(date, "%Y-%m-%d %H:%M:%S")

        message = "You have been invited to an Opportunity:\n\nTitle: %s\nOrganisation: %s\nStart Date: %s\nDistrict: %s\nStreet Address: %s\nPostcode: %s\nDescription: %s\nContact: %s\nSkill: %s\nAge Restrictions: %s\nPractical Information: %s\nParking Options: %s\nWhat to Bring: %s\n\nYou can respond to the invite here: %s" % \
            (event_name,
             organisation,
             ntable.date.represent(date),
             location.L3,
             location.addr_street or "",
             location.addr_postcode or "",
             record.get("description") or "",
             contact,
             skill,
             tags.get("age_restrictions")["value"] or "",
             tags.get("practical_info")["value"] or "",
             tags.get("parking")["value"] or "",
             tags.get("bring")["value"] or "",
             base_url,
             )

        # Send message to each
        ctable = s3db.pr_contact
        ptable = s3db.pr_person
        query = (ptable.id.belongs(selected)) & \
                (ptable.pe_id == ctable.pe_id) & \
                (ctable.contact_method == "EMAIL") & \
                (ctable.deleted == False)
        contacts = db(query).select(ptable.id,
                                    ctable.value,
                                    )
        contacts = {c["pr_person.id"]: c["pr_contact.value"] for c in contacts}
        nptable = s3db.req_need_person
        links = db(nptable.person_id.belongs(selected)).select(nptable.person_id,
                                                               nptable.id,
                                                               )
        links = {l.person_id: l.id for l in links}

        send_email = current.msg.send_email
        for person_id in selected:
            person_id = int(person_id)
            send_email(to = contacts.get(person_id),
                       subject = subject,
                       message = "%s/%s" % (message, links.get(person_id)),
                       )

    settings.tasks.req_need_notification = req_need_notification

    # -------------------------------------------------------------------------
    def req_need_reminder(r, **attr):
        """
            Send reminder notification to Invitees who are Invited, Accepted or Approved
            - interactive
        """

        import json
        from gluon import redirect, URL

        nptable = current.s3db.req_need_person
        query = (nptable.need_id == r.id) & \
                (nptable.status.belongs(2, 4, 5)) & \
                (nptable.deleted == False)
        links = current.db(query).select(nptable.person_id)
        selected = [l.person_id for l in links]

        # Sent Reminders async as it may take some time to run
        current.s3task.run_async("settings_task",
                                 args = ["req_need_notification"],
                                 vars = {"record": r.record.as_json(),
                                         "selected": json.dumps(selected),
                                         })

        current.session.confirmation = T("Reminder sent")
        redirect(URL(args=None))

    # -------------------------------------------------------------------------
    def req_need_reminder_day(record_id):
        """
            Send reminder notification to Invitees who are Invited, Accepted or Approved
            - automated 1 day before Opportunity
        """

        db = current.db
        s3db = current.s3db

        table = s3db.req_need
        record = db(table.id == record_id).select(table.id,
                                                  table.name,
                                                  table.date,
                                                  table.description,
                                                  table.location_id,
                                                  limitby = (0, 1)
                                                  ).first()

        nptable = s3db.req_need_person
        query = (nptable.need_id == record_id) & \
                (nptable.status.belongs(2, 4, 5)) & \
                (nptable.deleted == False)
        links = db(query).select(nptable.person_id)
        selected = [l.person_id for l in links]

        req_need_notification(record, selected)

    settings.tasks.req_need_reminder_day = req_need_reminder_day

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
        table.name.label = T("Title")
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
                                        "description",
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

        list_fields = ["name",
                       "date",
                       "end_date",
                       "location_id",
                       "description",
                       "need_contact.person_id",
                       #(T("Phone"), "need_contact.person_id$phone.value"),
                       #(T("Email"), "need_contact.person_id$email.value"),
                       "need_skill.skill_id",
                       "need_skill.quantity",
                       ]

        auth = current.auth
        if auth.s3_has_role("ADMIN"):
            filter_widgets.insert(-1, S3OptionsFilter("need_organisation.organisation_id"))
            list_fields.insert(0, "need_organisation.organisation_id")
        else:
            organisation_id = auth.user.organisation_id
            f = s3db.req_need_organisation.organisation_id
            f.default = organisation_id
            # Needs to be in the form
            #f.readable = f.writable = False
            #f.requires = s3db.org_organisation_requires(updateable = True)
            from gluon import IS_IN_SET
            f.requires = IS_IN_SET({organisation_id: s3db.org_organisation[organisation_id].name}, zero=None)
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
                       crud_form = S3SQLCustomForm("name",
                                                   "need_organisation.organisation_id",
                                                   "date",
                                                   "end_date",
                                                   "location_id",
                                                   "description",
                                                   "need_contact.person_id",
                                                   S3SQLInlineComponent("need_skill",
                                                                        label = "",
                                                                        fields = ["skill_id",
                                                                                  "quantity",
                                                                                  ],
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
                       onaccept = req_need_onaccept,
                       )

        s3db.configure("req_need_organisation",
                       onaccept = req_need_organisation_onaccept,
                       )

    settings.customise_req_need_resource = customise_req_need_resource

    # -----------------------------------------------------------------------------
    def customise_req_need_controller(**attr):

        auth = current.auth
        s3db = current.s3db
        s3 = current.response.s3

        s3.crud.assign_button = "Invite"

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            set_method = s3db.set_method

            #if r.method == "read":
            #    # Show the Contact's Phone & Email
            #    # @ToDo: Do this only for Vols whose Application has been succesful
            #    # @ToDo: Create custom version of this which bypasses ACLs since
            #    #        - Will fail for normal Vols as they can't see other Vols anyway
            #    #        - Also failing for OrgAdmin as the user-added Phone is in the Personal PE not the Org's
            #    s3db.req_need_contact.person_id.represent = s3db.pr_PersonRepresentContact(show_email = True,
            #                                                                               show_link = False,
            #                                                                               )

            if auth.s3_has_role("RESERVE", include_admin=False):
                # Filter to just those they are invited to
                from s3 import FS
                #r.resource.add_filter(FS("need_person.person_id") == auth.s3_logged_in_person())
                table = s3db.req_need_person
                links = current.db(table.person_id == auth.s3_logged_in_person()).select(table.need_id)
                needs_invited = [l.need_id for l in links]
                r.resource.add_filter(FS("id").belongs(needs_invited))
            else:
                set_method("req", "need",
                           method = "apply",
                           action = req_need_apply)

                set_method("req", "need",
                           method = "remind",
                           action = req_need_reminder)

            if not r.component:
                from gluon import URL
                r.resource.configure(create_next = URL(c="req", f="need",
                                                       args = ["[id]", "assign"]))

            if r.method == "assign":

                from gluon import URL
                #from s3 import FS, S3OptionsFilter, S3Represent, s3_str
                from s3 import S3OptionsFilter, S3Represent, s3_str

                db = current.db

                # Filter out Donors
                gtable = db.auth_group
                #DONOR = db(gtable.uuid == "DONOR").select(gtable.id,
                #                                          limitby = (0, 1)
                #                                          ).first().id
                #s3.filter = ~(FS("user.membership.group_id") == DONOR)
                mtable = db.auth_membership
                ltable = s3db.pr_person_user
                ptable = s3db.pr_person
                query = (gtable.uuid == "DONOR") & \
                        (gtable.id == mtable.group_id) & \
                        (mtable.user_id == ltable.user_id) & \
                        (ltable.pe_id == ptable.pe_id)
                donors = db(query).select(ptable.id)
                donors = [p.id for p in donors]
                s3.filter = ~(ptable.id.belongs(donors))

                # Filtered components
                s3db.add_components("hrm_human_resource",
                                    hrm_human_resource_tag = ({"name": "job_title",
                                                               "joinby": "human_resource_id",
                                                               "filterby": {"tag": "job_title"},
                                                               "multiple": False,
                                                               },
                                                              ),
                                    )

                gtable = s3db.gis_location
                districts = db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                         gtable.name,
                                                                                         cache = s3db.cache)
                districts = {d.id:d.name for d in districts}

                s3db.pr_group_membership.group_id.represent = S3Represent(lookup = "pr_group",
                                                                          show_link = True)

                actions = [{"label": s3_str(T("Open")),
                            "url": URL(c = "pr",
                                       f = "person",
                                       args = ["[id]", "redirect"],
                                       ),
                            "_class": "action-btn",
                            },
                           ]

                filter_widgets = [S3OptionsFilter("human_resource.organisation_id"),
                                  S3OptionsFilter("person_location.location_id",
                                                  label = T("Location"),
                                                  options = districts,
                                                  ),
                                  S3OptionsFilter("competency.skill_id"),
                                  ]

                list_fields = ["id",
                               "first_name",
                               "last_name",
                               "human_resource.organisation_id",
                               "group_membership.group_id",
                               (T("Role"), "human_resource.job_title.value"),
                               (T("Skills"), "competency.skill_id"),
                               ]

                set_method("req", "need",
                           method = "assign",
                           action = s3db.pr_AssignMethod(component = "need_person",
                                                         actions = actions,
                                                         filter_widgets = filter_widgets,
                                                         list_fields = list_fields,
                                                         postprocess = "req_need_notification",
                                                         title = T("Invite People"),
                                                         ))

                s3db.add_custom_callback("req_need_person",
                                         "onaccept",
                                         req_need_person_create_onaccept,
                                         method = "create",
                                         )

            return result
        s3.prep = prep

        # Custom postp
        standard_postp = s3.postp
        def postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.component_name == "need_person" and \
               not auth.s3_has_role("ORG_ADMIN"):

                from gluon import URL
                from s3 import s3_str, S3CRUD

                # Normal Action Buttons
                S3CRUD.action_buttons(r, deletable = False)

                # Custom Action Buttons
                table = s3db.req_need_person
                rows = current.db(table.status.belongs((1, 2))).select(table.id)
                restrict = [str(row.id) for row in rows]
                s3.actions += [{"label": s3_str(T("Withdraw")),
                                "url": URL(c = "req",
                                           f = "need",
                                           args = [r.id,
                                                   "need_person",
                                                   "[id]",
                                                   "delete",
                                                   ],
                                           ),
                                "restrict": restrict,
                                "_class": "delete-btn",
                                },
                               ]

            return output
        s3.postp = postp

        attr["rheader"] = ccc_rheader

        return attr

    settings.customise_req_need_controller = customise_req_need_controller

    # -------------------------------------------------------------------------
    def req_need_person_create_onaccept(form):

        db = current.db
        s3db = current.s3db
        table = s3db.req_need_person
        record = db(table.id == form.vars.get("id")).select(table.id,
                                                            table.person_id,
                                                            limitby = (0, 1),
                                                            ).first()
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (ptable.id == record.person_id) & \
                (ptable.pe_id == ltable.pe_id)
        link = db(query).select(ltable.user_id,
                                limitby = (0, 1)
                                ).first()
        try:
            record.update_record(owned_by_user = link.user_id)
        except AttributeError:
            pass

    # -------------------------------------------------------------------------
    def req_need_person_update_onaccept(form):
        """
            Inform applicant if they have been Approved/Declined
            tbc?: Inform OrgAdmins if they have been Accepted/Rejected
        """

        form_vars_get = form.vars.get
        if form.record.status in (1, 2) and \
           form_vars_get("status") == "3":
            # Rejected
            approved_or_rejected = "rejected"
        elif form.record.status in (1, 3) and \
             form_vars_get("status") == "2":
            # Approved
            approved_or_rejected = "approved"
        else:
            return

        db = current.db
        s3db = current.s3db
        table = s3db.req_need_person
        need_person_id = form_vars_get("id")

        record = db(table.id == need_person_id).select(table.need_id,
                                                       table.person_id,
                                                       limitby = (0, 1)
                                                       ).first()

        # Message
        utable = db.auth_user
        ltable = s3db.pr_person_user
        ptable = s3db.pr_person
        query = (ptable.id == record.person_id) & \
                (ptable.pe_id == ltable.pe_id) & \
                (ltable.user_id == utable.id)
        user = db(query).select(utable.email,
                                limitby = (0, 1)
                                ).first()

        # Construct Email message
        subject = "%s: You have been %s to participate in an Opportunity" % \
            (settings.get_system_name_short(),
             approved_or_rejected,
             )

        ntable = s3db.req_need
        need = db(ntable.id == record.need_id).select(ntable.name,
                                                      limitby = (0, 1)
                                                      ).first().name

        message = "You have been %s to participate in an Opportunity:\n%s" % \
            (approved_or_rejected,
             need,
             )

        # Send message to each
        current.msg.send_email(to = user.email,
                               subject = subject,
                               message = message,
                               )

    # -------------------------------------------------------------------------
    def customise_req_need_person_resource(r, tablename):

        s3db = current.s3db

        table = s3db.req_need_person
        f = table.person_id
        f.comment = None
        f.writable = False
        f.represent = s3db.pr_PersonRepresent(show_link = True)

        current.response.s3.crud_strings.req_need_person = Storage(
            label_create = T("Add Participant"),
            title_display = T("Participant Details"),
            title_list = T("Participants"),
            title_update = T("Edit Participant"),
            title_upload = T("Import Participants"),
            label_list_button = T("List Participants"),
            label_delete_button = T("Remove Participant"),
            msg_record_created = T("Participant added"),
            msg_record_modified = T("Participant updated"),
            msg_record_deleted = T("Participant removed"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Participants registered"))

        deletable = True
        if r.component_id:
            record = current.db(table.id == r.component_id).select(table.status,
                                                                   limitby = (0, 1)
                                                                   ).first()
            if current.auth.s3_has_role("ORG_ADMIN"):
                from gluon import IS_IN_SET
                if record.status in (1, 2, 3):
                    deletable = False
                    table.status.requires = IS_IN_SET({1: T("Applied"),
                                                       2: T("Approved"),
                                                       3: T("Rejected"),
                                                       })
                else:
                    table.status.requires = IS_IN_SET({4: T("Invited"),
                                                       5: T("Accepted"),
                                                       6: T("Declined"),
                                                       })
            else:
                if record.status in (4, 5, 6):
                    deletable = False
                    from gluon import IS_IN_SET
                    if r.method == "update":
                        table.status.requires = IS_IN_SET({5: T("Accepted"),
                                                           6: T("Declined"),
                                                           })
                    else:
                        table.status.requires = IS_IN_SET({4: T("Invited"),
                                                           5: T("Accepted"),
                                                           6: T("Declined"),
                                                           })
                else:
                    current.response.s3.crud_strings.req_need_person.label_delete_button = T("Withdraw Application")
                    table.status.writable = False
        elif r.component:
            if current.auth.s3_has_role("ORG_ADMIN"):
                current.response.s3.crud_labels["DELETE"] = "Remove"
            else:
                current.response.s3.crud_labels["DELETE"] = "Withdraw"

        s3db.configure("req_need_person",
                       deletable = deletable,
                       list_fields = ["person_id",
                                      "person_id$human_resource.organisation_id",
                                      "status",
                                      "comments",
                                      ],
                       # Don't add people here (they are either invited or apply)
                       listadd = False,
                       update_onaccept = req_need_person_update_onaccept,
                       )

    settings.customise_req_need_person_resource = customise_req_need_person_resource

    # -------------------------------------------------------------------------
    def customise_supply_person_item_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3OptionsFilter, S3TextFilter

        s3db = current.s3db

        # Filtered components
        s3db.add_components("pr_person",
                            pr_person_tag = ({"name": "organisation",
                                              "joinby": "person_id",
                                              "filterby": {"tag": "organisation"},
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

        # No Hyperlink for Items (don't have permissions anyway)
        s3db.supply_person_item.item_id.represent = s3db.supply_ItemRepresent()

        current.response.s3.crud_strings[tablename] = Storage(
            title_display = T("Donation Details"),
            title_list = T("Donations"),
            title_update = T("Edit Donation"),
            label_list_button = T("List Donations"),
            msg_record_modified = T("Donation updated"),
            msg_list_empty = T("No Donations currently registered")
        )

        crud_form = S3SQLCustomForm((T("Goods / Service"), "item_id"),
                                    (T("Details"), "comments"),
                                    (T("Donor"), "person_id"),
                                    "status_id",
                                    (T("Requested By"), "organisation_id"),
                                    )

        filter_widgets = [S3TextFilter(["item_id$name",
                                        "comments",
                                        # Not working:
                                        #"person_id$first_name",
                                        #"person_id$last_name",
                                        ],
                                       #formstyle = text_filter_formstyle,
                                       label = "",
                                       _placeholder = T("Search"),
                                       ),
                          S3OptionsFilter("status_id",
                                          ),
                          ]

        list_fields = [(T("Goods / Service"), "item_id"),
                       (T("Details"), "comments"),
                       (T("Donor"), "person_id"),
                       (T("Donor Organization"), "person_id$organisation.value"),
                       (T("Delivery"), "person_id$delivery.value"),
                       (T("Availability"), "person_id$availability.value"),
                       "status_id",
                       (T("Requested By"), "organisation_id"),
                       ]

        s3db.configure("supply_person_item",
                       crud_form = crud_form,
                       deletable = False,
                       insertable = False,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_supply_person_item_resource = customise_supply_person_item_resource

    # -----------------------------------------------------------------------------
    def customise_supply_person_item_controller(**attr):

        from gluon import URL

        s3db = current.s3db
        s3 = current.response.s3

        stable = s3db.supply_person_item_status
        status = current.db(stable.name == "Available").select(stable.id,
                                                               limitby = (0, 1)
                                                               ).first()
        if status:
            # Default Filter
            from s3 import s3_set_default_filter
            s3_set_default_filter("~.status_id",
                                  status.id,
                                  tablename = "supply_person_item")

        if current.auth.s3_has_role("ORG_ADMIN"):
            # Add Hyperlink for Donors
            s3db.supply_person_item.person_id.represent = \
                s3db.pr_PersonRepresentContact(linkto = URL(c="pr", f="person",
                                                            args = ["[id]"],
                                                            vars = {"donors": 1},
                                                            extension = ""))

        # Post-process
        # (no need to call default one as not defined)
        def postp(r, output):

            if r.interactive:
                #if not r.component:
                from s3 import s3_str, S3CRUD
                S3CRUD.action_buttons(r)
                s3.actions.append({"url": URL(c="project", f="task",
                                              args = "create",
                                              vars = {"person_item_id": "[id]"},
                                              ),
                                   "_class": "action-btn send",
                                   "label": s3_str(T("Send Message"))
                                   })

            return output
        s3.postp = postp

        return attr

    settings.customise_supply_person_item_controller = customise_supply_person_item_controller

# END =========================================================================
