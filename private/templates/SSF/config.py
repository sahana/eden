# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current, URL
from gluon.storage import Storage
from gluon.validators import IS_IN_SET
from gluon.html import *

from s3 import *
from s3layouts import S3AddResourceLink

T = current.T
settings = current.deployment_settings

"""
    Template settings for SSF
"""

# Pre-Populate
settings.base.prepopulate = ("SSF", "default/users")

# Theme
settings.base.theme = "SSF"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
settings.ui.filter_formstyle = "table_inline"

# Uncomment to disable responsive behavior of datatables
# - Disabled until tested
settings.ui.datatables_responsive = False

# Should users be allowed to register themselves?
settings.security.self_registration = True
settings.auth.registration_requires_verification = True
settings.auth.registration_requires_approval = False

# Uncomment this to set the opt in default to True
settings.auth.opt_in_default = True
# Uncomment this to default the Organisation during registration
settings.auth.registration_organisation_default = "Sahana Software Foundation"

# Always notify the approver of a new (verified) user, even if the user is automatically approved
settings.auth.always_notify_approver = True

# Base settings
settings.base.system_name = T("Sahana Sunflower: A Community Portal")
settings.base.system_name_short = T("Sahana Sunflower")

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
settings.L10n.utc_offset = "UTC +0000"
# Default timezone for users
settings.L10n.utc_offset = "UTC +0000"

# Add thousands separator to numbers, eg. 1,000,000
#settings.L10n.thousands_separator = True

