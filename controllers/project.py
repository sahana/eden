# -*- coding: utf-8 -*-

"""
    Project Tracking & Management
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

mode_task = settings.get_project_mode_task()

# -----------------------------------------------------------------------------
def index():
    """ Module's Custom Home Page """

    return settings.customise_home(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Default module homepage
    """

    if mode_task:
        if settings.get_project_projects():
            # Bypass home page & go directly to task list for a project
            s3_redirect_default(URL(f="project", vars={"tasks":1}))
        else:
            # Bypass home page & go directly to task list
            s3_redirect_default(URL(f="task"))
    else:
        # Bypass home page & go directly to projects list
        s3_redirect_default(URL(f="project"))

# =============================================================================
def create():
    """ Redirect to project/create """
    redirect(URL(f="project", args="create"))

# -----------------------------------------------------------------------------
def project():
    """ RESTful CRUD controller """

    if "tasks" in get_vars:
        # Open-Tasks-For-Project Selector
        return open_tasks_for_project()

    # Pre-process
    def prep(r):

        # Location Filter
        s3db.gis_location_filter(r)

        component = r.component
        component_name = component.name if component else None

        hr_group = r.get_vars.get("group")

        if r.method == "datalist":
            # Set list_fields for renderer (project_project_list_layout)
            s3db.configure("project_project",
                           list_fields = ["name",
                                          "description",
                                          "location.location_id",
                                          "start_date",
                                          "organisation_id",
                                          "organisation_id$logo",
                                          "modified_by",
                                          ]
                           )

        # Filter human resource records if "group" in get_vars
        elif component_name == "human_resource":
            type_field = FS("human_resource.type")
            if hr_group == "staff":
                query = (type_field == 1)
            elif hr_group == "volunteer":
                query = (type_field == 2)
            else:
                query = None
            if query:
                r.resource.add_component_filter("human_resource", query)

        if r.interactive:
            htable = s3db.table("hrm_human_resource")
            if htable:
                htable.person_id.comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Person"),
                                                                 T("Select the person assigned to this role for this project."),
                                                                 )
                                               )

            if not component:
                # Filter Themes based on Sector
                if r.record:
                    table = s3db.project_sector_project
                    query = (table.project_id == r.id) & \
                            (table.deleted == False)
                    rows = db(query).select(table.sector_id)
                    sector_ids = [row.sector_id for row in rows]
                    set_theme_requires(sector_ids)

                if r.method in ("create", "update"):
                    # Context from a Profile page?"
                    location_id = get_vars.get("(location)", None)
                    if location_id:
                        field = s3db.project_location.location_id
                        field.default = location_id
                        field.readable = field.writable = False
                    organisation_id = get_vars.get("(organisation)", None)
                    if organisation_id:
                        field = r.table.organisation_id
                        field.default = organisation_id
                        field.readable = field.writable = False

                elif r.method == "details":
                    # Until we can automate this inside s3profile
                    # - remove the fkey from the list_fields
                    configure = s3db.configure
                    get_config = s3db.get_config
                    define_resource = s3db.resource
                    for tablename in ("project_organisation",
                                      "project_location",
                                      "project_beneficiary",
                                      "project_human_resource_project",
                                      ):
                        s3db.table(tablename)
                        list_fields = get_config(tablename, "list_fields")
                        if not list_fields:
                            list_fields = define_resource(tablename).list_fields()
                        try:
                            list_fields.remove("project_id")
                        except:
                            # Already removed
                            pass
                        configure(tablename, list_fields=list_fields)

                if r.id:
                    r.table.human_resource_id.represent = \
                        s3db.hrm_HumanResourceRepresent(show_link=True)

                elif r.get_vars.get("project.status_id", None):
                    stable = s3db.project_status
                    status = get_vars.get("project.status_id")
                    row = db(stable.name == status).select(stable.id,
                                                           limitby=(0, 1)).first()
                    if row:
                        r.table.status_id.default = row.id
                        r.table.status_id.writable = False

            elif component_name == "organisation":
                if r.method != "update":
                    allowed_roles = dict(settings.get_project_organisation_roles())
                    if settings.get_template() == "DRRPP":
                        # Partner NS should only come via sync from RMS
                        # @ToDo: Move to Template customise
                        allowed_roles.pop(9, None)

                    lead_role = 1
                    otable = s3db.project_organisation
                    query = (otable.project_id == r.id) & \
                            (otable.role == lead_role) & \
                            (otable.deleted != True)
                    row = db(query).select(otable.id,
                                           limitby=(0, 1)).first()
                    if row:
                        # Project has already a lead organisation
                        # => exclude lead_role in component add-form
                        allowed_roles.pop(lead_role, None)
                    otable.role.requires = IS_EMPTY_OR(IS_IN_SET(allowed_roles))

            elif component_name == "activity":
                # Filter Activity Types/Themes based on Sector
                table = s3db.project_sector_project
                query = (table.project_id == r.id) & \
                        (table.deleted == False)
                rows = db(query).select(table.sector_id)
                sector_ids = [row.sector_id for row in rows]
                set_activity_type_requires("project_activity_activity_type", sector_ids)
                set_theme_requires(sector_ids)

            elif component_name == "goal":
                # Not working for embedded create form
                #if r.method == "create":
                if r.method != "update":
                    ctable = r.component.table
                    field = ctable.weighting
                    field.readable = field.writable = False
                    ctable.current_status_by_indicators.readable = False
                    ctable.overall_status_by_indicators.readable = False
                    ctable.actual_progress_by_activities.readable = False
                    ctable.planned_progress_by_activities.readable = False

            elif component_name == "outcome":
                ctable = r.component.table
                if r.method != "update":
                    field = ctable.weighting
                    field.readable = field.writable = False
                    ctable.current_status_by_indicators.readable = False
                    ctable.overall_status_by_indicators.readable = False
                    ctable.actual_progress_by_activities.readable = False
                    ctable.planned_progress_by_activities.readable = False
                if settings.get_project_goals():
                    # Filter to just those for this Project & make mandatory
                    ctable.goal_id.requires = IS_ONE_OF(db, "project_goal.id",
                                                        s3db.project_goal_represent,
                                                        sort=True,
                                                        filterby="project_id",
                                                        filter_opts=[r.id],
                                                        )

            elif component_name == "output":
                ctable = r.component.table
                if r.method != "update":
                    field = ctable.weighting
                    field.readable = field.writable = False
                    ctable.current_status_by_indicators.readable = False
                    ctable.overall_status_by_indicators.readable = False
                    ctable.actual_progress_by_activities.readable = False
                    ctable.planned_progress_by_activities.readable = False
                if settings.get_project_outcomes():
                    # Filter to just those for this Project & make mandatory
                    ctable.outcome_id.requires = IS_ONE_OF(db, "project_outcome.id",
                                                           s3db.project_outcome_represent,
                                                           sort=True,
                                                           filterby="project_id",
                                                           filter_opts=[r.id],
                                                           )
                elif settings.get_project_goals():
                    # Filter to just those for this Project & make mandatory
                    ctable.goal_id.requires = IS_ONE_OF(db, "project_goal.id",
                                                        s3db.project_goal_represent,
                                                        sort=True,
                                                        filterby="project_id",
                                                        filter_opts=[r.id],
                                                        )

            elif component_name == "indicator":
                ctable = r.component.table
                if r.method != "update":
                    field = ctable.weighting
                    field.readable = field.writable = False
                    ctable.current_status_by_indicators.readable = False
                    ctable.overall_status_by_indicators.readable = False
                    ctable.actual_progress_by_activities.readable = False
                    ctable.planned_progress_by_activities.readable = False
                if settings.get_project_outputs():
                    # Filter to just those for this Project & make mandatory
                    ctable.output_id.requires = IS_ONE_OF(db, "project_output.id",
                                                          s3db.project_output_represent,
                                                          sort=True,
                                                          filterby="project_id",
                                                          filter_opts=[r.id],
                                                          )
                elif settings.get_project_outcomes():
                    # Filter to just those for this Project & make mandatory
                    ctable.outcome_id.requires = IS_ONE_OF(db, "project_outcome.id",
                                                           s3db.project_outcome_represent,
                                                           sort=True,
                                                           filterby="project_id",
                                                           filter_opts=[r.id],
                                                           )
                elif settings.get_project_goals():
                    # Filter to just those for this Project & make mandatory
                    ctable.goal_id.requires = IS_ONE_OF(db, "project_goal.id",
                                                        s3db.project_goal_represent,
                                                        sort=True,
                                                        filterby="project_id",
                                                        filter_opts=[r.id],
                                                        )

            elif component_name == "indicator_data":
                ctable = r.component.table
                # Filter to just those for this Project & make mandatory
                ctable.indicator_id.requires = IS_ONE_OF(db, "project_indicator.id",
                                                         s3db.project_indicator_represent,
                                                         sort=True,
                                                         filterby="project_id",
                                                         filter_opts=[r.id],
                                                         )
                # @ToDo: end_date cannot be before Project Start
                #ctable.end_date.requires =

                # Have a filter for indicator in indicator data report
                #if r.method == "report":
                #    from s3 import S3OptionsFilter
                #    filter_widgets = [S3OptionsFilter("indicator_id",
                #                                      label = T("Indicator"),
                #                                      ),
                #                      ]
                #else:
                #    filter_widgets = None
                #r.component.configure(filter_widgets = filter_widgets)

            elif component_name == "indicator_criteria":
                # Filter to just those for this Project & make mandatory
                ctable = r.component.table
                ctable.indicator_id.requires = IS_ONE_OF(db, "project_indicator.id",
                                                         s3db.project_indicator_represent,
                                                         sort=True,
                                                         filterby="project_id",
                                                         filter_opts=[r.id],
                                                         )

            elif component_name == "indicator_activity":
                s3db.project_activity.name.requires = IS_NOT_EMPTY()
                ctable = r.component.table
                if r.method != "update":
                    field = ctable.weighting
                    field.readable = field.writable = False
                # Filter to just those for this Project & make mandatory
                ctable.indicator_id.requires = IS_ONE_OF(db, "project_indicator.id",
                                                        s3db.project_indicator_represent,
                                                        sort=True,
                                                        filterby="project_id",
                                                        filter_opts=[r.id],
                                                        )

            elif component_name == "activity_data":
                ctable = r.component.table
                # Filter to just those for this Project
                ctable.indicator_activity_id.requires = IS_ONE_OF(db, "project_indicator_activity.id",
                                                                  s3db.project_indicator_activity_represent,
                                                                  sort=True,
                                                                  filterby="project_id",
                                                                  filter_opts=[r.id],
                                                                  )

            elif component_name == "task":
                if not auth.s3_has_role("STAFF"):
                    # Hide fields which are meant for staff members
                    # (avoid confusion both of inputters & recipients)
                    unwanted_fields = ["source",
                                       "pe_id",
                                       "date_due",
                                       "time_estimated",
                                       "time_actual",
                                       "status",
                                       ]
                    ttable = component.table
                    for fieldname in unwanted_fields:
                        field = ttable[fieldname]
                        field.readable = field.writable = False

                if "open" in r.get_vars:
                    # Show only the Open Tasks for this Project (unused?)
                    statuses = s3.project_task_active_statuses
                    query = FS("status").belongs(statuses)
                    r.resource.add_component_filter("task", query)

                # Filter activities and milestones to the current project
                options_filter = {"filterby": "project_id",
                                  "filter_opts": (r.id,),
                                  }
                fields = []
                if settings.get_project_activities():
                    fields.append(s3db.project_task_activity.activity_id)
                if settings.get_project_milestones():
                    fields.append(s3db.project_task_milestone.milestone_id)
                for f in fields:
                    requires = f.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        requires = requires.other
                    if hasattr(requires, "set_filter"):
                        requires.set_filter(**options_filter)

            elif component_name == "beneficiary":
                # Filter the location selector to the project's locations
                component.table.project_location_id.requires = \
                    IS_EMPTY_OR(IS_ONE_OF(db, "project_location.id",
                                          s3db.project_location_represent,
                                          sort=True,
                                          filterby="project_id",
                                          filter_opts=[r.id],
                                          )
                                )

            elif component_name in ("human_resource", "human_resource_project"):

                htable = s3db.hrm_human_resource
                htable.person_id.represent = \
                    s3db.pr_PersonRepresent(show_link=True)

                # These values are defined in hrm_type_opts
                human_resource_id = r.table.human_resource_id
                filter_opts = None
                if hr_group:
                    crud_strings = s3.crud_strings
                    if hr_group == "staff":
                        filter_opts = (1,)
                        human_resource_id.label = T("Staff")
                        crud_strings["project_human_resource_project"] = crud_strings["hrm_staff"]

                    elif hr_group == "volunteer":
                        filter_opts = (2,)
                        human_resource_id.label = T("Volunteer")
                        crud_strings["project_human_resource_project"] = crud_strings["hrm_volunteer"]

                if filter_opts:
                    # Use the group to filter the form widget when
                    # adding a new record
                    human_resource_id.requires = \
                        IS_ONE_OF(db, "hrm_human_resource.id",
                                  s3db.hrm_human_resource_represent,
                                  filterby="type",
                                  filter_opts=filter_opts,
                                  orderby="hrm_human_resource.person_id",
                                  sort=True
                        )

                # @ToDo:
                #if settings.has_module("budget"):
                #    from s3 import S3SQLCustomForm, S3SQLInlineComponent
                #    field = s3db.budget_allocation.budget_entity_id
                #    field.readable = field.writable = True
                #    field.requires = S3Represent(lookup="budget_budget", key="budget_entity_id")
                #    field.requires = IS_ONE_OF()
                #
                #    crud_form = S3SQLCustomForm("project_id",
                #                                "human_resource_id",
                #                                "status",
                #                                S3SQLInlineComponent("allocation",
                #                                                     label = T("Budget"),
                #                                                     fields = ["budget_entity_id",
                #                                                               "start_date",
                #                                                               "end_date",
                #                                                               "daily_cost",
                #                                                               ],
                #                                                     ),
                #                                )
                #    s3db.configure("project_human_resoruce_project",
                #                   crud_form = crud_form,
                #                   list_fields = [#"project_id", # Not being dropped in component view
                #                                  "human_resource_id",
                #                                  "status",
                #                                  "allocation.budget_entity_id",
                #                                  "allocation.start_date",
                #                                  "allocation.end_date",
                #                                  "allocation.daily_cost",
                #                                  ],

            elif component_name == "document":
                # Hide unnecessary fields
                dtable = component.table
                dtable.organisation_id.readable = \
                dtable.organisation_id.writable = False
                dtable.person_id.readable = \
                dtable.person_id.writable = False
                dtable.location_id.readable = \
                dtable.location_id.writable = False

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:

            component_name = r.component_name
            if not r.component:
                if mode_task:
                    read_url = URL(args=["[id]", "task"])
                    update_url = URL(args=["[id]", "task"])
                    s3_action_buttons(r,
                                      read_url=read_url,
                                      update_url=update_url)

            #elif component_name == "indicator":
            #    # Open should open the profile page
            #    read_url = URL(f="indicator",
            #                   args=["[id]", "profile"])
            #    update_url = URL(f="indicator",
            #                     args=["[id]", "profile"])
            #    s3_action_buttons(r,
            #                      read_url=read_url,
            #                      update_url=update_url)

            elif component_name == "task" and r.component_id:
                # Put Comments in rfooter
                s3db.project_ckeditor()
                s3.rfooter = LOAD("project", "comments.load",
                                  args=[r.component_id],
                                  ajax=True)

        return output
    s3.postp = postp

    return s3_rest_controller(module, "project",
                              csv_template = "project",
                              hide_filter = {None: False,
                                             #"indicator_data": False,
                                             "_default": True,
                                             },
                              rheader = s3db.project_rheader,
                              )

# -----------------------------------------------------------------------------
def open_tasks_for_project():
    """
        Simplified controller to select a project and open the
        list of open tasks for it
    """

    def prep(r):
        tablename = "project_project"
        s3.crud_strings[tablename].title_list = T("Open Tasks for Project")
        s3.crud_labels.READ = s3.crud_labels.UPDATE = T("Select")
        s3db.configure(tablename,
                       deletable=False,
                       listadd=False,
                      )
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive and not r.component:
            tasklist_url = URL(f="task", vars={"project":"[id]"})
            s3_action_buttons(r,
                              deletable=False,
                              read_url=tasklist_url,
                              update_url=tasklist_url)
        return output
    s3.postp = postp

    return s3_rest_controller(module, "project",
                              hide_filter = False,
                              )

# -----------------------------------------------------------------------------
def set_theme_requires(sector_ids):
    """
        Filters the theme_id based on the sector_id
    """

    ttable = s3db.project_theme
    tstable = s3db.project_theme_sector

    # All themes linked to the project's sectors or to no sectors
    rows = db().select(ttable.id,
                       tstable.sector_id,
                       left=tstable.on(ttable.id == tstable.theme_id))
    sector_ids = sector_ids or []
    theme_ids = [row.project_theme.id for row in rows
                 if not row.project_theme_sector.sector_id or
                    row.project_theme_sector.sector_id in sector_ids]

    table = s3db.project_theme_project
    field = table.theme_id
    field.requires = IS_EMPTY_OR(IS_ONE_OF(db, "project_theme.id",
                                           field.represent,
                                           filterby="id",
                                           filter_opts=theme_ids,
                                           sort=True,
                                           )
                                 )

# -----------------------------------------------------------------------------
def set_activity_type_requires(tablename, sector_ids):
    """
        Filters the activity_type_id based on the sector_id
    """

    attable = s3db.project_activity_type
    if sector_ids:
        atstable = s3db.project_activity_type_sector

        # All activity_types linked to the projects sectors or to no sectors
        rows = db().select(attable.id,
                           atstable.sector_id,
                           left=atstable.on(attable.id == atstable.activity_type_id))
        activity_type_ids = [row.project_activity_type.id for row in rows
                     if not row.project_activity_type_sector.sector_id or
                        row.project_activity_type_sector.sector_id in sector_ids]
    else:
        activity_type_ids = []
    s3db[tablename].activity_type_id.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db, "project_activity_type.id",
                                              s3base.S3Represent(lookup="project_activity_type"),
                                              filterby="id",
                                              filter_opts=activity_type_ids,
                                              sort=True,
                                              )
                                    )

# =============================================================================
def sector():
    """ RESTful CRUD controller """

    return s3_rest_controller("org", "sector")

# -----------------------------------------------------------------------------
def status():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def theme():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def theme_project():
    """
        RESTful CRUD controller
        - not normally exposed to users via a menu
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def theme_sector():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def hazard():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def framework():
    """ RESTful CRUD controller """

    return s3_rest_controller(dtargs = {"dt_text_maximum_len": 160},
                              hide_filter = True,
                              )

# =============================================================================
def organisation():
    """ RESTful CRUD controller """

    if settings.get_project_multiple_organisations():
        # e.g. IFRC
        s3db.configure("project_organisation",
                       deletable = False,
                       editable = False,
                       insertable = False,
                       )

        #list_btn = A(T("Funding Report"),
        #             _href=URL(c="project", f="organisation",
        #                      args="report", vars=get_vars),
        #             _class="action-btn")

        return s3_rest_controller(#list_btn=list_btn,
                                  )

    else:
        # e.g. DRRPP
        tabs = [(T("Basic Details"), None),
                (T("Projects"), "project"),
                (T("Contacts"), "human_resource"),
                ]
        rheader = lambda r: s3db.org_rheader(r, tabs)
        return s3_rest_controller("org", resourcename,
                                  rheader = rheader,
                                  )

# =============================================================================
def beneficiary_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def beneficiary():
    """ RESTful CRUD controller """

    # Normally only used in Report
    # - make changes as component of Project
    s3db.configure("project_beneficiary",
                   deletable = False,
                   editable = False,
                   insertable = False,
                   )

    list_btn = A(T("Beneficiary Report"),
                 _href=URL(c="project", f="beneficiary",
                           args="report", vars=get_vars),
                 _class="action-btn")

    #def prep(r):
    #    if r.method in ("create", "create.popup", "update", "update.popup"):
    #        # Coming from Profile page?
    #        location_id = r.get_vars.get("~.(location)", None)
    #        if location_id:
    #            field = r.table.location_id
    #            field.default = location_id
    #            field.readable = field.writable = False
    #    if r.record:
    #        field = r.table.location_id
    #        field.comment = None
    #        field.writable = False
    #    return True
    #s3.prep = prep

    return s3_rest_controller(hide_filter = False,
                              )

# =============================================================================
def activity_type():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity_type_sector():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def activity_organisation():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller(module, "activity_organisation")

# -----------------------------------------------------------------------------
def activity():
    """ RESTful CRUD controller """

    table = s3db.project_activity

    if "project_id" in get_vars:
        field = table.project_id
        field.default = get_vars.project_id
        field.writable = False
        field.comment = None

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.component is not None:
                component_name = r.component_name
                if component_name == "distribution":
                    dtable = s3db.supply_distribution
                    f = dtable.location_id
                    f.default = r.record.location_id
                    f.readable = f.writable = False
                    f = dtable.date
                    f.default = r.record.date
                    f.readable = f.writable = False
                elif component_name == "document":
                    dtable = s3db.doc_document
                    dtable.organisation_id.readable = dtable.organisation_id.writable = False
                    dtable.person_id.readable = dtable.person_id.writable = False
                    f = dtable.location_id
                    f.default = r.record.location_id
                    f.readable = f.writable = False
                    s3db.configure("doc_document",
                                   list_fields = ["name",
                                                  "date",
                                                  ],
                                   )
        return True
    s3.prep = prep

    return s3_rest_controller("project", "activity",
                              csv_template = "activity",
                              #hide_filter = False,
                              rheader = s3db.project_rheader,
                              )

# -----------------------------------------------------------------------------
def distribution():
    """ Activities which include Distributions """

    # Load model
    table = s3db.project_activity

    # CRUD strings
    s3.crud_strings["project_activity"] = Storage(
        label_create = T("Create Distribution"),
        title_display = T("Distribution Details"),
        title_list = T("Distributions"),
        title_update = T("Edit Distribution"),
        title_report = T("Distribution Report"),
        label_list_button = T("List Distributions"),
        msg_record_created = T("Distribution Added"),
        msg_record_modified = T("Distribution Updated"),
        msg_record_deleted = T("Distribution Deleted"),
        msg_list_empty = T("No Distributions Found")
    )

    return activity()

# -----------------------------------------------------------------------------
def location():
    """ RESTful CRUD controller """

    table = s3db.project_location

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.record:
                table = s3db.project_sector_project
                query = (table.project_id == r.record.project_id) & \
                        (table.deleted == False)
                rows = db(query).select(table.sector_id)
                sector_ids = [row.sector_id for row in rows]
            else:
                sector_ids = []
            set_activity_type_requires("project_activity_type_location", sector_ids)

            if r.component_name == "document":
                table = db.doc_document
                table.organisation_id.readable = table.organisation_id.writable = False
                table.person_id.readable = table.person_id.writable = False
                table.location_id.readable = table.location_id.writable = False

        return True
    s3.prep = prep

    # Pre-process
    def postp(r, output):
        if r.representation == "plain":
            # Replace the Map Popup contents with custom content
            item = TABLE()
            if settings.get_project_community():
                # The Community is the primary resource
                record = r.record
                table.id.readable = False
                table.location_id.readable = False
                fields = [table[f] for f in table.fields if table[f].readable]
                for field in fields:
                    data = record[field]
                    if data:
                        represent = field.represent
                        if represent:
                            item.append(TR(TD(field.label),
                                           TD(represent(data))))
                        else:
                            item.append(TR(TD(field.label), TD(data)))
                hierarchy = gis.get_location_hierarchy()
                gtable = s3db.gis_location
                location = db(gtable.id == record.location_id).select(gtable.L1,
                                                                      gtable.L2,
                                                                      gtable.L3,
                                                                      gtable.L4,
                                                                      ).first()
                if location:
                    for field in ["L4", "L3", "L2", "L1"]:
                        if field in hierarchy and location[field]:
                            item.append(TR(TD(hierarchy[field]),
                                           TD(location[field])))
                output["item"] = item
            else:
                # The Project is the primary resource
                project_id = r.record.project_id
                ptable = s3db.project_project
                query = (ptable.id == project_id)
                project = db(query).select(limitby=(0, 1)).first()
                ptable.id.readable = False
                fields = [ptable[f] for f in ptable.fields if ptable[f].readable]
                for field in fields:
                    if field == "currency":
                        # Don't display Currency if no Budget
                        if not project["budget"]:
                            continue
                    data = project[field]
                    if data:
                        represent = field.represent
                        if represent:
                            item.append(TR(TD(field.label),
                                           TD(represent(data))))
                        else:
                            item.append(TR(TD(field.label), TD(data)))
                title = s3.crud_strings["project_project"].title_display
                # Assume authorised to see details
                popup_url = URL(f="project", args=[project_id])
                details_btn = A(T("Open"),
                                _href=popup_url,
                                _class="btn",
                                _id="details-btn",
                                _target="_blank")
                output = dict(item = item,
                              title = title,
                              details_btn = details_btn,
                              )
        return output
    s3.postp = postp

    return s3_rest_controller(interactive_report = True,
                              csv_template = "location",
                              hide_filter = False,
                              rheader = s3db.project_rheader,
                              )

# -----------------------------------------------------------------------------
def demographic():
    """ RESTful CRUD controller """

    return s3_rest_controller("stats", "demographic")

# -----------------------------------------------------------------------------
def demographic_data():
    """ RESTful CRUD controller """

    return s3db.stats_demographic_data_controller()

# -----------------------------------------------------------------------------
def location_contact():
    """ RESTful CRUD controller for Community Contacts """

    return s3_rest_controller(hide_filter = False,
                              )

# -----------------------------------------------------------------------------
def report():
    """
        RESTful CRUD controller

        @ToDo: Why is this needed? To have no rheader?
    """

    return s3_rest_controller(module, "activity")

# -----------------------------------------------------------------------------
def partners():
    """
        RESTful CRUD controller for Organisations filtered by Type
    """

    # @ToDo: This could need to be a deployment setting
    get_vars["organisation_type.name"] = \
        "Academic,Bilateral,Government,Intergovernmental,NGO,UN agency"

    # Load model
    table = s3db.org_organisation

    # Type is Mandatory (otherwise they can disappear from view)
    # @ToDo: How to achieve this in an S3SQLInlineLink?

    # Modify CRUD Strings
    s3.crud_strings.org_organisation = Storage(
        label_create = T("Create Partner Organization"),
        title_display = T("Partner Organization Details"),
        title_list = T("Partner Organizations"),
        title_update = T("Edit Partner Organization"),
        title_upload = T("Import Partner Organizations"),
        label_list_button = T("List Partner Organizations"),
        label_delete_button = T("Delete Partner Organization"),
        msg_record_created = T("Partner Organization added"),
        msg_record_modified = T("Partner Organization updated"),
        msg_record_deleted = T("Partner Organization deleted"),
        msg_list_empty = T("No Partner Organizations currently registered")
        )

    return s3db.org_organisation_controller()

# =============================================================================
def task():
    """ RESTful CRUD controller """

    return s3db.project_task_controller()

# =============================================================================
def task_project():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def task_activity():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def task_milestone():
    """ RESTful CRUD controller for options.s3json lookups """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def task_tag():
    """ RESTful CRUD controller for options.s3json lookups """

    # Pre-process
    def prep(r):
        if r.method != "options" or r.representation != "s3json":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def role():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
def member():
    """ RESTful CRUD Controller """

    return s3_rest_controller()

# =============================================================================
def milestone():
    """ RESTful CRUD controller """

    if "project_id" in get_vars:
        field = s3db.project_milestone.project_id
        field.default = get_vars.project_id
        field.writable = False
        field.comment = None

    return s3_rest_controller()

# =============================================================================
def tag():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
def time():
    """ RESTful CRUD controller """

    # Load model to get normal CRUD strings
    table = s3db.project_time
    hide_filter = False
    if "mine" in get_vars:
        # Display this user's Logged Hours in reverse-order
        hide_filter = True
        s3.crud_strings["project_time"].title_list = T("My Logged Hours")
        person_id = auth.s3_logged_in_person()
        if person_id:
            # @ToDo: Use URL filter instead, but the Search page will have
            # to populate it's widgets based on the URL filter
            s3.filter = (table.person_id == person_id)
            # Log time with just this user's open tasks visible
            ttable = db.project_task
            query = (ttable.pe_id == auth.user.pe_id) & \
                    (ttable.deleted == False)
            if "update" not in request.args:
                # Only log time against Open Tasks
                query &= (ttable.status.belongs(s3db.project_task_active_statuses))
            dbset = db(query)
            table.task_id.requires = IS_ONE_OF(dbset, "project_task.id",
                                               s3db.project_task_represent_w_project
                                               )
        list_fields = ["id",
                       "date",
                       "hours",
                       (T("Project"), "task_id$task_project.project_id"),
                       (T("Activity"), "task_id$task_activity.activity_id"),
                       "task_id",
                       "comments",
                       ]
        if settings.get_project_milestones():
            # Use the field in this format to get the custom represent
            list_fields.insert(5, (T("Milestone"), "task_id$task_milestone.milestone_id"))

        s3db.configure("project_time",
                       list_fields = list_fields,
                       orderby = "project_time.date desc",
                       )

    elif "week" in get_vars:
        # Filter to the specified number of weeks
        weeks = int(get_vars.get("week", 1))
        now = request.utcnow
        week = datetime.timedelta(days=7)
        delta = week * weeks
        s3.filter = (table.date > (now - delta))

    elif "month" in get_vars:
        # Filter to the specified number of months
        months = int(get_vars.get("month", 1))
        now = request.utcnow
        month = datetime.timedelta(weeks=4)
        delta = month * months
        s3.filter = (table.date > (now - delta))

    return s3_rest_controller(hide_filter = hide_filter,
                              )

# =============================================================================
# Programmes
# =============================================================================
def programme():
    """ RESTful controller for Programmes """

    return s3_rest_controller()

def programme_project():
    """ RESTful controller for Programmes <> Projects """

    s3.prep = lambda r: r.method == "options" and r.representation == "s3json"

    return s3_rest_controller()

# =============================================================================
def strategy():
    """ RESTful controller for Strategies """

    return s3_rest_controller()

# =============================================================================
# Planning
# =============================================================================
def goal():
    """ RESTful controller for Goals """

    return s3_rest_controller()

def outcome():
    """ RESTful controller for Outcomes """

    return s3_rest_controller()

def output():
    """ RESTful controller for Outputs """

    return s3_rest_controller()

def indicator():
    """ RESTful CRUD controller """

    def prep(r):
        if r.method == "profile":
            # @ToDo: Needs Edit button
            table = r.table
            record = r.record
            code = record.code
            def dt_row_actions(component):
                return lambda r, list_id: [
                    {"label": T("Open"),
                     "url": r.url(component=component,
                                  component_id="[id]",
                                  method="update.popup",
                                  vars={"refresh": list_id}),
                     "_class": "action-btn edit s3_modal",
                     },
                    {"label": T("Delete"),
                     "_ajaxurl": r.url(component=component,
                                       component_id="[id]",
                                       method="delete.json",
                                       ),
                     "_class": "action-btn delete-btn-ajax dt-ajax-delete",
                     },
                ]

            data_widget = dict(label = "Data",
                               label_create = "Add Data",
                               type = "datatable",
                               actions = dt_row_actions("indicator_data"),
                               tablename = "project_indicator_data",
                               filter = FS("indicator_id") == record.id,
                               create_controller = "project",
                               create_function = "indicator",
                               create_component = "indicator_data",
                               #icon = "book",
                               )
            profile_widgets = [data_widget,
                               ]
            s3db.configure("project_indicator",
                           profile_cols = 1,
                           profile_header = DIV(H2(code),
                                                H3(table.name.label),
                                                P(record.name),
                                                H3(table.verification.label),
                                                P(record.verification),
                                                _class="profile-header",
                                                ),
                           profile_title = "%s : %s" % (s3_unicode(s3.crud_strings["project_indicator"].title_display),
                                                        code),
                           profile_widgets = profile_widgets,
                           )
            s3db.configure("project_indicator_data",
                           list_fields = ["name",
                                          "end_date",
                                          "target_value",
                                          "value",
                                          (T("Percentage"), "percentage"),
                                          "comments",
                                          ],
                           )
            s3.rfooter = A(T("Return to Project"),
                           _href=URL(f="project",
                                     args=[record.project_id, "indicator"]),
                           _class = "action-btn"
                           )

        elif r.component_name == "indicator_data":
            field = s3db.project_indicator_data.project_id
            field.default = r.record.project_id
            field.readable = field.writable = False

        return True
    s3.prep = prep

    return s3_rest_controller()

def indicator_data():
    """ RESTful CRUD controller """

    return s3_rest_controller()

def person():
    """ RESTful controller for Community Volunteers """

    # @ToDo: Filter

    return s3db.vol_person_controller()

def volunteer():
    """ RESTful controller for Community Volunteers """

    # @ToDo: Filter
    #s3.filter = FS("type") == 2

    return s3db.vol_volunteer_controller()

# -----------------------------------------------------------------------------
def window():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
# Comments
# =============================================================================
def comment_parse(comment, comments, task_id=None):
    """
        Parse a Comment

        @param: comment - a gluon.sql.Row: the current comment
        @param: comments - a gluon.sql.Rows: full list of comments
        @param: task_id - a reference ID: optional task commented on
    """

    author = B(T("Anonymous"))
    if comment.created_by:
        utable = s3db.auth_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (utable.id == comment.created_by)
        left = [ltable.on(ltable.user_id == utable.id),
                ptable.on(ptable.pe_id == ltable.pe_id)]
        row = db(query).select(utable.email,
                               ptable.first_name,
                               ptable.middle_name,
                               ptable.last_name,
                               left=left, limitby=(0, 1)).first()
        if row:
            person = row.pr_person
            user = row[utable._tablename]
            username = s3_fullname(person)
            email = user.email.strip().lower().encode("utf-8")
            import hashlib
            hash = hashlib.md5(email).hexdigest()
            url = "http://www.gravatar.com/%s" % hash
            author = B(A(username, _href=url, _target="top"))
    if not task_id and comment.task_id:
        table = s3db.project_task
        task = "re: %s" % table[comment.task_id].name
        header = DIV(author, " ", task)
        task_id = comment.task_id
    else:
        header = author
    thread = LI(DIV(s3base.s3_avatar_represent(comment.created_by),
                    DIV(DIV(header,
                            _class="comment-header"),
                        DIV(XML(comment.body),
                            _class="comment-body"),
                        _class="comment-text"),
                        DIV(DIV(comment.created_on,
                                _class="comment-date"),
                            DIV(A(T("Reply"),
                                  _class="action-btn"),
                                _onclick="comment_reply(%i);" % comment.id,
                                _class="comment-reply"),
                            _class="fright"),
                    _id="comment-%i" % comment.id,
                    _task_id=task_id,
                    _class="comment-box"))

    # Add the children of this thread
    children = UL(_class="children")
    id = comment.id
    count = 0
    for comment in comments:
        if comment.parent == id:
            count = 1
            child = comment_parse(comment, comments, task_id=task_id)
            children.append(child)
    if count == 1:
        thread.append(children)

    return thread

# -----------------------------------------------------------------------------
def comments():
    """ Function accessed by AJAX from rfooter to handle Comments """

    try:
        task_id = request.args[0]
    except:
        raise HTTP(400)

    table = s3db.project_comment
    field = table.task_id
    field.default = task_id
    field.writable = field.readable = False

    # Create S3Request for S3SQLForm
    r = s3_request(prefix = "project",
                   name = "comment",
                   # Override task_id
                   args = [],
                   vars = None,
                   # Override .loads
                   extension = "html",
                   )

    # Customise resource
    r.customise_resource()

    # Form to add a new Comment
    form = s3base.S3SQLCustomForm("parent", "task_id", "body")(r)

    # List of existing Comments
    comments = db(field == task_id).select(table.id,
                                           table.parent,
                                           table.body,
                                           table.created_by,
                                           table.created_on,
                                           )

    output = UL(_id="comments")
    for comment in comments:
        if not comment.parent:
            # Show top-level threads at top-level
            thread = comment_parse(comment, comments, task_id=task_id)
            output.append(thread)

    script = "".join((
'''$('#comments').collapsible({xoffset:'-5',yoffset:'50',imagehide:img_path+'arrow-down.png',imageshow:img_path+'arrow-right.png',defaulthide:false})
$('#project_comment_parent__row1').hide()
$('#project_comment_parent__row').hide()
$('#project_comment_body').ckeditor(ck_config)
$('#submit_record__row input').click(function(){
 $('#comment-form').hide()
 $('#project_comment_body').ckeditorGet().destroy()
 return true
})'''))

    # No layout in this output!
    #s3.jquery_ready.append(script)

    output = DIV(output,
                 DIV(H4(T("New Comment"),
                        _id="comment-title"),
                     form,
                     _id="comment-form",
                     _class="clear"),
                 SCRIPT(script))

    return XML(output)

def comment():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# =============================================================================
# Campaigns
# =============================================================================
def campaign():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def campaign_keyword():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def campaign_message():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def campaign_response():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def campaign_response_summary():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def human_resource_project():
    """
        REST controller for options.s3json lookups
    """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller()

# END =========================================================================
