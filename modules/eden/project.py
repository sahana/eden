# -*- coding: utf-8 -*-

""" Sahana Eden Project Model

    @copyright: 2011-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3ProjectModel",
           "S3Project3WModel",
           "S3ProjectActivityModel",
           "S3ProjectAnnualBudgetModel",
           "S3ProjectFrameworkModel",
           "S3ProjectThemeModel",
           "S3ProjectTaskModel",
           "S3ProjectTaskHRMModel",
           "S3ProjectTaskIReportModel",
           "project_location_represent",
           "project_rheader",
           "project_task_controller",
           ]

import datetime

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from gluon.sqlhtml import CheckboxesWidget
from gluon.contrib.simplejson.ordered_dict import OrderedDict

from ..s3 import *
from layouts import S3AddResourceLink

# =============================================================================
class S3ProjectModel(S3Model):
    """
        Project Model

        Note: This module can be extended by 2 different modes:
         - '3w':   "Who's doing What Where"
                    suitable for use by multinational organisations tracking
                    projects at a high level
            - sub-mode 'drr':   Disaster Risk Reduction extensions
         - 'task':  Suitable for use by a smaller organsiation tracking tasks
                    within projects

        Theer are also a number of other deployment_settings to control behaviour

        This class contains the tables common to both uses
        There are additional tables in S3Project3WModel and S3ProjectTaskModel
        for the other 2 use cases
        There are also additional Classes for optional Link Tables
    """

    names = ["project_theme",
             "project_theme_id",
             "project_hazard",
             "project_hfa_opts",
             "project_project",
             "project_activity_type",
             "project_project_id",
             "project_multi_activity_type_id",
             ]

    def model(self):

        T = current.T
        db = current.db

        location_id = self.gis_location_id
        countries_id = self.gis_countries_id
        organisation_id = self.org_organisation_id
        sector_id = self.org_sector_id
        human_resource_id = self.hrm_human_resource_id

        NONE = current.messages.NONE

        settings = current.deployment_settings
        mode_3w = settings.get_project_mode_3w()
        mode_task = settings.get_project_mode_task()
        mode_drr = settings.get_project_mode_drr()
        use_codes = settings.get_project_codes()
        use_sectors = settings.get_project_sectors()
        multi_budgets = settings.get_project_multiple_budgets()
        multi_orgs = settings.get_project_multiple_organisations()
        theme_percentages = settings.get_project_theme_percentages()

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Theme
        # @ToDo: Move to S3ProjectThemeModel once direct link removed
        #        - which needs an embedded widget UI
        #
        tablename = "project_theme"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True, unique=True),
                             s3_comments(),
                             format = "%(name)s",
                             *s3_meta_fields())

        # Field configuration?

        # CRUD Strings?

        # Search Method?

        # Resource Configuration?

        # Reusable Fields
        # Single for theme_percentages=True
        theme_id = S3ReusableField("theme_id", table,
                                   label = T("Theme"),
                                   sortby = "name",
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "project_theme.id",
                                                          self.project_theme_represent,
                                                          sort=True)),
                                   represent = self.project_theme_represent,
                                   ondelete = "RESTRICT")

        # Multiple for theme_percentages=False
        multi_theme_id = S3ReusableField("multi_theme_id",
                                         "list:reference project_theme",
                                         label = T("Themes"),
                                         sortby = "name",
                                         requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "project_theme.id",
                                                                  self.project_theme_represent,
                                                                  sort=True,
                                                                  multiple=True)),
                                         represent = lambda opt, row=None: \
                                            multiref_represent(opt, "project_theme"),
                                         ondelete = "RESTRICT",
                                         widget = lambda f, v: \
                                            CheckboxesWidgetS3.widget(f, v,
                                                                      cols=3)
                                        )

        # Projects
        add_component("project_theme_percentage", project_theme="theme_id")

        # ---------------------------------------------------------------------
        # Hazard
        # @ToDo: Move to link table to move to S3ProjectDRRModel
        #
        tablename = "project_hazard"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True, unique=True),
                             s3_comments(),
                             format="%(name)s",
                             *s3_meta_fields())

        # Field configuration?

        # CRUD Strings?

        # Search Method?

        # Resource Configuration?

        # Reusable Field
        multi_hazard_id = S3ReusableField("multi_hazard_id",
                                          "list:reference project_hazard",
                                          sortby = "name",
                                          label = T("Hazards"),
                                          requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "project_hazard.id",
                                                                  self.project_hazard_represent,
                                                                  sort=True,
                                                                  multiple=True)),
                                          represent = lambda opt, row=None: \
                                            multiref_represent(opt, "project_hazard"),
                                          ondelete = "RESTRICT",
                                          widget = lambda f, v: \
                                            CheckboxesWidgetS3.widget(f, v,
                                                                      cols=3)
                                          )

        # ---------------------------------------------------------------------
        # Project
        #

        # HFA
        project_hfa_opts = {
            1: T("HFA1: Ensure that disaster risk reduction is a national and a local priority with a strong institutional basis for implementation."),
            2: T("HFA2: Identify, assess and monitor disaster risks and enhance early warning."),
            3: T("HFA3: Use knowledge, innovation and education to build a culture of safety and resilience at all levels."),
            4: T("HFA4: Reduce the underlying risk factors."),
            5: T("HFA5: Strengthen disaster preparedness for effective response at all levels."),
        }

        tablename = "project_project"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             # multi_orgs deployments use the separate project_organisation table
                             organisation_id(
                                          readable=False if multi_orgs else True,
                                          writable=False if multi_orgs else True,
                                        ),
                             Field("name", unique = True,
                                   label = T("Name"),
                                   # Require unique=True if using IS_NOT_ONE_OF like here (same table,
                                   # no filter) in order to allow both automatic indexing (faster)
                                   # and key-based de-duplication (i.e. before field validation)
                                   requires = [IS_NOT_EMPTY(error_message=T("Please fill this!")),
                                               IS_NOT_ONE_OF(db, "project_project.name")]
                                   ),
                             Field("code",
                                   label = T("Code"),
                                   readable = use_codes,
                                   writable = use_codes,
                                   ),
                             Field("description", "text",
                                   label = T("Description")),
                             # NB There is additional client-side validation for start/end date in the Controller
                             s3_date("start_date",
                                     label = T("Start Date")
                                     ),
                             s3_date("end_date",
                                     label = T("End Date")
                                     ),
                             Field("calendar",
                                   label = T("Calendar"),
                                   readable = mode_task,
                                   writable = mode_task,
                                   requires = IS_NULL_OR(IS_URL()),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Calendar"),
                                                                   T("URL to a Google Calendar to display on the project timeline.")))),
                             # multi_budgets deployments handle on the Budgets Tab
                             Field("budget", "double",
                                   readable = False if multi_budgets else True,
                                   writable = False if multi_budgets else True,
                                   label = T("Budget"),
                                   represent = lambda v, row=None: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)),
                             s3_currency(
                                         readable = False if multi_budgets else True,
                                         writable = False if multi_budgets else True,
                                         ),
                             sector_id(
                                       readable = use_sectors,
                                       writable = use_sectors,
                                       widget = lambda f, v: \
                                        CheckboxesWidget.widget(f, v, cols=3)
                                       ),
                             countries_id(
                                          readable = mode_3w,
                                          writable = mode_3w
                                         ),
                             multi_hazard_id(
                                            readable = mode_drr,
                                            writable = mode_drr
                                            ),
                             multi_theme_id(
                                            readable = mode_3w and \
                                                       not theme_percentages,
                                            writable = mode_3w and \
                                                       not theme_percentages,
                                           ),
                             Field("hfa", "list:integer",
                                   label = T("HFA Priorities"),
                                   readable = mode_drr,
                                   writable = mode_drr,
                                   requires = IS_NULL_OR(IS_IN_SET(project_hfa_opts,
                                                                   multiple = True)),
                                   represent = self.hfa_opts_represent,
                                   widget = CheckboxesWidgetS3.widget),
                             Field("objectives", "text",
                                   readable = mode_drr,
                                   writable = mode_drr,
                                   label = T("Objectives")),
                             human_resource_id(label=T("Contact Person")),
                             s3_comments(comment=DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Comments"),
                                                                       T("Outcomes, Impact, Challenges")))),
                             format="%(name)s",
                             *s3_meta_fields())

        # Field configuration?

        # CRUD Strings
        ADD_PROJECT = T("Add Project")
        crud_strings[tablename] = Storage(
            title_create = ADD_PROJECT,
            title_display = T("Project Details"),
            title_list = T("Projects"),
            title_update = T("Edit Project"),
            title_search = T("Search Projects"),
            title_upload = T("Import Project List"),
            subtitle_create = T("Add New Project"),
            subtitle_upload = T("Upload Project List"),
            label_list_button = T("List Projects"),
            label_create_button = ADD_PROJECT,
            label_delete_button = T("Delete Project"),
            msg_record_created = T("Project added"),
            msg_record_modified = T("Project updated"),
            msg_record_deleted = T("Project deleted"),
            msg_list_empty = T("No Projects currently registered"))

        # Search Method

        advanced = [S3SearchSimpleWidget(
                        name = "project_search_text_advanced",
                        label = T("Description"),
                        comment = T("Search for a Project by name, code, or description."),
                        field = ["name",
                                 "code",
                                 "description",
                                ]
                        ),
                    S3SearchOptionsWidget(
                        name = "project_search_country",
                        label = T("Countries"),
                        field = "countries_id",
                    )]
        append = advanced.append

        if use_sectors:
            if settings.get_ui_cluster():
                sector = T("Cluster")
            else:
                sector = T("Sector")
            append(S3SearchOptionsWidget(
                        name = "project_search_sector",
                        label = sector,
                        field = "sector_id",
                        cols = 4
                    ))
        if mode_drr:
            append(S3SearchOptionsWidget(
                        name = "project_search_hazard",
                        label = T("Hazard"),
                        field = "multi_hazard_id",
                        cols = 4
                    ))
        if not theme_percentages:
            append(S3SearchOptionsWidget(
                        name = "project_search_theme",
                        label = T("Theme"),
                        field = "multi_theme_id",
                        cols = 4
                    ))
        if mode_drr:
            append(S3SearchOptionsWidget(
                        name = "project_search_hfa",
                        label = T("HFA"),
                        field = "hfa"
                    ))

        project_search = S3Search(advanced = advanced)

        # Resource Configuration
        if multi_orgs:
            create_next = URL(c="project", f="project",
                              args=["[id]", "organisation"])
        elif theme_percentages:
            create_next = URL(c="project", f="project",
                              args=["[id]", "theme_percentage"])
        elif mode_task:
            create_next = URL(c="project", f="project",
                              args=["[id]", "activity"])
        else:
            create_next = URL(c="project", f="project",
                              args=["[id]"])

        list_fields = ["id"]
        append = list_fields.append
        if use_codes:
            append("code")
        append("name")
        if multi_orgs:
            table.virtualfields.append(S3ProjectOrganisationVirtualFields())
            LEAD_ROLE = settings.get_project_organisation_lead_role()
            append((settings.get_project_organisation_roles()[LEAD_ROLE], "organisation"))
        else:
            append("organisation_id")
        if use_sectors:
            append("sector_id")
        if mode_3w:
            append("countries_id")
        if mode_drr:
            append("multi_hazard_id")
            append("hfa")
        if not theme_percentages:
            append("multi_theme_id")
        if multi_orgs:
            append((T("Total Funding Amount"), "total_organisation_amount"))
        if multi_budgets:
            table.virtualfields.append(S3ProjectBudgetVirtualFields())
            append((T("Total Annual Budget"), "total_annual_budget"))
        append("start_date")
        append("end_date")

        report_fields = list_fields

        configure(tablename,
                  super_entity="doc_entity",
                  deduplicate=self.project_project_deduplicate,
                  onvalidation=self.project_project_onvalidation,
                  create_next=create_next,
                  search_method=project_search,
                  list_fields=list_fields,
                  report_options=Storage(
                    search=advanced,
                    rows=report_fields,
                    cols=report_fields,
                    facts=report_fields,
                    defaults=Storage(
                        rows="multi_hazard_id",
                        cols="countries_id",
                        fact="multi_theme_id",
                        aggregate="count",
                        totals=True
                    )
                )
            )

        # Reusable Field
        project_id = S3ReusableField("project_id", table,
                                     sortby="name",
                                     requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "project_project.id",
                                                              project_project_represent
                                                              )),
                                     represent = project_project_represent,
                                     comment = S3AddResourceLink(c="project", f="project",
                                                                 tooltip=T("If you don't see the project in the list, you can add a new one by clicking link 'Add Project'.")),
                                     label = T("Project"),
                                     ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Custom Methods
        set_method("project", "project",
                   method="timeline",
                   action=self.project_timeline)

        set_method("project", "project",
                   method="map",
                   action=self.project_map)

        # Components
        # Organisations
        add_component("project_organisation", project_project="project_id")

        # Sites
        add_component("project_site", project_project="project_id")

        # Activities
        add_component("project_activity", project_project="project_id")

        # Milestones
        add_component("project_milestone", project_project="project_id")

        # Tasks
        add_component("project_task",
                      project_project=Storage(
                                link="project_task_project",
                                joinby="project_id",
                                key="task_id",
                                actuate="replace",
                                autocomplete="name",
                                autodelete=False))

        # project Locations
        add_component("project_location", project_project="project_id")

        # Beneficiaries
        add_component("project_beneficiary", project_project="project_id")

        # Annual Budgets
        add_component("project_annual_budget", project_project="project_id")

        # Human Resources
        add_component("project_human_resource", project_project="project_id")

        # Themes
        add_component("project_theme_percentage", project_project="project_id")

        # ---------------------------------------------------------------------
        # Project Human Resources
        #
        define_table("project_human_resource",
                     project_id(),
                     human_resource_id(),
                     *s3_meta_fields()
                    )

        configure("project_human_resource",
                  onvalidation=self.project_human_resource_onvalidation,
                  list_fields=["project_id",
                               "human_resource_id$person_id",
                               "human_resource_id$organisation_id",
                               "human_resource_id$job_title",
                               "human_resource_id$status"
                            ],
                        )

        # ---------------------------------------------------------------------
        # Activity Type
        #
        tablename = "project_activity_type"
        table = define_table(tablename,
                             Field("name", length=128,
                                   notnull=True, unique=True),
                             format="%(name)s",
                             *s3_meta_fields())

        # Field configuration?

        # CRUD Strings
        ADD_ACTIVITY_TYPE = T("Add Activity Type")
        crud_strings[tablename] = Storage(
            title_create = ADD_ACTIVITY_TYPE,
            title_display = T("Activity Type"),
            title_list = T("Activity Types"),
            title_update = T("Edit Activity Type"),
            title_search = T("Search for Activity Type"),
            subtitle_create = T("Add New Activity Type"),
            label_list_button = T("List Activity Types"),
            label_create_button = ADD_ACTIVITY_TYPE,
            msg_record_created = T("Activity Type Added"),
            msg_record_modified = T("Activity Type Updated"),
            msg_record_deleted = T("Activity Type Deleted"),
            msg_list_empty = T("No Activity Types Found")
        )

        # Search Method?

        # Resource Configuration?

        # Reusable Fields
        activity_type_id = S3ReusableField("activity_type_id", table,
                                           sortby = "name",
                                           requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "project_activity_type.id",
                                                                  self.project_activity_type_represent,
                                                                  sort=True)),
                                           represent = lambda id, row=None: \
                                                       s3_get_db_field_value(tablename = "project_activity_type",
                                                                             fieldname = "name",
                                                                             look_up_value = id),
                                           label = T("Activity Type"),
                                           comment = S3AddResourceLink(title=ADD_ACTIVITY_TYPE,
                                                                       c="project",
                                                                       f="activity_type",
                                                                       tooltip=T("If you don't see the type in the list, you can add a new one by clicking link 'Add Activity Type'.")),
                                           ondelete = "RESTRICT")

        multi_activity_type_id = S3ReusableField("multi_activity_type_id",
                                                 "list:reference project_activity_type",
                                                 sortby = "name",
                                                 label = T("Types of Activities"),
                                                 requires = IS_NULL_OR(
                                                                IS_ONE_OF(db, "project_activity_type.id",
                                                                          self.project_activity_type_represent,
                                                                          sort=True,
                                                                          multiple=True)),
                                                 represent = lambda opt, row=None: \
                                                    multiref_represent(opt, "project_activity_type"),
                                                 widget = lambda f, v: \
                                                    CheckboxesWidgetS3.widget(f, v, col=3),
                                                 ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return dict(
            project_project_id = project_id,
            project_multi_activity_type_id = multi_activity_type_id,
            project_theme_id = theme_id,
            project_hfa_opts = project_hfa_opts,
        )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for model-global names if module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable=False,
                                writable=False)

        multi_activity_id = S3ReusableField("activity_id", "list:integer",
                                            readable=False,
                                            writable=False)

        return Storage(
            project_project_id = lambda: dummy("project_id"),
            project_multi_activity_id = multi_activity_id
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_project_onvalidation(form):
        """ Form validation """

        # if the project has an Host National Society organisation
        # update organisation_id with its id

        if not form.vars.code and "name" in form.vars:
            # Populate code from name
            form.vars.code = form.vars.name
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_project_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename == "project_project":
            data = item.data
            table = item.table
            # If we have a code, then assume this is unique, however the same
            # project name may be used in multiple locations
            if "code" in data and data.code:
                query = (table.code.lower() == data.code.lower())
            elif "name" in data and data.name:
                query = (table.name.lower() == data.name.lower())
            else:
                # Nothing we can work with
                return

            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_map(r, **attr):
        """
            Display a filterable set of Projects on a Map
            - assumes mode_3w
            - currently assumes that theme_percentages=True

            @ToDo: Browse by Year
        """

        if r.representation == "html" and \
           r.name == "project":

            T = current.T
            db = current.db
            s3db = current.s3db
            response = current.response

            ptable = s3db.project_project
            ttable = s3db.project_theme
            tptable = s3db.project_theme_percentage
            ltable = s3db.gis_location

            # Search Widget
            themes_dropdown = SELECT(_multiple=True,
                                     _id="project_theme_id",
                                     _style="height:80px;")
            append = themes_dropdown.append
            table = current.s3db.project_theme
            themes = current.db(table.deleted == False).select(table.id,
                                                               table.name,
                                                               orderby=table.name)
            for theme in themes:
                append(OPTION(theme.name,
                              _value=theme.id,
                              _selected="selected"))

            form = FORM(themes_dropdown)

            # Map
            # The Layer of Projects to show on the Map
            # @ToDo: Create a URL to the project_polygons custom method & use that
            # @ToDo: Pass through attributes that we don't need for the 1st level of mapping
            #        so that they can be used without a screen refresh
            url = URL(f="location", extension="geojson")
            layer = {
                    "name"   : T("Projects"),
                    "id"     : "projects",
                    "url"    : url,
                    "active" : True,
                    #"marker" : None,
                }

            map = current.gis.show_map(
                        collapsed = True,
                        feature_resources = [layer],
                    )

            output = dict(
                title = T("Projects Map"),
                form = form,
                map = map,
            )

            # Add Static JS
            response.s3.scripts.append(URL(c="static",
                                           f="scripts",
                                           args=["S3", "s3.project_map.js"]))

            response.view = "map.html"
            return output
        else:
            raise HTTP(501, BADMETHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_polygons(r, **attr):
        """
            Export Projects as Country-level GeoJSON Polygons to view on the map
            - currently assumes that theme_percentages=True
        """

        db = current.db
        s3db = current.s3db
        ptable = s3db.project_project
        ttable = s3db.project_theme
        tptable = s3db.project_theme_percentage
        ltable = s3db.gis_location

        vars = current.request.get_vars

        themes = db(ttable.deleted == False).select(ttable.id,
                                                    ttable.name,
                                                    orderby = ttable.name)

        # Total the Budget spent by Theme for each country
        countries = {}
        query = (ptable.deleted == False) & \
                (tptable.project_id == ptable.id)
        #if "theme_id" in vars:
        #    query = query & (tptable.id.belongs(vars.theme_id))
        projects = db(query).select()
        for project in projects:
            # Only show those projects which are only within 1 country
            _countries = project.project_project.countries_id
            if len(_countries) == 1:
                country = _countries[0]
                if country in countries:
                    budget = project.project_project.total_annual_budget
                    theme = project.project_theme_percentage.theme_id
                    percentage = project.project_theme_percentage.percentage
                    countries[country][theme] += budget * percentage
                else:
                    name = db(ltable.id == country).select(ltable.name).first().name
                    countries[country] = dict(name = name)
                    # Init all themes to 0
                    for theme in themes:
                        countries[country][theme.id] = 0
                    # Add value for this record
                    budget = project.project_project.total_annual_budget
                    theme = project.project_theme_percentage.theme_id
                    percentage = project.project_theme_percentage.percentage
                    countries[country][theme] += budget * percentage

        query = (ltable.id.belongs(countries))
        locations = db(query).select(ltable.id,
                                     ltable.wkt)
        for location in locations:
            pass

        # Convert to GeoJSON
        output = json.dumps({})

        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def project_timeline(r, **attr):
        """
            Display the project on a Simile Timeline

            http://www.simile-widgets.org/wiki/Reference_Documentation_for_Timeline

            Currently this just displays a Google Calendar

            @ToDo: Add Milestones
            @ToDo: Filters for different 'layers'
            @ToDo: export milestones/tasks as .ics
        """

        if r.representation == "html" and r.name == "project":

            appname = current.request.application
            response = current.response
            s3 = response.s3

            calendar = r.record.calendar

            # Add core Simile Code
            s3.scripts.append("/%s/static/scripts/simile/timeline/timeline-api.js" % appname)

            # Pass vars to our JS code
            s3.js_global.append('''S3.timeline.calendar="%s"''' % calendar)

            # Add our control script
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.js" % appname)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.min.js" % appname)

            # Create the DIV
            item = DIV(_id="s3timeline",
                       _style="height:400px;border:1px solid #aaa;font-family:Trebuchet MS,sans-serif;font-size:85%;")

            output = dict(item=item)

            output["title"] = current.T("Project Calendar")

            # Maintain RHeader for consistency
            if "rheader" in attr:
                rheader = attr["rheader"](r)
                if rheader:
                    output["rheader"] = rheader

            response.view = "timeline.html"
            return output

        else:
            raise HTTP(501, BADMETHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_type_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.project_activity_type
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def project_hazard_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.project_hazard
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def project_theme_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.project_theme
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def hfa_opts_represent(opt, row=None):
        """ Option representation """

        NONE = current.messages.NONE

        project_hfa_opts = current.response.s3.project_hfa_opts

        opts = opt
        if isinstance(opt, int):
            opts = [opt]
        elif not isinstance(opt, (list, tuple)):
            return NONE
        vals = [str(project_hfa_opts.get(o, NONE)) for o in opts]
        return ", ".join(vals)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_human_resource_onvalidation(form):
        """
            Prevent the same hrm_human_resource record being added more than
            once.
        """

        # The project human resource table
        hr = current.s3db.project_human_resource

        # Fetch the first row that has the same project and human resource ids
        query = (hr.human_resource_id == form.vars.human_resource_id) & \
                (hr.project_id == form.request_vars.project_id)
        row = current.db(query).select(hr.id,
                                       limitby=(0, 1)).first()

        # If we found a row we have a duplicate. Return an error to the user.
        if row:
            form.errors.human_resource_id = current.T("Record already exists")

        return

# =============================================================================
class S3Project3WModel(S3Model):
    """
        Project 3W (Who's doing What Where) Model

        This class contains the tables suitable for use by multinational
        organisations tracking projects at a high level
    """

    names = ["project_beneficiary_type",
             "project_beneficiary",
             "project_location",
             "project_community_contact",
             "project_organisation",
             "project_organisation_roles",
             "project_organisation_lead_role",
             ]

    def model(self):

        T = current.T
        db = current.db

        settings = current.deployment_settings
        community = settings.get_project_community()
        theme_percentages = settings.get_project_theme_percentages()

        person_id = self.pr_person_id
        organisation_id = self.org_organisation_id
        project_id = self.project_project_id

        NONE = current.messages.NONE

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Project Location ('Community')
        #
        tablename = "project_location"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             project_id(),
                             self.gis_location_id(
                                   readable = True,
                                   writable = True,
                                   widget = S3LocationSelectorWidget(hide_address=True),
                                   represent = self.gis_location_lx_represent),
                             self.project_multi_activity_type_id(
                                    # Probably want a diff deployemnt_setting, but this will do for now
                                    readable = not theme_percentages,
                                    writable = not theme_percentages,
                                ),
                             # Field populated by project_theme_percentage_onaccept()
                             self.project_multi_theme_percentage_id(
                                    readable = theme_percentages,
                                    writable = False,
                                ),
                             # @ToDo: This duplicates the data in gis_location
                             #        - move to stats_demographic_data
                             Field("population", "integer",
                                   label = T("Population")),
                             # @ToDo: Replace with a 'family size' value & auto-calculate?
                             Field("number_families", "integer",
                                   label = T("Number of Families")),
                             s3_comments(),
                             # @ToDo: Once project_beneficiary can search Lx via project_location_id$location_id$L1
                             #        or else maybe just add L1 direct to that table?
                             #*s3_meta_fields())
                             *(s3_lx_fields() + s3_meta_fields()))

        table.virtualfields.append(S3ProjectLocationVirtualFields())

        # CRUD Strings
        if community:
            LOCATION = T("Community")
            LOCATION_TOOLTIP = T("If you don't see the community in the list, you can add a new one by clicking link 'Add Community'.")
            ADD_LOCATION = T("Add Community")
            crud_strings[tablename] = Storage(
                    title_create = ADD_LOCATION,
                    title_display = T("Community Details"),
                    title_list = T("Communities"),
                    title_update = T("Edit Community Details"),
                    title_search = T("Search Community"),
                    title_upload = T("Import Community Data"),
                    title_report = T("Who is doing What Where"),
                    title_map = T("Map of Communties"),
                    subtitle_create = T("Add New Community"),
                    label_list_button = T("List Communities"),
                    label_create_button = ADD_LOCATION,
                    msg_record_created = T("Community Added"),
                    msg_record_modified = T("Community Updated"),
                    msg_record_deleted = T("Community Deleted"),
                    msg_list_empty = T("No Communities Found")
            )
        else:
            LOCATION = T("Location")
            LOCATION_TOOLTIP = T("If you don't see the location in the list, you can add a new one by clicking link 'Add Location'.")
            ADD_LOCATION = T("Add Location")
            crud_strings[tablename] = Storage(
                    title_create = ADD_LOCATION,
                    title_display = T("Location Details"),
                    title_list = T("Locations"),
                    title_update = T("Edit Location Details"),
                    title_search = T("Search Location"),
                    title_upload = T("Import Location Data"),
                    title_report = T("Who is doing What Where"),
                    title_map = T("Map of Projects"),
                    subtitle_create = T("Add New Location"),
                    label_list_button = T("List Locations"),
                    label_create_button = ADD_LOCATION,
                    msg_record_created = T("Location Added"),
                    msg_record_modified = T("Location Updated"),
                    msg_record_deleted = T("Location Deleted"),
                    msg_list_empty = T("No Locations Found")
            )

        # Search Method
        if community:
            simple = S3SearchSimpleWidget(
                name = "project_location_search_text",
                label = T("Name"),
                comment = T("Search for a Project Community by name."),
                field = ["name"]
            )
        else:
            simple = S3SearchSimpleWidget(
                name = "project_location_search_text",
                label = T("Text"),
                comment = T("Search for a Project by name, code, location, or description."),
                field = ["location_id$L0",
                         "location_id$L1",
                         "location_id$L2",
                         "location_id$L3",
                         "location_id$L4",
                         "project_id$name",
                         "project_id$code",
                         "project_id$description",
                        ]
            )

        def project_theme_opts():
            """
                Provide the options for the Theme search filter
            """
            table = self.project_theme
            opts = db(table.deleted == False).select(table.id,
                                                     table.name,
                                                     orderby=table.name)
            od = OrderedDict()
            for opt in opts:
                od[opt.id] = opt.name
            return od

        if theme_percentages:
            theme_search = S3SearchOptionsWidget(
                    name = "project_location_search_theme",
                    label = T("Theme"),
                    #field = "multi_theme_percentage_id$theme_id",
                    field = "multi_theme_percentage_id",
                    cols = 1,
                    options = project_theme_opts,
                )
        else:
            theme_search = S3SearchOptionsWidget(
                    name = "project_location_search_theme",
                    label = T("Theme"),
                    field = "project_id$multi_theme_id",
                    cols = 1,
                    options = project_theme_opts,
                )
        advanced_search = (
            simple,
            # This is only suitable for deployments with a few projects
            #S3SearchOptionsWidget(
            #    name = "project_location_search_project",
            #    label = T("Project"),
            #    field = "project_id",
            #    cols = 3
            #),
            theme_search,
            S3SearchOptionsWidget(
                name = "project_location_search_L0",
                #field="L0",
                field = "location_id$L0",
                label = T("Country"),
                cols = 3
            ),
            S3SearchOptionsWidget(
                name = "project_location_search_L1",
                #field = "L1",
                field = "location_id$L1",
                location_level = "L1",
                cols = 3
            ),
            S3SearchOptionsWidget(
                name = "project_location_search_L2",
                #field = "L2",
                field = "location_id$L2",
                location_level = "L2",
                cols = 3
            ),
            S3SearchOptionsWidget(
                name = "project_location_search_L3",
                #field = "L3",
                field = "location_id$L3",
                location_level = "L3",
                cols = 3
            )
        )

        project_location_search = S3Search(
            simple = (simple),
            advanced = advanced_search,
        )

        # Resource Configuration
        report_fields = [(T("Location"), "location_id"),
                         (T("Organization"), "organisation"),
                         (T("Project"), "project_id"),
                         (T("Activity Type"), "multi_activity_type_id"),
                        ]
        list_fields = ["location_id",
                       "project_id",
                       ]
        if theme_percentages:
            list_fields.append("multi_theme_percentage_id")
        else:
            list_fields.append("multi_activity_type_id")
        list_fields.append("comments")

        configure(tablename,
                  super_entity="doc_entity",
                  create_next=URL(c="project", f="location",
                                  args=["[id]", "beneficiary"]),
                  search_method=project_location_search,
                  onaccept=self.project_location_onaccept,
                  deduplicate=self.project_location_deduplicate,
                  report_options=Storage(
                                         search = advanced_search,
                                         rows=report_fields,
                                         cols=report_fields,
                                         facts=report_fields,
                                         defaults=Storage(
                                                          rows="location_id",
                                                          cols="project_id",
                                                          fact="multi_activity_type_id",
                                                          aggregate="list",
                                                          totals=True
                                                          )
                                         ),
                  list_fields = list_fields,
                  )

        # Reusable Field
        project_location_id = S3ReusableField("project_location_id", table,
                                      requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "project_location.id",
                                                              project_location_represent,
                                                              sort=True)),
                                      represent = project_location_represent,
                                      label = LOCATION,
                                      comment = S3AddResourceLink(ADD_LOCATION,
                                                                  c="project", f="location",
                                                                  tooltip=LOCATION_TOOLTIP),
                                      ondelete = "CASCADE")

        # Components
        add_component("project_beneficiary",
                      project_location="project_location_id")

        add_component("pr_person",
                      project_location=Storage(
                            name="contact",
                            link="project_community_contact",
                            joinby="project_location_id",
                            key="person_id",
                            actuate="hide",
                            autodelete=False))

        # ---------------------------------------------------------------------
        # Project Community Contact Person
        #
        tablename = "project_community_contact"
        table = define_table(tablename,
                             project_location_id(),
                             person_id(widget=S3AddPersonWidget(controller="pr"),
                                       requires=IS_ADD_PERSON_WIDGET(),
                                       comment=None),
                             *s3_meta_fields())

        table.virtualfields.append(S3ProjectCommunityContactVirtualFields())

        # CRUD Strings
        ADD_CONTACT = T("Add Contact")
        LIST_OF_CONTACTS = T("Community Contacts")
        crud_strings[tablename] = Storage(
            title_create = ADD_CONTACT,
            title_display = T("Contact Details"),
            title_list = T("Contacts"),
            title_update = T("Edit Contact Details"),
            title_search = T("Search Contacts"),
            subtitle_create = T("Add New Contact"),
            label_list_button = T("List Contacts"),
            label_create_button = ADD_CONTACT,
            msg_record_created = T("Contact Added"),
            msg_record_modified = T("Contact Updated"),
            msg_record_deleted = T("Contact Deleted"),
            msg_list_empty = T("No Contacts Found"))

        community_contact_search = S3Search(
            advanced=(S3SearchSimpleWidget(
                            name = "community_contact_search_simple",
                            label = T("Name"),
                            comment = T("You can search by person name - enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
                            field = ["person_id$first_name",
                                     "person_id$middle_name",
                                     "person_id$last_name"
                                    ]
                        ),
                        S3SearchOptionsWidget(
                            name="community_contact_search_L1",
                            field="person_id$L1",
                            location_level="L1",
                            cols = 3,
                        ),
                        S3SearchOptionsWidget(
                            name="community_contact_search_L2",
                            field="person_id$L2",
                            location_level="L2",
                            cols = 3,
                        )
                    ))

        # Resource configuration
        hierarchy = current.gis.get_location_hierarchy()
        configure(tablename,
                  search_method=community_contact_search,
                  list_fields=["person_id",
                               # (hierarchy["L0"], "person_id$L0"),
                               # (hierarchy["L1"], "person_id$L1"),
                               # (hierarchy["L2"], "person_id$L2"),
                               # (hierarchy["L3"], "person_id$L3"),
                               (T("Email"), "email"),
                               (T("Mobile Phone"), "sms"),
                               "project_location_id",
                               (T("Project"), "project_location_id$project_id"),
                               ])

        # ---------------------------------------------------------------------
        # Project Beneficiary Type
        #
        tablename = "project_beneficiary_type"
        table = define_table(tablename,
                             Field("name", length=128, unique=True,
                                   requires = IS_NOT_IN_DB(db,
                                                           "project_beneficiary_type.name")),
                             *s3_meta_fields())

        # Field configuration?

        # CRUD Strings
        ADD_BNF_TYPE = T("Add Beneficiary Type")
        crud_strings[tablename] = Storage(
            title_create = ADD_BNF_TYPE,
            title_display = T("Beneficiary Type"),
            title_list = T("Beneficiary Types"),
            title_update = T("Edit Beneficiary Type"),
            title_search = T("Search Beneficiary Types"),
            subtitle_create = T("Add New Beneficiary Type"),
            label_list_button = T("List Beneficiary Types"),
            label_create_button = ADD_BNF_TYPE,
            msg_record_created = T("Beneficiary Type Added"),
            msg_record_modified = T("Beneficiary Type Updated"),
            msg_record_deleted = T("Beneficiary Type Deleted"),
            msg_list_empty = T("No Beneficiary Types Found")
        )

        # Search Method?

        # Resource Configuration?

        # Reusable Field
        beneficiary_type_id = S3ReusableField("beneficiary_type_id", table,
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "project_beneficiary_type.id",
                                                          self.project_beneficiary_type_represent)),
                                   represent = self.project_beneficiary_type_represent,
                                   label = T("Beneficiary Type"),
                                   comment = S3AddResourceLink(c="project",
                                                               f="beneficiary_type",
                                                               title=ADD_BNF_TYPE,
                                                               tooltip=T("Please record Beneficiary according to the reporting needs of your project")),
                                   ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Project Beneficiary
        #
        tablename = "project_beneficiary"
        table = define_table(tablename,
                             # populated automatically
                             project_id(readable=False,
                                        writable=False),
                             #activity_id(comment=None),
                             project_location_id(comment=None),
                             beneficiary_type_id(empty=False),
                             Field("number", "integer",
                                   label = T("Quantity"),
                                   requires = IS_INT_IN_RANGE(0, 99999999),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             s3_date("start_date",
                                     label = T("Start Date"),
                                     empty = False,
                                     ),
                             s3_date("end_date",
                                     label = T("End Date"),
                                     empty = False,
                                     ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_BNF = T("Add Beneficiaries")
        crud_strings[tablename] = Storage(
            title_create = ADD_BNF,
            title_display = T("Beneficiaries Details"),
            title_list = T("Beneficiaries"),
            title_update = T("Edit Beneficiaries"),
            title_search = T("Search Beneficiaries"),
            title_report = T("Beneficiary Report"),
            subtitle_create = T("Add New Beneficiaries"),
            label_list_button = T("List Beneficiaries"),
            label_create_button = ADD_BNF,
            msg_record_created = T("Beneficiaries Added"),
            msg_record_modified = T("Beneficiaries Updated"),
            msg_record_deleted = T("Beneficiaries Deleted"),
            msg_list_empty = T("No Beneficiaries Found")
        )

        table.virtualfields.append(S3ProjectBeneficiaryVirtualFields())

        # Search Method?

        # Resource Configuration
        report_fields=[
                      #"activity_id",
                      "project_location_id",
                      (T("Beneficiary Type"), "beneficiary_type_id"),
                      "project_id",
                      (T("Year"), "year"),
                      "project_id$multi_hazard_id",
                      "project_id$multi_theme_id",
                      #"activity_id$multi_activity_type_id"
                     ]
        lh = current.gis.get_location_hierarchy()
        lh = [(lh[opt], opt) for opt in lh]
        report_fields.extend(lh)

        # ---------------------------------------------------------------------
        def year_options():
            """
                returns a dict of the options for the year virtual field
                used by the search widget

                orderby needed for postgres
            """

            ptable = db.project_project
            pbtable = db.project_beneficiary
            pquery = (ptable.deleted == False)
            pbquery = (pbtable.deleted == False)
            pmin = ptable.start_date.min()
            pbmin = pbtable.start_date.min()
            p_start_date_min = db(pquery).select(pmin,
                                                 orderby=pmin,
                                                 limitby=(0, 1)).first()[pmin]
            pb_start_date_min = db(pbquery).select(pbmin,
                                                   orderby=pbmin,
                                                   limitby=(0, 1)).first()[pbmin]
            if p_start_date_min and pb_start_date_min:
                start_year = min(p_start_date_min,
                                 pb_start_date_min).year
            else:
                start_year = (p_start_date_min and p_start_date_min.year) or \
                             (pb_start_date_min and pb_start_date_min.year)

            pmax = ptable.end_date.max()
            pbmax = pbtable.end_date.max()
            p_end_date_max = db(pquery).select(pmax,
                                               orderby=pmax,
                                               limitby=(0, 1)).first()[pmax]
            pb_end_date_max = db(pbquery).select(pbmax,
                                                 orderby=pbmax,
                                                 limitby=(0, 1)).first()[pbmax]
            if p_end_date_max and pb_end_date_max:
                end_year = max(p_end_date_max,
                               pb_end_date_max).year
            else:
                end_year = (p_end_date_max and p_end_date_max.year) or \
                           (pb_end_date_max and pb_end_date_max.year)

            if not start_year or not end_year:
                return {start_year:start_year} or {end_year:end_year}
            years = {}
            for year in xrange(start_year, end_year + 1):
                years[year] = year
            return years

        configure(tablename,
                  onaccept=self.project_beneficiary_onaccept,
                  deduplicate=self.project_beneficiary_deduplicate,
                  report_options=Storage(
                    search=[
                        S3SearchOptionsWidget(
                            field="project_id",
                            name="project",
                            label=T("Project")
                        ),
                        S3SearchOptionsWidget(
                            field="beneficiary_type_id",
                            name="beneficiary_type_id",
                            label=T("Beneficiary Type")
                        ),
                        # @ToDo: These do now work - no results are returned
                        S3SearchOptionsWidget(
                            field="year",
                            name="year",
                            label=T("Year"),
                            options = year_options
                        ),
                        S3SearchOptionsWidget(
                            name = "beneficiary_search_L1",
                            # @ToDo
                            #field = "project_location_id$location_id$L1",
                            field = "project_location_id$L1",
                            location_level = "L1",
                            cols = 3,
                        ),
                    ],
                    rows=report_fields,
                    cols=report_fields,
                    facts=["number"],
                    methods=["sum"],
                    defaults=Storage( rows="project_id",
                                      cols="beneficiary_type_id",
                                      fact="number",
                                      aggregate="sum",
                                      totals=True
                                      )
                  )
                 )

        # Reusable Field
        beneficiary_id = S3ReusableField("beneficiary_id", table,
                                         sortby="name",
                                         requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "project_beneficiary.id",
                                                                  self.project_beneficiary_represent,
                                                                  sort=True)),
                                         represent = self.project_beneficiary_represent,
                                         label = T("Beneficiaries"),
                                         comment = S3AddResourceLink(c="project",
                                                                     f="beneficiary",
                                                                     title=ADD_BNF,
                                                                     tooltip=T("If you don't see the beneficiary in the list, you can add a new one by clicking link 'Add Beneficiary'.")),
                                         ondelete = "SET NULL")

        # ---------------------------------------------------------------------
        # Project Organisations
        # for multi_orgs=True
        #
        project_organisation_roles = settings.get_project_organisation_roles()
        project_organisation_lead_role = settings.get_project_organisation_lead_role()

        organisation_help = T("Add all organizations which are involved in different roles in this project")

        tablename = "project_organisation"
        table = define_table(tablename,
                             project_id(),
                             organisation_id(comment=S3AddResourceLink(c="org",
                                                                       f="organisation",
                                                                       label=T("Add Organization"),
                                                                       title=T("Organization"),
                                                                       tooltip=organisation_help)
                                             ),
                             Field("role", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(project_organisation_roles)),
                                   represent = lambda opt, row=None: \
                                               project_organisation_roles.get(opt, NONE)),
                             Field("amount", "double",
                                   requires = IS_NULL_OR(IS_FLOAT_AMOUNT()),
                                   represent = lambda v, row=None: \
                                               IS_FLOAT_AMOUNT.represent(v, precision=2),
                                   widget = IS_FLOAT_AMOUNT.widget,
                                   label = T("Funds Contributed by this Organization")),
                             s3_currency(),
                             s3_comments(),
                             *s3_meta_fields())

        # Field configuration?

        # CRUD Strings
        ADD_PROJECT_ORG = T("Add Organization to Project")
        crud_strings[tablename] = Storage(
            title_create = ADD_PROJECT_ORG,
            title_display = T("Organization Details"),
            title_list = T("Organizations"),
            title_update = T("Edit Organization"),
            title_search = T("Search Organizations"),
            title_upload = T("Import Organizations"),
            title_report = T("Funding Report"),
            subtitle_create = T("Add Organization to Project"),
            label_list_button = T("List Organizations"),
            label_create_button = ADD_PROJECT_ORG,
            label_delete_button = T("Remove Organization from Project"),
            msg_record_created = T("Organization added to Project"),
            msg_record_modified = T("Project Organization updated"),
            msg_record_deleted = T("Organization removed from Project"),
            msg_list_empty = T("No Organizations for this Project"))

        # Search Method?

        # Resource Configuration
        configure(tablename,
                  deduplicate=self.project_organisation_deduplicate,
                  onvalidation=self.project_organisation_onvalidation,
                  onaccept=self.project_organisation_onaccept,
                  ondelete=self.project_organisation_ondelete)

        # Reusable Field

        # Components

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return dict(
            project_organisation_roles = project_organisation_roles,
            project_organisation_lead_role = project_organisation_lead_role,
        )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for model-global names if module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable=False,
                                writable=False)

        return Storage(
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_type_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        if not id:
            return current.messages.NONE

        db = current.db
        table = db.project_beneficiary_type
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_represent(id, row=None):
        """ FK representation """

        if row:
            return row.type
        if not id:
            return current.messages.NONE

        db = current.db
        table = db.project_beneficiary
        r = db(table.id == id).select(table.type,
                                      limitby = (0, 1)).first()
        try:
            return r.type
        except:
            return current.messages.UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_onaccept(form):
        """ Record creation post-processing """

        db = current.db
        btable = db.project_beneficiary
        ctable = db.project_location

        record_id = form.vars.id
        query = (btable.id == record_id) & \
                (ctable.id == btable.project_location_id)
        project_location = db(query).select(ctable.project_id,
                                            limitby=(0, 1)).first()
        if project_location:
            db(btable.id == record_id).update(
                    project_id=project_location.project_id
                )
        return

    # ---------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "project_beneficiary":
            return

        data = item.data
        if "beneficiary_type_id" in data and \
           "project_location_id" in data:
            # Match beneficiary by type and activity_id
            table = item.table
            beneficiary_type_id = data.beneficiary_type_id
            project_location_id = data.project_location_id
            query = (table.beneficiary_type_id == beneficiary_type_id) & \
                    (table.project_location_id == project_location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_location_onaccept(form):
        """
            Populate the Lx fields from the location_id
        """

        vars = form.vars
        location_id = vars.location_id
        if location_id:
            # Populate the Lx fields
            ctable = current.db.project_location
            s3_lx_update(ctable, vars.id)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_location_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "project_location":
            return

        data = item.data
        if "project_id" in data and \
           "location_id" in data:
            # Match location by project_id and location_id
            project_id = data.project_id
            location_id = data.location_id
            table = item.table
            query = (table.project_id == project_id) & \
                    (table.location_id == location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_organisation_onvalidation(form, lead_role=None):
        """ Form validation """

        if lead_role is None:
            lead_role = current.response.s3.project_organisation_lead_role

        vars = form.vars
        project_id = vars.project_id
        organisation_id = vars.organisation_id
        if str(vars.role) == str(lead_role) and project_id:
            db = current.db
            otable = db.project_organisation
            query = (otable.deleted != True) & \
                    (otable.project_id == project_id) & \
                    (otable.role == lead_role) & \
                    (otable.organisation_id != organisation_id)
            row = db(query).select(otable.id,
                                   limitby=(0, 1)).first()
            if row:
                form.errors.role = T("Lead Implementer for this project is already set, please choose another role.")
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_organisation_onaccept(form):
        """
            Record creation post-processing

            If the added organisation is the lead role, set the
            project.organisation to point to the same organisation.
        """

        vars = form.vars
        if str(vars.role) == \
           str(current.response.s3.project_organisation_lead_role):
            organisation_id = vars.organisation_id
            db = current.db
            project_organisation = db.project_organisation
            project_project = db.project_project

            # Query to get the project ID via the new project
            # organisation record
            query = (project_organisation.id == vars.id) & \
                    (project_project.id == project_organisation.project_id)
            project = db(query).select(project_project.id,
                                       limitby=(0, 1)).first()

            if project:
                # Set the organisation property of the project
                # to match the new lead organisation
                db(project_project.id == project.id).update(
                        organisation_id=organisation_id
                    )

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_organisation_ondelete(row):
        """
            Executed when a project organisation record is deleted.

            If the deleted organisation is the lead role on this project,
            set the project organisation to None.
        """

        db = current.db
        potable = db.project_organisation
        ptable = db.project_project
        query = (potable.id == row.get("id"))
        deleted_row = db(query).select(potable.deleted_fk,
                                       potable.role,
                                       limitby=(0, 1)).first()

        if str(deleted_row.role) == \
           str(current.response.s3.project_organisation_lead_role):
            # Get the project_id
            deleted_fk = json.loads(deleted_row.deleted_fk)
            project_id = deleted_fk["project_id"]

            # Set the project organisation_id to NULL (using None)
            db(ptable.id == project_id).update(organisation_id=None)

        return

    # ---------------------------------------------------------------------
    @staticmethod
    def project_organisation_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "project_organisation":
            return
        data = item.data
        if "project_id" in data and \
           "organisation_id" in data:
            # Match project by org_id and project_id
            table = item.table
            project_id = data.project_id
            organisation_id = data.organisation_id
            query = (table.project_id == project_id) & \
                    (table.organisation_id == organisation_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3ProjectActivityModel(S3Model):
    """
        Project Activity Model

        This model holds the specific Activities for Projects
    """

    names = ["project_activity",
             "project_activity_id",
             "project_multi_activity_id",
             ]

    def model(self):

        T = current.T
        db = current.db

        settings = current.deployment_settings
        mode_task = settings.get_project_mode_task()

        # ---------------------------------------------------------------------
        # Project Activity
        #
        tablename = "project_activity"
        table = self.define_table(tablename,
                                  self.super_link("doc_id", "doc_entity"),
                                  self.project_project_id(),
                                  Field("name",
                                        label = T("Short Description"),
                                        requires=IS_NOT_EMPTY()),
                                  self.gis_location_id(widget = S3LocationSelectorWidget(hide_address=True)),
                                  self.project_multi_activity_type_id(),
                                  Field("time_estimated", "double",
                                        readable = mode_task,
                                        writable = mode_task,
                                        label = "%s (%s)" % (T("Time Estimate"),
                                                             T("hours"))),
                                  Field("time_actual", "double",
                                        readable = mode_task,
                                        # Gets populated from constituent Tasks
                                        writable = False,
                                        label = "%s (%s)" % (T("Time Taken"),
                                                             T("hours"))),
                                  s3_comments(),
                                  format="%(name)s",
                                  *(s3_lx_fields() + s3_meta_fields()))
        # CRUD Strings
        ACTIVITY = T("Activity")
        ACTIVITY_TOOLTIP = T("If you don't see the activity in the list, you can add a new one by clicking link 'Add Activity'.")
        ADD_ACTIVITY = T("Add Activity")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_ACTIVITY,
            title_display = T("Activity Details"),
            title_list = T("Activities"),
            title_update = T("Edit Activity"),
            title_search = T("Search Activities"),
            title_upload = T("Import Activity Data"),
            title_report = T("Activity Report"),
            subtitle_create = T("Add New Activity"),
            label_list_button = T("List Activities"),
            label_create_button = ADD_ACTIVITY,
            msg_record_created = T("Activity Added"),
            msg_record_modified = T("Activity Updated"),
            msg_record_deleted = T("Activity Deleted"),
            msg_list_empty = T("No Activities Found")
        )

        # Virtual Fields
        if mode_task:
            table.virtualfields.append(S3ProjectActivityVirtualFields())

        # Search Method
        project_activity_search = S3Search(field="name")

        # Resource Configuration
        report_fields = []
        append = report_fields.append
        if mode_task:
            append((T("Organization"), "organisation"))
        append((T("Project"), "project_id"))
        append((T("Activity"), "name"))
        append((T("Activity Type"), "multi_activity_type_id"))
        if settings.get_project_sectors():
            append((T("Sector"), "project_id$sector_id"))
        if not settings.get_project_theme_percentages():
            append((T("Theme"), "project_id$multi_theme_id"))
        if settings.get_project_mode_drr():
            append((T("Hazard"), "project_id$multi_hazard_id"))
            append((T("HFA"), "project_id$hfa"))
        lh = current.gis.get_location_hierarchy()
        lh = [(lh[opt], opt) for opt in lh]
        report_fields.extend(lh)
        append("location_id")
        list_fields = ["name",
                       "project_id",
                       "multi_activity_type_id",
                       "comments"
                    ]
        if mode_task:
            append((T("Time Estimated"), "time_estimated"))
            append((T("Time Actual"), "time_actual"))
            create_next = URL(c="project", f="activity",
                              args=["[id]", "task"])
        else:
            create_next = URL(c="project", f="activity",
                              args=["[id]"])

        self.configure(tablename,
                       super_entity="doc_entity",
                       create_next=create_next,
                       search_method=project_activity_search,
                       deduplicate=self.project_activity_deduplicate,
                       report_options=Storage(
                                rows=report_fields,
                                cols=report_fields,
                                facts=report_fields,
                                defaults=Storage(
                                    rows="project_id",
                                    cols="name",
                                    fact="time_actual",
                                    aggregate="sum",
                                    totals=True
                                )
                            ),
                       list_fields = list_fields,
                       )

        # Reusable Field
        activity_id = S3ReusableField("activity_id", table,
                                      sortby="name",
                                      requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "project_activity.id",
                                                              "%(name)s",
                                                              sort=True)),
                                      represent = lambda id, row=None: \
                                                  s3_get_db_field_value(tablename = "project_activity",
                                                                        fieldname = "name",
                                                                        look_up_value = id),
                                      label = ACTIVITY,
                                      comment = S3AddResourceLink(ADD_ACTIVITY,
                                                                  c="project", f="activity",
                                                                  tooltip=ACTIVITY_TOOLTIP),
                                      ondelete = "CASCADE")

        multi_activity_id = S3ReusableField("activity_id", "list:reference project_activity",
                                            sortby="name",
                                            label = T("Activities"),
                                            requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "project_activity.id",
                                                                  "%(name)s",
                                                                  multiple=True,
                                                                  sort=True)),
                                            widget = S3MultiSelectWidget(),
                                            represent = multi_activity_represent,
                                            comment = S3AddResourceLink(ADD_ACTIVITY,
                                                                        c="project", f="activity",
                                                                        tooltip=ACTIVITY_TOOLTIP),
                                            ondelete = "SET NULL")

        # Components

        # Disabled until beneficiaries are updated to support both
        # communities and activities
        #add_component("project_beneficiary",
        #              project_activity="activity_id")

        # Tasks
        self.add_component("project_task",
                           project_activity=Storage(
                                link="project_task_activity",
                                joinby="activity_id",
                                key="task_id",
                                actuate="replace",
                                autocomplete="name",
                                autodelete=False))

        # Pass variables back to global scope (s3db.*)
        return dict(
            project_activity_id = activity_id,
            project_multi_activity_id = multi_activity_id,
        )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for model-global names if module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable=False,
                                writable=False)

        multi_activity_id = S3ReusableField("activity_id", "list:integer",
                                            readable=False,
                                            writable=False)

        return Storage(
            project_activity_id = lambda: dummy("activity_id"),
            project_multi_activity_id = multi_activity_id
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "project_activity":
            return
        table = item.table
        duplicate = None
        data = item.data
        if "project_id" in data and "name" in data:
            # Match activity by project_id and name
            project_id = data.project_id
            name = data.name
            location_id = data.location_id
            query = (table.project_id == project_id) & \
                    (table.name == name) & \
                    (table.location_id == location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3ProjectAnnualBudgetModel(S3Model):
    """
        Project Budget Model

        This model holds the annual budget entries for projects
    """

    names = ["project_annual_budget"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Annual Budgets
        #
        tablename = "project_annual_budget"
        self.define_table(tablename,
                          self.project_project_id(requires=IS_ONE_OF(current.db,
                                                   "project_project.id",
                                                   "%(name)s")),
                          Field("year", "integer", notnull=True,
                                default=None, # make it current year
                                requires=IS_INT_IN_RANGE(1950, 3000),
                                label=T("Year"),
                                ),
                          Field("amount", "double", notnull=True,
                                default=0.00,
                                requires=IS_FLOAT_AMOUNT(),
                                label=T("Amount"),
                                ),
                          s3_currency(required=True),
                          *s3_meta_fields()
                        )


        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("New Annual Budget"),
            title_display = T("Annual Budget"),
            title_list = T("Annual Budgets"),
            title_update = T("Edit Annual Budget"),
            title_search = T("Search Annual Budgets"),
            title_upload = T("Import Annual Budget data"),
            title_report = T("Report on Annual Budgets"),
            subtitle_create = T("Add New Annual Budget"),
            label_list_button = T("List Annual Budgets"),
            label_create_button = T("New Annual Budget"),
            msg_record_created = T("New Annual Budget created"),
            msg_record_modified = T("Annual Budget updated"),
            msg_record_deleted = T("Annual Budget deleted"),
            msg_list_empty = T("No annual budgets found")
        )

        self.configure(tablename,
                       list_fields=[
                            "id",
                            "year",
                            "amount",
                            "currency",
                            ]
                        )

        # Pass variables back to global scope (s3db.*)
        return dict(
        )

# =============================================================================
class S3ProjectFrameworkModel(S3Model):
    """
        Project Framework Model

        This model holds project frameworks
    """

    names = ["project_framework",
             "project_framework_organisation"
             ]

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Project Frameworks
        #
        tablename = "project_framework"
        table = define_table(tablename,
                             self.super_link("doc_id", "doc_entity"),
                             Field("name",
                                   label = T("Name"),
                                   ),
                             s3_comments("description",
                                         label = T("Description"),
                                         comment=None,
                                         ),
                             Field("time_frame",
                                   label = T("Time Frame"),
                                   ),
                             *s3_meta_fields()
                             )


        # CRUD Strings
        if current.deployment_settings.get_auth_record_approval():
            msg_record_created = T("Framework added, awaiting administrator's approval")
        else:
            msg_record_created = T("Framework added")
        crud_strings[tablename] = Storage(
            title_create = T("Add Framework"),
            title_display = T("Framework"),
            title_list = T("Frameworks"),
            title_update = T("Edit Framework"),
            title_search = T("Search Frameworks"),
            title_upload = T("Import Framework data"),
            subtitle_create = T("Add New Framework"),
            label_list_button = T("List Frameworks"),
            label_create_button = T("Add Framework"),
            msg_record_created = msg_record_created,
            msg_record_modified = T("Framework updated"),
            msg_record_deleted = T("Framework deleted"),
            msg_list_empty = T("No Frameworks found")
        )

        self.configure(tablename,
                       super_entity="doc_entity",
                       create_next=URL(f="framework",
                                       args=["[id]", "organisation"]),
                       )

        framework_id = S3ReusableField("framework_id", table,
                                label = T("Organization"),
                                requires = IS_NULL_OR(IS_ONE_OF(db,
                                                    "project_framework.id",
                                                    "%(name)s")),
                                represent = self.project_framework_represent,
                                ondelete = "CASCADE",
                                )

        self.add_component("org_organisation",
                           project_framework=Storage(
                                link="project_framework_organisation",
                                joinby="framework_id",
                                key="organisation_id",
                                actuate="embed",
                                autocomplete="name",
                                autodelete=False))

        # ---------------------------------------------------------------------
        # Project Framework Organisations
        #
        tablename = "project_framework_organisation"
        define_table(tablename,
                     framework_id(),
                     self.org_organisation_id(),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Organization"),
            title_display = T("Organization"),
            title_list = T("Organizations"),
            title_update = T("Edit Organization"),
            title_search = T("Search Organizations"),
            title_upload = T("Import Framework data"),
            subtitle_create = T("Add New Organization"),
            label_list_button = T("List Organizations"),
            label_create_button = T("Add Organization"),
            msg_record_created = T("Organization added to Framework"),
            msg_record_modified = T("Organization updated"),
            msg_record_deleted = T("Organization removed from Framework"),
            msg_list_empty = T("No Organizations found for this Framework")
        )

        # Pass variables back to global scope (s3db.*)
        return dict(
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_framework_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        if not id:
            return current.messages.NONE

        db = current.db
        table = db.project_framework
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

# =============================================================================
class S3ProjectThemeModel(S3Model):
    """
        Project Theme Model

        This model holds the % breakdown by theme (sector in IATI) for projects
    """

    names = ["project_theme_percentage",
             "project_multi_theme_percentage_id"
             ]

    def model(self):

        T = current.T
        db = current.db

        tablename = "project_theme_percentage"
        self.define_table(tablename,
                          self.project_project_id(
                            requires=IS_ONE_OF(db, "project_project.id",
                                               "%(name)s")
                            ),
                          self.project_theme_id(
                            requires=IS_ONE_OF(db, "project_theme.id",
                                               "%(name)s")
                            ),
                          Field("percentage", "integer",
                                label = T("Percentage"),
                                default = 0,
                                requires = IS_INT_IN_RANGE(0, 101),
                                ),
                          *s3_meta_fields()
                          )


        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("New Theme"),
            title_display = T("Theme"),
            title_list = T("Themes"),
            title_update = T("Edit Theme"),
            title_search = T("Search Themes"),
            title_upload = T("Import Theme data"),
            title_report = T("Report on Themes"),
            subtitle_create = T("Add New Theme"),
            label_list_button = T("List Themes"),
            label_create_button = T("New Theme"),
            msg_record_created = T("Theme added"),
            msg_record_modified = T("Theme updated"),
            msg_record_deleted = T("Theme removed"),
            msg_list_empty = T("No themes found")
        )

        self.configure(tablename,
                       onaccept=self.project_theme_percentage_onaccept)

        # Multiple for theme_percentages=False
        multi_theme_percentage_id = S3ReusableField("multi_theme_percentage_id",
                            "list:reference project_theme_percentage",
                            label = T("Themes"),
                            requires = IS_NULL_OR(IS_ONE_OF(db,
                                                "project_theme_percentage.id",
                                                "%(id)s",
                                                multiple=True)),
                            represent = multi_theme_percentage_represent,
                            ondelete = "SET NULL",
                            )

        # Pass variables back to global scope (s3db.*)
        return dict(
            project_multi_theme_percentage_id = multi_theme_percentage_id,
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_theme_percentage_onaccept(form):
        """
            Record creation post-processing

            Update the percentages of all the Project's Locations.
        """

        # Check for prepop
        project_id = form.vars.get("project_id", None)
        if not project_id and form.request_vars:
            # Interactive form
            project_id = form.request_vars.get("project_id", None)
        if not project_id:
            return
        # Calculate the list of Percentages for this Project
        db = current.db
        table = db.project_theme_percentage
        query = (table.deleted == False) & \
                (table.project_id == project_id)
        rows = db(query).select(table.id)
        percentages = [row.id for row in rows]

        # Update the Project's Locations
        table = current.s3db.project_location
        query = (table.project_id == project_id)
        db(query).update(multi_theme_percentage_id = percentages)

# =============================================================================
class S3ProjectTaskModel(S3Model):
    """
        Project Task Model

        This class holds the tables used for an Organisation to manage
        their Tasks in detail.
    """

    names = ["project_milestone",
             "project_task",
             "project_time",
             "project_comment",
             "project_task_project",
             "project_task_activity",
             "project_task_id",
             ]

    def model(self):

        db = current.db
        T = current.T
        auth = current.auth
        request = current.request

        project_id = self.project_project_id

        s3_utc_represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Project Milestone
        #
        tablename = "project_milestone"
        table = define_table(tablename,
                             # Stage Report
                             super_link("doc_id", "doc_entity"),
                             project_id(),
                             Field("name",
                                   label = T("Short Description"),
                                   requires=IS_NOT_EMPTY()),
                             s3_date(label = T("Date")),
                             s3_comments(),
                             format="%(name)s",
                             *s3_meta_fields())

        # CRUD Strings
        ADD_MILESTONE = T("Add Milestone")
        crud_strings[tablename] = Storage(
            title_create = ADD_MILESTONE,
            title_display = T("Milestone Details"),
            title_list = T("Milestones"),
            title_update = T("Edit Milestone"),
            title_search = T("Search Milestones"),
            title_upload = T("Import Milestone Data"),
            subtitle_create = T("Add New Milestone"),
            label_list_button = T("List Milestones"),
            label_create_button = ADD_MILESTONE,
            msg_record_created = T("Milestone Added"),
            msg_record_modified = T("Milestone Updated"),
            msg_record_deleted = T("Milestone Deleted"),
            msg_list_empty = T("No Milestones Found")
        )

        # Reusable Field
        milestone_id = S3ReusableField("milestone_id", table,
                                       sortby="name",
                                       requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "project_milestone.id",
                                                              "%(name)s")),
                                       represent = self.milestone_represent,
                                       comment = S3AddResourceLink(c="project",
                                                                   f="milestone",
                                                                   title=ADD_MILESTONE,
                                                                   tooltip=T("A project milestone marks a significant date in the calendar which shows that progress towards the overall objective is being made.")),
                                       label = T("Milestone"),
                                       ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Tasks
        #
        # Tasks can be linked to Activities or directly to Projects
        # - they can also be used by the Event/Scenario modules
        #
        # @ToDo: Recurring tasks
        #
        # These Statuses can be customised, although doing so limits the ability to do synchronization
        # - best bet is simply to comment statuses that you don't wish to use
        #
        project_task_status_opts = {
            1: T("Draft"),
            2: T("New"),
            3: T("Assigned"),
            4: T("Feedback"),
            5: T("Blocked"),
            6: T("On Hold"),
            7: T("Cancelled"),
            8: T("Duplicate"),
            9: T("Ready"),
            10: T("Verified"),
            11: T("Reopened"),
            12: T("Completed"),
            #99: T("unspecified")
        }

        project_task_active_statuses = [2, 3, 4, 11]
        project_task_priority_opts = {
            1:T("Urgent"),
            2:T("High"),
            3:T("Normal"),
            4:T("Low")
        }

        #staff = auth.s3_has_role("STAFF")
        staff = True
        settings = current.deployment_settings
        milestones = settings.get_project_milestones()

        tablename = "project_task"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             Field("template", "boolean",
                                   default=False,
                                   readable=False,
                                   writable=False),
                             Field("name",
                                   label = T("Short Description"),
                                   length=100,
                                   notnull=True,
                                   requires = IS_LENGTH(maxsize=100, minsize=1)),
                             Field("description", "text",
                                   label = T("Detailed Description/URL"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Detailed Description/URL"),
                                                                   T("Please provide as much detail as you can, including the URL(s) where the bug occurs or you'd like the new feature to go.")))),
                             self.org_site_id,
                             self.gis_location_id(
                                    label=T("Deployment Location"),
                                    readable=False,
                                    writable=False
                                    ),
                             Field("source",
                                   label = T("Source")),
                             Field("priority", "integer",
                                   requires = IS_IN_SET(project_task_priority_opts,
                                                        zero=None),
                                   default = 3,
                                   label = T("Priority"),
                                   represent = lambda opt, row=None: \
                                               project_task_priority_opts.get(opt,
                                                                              UNKNOWN_OPT)),
                             # Could be a Person, Team or Organisation
                             super_link("pe_id", "pr_pentity",
                                        readable = staff,
                                        writable = staff,
                                        label = T("Assigned to"),
                                        filterby = "instance_type",
                                        filter_opts = ["pr_person", "pr_group", "org_organisation"],
                                        represent = self.project_assignee_represent,
                                        # @ToDo: Widget
                                        #widget = S3PentityWidget(),
                                        #comment = DIV(_class="tooltip",
                                        #              _title="%s|%s" % (T("Assigned to"),
                                        #                                T("Enter some characters to bring up a list of possible matches")))
                                        ),
                             Field("date_due", "datetime",
                                   label = T("Date Due"),
                                   readable = staff,
                                   writable = staff,
                                   requires = [IS_EMPTY_OR(
                                               IS_UTC_DATETIME_IN_RANGE(
                                                   minimum=request.utcnow - datetime.timedelta(days=1),
                                                   error_message="%s %%(min)s!" %
                                                                 T("Enter a valid future date")))],
                                   widget = S3DateTimeWidget(past=0,
                                                             future=8760),  # Hours, so 1 year
                                   represent = s3_date_represent),
                             milestone_id(
                                   readable = milestones and staff,
                                   writable = milestones and staff,
                                   ),
                             Field("time_estimated", "double",
                                   readable = staff,
                                   writable = staff,
                                   represent = lambda v: v or "",
                                   label = "%s (%s)" % (T("Time Estimate"),
                                                       T("hours"))),
                             Field("time_actual", "double",
                                   readable = staff,
                                   # This comes from the Time component
                                   writable=False,
                                   label = "%s (%s)" % (T("Time Taken"),
                                                        T("hours"))),
                             Field("status", "integer",
                                   requires = IS_IN_SET(project_task_status_opts,
                                                        zero=None),
                                   default = 2,
                                   readable = staff,
                                   writable = staff,
                                   label = T("Status"),
                                   represent = lambda opt, row=None: \
                                               project_task_status_opts.get(opt,
                                                                            UNKNOWN_OPT)),
                             *s3_meta_fields())

        # Field configurations
        # Comment these if you don't need a Site associated with Tasks
        #table.site_id.readable = table.site_id.writable = True
        #table.site_id.label = T("Check-in at Facility") # T("Managing Office")
        table.created_on.represent = s3_date_represent

        # CRUD Strings
        ADD_TASK = T("Add Task")
        crud_strings[tablename] = Storage(
            title_create = ADD_TASK,
            title_display = T("Task Details"),
            title_list = T("Tasks"),
            title_update = T("Edit Task"),
            title_search = T("Search Tasks"),
            title_upload = T("Import Tasks"),
            subtitle_create = T("Add New Task"),
            label_list_button = T("List Tasks"),
            label_create_button = ADD_TASK,
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task deleted"),
            msg_list_empty = T("No tasks currently registered"))

        # Virtual Fields
        # Do just for the common report
        table.virtualfields.append(S3ProjectTaskVirtualFields())

        # Search Method
        advanced_task_search = [
                    S3SearchSimpleWidget(
                        name = "task_search_text_advanced",
                        label = T("Description"),
                        comment = T("Search for a Task by description."),
                        field = [ "name",
                                  "description",
                                ]
                    ),
                    S3SearchOptionsWidget(
                        name = "task_search_priority",
                        label = T("Priority"),
                        field = "priority",
                        cols = 4
                    ),
                    S3SearchOptionsWidget(
                        name = "task_search_project",
                        label = T("Project"),
                        field = "project",
                        options = self.task_project_opts,
                        cols = 3
                    ),
                    S3SearchOptionsWidget(
                        name = "task_search_activity",
                        label = T("Activity"),
                        field = "activity",
                        options = self.task_activity_opts,
                        cols = 3
                    ),
                    S3SearchOptionsWidget(
                        name = "task_search_created_by",
                        label = T("Created By"),
                        field = "created_by",
                        cols = 4
                    ),
                    S3SearchOptionsWidget(
                        name = "task_search_assignee",
                        label = T("Assigned To"),
                        field = "pe_id",
                        null = T("Unassigned"),
                        cols = 4
                    ),
                    S3SearchMinMaxWidget(
                        name="task_search_date_created",
                        method="range",
                        label=T("Date Created"),
                        field="created_on"
                    ),
                    S3SearchMinMaxWidget(
                        name="task_search_date_due",
                        method="range",
                        label=T("Date Due"),
                        field="date_due"
                    ),
                    S3SearchOptionsWidget(
                        name = "task_search_status",
                        label = T("Status"),
                        field = "status",
                        cols = 4
                    ),
                ]
        list_fields=["id",
                     "priority",
                     (T("ID"), "task_id"),
                     "name",
                     "pe_id",
                     "date_due",
                     "time_estimated",
                     "created_on",
                     "status",
                     #"site_id"
                    ]

        if settings.get_project_milestones():
            list_fields.insert(5, "milestone_id")
            advanced_task_search.insert(4, S3SearchOptionsWidget(
                                                name = "task_search_milestone",
                                                label = T("Milestone"),
                                                field = "milestone_id$name",
                                                cols = 3
                                            ))

        task_search = S3Search(advanced = advanced_task_search)

        # Resource Configuration
        configure(tablename,
                  super_entity="doc_entity",
                  copyable=True,
                  orderby="project_task.priority",
                  owner_entity=self.task_owner_entity,
                  onvalidation=self.task_onvalidation,
                  create_next=URL(f="task", args=["[id]"]),
                  create_onaccept=self.task_create_onaccept,
                  update_onaccept=self.task_update_onaccept,
                  search_method=task_search,
                  list_fields=list_fields,
                  extra="description")

        # Reusable field
        task_id = S3ReusableField("task_id", table,
                                  label = T("Task"),
                                  sortby="name",
                                  requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "project_task.id",
                                                          "%(name)s")),
                                  represent = lambda id, row=None: \
                                    (id and [db.project_task[id].name] or [messages.NONE])[0],
                                  comment = S3AddResourceLink(c="project",
                                                              f="task",
                                                              title=ADD_TASK,
                                                              tooltip=T("A task is a piece of work that an individual or team can do in 1-2 days.")),
                                  ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Custom Methods
        self.set_method("project", "task",
                        method="dispatch",
                        action=self.task_dispatch)

        # Components
        # Projects (for imports)
        add_component("project_project",
                      project_task=Storage(
                                link="project_task_project",
                                joinby="task_id",
                                key="project_id",
                                actuate="embed",
                                autocomplete="name",
                                autodelete=False))

        # Activities (for imports)
        add_component("project_activity",
                      project_task=Storage(
                                link="project_task_activity",
                                joinby="task_id",
                                key="activity_id",
                                actuate="embed",
                                autocomplete="name",
                                autodelete=False))

        # Job roles
        add_component("hrm_job_role",
                      project_task=Storage(
                                link="project_task_job_role",
                                joinby="task_id",
                                key="job_role_id",
                                actuate="embed",
                                autocomplete="name",
                                autodelete=False))

        # Human Resources (assigned)
        add_component("hrm_human_resource",
                      project_task=Storage(
                                link="project_task_human_resource",
                                joinby="task_id",
                                key="human_resource_id",
                                actuate="embed",
                                autocomplete="name",
                                autodelete=False))

        # Requests
        add_component("req_req",
                      project_task=Storage(
                                link="project_task_req",
                                joinby="task_id",
                                key="req_id",
                                actuate="embed",
                                autocomplete="request_number",
                                autodelete=False))

        # Time
        add_component("project_time", project_task="task_id")

        # Comments (for imports))
        add_component("project_comment", project_task="task_id")

        # ---------------------------------------------------------------------
        # Link Tasks <-> Projects
        #
        tablename = "project_task_project"
        table = define_table(tablename,
                             task_id(),
                             project_id(),
                             *s3_meta_fields())

        # Field configuration
        # CRUD Strings
        # Search Method
        # Resource Configuration
        # Reusable Field

        # ---------------------------------------------------------------------
        # Link task <-> activity
        #
        # Tasks <> Activities
        tablename = "project_task_activity"
        table = define_table(tablename,
                             task_id(),
                             self.project_activity_id(),
                             *s3_meta_fields())

        # Field configuration
        # CRUD Strings
        # Search Method
        # Resource Configuration
        # Reusable Field

        # ---------------------------------------------------------------------
        # Project comment
        #
        # @ToDo: Attachments?
        #
        # Parent field allows us to:
        #  * easily filter for top-level threads
        #  * easily filter for next level of threading
        #  * hook a new reply into the correct location in the hierarchy
        #
        tablename = "project_comment"
        table = define_table(tablename,
                             Field("parent", "reference project_comment",
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "project_comment.id"
                                                          )),
                                   readable=False),
                             task_id(),
                             Field("body", "text",
                                   notnull=True,
                                   label = T("Comment")),
                             *s3_meta_fields())

        # Field configuration?

        # CRUD Strings?

        # Search Method?

        # Resource Configuration
        configure(tablename,
                  list_fields=["id",
                               "task_id",
                               "created_by",
                               "modified_on"
                               ])

        # Reusable Field?

        # ---------------------------------------------------------------------
        # Project Time
        # - used to Log hours spent on a Task
        #
        tablename = "project_time"
        table = define_table(tablename,
                             task_id(),
                             self.pr_person_id(default=auth.s3_logged_in_person()),
                             Field("date", "datetime",
                                   label = T("Date"),
                                   requires = IS_EMPTY_OR(IS_UTC_DATETIME()),
                                   represent = s3_utc_represent,
                                   widget = S3DateTimeWidget(past=8760, # Hours, so 1 year
                                                             future=0),
                                   default = request.utcnow),
                             Field("hours", "double",
                                   label = "%s (%s)" % (T("Time"),
                                                        T("hours")),
                                   represent=lambda v, row=None: IS_FLOAT_AMOUNT.represent(v, precision=2)),
                             s3_comments(),
                             format="%(comments)s",
                             *s3_meta_fields())

        # CRUD Strings
        ADD_TIME = T("Log Time Spent")
        crud_strings[tablename] = Storage(
            title_create = ADD_TIME,
            title_display = T("Logged Time Details"),
            title_list = T("Logged Time"),
            title_update = T("Edit Logged Time"),
            title_search = T("Search Logged Time"),
            title_upload = T("Import Logged Time data"),
            title_report = T("Last Week's Work"),
            subtitle_create = T("Log New Time"),
            label_list_button = T("List Logged Time"),
            label_create_button = ADD_TIME,
            msg_record_created = T("Time Logged"),
            msg_record_modified = T("Time Log Updated"),
            msg_record_deleted = T("Time Log Deleted"),
            msg_list_empty = T("No Time Logged")
        )
        if "rows" in request.get_vars and request.get_vars.rows == "project":
            crud_strings[tablename].title_report = T("Project Time Report")

        # Virtual Fields
        table.virtualfields.append(S3ProjectTimeVirtualFields())

        configure(tablename,
                  onaccept=self.time_onaccept,
                  list_fields=["id",
                               (T("Project"), "project"),
                               "task_id",
                               "person_id",
                               "date",
                               "hours",
                               "comments",
                               ])

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return dict(
            project_task_id = task_id,
            project_task_active_statuses = project_task_active_statuses,
        )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for model-global names if module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable=False,
                                writable=False)

        return Storage(
            project_task_id = lambda: dummy("task_id")
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def task_project_opts():
        """
            Provide the options for the Project search filter
            - all Projects with Tasks
        """

        db = current.db
        ptable = db.project_project
        ttable = db.project_task
        ltable = db.project_task_project
        query = (ttable.deleted == False) & \
                (ltable.task_id == ttable.id) & \
                (ltable.project_id == ptable.id)
        opts = db(query).select(ptable.name)
        _dict = {}
        for opt in opts:
            _dict[opt.name] = opt.name
        return _dict

    # -------------------------------------------------------------------------
    @staticmethod
    def task_activity_opts():
        """
            Provide the options for the Activity search filter
            - all Activities with Tasks
        """

        db = current.db
        atable = db.project_activity
        ttable = db.project_task
        ltable = db.project_task_activity
        query = (ttable.deleted == False) & \
                (ltable.task_id == ttable.id) & \
                (ltable.activity_id == atable.id)
        opts = db(query).select(atable.name)
        _dict = {}
        for opt in opts:
            _dict[opt.name] = opt.name
        return _dict

    # ---------------------------------------------------------------------
    @staticmethod
    def milestone_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE
            
        db = current.db
        table = db.project_milestone
        record = db(table.id == id).select(table.name,
                                          limitby=(0, 1)).first()
        try:
            return record.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def project_assignee_represent(id, row=None):
        """ FK representation """

        if row:
            id = row.pe_id
            instance_type = row.instance_type
        elif id:
            if isinstance(id, Row):
                instance_type = id.instance_type
                id = id.pe_id
            else:
                instance_type = None
        else:
            return current.messages.NONE
        
        db = current.db
        s3db = current.s3db
        if not instance_type:
            table = s3db.pr_pentity
            r = db(table._id == id).select(table.instance_type,
                                           limitby=(0, 1)).first()
            instance_type = r.instance_type

        if instance_type == "pr_person":
            # initials?
            return s3_fullname(pe_id=id) or current.messages.UNKNOWN_OPT
        elif instance_type in ("pr_group", "org_organisation"):
            # Team or Organisation
            table = s3db[instance_type]
            r = db(table.pe_id == id).select(table.name,
                                             limitby=(0, 1)).first()
            try:
                return r.name
            except:
                return current.messages.UNKNOWN_OPT
        else:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def task_owner_entity(table, record):
        """ Set the task owner entity to the project's owner entity """

        task_id = record.id
        db = current.db
        ptable = db.project_project
        ltable = db.project_task_project
        query = (ltable.task_id == task_id) & \
                (ltable.project_id == ptable.id)
        project = db(query).select(ptable.owned_by_entity,
                                   limitby=(0, 1)).first()
        if project:
            return project.owned_by_entity
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def task_onvalidation(form):
        """ Task form validation """

        vars = form.vars
        if str(vars.status) == "3" and not vars.pe_id:
            form.errors.pe_id = \
                current.T("Status 'assigned' requires the %(fieldname)s to not be blank") % \
                    dict(fieldname=current.db.project_task.pe_id.label)
        elif vars.pe_id and str(vars.status) == "2":
            # Set the Status to 'Assigned' if left at default 'New'
            vars.status = 3
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def task_create_onaccept(form):
        """
            When a Task is created:
                * Process the additional fields: Project/Activity
                * create associated Link Tables
                * ensure that it is owned by the Project Customer
                * notify assignee
        """

        db = current.db
        s3db = current.s3db
        session = current.session

        vars = form.vars
        id = vars.id
        _vars = current.request.post_vars

        if session.s3.event:
            # Create a link between this Task & the active Event
            etable = s3db.event_task
            etable.insert(event_id=session.s3.event,
                          task_id=id)

        vars = current.request.post_vars
        table = db.project_task
        if "project_id" in vars:
            # Create Link to Project
            ltable = db.project_task_project
            if vars.project_id:
                link_id = ltable.insert(task_id = id,
                                        project_id = _vars.project_id)

        if "activity_id" in vars:
            # Create Link to Activity
            ltable = db.project_task_activity
            if vars.activity_id:
                link_id = ltable.insert(task_id = id,
                                        activity_id = _vars.activity_id)

        # Make sure the task is also linked to the project
        # when created under an activity
        if id:
            lta = db.project_task_activity
            ltp = db.project_task_project
            ta = db.project_activity
            query = (ltp.task_id == id)
            row = db(query).select(ltp.project_id,
                                   limitby=(0, 1)).first()
            if not row:
                query = (lta.task_id == id) & \
                        (lta.activity_id == ta.id)
                row = db(query).select(ta.project_id,
                                       limitby=(0, 1)).first()
                if row and row.project_id:
                    ltp.insert(task_id=id,
                               project_id=row.project_id)

        # Notify Assignee
        task_notify(form)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def task_update_onaccept(form):
        """
            * Process the additional fields: Project/Activity
            * Log changes as comments
            * If the task is assigned to someone then notify them
        """

        db = current.db
        s3db = current.s3db
        s3mgr = current.manager

        vars = form.vars
        id = vars.id
        record = form.record

        table = db.project_task

        changed = {}
        if record: # Not True for a record merger
            for var in vars:
                vvar = vars[var]
                rvar = record[var]
                if vvar != rvar:
                    type = table[var].type
                    if type == "integer" or \
                       type.startswith("reference"):
                        vvar = int(vvar)
                        if vvar == rvar:
                            continue
                    represent = table[var].represent
                    if not represent:
                        represent = lambda o: o
                    if rvar:
                        changed[var] = "%s changed from %s to %s" % \
                            (table[var].label, represent(rvar), represent(vvar))
                    else:
                        changed[var] = "%s changed to %s" % \
                            (table[var].label, represent(vvar))

        if changed:
            table = db.project_comment
            text = s3_auth_user_represent(current.auth.user.id)
            for var in changed:
                text = "%s\n%s" % (text, changed[var])
            table.insert(task_id=id,
                         body=text)

        vars = current.request.post_vars
        if "project_id" in vars:
            ptable = db.project_project
            ltable = db.project_task_project
            filter = (ltable.task_id == id)
            if vars.project_id:
                # Create the link to the Project
                #master = s3mgr.define_resource("project", "task", id=id)
                #record = db(ptable.id == vars.project_id).select(ptable.id,
                #                                                 limitby=(0, 1)).first()
                #link = s3mgr.define_resource("project", "task_project")
                #link_id = link.update_link(master, record)
                query = (ltable.task_id == id) & \
                        (ltable.project_id == vars.project_id)
                record = db(query).select(ltable.id, limitby=(0, 1)).first()
                if record:
                    link_id = record.id
                else:
                    link_id = ltable.insert(task_id = id,
                                            project_id = vars.project_id)
                filter = filter & (ltable.id != link_id)
            # Remove any other links
            links = s3mgr.define_resource("project", "task_project",
                                          filter=filter)
            ondelete = s3db.get_config("project_task_project",
                                       "ondelete")
            links.delete(ondelete=ondelete)

        if "activity_id" in vars:
            atable = db.project_activity
            ltable = db.project_task_activity
            filter = (ltable.task_id == id)
            if vars.activity_id:
                # Create the link to the Activity
                #master = s3mgr.define_resource("project", "task", id=id)
                #record = db(atable.id == vars.activity_id).select(atable.id,
                #                                                  limitby=(0, 1)).first()
                #link = s3mgr.define_resource("project", "task_activity")
                #link_id = link.update_link(master, record)
                query = (ltable.task_id == id) & \
                        (ltable.activity_id == vars.activity_id)
                record = db(query).select(ltable.id, limitby=(0, 1)).first()
                if record:
                    link_id = record.id
                else:
                    link_id = ltable.insert(task_id = id,
                                            activity_id = vars.activity_id)
                filter = filter & (ltable.id != link_id)
            # Remove any other links
            links = s3mgr.define_resource("project", "task_activity",
                                          filter=filter)
            ondelete = s3db.get_config("project_task_activity",
                                       "ondelete")
            links.delete(ondelete=ondelete)

        # Notify Assignee
        task_notify(form)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def task_dispatch(r, **attr):
        """
            Send a Task Dispatch notice from a Task
            - if a location is supplied, this will be formatted as an OpenGeoSMS
        """

        if r.representation == "html" and \
           r.name == "task" and r.id and not r.component:

            record = r.record
            text = "%s: %s" % (record.name,
                               record.description)

            # Encode the message as an OpenGeoSMS
            msg = current.msg
            message = msg.prepare_opengeosms(record.location_id,
                                             code="ST",
                                             map="google",
                                             text=text)

            # URL to redirect to after message sent
            url = URL(c="project",
                      f="task",
                      args=r.id)

            # Create the form
            if record.pe_id:
                opts = dict(recipient=record.pe_id)
            else:
                opts = dict(recipient_type="pr_person")
            output = msg.compose(type="SMS",
                                 message = message,
                                 url = url,
                                 **opts)

            # Maintain RHeader for consistency
            if "rheader" in attr:
                rheader = attr["rheader"](r)
                if rheader:
                    output["rheader"] = rheader

            output["title"] = current.T("Send Task Notification")
            current.response.view = "msg/compose.html"
            return output

        else:
            raise HTTP(501, BADMETHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def time_onaccept(form):
        """ When Time is logged, update the Task & Activity """

        db = current.db
        titable = db.project_time
        ttable = db.project_task
        atable = db.project_activity
        tatable = db.project_task_activity

        # Find the Task
        task_id = form.vars.task_id
        if not task_id:
            # Component Form
            query = (titable.id == form.vars.id)
            record = db(query).select(titable.task_id,
                                      limitby=(0, 1)).first()
            if record:
                task_id = record.task_id

        # Total the Hours Logged
        query = (titable.deleted == False) & \
                (titable.task_id == task_id)
        rows = db(query).select(titable.hours)
        hours = 0
        for row in rows:
            hours += row.hours

        # Update the Task
        query = (ttable.id == task_id)
        db(query).update(time_actual=hours)

        # Find the Activity
        query = (tatable.deleted == False) & \
                (tatable.task_id == task_id)
        activity = db(query).select(tatable.activity_id,
                                    limitby=(0, 1)).first()
        if activity:
            activity_id = activity.activity_id

            # Find all Tasks in this Activity
            query = (ttable.deleted == False) & \
                    (tatable.deleted == False) & \
                    (tatable.task_id == ttable.id) & \
                    (tatable.activity_id == activity_id)
            tasks = db(query).select(ttable.time_actual)

            # Total the Hours Logged
            hours = 0
            for task in tasks:
                hours += task.time_actual

            # Update the Activity
            query = (atable.id == activity_id)
            db(query).update(time_actual=hours)

        return

# =============================================================================
class S3ProjectTaskHRMModel(S3Model):
    """
        Project Task HRM Model

        This class holds the tables used to link Tasks to Human Resources
        - either individuals or Job Roles
    """

    names = ["project_task_job_role",
             "project_task_human_resource",
             ]

    def model(self):

        define_table = self.define_table
        task_id = self.project_task_id

        # ---------------------------------------------------------------------
        # Link Tasks <> Human Resources
        tablename = "project_task_human_resource"
        table = define_table(tablename,
                             task_id(),
                             self.hrm_human_resource_id(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Link Tasks <> Job Roles
        tablename = "project_task_job_role"
        table = define_table(tablename,
                             task_id(),
                             self.hrm_job_role_id(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return dict(
        )

# =============================================================================
class S3ProjectTaskIReportModel(S3Model):
    """
        Project Task IReport Model

        This class holds the table used to link Tasks with Incident Reports.
        @ToDo: Link to Incidents instead?
    """

    names = ["project_task_ireport",
             ]

    def model(self):

        # Link Tasks <-> Incident Reports
        #
        tablename = "project_task_ireport"
        table = self.define_table(tablename,
                                  self.project_task_id(),
                                  self.irs_ireport_id(),
                                  *s3_meta_fields())

        self.configure(tablename,
                       onaccept=self.task_ireport_onaccept)

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return dict(
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def task_ireport_onaccept(form):
        """
            When a Task is linked to an IReport, then populate the location_id
        """

        vars = form.vars
        ireport_id = vars.ireport_id
        task_id = vars.task_id

        db = current.db

        # Check if we already have a Location for the Task
        table = db.project_task
        query = (table.id == task_id)
        record = db(query).select(table.location_id,
                                  limitby=(0, 1)).first()
        if not record or record.location_id:
            return

        # Find the Incident Location
        itable = db.irs_ireport
        query = (itable.id == ireport_id)
        record = db(query).select(itable.location_id,
                                  limitby=(0, 1)).first()
        if not record or not record.location_id:
            return

        location_id = record.location_id

        # Update the Task
        query = (table.id == task_id)
        db(query).update(location_id=location_id)

        return

# =============================================================================
def project_project_represent(id, row=None, show_link=True):
    """ FK representation """

    if row:
        pass
    elif id:
        db = current.db
        table = db.project_project
        row = db(table.id == id).select(table.name,
                                        table.code,
                                        limitby=(0, 1)).first()
    else:
        return current.messages.NONE

    try:
        if current.deployment_settings.get_project_codes():
            repr = "%s: %s" % (row.code, row.name)
        else:
            repr = row.name
        if not show_link:
            return repr
        return A(repr, _href = URL(c="project",
                                   f="project",
                                   args=[id]))
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def multiref_represent(opts, tablename, represent_string = "%(name)s"):
    """
        Represent a list of references

        @param opt: the current value or list of values
        @param tablename: the referenced table
        @param represent_string: format string to represent the records
    """

    DEFAULT = ""

    s3db = current.s3db
    table = s3db.table(tablename, None)
    if table is None:
        return DEFAULT

    if not isinstance(opts, (list, tuple)):
        opts = [opts]

    rows = current.db(table.id.belongs(opts)).select()
    rstr = Storage([(str(row.id), row) for row in rows])
    keys = rstr.keys()
    represent = lambda o: str(o) in keys and \
                          represent_string % rstr[str(o)] or \
                          current.messages.UNKNOWN_OPT
    vals = [represent(o) for o in opts]

    if len(opts) > 1:
        vals = ", ".join(vals)
    else:
        vals = len(vals) and vals[0] or DEFAULT

    return vals

# =============================================================================
def multi_activity_represent(opt):
    """
        Activity representation
        for multiple=True options
    """

    if not opt:
        return current.messages.NONE

    table = current.s3db.project_activity
    set = current.db(table.id > 0).select(table.id,
                                          table.name).as_dict()

    if not set:
        return current.messages.NONE

    if isinstance(opt, (list, tuple)):
        opts = opt
        try:
            vals = [str(set.get(o)["name"]) for o in opts]
        except:
            return None
    elif isinstance(opt, int):
        opts = [opt]
        vals = str(set.get(opt)["name"])
    else:
        return current.messages.NONE

    if len(opts) > 1:
        vals = ", ".join(vals)
    else:
        vals = len(vals) and vals[0] or ""
    return vals

# =============================================================================
def multi_theme_percentage_represent(id):
    """
        Representation for Theme Percentages
        for multiple=True options
    """

    if not id:
        return current.messages.NONE

    s3db = current.s3db
    table = s3db.project_theme_percentage
    ttable = s3db.project_theme

    def represent_row(row):
        return "%s (%s%s)" % (row.project_theme.name,
                              row.project_theme_percentage.percentage,
                              "%")

    if isinstance(id, (list, tuple)):
        query = (table.id.belongs(id)) & \
                (ttable.id == table.theme_id)
        rows = current.db(query).select(table.percentage,
                                        ttable.name)
        repr = ", ".join(represent_row(row) for row in rows)
        return repr
    else:
        query = (table.id == id) & \
                (ttable.id == table.theme_id)
        row = current.db(query).select(table.percentage,
                                       ttable.name).first()
        try:
            return represent_row(row)
        except:
            return current.messages.UNKNOWN_OPT

# =============================================================================
def project_location_represent(id, row=None):
    """
    """

    if row:
        return current.s3db.gis_location_lx_represent(row.location_id)
    else:
        return current.s3db.gis_location_lx_represent( 
               s3_get_db_field_value(tablename = "project_location",
                                     fieldname = "location_id",
                                     look_up_value = id)
                )

# =============================================================================
def task_notify(form):
    """
        If the task is assigned to someone then notify them
    """

    vars = form.vars
    try:
        pe_id = int(vars.pe_id)
    except TypeError, ValueError:
        return
    if form.record is None or (pe_id != form.record.pe_id):
        # Assignee has changed
        settings = current.deployment_settings
        if settings.has_module("msg"):
            # Notify assignee
            subject = "%s: Task assigned to you" % settings.get_system_name_short()
            url = "%s%s" % (settings.get_base_public_url(),
                            URL(c="project", f="task", args=vars.id))
            message = "You have been assigned a Task:\n\n%s\n\n%s\n\n%s" % \
                (url,
                 vars.name,
                 vars.description or "")
            current.msg.send_by_pe_id(pe_id, subject, message)
    return

# =============================================================================
class S3ProjectOrganisationVirtualFields:
    """ Virtual fields for the project_project table when multi_orgs=True """

    # -------------------------------------------------------------------------
    def organisation(self):
        """ Name of the lead organisation of the project """

        LEAD_ROLE = current.deployment_settings.get_project_organisation_lead_role()
        s3db = current.s3db
        otable = s3db.org_organisation
        ltable = s3db.project_organisation
        query = (ltable.deleted != True) & \
                (ltable.project_id == self.project_project.id) & \
                (ltable.role == LEAD_ROLE) & \
                (ltable.organisation_id == otable.id)
        org = current.db(query).select(otable.name,
                                       limitby=(0, 1)).first()
        if org:
            return org.name
        else:
            return None

    # -------------------------------------------------------------------------
    def total_organisation_amount(self):
        """ Total of project_organisation amounts for project"""

        potable = current.s3db.project_organisation
        query = (potable.deleted != True) & \
                (potable.project_id == self.project_project.id)
        sum_field = potable.amount.sum()
        return current.db(query).select(sum_field).first()[sum_field]

# =============================================================================
class S3ProjectBudgetVirtualFields:
    """ Virtual fields for the project_project table when multi_budgets=True """

    # -------------------------------------------------------------------------
    def total_annual_budget(self):
        """ Total of all annual budgets for project"""

        pabtable = current.s3db.project_annual_budget
        query = (pabtable.deleted != True) & \
                (pabtable.project_id == self.project_project.id)
        sum_field = pabtable.amount.sum()
        return current.db(query).select(sum_field).first()[sum_field]

# =============================================================================
class S3ProjectActivityVirtualFields:
    """ Virtual fields for the project_activity table """

    extra_fields = ["project_id", "location_id"]

    # -------------------------------------------------------------------------
    def organisation(self):
        """ Name of the lead organisation of the project """

        LEAD_ROLE = current.deployment_settings.get_project_organisation_lead_role()

        s3db = current.s3db
        otable = s3db.org_organisation
        ltable = s3db.project_organisation

        query = (ltable.deleted != True) & \
                (ltable.project_id == self.project_activity.project_id) & \
                (ltable.role == LEAD_ROLE) & \
                (ltable.organisation_id == otable.id)
        org = current.db(query).select(otable.name,
                                       limitby=(0, 1)).first()
        if org:
            return org.name
        else:
            return None

    # -------------------------------------------------------------------------
    def L0(self):
        parents = Storage()
        parents = current.gis.get_parent_per_level(parents,
                                                   self.project_activity.location_id,
                                                   ids=False,
                                                   names=True)
        if "L0" in parents:
            return parents["L0"]
        else:
            return None

    # -------------------------------------------------------------------------
    def L1(self):
        parents = Storage()
        parents = current.gis.get_parent_per_level(parents,
                                                   self.project_activity.location_id,
                                                   ids=False,
                                                   names=True)
        if "L1" in parents:
            return parents["L1"]
        else:
            return None

    # -------------------------------------------------------------------------
    def L2(self):
        parents = Storage()
        parents = current.gis.get_parent_per_level(parents,
                                                   self.project_activity.location_id,
                                                   ids=False,
                                                   names=True)
        if "L2" in parents:
            return parents["L2"]
        else:
            return None

    # -------------------------------------------------------------------------
    def L3(self):
        parents = Storage()
        parents = current.gis.get_parent_per_level(parents,
                                                   self.project_activity.location_id,
                                                   ids=False,
                                                   names=True)
        if "L3" in parents:
            return parents["L3"]
        else:
            return None

# =============================================================================
class S3ProjectLocationVirtualFields:
    """ Virtual fields for the project_location table """

    extra_fields = ["project_id", "location_id"]

    # -------------------------------------------------------------------------
    def organisation(self):
        """ Name of the lead organisation of the project """

        LEAD_ROLE = current.deployment_settings.get_project_organisation_lead_role()

        s3db = current.s3db
        otable = s3db.org_organisation
        ltable = s3db.project_organisation
        query = (ltable.deleted != True) & \
                (ltable.project_id == self.project_location.project_id) & \
                (ltable.role == LEAD_ROLE) & \
                (ltable.organisation_id == otable.id)
        org = current.db(query).select(otable.name,
                                       limitby=(0, 1)).first()
        if org:
            return org.name
        else:
            return None

    # -------------------------------------------------------------------------
    # def themes(self):
        # """ Themes of the project """

        # s3db = current.s3db
        # ttable = s3db.project_theme
        # themes = None
        # if current.deployment_settings.get_project_theme_percentages():
            # tptable = s3db.project_theme_percentage
            # query = (tptable.project_id == self.project_location.project_id) & \
                    # (ttable.id == tptable.theme_id)
            # themes = current.db(query).select(ttable.name)
        # else:
            # db = current.db
            # # 1st pull-back the themes
            # ptable = s3db.project_project
            # query = (ptable.id == self.project_location.project_id)
            # project = db(query).select(ptable.multi_theme_id,
                                       # limitby=(0, 1)).first()
            # if project and project.multi_theme_id:
                # theme_ids = [theme_id for theme_id in project.multi_theme_id]
                # query = (ttable.id.belongs(theme_ids))
                # themes = db(query).select(ttable.name)

        # if themes:
            # return [theme.name for theme in themes]
        # else:
            # return None

    # -------------------------------------------------------------------------
    def name(self):
        """
            Name for Map onHover popups
        """

        record = self.project_location
        if current.deployment_settings.get_project_community():
            # Community is the primary resource
            location = current.s3db.gis_location_lx_represent(record.location_id)
            return location
        else:
            # Location is just a way to display Projects
            location = current.s3db.gis_location_lx_represent(record.location_id)
            project = project_project_represent(record.project_id, show_link=False)
            return "%s (%s)" % (project, location)

# =============================================================================
class S3ProjectBeneficiaryVirtualFields:
    """ Virtual fields for the project_beneficiary table """

    extra_fields = ["project_location_id",
                    "project_id",
                    "start_date",
                    "end_date"]

    # -------------------------------------------------------------------------
    @staticmethod
    def _get_project_location(project_location_id):
        """
            Get the location from the database for this project_location and
            return the location tree
        """

        ctable = current.s3db.project_location
        query = (ctable.id == project_location_id)
        project_location = current.db(query).select(ctable.location_id,
                                                    limitby=(0,1)).first()

        parents = Storage()
        if project_location:
            parents = current.gis.get_parent_per_level(parents,
                                                       project_location.location_id,
                                                       ids=False,
                                                       names=True)

        return parents

    # -------------------------------------------------------------------------
    def L0(self):
        parents = self._get_project_location(self.project_beneficiary.project_location_id)

        if "L0" in parents:
            return parents["L0"]
        else:
            return current.messages.NONE


    # -------------------------------------------------------------------------
    def L1(self):
        parents = self._get_project_location(self.project_beneficiary.project_location_id)

        if "L1" in parents:
            return parents["L1"]
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    def L2(self):
        parents = self._get_project_location(self.project_beneficiary.project_location_id)

        if "L2" in parents:
            return parents["L2"]
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    def L3(self):
        parents = self._get_project_location(self.project_beneficiary.project_location_id)

        if "L3" in parents:
            return parents["L3"]
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    def year(self):
        start_date = self.project_beneficiary.start_date
        end_date = self.project_beneficiary.end_date
        if not start_date or not end_date:
            project = current.s3db.project_project[self.project_beneficiary.project_id]
            if project:
                if not start_date:
                    start_date = project.start_date
                if not end_date:
                    end_date = project.end_date
        if not start_date or not end_date:
            return [start_date.year or end_date.year]
        return [year for year in xrange(start_date.year, end_date.year + 1)]

# =============================================================================
class S3ProjectCommunityContactVirtualFields:
    """ Virtual fields for the project_community_contact table """

    extra_fields = ["person_id"]

    # -------------------------------------------------------------------------
    def email(self):

        s3db = current.s3db
        ptable = s3db.pr_person
        ctable = s3db.pr_contact

        person_id = self.project_community_contact.person_id
        query = (ctable.deleted != True) & \
                (ptable.id == person_id) & \
                (ctable.pe_id == ptable.pe_id) & \
                (ctable.contact_method == "EMAIL")
        items = current.db(query).select(ctable.value)
        return ", ".join([item.value for item in items])

    # -------------------------------------------------------------------------
    def sms(self):

        s3db = current.s3db
        ptable = s3db.pr_person
        ctable = s3db.pr_contact

        person_id = self.project_community_contact.person_id
        query = (ctable.deleted != True) & \
                (ptable.id == person_id) & \
                (ctable.pe_id == ptable.pe_id) & \
                (ctable.contact_method == "SMS")
        items = current.db(query).select(ctable.value)
        return ", ".join([item.value for item in items])

# =============================================================================
class S3ProjectThemeVirtualFields:
    """ Virtual fields for the project table """

    extra_fields = []

    # -------------------------------------------------------------------------
    def themes(self):
        """
            Themes associated with this Project
        """

        s3db = current.s3db
        ptable = s3db.project_project
        ttable = s3db.project_theme
        ltable = s3db.project_theme_percentage
        query = (ltable.deleted != True) & \
                (ltable.project_id == self.project_project.id) & \
                (ltable.theme_id == ttable.id)
        themes = current.db(query).select(ttable.name,
                                          ltable.percentage)

        if not themes:
            return current.messages.NONE

        represent = ""
        for theme in themes:
            name = theme.project_theme.name
            percentage = theme.project_theme_percentage.percentage
            if represent:
                represent = "%s, %s (%s%s)" % (represent,
                                               name,
                                               percentage,
                                               "%")
            else:
                represent = "%s (%s%s)" % (name, percentage, "%")

        return represent

# =============================================================================
class S3ProjectTaskVirtualFields:
    """ Virtual fields for the project_task table """

    extra_fields = ["id",
                    "project_task_project:project_id$name",
                    "project_task_activity:activity_id$name"]

    # -------------------------------------------------------------------------
    def project(self):
        """
            Project associated with this task
        """

        try:
            return self.project_project.name
        except AttributeError:
            return None

    # -------------------------------------------------------------------------
    def activity(self):
        """
            Activity associated with this task
        """

        try:
            return self.project_activity.name
        except AttributeError:
            return None

    # -------------------------------------------------------------------------
    def task_id(self):

        try:
            return self.project_task.id
        except AttributeError:
            return None

# =============================================================================
class S3ProjectTimeVirtualFields:
    """ Virtual fields for the project_time table """

    extra_fields = ["task_id", "person_id", "date"]

    # -------------------------------------------------------------------------
    def project(self):
        """
            Project associated with this time entry
            - used by the 'Project Time' report
        """

        s3db = current.s3db
        ptable = s3db.project_project
        ltable = s3db.project_task_project
        query = (ltable.deleted != True) & \
                (ltable.task_id == self.project_time.task_id) & \
                (ltable.project_id == ptable.id)
        project = current.db(query).select(ptable.name,
                                           limitby=(0, 1)).first()
        if project:
            return project.name
        else:
            return None

    # -------------------------------------------------------------------------
    def day(self):
        """
            Day of the last Week this time entry relates to
            - used by the 'Last Week's Work' report
        """

        thisdate = self.project_time.date

        if not thisdate:
            return "-"

        now = current.request.utcnow
        week = datetime.timedelta(days=7)
        if thisdate < (now - week):
            # Ignore data older than the last week
            # - should already be filtered in controller anyway
            return "-"

        return thisdate.date().strftime("%d %B")

# =============================================================================
def project_ckeditor():
    """ Load the Project Comments JS """

    s3 = current.response.s3

    ckeditor = URL(c="static", f="ckeditor", args="ckeditor.js")
    s3.scripts.append(ckeditor)
    adapter = URL(c="static", f="ckeditor", args=["adapters", "jquery.js"])
    s3.scripts.append(adapter)

    # Toolbar options: http://docs.cksource.com/CKEditor_3.x/Developers_Guide/Toolbar
    js = "".join((
'''S3.i18n.reply="''', str(current.T("Reply")), '''"
var img_path=S3.Ap.concat('/static/img/jCollapsible/')
var ck_config={toolbar:[['Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Smiley','-','Source','Maximize']],toolbarCanCollapse:false,removePlugins:'elementspath'}
function comment_reply(id){
 $('#project_comment_task_id__row').hide()
 $('#project_comment_task_id__row1').hide()
 $('#comment-title').html(S3.i18n.reply)
 $('#project_comment_body').ckeditorGet().destroy()
 $('#project_comment_body').ckeditor(ck_config)
 $('#comment-form').insertAfter($('#comment-'+id))
 $('#project_comment_parent').val(id)
 var task_id = $('#comment-'+id).attr('task_id')
 $('#project_comment_task_id').val(task_id)
}'''))

    s3.js_global.append(js)

# =============================================================================
def project_rheader(r, tabs=[]):
    """ Project Resource Headers - used in Project & Budget modules """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None
    record = r.record
    if record is None:
        # List or Create form: rheader makes no sense here
        return None

    table = r.table
    resourcename = r.name
    T = current.T
    auth = current.auth
    settings = current.deployment_settings

    if resourcename == "project":
        mode_3w = settings.get_project_mode_3w()
        mode_task = settings.get_project_mode_task()

        # Tabs
        ADMIN = current.session.s3.system_roles.ADMIN
        admin = auth.s3_has_role(ADMIN)
        #staff = auth.s3_has_role("STAFF")
        staff = True

        tabs = [(T("Basic Details"), None)]
        append = tabs.append
        if settings.get_project_multiple_organisations():
            append((T("Organizations"), "organisation"))
        if settings.get_project_theme_percentages():
            append((T("Themes"), "theme_percentage"))
        if mode_3w:
            if settings.get_project_community():
                append((T("Communities"), "location"))
            else:
                append((T("Locations"), "location"))
            append((T("Beneficiaries"), "beneficiary"))
        if settings.get_project_milestones():
            append((T("Milestones"), "milestone"))
        if settings.get_project_activities():
            append((T("Activities"), "activity"))
        if mode_task:
            append((T("Tasks"), "task"))
        if record.calendar:
            append((T("Calendar"), "timeline"))
        if settings.get_project_multiple_budgets():
            append((T("Annual Budgets"), "annual_budget"))
        if mode_3w:
            append((T("Documents"), "document"))
        else:
            append((T("Attachments"), "document"))
        if settings.get_hrm_show_staff():
            append((T("Staff"), "human_resource", dict(group="staff")))
        if settings.has_module("vol"):
            append((T("Volunteers"), "human_resource", dict(group="volunteer")))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        tbl = TABLE()
        append = tbl.append
        fields = ["code", "name", "organisation_id", "countries_id", "start_date", "end_date"]
        for field in fields:
            _field = table[field]
            if _field.readable and record[field]:
                represent = _field.represent(record[field]) if _field.represent else record[field]
                append(TR(
                            TH("%s: " % _field.label),
                            represent
                    ))

        rheader = DIV(tbl, rheader_tabs)

    elif resourcename == "location":
        tabs = [(T("Details"), None),
                (T("Beneficiaries"), "beneficiary"),
                (T("Contact People"), "contact"),
                ]
        rheader_fields = []
        if record.project_id is not None:
            rheader_fields.append(["project_id"])
        rheader_fields.append(["location_id"])
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "framework":
        tabs = [(T("Details"), None),
                (T("Organizations"), "organisation"),
                (T("Documents"), "document")]
        rheader_fields = [["name"]]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "activity":
        tabs = [(T("Details"), None),
                (T("Contact Persons"), "contact")]
        if settings.get_project_mode_task():
            tabs.append((T("Tasks"), "task"))
            tabs.append((T("Attachments"), "document"))
        else:
            tabs.append((T("Documents"), "document"))
        rheader_fields = []
        if record.project_id is not None:
            rheader_fields.append(["project_id"])
        rheader_fields.append(["name"])
        rheader_fields.append(["location_id"])
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "task":
        db = current.db
        s3db = current.s3db

        # Tabs
        tabs = [(T("Details"), None)]
        append = tabs.append
        staff = auth.s3_has_role("STAFF")
        if staff:
            append((T("Time"), "time")),
        append((T("Attachments"), "document"))
        if settings.has_module("msg"):
            append((T("Notify"), "dispatch"))
        #(T("Roles"), "job_role"),
        #(T("Assignments"), "human_resource"),
        #(T("Requests"), "req")

        rheader_tabs = s3_rheader_tabs(r, tabs)

        # RHeader
        ptable = s3db.project_project
        ltable = s3db.project_task_project
        query = (ltable.deleted == False) & \
                (ltable.task_id == r.id) & \
                (ltable.project_id == ptable.id)
        project = db(query).select(ptable.code,
                                   ptable.name,
                                   limitby=(0, 1)).first()
        if project:
            project = TR(
                            TH("%s: " % T("Project")),
                            project_project_represent(id=None,
                                                      row=project)
                        )
        else:
            project = ""

        atable = s3db.project_activity
        ltable = s3db.project_task_activity
        query = (ltable.deleted == False) & \
                (ltable.task_id == r.id) & \
                (ltable.activity_id == atable.id)
        activity = db(query).select(atable.name,
                                    limitby=(0, 1)).first()
        if activity:
            activity = TR(
                            TH("%s: " % T("Activity")),
                            activity.name
                        )
        else:
            activity = ""

        if record.description:
            description = TR(
                            TH("%s: " % table.description.label),
                            record.description
                        )
        else:
            description = ""

        if record.site_id:
            facility = TR(
                            TH("%s: " % table.site_id.label),
                            table.site_id.represent(record.site_id),
                        )
        else:
            facility = ""

        if record.location_id:
            location = TR(
                            TH("%s: " % table.location_id.label),
                            table.location_id.represent(record.location_id),
                        )
        else:
            location = ""

        if record.pe_id:
            assignee = TR(
                            TH("%s: " % table.pe_id.label),
                            s3db.pr_pentity_represent(record.pe_id,
                                                      show_label=False),
                        )
        else:
            assignee = ""

        if record.created_by:
            creator = TR(
                            TH("%s: " % T("Created by")),
                            s3db.pr_pentity_represent(record.created_by, show_label=False),
                        )
        else:
            creator = ""

        if record.time_estimated:
            time_estimated = TR(
                            TH("%s: " % table.time_estimated.label),
                            record.time_estimated
                        )
        else:
            time_estimated = ""

        if record.time_actual:
            time_actual = TR(
                            TH("%s: " % table.time_actual.label),
                            record.time_actual
                        )
        else:
            time_actual = ""

        rheader = DIV(TABLE(
            project,
            activity,
            TR(
                TH("%s: " % table.name.label),
                record.name,
                ),
            description,
            facility,
            location,
            assignee,
            creator,
            time_estimated,
            time_actual,
            #comments,
            ), rheader_tabs)

    return rheader

# =============================================================================
def project_task_controller():
    """
        Tasks Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    T = current.T
    auth = current.auth
    request = current.request
    session = current.session
    s3 = current.response.s3
    db = current.db
    s3db = current.s3db

    # Load model
    tablename = "project_task"
    table = s3db[tablename]
    statuses = s3.project_task_active_statuses
    crud_strings = s3.crud_strings[tablename]
    if "mine" in request.get_vars:
        # Show the Open Tasks for this User
        crud_strings.title_list = T("My Open Tasks")
        crud_strings.msg_list_empty = T("No Tasks Assigned")
        s3db.configure(tablename,
                       copyable=False,
                       listadd=False)
        try:
            # Add Virtual Fields
            list_fields = s3db.get_config(tablename,
                                          "list_fields")
            list_fields.insert(4, (T("Project"), "project"))
            # Hide the Assignee column (always us)
            list_fields.remove("pe_id")
            # Hide the Status column (always 'assigned' or 'reopened')
            list_fields.remove("status")
            s3db.configure(tablename,
                           list_fields=list_fields)
        except:
            pass
        if auth.user:
            pe_id = auth.user.pe_id
            s3.filter = (table.pe_id == pe_id) & \
                        (table.status.belongs(statuses))
    elif "project" in request.get_vars:
        # Show Open Tasks for this Project
        project = request.get_vars.project
        ptable = s3db.project_project
        try:
            name = db(ptable.id == project).select(ptable.name,
                                                   limitby=(0, 1)).first().name
        except:
            session.error = T("Project not Found")
            redirect(URL(args=None, vars=None))
        crud_strings.title_list = T("Open Tasks for %(project)s") % dict(project=name)
        crud_strings.title_search = T("Search Open Tasks for %(project)s") % dict(project=name)
        crud_strings.msg_list_empty = T("No Open Tasks for %(project)s") % dict(project=name)
        # Add Virtual Fields
        list_fields = s3db.get_config(tablename,
                                      "list_fields")
        list_fields.insert(2, (T("Activity"), "activity"))
        s3db.configure(tablename,
                       # Block Add until we get the injectable component lookups
                       insertable=False,
                       deletable=False,
                       copyable=False,
                       #search_method=task_search,
                       list_fields=list_fields)
        ltable = s3db.project_task_project
        response.s3.filter = (ltable.project_id == project) & \
                             (ltable.task_id == table.id) & \
                             (table.status.belongs(statuses))
    else:
        crud_strings.title_list = T("All Tasks")
        crud_strings.title_search = T("All Tasks")
        list_fields = s3db.get_config(tablename,
                                      "list_fields")
        list_fields.insert(2, (T("Project"), "project"))
        list_fields.insert(3, (T("Activity"), "activity"))
        s3db.configure(tablename,
                       report_options=Storage(
                            search=[
                                S3SearchOptionsWidget(
                                    field="project",
                                    name="project",
                                    label=T("Project")
                                )
                            ]
                       ),
                       list_fields=list_fields
                       )
        if "open" in request.get_vars:
            # Show Only Open Tasks
            crud_strings.title_list = T("All Open Tasks")
            s3.filter = (table.status.belongs(statuses))

    # Pre-process
    def prep(r):
        if r.interactive:
            if r.record:
                # Put the Comments in the RFooter
                project_ckeditor()
                s3.rfooter = LOAD("project", "comments.load",
                                  args=[r.id],
                                  ajax=True)
            if r.component:
                if r.component_name == "req":
                    if current.deployment_settings.has_module("hrm"):
                        r.component.table.type.default = 3
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        s3db.req_create_form_mods()
                elif r.component_name == "human_resource":
                    r.component.table.type.default = 2
            else:
                if not auth.s3_has_role("STAFF"):
                    # Hide fields to avoid confusion (both of inputters & recipients)
                    table = r.table
                    field = table.source
                    field.readable = field.writable = False
                    field = table.pe_id
                    field.readable = field.writable = False
                    field = table.date_due
                    field.readable = field.writable = False
                    field = table.milestone_id
                    field.readable = field.writable = False
                    field = table.time_estimated
                    field.readable = field.writable = False
                    field = table.time_actual
                    field.readable = field.writable = False
                    field = table.status
                    field.readable = field.writable = False
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if r.method != "import":
                update_url = URL(args=["[id]"], vars=request.get_vars)
                current.manager.crud.action_buttons(r,
                                                    update_url=update_url)
                if not r.component and \
                   r.method != "search" and \
                   "form" in output:
                    # Insert fields to control the Project & Activity
                    sep = ": "
                    if auth.s3_has_role("STAFF"):
                        # Activity not easy for non-Staff to know about, so don't add
                        table = s3db.project_task_activity
                        field = table.activity_id
                        if r.id:
                            query = (table.task_id == r.id)
                            default = db(query).select(table.activity_id,
                                                       limitby=(0, 1)).first()
                            if default:
                                default = default.activity_id
                        else:
                            default = field.default
                        widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                        field_id = "%s_%s" % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, label and sep, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        activity = s3.crud.formstyle(row_id, label, widget, field.comment)
                        try:
                            output["form"][0].insert(0, activity[1])
                        except:
                            # A non-standard formstyle with just a single row
                            pass
                        try:
                            output["form"][0].insert(0, activity[0])
                        except:
                            pass
                        s3.scripts.append("/%s/static/scripts/S3/s3.project.js" % \
                            current.request.application)
                    if "project" in request.get_vars:
                        widget = INPUT(value=request.get_vars.project, _name="project_id")
                        project = s3.crud.formstyle("project_task_project__row", "", widget, "")
                    else:
                        table = s3db.project_task_project
                        field = table.project_id
                        if r.id:
                            query = (table.task_id == r.id)
                            default = db(query).select(table.project_id,
                                                       limitby=(0, 1)).first()
                            if default:
                                default = default.project_id
                        else:
                            default = field.default
                        widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                        field_id = "%s_%s" % (table._tablename, field.name)
                        label = field.label
                        label = LABEL(label, label and sep, _for=field_id,
                                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                        comment = field.comment if auth.s3_has_role("STAFF") else ""
                        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                        project = s3.crud.formstyle(row_id, label, widget, comment)
                    try:
                        output["form"][0].insert(0, project[1])
                    except:
                        # A non-standard formstyle with just a single row
                        pass
                    try:
                        output["form"][0].insert(0, project[0])
                    except:
                        pass

        return output
    s3.postp = postp

    return current.rest_controller("project", "task",
                                   rheader=s3db.project_rheader)

# END =========================================================================
