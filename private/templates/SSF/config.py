# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

T = current.T
settings = current.deployment_settings

"""
    Template settings for SSF
"""

# Pre-Populate
settings.base.prepopulate = ("SSF", "demo/users", "SSF/Test")

# Theme
settings.base.theme = "SSF"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"

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
settings.project.activities = True
# Uncomment this to enable Milestones in tasks
settings.project.milestones = True
# Uncomment this to enable Sectors in projects
settings.project.sectors = True
# Uncomment this to use Projects for Activities & Tasks
settings.project.projects = True
# Uncomment this to enable Hazards in 3W projects
settings.project.hazards = True
# Uncomment this to enable Themes in 3W projects
settings.project.themes = True
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True

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

        if r.interactive:
            is_deployment = False

            stable = s3db.project_sector_project
            otable = s3db.org_sector

            # Viewing details of project_project record
            if r.id:
                # Check if current record is Deployment
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

            from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

            if is_deployment:
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

                # Bring back to the Deployments page if record deleted
                var = {"sector.name": "None,Deployment"}
                delete_next = URL(c="project", f="project", vars=var)

                # Get sector_id for Deployment
                query = (otable.name == "Deployment")
                row = db(query).select(otable.id, limitby=(0, 1)).first()

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
                            fields = [(T("Type"),"name"), "file"],
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
                            fields = [(T("Type"),"name"), "url"],
                            filterby = dict(field = "url",
                                            options = None,
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
                var = {"sector.name": "None,Project"}
                delete_next = URL(c="project", f="project", vars=var)

                # Get sector_id for Project
                query = (otable.name == "Project")
                row = db(query).select(otable.id, limitby=(0, 1)).first()

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

    return attr

settings.customise_project_project_controller = customise_project_project_controller

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
            name_nice = T("Person Registry"),
            #description = T("Central point to record details on People"),
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
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
            module_type = 2,
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
