# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL
from gluon.storage import Storage
from gluon.validators import IS_IN_SET
from gluon.html import *

from s3 import *
from menus import S3OptionsMenu

def config(settings):
    """
        Template settings for Sahana Software Foundation's 'Sunflower'

        http://eden.sahanafoundation.org/wiki/BluePrint/Sunflower
    """

    T = current.T

    # Pre-Populate
    settings.base.prepopulate += ("historic/SSF", "default/users")
    # Base settings
    settings.base.system_name = T("Sahana Sunflower: A Community Portal")
    settings.base.system_name_short = T("Sahana Sunflower")
    settings.base.theme = "historic.SSF"

    # UI
    settings.ui.icons = "font-awesome3"
    settings.ui.custom_icons = {
        "watch": "icon-eye-open",
        "unwatch": "icon-eye-close",
        "rss": "icon-rss-sign",
        "deploy": "icon-rocket",
        "contribute": "icon-lightbulb",
    }

    # Message
    settings.msg.notify_email_format = "text"

    # Auth settings
    settings.auth.registration_requires_verification = True
    settings.auth.registration_requires_approval = False
    # Uncomment this to set the opt in default to True
    settings.auth.opt_in_default = True
    # Uncomment this to default the Organisation during registration
    settings.auth.registration_organisation_default = "Sahana Software Foundation"
    # Always notify the approver of a new (verified) user, even if the user is automatically approved
    settings.auth.always_notify_approver = True
    # Assign the new users the permission to read.
    settings.auth.registration_roles = {"organisation_id": ["PROJECT_READ"],
                                        }

    # L10n settings
    settings.L10n.languages = OrderedDict([
       ("ar", "العربية"),
       ("bs", "Bosanski"),
       ("en", "English"),
       ("fr", "Français"),
       ("de", "Deutsch"),
       ("el", "ελληνικά"),
       ("es", "Español"),
       ("it", "Italiano"),
       ("ja", "日本語"),
       ("km", "ភាសាខ្មែរ"),
       ("ko", "한국어"),
       ("ne", "नेपाली"),          # Nepali
       ("prs", "دری"), # Dari
       ("ps", "پښتو"), # Pashto
       ("pt", "Português"),
       ("pt-br", "Português (Brasil)"),
       ("ru", "русский"),
       ("tet", "Tetum"),
       ("tl", "Tagalog"),
       ("ur", "اردو"),
       ("vi", "Tiếng Việt"),
       ("zh-cn", "中文 (简体)"),
       ("zh-tw", "中文 (繁體)"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "en"
    # Display the language toolbar
    settings.L10n.display_toolbar = True
    # Default timezone for users
    settings.L10n.utc_offset = "+0000"

    # Add thousands separator to numbers, eg. 1,000,000
    #settings.L10n.thousands_separator = True

    # Finance settings
    #settings.fin.currencies = {
    #    "USD" : "United States Dollars",
    #    "EUR" : "Euros",
    #    "GBP" : "Great British Pounds",
    #}
    #settings.fin.currency_default = "USD" # Dollars
    #settings.fin.currency_writable = False # False currently breaks things
    # Display Resources recorded to Admin-Level Locations on the map

    # @ToDo: Move into gis_config?
    settings.gis.display_L0 = False
    # Duplicate Features so that they show wrapped across the Date Line?
    # Points only for now
    # lon<0 have a duplicate at lon+360
    # lon>0 have a duplicate at lon-360
    settings.gis.duplicate_features = False
    # Mouse Position: 'normal', 'mgrs' or 'off'
    settings.gis.mouse_position = "normal"
    # Do we have a spatial DB available? (currently unused. Will support PostGIS & Spatialite.)
    settings.gis.spatialdb = False

    # Use 'soft' deletes
    settings.security.archive_not_delete = True
    # Should users be allowed to register themselves?
    settings.security.self_registration = True

    # AAA Settings

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table & Organisation ACLs
    # 7: Apply Controller, Function, Table, Organisation & Facility ACLs

    settings.security.policy = 5


    # Human Resource Management
    # Uncomment to hide the Staff resource
    settings.hrm.show_staff = False

    # Enable the use of Organisation Branches
    settings.org.branches = True

    # Project
    # Uncomment this to use settings suitable for detailed Task management
    settings.project.mode_task = True
    # Uncomment this to use Activities for projects & tasks
    #settings.project.activities = True
    # Uncomment this to enable Milestones in tasks
    settings.project.milestones = True
    # Uncomment this to enable Sectors in projects
    settings.project.sectors = True
    # Uncomment this to use Projects for Activities & Tasks
    settings.project.projects = True
    # Uncomment this to use Tags in Tasks
    settings.project.task_tag = True
    # Uncomment this to enable Hazards in 3W projects
    settings.project.hazards = True
    # Uncomment this to enable Themes in 3W projects
    settings.project.themes = True
    # Uncomment this to use multiple Organisations per project
    settings.project.multiple_organisations = True
    # Uncomment this to use emergency contacts in pr
    settings.pr.show_emergency_contacts = False

    # -----------------------------------------------------------------------------
    def deployment_page(r, **attr):
        """
            Custom Method for deployment page.
        """

        if r.http != "GET":
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        output = {}

        output["deployment_name"] = r.record.name
        output["description"] = r.record.description

        # Query the organisation name
        otable = s3db.org_organisation
        query = (otable.id == r.record.organisation_id) & \
                (otable.deleted == False)

        rows = db(query).select(otable.name,
                                    limitby=(0, 1)).first()
        output["org_name"] = rows.name

        # Query the locations
        ltable = s3db.project_location
        gtable = s3db.gis_location
        query = (ltable.project_id == r.id) & \
                (ltable.location_id == gtable.id) & \
                (gtable.deleted == False)
        rows = db(query).select(gtable.name)
        output["locations"] = [row.name for row in rows]

        # Query the links
        dtable = s3db.doc_document
        query = (dtable.doc_id == r.record.doc_id) & \
                (dtable.url != "") & \
                (dtable.url != None) & \
                (dtable.deleted == False)
        rows = db(query).select(dtable.name, dtable.url)
        output["links"] = [(row.name, row.url) for row in rows]


        query = (dtable.doc_id == r.record.doc_id) & \
                (dtable.file != "") & \
                (dtable.file != None) & \
                (dtable.deleted == False)
        rows = db(query).select(dtable.name, dtable.file)
        output["files"] = [(row.name, row.file) for row in rows]

        # Set the custom view
        from os import path
        view = path.join(current.request.folder, "modules", "templates",
                         "SSF", "views", "deployment_page.html")
        try:
            # Pass view as file not str to work in compiled mode
            current.response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP(404, "Unable to open Custom View: %s" % view)

        return output

    # -----------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        tablename = "project_project"

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            s3.crud_strings["project_member"] = Storage(
                msg_record_created = None,
                msg_record_deleted = None
            )

            if r.interactive:
                is_deployment = False

                stable = s3db.project_sector_project
                otable = s3db.org_sector

                # Edit the end_date label of "project_milestone" table
                milestone_table = s3db.project_milestone
                milestone_table.date.label = T("End Date")

                # Check if current record is Deployment
                if r.id:
                    # Viewing details of project_project record
                    query = (stable.project_id == r.id) & \
                            (otable.id == stable.sector_id)
                    rows = db(query).select(otable.name)
                    for row in rows:
                        if row.name == "Deployment":
                            is_deployment = True

                request_sector = r.get_vars.get("sector.name")

                # Viewing Projects/Deployments Page
                if request_sector and "Deployment" in request_sector:
                    is_deployment = True

                if is_deployment:
                    # Change the Side-Menu
                    menu = current.menu
                    menu.options = S3OptionsMenu("deployment").menu
                    menu.main.select("deployment")
                    # Change the CRUD strings and labels
                    s3db[tablename].name.label = T("Deployment Name")
                    s3.crud_strings[tablename] = Storage(
                        label_create = T("Create Deployment"),
                        title_display = T("Deployment Details"),
                        title_list = T("Deployments"),
                        title_update = T("Edit Deployment"),
                        title_report = T("Deployment Report"),
                        title_upload = T("Import Deployments"),
                        label_list_button = T("List Deployments"),
                        label_delete_button = T("Delete Deployment"),
                        msg_record_created = T("Deployment added"),
                        msg_record_modified = T("Deployment updated"),
                        msg_record_deleted = T("Deployment deleted"),
                        msg_list_empty = T("No Deployments currently registered")
                    )
                    # Set the method for deployment page
                    s3db.set_method(r.controller,
                                    r.function,
                                    method = "deployment",
                                    action = deployment_page)
                else:
                     current.menu.main.select("project")

                if not r.component:
                    # Viewing project/deployment's Basic Details
                    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink
                    if is_deployment:
                        # Bring back to the Deployments page if record deleted
                        delete_next = URL(c="project", f="project",
                                          vars={"sector.name": "None,Deployment"})

                        # Get sector_id for Deployment
                        row = db(otable.name == "Deployment").select(otable.id,
                                                                     limitby=(0, 1)
                                                                     ).first()

                        # Modify the CRUD form
                        crud_form = S3SQLCustomForm(
                            "organisation_id",
                            "name",
                            "sector_project.sector_id",
                            "description",
                            "status_id",
                            "start_date",
                            "end_date",
                            "calendar",
                            S3SQLInlineComponent(
                                "location",
                                label = T("Countries"),
                                fields = ["location_id"],
                                orderby = "location_id$name",
                                render_list = True
                            ),
                            S3SQLInlineLink(
                                "hazard",
                                label = T("Hazard"),
                                field = "hazard_id",
                            ),
                            S3SQLInlineLink(
                                "theme",
                                label = T("Type"),
                                field = "theme_id",
                            ),
                            "human_resource_id",
                            # Files
                            S3SQLInlineComponent(
                                "document",
                                name = "file",
                                label = T("Files"),
                                fields = [(T("Type"), "name"), "file"],
                                filterby = dict(field = "file",
                                                options = "",
                                                invert = True,
                                                )
                            ),
                            # Links
                            S3SQLInlineComponent(
                                "document",
                                name = "url",
                                label = T("Links"),
                                fields = [(T("Type"), "name"), "url"],
                                filterby = dict(field = "url",
                                                options = None,
                                                invert = True,
                                                )
                            ),
                            S3SQLInlineComponent(
                                "image",
                                fields = ["", "file"],
                                filterby = dict(field = "file",
                                                options = "",
                                                invert = True,
                                                )
                            ),
                            "comments",
                            )

                        location_id = s3db.project_location.location_id
                        # Limit to just Countries
                        location_id.requires = s3db.gis_country_requires
                        # Use dropdown, not AC
                        location_id.widget = None
                    else:
                        # Bring back to the Projects page if record deleted
                        delete_next = URL(c="project", f="project",
                                          vars={"sector.name": "None,Project"})

                        # Get sector_id for Project
                        row = db(otable.name == "Project").select(otable.id,
                                                                  limitby=(0, 1)
                                                                  ).first()

                        # Modify the CRUD form
                        crud_form = S3SQLCustomForm("organisation_id",
                                                    "name",
                                                    "sector_project.sector_id",
                                                    "description",
                                                    "status_id",
                                                    "start_date",
                                                    "end_date",
                                                    "calendar",
                                                    "human_resource_id",
                                                    "comments",
                                                    )

                    # Set the default sector
                    try:
                        stable.sector_id.default = row.id
                    except:
                        current.log.error("Pre-Populate",
                                          "Sectors not prepopulated")

                    # Remove Add Sector button
                    stable.sector_id.comment = None

                    s3db.configure(tablename,
                                   crud_form = crud_form,
                                   delete_next = delete_next,
                                   )

            return True

        s3.prep = custom_prep

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive and r.id is None:
                # Change the Open button to deployment page if deployment
                request_sector = r.get_vars.get("sector.name")

                if request_sector and "Deployment" in request_sector:
                    s3.actions[0]["url"] = URL(c="project", f="project",
                                               args=["[id]", "deployment"])

            # Add Interested option
            if r.component_name == "task" and r.component_id:
                task_table = s3db.project_task
                query = (task_table.id == r.component_id)
                row = db(query).select(task_table.uuid).first()
                data = get_member_data(task_id = r.component_id,
                                       task_uuid = row.uuid)
                interest = task_member_option(data,
                                              as_div = True)
                if "item" in output:
                    item = output["item"]
                    item.components.insert(0, interest)
                if "form" in output:
                    form = output["form"]
                    form.components.insert(0, interest)

            return output
        s3.postp = custom_postp

        args = current.request.args
        if len(args) > 1 and args[1] == "task":
            attr["hide_filter"] = False

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

    # -----------------------------------------------------------------------------
    def customise_project_task_controller(**attr):

        response = current.response
        s3db = current.s3db
        auth = current.auth
        s3 = response.s3
        current.menu.options = S3OptionsMenu("task").menu

        def task_rheader(r):

            tablename = r.tablename
            record = r.record
            table = r.table

            if r.representation != "html" or not record:
                # rheaders are only used in interactive views
                return None

            settings = current.deployment_settings
            attachments_label = settings.get_ui_label_attachments()
            # Tabs
            tabs = [(T("Details"), None),
                    (attachments_label, "document")]
            append = tabs.append
            if settings.has_module("msg"):
                append((T("Notify"), "dispatch"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            # rheader
            resource = r.resource
            fields = resource.fields + ['task_tag.tag_id',
                                        'task_milestone.milestone_id',
                                        'task_project.project_id']

            data = resource.select(fields,
                                   getids=True,
                                   represent=True)
            try:
                row = data.rows[0]
            except IndexError:
                rheader = ""
            else:
                member_data = get_member_data(r.id, row["project_task.uuid"])
                interest = task_member_option(member_data)

                project = TR(TH("%s: " % T("Project")),
                             row["project_task_project.project_id"])

                tags = TR(TH("%s: " % T("Tags")),
                          row["project_task_tag.tag_id"])

                created_by = TR(TH("%s: " % T("Created By")),
                                row["project_task.created_by"])

                milestone = TR(TH("%s: " % T("Milestone")),
                               row["project_task_milestone.milestone_id"])

                status = TR(TH("%s: " % T("Status")),
                            row["project_task.status"])

                rheader = DIV(TABLE(project,
                                    TR(TH("%s: " % table.name.label),
                                       record.name,
                                    ),
                                    milestone,
                                    tags,
                                    status,
                                    created_by,
                                    interest,
                                    ), rheader_tabs)
            return rheader

        attr["rheader"] = task_rheader
        return attr

    settings.customise_project_task_controller = customise_project_task_controller

    # -----------------------------------------------------------------------------
    def project_member_onaccept(form, task_id):
        """
            After DB I/O for Project Member
            - Subscribe User to Task updates
        """
        if task_id is None:
            task_id = str(form.vars.task_id)
        sub = TaskSubscriptions()
        sub.add_task_subscription(task_id)

    # -----------------------------------------------------------------------------
    def project_member_ondelete(form, task_id):
        """
            - Unsubscribe User to Task updates
        """
        sub = TaskSubscriptions()
        sub.remove_task_subscription(task_id)

    # -----------------------------------------------------------------------------
    def customise_project_member_resource(r, tablename):

        s3db = current.s3db
        task_id = current.request.get_vars.get("task_id")
        s3db.configure("project_member",
                       onaccept = lambda form: project_member_onaccept(form, task_id),
                       ondelete = lambda form: project_member_ondelete(form, str(r.id)))

    settings.customise_project_member_resource = customise_project_member_resource

    # -----------------------------------------------------------------------------
    def customise_project_member_controller(**attr):

        request = current.request
        task_id = request.get_vars["task_id"]
        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False
            if r.representation == "s3json":
                # Check if already a Member ?
                task_id = r.get_vars.task_id
                db = current.db
                mtable = current.s3db.project_member
                user = current.auth.s3_logged_in_person()
                query = (mtable.task_id == task_id) & \
                        (mtable.person_id == user)
                rows = db(query).select(mtable.id, limitby = (0, 1))
                if rows:
                    # Bypass request
                    item = current.xml.json_message(success=True,
                                                    created=[rows[0].id])
                    result = {"output": {"item": item},
                              "bypass": True}
                    return result
                else:
                    return True
            else:
                return False

        s3.prep = custom_prep
        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)
            if "item" in output:
                # Bypass
                current.response.headers["Content-Type"] = "application/json"
            return output

        s3.postp = custom_postp
        return attr

    settings.customise_project_member_controller = customise_project_member_controller

    # -----------------------------------------------------------------------------
    def get_member_data(task_id,
                        task_uuid):
        """
            Retreive the Data to be used by the 'Watch Button' in
            Client-Side.

            @param task_id: Task id
            @param task_uuid: Task UUID
        """
        response = current.response
        s3 = response.s3
        s3db = current.s3db
        auth = current.auth
        db = current.db

        # Check if the User has a role
        user = auth.s3_logged_in_person()
        mtable = s3db.project_member
        rtable = s3db.project_role

        query = (mtable.task_id == task_id) & \
                (mtable.deleted == False) & \
                (mtable.person_id == user)

        user_role = db(query).select(mtable.id,
                                     mtable.uuid).first()
        data = dict(task_uuid = task_uuid,
                    url = "/project/task/%s/member/" % (str(task_id)),
                    id = "null")

        if user_role:
            data["id"] = str(user_role.id)

        return data

    # -----------------------------------------------------------------------------
    def task_member_option(data,
                           as_div = False):
        """
            returns an Button to allow Users to 'Watch' Tasks.

            @param data: Data to be added to the Button
            @param as_div: button to be displayed in a form.
                           default => rheader
        """
        auth = current.auth
        s3 = current.response.s3
        scripts = s3.scripts

        WATCH = T("Watch")
        UNWATCH = T("Unwatch")
        scripts.append("/%s/static/themes/SSF/js/role.js" % \
                                            (current.request.application))

        s3.js_global.append('''
    i18n.assign_role="%s"
    i18n.revert_role="%s"''' % (WATCH,
                                UNWATCH))

        user_id = auth.s3_logged_in_person()

        if not user_id:
            interest = ""
        else:
            _id = data["id"]
            if _id == "null":
                icon = ICON("watch")
                label = WATCH
            else:
                icon = ICON("unwatch")
                label = UNWATCH

            button = A(icon,
                       SPAN(label),
                       data = data,
                       _id="assign-role",
                       _class="button action-btn")
            if as_div:
                interest = DIV(BR(),
                               button,
                               _id="assign-container")
            else:
                interest = TD(button)

        return interest

    # -----------------------------------------------------------------------------
    def custom_project_task_create_onaccept(form):
        """
            - Subscribe author to updates
            - Add author as a Member
        """

        user = current.auth.s3_logged_in_person()
        task_id = form.vars.id
        current.s3db.project_member.insert(task_id=task_id,
                                           person_id=user)
        sub = TaskSubscriptions()
        sub.add_task_subscription(str(task_id))

    # -----------------------------------------------------------------------------
    def customise_project_task_resource(r, tablename):
        """
            Customise project_task resource
            - CRUD Form
            Runs after controller customisation
            But runs before prep
        """

        s3db = current.s3db
        db = current.db
        T = current.T
        crud_strings = current.response.s3.crud_strings

        crud_strings["project_member"] = Storage(
            msg_record_created = None,
            msg_record_deleted = None
        )

        get_config = s3db.get_config

        if r.interactive or r.representation == "aadata":
            # Remove "Assigned to" field from table
            list_fields = get_config(tablename, "list_fields")
            try:
                list_fields.remove("pe_id")
            except ValueError:
                pass

        if r.interactive:
            trimmed_task = False
            get_vars = r.get_vars
            ADD_TASK = T("Create Task")

            # Check if it is a bug report
            if get_vars.get("bug"):
                tagname = "bug"
                trimmed_task = True
                ADD_TASK = T("Report a Bug")

            # Check if it is a feature request
            elif get_vars.get("featureRequest"):
                tagname = "feature request"
                trimmed_task = True
                ADD_TASK = T("Request a Feature")

            # Check if it is a support task
            elif get_vars.get("support"):
                tagname = "support"
                trimmed_task = True
                ADD_TASK = T("Request Support")

            from s3.s3forms import S3SQLCustomForm, S3SQLInlineLink, S3SQLInlineComponent
            if trimmed_task:
                # Show a trimmed view of creating task
                crud_fields = ["name",
                               "description",
                               S3SQLInlineLink(
                                   "tag",
                                   label = T("Tag"),
                                   field = "tag_id",
                               ),
                               "priority",
                               "status",
                               S3SQLInlineComponent(
                                   "document",
                                   label = T("Attachment"),
                                   fields = ["", "file"],
                               ),
                               ]

                crud_strings["project_task"]["label_create"] = ADD_TASK
                tagtable = s3db.project_tag
                query = (tagtable.deleted != True) & \
                        (tagtable.name == tagname)
                row = db(query).select(tagtable.id, limitby=(0, 1)).first()

                # Set the tag
                try:
                    s3db.project_task_tag.tag_id.default = row.id
                except:
                    current.log.error("Pre-Populate",
                                      "Tags not prepopulated")
            else:
                # Show all fields for creating the task
                crud_fields = [S3SQLInlineComponent(
                                   "task_milestone",
                                   label = T("Milestone"),
                                   fields = [("", "milestone_id")],
                                   multiple = False,
                               ),
                               "name",
                               "description",
                               S3SQLInlineComponent(
                                   "task_tag",
                                   label = T("Tags"),
                                   fields = [("", "tag_id")],
                               ),
                               "priority",
                               "status",
                               S3SQLInlineComponent(
                                   "member",
                                   label = T("Members"),
                                   fields = [("", "person_id")],
                                   readonly = True,
                               ),
                               "source",
                               "date_due",
                               "time_estimated",
                               S3SQLInlineComponent(
                                   "document",
                                   label = T("Attachment"),
                                   fields = ["", "file"],
                               ),
                               S3SQLInlineComponent("time",
                                    label = T("Time Log"),
                                    fields = ["date",
                                              "person_id",
                                              "hours",
                                              "comments"
                                              ],
                                    orderby = "date"
                               ),
                               "time_actual",
                               ]
                if r.tablename == "project_task":
                    # Add the project field if it is not under the component
                    crud_fields.insert(0, S3SQLInlineComponent("task_project",
                                                               label = T("Project"),
                                                               fields = [("", "project_id")],
                                                               multiple = False,
                                                               ))

            # Remove filter for "Assigned to"
            filter_widgets = get_config(tablename, "filter_widgets")
            custom_filter_widgets = [widget for widget in filter_widgets
                                            if widget.field != "pe_id"]

            create_onaccept = get_config(tablename, "create_onaccept")
            s3db.configure(tablename,
                           crud_form = S3SQLCustomForm(*crud_fields),
                           filter_widgets = custom_filter_widgets,
                           create_onaccept = [create_onaccept,
                                              custom_project_task_create_onaccept,
                                              ],
                           )

    settings.customise_project_task_resource = customise_project_task_resource

    # -----------------------------------------------------------------------------
    def project_comment_onaccept(form):
        """
            After DB I/O for Task Comments
            - Add User as a Member of the task
        """
        user = current.auth.s3_logged_in_person()
        mtable = current.s3db.project_member
        task_id = current.request.args[0]

        if user:
            query = (mtable.person_id == user) & \
                    (mtable.task_id == task_id)
            member = current.db(query).select(mtable.role_id, limitby=(0, 1))
            if not member:
                # Add User as a Member
                mtable.insert(task_id=task_id,
                              person_id=user)
                # Subscribe user to task updates
                sub = TaskSubscriptions()
                sub.add_task_subscription(task_id)

    # -----------------------------------------------------------------------------
    def customise_project_comment_resource(r, tablename):

        crud_strings = current.response.s3.crud_strings
        T = current.T
        s3db = current.s3db
        from s3 import s3_unicode

        crud_strings[tablename] = Storage(
            title_list = T("Task Comments")
        )
        task_id = r.id
        # Notification Fields
        s3db.configure(tablename,
                       notify_fields = ["task_id",
                                        "created_by",
                                        "body"],
                       onaccept = project_comment_onaccept,
                       )

        # Custom Represent to change represent link
        DefaultTaskRepresent = s3db.project_TaskRepresent
        class custom_TaskRepresent(DefaultTaskRepresent):
            """
                Custom Represent to include public 'URL' in Task link
            """
            def link(self, k, v, row=None):
                """
                    @param k: the key
                    @param v: the representation of the key
                    @param row: the row with this key (unused in the base class)
                """
                k = s3_unicode(k)
                public_url = settings.get_base_public_url()
                if self.linkto:
                    task_url = self.linkto
                else:
                    task_url = URL(c="project", f="task", args=["[id]"])
                task_url = task_url.replace("[id]", k) \
                                   .replace("%5Bid%5D", k)
                link = public_url + task_url
                return A(v, _href=link)

        s3db.project_comment.task_id.represent = custom_TaskRepresent(show_link=True)

    settings.customise_project_comment_resource = customise_project_comment_resource

    # -----------------------------------------------------------------------------
    def customise_project_comment_controller(**attr):

        s3 = current.response.s3

        # Custom Prep
        def custom_prep(r):
            if r.representation in ("rss", "msg"):
                return True
            return False
        s3.prep = custom_prep

        return attr

    settings.customise_project_comment_controller = customise_project_comment_controller

    # -----------------------------------------------------------------------------
    def customise_delphi_problem_controller(**attr):

        tablename = "delphi_problem"

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Goal"),
            title_display = T("Goal Details"),
            title_list = T("Goals"),
            title_update = T("Edit Goal"),
            title_report = T("Goal Report"),
            title_upload = T("Import Goals"),
            label_list_button = T("List Goals"),
            label_delete_button = T("Delete Goal"),
            msg_record_created = T("Goal added"),
            msg_record_modified = T("Goal updated"),
            msg_record_deleted = T("Goal deleted"),
            msg_list_empty = T("No Goals currently registered")
        )
        return attr

    settings.customise_delphi_problem_controller = customise_delphi_problem_controller

    # -----------------------------------------------------------------------------
    def customise_delphi_solution_controller(**attr):

        tablename = "delphi_solution"

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Initiative"),
            title_display = T("Initiative Details"),
            title_list = T("Initiatives"),
            title_update = T("Edit Initiative"),
            title_report = T("Initiative Report"),
            title_upload = T("Import Initiatives"),
            label_list_button = T("List Initiatives"),
            label_delete_button = T("Delete Initiative"),
            msg_record_created = T("Initiative added"),
            msg_record_modified = T("Initiative updated"),
            msg_record_deleted = T("Initiative deleted"),
            msg_list_empty = T("No Initiatives currently registered")
        )
        return attr

    settings.customise_delphi_solution_controller = customise_delphi_solution_controller

    # -----------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3
        s3db = current.s3db

        # Change the tabs in the rheader
        tabs = [(T("Basic Details"), None),
                ]
        has_permission = current.auth.s3_has_permission
        if has_permission("read", "pr_contact"):
            tabs.append((T("Contact Details"), "contacts"))

        attr["rheader"] = lambda r: s3db.pr_rheader(r, tabs=tabs)

        # Custom Prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            resource = r.resource
            if r.interactive or r.representation == "aadata":
                # Set the list fields
                list_fields = ("first_name",
                               "middle_name",
                               "last_name",
                               "human_resource.organisation_id",
                               "address.location_id",
                               )
                resource.configure(list_fields = list_fields)

            if r.interactive:
                tablename = "pr_person"

                # Set the CRUD Strings
                s3.crud_strings[tablename] = Storage(
                    label_create = T("Create a Contributor"),
                    title_display = T("Contributor Details"),
                    title_list = T("Contributors"),
                    title_update = T("Edit Contributor Details"),
                    label_list_button = T("List Contributors"),
                    label_delete_button = T("Delete Contributor"),
                    msg_record_created = T("Contributor added"),
                    msg_record_modified = T("Contributor details updated"),
                    msg_record_deleted = T("Contributor deleted"),
                    msg_list_empty = T("No Contributors currently registered")
                )

                # Custom Form (Read/Create/Update)
                from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
                crud_form = S3SQLCustomForm(
                    "first_name",
                    "middle_name",
                    "last_name",
                    S3SQLInlineComponent("contact",
                        label = T("Email"),
                        multiple = False,
                        fields = [("", "value")],
                        filterby = dict(field = "contact_method",
                                        options = "EMAIL"),
                        ),
                    "gender",
                    S3SQLInlineComponent("note",
                        name = "bio",
                        label = T("Bio Paragraph"),
                        multiple = False,
                        fields = [("", "note_text")],
                        ),
                    S3SQLInlineComponent(
                        "image",
                        name = "image",
                        label = T("Photo"),
                        multiple = False,
                        fields = [("", "image")],
                        filterby = dict(field = "profile",
                                        options=[True]
                                        ),
                        ),
                    S3SQLInlineComponent(
                        "human_resource",
                        name = "hrm_human_resource",
                        label = "",
                        multiple = False,
                        fields = ["", "organisation_id", "job_title_id"],
                        ),
                    S3SQLInlineComponent(
                            "address",
                            label = T("Home Location"),
                            fields = [("", "location_id")],
                            render_list = True
                        ),
                    )
                resource.configure(crud_form = crud_form)
            return True
        s3.prep = custom_prep

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -----------------------------------------------------------------------------
    def customise_pr_contact_controller(**attr):

        s3 = current.response.s3
        s3db = current.s3db

        # Custom Prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            if r.interactive:
                # Change the contact methods appearing in adding contact info
                MOBILE = current.deployment_settings.get_ui_label_mobile_phone()
                contact_methods = {"SKYPE":       T("Skype"),
                                   "SMS":         MOBILE,
                                   "IRC":         T("IRC handle"),
                                   "GITHUB":      T("Github Repo"),
                                   "LINKEDIN":    T("LinkedIn Profile"),
                                   "BLOG":        T("Blog"),
                                   }
                s3db.pr_contact.contact_method.requires = IS_IN_SET(contact_methods,
                                                                    zero=None)

                from s3.s3forms import S3SQLCustomForm

                crud_form = S3SQLCustomForm(
                        "contact_method",
                        "value",
                    )
                s3db.configure("pr_contact",
                               crud_form = crud_form,
                               )

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_pr_contact_controller = customise_pr_contact_controller

    # -----------------------------------------------------------------------------
    def custom_render(resource, data, meta_data, format=None):
        """
            Custom Method to pre-render the contents for the message template

            @param resource: the S3Resource
            @param data: the data returned from S3Resource.select
            @param meta_data: the meta data for the notification
            @param format: the contents format ("text" or "html")
        """
        rows = data["rows"]

        if format == "text":

            created_on_selector = resource.prefix_selector("created_on")
            created_on_colname = None
            notify_on = meta_data["notify_on"]
            last_check_time = meta_data["last_check_time"]
            rfields = data["rfields"]
            output = {}
            new, upd = [], []

            # Standard text format
            labels = []
            append = labels.append

            for rfield in rfields:
                if rfield.selector == created_on_selector:
                    created_on_colname = rfield.colname
                elif rfield.ftype != "id":
                    append((rfield.colname, rfield.label))

            for row in rows:
                append_record = upd.append
                if created_on_colname:
                    try:
                        created_on = row["_row"][created_on_colname]
                    except KeyError, AttributeError:
                        pass
                    else:
                        if s3_utc(created_on) >= last_check_time:
                            append_record = new.append

                record = []
                append_column = record.append
                for colname, label in labels:
                    append_column((label, row[colname]))
                append_record(record)

            if "new" in notify_on and len(new):
                output["new"] = len(new)
                output["new_records"] = new
            else:
                output["new"] = None
            if "upd" in notify_on and len(upd):
                output["upd"] = len(upd)
                output["upd_records"] = upd
            else:
                output["upd"] = None
        else:
            # ** Styling must be inline for HTML emails **
            panel_body = "border-radius:4px;\
                          box-shadow:0 1px 1px rgba(0, 0, 0, 0.05);\
                          background-color:#fff;\
                          border:1px solid transparent;\
                          border-color:#ddd;"
            panel_title = "border-top-left-radius:3px;\
                           border-top-right-radius:3px;\
                           padding:10px 15px;\
                           background-color:#f5f5f5;\
                           color:#333;\
                           border-bottom:1px solid #ddd;"
            panel_heading = "color:inherit;\
                             font-size:14px;\
                             margin-bottom:0px;\
                             margin-top:0px;\
                             border-color:#ddd;"
            panel_contents = "padding:15px;"
            elements = []
            append = elements.append
            for row in rows:
                comment_title = TAG[""](B(row["project_comment.created_by"]),
                                        XML("&nbsp;&nbsp; commented on &nbsp;&nbsp;"),
                                        B(row["project_comment.task_id"]))
                comment_body = XML(row["project_comment.body"])
                comment_container = DIV(DIV(DIV(comment_title,
                                                _style=panel_heading),
                                            _style=panel_title),
                                        DIV(comment_body,
                                            _style=panel_contents),
                                        _style=panel_body)
                append(comment_container)
                append(BR())
            output = {"body": DIV(*elements)}

        config_url = settings.get_base_public_url() + URL(c="default",
                                                          f="index",
                                                          args=["subscriptions"])
        output["config"] = A("Configure Subscription settings", _href=config_url)
        output.update(meta_data)
        return output

    settings.msg.notify_renderer = custom_render

    # -----------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
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
                #description = T("Site Administration"),
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                module_type = None  # This item is handled separately for the menu
            )),
        ("appadmin", Storage(
                name_nice = T("Administration"),
                #description = T("Site Administration"),
                restricted = True,
                module_type = None  # No Menu
            )),
        ("errors", Storage(
                name_nice = T("Ticket Viewer"),
                #description = T("Needed for Breadcrumbs"),
                restricted = False,
                module_type = None  # No Menu
            )),
        ("sync", Storage(
                name_nice = T("Synchronization"),
                #description = T("Synchronization"),
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                module_type = None  # This item is handled separately for the menu
            )),
        ("gis", Storage(
                name_nice = T("Map"),
                #description = T("Situation Awareness & Geospatial Analysis"),
                restricted = True,
                module_type = 6,     # 6th item in the menu
            )),
        ("pr", Storage(
                name_nice = T("Contributors"),
                description = T("Contributors to Sahana"),
                restricted = True,
                module_type = 2
            )),
        ("org", Storage(
                name_nice = T("Organizations"),
                #description = T('Lists "who is doing what & where". Allows relief agencies to coordinate their activities'),
                restricted = True,
                module_type = 10
            )),
        # All modules below here should be possible to disable safely
        ("hrm", Storage(
                name_nice = T("Volunteers"),
                #description = T("Human Resource Management"),
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
                module_type = 10,
            )),
        ("doc", Storage(
                name_nice = T("Documents"),
                #description = T("A library of digital resources, such as photos, documents and reports"),
                restricted = True,
                module_type = 10,
            )),
        ("msg", Storage(
                name_nice = T("Messaging"),
                #description = T("Sends & Receives Alerts via Email & SMS"),
                restricted = True,
                # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
                module_type = None,
            )),
        #("supply", Storage(
        #        name_nice = T("Supply Chain Management"),
        #        #description = T("Used within Inventory Management, Request Management and Asset Management"),
        #        restricted = True,
        #        module_type = None, # Not displayed
        #    )),
        #("asset", Storage(
        #        name_nice = T("Assets"),
        #        #description = T("Recording and Assigning Assets"),
        #        restricted = True,
        #        module_type = 5,
        #    )),
        #("req", Storage(
        #        name_nice = T("Requests"),
        #        #description = T("Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested."),
        #        restricted = True,
        #        module_type = 10,
        #    )),
        ("project", Storage(
                name_nice = T("Task Lists"),
                #description = T("Tracking of Projects, Activities and Tasks"),
                restricted = True,
                module_type = 1
            )),
        ("survey", Storage(
                name_nice = T("Surveys"),
                #description = T("Create, enter, and manage surveys."),
                restricted = True,
                module_type = 5,
            )),
        #("event", Storage(
        #        name_nice = T("Events"),
        #        #description = T("Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities)."),
        #        restricted = True,
        #        module_type = 10,
        #    )),
        # NB Budget module depends on Project Tracking Module
        #("budget", Storage(
        #        name_nice = T("Budgeting Module"),
        #        #description = T("Allows a Budget to be drawn up"),
        #        restricted = True,
        #        module_type = 10
        #    )),
        ("delphi", Storage(
                name_nice = T("Delphi Decision Maker"),
                #description = T("Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list."),
                restricted = False,
                module_type = 10,
            )),
        ("cms", Storage(
               name_nice = T("Content Management"),
               #description = T("Content Management System"),
               restricted = True,
               module_type = 3,
           )),
    ])