# Finance settings
#settings.fin.currencies = {
#    "USD" :T("United States Dollars"),
#    "EUR" :T("Euros"),
#    "GBP" :T("Great British Pounds")
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
# Uncomment this to allow Users assign themselves a 'role'
#settings.project.task_member_roles = True

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
    view = path.join(current.request.folder, "private", "templates",
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
    from gluon.tools import LOAD

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.interactive:
            is_deployment = False

            stable = s3db.project_sector_project
            otable = s3db.org_sector

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
 
        if r.component_name == "task" and r.component_id:
            # Put the Comments in the rfooter
            s3db.project_ckeditor()
            s3.rfooter = LOAD("project", "comments.load",
                              args=[r.component_id],
                              ajax=True)
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
            interest = task_member_option(record_id = r.component_id,
                                          as_div = True)
            if "item" in output:
                _item = output["item"]
                _item.components.insert(0, interest)
            if "form" in output:
                _form = output["form"]
                _form.components.insert(0, interest)

        return output
    s3.postp = custom_postp
    
    args = current.request.args
    if len(args) > 1 and args[1] == "task":
        attr["hide_filter"] = False

    return attr

settings.customise_project_project_controller = customise_project_project_controller

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
    auth = current.auth

    if r.interactive:
        trimmed_task = False
        get_vars = r.get_vars

        # Check if it is a bug report
        if get_vars.get("bug"):
            tagname = "bug"
            trimmed_task = True

        # Check if it is a feature request
        elif get_vars.get("featureRequest"):
            tagname = "feature request"
            trimmed_task = True

        # Check if it is a support task
        elif get_vars.get("support"):
            tagname = "support"
            trimmed_task = True

        from s3.s3forms import S3SQLCustomForm, S3SQLInlineLink, S3SQLInlineComponent
        if trimmed_task:
            # Show a trimmed view of creating task
            crud_fields = [S3SQLInlineComponent(
                               "task_member",
                               label = T("Members"),
                               fields = [("", "member_id")],
                               multiple = False,
                           ),
                           "name",
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
                               "task_member",
                               label = T("Members"),
                               fields = [("", "member_id")],
                               multiple = False,
                           ),
                           S3SQLInlineComponent(
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
                crud_fields.insert(1, S3SQLInlineComponent("task_project",
                                                           label = T("Project"),
                                                           fields = [("", "project_id")],
                                                           multiple = False,
                                                           ))
        crud_form = S3SQLCustomForm(*crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

settings.customise_project_task_resource = customise_project_task_resource

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
def assign_role(r, **attr):
    """
        Assign Role selected to User logged in
    """
    auth = current.auth
    s3db = current.s3db
    db = current.db

    if r.representation == "json" and r.http == "POST":

        mtable = s3db.project_member
        ltable = s3db.project_task_member
        user_id = auth.s3_logged_in_person()

        # Id of role
        r_id = r.post_vars["role"]

        if r.get_vars["action"] == "add":
            # Get the Role id selected
            r_id = r.post_vars["role"]
            
            # Check if role selected exists for user
            query = (mtable.person_id == user_id) & \
                    (mtable.role_id == r_id) 
            row = db(query).select(mtable.id).first()
            if row:
                m_id = row.id 
            else:
                m_id = mtable.insert(person_id=user_id,
                                     role_id=r_id)

            ltable.insert(member_id=m_id,
                          task_id=r.id)
        else:

            query = (mtable.person_id == user_id) & \
                    (mtable.role_id == r_id)

            # Get Member id of user
            row = db(query).select(mtable.id).first()
            
            query = (ltable.member_id == row.id) & \
                    (ltable.task_id == r.id)
            
            # Remove member from Link Table
            db(query).delete()

            # if a specific role no longer exists in any of the tasks
            # remove the record(user, role) from Members
            rows = db(ltable.member_id == row.id).select()
            if not rows:
                db(mtable.id == row.id).delete()

    else:
        r.error(501, current.ERROR.BAD_FORMAT)

    current.response.headers["Content-Type"] = "application/json"
    output = json.dumps(dict(status="Ok"))
    return output

# -----------------------------------------------------------------------------
def customise_project_task_controller(**attr):
    
    s3db = current.s3db
    auth = current.auth
    s3 = current.response.s3

    def task_rheader(r):
    
        if r.representation != "html":
            # rheaders are only used in interactive views
            return None
        
        response = current.response
        T = current.T

        tablename, record = s3_rheader_resource(r)

        if not record:
            return None
        
        table = s3db.table(tablename)

        resourcename = r.name

        T = current.T
        #auth = current.auth
        settings = current.deployment_settings

        attachments_label = settings.get_ui_label_attachments()
        # Tabs
        tabs = [(T("Details"), None)]
        append = tabs.append
        append((attachments_label, "document"))
        if settings.has_module("msg"):
            append((T("Notify"), "dispatch"))

        rheader_tabs = s3_rheader_tabs(r, tabs)
        
        # rheader
        db = current.db
        ltable = s3db.project_task_project
        ptable = db.project_project
        query = (ltable.deleted == False) & \
                (ltable.task_id == r.id) & \
                (ltable.project_id == ptable.id)
        row = db(query).select(ptable.id,
                               ptable.code,
                               ptable.name,
                               limitby=(0, 1)).first()
        if row:
            project = s3db.project_project_represent(None, row)
            project = TR(TH("%s: " % T("Project")),
                         project,
                         )
        else:
            project = TR(TH("%s: " % T("Project")),
                         "-",
                         )

        # Tags
        ltable = s3db.project_task_tag
        tag_represent = S3Represent(lookup="project_tag",
                                    translate=True)

        query = (ltable.task_id == r.id)
        rows = db(query).select(ltable.tag_id)
        tag_rows = [ str(tag_represent(row.tag_id)) for row in rows ]
        _tags = ", ".join(tag_rows)

        if rows:
            tags = TR(TH("%s: " % T("Tags")),
                      _tags)
        else:
            tags = TR(TH("%s: " % T("Tags")),
                      "-")

        if record.created_by:
            creator = TR(TH("%s: " % T("Created By")),
                         s3_auth_user_represent(record.created_by),
                         )
        else:
            creator = TR(TH("%s: " % T("Created By")),
                         "-"
                         )
        
        # Milestone 
        ltable = s3db.project_task_milestone
        milestone_represent = S3Represent(lookup="project_milestone",
                                          fields=["name", "date"],
                                          labels="%(name)s: %(date)s")

        query = (ltable.task_id == r.id) 
        row = db(query).select(ltable.milestone_id).first()
        
        if row:
            milestone = TR(TH("%s: " % T("Milestone")), 
                           milestone_represent(row.milestone_id))
        else:
            milestone = TR(TH("%s: " % T("Milestone")),
                           "-")

        # Status
        if record.status:
            status = TR(TH("%s: " % T("Status")),
                        table.status.represent(record.status))
        else:
            status = TR(TH("%s: " % T("Status")),
                        "-")

        interest = task_member_option(record_id = r.id)
        
        rheader = DIV(TABLE(project,
                            TR(TH("%s: " % table.name.label),
                               record.name,
                               ),
                            tags,
                            creator,
                            milestone,
                            status,
                            interest,
                            ), rheader_tabs)

        return rheader

    s3db.set_method("project", "task",
                    method="assign",
                    action=assign_role)
    
    attr["rheader"] = task_rheader
    return attr

settings.customise_project_task_controller = customise_project_task_controller

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

        s3db = current.s3db
        tablename = "pr_person"

        if r.interactive:
            # Set the list fields
            list_fields = ["first_name",
                           "middle_name",
                           "last_name",
                           "human_resource.organisation_id",
                           "address.location_id"
                           ]

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

            s3db.configure(tablename,
                           crud_form = crud_form,
                           list_fields = list_fields
                           )
        return True
    s3.prep = custom_prep

    return attr

settings.customise_pr_person_controller = customise_pr_person_controller

# -----------------------------------------------------------------------------
def task_member_option(record_id, as_div = False):
    """
        returns an option to allow Users to mark themselves as 'Interested' 
        in a Task.

        @param record_id: Task id 
        @param as_div: option will be displayed in a form.
                       default => rheader
    """
    s3 = current.response.s3
    s3db = current.s3db
    auth = current.auth
    response = current.response
    db = current.db
    settings = current.deployment_settings
    scripts = s3.scripts

    scripts.append("/%s/static/themes/%s/js/role.js" % \
                                        (current.request.application,
                                         response.s3.theme))

    s3.js_global.append('''
i18n.assign_role="%s"
i18n.revert_role="%s"''' % (T("Watch"),
                            T("Unwatch")))

    user_role = ""
    btn_label = T("Watch")
    is_disabled = "false"

    create_role = S3AddResourceLink(c="project", f="role",
                                    vars=dict(caller="project_task_role",
                                              child="role_id",
                                              parent="member",
                                              prefix="project"),
                                    label=T("Create Role"),
                                    title=T("Create Role"))
 
    mtable = s3db.project_member
    ltable = s3db.project_task_member
    user_id = auth.s3_logged_in_person()

    interest = TD()
    
    if user_id:

        # Allow Logged in Users to assign themselves
        # a role

        query = (ltable.task_id == record_id) & \
                (mtable.person_id == user_id) & \
                (ltable.member_id == mtable.id)

        row = db(query).select(mtable.role_id).first()
        attr = {}
        
        if row:
            user_role = row.role_id
            # Disable Dropdown with role selected 
            # Revert button
            btn_label = T("Unwatch")
            attr["_disabled"] = ""

        attr["_id"] = "project_task_role"
        btn_class = "btn btn-default"
        if as_div:
            attr["_class"] = "as_div"
            btn_class = btn_class + " as_div"

        # Assign Button
        assign_button = A(btn_label,
                          _id="assign-role",
                          _role="button",
                          _class=btn_class)

        rtable = s3db.project_role
        fields = [rtable.role, rtable.id]
        query = rtable.deleted == False
        roles_display = ""

        if settings.get_project_task_member_roles():
            # Allow Users to select a role
            rows = db(query).select(*fields)
            options = [ OPTION(row.role, _value=row.id) for row in rows ]
        else:

            # Don't display list of roles
            create_role = ""
            roles_display = attr["_style"] = "display:none"
            query &= (rtable.role == "Following")
            row = db(query).select(*fields).first()
            # Select the 'Following' role ( default role )
            user_role = row.id
            options = [ OPTION(row.role, _value=row.id) ]

        _roles = TD(SELECT([OPTION("")] + options,
                           value=user_role,
                           **attr),
                    _style=roles_display)

        if as_div:
            interest = DIV(DIV(B(T("Interested")),
                               _roles,
                               assign_button,
                               P(create_role,
                                 _id="create-new-role"),
                               _id="sub-assign-container"),
                           _id="assign-container")
        else:
            interest = TR(TH(T("Interested")),
                          _roles,
                          assign_button,
                          create_role)
    return interest
    
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
    #("scenario", Storage(
    #        name_nice = T("Scenarios"),
    #        #description = T("Define Scenarios for allocation of appropriate Resources (Human, Assets & Facilities)."),
    #        restricted = True,
    #        module_type = 10,
    #    )),
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
