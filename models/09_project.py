# -*- coding: utf-8 -*-

"""
    Project Tracking & Management

    Project > Activity > Task
        although each level of the hierarchy can stand alone
"""

if deployment_settings.has_module("project"):

    from gluon.sqlhtml import CheckboxesWidget

    # =========================================================================
    # Component definitions
    #

    # Projects as component of Organisations
    s3mgr.model.add_component("project_project",
                              org_organisation=Storage(
                                    link="project_organisation",
                                    joinby="organisation_id",
                                    key="project_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

    # Project Organisation as component of Projects
    s3mgr.model.add_component("project_organisation",
                              project_project="project_id")

    # Project Site as component of Projects
    s3mgr.model.add_component("project_site",
                              project_project="project_id")

    # Activities as component of Projects and Sites
    s3mgr.model.add_component("project_activity",
                              project_project="project_id",
                              org_site=super_key(db.org_site))

    # Beneficiaries as component of Project Sites and Activities
    s3mgr.model.add_component("project_beneficiary",
                              project_project="project_id",
                              project_activity="activity_id")

    # Need as component of Assessments
    #s3mgr.model.add_component("project_need",
    #                          assess_assess="assess_id")

    # Task as component of Organisations
    # @ToDo: Do this via project_organisation?

    # Tasks as component of Projects
    s3mgr.model.add_component("project_task",
                              project_project=Storage(
                                    link="project_task_project",
                                    joinby="project_id",
                                    key="task_id",
                                    actuate="replace",
                                    autocomplete="name",
                                    autodelete=False))

    # Tasks as component of Activities
    s3mgr.model.add_component("project_task",
                              project_activity=Storage(
                                    link="project_task_activity",
                                    joinby="activity_id",
                                    key="task_id",
                                    actuate="replace",
                                    autocomplete="name",
                                    autodelete=False))

    # Tasks as component of Incident Reports
    s3mgr.model.add_component("project_task",
                              irs_ireport=Storage(
                                    link="project_task_ireport",
                                    joinby="ireport_id",
                                    key="task_id",
                                    actuate="replace",
                                    autocomplete="name",
                                    autodelete=False))

    # Roles (required) as component of Tasks
    s3mgr.model.add_component("hrm_job_role",
                              project_task=Storage(
                                    link="project_task_job_role",
                                    joinby="task_id",
                                    key="job_role_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

    # Human Resources (assigned) as component of Tasks
    s3mgr.model.add_component("hrm_human_resource",
                              project_task=Storage(
                                    link="project_task_human_resource",
                                    joinby="task_id",
                                    key="human_resource_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

    # Documents as component of Tasks
    s3mgr.model.add_component("doc_document",
                              project_task=Storage(
                                    link="project_task_document",
                                    joinby="task_id",
                                    key="document_id",
                                    actuate="embed",
                                    autocomplete="name",
                                    autodelete=False))

    # Requests as component of Tasks
    s3mgr.model.add_component("req_req",
                              project_task=Storage(
                                    link="project_task_req",
                                    joinby="task_id",
                                    key="req_id",
                                    actuate="embed",
                                    autocomplete="request_number",
                                    autodelete=False))

    # =========================================================================
    # Multi-reference representation
    #
    def multiref_represent(opt, tablename, represent_string = "%(name)s"):
        """
            @todo: docstring? move into utils?
        """

        table = db[tablename]
        set = db(table.id > 0).select(table.id,
                                        table.name).as_dict()

        if isinstance(opt, (list, tuple)):
            opts = opt
            vals = [represent_string % set.get(opt) for opt in opts if opt in set.keys()]
        elif isinstance(opt, int):
            opts = [opt]
            vals = represent_string % set.get(opt)
        else:
            return NONE

        if len(opts) > 1:
            vals = ", ".join(vals)
        else:
            vals = len(vals) and vals[0] or ""
        return vals

    # =========================================================================
    # Tables
    #
    def project_tables():
        """ Load the Project tables as-needed """

        # ---------------------------------------------------------------------
        # Theme
        #
        resourcename = "theme"
        tablename = "project_theme"
        table = db.define_table(tablename,
                                Field("name", length=128, notnull=True, unique=True),
                                Field("comments"),
                                *s3_meta_fields())

        multi_theme_id = S3ReusableField("multi_theme_id", "list:reference project_theme",
                                         label = T("Themes"),
                                         sortby = "name",
                                         requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                        "project_theme.id",
                                                                        "%(name)s",
                                                                        sort=True,
                                                                        multiple=True)),
                                         represent = lambda opt: multiref_represent(opt, "project_theme"),
                                         default = [],
                                         ondelete = "RESTRICT",
                                         widget = lambda f, v: CheckboxesWidgetS3.widget(f, v, cols = 3))

        # ---------------------------------------------------------------------
        # Hazard
        #
        resourcename = "hazard"
        tablename = "project_hazard"
        table = db.define_table(tablename,
                                Field("name", length=128, notnull=True, unique=True),
                                Field("comments"),
                                *s3_meta_fields())

        multi_hazard_id = S3ReusableField("multi_hazard_id", "list:reference project_hazard",
                                          sortby = "name",
                                          label = T("Hazards"),
                                          requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                          "project_hazard.id",
                                                                          "%(name)s",
                                                                          sort=True,
                                                                          multiple=True)),
                                          represent = lambda opt: multiref_represent(opt, "project_hazard"),
                                          ondelete = "RESTRICT",
                                          widget = lambda f, v: CheckboxesWidgetS3.widget(f, v, cols = 3))

        # ---------------------------------------------------------------------
        # HFA
        #
        project_hfa_opts = {
            1: "HFA1: Ensure that disaster risk reduction is a national and a local priority with a strong institutional basis for implementation.",
            2: "HFA2: Identify, assess and monitor disaster risks and enhance early warning.",
            3: "HFA3: Use knowledge, innovation and education to build a culture of safety and resilience at all levels.",
            4: "HFA4: Reduce the underlying risk factors.",
            5: "HFA5: Strengthen disaster preparedness for effective response at all levels.",
        }

        def hfa_opts_represent(opt):
            opts = opt
            if isinstance(opt, int):
                opts = [opt]
            elif not isinstance(opt, (list, tuple)):
                return NONE
            vals = [project_hfa_opts.get(o,NONE) for o in opts]
            return ", ".join(vals)

        # ---------------------------------------------------------------------
        # Enable DRR extensions?
        #
        drr = deployment_settings.get_project_drr()

        # ---------------------------------------------------------------------
        # Countries (multi-link)
        #
        def countries_represent(locations):

            from gluon.dal import Rows
            if isinstance(locations, Rows):
                try:
                    locations = [r.name for r in locations]
                    return ", ".join(locations)
                except:
                    locations = [r.id for r in locations]
            if not isinstance(locations, list):
                locations = [locations]
            table = db.gis_location
            query = table.id.belongs(locations)
            rows = db(query).select(table.name)
            return countries_represent(rows)

        countries_id = S3ReusableField("countries_id", "list:reference gis_location",
                                       label = T("Countries"),
                                       requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                       "gis_location.id",
                                                                       "%(name)s",
                                                                       filterby = "level",
                                                                       filter_opts = ["L0"],
                                                                       sort=True,
                                                                       multiple=True)),
                                       represent = countries_represent,
                                       ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Project
        #
        resourcename = "project"
        tablename = "project_project"
        table = db.define_table(tablename,
                                Field("name",
                                      label = T("Name"),
                                      # Require unique=True if using IS_NOT_ONE_OF like here (same table,
                                      # no filter) in order to allow both automatic indexing (faster)
                                      # and key-based de-duplication (i.e. before field validation)
                                      unique = True,
                                      requires = [IS_NOT_EMPTY(error_message=T("Please fill this!")),
                                                  IS_NOT_ONE_OF(db, "project_project.name")]),
                                Field("code",
                                      label = T("Code"),
                                      readable=False,
                                      writable=False),
                                Field("description", "text",
                                      label = T("Description")),

                                Field("start_date", "date",
                                      label = T("Start date"),
                                      requires = IS_NULL_OR(IS_DATE(format = s3_date_format))),
                                Field("end_date", "date",
                                      label = T("End date"),
                                      requires = IS_NULL_OR(IS_DATE(format = s3_date_format))),
                                Field("duration",
                                      readable=False,
                                      writable=False,
                                      label = T("Duration")),

                                sector_id(widget=lambda f, v: \
                                    CheckboxesWidget.widget(f, v, cols=3)),

                                countries_id(#readable=False, writable=False
                                            ),

                                multi_hazard_id(readable=drr, writable=drr),
                                multi_theme_id(#readable=False, writable=False
                                               ),
                                Field("hfa", "list:integer",
                                      label = T("HFA Priorities"),
                                      readable=drr,
                                      writable=drr,
                                      requires = IS_NULL_OR(IS_IN_SET(project_hfa_opts,
                                                                      multiple = True)),
                                      represent = hfa_opts_represent,
                                      widget = CheckboxesWidgetS3.widget),

                                Field("objectives", "text",
                                      label = T("Objectives")),
                                *s3_meta_fields())

        # CRUD strings
        ADD_PROJECT = T("Add Project")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PROJECT,
            title_display = T("Project Details"),
            title_list = T("List Projects"),
            title_update = T("Edit Project"),
            title_search = T("Search Projects"),
            title_upload = T("Import Project List"),
            subtitle_create = T("Add New Project"),
            subtitle_list = T("Projects"),
            subtitle_upload = T("Upload Project List"),
            label_list_button = T("List Projects"),
            label_create_button = ADD_PROJECT,
            label_delete_button = T("Delete Project"),
            msg_record_created = T("Project added"),
            msg_record_modified = T("Project updated"),
            msg_record_deleted = T("Project deleted"),
            msg_list_empty = T("No Projects currently registered"))

        # Reusable field
        def project_represent(id, show_link=True):
            if id:
                val = (id and [db.project_project[id].name] or [NONE])[0]
                if not show_link:
                    return val
                return A(val,
                         _href = URL(c="project",
                                     f="project",
                                     args=[id])
                         )
            else:
                return NONE

        project_id = S3ReusableField("project_id", db.project_project,
            sortby="name",
            requires = IS_NULL_OR(IS_ONE_OF(db, "project_project.id",
                                            "%(name)s")),
            represent = project_represent,
            comment = DIV(A(ADD_PROJECT,
                            _class="colorbox",
                            _href=URL(c="project", f="project", args="create",
                                      vars=dict(format="popup")),
                            _target="top",
                            _title=ADD_PROJECT),
                      DIV( _class="tooltip",
                           _title="%s|%s" % (ADD_PROJECT,
                                             T("Add new project.")))),
            label = T("Project"),
            ondelete = "CASCADE")

        # Form validation
        def project_project_onvalidation(form):

            if not form.vars.code and "name" in form.vars:
                # Populate code from name
                form.vars.code = form.vars.name

        # Import item de-duplication
        def project_project_deduplicate(item):

            if item.id:
                return
            if item.tablename == "project_project" and \
               "name" in item.data:
                # Match project by name (all-lowercase)
                table = item.table
                name = item.data.name
                query = (table.name.lower() == name.lower())
                duplicate = db(query).select(table.id,
                                             limitby=(0, 1)).first()
                if duplicate:
                    item.id = duplicate.id
                    item.method = item.METHOD.UPDATE
            return

        # CRUD configuration
        s3mgr.configure(tablename,
                        deduplicate=project_project_deduplicate,
                        onvalidation=project_project_onvalidation,
                        create_next=URL(c="project", f="project",
                                        args=["[id]", "organisation"]),
                        list_fields=["id",
                                     "name",
                                     "countries_id",
                                     "start_date",
                                     "end_date",
                                    ])

        # ---------------------------------------------------------------------
        # Project Organisation
        #
        project_organisation_types = {
            1: T("Lead Implementer"), # T("Host National Society")
            2: T("Partner"), # T("Partner National Society")
            3: T("Donor"),
            4: T("Customer"), # T("Beneficiary")?
        }
        LEAD_ROLE = 1

        resourcename = "organisation"
        tablename = "project_organisation"
        table = db.define_table(tablename,
                                project_id(),
                                organisation_id(),
                                Field("role", "integer",
                                      requires = IS_NULL_OR(IS_IN_SET(project_organisation_types)),
                                      represent = lambda opt: \
                                        project_organisation_types.get(opt, NONE)),
                                Field("amount", "double",
                                      requires = IS_FLOAT_AMOUNT(),
                                      represent = lambda v: \
                                        IS_FLOAT_AMOUNT.represent(v, precision=2),
                                      widget = IS_FLOAT_AMOUNT.widget,
                                      label = T("Funds Contributed by this Organization")),
                                currency_type(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_PROJECT_ORG = T("Add Organization to Project")
        LIST_PROJECT_ORG = T("List Project Organizations")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PROJECT_ORG,
            title_display = T("Project Organization Details"),
            title_list = LIST_PROJECT_ORG,
            title_update = T("Edit Project Organization"),
            title_search = T("Search Project Organizations"),
            title_upload = T("Import Project Organizations"),
            subtitle_create = T("Add Organization to Project"),
            subtitle_list = T("Project Organizations"),
            label_list_button = LIST_PROJECT_ORG,
            label_create_button = ADD_PROJECT_ORG,
            label_delete_button = T("Remove Organization from Project"),
            msg_record_created = T("Organization added to Project"),
            msg_record_modified = T("Project Organization updated"),
            msg_record_deleted = T("Organization removed from Project"),
            msg_list_empty = T("No Organizations for this Project"))

        def project_organisation_onvalidation(form, lead_role=LEAD_ROLE):

            project_id = form.vars.project_id
            organisation_id = form.vars.organisation_id
            if str(form.vars.role) == str(lead_role) and project_id:
                otable = db.project_organisation
                query = (otable.deleted != True) & \
                        (otable.project_id == project_id) & \
                        (otable.role == lead_role) & \
                        (otable.organisation_id != organisation_id)
                row = db(query).select(otable.id, limitby=(0, 1)).first()
                if row:
                    form.errors.role = T("Lead Implementer for this project is already set, please choose another role.")
            return

        def project_organisation_deduplicate(item):

            if item.id:
                return
            if item.tablename == "project_organisation" and \
               "project_id" in item.data and \
               "organisation_id" in item.data:
                # Match project by org_id and project_id
                table = item.table
                project_id = item.data.project_id
                organisation_id = item.data.organisation_id
                query = (table.project_id == project_id) & \
                        (table.organisation_id == organisation_id)
                duplicate = db(query).select(table.id,
                                             limitby=(0, 1)).first()
                if duplicate:
                    item.id = duplicate.id
                    item.method = item.METHOD.UPDATE
            return

        s3mgr.configure(tablename,
                        deduplicate=project_organisation_deduplicate,
                        onvalidation = project_organisation_onvalidation)

        # ---------------------------------------------------------------------
        # Activity Type
        #
        resourcename = "activity_type"
        tablename = "project_activity_type"
        table = db.define_table(tablename,
                                Field("name", length=128,
                                      notnull=True, unique=True),
                                *s3_meta_fields())

        ADD_ACTIVITY_TYPE = T("Add Activity Type")

        # Reusable comment
        def activity_type_comment():
            if auth.has_membership(auth.id_group(1)):
                return DIV(A(ADD_ACTIVITY_TYPE,
                             _class="colorbox",
                             _href=URL(c="project", f="activity_type",
                                       args="create",
                                       vars=dict(format="popup")),
                             _target="top",
                             _title=ADD_ACTIVITY_TYPE
                             )
                           )
            else:
                return None

        # Reusable FK field (single)
        activity_type_id = S3ReusableField("activity_type_id",
                                           db.project_activity_type,
                                           sortby="name",
                                           requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                           "project_activity_type.id",
                                                                           "%(name)s",
                                                                           sort=True)),
                                           represent = lambda id: \
                                            s3_get_db_field_value(tablename = "project_activity_type",
                                                                  fieldname = "name",
                                                                  look_up_value = id),
                                           label = T("Activity Type"),
                                           comment = activity_type_comment(),
                                           ondelete = "RESTRICT")

        # Reusable FK field (multiple)
        multi_activity_type_id = S3ReusableField("multi_activity_type_id",
                                                 "list:reference project_activity_type",
                                                 sortby = "name",
                                                 label = T("Activities"),
                                                 requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                                 "project_activity_type.id",
                                                                                 "%(name)s",
                                                                                 sort=True,
                                                                                 multiple=True)),
                                                 represent = lambda opt: \
                                                    multiref_represent(opt,
                                                                       "project_activity_type"),
                                                 #comment = skill_help,
                                                 default = [],
                                                 widget = lambda f, v: \
                                                    CheckboxesWidgetS3.widget(f, v, col=3),
                                                 ondelete = "RESTRICT")

        # CRUD Strings
        ADD_ACTIVITY = T("Add Activity Type")
        LIST_ACTIVITIES = T("List of Activity Types")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ACTIVITY,
            title_display = T("Activity Type"),
            title_list = LIST_ACTIVITIES,
            title_update = T("Edit Activity Type"),
            title_search = T("Search for Activity Type"),
            subtitle_create = T("Add New Activity Type"),
            subtitle_list = T("All Activity Types"),
            label_list_button = LIST_ACTIVITIES,
            label_create_button = ADD_ACTIVITY,
            msg_record_created = T("Activity Type Added"),
            msg_record_modified = T("Activity Type Updated"),
            msg_record_deleted = T("Activity Type Deleted"),
            msg_list_empty = T("No Activity Types Found")
        )

        # ---------------------------------------------------------------------
        # Project Activity
        #
        tablename = "project_activity"
        table = db.define_table(tablename,
                                project_id(),
                                Field("name", label = T("Short Description"),
                                      requires=IS_NOT_EMPTY()),
                                multi_activity_type_id(),
                                #organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                                location_id(widget = S3LocationSelectorWidget(hide_address=True)),
                                s3_comments(),
                                *s3_meta_fields())

        class project_activity_virtualfields:

            extra_fields = ["project_id"]

            def organisation(self):

                otable = db.org_organisation
                ltable = db.project_organisation
                query = (ltable.deleted != True) & \
                        (ltable.project_id == self.project_activity.project_id) & \
                        (ltable.role == LEAD_ROLE) & \
                        (ltable.organisation_id == otable.id)
                org = db(query).select(otable.name,
                                       limitby=(0, 1)).first()
                if org:
                    return org.name
                else:
                    return None

        table.virtualfields.append(project_activity_virtualfields())

        # CRUD Strings
        ADD_ACTIVITY = T("Add Activity")
        LIST_ACTIVITIES = T("List Activities")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ACTIVITY,
            title_display = T("Activity Details"),
            title_list = LIST_ACTIVITIES,
            title_update = T("Edit Activity"),
            title_search = T("Search Activities"),
            title_upload = T("Import Activity Data"),
            title_report = T("Who is doing What Where"),
            subtitle_create = T("Add New Activity"),
            subtitle_list = T("Activities"),
            subtitle_report = T("Activities"),
            label_list_button = LIST_ACTIVITIES,
            label_create_button = ADD_ACTIVITY,
            msg_record_created = T("Activity Added"),
            msg_record_modified = T("Activity Updated"),
            msg_record_deleted = T("Activity Deleted"),
            msg_list_empty = T("No Activities Found")
        )

        # Reusable FK field
        activity_id = S3ReusableField( "activity_id", db.project_activity,
                                       sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                       "project_activity.id",
                                                                       "%(name)s",
                                                                       sort=True)),
                                       represent = lambda id: s3_get_db_field_value(tablename = "project_activity",
                                                                                    fieldname = "name",
                                                                                    look_up_value = id),
                                       label = T("Activity"),
                                       comment = DIV(A(ADD_ACTIVITY,
                                                       _class="colorbox",
                                                       _href=URL(c="project", f="activity",
                                                                 args="create",
                                                                 vars=dict(format="popup")),
                                                       _target="top",
                                                       _title=ADD_ACTIVITY)),
                                       ondelete = "CASCADE")

        def project_activity_onaccept(form):

            if form.vars.name and form.vars.location_id:
                table = db.gis_location
                query = table.id == form.vars.location_id
                db(query).update(name=form.vars.name)
            return

        def project_activity_deduplicate(item):

            if item.id:
                return
            if item.tablename == "project_activity" and \
               "name" in item.data and \
               "project_id" in item.data:
                # Match activity by name and project_id
                table = item.table
                name = item.data.name
                project_id = item.data.project_id
                query = (table.name == name) & \
                        (table.project_id == project_id)
                duplicate = db(query).select(table.id,
                                             limitby=(0, 1)).first()
                if duplicate:
                    item.id = duplicate.id
                    item.method = item.METHOD.UPDATE
            return

        project_activity_search = s3base.S3Search(
            simple=(s3base.S3SearchSimpleWidget(field="name",
                                                name="simple"),))

        # Resource configuration
        analyze_fields = [
                            (T("Organization"), "organisation"),
                            (T("Project"), "project_id$name"),
                            "location_id",
                            (T("Activity"), "name"),
                            (T("Activity Type"), "multi_activity_type_id")
                         ]
        s3mgr.configure(tablename,
                        search_method=project_activity_search,
                        onaccept=project_activity_onaccept,
                        deduplicate=project_activity_deduplicate,
                        analyze_rows=analyze_fields,
                        analyze_cols=analyze_fields,
                        analyze_fact=analyze_fields)

        # ---------------------------------------------------------------------
        # Project Site
        #
        resourcename = "site"
        tablename = "project_site"
        table = db.define_table(tablename,
                                super_link(db.org_site), # site_id
                                project_id(),
                                Field("name", notnull=True,
                                      length=64, # Mayon Compatibility
                                      label = T("Name")),
                                location_id(),
                                multi_activity_type_id(),
                                *(address_fields() + s3_meta_fields()))

        # CRUD strings
        ADD_PROJECT_SITE = T("Add Project Site")
        LIST_PROJECT_SITE = T("List Project Sites")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PROJECT_SITE,
            title_display = T("Project Site Details"),
            title_list = LIST_PROJECT_SITE,
            title_update = T("Edit Project Site"),
            title_search = T("Search Project Sites"),
            title_upload = T("Import Project Sites"),
            subtitle_create = T("Add New Project Site"),
            subtitle_list = T("Sites"),
            label_list_button = LIST_PROJECT_SITE,
            label_create_button = ADD_PROJECT_SITE,
            label_delete_button = T("Delete Project Site"),
            msg_record_created = T("Project Site added"),
            msg_record_modified = T("Project Site updated"),
            msg_record_deleted = T("Project Site deleted"),
            msg_list_empty = T("No Project Sites currently registered"))

        # Reusable field for other tables to reference
        project_site_comment = DIV(A(ADD_PROJECT_SITE,
                                     _class="colorbox",
                                     _href=URL(c="project", f="site",
                                               args="create",
                                               vars=dict(format="popup")),
                                     _target="top",
                                     _title=ADD_PROJECT_SITE),
                                   DIV( _class="tooltip",
                                        _title="%s|%s" % (
                                            ADD_PROJECT_SITE,
                                            T("If you don't see the site in the list, you can add a new one by clicking link 'Add Project Site'.")
                                            )
                                       )
                                   )

        project_site_id = S3ReusableField("project_site_id", db.project_site,
                                          #sortby="default/indexname",
                                          requires = IS_NULL_OR(IS_ONE_OF(db, "project_site.id", "%(name)s")),
                                          represent = lambda id: \
                                                      (id and [db(db.project_site.id == id).select(db.project_site.name,
                                                                                                   limitby=(0, 1)).first().name] or [NONE])[0],
                                          label = T("Project Site"),
                                          comment = office_comment,
                                          ondelete = "CASCADE")

        s3mgr.configure(tablename,
                        super_entity=db.org_site,
                        onvalidation=address_onvalidation)

        # ---------------------------------------------------------------------
        # Project Beneficiary Type
        #
        resourcename = "beneficiary_type"
        tablename = "project_beneficiary_type"
        table = db.define_table(tablename,
                                Field("name",
                                      length=128,
                                      unique=True,
                                      requires = IS_EMPTY_OR(IS_NOT_IN_DB(db,
                                                                "project_beneficiary_type.name"))),
                                *s3_meta_fields())

        # CRUD Strings
        ADD_BNF_TYPE = T("Add Beneficiary Type")
        LIST_BNF_TYPE = T("List Beneficiary Types")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_BNF_TYPE,
            title_display = T("Beneficiary Type"),
            title_list = LIST_BNF_TYPE,
            title_update = T("Edit Beneficiary Type"),
            title_search = T("Search Beneficiary Types"),
            subtitle_create = T("Add New Beneficiary Type"),
            subtitle_list = T("Beneficiary Types"),
            label_list_button = LIST_BNF_TYPE,
            label_create_button = ADD_BNF_TYPE,
            msg_record_created = T("Beneficiary Type Added"),
            msg_record_modified = T("Beneficiary Type Updated"),
            msg_record_deleted = T("Beneficiary Type Deleted"),
            msg_list_empty = T("No Beneficiary Types Found")
        )

        def beneficiary_type_represent(type_id):

            if isinstance(type_id, Row):
                if "name" in type_id:
                    return type_id.name
                elif "id" in type_id:
                    type_id = type_id.id
                else:
                    return UNKNOWN_OPT
            bnf_type = db.project_beneficiary_type
            query = bnf_type.id == type_id
            row = db(query).select(bnf_type.name, limitby=(0, 1)).first()
            if row:
                return row.name
            else:
                return UNKNOWN_OPT

        bnf_type = S3ReusableField("bnf_type", db.project_beneficiary_type,
                                   requires = IS_NULL_OR(IS_ONE_OF(db,
                                                         "project_beneficiary_type.id",
                                                         beneficiary_type_represent)),
                                   represent = beneficiary_type_represent,
                                   label = T("Beneficiary Type"),
                                   comment = DIV(A(ADD_BNF_TYPE,
                                                   _class="colorbox",
                                                   _href=URL(c="project", f="beneficiary_type",
                                                             args="create",
                                                             vars=dict(format="popup",
                                                                       child="bnf_type")),
                                                   _target="top",
                                                   _title=ADD_BNF_TYPE),
                                                 DIV(_class="tooltip",
                                                     _title="%s|%s" % (ADD_BNF_TYPE,
                                                                T("Add a new beneficiary type")))),
                                   ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Project Beneficiary
        #
        resourcename = "beneficiary"
        tablename = "project_beneficiary"
        table = db.define_table(tablename,
                                # populated automatically
                                project_id(readable=False,
                                           writable=False),
                                activity_id(comment=None),
                                bnf_type(),
                                Field("number", "integer",
                                      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999))),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD Strings
        ADD_BNF = T("Add Beneficiaries")
        LIST_BNF = T("List Beneficiaries")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_BNF,
            title_display = T("Beneficiaries Details"),
            title_list = LIST_BNF,
            title_update = T("Edit Beneficiaries"),
            title_search = T("Search Beneficiaries"),
            title_report = T("Beneficiary Report"),
            subtitle_create = T("Add New Beneficiaries"),
            subtitle_list = T("Beneficiaries"),
            label_list_button = LIST_BNF,
            label_create_button = ADD_BNF,
            msg_record_created = T("Beneficiaries Added"),
            msg_record_modified = T("Beneficiaries Updated"),
            msg_record_deleted = T("Beneficiaries Deleted"),
            msg_list_empty = T("No Beneficiaries Found")
        )

        # Reusable field
        beneficiary_id = S3ReusableField("beneficiary_id", db.project_beneficiary,
                                         sortby="name",
                                         requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                         "project_beneficiary.id",
                                                                         "%(type)s",
                                                                         sort=True)),
                                         represent = lambda id: \
                                            s3_get_db_field_value(tablename = "project_beneficiary",
                                                                  fieldname = "type",
                                                                  look_up_value = id),
                                         label = T("Beneficiaries"),
                                         comment = DIV(A(ADD_BNF,
                                                         _class="colorbox",
                                                         _href=URL(c="project",
                                                                   f="beneficiary",
                                                                   args="create",
                                                                   vars=dict(format="popup")),
                                                         _target="top",
                                                         _title=ADD_BNF)),
                                         ondelete = "SET NULL")

        def project_beneficiary_onaccept(form):

            btable = db.project_beneficiary
            atable = db.project_activity

            record_id = form.vars.id
            query = (btable.id == record_id) & \
                    (atable.id == btable.activity_id)
            activity = db(query).select(atable.project_id, limitby=(0, 1)).first()
            if activity:
                db(btable.id == record_id).update(project_id=activity.project_id)
            return

        def project_beneficiary_deduplicate(item):

            if item.id:
                return
            if item.tablename == "project_beneficiary" and \
               "bnf_type" in item.data and \
               "activity_id" in item.data:
                # Match activity by type and activity_id
                table = item.table
                bnf_type = item.data.bnf_type
                activity_id = item.data.activity_id
                query = (table.bnf_type == bnf_type) & \
                        (table.activity_id == activity_id)
                duplicate = db(query).select(table.id,
                                             limitby=(0, 1)).first()
                if duplicate:
                    item.id = duplicate.id
                    item.method = item.METHOD.UPDATE
            return

        s3mgr.configure(tablename,
                        onaccept=project_beneficiary_onaccept,
                        deduplicate=project_beneficiary_deduplicate,
                        #analyze_filter=[
                            #s3base.S3SearchOptionsWidget(field=["project_id"],
                                                         #name="project",
                                                         #label=T("Project"))
                        #],
                        analyze_rows=[
                                      "activity_id",
                                      "project_id",
                                      "project_id$multi_hazard_id",
                                      "project_id$multi_theme_id",
                                      "activity_id$multi_activity_type_id"
                                     ],
                        analyze_cols=[
                                      "bnf_type",
                                     ],
                        analyze_fact=["number"],
                        analyze_method=["sum"])

        # ---------------------------------------------------------------------
        # Need Type
        #
        #resourcename = "need_type"
        #tablename = "%s_%s" % (module, resourcename)
        #table = db.define_table(tablename,
        #                        Field("name", length=128, notnull=True, unique=True),
        #                        sector_id(),
        #                        *s3_meta_fields())

        # CRUD strings
        #ADD_BASELINE_TYPE = T("Add Need Type")
        #LIST_BASELINE_TYPE = T("List Need Types")
        #s3.crud_strings[tablename] = Storage(
        #    title_create = ADD_BASELINE_TYPE,
        #    title_display = T("Need Type Details"),
        #    title_list = LIST_BASELINE_TYPE,
        #    title_update = T("Edit Need Type"),
        #    title_search = T("Search Need Type"),
        #    subtitle_create = T("Add New Need Type"),
        #    subtitle_list = T("Need Types"),
        #    label_list_button = LIST_BASELINE_TYPE,
        #    label_create_button = ADD_BASELINE_TYPE,
        #    label_delete_button = T("Delete Need Type"),
        #    msg_record_created = T("Need Type added"),
        #    msg_record_modified = T("Need Type updated"),
        #    msg_record_deleted = T("Need Type deleted"),
        #    msg_list_empty = T("No Need Types currently registered"))

        #def need_type_comment():
        #    if auth.has_membership(auth.id_group("'Administrator'")):
        #        return DIV(A(ADD_BASELINE_TYPE,
        #                     _class="colorbox",
        #                     _href=URL(c="project", f="need_type", args="create",
        #                               vars=dict(format="popup")),
        #                     _target="top",
        #                     _title=ADD_BASELINE_TYPE))
        #    else:
        #        return None

        #need_type_id = S3ReusableField("need_type_id", db.project_need_type,
        #                               sortby="name",
        #                               requires = IS_NULL_OR(IS_ONE_OF(db, "project_need_type.id",
        #                                                               "%(name)s", sort=True)),
        #                               represent = lambda id: s3_get_db_field_value(tablename = "project_need_type",
        #                                                                            fieldname = "name",
        #                                                                            look_up_value = id),
        #                               label = T("Need Type"),
        #                               comment = need_type_comment(),
        #                               ondelete = "RESTRICT")

        #def need_type_represent(id):
        #    return s3_get_db_field_value(tablename = "project_need_type",
        #                                 fieldname = "name",
        #                                 look_up_value = id)

        # ---------------------------------------------------------------------
        # Load assess_id definition
        #
        #if deployment_settings.has_module("assess"):
        #    s3mgr.load("assess_assess")
        #assess_id = response.s3.assess_id

        # ---------------------------------------------------------------------
        # Need
        #
        #resourcename = "need"
        #tablename = "%s_%s" % (module, resourcename)
        #table = db.define_table(tablename,
        #                        assess_id(readable=False,
        #                                  writable=False),
        #                        need_type_id(),
        #                        Field("value", "double",
        #                              label = "#",
        #                              represent = lambda value: value is not None and "%d" % value or NONE),
        #                        s3_comments(),
        #                        *s3_meta_fields())

        # CRUD strings
        #ADD_BASELINE = T("Add Need")
        #LIST_BASELINE = T("List Needs")
        #s3.crud_strings[tablename] = Storage(
        #    title_create = ADD_BASELINE,
        #    title_display = T("Needs Details"),
        #    title_list = LIST_BASELINE,
        #    title_update = T("Edit Need"),
        #    title_search = T("Search Needs"),
        #    subtitle_create = T("Add New Need"),
        #    subtitle_list = T("Needs"),
        #    label_list_button = LIST_BASELINE,
        #    label_create_button = ADD_BASELINE,
        #    label_delete_button = T("Delete Need"),
        #    msg_record_created = T("Need added"),
        #    msg_record_modified = T("Need updated"),
        #    msg_record_deleted = T("Need deleted"),
        #    msg_list_empty = T("No Needs currently registered"))

        # ---------------------------------------------------------------------
        # Tasks
        #
        # Tasks can be linked to Activities or directly to Projects
        # - they can also be used by the Event/Scenario modules
        #
        # @ToDo: Recurring tasks
        #
        project_task_status_opts = {
            1: T("Draft"),
            2: T("New"),
            3: T("Assigned"),
            4: T("On Hold"),
            5: T("Feedback"),
            6: T("Cancelled"),
            7: T("Blocked"),
            8: T("Completed"),
            9: T("Verified"),
            99: T("unspecified")
        }

        project_task_priority_opts = {
            3:T("High"),
            2:T("Normal"),
            1:T("Low")
        }

        tablename = "project_task"
        table = db.define_table(tablename,
                                Field("template", "boolean",
                                      default=False,
                                      readable=False,
                                      writable=False),
                                Field("status", "integer",
                                      requires = IS_IN_SET(project_task_status_opts,
                                                           zero=None),
                                      default = 2,
                                      label = T("Status"),
                                      represent = lambda opt: \
                                        project_task_status_opts.get(opt,
                                                                     UNKNOWN_OPT)),
                                Field("name",
                                      label = T("Short Description"),
                                      length=80,
                                      notnull=True,
                                      requires = IS_NOT_EMPTY()),
                                Field("description", "text",
                                      label = T("Detailed Description")),
                                Field("priority", "integer",
                                      requires = IS_IN_SET(project_task_priority_opts,
                                                           zero=None),
                                      default = 2,
                                      label = T("Priority"),
                                      represent = lambda opt: \
                                        project_task_priority_opts.get(opt,
                                                                       UNKNOWN_OPT)),
                                # Could be an Organisation, a Team or a Person
                                super_link(db.pr_pentity,
                                           readable = True,
                                           writable = True,
                                           label = T("Assigned to"),
                                           represent = lambda id: \
                                            s3_pentity_represent(id, show_label=False),
                                           # @ToDo: Widget
                                           #widget = S3PentityWidget(),
                                           #comment = DIV(_class="tooltip",
                                           #              _title="%s|%s" % (T("Assigned to"),
                                           #                                T("Enter some characters to bring up a list of possible matches")))
                                            ),
                                Field("date_due", "datetime",
                                      label = T("Date Due"),
                                      requires = [IS_EMPTY_OR(
                                                  IS_UTC_DATETIME_IN_RANGE(
                                                    minimum=request.utcnow - datetime.timedelta(days=1),
                                                    error_message="%s %%(min)s!" %
                                                        T("Enter a valid future date")))],
                                      widget = S3DateTimeWidget(past=0,
                                                                future=8760),  # Hours, so 1 year
                                      represent = s3_utc_represent),
                                Field("time_estimated", "time",
                                      label = "%s (%s)" % (T("Time Estimate"),
                                                           T("hours"))),
                                Field("time_actual", "time",
                                      label = "%s (%s)" % (T("Time Taken"),
                                                           T("hours"))),
                                site_id,
                                location_id(label=T("Deployment Location"),
                                            #readable=False, writable=False
                                            ),
                                *s3_meta_fields())

        # Comment these if you don't need a Site associated with Tasks
        table.site_id.readable = table.site_id.writable = True
        table.site_id.label = T("Check-in at Facility") # T("Managing Office")

        # CRUD Strings
        ADD_TASK = T("Add Task")
        LIST_TASKS = T("List Tasks")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_TASK,
            title_display = T("Task Details"),
            title_list = LIST_TASKS,
            title_update = T("Edit Task"),
            title_search = T("Search Tasks"),
            subtitle_create = T("Add New Task"),
            subtitle_list = T("Tasks"),
            label_list_button = LIST_TASKS,
            label_create_button = ADD_TASK,
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task deleted"),
            msg_list_empty = T("No tasks currently registered"))

        # Reusable field
        task_id = S3ReusableField("task_id", db.project_task,
                                  label = T("Task"),
                                  sortby="name",
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "project_task.id", "%(name)s")),
                                  represent = lambda id: (id and [db.project_task[id].name] or [NONE])[0],
                                  comment = DIV(A(ADD_TASK,
                                                  _class="colorbox",
                                                  _href=URL(c="project", f="task",
                                                            args="create",
                                                            vars=dict(format="popup")),
                                                  _target="top",
                                                  _title=ADD_TASK),
                                                DIV(_class="tooltip",
                                                    _title="%s|%s" % (ADD_TASK,
                                                        T("A task is a piece of work that an individual or team can do in 1-2 days")))),
                                  ondelete = "CASCADE")

        def task_onvalidation(form):
            """ Task form validation """

            if str(form.vars.status) == "3" and not form.vars.pe_id:
                form.errors.pe_id = \
                    T("Status 'assigned' requires the %(fieldname)s to not be blank") % \
                        dict(fieldname=db.project_task.pe_id.label)
            return True

        def task_create_onaccept(form):
            """ When a Task is created, also create associated Link Tables """

            if session.s3.event:
                # Create a link between this Task & the active Event
                s3mgr.load("event_task")
                db.event_task.insert(event_id=session.s3.event, task_id=form.vars.id)
            return True

        s3mgr.configure(tablename,
                        copyable=True,
                        onvalidation = task_onvalidation,
                        create_onaccept = task_create_onaccept,
                        list_fields=["id",
                                     #"urgent",
                                     "priority",
                                     "status",
                                     "name",
                                     "pe_id",
                                     "date_due",
                                     #"site_id"
                                    ],
                        extra="description")

        # ---------------------------------------------------------------------
        # Link tables for Project Tasks
        #
        # Tasks <> Projects
        tablename = "project_task_project"
        table = db.define_table(tablename,
                                task_id(),
                                project_id(),
                                *s3_meta_fields())

        # Tasks <> Activities
        tablename = "project_task_activity"
        table = db.define_table(tablename,
                                task_id(),
                                activity_id(),
                                *s3_meta_fields())

        if deployment_settings.has_module("doc"):
            # Tasks <> Documents
            response.s3.activity_id = activity_id
            response.s3.project_id = project_id
            s3mgr.load("doc_document")
            tablename = "project_task_document"
            table = db.define_table(tablename,
                                    task_id(),
                                    response.s3.document_id(),
                                    *s3_meta_fields())

        if deployment_settings.has_module("hrm"):
            # Tasks <> Human Resources
            tablename = "project_task_human_resource"
            table = db.define_table(tablename,
                                    task_id(),
                                    human_resource_id(),
                                    *s3_meta_fields())

            # Tasks <> Job Roles
            tablename = "project_task_job_role"
            table = db.define_table(tablename,
                                    task_id(),
                                    job_role_id(),
                                    *s3_meta_fields())

        if deployment_settings.has_module("irs"):
            # Tasks <> Incident Reports
            s3mgr.load("irs_ireport")
            ireport_id = response.s3.ireport_id
            tablename = "project_task_ireport"
            table = db.define_table(tablename,
                                    task_id(),
                                    ireport_id(),
                                    *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Comments
        # @ToDo: Attachments?
        #
        # Parent field allows us to:
        #  * easily filter for top-level threads
        #  * easily filter for next level of threading
        #  * hook a new reply into the correct location in the hierarchy
        #
        # ---------------------------------------------------------------------
        tablename = "project_comment"
        table = db.define_table(tablename,
                                Field("parent", "reference project_comment",
                                      requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                       "project_comment.id")),
                                      readable=False),
                                #project_id(),
                                #activity_id(),
                                task_id(),
                                Field("body", "text", notnull=True,
                                      label = T("Comment")),
                                *s3_meta_fields()
                                )

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "task_id",
                                     "created_by",
                                     "modified_on"])

        # ---------------------------------------------------------------------
        # Project Resource Headers
        #
        def project_rheader(r, tabs=[]):
            """ Project Resource Headers - used in Project & Budget modules """

            rheader = None

            if r.representation == "html":
                rheader_tabs = s3_rheader_tabs(r, tabs)
                table = r.table
                record = r.record
                if record:
                    if r.name == "project":
                        rheader = DIV(TABLE(
                            TR(
                                TH("%s: " % table.code.label),
                                record.code,
                                TH("%s: " % table.name.label),
                                record.name
                                ),
                            TR(
                                #TH("%s: " % table.location_id.label),
                                #table.location_id.represent(record.location_id),
                                ),
                            #TR(
                            #    TH("%s: " % table.status.label),
                            #    project_status_opts.get(record.status, UNKNOWN_OPT),
                            #    TH("%s: " % table.sector_id.label),
                            #    sectors,
                            #    )
                            ), rheader_tabs)

                    elif r.name == "activity":
                        rheader = DIV(TABLE(
                            TR(
                                TH("%s: " % table.name.label),
                                record.name,
                                ),
                            #TR(
                                #TH("%s: " % table.location_id.label),
                                #gis_location_represent(record.location_id),
                                #TH("%s: " % T("Duration")),
                                #"%s to %s" % (record.start_date,
                                              #record.end_date),
                                #),
                            #TR(
                                #TH("%s: " % table.organisation_id.label),
                                #organisation_represent(record.organisation_id),
                                #TH("%s: " % table.sector_id.label),
                                #org_sector_represent(record.sector_id),
                                #),
                            ), rheader_tabs)

            return rheader

        # ---------------------------------------------------------------------
        def task_rheader(r):
            """ Task Resource Headers """

            rheader = None

            if r.representation == "html":
                table = r.table
                record = r.record
                if record:
                    if r.name == "task":
                        tabs = [(T("Details"), None),
                                (T("Comments"), "discuss")
                               ]
                        if deployment_settings.has_module("doc"):
                            tabs.append((T("Attachments"), "document"))
                        if deployment_settings.has_module("hrm"):
                            tabs.append((T("Roles"), "job_role"))
                            tabs.append((T("Assignments"), "human_resource"))
                        if deployment_settings.has_module("req"):
                            tabs.append((T("Requests"), "req"))

                        rheader_tabs = s3_rheader_tabs(r, tabs)

                        rheader = DIV(TABLE(
                            TR(
                                TH("%s: " % table.name.label),
                                record.name,
                                TH("%s: " % table.site_id.label),
                                org_site_represent(record.site_id),
                                ),
                            TR(
                                TH("%s: " % table.pe_id.label),
                                s3_pentity_represent(record.pe_id,
                                                     show_label=False),
                                TH("%s: " % table.location_id.label),
                                gis_location_represent(record.location_id),
                                ),
                            TR(
                                TH("%s: " % table.description.label),
                                record.description
                                ),
                            ), rheader_tabs)

            return rheader

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return dict(
            project_id = project_id,
            project_represent = project_represent,
            project_rheader = project_rheader,
            project_organisation_types = project_organisation_types,
            activity_id = activity_id,
            task_id = task_id,
            task_rheader = task_rheader,
            #need_type_represent = need_type_represent
        )

    # =========================================================================
    # Provide a handle to this load function
    #
    s3mgr.loader(project_tables,
                 "project_hazard",
                 "project_theme",
                 "project_project",
                 "project_organisation",
                 "project_activity_type",
                 "project_activity",
                 "project_site",
                 "project_beneficiary_type",
                 "project_beneficiary",
                 "project_task",
                 "project_comment",
                 #"project_need_type",
                 #"project_need"
                 )

else:
    # =========================================================================
    # Allow FKs to be added safely to other models in case module disabled
    #
    def project_id(**arguments):
        return Field("project_id", "integer", readable=False, writable=False)
    response.s3.project_id = project_id

    def activity_id(**arguments):
        return Field("activity_id", "integer", readable=False, writable=False)
    response.s3.activity_id = activity_id

    def task_id(**arguments):
        return Field("task_id", "integer", readable=False, writable=False)
    response.s3.task_id = task_id

# END =========================================================================
