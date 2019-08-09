# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Settings for UCCE: User-Centred Community Engagement
        A project for Oxfam & Save the Children run with Eclipse Experience
    """

    T = current.T

    settings.base.system_name = T("User-Centred Community Engagement")
    settings.base.system_name_short = T("UCCE")

    # PrePopulate data
    settings.base.prepopulate += ("UCCE",)
    settings.base.prepopulate_demo += ("UCCE/Demo",)

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "UCCE"
    # Custom Logo
    settings.ui.menu_logo = "/%s/static/themes/UCCE/img/ee_logo.png" % current.request.application

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    settings.auth.registration_link_user_to = ["staff"]
    settings.auth.registration_link_user_to_default = ["staff"]

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"

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

    settings.security.policy = 6 # Controller, Function, Table ACLs and Entity Realm

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
        # Needed for default realm permissions
        # Currently-needed for Profile link:
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
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
        ("dc", Storage(
           name_nice = T("Assessments"),
           #description = "Data collection tool",
           restricted = True,
           module_type = 5
        )),
        ("project", Storage(
           name_nice = T("Projects"),
           restricted = True,
           module_type = 5
        )),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

    settings.ui.filter_clear = False
    settings.search.filter_manager = False

    # -------------------------------------------------------------------------
    def ucce_rheader(r):
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

        from gluon import A, DIV, TABLE, TR, TH, URL

        if tablename == "dc_template":
            #tabs = [(T("Basic Details"), None),
            #        (T("Participants"), "participant"),
            #        ]

            #rheader_tabs = s3_rheader_tabs(r, tabs)

            db = current.db
            s3db = current.s3db

            ttable = s3db.dc_target
            target = db(ttable.template_id == record.id).select(ttable.id,
                                                                ttable.status,
                                                                limitby = (0, 1)
                                                                ).first()
            try:
                target_id = target.id
                target_status = target.status
            except AttributeError:
                target_id = None
                target_status = None

            if not target_status:
                # No Target linked...something odd happening
                button = ""
            elif target_status == 2:
                # Active
                button = A(T("Deactivate"),
                           _href=URL(c="dc", f="target",
                                     args=[target_id, "deactivate.popup"],
                                     ),
                           _class="action-btn s3_modal",
                           _title=T("Deactivate Survey"),
                           )
            else:
                # Draft / Deactivated
                button = A(T("Activate"),
                           _href=URL(c="dc", f="target",
                                     args=[target_id, "activate.popup"],
                                     ),
                           _class="action-btn s3_modal",
                           _title=T("Activate Survey"),
                           )

            ptable = s3db.project_project
            ltable = s3db.project_project_target
            query = (ltable.target_id == target_id) & \
                    (ltable.project_id == ptable.id)
            project = db(query).select(ptable.name,
                                       limitby = (0, 1)
                                       ).first()
            try:
                project_name = project.name
            except AttributeError:
                project_name = ""

            #table = r.table
            rheader = DIV(TABLE(TR(# @ToDo: make this editable
                                   TH("%s: " % T("Survey name")),
                                   record.name,
                                   TH("%s: " % T("Project")),
                                   project_name,
                                   button,
                                   )),
                          #rheader_tabs,
                          )

        return rheader

    # -------------------------------------------------------------------------
    def dc_target_create_onaccept(form):
        """
            Create a Template with the same name as the Target
                Copy the masterkey to the s3_table
            Link the Target to this new Template
        """

        form_vars_get = form.vars.get
        template_id = form_vars_get("template_id")
        if template_id:
            # We already have a template, e.g. prepop
            return

        db = current.db
        s3db = current.s3db
        target_id = form_vars_get("id")
        name = form_vars_get("name")

        template = {"name": name}
        tetable = s3db.dc_template
        template_id = tetable.insert(**template)
        template["id"] = template_id
        onaccept = s3db.get_config("dc_template", "create_onaccept")
        onaccept(Storage(vars = template))

        tatable = s3db.dc_target
        db(tatable.id == target_id).update(template_id = template_id)

        ltable = s3db.project_project_target
        pmtable = s3db.project_project_masterkey
        query = (ltable.target_id == target_id) & \
                (ltable.project_id == pmtable.project_id)
        link = db(query).select(pmtable.masterkey_id,
                                limitby = (0, 1)
                                ).first()
        query = (tatable.id == target_id) & \
                (tetable.id == tatable.template_id)
        template = db(query).select(tetable.table_id,
                                    limitby = (0, 1)
                                    ).first()

        db(s3db.s3_table.id == template.table_id).update(masterkey_id = link.masterkey_id)

    # -------------------------------------------------------------------------
    def dc_target_ondelete(form):
        """
            Delete the associated Template
        """

        db = current.db
        s3db = current.s3db

        target_id = form.id

        table = s3db.dc_target
        record = db(table.id == target_id).select(table.deleted_fk,
                                                  limitby = (0, 1),
                                                  ).first()
        if record:
            import json
            deleted_fks = json.loads(record.deleted_fk)
            template_id = deleted_fks.get("template_id")
            resource = s3db.resource("dc_template",
                                     filter=(s3db.dc_template.id == template_id))
            resource.delete()

    # -------------------------------------------------------------------------
    def customise_dc_question_resource(r, tablename):

        from gluon import IS_IN_SET
        from s3 import S3Represent, S3SQLCustomForm

        crud_form = S3SQLCustomForm((T("Type"), "field_type"),
                                    (T("Question"), "name"),
                                    (T("Make question mandatory"), "require_not_empty"),
                                    (T("Choices"), "options"),
                                    (T("Add graphic"), "file"),
                                    )

        type_opts = {1: T("Text box"),
                     2: T("Number question"),
                     6: T("Multiple choice question"),
                     12: T("Likert-scale"),
                     13: T("Heatmap"),
                     }

        s3db = current.s3db
        table = s3db.dc_question
        table.field_type.represent = S3Represent(options=type_opts)
        table.field_type.requires = IS_IN_SET(type_opts)
        table.require_not_empty.comment = None

        s3db.configure("dc_question",
                       crud_form = crud_form,
                       list_fields = [(T("Type"), "field_type"),
                                      (T("Question"), "name"),
                                      (T("Mandatory"), "require_not_empty"),
                                      ]
                       )

    settings.customise_dc_question_resource = customise_dc_question_resource

    # -----------------------------------------------------------------------------
    def customise_dc_question_controller(**attr):

        # Custom Methods
        from templates.UCCE.controllers import dc_QuestionCreate
        from templates.UCCE.controllers import dc_QuestionImageDelete
        from templates.UCCE.controllers import dc_QuestionImageUpload
        from templates.UCCE.controllers import dc_QuestionSave

        set_method = current.s3db.set_method
        set_method("dc", "question",
                   method = "create_json",
                   action = dc_QuestionCreate())
        set_method("dc", "question",
                   method = "image_delete",
                   action = dc_QuestionImageDelete())
        set_method("dc", "question",
                   method = "image_upload",
                   action = dc_QuestionImageUpload())
        set_method("dc", "question",
                   method = "update_json",
                   action = dc_QuestionSave())

        return attr

    settings.customise_dc_question_controller = customise_dc_question_controller

    # -------------------------------------------------------------------------
    def customise_dc_target_resource(r, tablename):

        from gluon import URL
        from s3 import S3SQLCustomForm, S3TextFilter

        from templates.UCCE.controllers import dc_target_list_layout

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Survey"),
            title_display = T("Survey Details"),
            #title_list = T("Surveys"),
            title_list = "",
            title_update = T("Edit Survey"),
            #title_upload = T("Import Surveys"),
            label_list_button = T("List Surveys"),
            label_delete_button = T("Delete Survey"),
            msg_record_created = T("Survey added"),
            msg_record_modified = T("Survey updated"),
            msg_record_deleted = T("Survey deleted"),
            msg_list_empty = T("No Surveys currently registered"))

        s3db = current.s3db

        # Lift mandatory link to template so that we can create the template onaccept
        #s3db.dc_target.template_id.requires


        s3db.configure("dc_target",
                       create_next = URL(c="dc", f="template", vars={"target_id": "[id]"}),
                       create_onaccept = dc_target_create_onaccept,
                       crud_form = S3SQLCustomForm((T("Survey name"), "name")),
                       listadd = False,
                       list_fields = ["name",
                                      "status",
                                      "project_target.project_id",
                                      ],
                       list_layout = dc_target_list_layout,
                       ondelete = dc_target_ondelete,
                       filter_widgets = [S3TextFilter(["name",
                                                       "project.name",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search project or survey"),
                                                      ),
                                         ],
                       )

    settings.customise_dc_target_resource = customise_dc_target_resource

    # -----------------------------------------------------------------------------
    def customise_dc_target_controller(**attr):

        # Custom Methods
        from templates.UCCE.controllers import dc_TargetActivate
        from templates.UCCE.controllers import dc_TargetDeactivate
        from templates.UCCE.controllers import dc_TargetDelete
        from templates.UCCE.controllers import dc_TargetName

        set_method = current.s3db.set_method
        set_method("dc", "target",
                   method = "activate",
                   action = dc_TargetActivate())
        set_method("dc", "target",
                   method = "deactivate",
                   action = dc_TargetDeactivate())
        set_method("dc", "target",
                   method = "delete_confirm",
                   action = dc_TargetDelete())
        set_method("dc", "target",
                   method = "name",
                   action = dc_TargetName())

        current.response.s3.dl_no_header = True
        attr["dl_rowsize"] = 2

        return attr

    settings.customise_dc_target_controller = customise_dc_target_controller

    # -------------------------------------------------------------------------
    def dc_template_update_onaccept(form):
        """
            Ensure that the Survey using this Template has the same name as the Template
        """

        s3db = current.s3db
        form_vars_get = form.vars.get

        template_id = form_vars_get("id")
        name = form_vars_get("name")

        current.db(s3db.dc_target.template_id == template_id).update(name = name)

    # -------------------------------------------------------------------------
    def customise_dc_template_resource(r, tablename):

        current.response.s3.crud_strings[tablename].title_display = T("Editor")

        s3db = current.s3db

        s3db.configure("dc_template",
                       update_onaccept = dc_template_update_onaccept
                       )

    settings.customise_dc_template_resource = customise_dc_template_resource

    # -----------------------------------------------------------------------------
    def customise_dc_template_controller(**attr):

        s3db = current.s3db

        target_id =  current.request.get_vars.get("target_id")
        if target_id:
            # Find the Template for this Target
            ttable = s3db.dc_target
            target = current.db(ttable.id == target_id).select(ttable.template_id,
                                                               limitby = (0, 1),
                                                               ).first()
            if target:
                from gluon import redirect, URL
                redirect(URL(c="dc", f="template", args=[target.template_id, "editor"]))

        # Custom Methods
        from templates.UCCE.controllers import dc_TemplateEditor
        from templates.UCCE.controllers import dc_TemplateSave

        set_method = s3db.set_method
        set_method("dc", "template",
                   method = "editor",
                   action = dc_TemplateEditor())

        set_method("dc", "template",
                   method = "update_json",
                   action = dc_TemplateSave())

        attr["rheader"] = ucce_rheader

        return attr

    settings.customise_dc_template_controller = customise_dc_template_controller

    # -------------------------------------------------------------------------
    def customise_doc_document_resource(r, tablename):

        from gluon import URL
        from s3 import S3SQLCustomForm, S3TextFilter

        from templates.UCCE.controllers import doc_document_list_layout

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Guide"),
            title_display = T("Guide Details"),
            #title_list = T("Guides"),
            title_list = "",
            title_update = T("Edit Guide"),
            #title_upload = T("Import Guides"),
            label_list_button = T("List Guides"),
            label_delete_button = T("Delete Guide"),
            msg_record_created = T("Guide added"),
            msg_record_modified = T("Guide updated"),
            msg_record_deleted = T("Guide deleted"),
            msg_list_empty = T("No Guides currently registered")
        )

        s3db = current.s3db

        f = s3db.doc_document.comments
        f.comment = None

        s3db.configure("doc_document",
                       create_next = URL(args="datalist"),
                       crud_form = S3SQLCustomForm("name",
                                                   "file",
                                                   "comments",
                                                   ),
                       list_fields = ["name",
                                      "file",
                                      "comments",
                                      ],
                       list_layout = doc_document_list_layout,
                       filter_widgets = [S3TextFilter(["name",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search guides"),
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
    def project_project_onaccept(form):
        """
            Create & link the Master Key
        """

        from random import randint

        db = current.db
        s3db = current.s3db
        table = s3db.auth_masterkey

        not_unique = True
        while not_unique:
            masterkey = "%s-%s-%s" % (str(randint(0,999)).zfill(3),
                                      str(randint(0,999)).zfill(3),
                                      str(randint(0,999)).zfill(3),
                                      )
            exists = db(table.name == masterkey).select(table.id,
                                                        limitby = (0, 1)
                                                        )
            if not exists:
                not_unique = False

        utable = db.auth_user
        user = db(utable.email == "mobile_user@example.com").select(utable.id,
                                                                    limitby = (0, 1)
                                                                    ).first()

        masterkey_id = table.insert(name = masterkey,
                                    user_id = user.id,
                                    )

        s3db.project_project_masterkey.insert(masterkey_id = masterkey_id,
                                              project_id = form.vars.get("id"),
                                              )

    # -------------------------------------------------------------------------
    def project_project_ondelete(form):
        """
            Delete the associated Targets & Templates
        """

        import json

        db = current.db
        s3db = current.s3db

        project_id = form.id
        target_ids = []
        template_ids = []


        ltable = s3db.project_project_target
        rows = db(ltable.deleted == True).select(ltable.deleted_fk)
        for row in rows:
            deleted_fks = json.loads(row.deleted_fk)
            if deleted_fks.get("project_id") == project_id:
                target_id = deleted_fks.get("target_id")
                target_ids.append(target_id)

        if not target_ids:
            return

        table = s3db.dc_target
        targets = db(table.id.belongs(target_ids)).select(table.template_id)
        for target in targets:
            template_ids.append(target.template_id)

        resource = s3db.resource("dc_template",
                                 filter=(s3db.dc_template.id.belongs(template_ids)))
        resource.delete()
        # ondelete CASCADE will clear these:
        #resource = s3db.resource("dc_target",
        #                         filter=(s3db.dc_target.id.belongs(target_ids)))
        #resource.delete()

    # -------------------------------------------------------------------------
    def project_project_target_create_onaccept(form):
        """
            Copy the masterkey to the s3_table
            - used during prepop
        """

        form_vars_get = form.vars.get
        project_id = form_vars_get("project_id")
        target_id = form_vars_get("target_id")

        db = current.db
        s3db = current.s3db

        pmtable = s3db.project_project_masterkey
        link = db(pmtable.project_id == project_id).select(pmtable.masterkey_id,
                                                           limitby = (0, 1)
                                                           ).first()
        tatable = s3db.dc_target
        tetable = s3db.dc_template
        query = (tatable.id == target_id) & \
                (tetable.id == tatable.template_id)
        template = db(query).select(tetable.table_id,
                                    limitby = (0, 1)
                                    ).first()

        if template:
            db(s3db.s3_table.id == template.table_id).update(masterkey_id = link.masterkey_id)

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        from gluon import URL
        from s3 import S3SQLCustomForm, S3TextFilter

        from templates.UCCE.controllers import project_project_list_layout

        s3db = current.s3db

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("New project"),
            #title_display = T("Project Details"),
            # Only used in /target/create?
            title_display = T("Editor"),
            #title_list = T("Projects"),
            title_list = "",
            title_update = T("Edit project name"),
            #title_upload = T("Import Projects"),
            label_list_button = T("List Projects"),
            label_delete_button = T("Delete Projects"),
            msg_record_created = T("Project added"),
            msg_record_modified = T("Project updated"),
            msg_record_deleted = T("Project deleted"),
            msg_list_empty = T("No Projects currently registered")
        )

        user = current.auth.user
        organisation_id = user and user.organisation_id
        if organisation_id:
            f = s3db.project_project.organisation_id
            f.default = organisation_id
            f.readable = f.writable = False

        s3db.configure("project_project",
                       create_next = URL(args="datalist"),
                       # No need to chain as default one not relevant for this usecase:
                       create_onaccept = project_project_onaccept,
                       crud_form = S3SQLCustomForm((T("Organization"), "organisation_id"),
                                                   (T("New project name"), "name"),
                                                   ),
                       # Ignored here as set in Prep in default controller
                       #list_fields = ["name",
                       #               "project_target.target_id",
                       #               ],
                       list_layout = project_project_list_layout,
                       ondelete = project_project_ondelete,
                       filter_widgets = [S3TextFilter(["name",
                                                       "target.name",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search project or survey"),
                                                      ),
                                         ],
                       )

        s3db.configure("project_project_target",
                       create_onaccept = project_project_target_create_onaccept,
                       )

    settings.customise_project_project_resource = customise_project_project_resource

    # -----------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        # Custom Method
        from templates.UCCE.controllers import dc_ProjectDelete

        s3db = current.s3db
        s3db.set_method("project", "project",
                        method = "delete_confirm",
                        action = dc_ProjectDelete())

        s3 = current.response.s3

        # Custom postp
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.method == "datalist":
                # Over-ride list_fields set in default prep
                s3db.configure("project_project",
                               list_fields = ["name",
                                              "project_target.target_id",
                                              "masterkey.name",
                                              ],
                               )
                # Inject JS to handle Switches & deletion of Inner cards
                if s3.debug:
                    s3.scripts.append("/%s/static/themes/UCCE/js/projects.js" % r.application)
                else:
                    s3.scripts.append("/%s/static/themes/UCCE/js/projects.min.js" % r.application)

            return result
        s3.prep = prep

        s3.dl_no_header = True

        attr["rheader"] = None

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

# END =========================================================================