# -----------------------------------------------------------------------------
# Functions and Classes which are importable by other Templates
# -----------------------------------------------------------------------------

# =============================================================================
class TaskSubscriptions(object):
    """ Manage subscriptions """

    def __init__(self):

        # Available resources
        resources = [dict(resource="project_comment",
                          url="project/comment",
                          label=current.T("Updates"))
                     ]
        self.rfilter = "comment.task_id__belongs"
        # Remove comments created by the user
        self.exclude = ["comment.created_by__ne", str(current.auth.user.id)]
        # Get current subscription settings resp. from defaults
        self.subscription = self.get_subscription()
        subscription = self.subscription

        subscription["subscribe"] = [resources[0]]
        subscription["notify_on"] = ["new","upd"]
        subscription["frequency"] = "immediately"
        subscription["method"] = ["EMAIL"]

    def remove_task_subscription(self, task_id):
        """
            Remove Task from subscription filter
        """

        db = current.db
        s3db = current.s3db
        subscription = self.subscription
        rfilter = self.rfilter
        ids = subscription["get_vars"][rfilter].split(",")
        if task_id in ids:
            ids.remove(task_id)
        if len(ids) == 0:
            # Delete Subscription
            stable = s3db.pr_subscription
            db(stable.id == subscription["id"]).update(deleted=True)
            # No need for update_subscription
            return True
        else:
            ids = ",".join(ids)

        sfilter = [[rfilter, ids], self.exclude]
        subscription["filters"] = json.dumps(sfilter)

        return self.update_subscription()

    # -------------------------------------------------------------------------
    def add_task_subscription(self, task_id):
        """
            Add Task to subscription filter
        """

        subscription = self.subscription
        rfilter = self.rfilter

        if subscription["get_vars"].get(rfilter, None):
            # Add task_id to filter
            ids = subscription["get_vars"][rfilter]
            ids += "," + task_id
        else:
            ids = task_id

        sfilter = [[rfilter, ids], self.exclude]
        subscription["filters"] = json.dumps(sfilter)
        return self.update_subscription()

    # -------------------------------------------------------------------------
    def get_subscription(self):
        """
            Get current subscription settings
        """

        db = current.db
        s3db = current.s3db
        settings = current.deployment_settings

        pe_id = current.auth.user.pe_id

        stable = s3db.pr_subscription
        ftable = s3db.pr_filter
        query = (stable.pe_id == pe_id) & \
                (stable.deleted != True)
        left = ftable.on(ftable.id == stable.filter_id)
        row = db(query).select(stable.id,
                               stable.notify_on,
                               stable.frequency,
                               stable.email_format,
                               ftable.id,
                               ftable.query,
                               left=left,
                               limitby=(0, 1)).first()

        output = {"pe_id": pe_id}

        get_vars = {}
        if row:
            # Existing settings
            s = getattr(row, "pr_subscription")
            f = getattr(row, "pr_filter")

            rtable = s3db.pr_subscription_resource
            query = (rtable.subscription_id == s.id) & \
                    (rtable.deleted != True)
            rows = db(query).select(rtable.id,
                                    rtable.resource,
                                    rtable.url,
                                    rtable.last_check_time,
                                    rtable.next_check_time)
            if f.query:
                filters = json.loads(f.query)
                for k, v in filters:
                    if v is None:
                        continue
                    if k in get_vars:
                        if type(get_vars[k]) is list:
                            get_vars[k].append(v)
                        else:
                            get_vars[k] = [get_vars[k], v]
                    else:
                        get_vars[k] = v

            output.update({"id": s.id,
                           "filter_id": f.id,
                           "get_vars" : get_vars,
                           "resources": rows,
                           "notify_on": s.notify_on,
                           "frequency": s.frequency,
                           "method": ["EMAIL"], #s.method,
                           "email_format": s.email_format,
                           })

        else:
            # Form defaults
            output.update({"id": None,
                           "filter_id": None,
                           "get_vars" : get_vars,
                           "resources": None,
                           "notify_on": stable.notify_on.default,
                           "frequency": stable.frequency.default,
                           "method": ["EMAIL"], #stable.method.default
                           "email_format": settings.get_msg_notify_email_format(),
                           })
        return output

    # -------------------------------------------------------------------------
    def update_subscription(self):
        """
            Update subscription settings
        """

        db = current.db
        s3db = current.s3db
        subscription = self.subscription
        pe_id = subscription["pe_id"]

        # Save filters
        filter_id = subscription["filter_id"]
        filters = subscription.get("filters")
        if filters:
            ftable = s3db.pr_filter
            if not filter_id:
                success = ftable.insert(pe_id=pe_id, query=filters)
                filter_id = success
            else:
                success = db(ftable.id == filter_id).update(query=filters)
            if not success:
                return None

        # Save subscription settings
        stable = s3db.pr_subscription
        subscription_id = subscription["id"]
        frequency = subscription["frequency"]
        email_format = subscription["email_format"]
        if not subscription_id:
            success = stable.insert(pe_id=pe_id,
                                    filter_id=filter_id,
                                    notify_on=subscription["notify_on"],
                                    frequency=frequency,
                                    email_format=email_format,
                                    method=subscription["method"])
            subscription_id = success
        else:
            success = db(stable.id == subscription_id).update(
                            pe_id=pe_id,
                            filter_id=filter_id,
                            notify_on=subscription["notify_on"],
                            frequency=frequency,
                            email_format=email_format,
                            method=subscription["method"])
        if not success:
            return None

        # Save subscriptions
        rtable = s3db.pr_subscription_resource
        subscribe = subscription.get("subscribe")
        if subscribe:
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            resources = subscription["resources"]

            subscribed = {}
            timestamps = {}
            if resources:
                for r in resources:
                    subscribed[(r.resource, r.url)] = r.id
                    timestamps[r.id] = (r.last_check_time,
                                        r.next_check_time)

            intervals = s3db.pr_subscription_check_intervals
            interval = timedelta(minutes=intervals.get(frequency, 0))

            keep = set()
            fk = '''{"subscription_id":%s}''' % subscription_id
            for new in subscribe:
                resource, url = new["resource"], new["url"]
                if (resource, url) not in subscribed:
                    # Restore subscription if previously unsubscribed, else
                    # insert new record
                    unsubscribed = {"deleted": True,
                                    "deleted_fk": fk,
                                    "resource": resource,
                                    "url": url}
                    rtable.update_or_insert(_key=unsubscribed,
                                            deleted=False,
                                            deleted_fk=None,
                                            subscription_id=subscription_id,
                                            resource=resource,
                                            url=url,
                                            last_check_time=now,
                                            next_check_time=None)
                else:
                    # Keep it
                    record_id = subscribed[(resource, url)]
                    last_check_time, next_check_time = timestamps[record_id]
                    data = {}
                    if not last_check_time:
                        # Someone has tampered with the timestamps, so
                        # we need to reset them and start over
                        last_check_time = now
                        data["last_check_time"] = last_check_time
                    due = last_check_time + interval
                    if next_check_time != due:
                        # Time interval has changed
                        data["next_check_time"] = due
                    if data:
                        db(rtable.id == record_id).update(**data)
                    keep.add(record_id)

            # Unsubscribe all others
            unsubscribe = set(subscribed.values()) - keep
            db(rtable.id.belongs(unsubscribe)).update(deleted=True,
                                                      deleted_fk=fk,
                                                      subscription_id=None)

        # Update subscription
        subscription["id"] = subscription_id
        subscription["filter_id"] = filter_id
        return subscription

# END =========================================================================
