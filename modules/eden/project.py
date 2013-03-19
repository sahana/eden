# -*- coding: utf-8 -*-

""" Sahana Eden Project Model

    @copyright: 2011-2013 (c) Sahana Software Foundation
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
           "S3ProjectActivityModel",
           "S3ProjectActivityTypeModel",
           "S3ProjectAnnualBudgetModel",
           "S3ProjectBeneficiaryModel",
           "S3ProjectFrameworkModel",
           "S3ProjectHazardModel",
           "S3ProjectLocationModel",
           "S3ProjectOrganisationModel",
           "S3ProjectSectorModel",
           "S3ProjectThemeModel",
           "S3ProjectDRRModel",
           "S3ProjectDRRPPModel",
           "S3ProjectTaskModel",
           "S3ProjectTaskHRMModel",
           "S3ProjectTaskIReportModel",
           "project_location_represent",
           "project_rheader",
           "project_task_form_inject",
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

        There are also a number of other deployment_settings to control behaviour

        This class contains the tables common to all uses
        There are additional tables in other Models
    """

    names = ["project_status",
             "project_project",
             "project_project_id",
             "project_human_resource",
             "project_hfa_opts",
             "project_jnap_opts",
             "project_pifacc_opts",
             "project_rfa_opts",
             "project_theme_opts",
             "project_theme_helps",
             "project_hazard_opts",
             "project_hazard_helps",
             ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        #NONE = current.messages["NONE"]

        human_resource_id = self.hrm_human_resource_id

        settings = current.deployment_settings
        mode_3w = settings.get_project_mode_3w()
        mode_task = settings.get_project_mode_task()
        mode_drr = settings.get_project_mode_drr()
        use_codes = settings.get_project_codes()
        use_sectors = settings.get_project_sectors()
        multi_budgets = settings.get_project_multiple_budgets()
        multi_orgs = settings.get_project_multiple_organisations()

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Project Statuses
        #
        tablename = "project_status"
        table = define_table(tablename,
                             Field("name", length=128,
                                   notnull=True, unique=True,
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_STATUS = T("Add Status")
        crud_strings[tablename] = Storage(
            title_create = ADD_STATUS,
            title_display = T("Status Details"),
            title_list = T("Statuses"),
            title_update = T("Edit Status"),
            title_upload = T("Import Statuses"),
            subtitle_create = T("Add New Status"),
            label_list_button = T("List Statuses"),
            label_create_button = ADD_STATUS,
            label_delete_button = T("Delete Status"),
            msg_record_created = T("Status added"),
            msg_record_modified = T("Status updated"),
            msg_record_deleted = T("Status deleted"),
            msg_list_empty = T("No Statuses currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename)
        status_id = S3ReusableField("status_id", table,
                                    label = T("Status"),
                                    sortby = "name",
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "project_status.id",
                                                          represent,
                                                          sort=True)),
                                    represent = represent,
                                    comment = S3AddResourceLink(title=ADD_STATUS,
                                                                c="project",
                                                                f="status"),
                                    ondelete = "SET NULL")

        # ---------------------------------------------------------------------
        # Projects
        #

        LEAD_ROLE = settings.get_project_organisation_lead_role()
        org_label = settings.get_project_organisation_roles()[LEAD_ROLE]

        tablename = "project_project"
        table = define_table(tablename,
                             self.super_link("doc_id", "doc_entity"),
                             # multi_orgs deployments use the separate project_organisation table
                             # - although Lead Org is still cached here to avoid the need for a virtual field to lookup
                             self.org_organisation_id(
                                label = org_label,
                                default = auth.root_org(),
                                requires = self.org_organisation_requires(
                                    required = True,
                                    # Only allowed to add Projects for Orgs that the user has write access to
                                    updateable = True,
                                    ),
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
                                   label = T("Short Title / ID"),
                                   readable = use_codes,
                                   writable = use_codes,
                                   ),
                             Field("description", "text",
                                   label = T("Description")),
                             status_id(),
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
                                   represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)),
                             s3_currency(
                                         readable = False if multi_budgets else True,
                                         writable = False if multi_budgets else True,
                                         ),
                             Field("objectives", "text",
                                   readable = mode_3w,
                                   writable = mode_3w,
                                   label = T("Objectives")),
                             human_resource_id(label=T("Contact Person")),
                             s3_comments(comment=DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Comments"),
                                                                       T("Outcomes, Impact, Challenges")))),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_PROJECT = T("Add Project")
        crud_strings[tablename] = Storage(
            title_create = ADD_PROJECT,
            title_display = T("Project Details"),
            title_list = T("Projects"),
            title_update = T("Edit Project"),
            title_search = T("Search Projects"),
            title_report = T("Project Report"),
            title_upload = T("Import Projects"),
            subtitle_create = T("Add New Project"),
            label_list_button = T("List Projects"),
            label_create_button = ADD_PROJECT,
            label_delete_button = T("Delete Project"),
            msg_record_created = T("Project added"),
            msg_record_modified = T("Project updated"),
            msg_record_deleted = T("Project deleted"),
            msg_list_empty = T("No Projects currently registered"))

        # Search Method
        simple = [
            S3SearchSimpleWidget(name = "project_search_text_advanced",
                                 label = T("Description"),
                                 comment = T("Search for a Project by name, code, or description."),
                                 field = ["name",
                                          "code",
                                          "description",
                                          ]
                                 ),
            S3SearchOptionsWidget(
                name = "project_search_status",
                label = T("Status"),
                field = "status_id",
                cols = 4,
                )
            ]
        advanced = list(simple)
        append = advanced.append

        append(S3SearchOptionsWidget(
                    name = "project_search_organisation_id",
                    label = org_label,
                    field = "organisation_id",
                    cols = 3
                ))

        append(S3SearchOptionsWidget(
                name = "project_search_L0",
                field = "location.location_id$L0",
                location_level="L0",
                cols = 3
                ))
        append(S3SearchOptionsWidget(
                name = "project_search_L1",
                field = "location.location_id$L1",
                location_level="L1",
                cols = 3
                ))
            #append(S3SearchOptionsWidget(
            #        name = "project_search_L2",
            #        label = T("Countries"),
            #        field = "location.location_id$L2",
            #        location_level="L2",
            #        cols = 3
            #        ))

        if use_sectors:
            if settings.get_ui_label_cluster():
                sector = T("Cluster")
            else:
                sector = T("Sector")
            append(S3SearchOptionsWidget(
                        name = "project_search_sector",
                        label = sector,
                        field = "sector.name",
                        options = self.org_sector_opts,
                        cols = 4
                    ))
        if mode_drr:
            append(S3SearchOptionsWidget(
                        name = "project_search_hazard",
                        label = T("Hazard"),
                        field = "hazard.name",
                        options = self.project_hazard_opts,
                        help_field = self.project_hazard_helps,
                        cols = 4
                    ))
        if mode_3w:
            append(S3SearchOptionsWidget(
                        name = "project_search_theme",
                        label = T("Theme"),
                        field = "theme.name",
                        options = self.project_theme_opts,
                        help_field = self.project_theme_helps,
                        cols = 4
                    ))
        if mode_drr:
            project_hfa_opts = self.project_hfa_opts()
            options = {}
            #options = {None:NONE} To search NO HFA
            for key in project_hfa_opts.keys():
                options[key] = "HFA %s" % key
            append(S3SearchOptionsWidget(
                        name = "project_search_hfa",
                        label = T("HFA"),
                        field = "drr.hfa",
                        options = options,
                        help_field = project_hfa_opts,
                        cols = 5
                    ))

        if multi_orgs:
            append(S3SearchOptionsWidget(
                        name = "project_search_partners",
                        field = "partner.organisation_id",
                        label = T("Partners"),
                        cols = 3,
                    ))

            append(S3SearchOptionsWidget(
                        name = "project_search_donors",
                        field = "donor.organisation_id",
                        label = T("Donors"),
                        cols = 3,
                    ))

        project_search = S3Search(simple = simple,
                                  advanced = advanced)

        # Resource Configuration
        if settings.get_project_theme_percentages():
            create_next = URL(c="project", f="project",
                              args=["[id]", "theme"])
        elif mode_task:
            if settings.get_project_milestones():
                create_next = URL(c="project", f="project",
                                  args=["[id]", "milestone"])
            else:
                create_next = URL(c="project", f="project",
                                  args=["[id]", "task"])
        else:
            # Default
            create_next = None

        list_fields = ["id"]
        append = list_fields.append
        if use_codes:
            append("code")
        append("name")
        append("organisation_id")
        if mode_3w:
            append((T("Locations"), "location.location_id"))
        if use_sectors:
            append((T("Sectors"), "sector.name"))
        if mode_drr:
            append((T("Hazards"), "hazard.name"))
            #append("drr.hfa")
        append((T("Themes"), "theme.name"))
        if multi_orgs:
            table.virtualfields.append(S3ProjectOrganisationFundingVirtualFields())
            append((T("Total Funding Amount"), "total_organisation_amount"))
        if multi_budgets:
            table.virtualfields.append(S3ProjectBudgetVirtualFields())
            append((T("Total Annual Budget"), "total_annual_budget"))
        append("start_date")
        append("end_date")

        report_fields = list_fields
        report_col_default = "location.location_id"
        report_fact_fields = [(field, "count") for field in report_fields]
        report_fact_default = "project.organisation_id"
        #report_fact_default = "theme.name"

        configure(tablename,
                  super_entity="doc_entity",
                  deduplicate=self.project_project_deduplicate,
                  onaccept=self.project_project_onaccept,
                  create_next=create_next,
                  search_method=project_search,
                  list_fields=list_fields,
                  report_options=Storage(
                    search=advanced,
                    rows=report_fields,
                    cols=report_fields,
                    fact=report_fact_fields,
                    defaults=Storage(
                        rows="hazard.name",
                        cols=report_col_default,
                        fact=report_fact_default,
                        aggregate="count",
                        totals=True
                    )
                  ),
                  realm_components = ["human_resource",
                                      "task",
                                      "organisation",
                                      "activity",
                                      "activity_type",
                                      "annual_budget",
                                      "beneficiary",
                                      "location",
                                      "milestone",
                                      "theme_percentage",
                                      "document",
                                      "image",
                                      ],
                  update_realm=True,
                  )

        # Reusable Field
        project_id = S3ReusableField("project_id", table,
            sortby="name",
            requires = IS_NULL_OR(
                            IS_ONE_OF(db(auth.s3_accessible_query("update",
                                                                  table)),
                                      "project_project.id",
                                      lambda id, row:
                                        project_project_represent(id, row, show_link=False)
                                      )),
            represent = project_project_represent,
            comment = S3AddResourceLink(c="project", f="project",
                                        tooltip=T("If you don't see the project in the list, you can add a new one by clicking link 'Add Project'.")),
            label = T("Project"),
            ondelete = "CASCADE"
            )

        # Custom Methods
        set_method("project", "project",
                   method="timeline",
                   action=self.project_timeline)

        set_method("project", "project",
                   method="map",
                   action=self.project_map)

        # Components
        if multi_orgs:
            # Organisations
            add_component("project_organisation", project_project="project_id")
            # Donors
            add_component("project_organisation",
                          project_project=dict(
                            name="donor",
                            joinby="project_id",
                            filterby="role",
                            filterfor=["3"], # Works for IFRC & DRRPP
                          ))
            # Partners
            add_component("project_organisation",
                          project_project=dict(
                            name="partner",
                            joinby="project_id",
                            filterby="role",
                            filterfor=["2"], # Works for IFRC & DRRPP
                          ))

        # Sites
        #add_component("project_site", project_project="project_id")

        # Activities
        add_component("project_activity", project_project="project_id")
        
        # Activity Types
        add_component("project_activity_type",
                      project_project=Storage(link="project_activity_type_project",
                                              joinby="project_id",
                                              key="activity_type_id",
                                              actuate="link"))        

        # Milestones
        add_component("project_milestone", project_project="project_id")

        # Tasks
        add_component("project_task",
                      project_project=Storage(link="project_task_project",
                                              joinby="project_id",
                                              key="task_id",
                                              actuate="replace",
                                              autocomplete="name",
                                              autodelete=False))

        # Annual Budgets
        add_component("project_annual_budget", project_project="project_id")

        # Beneficiaries
        add_component("project_beneficiary", project_project="project_id")

        # Hazards
        add_component("project_hazard",
                      project_project=Storage(link="project_hazard_project",
                                              joinby="project_id",
                                              key="hazard_id",
                                              actuate="hide"))

        # Human Resources
        add_component("project_human_resource", project_project="project_id")

        # Locations
        add_component("project_location", project_project="project_id")

        # Sectors
        add_component("org_sector",
                      project_project=Storage(link="project_sector_project",
                                              joinby="project_id",
                                              key="sector_id",
                                              actuate="hide"))

        # Themes
        add_component("project_theme",
                      project_project=Storage(link="project_theme_project",
                                              joinby="project_id",
                                              key="theme_id",
                                              actuate="hide"))

        # DRR
        if mode_drr:
            add_component("project_drr",
                          project_project=Storage(joinby="project_id",
                                                  multiple = False))

        # ---------------------------------------------------------------------
        # Project Human Resources
        #
        define_table("project_human_resource",
                     project_id(empty=False),
                     human_resource_id(empty=False),
                     *s3_meta_fields()
                     )

        configure("project_human_resource",
                  onvalidation=self.project_human_resource_onvalidation,
                  list_fields=[#"project_id",
                               "human_resource_id$person_id",
                               "human_resource_id$organisation_id",
                               "human_resource_id$job_title",
                               "human_resource_id$status"
                            ],
                        )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(
            project_project_id = project_id,
            project_hfa_opts = self.project_hfa_opts,
            project_jnap_opts = self.project_jnap_opts,
            project_pifacc_opts = self.project_pifacc_opts,
            project_rfa_opts = self.project_rfa_opts,
            project_theme_opts = self.project_theme_opts,
            project_theme_helps = self.project_theme_helps,
            project_hazard_opts = self.project_hazard_opts,
            project_hazard_helps = self.project_hazard_helps,
        )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for model-global names if module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable=False,
                                writable=False)

        return Storage(
                project_project_id = lambda: dummy("project_id"),
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_project_onaccept(form):
        """
            After DB I/O tasks for Project records
        """

        settings = current.deployment_settings
        if settings.get_project_multiple_organisations():
            # Create/update project_organisation record from the organisation_id
            # (Not in form.vars if added via component tab)
            vars = form.vars
            organisation_id = vars.organisation_id or \
                              current.request.post_vars.organisation_id
            if organisation_id:
                lead_role = settings.get_project_organisation_lead_role()

                otable = current.s3db.project_organisation
                query = (otable.project_id == vars.id) & \
                        (otable.role == lead_role)

                # Update the lead organisation
                count = current.db(query).update(organisation_id = organisation_id)
                if not count:
                    # If there is no record to update, then create a new one
                    otable.insert(project_id = vars.id,
                                  organisation_id = organisation_id,
                                  role = lead_role,
                                  )

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
            tptable = s3db.project_theme_project
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
                    "name"      : T("Projects"),
                    "id"        : "projects",
                    "tablename" : "project_location",
                    "url"       : url,
                    "active"    : True,
                    #"marker"   : None,
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
            Export Projects as GeoJSON Polygons to view on the map
            - currently assumes that theme_percentages=True
        """

        db = current.db
        s3db = current.s3db
        ptable = s3db.project_project
        ttable = s3db.project_theme
        tptable = s3db.project_theme_project
        pltable = s3db.project_location
        ltable = s3db.gis_location

        vars = current.request.get_vars

        themes = db(ttable.deleted == False).select(ttable.id,
                                                    ttable.name,
                                                    orderby = ttable.name)

        # Total the Budget spent by Theme for each country
        countries = {}
        query = (ptable.deleted == False) & \
                (tptable.project_id == ptable.id) & \
                (ptable.id == pltable.project_id) & \
                (ltable.id == pltable.location_id)

        #if "theme_id" in vars:
        #    query = query & (tptable.id.belongs(vars.theme_id))
        projects = db(query).select()
        for project in projects:
            # Only show those projects which are only within 1 country
            # @ToDo
            _countries = project.location_id
            if len(_countries) == 1:
                country = _countries[0]
                if country in countries:
                    budget = project.project_project.total_annual_budget
                    theme = project.project_theme_project.theme_id
                    percentage = project.project_theme_project.percentage
                    countries[country][theme] += budget * percentage
                else:
                    name = db(ltable.id == country).select(ltable.name).first().name
                    countries[country] = dict(name = name)
                    # Init all themes to 0
                    for theme in themes:
                        countries[country][theme.id] = 0
                    # Add value for this record
                    budget = project.project_project.total_annual_budget
                    theme = project.project_theme_project.theme_id
                    percentage = project.project_theme_project.percentage
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

    # -------------------------------------------------------------------------
    @staticmethod
    def project_hazard_opts():
        """
            Provide the options for the Hazard search filter
            - defined in the model used to ensure a good load order
        """

        table = current.s3db.project_hazard
        opts = current.db(table.deleted == False).select(table.id,
                                                         table.name,
                                                         orderby=table.name)
        T = current.T
        od = OrderedDict()
        for opt in opts:
            od[opt.id] = T(opt.name) if opt.name else ""
        return od

    # -------------------------------------------------------------------------
    @staticmethod
    def project_hazard_helps():
        """
            Provide the help tooltips for the Hazard search filter
            - defined in the model used to ensure a good load order
        """

        table = current.s3db.project_hazard
        opts = current.db(table.deleted == False).select(table.id,
                                                         table.comments)
        T = current.T
        d = {}
        for opt in opts:
            d[opt.id] = T(opt.comments) if opt.comments else ""
        return d

    # -------------------------------------------------------------------------
    @staticmethod
    def project_hfa_opts():
        """
            Provide the options for the HFA search filter
            - defined in the model used to ensure a good load order

            HFA: Hyogo Framework Agreement
        """

        T = current.T
        return {
            1: T("HFA1: Ensure that disaster risk reduction is a national and a local priority with a strong institutional basis for implementation."),
            2: T("HFA2: Identify, assess and monitor disaster risks and enhance early warning."),
            3: T("HFA3: Use knowledge, innovation and education to build a culture of safety and resilience at all levels."),
            4: T("HFA4: Reduce the underlying risk factors."),
            5: T("HFA5: Strengthen disaster preparedness for effective response at all levels."),
        }

    # -------------------------------------------------------------------------
    @staticmethod
    def project_jnap_opts():
        """
            Provide the options for the PIFACC search filter (currently unused)
            - defined in the model used to ensure a good load order

            JNAP (Joint National Action Plan for Disaster Risk Management and Climate Change Adaptation):
             applies to Cook Islands only
        """

        T = current.T
        return {
            1: T("JNAP-1: Strategic Area 1: Governance"),
            2: T("JNAP-2: Strategic Area 2: Monitoring"),
            3: T("JNAP-3: Strategic Area 3: Disaster Management"),
            4: T("JNAP-4: Strategic Area 4: Risk Reduction and Climate Change Adaptation"),
        }

    # -------------------------------------------------------------------------
    @staticmethod
    def project_pifacc_opts():
        """
            Provide the options for the PIFACC search filter (currently unused)
            - defined in the model used to ensure a good load order

            PIFACC (Pacific Islands Framework for Action on Climate Change):
             applies to Pacific countries only
        """

        T = current.T
        return {
            1: T("PIFACC-1: Implementing Tangible, On-Ground Adaptation Measures"),
            2: T("PIFACC-2: Governance and Decision Making"),
            3: T("PIFACC-3: Improving our understanding of climate change"),
            4: T("PIFACC-4: Education, Training and Awareness"),
            5: T("PIFACC-5: Mitigation of Global Greenhouse Gas Emissions"),
            6: T("PIFACC-6: Partnerships and Cooperation"),
        }

    # -------------------------------------------------------------------------
    @staticmethod
    def project_rfa_opts():
        """
            Provide the options for the RFA search filter
            - defined in the model used to ensure a good load order

            RFA: applies to Pacific countries only
        """

        T = current.T
        return {
            1: T("RFA1: Governance-Organisational, Institutional, Policy and Decision Making Framework"),
            2: T("RFA2: Knowledge, Information, Public Awareness and Education"),
            3: T("RFA3: Analysis and Evaluation of Hazards, Vulnerabilities and Elements at Risk"),
            4: T("RFA4: Planning for Effective Preparedness, Response and Recovery"),
            5: T("RFA5: Effective, Integrated and People-Focused Early Warning Systems"),
            6: T("RFA6: Reduction of Underlying Risk Factors"),
        }

    # -------------------------------------------------------------------------
    @staticmethod
    def project_theme_opts():
        """
            Provide the options for the Theme search filter
            - defined in the model used to ensure a good load order
        """

        table = current.s3db.project_theme
        opts = current.db(table.deleted == False).select(table.id,
                                                         table.name,
                                                         orderby=table.name)
        T = current.T
        od = OrderedDict()
        for opt in opts:
            od[opt.id] = T(opt.name) if opt.name else ""
        return od

    # -------------------------------------------------------------------------
    @staticmethod
    def project_theme_helps():
        """
            Provide the help tooltips for the Theme search filter
            - defined in the model used to ensure a good load order
        """

        table = current.s3db.project_theme
        opts = current.db(table.deleted == False).select(table.id,
                                                         table.comments)
        T = current.T
        d = {}
        for opt in opts:
            d[opt.id] = T(opt.comments) if opt.comments else ""
        return d

# =============================================================================
class S3ProjectActivityModel(S3Model):
    """
        Project Activity Model

        This model holds the specific Activities for Projects
        - currently used in mode_task but not mode_3w
    """

    names = ["project_activity",
             "project_activity_id",
             "project_activity_activity_type",
             ]

    def model(self):

        T = current.T
        db = current.db

        add_component = self.add_component
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        settings = current.deployment_settings
        mode_task = settings.get_project_mode_task()

        # ---------------------------------------------------------------------
        # Project Activity
        #
        tablename = "project_activity"
        table = define_table(tablename,
                             self.super_link("doc_id", "doc_entity"),
                             self.project_project_id(),
                             Field("name",
                                   label = T("Short Description"),
                                   requires = IS_NOT_EMPTY()
                                   ),
                             self.gis_location_id(
                                widget = S3LocationSelectorWidget(hide_address=True)
                                ),
                             Field("time_estimated", "double",
                                   readable = mode_task,
                                   writable = mode_task,
                                   label = "%s (%s)" % (T("Time Estimate"),
                                                        T("hours"))
                                   ),
                             Field("time_actual", "double",
                                   readable = mode_task,
                                   # Gets populated from constituent Tasks
                                   writable = False,
                                   label = "%s (%s)" % (T("Time Taken"),
                                                        T("hours"))
                                   ),
                             s3_comments(),
                             *s3_meta_fields())
        # CRUD Strings
        ACTIVITY = T("Activity")
        ACTIVITY_TOOLTIP = T("If you don't see the activity in the list, you can add a new one by clicking link 'Add Activity'.")
        ADD_ACTIVITY = T("Add Activity")
        crud_strings[tablename] = Storage(
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

        # Search Method
        project_activity_search = S3Search(field="name")

        # Resource Configuration
        report_fields = []
        append = report_fields.append
        append((T("Project"), "project_id"))
        append((T("Activity"), "name"))
        append((T("Activity Type"), "activity_type.name"))
        if settings.get_project_sectors():
            append((T("Sector"), "project_id$sector.name"))
        append((T("Theme"), "project_id$theme.name"))
        if settings.get_project_mode_drr():
            append((T("Hazard"), "project_id$hazard.name"))
            append((T("HFA"), "project_id$drr.hfa"))
        list_fields = ["name",
                       "project_id",
                       "activity_type.name",
                       "comments"
                       ]
        if mode_task:
            list_fields.insert(3, "time_estimated")
            list_fields.insert(4, "time_actual")
            append((T("Time Estimated"), "time_estimated"))
            append((T("Time Actual"), "time_actual"))
            create_next = URL(c="project", f="activity",
                              args=["[id]", "task"])
        else:
            create_next = URL(c="project", f="activity", args=["[id]"])

        self.configure(tablename,
                       super_entity="doc_entity",
                       create_next=create_next,
                       search_method=project_activity_search,
                       deduplicate=self.project_activity_deduplicate,
                       report_options=Storage(
                                rows=report_fields,
                                cols=report_fields,
                                fact=report_fields,
                                defaults=Storage(
                                    rows="activity.project_id",
                                    cols="activity.name",
                                    fact="activity.time_actual",
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
                                                              self.project_activity_represent,
                                                              sort=True)),
                                      represent = self.project_activity_represent,
                                      label = ACTIVITY,
                                      comment = S3AddResourceLink(ADD_ACTIVITY,
                                                                  c="project", f="activity",
                                                                  tooltip=ACTIVITY_TOOLTIP),
                                      ondelete = "CASCADE")

        # Components

        # Activity Types
        add_component("project_activity_type",
                      project_activity=Storage(
                        link="project_activity_activity_type",
                        joinby="activity_id",
                        key="activity_type_id",
                        actuate="replace",
                        autocomplete="name",
                        autodelete=False))

        # Disabled until beneficiaries are updated to support both
        # communities and activities
        #add_component("project_beneficiary",
        #              project_activity="activity_id")

        # Tasks
        add_component("project_task",
                      project_activity=Storage(
                        link="project_task_activity",
                        joinby="activity_id",
                        key="task_id",
                        actuate="replace",
                        autocomplete="name",
                        autodelete=False))

        # ---------------------------------------------------------------------
        # Activity Type - Activity Link Table
        #
        tablename = "project_activity_activity_type"
        table = define_table(tablename,
                             activity_id(empty=False),
                             self.project_activity_type_id(empty=False),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("New Activity Type"),
            title_display = T("Activity Type"),
            title_list = T("Activity Types"),
            title_update = T("Edit Activity Type"),
            title_search = T("Search Activity Types"),
            title_upload = T("Import Activity Type data"),
            subtitle_create = T("Add New Activity Type"),
            label_list_button = T("List Activity Types"),
            label_create_button = T("Add Activity Type to Activity"),
            msg_record_created = T("Activity Type added to Activity"),
            msg_record_modified = T("Activity Type updated"),
            msg_record_deleted = T("Activity Type removed from Activity"),
            msg_list_empty = T("No Activity Types found for this Activity")
        )

        # Pass names back to global scope (s3.*)
        return dict(
            project_activity_id = activity_id,
        )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for model-global names if module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable=False,
                                writable=False)

        return Storage(
                project_activity_id = lambda: dummy("activity_id"),
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_represent(id, row=None):
        """
            Show activities with a prefix of the project code
        """

        if row:
            activity = row
            db = current.db
            # Fetch the project record
            ptable = db.project_project
            project = db(ptable.id == row.project_id).select(ptable.code,
                                                             limitby=(0, 1)).first()
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.project_activity
            ptable = db.project_project
            left = ptable.on(ptable.id == table.project_id)
            row = db(table.id == id).select(table.name,
                                            table.project_id,
                                            ptable.code,
                                            left=left,
                                            limitby=(0, 1)).first()
            try:
                project = row[ptable]
                activity = row[table]
            except:
                return current.messages.UNKNOWN_OPT

        if project and project.code:
            return "%s > %s" % (project.code, activity.name)
        else:
            return activity.name

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "project_activity":
            return
        data = item.data
        if "project_id" in data and "name" in data:
            # Match activity by project_id and name
            project_id = data.project_id
            name = data.name
            table = item.table
            query = (table.project_id == project_id) & \
                    (table.name == name)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectActivityTypeModel(S3Model):
    """
        Project Activity Type Model

        This model holds the Activity Types for Projects
        - it is useful where we don't have the details on the actual Activities,
          but just this summary of Types
    """

    names = ["project_activity_type",
             "project_activity_type_location",
             "project_activity_type_project",
             "project_activity_type_sector",
             "project_activity_type_id",
             ]

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Activity Types
        #
        tablename = "project_activity_type"
        table = define_table(tablename,
                             Field("name", length=128,
                                   notnull=True, unique=True),
                             s3_comments(),
                             *s3_meta_fields())

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

        # Reusable Fields
        represent = S3Represent(lookup=tablename)
        activity_type_id = S3ReusableField("activity_type_id", table,
                                           sortby = "name",
                                           requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "project_activity_type.id",
                                                                  represent,
                                                                  sort=True)),
                                           represent = represent,
                                           label = T("Activity Type"),
                                           comment = S3AddResourceLink(title=ADD_ACTIVITY_TYPE,
                                                                       c="project",
                                                                       f="activity_type",
                                                                       tooltip=T("If you don't see the type in the list, you can add a new one by clicking link 'Add Activity Type'.")),
                                           ondelete = "SET NULL")

        # Component (for Custom Form)
        self.add_component("project_activity_type_sector",
                           project_activity_type="activity_type_id")

        crud_form = S3SQLCustomForm(
                        "name",
                        # Sectors
                        S3SQLInlineComponent(
                            "activity_type_sector",
                            label=T("Sectors to which this Activity Type can apply"),
                            fields=["sector_id"],
                        ),
                    )

        self.configure(tablename,
                       crud_form=crud_form,
                       list_fields=["id",
                                    "name",
                                    (T("Sectors"), "activity_type_sector.sector_id"),
                                    "comments",
                                    ])

        # ---------------------------------------------------------------------
        # Activity Type - Sector Link Table
        #
        tablename = "project_activity_type_sector"
        table = define_table(tablename,
                             activity_type_id(empty=False),
                             self.org_sector_id(label="",
                                                empty=False),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Activity Type - Project Location Link Table
        #
        tablename = "project_activity_type_location"
        table = define_table(tablename,
                             activity_type_id(empty=False),
                             self.project_location_id(empty=False),
                             *s3_meta_fields())
        
        # ---------------------------------------------------------------------
        # Activity Type - Project Link Table
        #
        tablename = "project_activity_type_project"
        table = define_table(tablename,
                             activity_type_id(empty=False),
                             self.project_project_id(empty=False),
                             *s3_meta_fields())        

        crud_strings[tablename] = Storage(
            title_create = T("New Activity Type"),
            title_display = T("Activity Type"),
            title_list = T("Activity Types"),
            title_update = T("Edit Activity Type"),
            title_search = T("Search Activity Types"),
            title_upload = T("Import Activity Type data"),
            subtitle_create = T("Add New Activity Type"),
            label_list_button = T("List Activity Types"),
            label_create_button = T("Add Activity Type to Project Location"),
            msg_record_created = T("Activity Type added to Project Location"),
            msg_record_modified = T("Activity Type updated"),
            msg_record_deleted = T("Activity Type removed from Project Location"),
            msg_list_empty = T("No Activity Types found for this Project Location")
        )

        # Pass names back to global scope (s3.*)
        return dict(
            project_activity_type_id = activity_type_id,
        )

# =============================================================================
class S3ProjectAnnualBudgetModel(S3Model):
    """
        Project Budget Model

        This model holds the annual budget entries for projects
    """

    names = ["project_annual_budget",
             ]

    def model(self):

        T = current.T
        db = current.db

        # ---------------------------------------------------------------------
        # Annual Budgets
        #
        tablename = "project_annual_budget"
        self.define_table(tablename,
                          self.project_project_id(
                            requires=IS_ONE_OF(db, "project_project.id",
                                               lambda id, row:
                                                project_project_represent(id, row,
                                                                          show_link=False)
                                               )
                            ),
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
                          *s3_meta_fields())


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
                       list_fields=["id",
                                    "year",
                                    "amount",
                                    "currency",
                                    ]
                       )

        # Pass names back to global scope (s3.*)
        return dict(
            )

# =============================================================================
class S3ProjectBeneficiaryModel(S3Model):
    """
        Project Beneficiary Model
        - depends on Stats module
    """

    names = ["project_beneficiary_type",
             "project_beneficiary",
             ]

    def model(self):

        if not current.deployment_settings.has_module("stats"):
            # Beneficiary Model needs Stats module enabling
            return dict()

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Project Beneficiary Type
        #
        tablename = "project_beneficiary_type"
        table = define_table(tablename,
                             super_link("parameter_id", "stats_parameter"),
                             Field("name", length=128, unique=True,
                                   requires = IS_NOT_IN_DB(db,
                                                           "project_beneficiary_type.name")),
                             s3_comments("description",
                                         label = T("Description")),
                             *s3_meta_fields())

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

        # Resource Configuration
        configure(tablename,
                  super_entity = "stats_parameter",
                  )

        # ---------------------------------------------------------------------
        # Project Beneficiary
        #
        tablename = "project_beneficiary"
        table = define_table(tablename,
                             # Link Fields
                             # populated automatically
                             self.project_project_id(readable=False,
                                                     writable=False),
                             self.project_location_id(comment=None),

                             # Instance
                             super_link("data_id", "stats_data"),
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             super_link("parameter_id", "stats_parameter",
                                        label = T("Beneficiary Type"),
                                        instance_types = ["project_beneficiary_type"],
                                        represent = S3Represent(lookup="stats_parameter"),
                                        readable = True,
                                        writable = True,
                                        empty = False,
                                        comment = S3AddResourceLink(c="project",
                                                                    f="beneficiary_type",
                                                                    vars = dict(child = "parameter_id"),
                                                                    title=ADD_BNF_TYPE,
                                                                    tooltip=T("Please record Beneficiary according to the reporting needs of your project")),
                                        ),
                             # populated automatically
                             self.gis_location_id(readable = False,
                                                  writable = False),
                             # @ToDo: What is this used for?
                             self.stats_group_id(readable = False,
                                                 writable = False),
                             Field("value", "double",
                                   label = T("Quantity"),
                                   requires = IS_INT_IN_RANGE(0, 99999999),
                                   represent = lambda v: \
                                    IS_INT_AMOUNT.represent(v)),
                             s3_date("date",
                                     label = T("Start Date"),
                                     #empty = False,
                                     ),
                             s3_date("end_date",
                                     label = T("End Date"),
                                     #empty = False,
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

        # Resource Configuration
        report_fields = ["project_location_id",
                         (T("Beneficiary Type"), "parameter_id"),
                         "project_id",
                         (T("Year"), "year"),
                         "project_id$hazard.name",
                         "project_id$theme.name",
                         (current.messages.COUNTRY, "location_id$L0"),
                         "location_id$L1",
                         "location_id$L2",
                         "location_id$L3",
                         "location_id$L4",
                         ]

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
            pbmin = pbtable.date.min()
            p_start_date_min = db(pquery).select(pmin,
                                                 orderby=pmin,
                                                 limitby=(0, 1)).first()[pmin]
            pb_date_min = db(pbquery).select(pbmin,
                                             orderby=pbmin,
                                             limitby=(0, 1)).first()[pbmin]
            if p_start_date_min and pb_date_min:
                start_year = min(p_start_date_min,
                                 pb_date_min).year
            else:
                start_year = (p_start_date_min and p_start_date_min.year) or \
                             (pb_date_min and pb_date_min.year)

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
                  super_entity = "stats_data",
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
                            field="parameter_id",
                            name="parameter_id",
                            label=T("Beneficiary Type")
                        ),
                        # @ToDo: These do no work - no results are returned
                        S3SearchOptionsWidget(
                            field="year",
                            name="year",
                            label=T("Year"),
                            options = year_options
                        ),
                        S3SearchOptionsWidget(
                            name = "beneficiary_search_L1",
                            field = "location_id$L1",
                            location_level = "L1",
                            cols = 3,
                        ),
                    ],
                    rows=report_fields,
                    cols=report_fields,
                    fact=["value"],
                    methods=["sum"],
                    defaults=Storage(rows="beneficiary.project_id",
                                     cols="beneficiary.parameter_id",
                                     fact="beneficiary.value",
                                     aggregate="sum",
                                     totals=True
                                     )
                  )
                 )

        # Reusable Field
        #beneficiary_id = S3ReusableField("beneficiary_id", table,
        #                                 sortby="name",
        #                                 requires = IS_NULL_OR(
        #                                                IS_ONE_OF(db, "project_beneficiary.id",
        #                                                          self.project_beneficiary_represent,
        #                                                          sort=True)),
        #                                 represent = self.project_beneficiary_represent,
        #                                 label = T("Beneficiaries"),
        #                                 comment = S3AddResourceLink(c="project",
        #                                                             f="beneficiary",
        #                                                             title=ADD_BNF,
        #                                                             tooltip=\
        #                                    T("If you don't see the beneficiary in the list, you can add a new one by clicking link 'Add Beneficiary'.")),
        #                                 ondelete = "SET NULL")

        # Pass names back to global scope (s3.*)
        return dict(
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_type_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        if not id:
            return current.messages["NONE"]

        db = current.db
        table = db.project_beneficiary_type
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return current.T(r.name)
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_represent(id, row=None):
        """ FK representation """

        if row:
            return row.type
        if not id:
            return current.messages["NONE"]

        db = current.db
        table = db.project_beneficiary
        ttable = db.project_beneficiary_type
        query = (table.id == id) & \
                (ttable,)
        r = db(query).select(table.value,
                             ttable.name,
                             limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_onaccept(form):
        """
            Update project_beneficiary project & location from project_location_id
        """

        db = current.db
        btable = db.project_beneficiary
        ltable = db.project_location

        record_id = form.vars.id
        query = (btable.id == record_id) & \
                (ltable.id == btable.project_location_id)
        project_location = db(query).select(ltable.project_id,
                                            ltable.location_id,
                                            limitby=(0, 1)).first()
        if project_location:
            db(btable.id == record_id).update(
                    project_id = project_location.project_id,
                    location_id = project_location.location_id
                )
        return

    # ---------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "project_beneficiary":
            return

        data = item.data
        if "parameter_id" in data and \
           "project_location_id" in data:
            # Match beneficiary by type and activity_id
            table = item.table
            parameter_id = data.parameter_id
            project_location_id = data.project_location_id
            query = (table.parameter_id == parameter_id) & \
                    (table.project_location_id == project_location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3ProjectFrameworkModel(S3Model):
    """
        Project Framework Model
    """

    names = ["project_framework",
             "project_framework_organisation"
             ]

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        messages = current.messages
        ORGANISATION = messages.ORGANISATION
        ORGANISATIONS = T("Organization(s)")

        # ---------------------------------------------------------------------
        # Project Frameworks
        #
        tablename = "project_framework"
        table = define_table(tablename,
                             self.super_link("doc_id", "doc_entity"),
                             Field("name", unique=True,
                                   label = T("Name"),
                                   ),
                             s3_comments("description",
                                         label = T("Description"),
                                         comment=None,
                                         ),
                             Field("time_frame",
                                   represent = lambda v: v or messages.NONE,
                                   label = T("Time Frame"),
                                   ),
                             *s3_meta_fields())

        # CRUD Strings
        if current.deployment_settings.get_auth_record_approval():
            msg_record_created = T("Policy or Strategy added, awaiting administrator's approval")
        else:
            msg_record_created = T("Policy or Strategy added")
        crud_strings[tablename] = Storage(
            title_create = T("Add Policy or Strategy"),
            title_display = T("Policy or Strategy"),
            title_list = T("Policies & Strategies"),
            title_update = T("Edit Policy or Strategy"),
            title_search = T("Search Policies & Strategies"),
            title_upload = T("Import Policies & Strategies"),
            subtitle_create = T("Add New Policy or Strategy"),
            label_list_button = T("List Policies & Strategies"),
            label_create_button = T("Add Policy or Strategy"),
            msg_record_created = msg_record_created,
            msg_record_modified = T("Policy or Strategy updated"),
            msg_record_deleted = T("Policy or Strategy deleted"),
            msg_list_empty = T("No Policies or Strategies found")
        )

        crud_form = S3SQLCustomForm(
            "name",
            S3SQLInlineComponent(
                "framework_organisation",
                label = ORGANISATIONS,
                fields = ["organisation_id"],
            ),
            "description",
            "time_frame",
            S3SQLInlineComponent(
                "document",
                label = T("Files"),
                fields = ["file"],
                filterby = dict(field = "file",
                                options = "",
                                invert = True,
                                )
            ),
        )

        # search_method = S3Search(simple = S3SearchSimpleWidget(
                # name = "project_framework_search_text",
                # label = T("Name"),
                # comment = T("Search for a Policy or Strategy by name or description."),
                # field = ["name",
                         # "description",
                         # ]
            # ))
        
        self.configure(tablename,
                       super_entity="doc_entity",
                       crud_form = crud_form,
                       #search_method = search_method,
                       list_fields = ["name",
                                      (ORGANISATIONS, "framework_organisation.organisation_id"),
                                      "description",
                                      "time_frame",
                                      (T("Files"), "document.file"),
                                      ]
                       )

        represent = S3Represent(lookup=tablename)
        framework_id = S3ReusableField("framework_id", table,
                                       label = ORGANISATION,
                                       requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "project_framework.id",
                                                              represent
                                                              )),
                                       represent = represent,
                                       ondelete = "CASCADE",
                                       )

        self.add_component("project_framework_organisation",
                           project_framework="framework_id")

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
            title_display = ORGANISATION,
            title_list = T("Organizations"),
            title_update = T("Edit Organization"),
            title_search = T("Search Organizations"),
            subtitle_create = T("Add New Organization"),
            label_list_button = T("List Organizations"),
            label_create_button = T("Add Organization"),
            msg_record_created = T("Organization added to Policy/Strategy"),
            msg_record_modified = T("Organization updated"),
            msg_record_deleted = T("Organization removed from Policy/Strategy"),
            msg_list_empty = T("No Organizations found for this Policy/Strategy")
        )

        # Pass names back to global scope (s3.*)
        return dict(
        )

# =============================================================================
class S3ProjectHazardModel(S3Model):
    """
        Project Hazard Model
    """

    names = ["project_hazard",
             "project_hazard_project"
             ]

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Hazard
        #
        tablename = "project_hazard"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True, unique=True),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_HAZARD = T("Add Hazard")
        crud_strings[tablename] = Storage(
            title_create = ADD_HAZARD,
            title_display = T("Hazard Details"),
            title_list = T("Hazards"),
            title_update = T("Edit Hazard"),
            title_upload = T("Import Hazards"),
            subtitle_create = T("Add New Hazard"),
            label_list_button = T("List Hazards"),
            label_create_button = ADD_HAZARD,
            label_delete_button = T("Delete Hazard"),
            msg_record_created = T("Hazard added"),
            msg_record_modified = T("Hazard updated"),
            msg_record_deleted = T("Hazard deleted"),
            msg_list_empty = T("No Hazards currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename)
        hazard_id = S3ReusableField("hazard_id", table,
                                    sortby = "name",
                                    label = T("Hazards"),
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "project_hazard.id",
                                                          represent,
                                                          sort=True)),
                                    represent = represent,
                                    ondelete = "CASCADE",
                                    )

        # ---------------------------------------------------------------------
        # Projects <> Hazards Link Table
        #
        tablename = "project_hazard_project"
        define_table(tablename,
                     hazard_id(),
                     self.project_project_id(),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Hazard"),
            title_display = T("Hazard"),
            title_list = T("Hazards"),
            title_update = T("Edit Hazard"),
            title_search = T("Search Hazards"),
            title_upload = T("Import Hazard data"),
            subtitle_create = T("Add New Hazard"),
            label_list_button = T("List Hazards"),
            label_create_button = T("Add Hazard to Project"),
            msg_record_created = T("Hazard added to Project"),
            msg_record_modified = T("Hazard updated"),
            msg_record_deleted = T("Hazard removed from Project"),
            msg_list_empty = T("No Hazards found for this Project")
        )

        # Pass names back to global scope (s3.*)
        return dict(
            )

# =============================================================================
class S3ProjectSectorModel(S3Model):
    """
        Project Sector Model
    """

    names = ["project_sector_project",
             ]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Projects <> Sectors Link Table
        #
        tablename = "project_sector_project"
        self.define_table(tablename,
                          self.org_sector_id(empty=False),
                          self.project_project_id(empty=False),
                          *s3_meta_fields()
                          )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("New Sector"),
            title_display = T("Sector"),
            title_list = T("Sectors"),
            title_update = T("Edit Sector"),
            title_search = T("Search Sectors"),
            title_upload = T("Import Sector data"),
            subtitle_create = T("Add New Sector"),
            label_list_button = T("List Sectors"),
            label_create_button = T("Add Sector to Project"),
            msg_record_created = T("Sector added to Project"),
            msg_record_modified = T("Sector updated"),
            msg_record_deleted = T("Sector removed from Project"),
            msg_list_empty = T("No Sectors found for this Project")
        )

        # Pass names back to global scope (s3.*)
        return dict(
            )

# =============================================================================
class S3ProjectLocationModel(S3Model):
    """
        Project Location Model
        - these can simply be ways to display a Project on the Map
          or these can be 'Communities'
    """

    names = ["project_location",
             "project_location_id",
             "project_location_contact",
             "project_location_virtualfields",
             ]

    def model(self):

        T = current.T
        db = current.db

        settings = current.deployment_settings
        community = settings.get_project_community()

        messages = current.messages
        NONE = messages["NONE"]
        COUNTRY = messages.COUNTRY

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Project Location ('Community')
        #
        tablename = "project_location"
        table = define_table(tablename,
                             self.super_link("doc_id", "doc_entity"),
                             # Populated onaccept - used for map popups
                             Field("name",
                                   readable=False,
                                   writable=False),
                             self.project_project_id(),
                             self.gis_location_id(
                                widget = S3LocationAutocompleteWidget(),
                                requires = IS_LOCATION(),
                                represent = self.gis_location_lx_represent,
                                comment = S3AddResourceLink(c="gis",
                                                            f="location",
                                                            label = T("Add Location"),
                                                            title=T("Location"),
                                                            tooltip=T("Enter some characters to bring up a list of possible matches")),
                                ),
                             s3_comments(),
                             *s3_meta_fields())

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
                    title_search = T("Search Communities"),
                    title_upload = T("Import Community Data"),
                    title_report = T("3W Report"),
                    title_map = T("Map of Communities"),
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
                    title_report = T("3W Report"),
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
                field = ["location_id$L0",
                         "location_id$L1",
                         "location_id$L2",
                         "location_id$L3",
                         "location_id$L4",
                         #"location_id$L5",
                         ]
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
                         #"location_id$L5",
                         "project_id$name",
                         "project_id$code",
                         "project_id$description",
                         ]
            )

        advanced_search = [
            simple,
            # This is only suitable for deployments with a few projects
            #S3SearchOptionsWidget(
            #    name = "project_location_search_project",
            #    label = T("Project"),
            #    field = "project_id",
            #    cols = 3
            #),
            S3SearchOptionsWidget(
                name = "project_location_search_theme",
                label = T("Theme"),
                field = "project_id$theme_project.theme_id",
                options = self.project_theme_opts,
                cols = 1,
            ),
            S3SearchOptionsWidget(
                name = "project_location_search_L0",
                field = "location_id$L0",
                label = COUNTRY,
                cols = 3
            ),
            S3SearchOptionsWidget(
                name = "project_location_search_L1",
                field = "location_id$L1",
                location_level = "L1",
                cols = 3
            ),
            S3SearchOptionsWidget(
                name = "project_location_search_L2",
                field = "location_id$L2",
                location_level = "L2",
                cols = 3
            ),
            S3SearchOptionsWidget(
                name = "project_location_search_L3",
                field = "location_id$L3",
                location_level = "L3",
                cols = 3
            )
        ]

        if settings.get_project_sectors():
            sectors = S3SearchOptionsWidget(
                name = "project_location_search_sector",
                label = T("Sector"),
                field = "project_id$sector.name",
                cols = 3
            )
            advanced_search.insert(1, sectors)

        search_method = S3Search(
            simple = (simple),
            advanced = advanced_search,
        )

        # Resource Configuration
        report_fields = [(COUNTRY, "location_id$L0"),
                         "location_id$L1",
                         "location_id$L2",
                         "location_id$L3",
                         "location_id$L4",
                         (messages.ORGANISATION, "project_id$organisation_id"),
                         (T("Project"), "project_id"),
                         (T("Activity Types"), "activity_type.activity_type_id"),
                         ]
        list_fields = ["location_id",
                       (COUNTRY, "location_id$L0"),
                       "location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       "project_id",
                       ]
        if settings.get_project_theme_percentages():
            list_fields.append((T("Themes"), "project_id$theme_project.theme_id"))
        else:
            list_fields.append((T("Activity Types"), "activity_type.activity_type_id"))
        list_fields.append("comments")

        configure(tablename,
                  super_entity="doc_entity",
                  create_next=URL(c="project", f="location",
                                  args=["[id]", "beneficiary"]),
                  deduplicate=self.project_location_deduplicate,
                  onaccept=self.project_location_onaccept,
                  search_method=search_method,
                  report_options=Storage(search = advanced_search,
                                         rows=report_fields,
                                         cols=report_fields,
                                         fact=report_fields,
                                         defaults=Storage(rows="location.location_id$L1",
                                                          cols="location.project_id",
                                                          fact="activity_type.activity_type_id",
                                                          aggregate="list",
                                                          totals=True
                                                          )
                                         ),
                  list_fields = list_fields,
                  )

        # Reusable Field
        project_location_id = S3ReusableField("project_location_id", table,
            requires = IS_NULL_OR(
                        IS_ONE_OF(db(current.auth.s3_accessible_query("update",
                                                                      table)),
                                  "project_location.id",
                                  project_location_represent,
                                  sort=True)),
            represent = project_location_represent,
            label = LOCATION,
            comment = S3AddResourceLink(ADD_LOCATION,
                                        c="project", f="location",
                                        tooltip=LOCATION_TOOLTIP),
            ondelete = "CASCADE"
            )

        # Components
        # Activity Types
        add_component("project_activity_type",
                      project_location=Storage(
                                link="project_activity_type_location",
                                joinby="project_location_id",
                                key="activity_type_id",
                                actuate="hide"))

        # Beneficiaries
        add_component("project_beneficiary",
                      project_location="project_location_id")

        # Contacts
        add_component("pr_person",
                      project_location=Storage(
                            name="contact",
                            link="project_location_contact",
                            joinby="project_location_id",
                            key="person_id",
                            actuate="hide",
                            autodelete=False))

        # Themes
        add_component("project_theme",
                      project_location=Storage(
                                link="project_theme_location",
                                joinby="project_location_id",
                                key="theme_id",
                                actuate="hide"))

        # ---------------------------------------------------------------------
        # Project Community Contact Person
        #
        tablename = "project_location_contact"
        table = define_table(tablename,
                             project_location_id(),
                             self.pr_person_id(
                                widget=S3AddPersonWidget(controller="pr"),
                                requires=IS_ADD_PERSON_WIDGET(),
                                comment=None
                                ),
                             *s3_meta_fields())

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

        # Components
        # Email
        add_component("pr_contact",
                      project_location_contact=dict(
                        name="email",
                        link="pr_person",
                        joinby="id",
                        key="pe_id",
                        fkey="pe_id",
                        pkey="person_id",
                        filterby="contact_method",
                        filterfor=["EMAIL"],
                      ))
        # Mobile Phone
        add_component("pr_contact",
                      project_location_contact=dict(
                        name="phone",
                        link="pr_person",
                        joinby="id",
                        key="pe_id",
                        fkey="pe_id",
                        pkey="person_id",
                        filterby="contact_method",
                        filterfor=["SMS"],
                      ))

        contact_search_method = S3Search(
            advanced=(S3SearchSimpleWidget(
                            name = "location_contact_search_simple",
                            label = T("Name"),
                            comment = T("You can search by person name - enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
                            field = ["person_id$first_name",
                                     "person_id$middle_name",
                                     "person_id$last_name"
                                    ]
                        ),
                        S3SearchOptionsWidget(
                            name="location_contact_search_L1",
                            field="project_location_id$location_id$L1",
                            location_level="L1",
                            cols = 3,
                        ),
                        S3SearchOptionsWidget(
                            name="location_contact_search_L2",
                            field="project_location_id$location_id$L2",
                            location_level="L2",
                            cols = 3,
                        )
                    ))

        # Resource configuration
        configure(tablename,
                  search_method=contact_search_method,
                  list_fields=["person_id",
                               (T("Email"), "email.value"),
                               (T("Mobile Phone"), "phone.value"),
                               "project_location_id",
                               (T("Project"), "project_location_id$project_id"),
                               ])

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(
                project_location_id = project_location_id,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_location_onaccept(form):
        """
            Calculate the 'name' field used by Map popups
        """

        vars = form.vars
        id = vars.id
        if vars.location_id and vars.project_id:
            name = project_location_represent(None, vars)
        elif id:
            name = project_location_represent(id)
        else:
            return None
        if len(name) > 512:
            # Ensure we don't break limits of SQL field
            name = name[:509] + "..."
        db = current.db
        db(db.project_location.id == id).update(name=name)

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

# =============================================================================
class S3ProjectOrganisationModel(S3Model):
    """
        Project Organisation Model
    """

    names = ["project_organisation",
             ]

    def model(self):

        T = current.T

        messages = current.messages
        NONE = messages["NONE"]

        # ---------------------------------------------------------------------
        # Project Organisations
        # for multi_orgs=True
        #
        project_organisation_roles = current.deployment_settings.get_project_organisation_roles()

        organisation_help = T("Add all organizations which are involved in different roles in this project")

        tablename = "project_organisation"
        table = self.define_table(tablename,
                                  self.project_project_id(),
                                  self.org_organisation_id(
                                    requires = self.org_organisation_requires(
                                                    required=True,
                                                    # Need to be able to add Partners/Donors not just Lead org
                                                    #updateable=True,
                                                    ),
                                    widget = None,
                                    comment=S3AddResourceLink(c="org",
                                                              f="organisation",
                                                              label=T("Add Organization"),
                                                              title=messages.ORGANISATION,
                                                              tooltip=organisation_help)
                                    ),
                                  Field("role", "integer",
                                        label = T("Role"),
                                        requires = IS_NULL_OR(
                                                    IS_IN_SET(project_organisation_roles)
                                                    ),
                                        represent = lambda opt: \
                                            project_organisation_roles.get(opt,
                                                                           NONE)),
                                  Field("amount", "double",
                                        requires = IS_NULL_OR(
                                                    IS_FLOAT_AMOUNT()),
                                        represent = lambda v: \
                                            IS_FLOAT_AMOUNT.represent(v, precision=2),
                                        widget = IS_FLOAT_AMOUNT.widget,
                                        label = T("Funds Contributed by this Organization")),
                                  s3_currency(),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD Strings
        ADD_PROJECT_ORG = T("Add Organization to Project")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_PROJECT_ORG,
            title_display = T("Project Organization Details"),
            title_list = T("Project Organizations"),
            title_update = T("Edit Project Organization"),
            title_search = T("Search Project Organizations"),
            title_upload = T("Import Project Organizations"),
            title_report = T("Funding Report"),
            subtitle_create = T("Add Organization to Project"),
            label_list_button = T("List Project Organizations"),
            label_create_button = ADD_PROJECT_ORG,
            label_delete_button = T("Remove Organization from Project"),
            msg_record_created = T("Organization added to Project"),
            msg_record_modified = T("Project Organization updated"),
            msg_record_deleted = T("Organization removed from Project"),
            msg_list_empty = T("No Organizations for Project(s)"))

        # Report Options
        report_fields = ["project_id",
                         "organisation_id",
                         "role",
                         "amount",
                         "currency",
                         ]
        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = report_fields,
                                 #methods = ["sum"],
                                 defaults = Storage(rows = "organisation.organisation_id",
                                                    cols = "organisation.currency",
                                                    fact = "organisation.amount",
                                                    aggregate = "sum",
                                                    totals = False
                                                    )
                                 )

        # Resource Configuration
        self.configure(tablename,
                       report_options = report_options,
                       deduplicate=self.project_organisation_deduplicate,
                       onvalidation=self.project_organisation_onvalidation,
                       onaccept=self.project_organisation_onaccept,
                       ondelete=self.project_organisation_ondelete,
                       )

        # Pass names back to global scope (s3.*)
        return dict(
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_organisation_onvalidation(form, lead_role=None):
        """ Form validation """

        if lead_role is None:
            lead_role = current.deployment_settings.get_project_organisation_lead_role()

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
            project.organisation to point to the same organisation
            & update the realm_entity.
        """

        vars = form.vars

        if str(vars.role) == \
             str(current.deployment_settings.get_project_organisation_lead_role()):

            # Get the project ID from the new project organisation record
            db = current.db
            ptable = db.project_project
            otable = db.project_organisation
            project_id = db(otable.id == vars.id).select(otable.project_id,
                                                         limitby=(0, 1)
                                                         ).first().project_id

            # Set the Project's organisation_id to the new lead organisation
            organisation_id = vars.organisation_id
            s3db = current.s3db
            db(ptable.id == project_id).update(
                                        organisation_id = organisation_id,
                                        realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                                         organisation_id)
                                        )

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
           str(current.deployment_settings.get_project_organisation_lead_role()):
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
class S3ProjectThemeModel(S3Model):
    """
        Project Theme Model
    """

    names = ["project_theme",
             "project_theme_id",
             "project_theme_sector",
             "project_theme_project",
             "project_theme_location",
             ]

    def model(self):

        T = current.T
        db = current.db

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        theme_percentages = current.deployment_settings.get_project_theme_percentages()

        # ---------------------------------------------------------------------
        # Themes
        #
        tablename = "project_theme"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True, unique=True),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_THEME = T("Add Theme")
        crud_strings[tablename] = Storage(
            title_create = ADD_THEME,
            title_display = T("Theme Details"),
            title_list = T("Themes"),
            title_update = T("Edit Theme"),
            title_upload = T("Import Themes"),
            subtitle_create = T("Add New Theme"),
            label_list_button = T("List Themes"),
            label_create_button = ADD_THEME,
            label_delete_button = T("Delete Theme"),
            msg_record_created = T("Theme added"),
            msg_record_modified = T("Theme updated"),
            msg_record_deleted = T("Theme deleted"),
            msg_list_empty = T("No Themes currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename)
        theme_id = S3ReusableField("theme_id", table,
                                   label = T("Theme"),
                                   sortby = "name",
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "project_theme.id",
                                                          represent,
                                                          sort=True)),
                                   represent = represent,
                                   ondelete = "CASCADE")

        # Components
        add_component("project_theme_project", project_theme="theme_id")

        add_component("project_theme_sector", project_theme="theme_id")

        crud_form = S3SQLCustomForm(
                        "name",
                        # Project Sectors
                        S3SQLInlineComponent(
                            "theme_sector",
                            label=T("Sectors to which this Theme can apply"),
                            fields=["sector_id"],
                        ),
                        "comments"
                    )

        configure(tablename,
                  crud_form=crud_form,
                  list_fields=["id",
                               "name",
                               (T("Sectors"), "theme_sector.sector_id"),
                               "comments",
                               ])

        # ---------------------------------------------------------------------
        # Theme - Sector Link Table
        #
        tablename = "project_theme_sector"
        table = define_table(tablename,
                             theme_id(empty=False),
                             self.org_sector_id(label="",
                                                empty=False),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("New Sector"),
            title_display = T("Sector"),
            title_list = T("Sectors"),
            title_update = T("Edit Sector"),
            title_search = T("Search Sectors"),
            title_upload = T("Import Sector data"),
            subtitle_create = T("Add New Sector"),
            label_list_button = T("List Sectors"),
            label_create_button = T("Add Sector to Theme"),
            msg_record_created = T("Sector added to Theme"),
            msg_record_modified = T("Sector updated"),
            msg_record_deleted = T("Sector removed from Theme"),
            msg_list_empty = T("No Sectors found for this Theme")
        )

        # ---------------------------------------------------------------------
        # Theme - Project Link Table
        #
        tablename = "project_theme_project"
        table = define_table(tablename,
                             theme_id(empty=False),
                             self.project_project_id(empty=False),
                             # % breakdown by theme (sector in IATI)
                             Field("percentage", "integer",
                                   label = T("Percentage"),
                                   default = 0,
                                   requires = IS_INT_IN_RANGE(0, 101),
                                   readable = theme_percentages,
                                   writable = theme_percentages,
                                   ),
                            *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("New Theme"),
            title_display = T("Theme"),
            title_list = T("Themes"),
            title_update = T("Edit Theme"),
            title_search = T("Search Themes"),
            title_upload = T("Import Theme data"),
            subtitle_create = T("Add New Theme"),
            label_list_button = T("List Themes"),
            label_create_button = T("Add Theme to Project"),
            msg_record_created = T("Theme added to Project"),
            msg_record_modified = T("Theme updated"),
            msg_record_deleted = T("Theme removed from Project"),
            msg_list_empty = T("No Themes found for this Project")
        )

        configure(tablename,
                  onaccept = self.project_theme_project_onaccept
                  )

        # ---------------------------------------------------------------------
        # Theme - Project Location Link Table
        #
        tablename = "project_theme_location"
        table = define_table(tablename,
                             theme_id(empty=False),
                             self.project_location_id(empty=False),
                             # % breakdown by theme (sector in IATI)
                             Field("percentage", "integer",
                                   label = T("Percentage"),
                                   default = 0,
                                   requires = IS_INT_IN_RANGE(0, 101),
                                   readable = theme_percentages,
                                   writable = theme_percentages,
                                   ),
                            *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("New Theme"),
            title_display = T("Theme"),
            title_list = T("Themes"),
            title_update = T("Edit Theme"),
            title_search = T("Search Themes"),
            title_upload = T("Import Theme data"),
            subtitle_create = T("Add New Theme"),
            label_list_button = T("List Themes"),
            label_create_button = T("Add Theme to Project Location"),
            msg_record_created = T("Theme added to Project Location"),
            msg_record_modified = T("Theme updated"),
            msg_record_deleted = T("Theme removed from Project Location"),
            msg_list_empty = T("No Themes found for this Project Location")
        )

        # Pass names back to global scope (s3.*)
        return dict(
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_theme_project_onaccept(form):
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
        percentages = {}
        db = current.db
        table = db.project_theme_project
        query = (table.deleted == False) & \
                (table.project_id == project_id)
        rows = db(query).select(table.theme_id,
                                table.percentage)
        for row in rows:
            percentages[row.theme_id] = row.percentage

        # Update the Project's Locations
        s3db = current.s3db
        table = s3db.project_location
        ltable = s3db.project_theme_location
        update_or_insert = ltable.update_or_insert
        query = (table.deleted == False) & \
                (table.project_id == project_id)
        rows = db(query).select(table.id)
        for row in rows:
            for theme_id in percentages:
                update_or_insert(project_location_id = row.id,
                                 theme_id = theme_id,
                                 percentage = percentages[theme_id])

# =============================================================================
class S3ProjectDRRModel(S3Model):
    """
        Models for DRR (Disaster Risk Reduction) extensions
    """

    names = ["project_drr",
             ]

    def model(self):

        T = current.T

        project_hfa_opts = self.project_hfa_opts()

        tablename = "project_drr"
        self.define_table(tablename,
                          self.project_project_id(empty=False),
                          Field("hfa", "list:integer",
                                label = T("HFA Priorities"),
                                requires = IS_NULL_OR(
                                            IS_IN_SET(project_hfa_opts.keys(),
                                                      labels = ["HFA %s" % hfa \
                                                                for hfa in project_hfa_opts.keys()],
                                                      multiple = True)),
                                represent = self.hfa_opts_represent,
                                widget = lambda f, v, **attr: \
                                    s3_grouped_checkboxes_widget(f, v,
                                                                 help_field=project_hfa_opts,
                                                                 **attr)
                                ),
                         *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return dict(
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def hfa_opts_represent(opt):
        """ Option representation """

        NONE = current.messages["NONE"]

        opts = opt
        if isinstance(opt, int):
            opts = [opt]
        elif not isinstance(opt, (list, tuple)):
            return NONE
        elif opt[0] is None:
            return NONE
        vals = ["HFA %s" % o for o in opts]
        return ", ".join(vals)

# =============================================================================
class S3ProjectDRRPPModel(S3Model):
    """
        Models for DRR Project Portal extensions
        - injected into custom Project CRUD forms
    """

    names = ["project_drrpp",
             "project_output",
             ]

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        project_id = self.project_project_id

        NONE = current.messages["NONE"]

        local_currencies = current.deployment_settings.get_fin_currencies().keys()
        local_currencies.remove("USD")

        project_rfa_opts = self.project_rfa_opts()
        project_pifacc_opts = self.project_pifacc_opts()
        project_jnap_opts = self.project_jnap_opts()

        tablename = "project_drrpp"
        define_table(tablename,
                     project_id(
                        requires=IS_ONE_OF(db, "project_project.id",
                                           lambda id, row:
                                            project_project_represent(id, row,
                                                                      show_link=False)
                                           )
                        ),
                     Field("parent_project",
                           represent = lambda v: v or NONE,
                           label = T("Parent Project"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Parent Project"),
                                                           T("The parent project or programme which this project is implemented under"))), 
                           
                     ),
                     Field("duration", "integer",
                           represent = lambda v: v or NONE,
                           label = T("Duration (months)")),
                     Field("local_budget", "double",
                           label = T("Total Funding (Local Currency)"),
                           represent = lambda v: \
                            IS_FLOAT_AMOUNT.represent(v, precision=2)),
                     s3_currency("local_currency",
                                 label = T("Local Currency"),
                                 requires = IS_IN_SET(local_currencies,
                                                      zero=None)
                                 ),
                     Field("activities", "text",
                           represent = lambda v: v or NONE,
                           label = T("Activities")),
                     Field("rfa", "list:integer",
                           label = T("RFA Priorities"),
                           requires = IS_NULL_OR(
                                        IS_IN_SET(project_rfa_opts.keys(),
                                                  labels = ["RFA %s" % \
                                                            rfa for rfa in project_rfa_opts.keys()],
                                                  multiple = True)),
                           represent = lambda opt: \
                            self.opts_represent(opt, "RFA"),
                           widget = lambda f, v, **attr: \
                            s3_grouped_checkboxes_widget(f, v,
                                                         help_field=project_rfa_opts,
                                                         **attr),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("RFA Priorities"),
                                                           T("Applicable to projects in Pacific countries only")))),
                     Field("pifacc", "list:integer",
                           label = T("PIFACC Priorities"),
                           requires = IS_NULL_OR(
                                        IS_IN_SET(project_pifacc_opts.keys(),
                                                  labels = ["PIFACC %s" % \
                                                            pifacc for pifacc in project_pifacc_opts.keys()],
                                                  multiple = True)),
                           represent = lambda opt: \
                            self.opts_represent(opt, "PIFACC"),
                           widget = lambda f, v, **attr: \
                            s3_grouped_checkboxes_widget(f, v,
                                                         help_field=project_pifacc_opts,
                                                         **attr),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("PIFACC Priorities"),
                                                           T("Pacific Islands Framework for Action on Climate Change. Applicable to projects in Pacific countries only")))),
                     Field("jnap", "list:integer",
                           label = T("JNAP Priorities"),
                           requires = IS_NULL_OR(
                                        IS_IN_SET(project_jnap_opts.keys(),
                                                  labels = ["JNAP %s" % \
                                                            jnap for jnap in project_jnap_opts.keys()],
                                                  multiple = True)),
                           represent = lambda opt: \
                            self.opts_represent(opt, "JNAP"),
                           widget = lambda f, v, **attr: \
                            s3_grouped_checkboxes_widget(f, v,
                                                         help_field=project_jnap_opts,
                                                         **attr),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("JNAP Priorities"),
                                                           T("Joint National Action Plan for Disaster Risk Management and Climate Change Adaptation. Applicable to Cook Islands only")))),
                     Field("L1", "list:integer",
                           label = T("Cook Islands"),
                           requires = IS_NULL_OR(
                                        IS_ONE_OF(db, "gis_location.id",
                                                  S3Represent(lookup="gis_location"),
                                                  filterby = "L0",
                                                  filter_opts = ["Cook Islands"],
                                                  not_filterby = "name",
                                                  not_filter_opts = ["Cook Islands"],
                                                  multiple=True)),
                           represent = S3Represent(lookup="gis_location",
                                                   multiple=True),
                           widget = lambda f, v, **attr: \
                            s3_checkboxes_widget(f, v, cols=4, **attr),
                           ),
                     Field("outputs", "text",
                           label = "%s (Old - do NOT use)" % T("Outputs"),
                           represent = lambda v: v or NONE,
                           readable = False,
                           writable = False,
                           ),
                     # @ToDo: Use the project_project.human_resource_id with a better widget.
                     # @ToDo: Becase RMS uses the human_resource_id field, the focal person from RMS won't be visible in DRRPP
                     Field("focal_person",
                           represent = lambda v: v or NONE,
                           label = T("Focal Person")),
                     self.org_organisation_id(label = T("Organization")),
                     Field("email",
                           requires=IS_NULL_OR(IS_EMAIL()),
                           represent = lambda v: v or NONE,
                           label = T("Email")),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_display = T("DRRPP Extensions"),
            title_update = T("Edit DRRPP Extensions"),
        )

        tablename = "project_output"
        define_table(tablename,
                     project_id(
                        requires=IS_ONE_OF(db, "project_project.id",
                                           lambda id, row:
                                            project_project_represent(id, row,
                                                                      show_link=False)
                                           )
                        ),
                     Field("name",
                           represent = lambda v: v or NONE,
                           label = T("Output")),
                     Field("status",
                           represent = lambda v: v or NONE,
                           label = T("Status")),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Output"),
            title_display = T("Output"),
            title_list = T("Outputs"),
            title_update = T("Edit Output"),
            subtitle_create = T("Add New Output"),
            label_list_button = T("List Outputs"),
            label_create_button = T("New Output"),
            msg_record_created = T("Output added"),
            msg_record_modified = T("Output updated"),
            msg_record_deleted = T("Output removed"),
            msg_list_empty = T("No outputs found")
        )

        # Pass names back to global scope (s3.*)
        return dict(
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def opts_represent(opt, prefix):
        """ Option representation """

        NONE = current.messages["NONE"]

        opts = opt
        if isinstance(opt, int):
            opts = [opt]
        elif not isinstance(opt, (list, tuple)):
            return NONE
        elif opt[0] is None:
            return NONE
        vals = ["%s %s" % (prefix, o) for o in opts]
        return ", ".join(vals)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_output_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "project_output":
            return
        data = item.data
        name = data.get("name", None)
        project_id = data.get("project_id", None)
        if name:
            table = item.table
            query = (table.name == name)
            if project_id:
                query &= ((table.project_id == project_id) | \
                          (table.project_id == None))

            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectTaskModel(S3Model):
    """
        Project Task Model

        This class holds the tables used for an Organisation to manage
        their Tasks in detail.
    """

    names = ["project_milestone",
             "project_task",
             "project_task_id",
             "project_time",
             "project_comment",
             "project_task_project",
             "project_task_activity",
             "project_task_milestone",
             ]

    def model(self):

        db = current.db
        T = current.T
        auth = current.auth
        request = current.request

        project_id = self.project_project_id

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
        represent = S3Represent(lookup=tablename)
        milestone_id = S3ReusableField("milestone_id", table,
                                       sortby="name",
                                       requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "project_milestone.id",
                                                              represent)),
                                       represent = represent,
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
        # @ToDo: Task templates
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
                                   represent = lambda opt: \
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
                             s3_datetime("date_due",
                                         label = T("Date Due"),
                                         past=0,
                                         future=8760,  # Hours, so 1 year
                                         represent="date",
                                         readable = staff,
                                         writable = staff,
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
                                   represent = lambda opt: \
                                    project_task_status_opts.get(opt,
                                                                 UNKNOWN_OPT)),
                             *s3_meta_fields())

        # Field configurations
        # Comment these if you don't need a Site associated with Tasks
        #table.site_id.readable = table.site_id.writable = True
        #table.site_id.label = T("Check-in at Facility") # T("Managing Office")
        table.created_on.represent = lambda dt: \
                                        S3DateTime.date_represent(dt, utc=True)

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
                        comment = T("Search for a Task by name or description."),
                        field = ["name",
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
                        field = "task_project.project_id",
                        options = self.task_project_opts,
                        cols = 3
                    ),
                    S3SearchOptionsWidget(
                        name = "task_search_activity",
                        label = T("Activity"),
                        field = "task_activity.activity_id",
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
                     (T("ID"), "task_id"),
                     "priority",
                     "name",
                     "pe_id",
                     "date_due",
                     "time_estimated",
                     "time_actual",
                     "created_on",
                     "status",
                     #"site_id"
                     ]

        if settings.get_project_milestones():
            list_fields.insert(5, (T("Milestone"), "milestone.name"))
            advanced_task_search.insert(4, S3SearchOptionsWidget(
                                            name = "task_search_milestone",
                                            label = T("Milestone"),
                                            field = "task_milestone.milestone_id",
                                            options = self.task_milestone_opts,
                                            cols = 3
                                            ))

        task_search = S3Search(advanced = advanced_task_search)

        task_report = Storage(rows = list_fields,
                              cols = list_fields,
                              fact = list_fields,
                              defaults = Storage(rows = "task.project",
                                                 cols = "task.pe_id",
                                                 fact = "task.time_estimated",
                                                 aggregate = "sum",
                                                 totals = True
                                                 ),
                              search = advanced_task_search,
                              )

        # Custom Form
        crud_form = S3SQLCustomForm(
                        "name",
                        "description",
                        "source",
                        "priority",
                        "pe_id",
                        "date_due",
                        "time_estimated",
                        "status",
                        S3SQLInlineComponent(
                            "time",
                            label = T("Time Log"),
                            fields = ["date",
                                      "person_id",
                                      "hours",
                                      "comments"
                                      ],
                            orderby = "date"
                        ),
                        "time_actual",
                    )

        # Resource Configuration
        configure(tablename,
                  super_entity="doc_entity",
                  copyable=True,
                  orderby="project_task.priority",
                  realm_entity=self.task_realm_entity,
                  onvalidation=self.task_onvalidation,
                  #create_next=URL(f="task", args=["[id]"]),
                  create_onaccept=self.task_create_onaccept,
                  update_onaccept=self.task_update_onaccept,
                  search_method=task_search,
                  report_options = task_report,
                  list_fields=list_fields,
                  crud_form = crud_form,
                  extra="description")

        # Reusable field
        task_id = S3ReusableField("task_id", table,
                                  label = T("Task"),
                                  sortby="name",
                                  requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "project_task.id",
                                                          self.project_task_represent)),
                                  represent = self.project_task_represent,
                                  comment = S3AddResourceLink(c="project",
                                                              f="task",
                                                              title=ADD_TASK,
                                                              tooltip=T("A task is a piece of work that an individual or team can do in 1-2 days.")),
                                  ondelete = "CASCADE")

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

        # Activities
        add_component("project_activity",
                      project_task=Storage(
                                link="project_task_activity",
                                joinby="task_id",
                                key="activity_id",
                                actuate="embed",
                                autocomplete="name",
                                autodelete=False))

        # Milestones
        add_component("project_milestone",
                      project_task=Storage(
                                link="project_task_milestone",
                                joinby="task_id",
                                key="milestone_id",
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
                             project_id(
                                # Override requires so that update access to the projects isn't required
                                requires = IS_ONE_OF(db, "project_project.id",
                                                     lambda id, row:
                                                        project_project_represent(id, row,
                                                                                  show_link=False)

                                                     )
                                ),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Link task <-> activity
        #
        # Tasks <> Activities
        tablename = "project_task_activity"
        table = define_table(tablename,
                             task_id(),
                             self.project_activity_id(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Link task <-> milestone
        #
        # Tasks <> Milestones
        tablename = "project_task_milestone"
        table = define_table(tablename,
                             task_id(),
                             milestone_id(),
                             *s3_meta_fields())

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

        # Resource Configuration
        configure(tablename,
                  list_fields=["id",
                               "task_id",
                               "created_by",
                               "modified_on"
                               ])

        # ---------------------------------------------------------------------
        # Project Time
        # - used to Log hours spent on a Task
        #
        tablename = "project_time"
        table = define_table(tablename,
                             task_id(
                                requires = IS_ONE_OF(db, "project_task.id",
                                                     lambda id, row: \
                                                        self.project_task_represent(id,
                                                                                    row,
                                                                                    show_link=False,
                                                                                    show_project=True)
                                                     ),
                                ),
                             self.pr_person_id(default=auth.s3_logged_in_person(),
                                               widget = SQLFORM.widgets.options.widget
                                               ),
                             s3_datetime(default="now",
                                         past=8760, # Hours, so 1 year
                                         future=0
                                         ),
                             Field("hours", "double",
                                   label = "%s (%s)" % (T("Time"),
                                                        T("hours")),
                                   represent=lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)),
                             s3_comments(),
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
            title_report = T("Project Time Report"),
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

        list_fields = ["id",
                       (T("Project"), "task_id$task_project.project_id"),
                       (T("Activity"), "task_id$task_activity.activity_id"),
                       "task_id",
                       "person_id",
                       "date",
                       "hours",
                       "comments",
                       ]

        # Virtual Fields
        table.day = Field.Lazy(project_time_day)
        table.week = Field.Lazy(project_time_week)

        report_fields = list_fields + \
                        [(T("Day"), "day"), (T("Week"), "week")]

        task_time_search = [S3SearchOptionsWidget(name="person_id",
                                                  label = T("Person"),
                                                  field = "person_id",
                                                  cols = 3),
                            S3SearchOptionsWidget(name="project",
                                                  label = T("Project"),
                                                  field = "task_id$task_project.project_id",
                                                  options = self.task_project_opts,
                                                  cols = 3),
                            S3SearchOptionsWidget(name="activity",
                                                  label = T("Activity"),
                                                  field = "task_id$task_activity.activity_id",
                                                  options = self.task_activity_opts,
                                                  cols = 3),
                            S3SearchMinMaxWidget(name="date",
                                                 label=T("Date"),
                                                 field="date"),
                            ]

        if settings.get_project_sectors():
            report_fields.insert(3, (T("Sector"),
                                     "task_id$task_project.project_id$sector"))
            def get_sector_opts():
                stable = self.org_sector
                rows = db(stable.deleted == False).select(stable.name)
                sector_opts = {}
                for row in rows:
                    name = row.name
                    sector_opts[name] = name
                return sector_opts
            task_time_search.insert(2, S3SearchOptionsWidget(name="sectors",
                                                             label = T("Sector"),
                                                             field = "task_id$task_project.project_id$sector",
                                                             options = get_sector_opts,
                                                             cols = 3),
                                    )

        configure(tablename,
                  onaccept=self.time_onaccept,
                  search_method=S3Search(advanced=task_time_search),
                  report_fields=["date"],
                  report_options=Storage(
                        rows = report_fields,
                        cols = report_fields,
                        fact = report_fields,
                        defaults = Storage(
                            rows = "task_id$task_project.project_id",
                            cols = "person_id",
                            fact = "hours",
                            aggregate = "sum",
                            totals = True
                        ),
                        search=task_time_search,
                    ),
                  list_fields=list_fields
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
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
            project_task_id = lambda: dummy("task_id"),
            project_task_active_statuses = [],
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
        query = (ttable.deleted != True) & \
                (ltable.task_id == ttable.id) & \
                (ltable.project_id == ptable.id)
        rows = db(query).select(ptable.id, ptable.name)
        return dict([(row.id, row.name) for row in rows])

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

    # -------------------------------------------------------------------------
    @staticmethod
    def task_milestone_opts():
        """
            Provide the options for the Milestone search filter
            - all Activities with Tasks
        """

        db = current.db
        mtable = db.project_milestone
        ttable = db.project_task
        ltable = db.project_task_milestone
        query = (ttable.deleted == False) & \
                (ltable.task_id == ttable.id) & \
                (ltable.milestone_id == mtable.id)
        opts = db(query).select(mtable.name)
        _dict = {}
        for opt in opts:
            _dict[opt.name] = opt.name
        return _dict

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
            return current.messages["NONE"]

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

    # ---------------------------------------------------------------------
    @staticmethod
    def project_task_represent(id, row=None, show_link=True,
                               show_project=False):
        """ FK representation """

        if row:
            represent = row.name
            if show_project:
                db = current.db
                ltable = db.project_task_project
                ptable = db.project_project
                query = (ltable.task_id == row.id) & \
                        (ltable.project_id == ptable.id)
                project = db(query).select(ptable.name,
                                           limitby=(0, 1)).first()
                if project:
                    represent = "%s (%s)" % (represent, project.name)

            if show_link:
                return A(represent,
                         _href=URL(c="project", f="task", extension="html",
                                   args=[row.id]))
            return represent
        elif not id:
            return current.messages["NONE"]

        db = current.db
        table = db.project_task
        r = db(table.id == id).select(table.name,
                                      limitby=(0, 1)).first()
        try:
            represent = r.name
        except:
            return current.messages.UNKNOWN_OPT
        else:
            if show_project:
                ltable = db.project_task_project
                ptable = db.project_project
                query = (ltable.task_id == id) & \
                        (ltable.project_id == ptable.id)
                project = db(query).select(ptable.name,
                                           limitby=(0, 1)).first()
                if project:
                    represent = "%s (%s)" % (represent, project.name)

            if show_link:
                return A(represent,
                         _href=URL(c="project", f="task", extension="html",
                                   args=[id]))
            return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def task_realm_entity(table, record):
        """ Set the task realm entity to the project's realm entity """

        task_id = record.id
        db = current.db
        ptable = db.project_project
        ltable = db.project_task_project
        query = (ltable.task_id == task_id) & \
                (ltable.project_id == ptable.id)
        project = db(query).select(ptable.realm_entity,
                                   limitby=(0, 1)).first()
        if project:
            return project.realm_entity
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
                * Process the additional fields: Project/Activity/Milestone
                * create associated Link Table records
                * notify assignee
        """

        db = current.db
        s3db = current.s3db
        session = current.session

        id = form.vars.id

        if session.s3.event:
            # Create a link between this Task & the active Event
            etable = s3db.event_task
            etable.insert(event_id=session.s3.event,
                          task_id=id)

        ltp = db.project_task_project

        vars = current.request.post_vars
        project_id = vars.get("project_id", None)
        if project_id:
            # Create Link to Project
            link_id = ltp.insert(task_id = id,
                                 project_id = project_id)

        activity_id = vars.get("activity_id", None)
        if activity_id:
            # Create Link to Activity
            lta = db.project_task_activity
            link_id = lta.insert(task_id = id,
                                 activity_id = activity_id)

        milestone_id = vars.get("milestone_id", None)
        if milestone_id:
            # Create Link to Milestone
            ltable = db.project_task_milestone
            link_id = ltable.insert(task_id = id,
                                    milestone_id = milestone_id)

        # Make sure the task is also linked to the project
        # when created under an activity
        row = db(ltp.task_id == id).select(ltp.project_id,
                                           limitby=(0, 1)).first()
        if not row:
            lta = db.project_task_activity
            ta = db.project_activity
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
            * Process the additional fields: Project/Activity/Milestone
            * Log changes as comments
            * If the task is assigned to someone then notify them
        """

        db = current.db
        s3db = current.s3db

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
                        if vvar:
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
            ltable = db.project_task_project
            filter = (ltable.task_id == id)
            project = vars.project_id
            if project:
                # Create the link to the Project
                #ptable = db.project_project
                #master = s3db.resource("project_task", id=id)
                #record = db(ptable.id == project).select(ptable.id,
                #                                         limitby=(0, 1)).first()
                #link = s3db.resource("project_task_project")
                #link_id = link.update_link(master, record)
                query = (ltable.task_id == id) & \
                        (ltable.project_id == project)
                record = db(query).select(ltable.id, limitby=(0, 1)).first()
                if record:
                    link_id = record.id
                else:
                    link_id = ltable.insert(task_id = id,
                                            project_id = project)
                filter = filter & (ltable.id != link_id)
            # Remove any other links
            links = s3db.resource("project_task_project", filter=filter)
            ondelete = s3db.get_config("project_task_project", "ondelete")
            links.delete(ondelete=ondelete)

        if "activity_id" in vars:
            ltable = db.project_task_activity
            filter = (ltable.task_id == id)
            activity = vars.activity_id
            if vars.activity_id:
                # Create the link to the Activity
                #atable = db.project_activity
                #master = s3db.resource("project_task", id=id)
                #record = db(atable.id == activity).select(atable.id,
                #                                          limitby=(0, 1)).first()
                #link = s3db.resource("project_task_activity")
                #link_id = link.update_link(master, record)
                query = (ltable.task_id == id) & \
                        (ltable.activity_id == activity)
                record = db(query).select(ltable.id, limitby=(0, 1)).first()
                if record:
                    link_id = record.id
                else:
                    link_id = ltable.insert(task_id = id,
                                            activity_id = activity)
                filter = filter & (ltable.id != link_id)
            # Remove any other links
            links = s3db.resource("project_task_activity", filter=filter)
            ondelete = s3db.get_config("project_task_activity", "ondelete")
            links.delete(ondelete=ondelete)

        if "milestone_id" in vars:
            ltable = db.project_task_milestone
            filter = (ltable.task_id == id)
            milestone = vars.milestone_id
            if milestone:
                # Create the link to the Milestone
                #mtable = db.project_milestone
                #master = s3db.resource("project_task", id=id)
                #record = db(mtable.id == milestone).select(mtable.id,
                #                                           limitby=(0, 1)).first()
                #link = s3db.resource("project_task_milestone")
                #link_id = link.update_link(master, record)
                query = (ltable.task_id == id) & \
                        (ltable.milestone_id == milestone)
                record = db(query).select(ltable.id, limitby=(0, 1)).first()
                if record:
                    link_id = record.id
                else:
                    link_id = ltable.insert(task_id = id,
                                            milestone_id = milestone)
                filter = filter & (ltable.id != link_id)
            # Remove any other links
            links = s3db.resource("project_task_milestone", filter=filter)
            ondelete = s3db.get_config("project_task_milestone", "ondelete")
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
            if row.hours:
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
                hours += task.time_actual or 0 # Handle None

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
        # Pass names back to global scope (s3.*)
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
        # Pass names back to global scope (s3.*)
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

    if not row:
        if not id:
            return current.messages["NONE"]
        db = current.db
        table = db.project_project
        row = db(table.id == id).select(table.name,
                                        table.code,
                                        limitby=(0, 1)).first()

    try:
        if current.deployment_settings.get_project_codes():
            repr = "%s: %s" % (row.code, row.name)
        else:
            repr = row.name
        if not show_link:
            return repr
        return A(repr, _href = URL(c="project", f="project", args=[id]))
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def multi_theme_percentage_represent(id):
    """
        Representation for Theme Percentages
        for multiple=True options
    """

    if not id:
        return current.messages["NONE"]

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
        Represent a Project Location (Community)
    """

    if not row:
        if not id:
            return current.messages["NONE"]
        db = current.db
        table = db.project_location
        row = db(table.id == id).select(table.location_id,
                                        table.project_id,
                                        limitby=(0, 1)).first()
    try:
        location = current.s3db.gis_location_lx_represent(row.location_id)
    except:
        return current.messages.UNKNOWN_OPT

    if current.deployment_settings.get_project_community():
        # Community is the primary resource
        return location
    else:
        # Location is just a way to display Projects on a map
        project = project_project_represent(row.project_id, show_link=False)
        return "%s (%s)" % (project, location)

# =============================================================================
def task_notify(form):
    """
        If the task is assigned to someone then notify them
    """

    vars = form.vars
    pe_id = vars.pe_id
    if not pe_id:
        return
    user = current.auth.user
    if user and user.pe_id == pe_id:
        # Don't notify the user when they assign themselves tasks
        return
    if int(vars.status) not in current.response.s3.project_task_active_statuses:
        # No need to notify about closed tasks
        return
    if form.record is None or (int(pe_id) != form.record.pe_id):
        # Assignee has changed
        settings = current.deployment_settings

        if settings.has_module("msg"):
            # Notify assignee
            subject = "%s: Task assigned to you" % settings.get_system_name_short()
            url = "%s%s" % (settings.get_base_public_url(),
                            URL(c="project", f="task", args=vars.id))
            priority = current.s3db.project_task.priority.represent(int(vars.priority))
            message = "You have been assigned a Task:\n\n%s\n\n%s\n\n%s\n\n%s" % \
                (url,
                 "%s priority" % priority,
                 vars.name,
                 vars.description or "")
            current.msg.send_by_pe_id(pe_id, subject, message)
    return

# =============================================================================
class S3ProjectOrganisationFundingVirtualFields:
    """ Virtual fields for the project_project table """

    def total_organisation_amount(self):
        """ Total of project_organisation amounts for project"""

        table = current.s3db.project_organisation
        query = (table.deleted != True) & \
                (table.project_id == self.project_project.id)
        sum_field = table.amount.sum()
        return current.db(query).select(sum_field).first()[sum_field]

# =============================================================================
class S3ProjectBudgetVirtualFields:
    """
        Virtual fields for the project_project table when multi_budgets=True
    """

    def total_annual_budget(self):
        """ Total of all annual budgets for project"""

        table = current.s3db.project_annual_budget
        query = (table.deleted != True) & \
                (table.project_id == self.project_project.id)
        sum_field = table.amount.sum()
        return current.db(query).select(sum_field).first()[sum_field]

# =============================================================================
class S3ProjectBeneficiaryVirtualFields:
    """ Virtual fields for the project_beneficiary table """

    extra_fields = ["project_id",
                    "date",
                    "end_date",
                    ]

    # -------------------------------------------------------------------------
    def year(self):

        try:
            project_id = self.project_beneficiary.project_id
        except AttributeError:
            return []
        try:
            date = self.project_beneficiary.date
        except AttributeError:
            date = None
        try:
            end_date = self.project_beneficiary.end_date
        except AttributeError:
            end_date = None

        if not date or not end_date:
            table = current.s3db.project_project
            project = current.db(table.id == project_id).select(table.start_date,
                                                                table.end_date,
                                                                limitby=(0, 1)
                                                                ).first()
            if project:
                if not date:
                    date = project.start_date
                if not end_date:
                    end_date = project.end_date
        if not date and not end_date:
            return []
        elif not date or not end_date:
            return [date.year or end_date.year]
        else:
            return [year for year in xrange(date.year, end_date.year + 1)]

# =============================================================================
class S3ProjectThemeVirtualFields:
    """ Virtual fields for the project table """

    extra_fields = []

    # -------------------------------------------------------------------------
    def themes(self):
        """
            Themes associated with this Project
        """

        try:
            project_id = self.project_project.id
        except AttributeError:
            return ""

        s3db = current.s3db
        ptable = s3db.project_project
        ttable = s3db.project_theme
        ltable = s3db.project_theme_percentage
        query = (ltable.deleted != True) & \
                (ltable.project_id == project_id) & \
                (ltable.theme_id == ttable.id)
        themes = current.db(query).select(ttable.name,
                                          ltable.percentage)

        if not themes:
            return current.messages["NONE"]

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

    extra_fields = ["id"]

    # -------------------------------------------------------------------------
    def task_id(self):

        try:
            return self.project_task.id
        except AttributeError:
            return None

# =============================================================================
# project_time virtual fields
#
def project_time_day(row):
    """
        Virtual field for project_time - abbreviated string format for
        date, allows grouping per day instead of the individual datetime,
        used for project time report.

        Requires "date" to be in the additional report_fields

        @param row: the Row
    """

    default = "-"

    try:
        thisdate = row["project_time.date"]
    except AttributeError:
        return default
    if not thisdate:
        return default

    now = current.request.utcnow
    week = datetime.timedelta(days=7)
    #if thisdate < (now - week):
        # Ignore data older than the last week
        # - should already be filtered in controller anyway
    #    return default

    return thisdate.date().strftime("%d %B %y")

# =============================================================================
def project_time_week(row):
    """
        Virtual field for project_time - returns the date of the Monday
        (=first day of the week) of this entry, used for project time report.

        Requires "date" to be in the additional report_fields

        @param row: the Row
    """

    default = "-"

    try:
        thisdate = row["project_time.date"]
    except AttributeError:
        return default
    if not thisdate:
        return default

    day = thisdate.date()
    monday = day - datetime.timedelta(days=day.weekday())

    return monday

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
'''i18n.reply="''', str(current.T("Reply")), '''"
var img_path=S3.Ap.concat('/static/img/jCollapsible/')
var ck_config={toolbar:[['Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Smiley','-','Source','Maximize']],toolbarCanCollapse:false,removePlugins:'elementspath'}
function comment_reply(id){
 $('#project_comment_task_id__row').hide()
 $('#project_comment_task_id__row1').hide()
 $('#comment-title').html(i18n.reply)
 $('#project_comment_body').ckeditorGet().destroy()
 $('#project_comment_body').ckeditor(ck_config)
 $('#comment-form').insertAfter($('#comment-'+id))
 $('#project_comment_parent').val(id)
 var task_id = $('#comment-'+id).attr('task_id')
 $('#project_comment_task_id').val(task_id)
}'''))

    s3.js_global.append(js)

# =============================================================================
def project_rheader(r):
    """ Project Resource Headers - used in Project & Budget modules """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    # Need to use this as otherwise demographic_data?viewing=project_location.x
    # doesn't have an rheader
    tablename, record = s3_rheader_resource(r)
    if not record:
        return None
    s3db = current.s3db
    table = s3db.table(tablename)

    resourcename = r.name

    T = current.T
    auth = current.auth
    settings = current.deployment_settings

    attachments_label = settings.get_ui_label_attachments()
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
            append((T("Themes"), "theme"))
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
            append((attachments_label, "document"))
        if settings.get_hrm_show_staff():
            append((T("Staff"), "human_resource", dict(group="staff")))
        if settings.has_module("vol"):
            append((T("Volunteers"), "human_resource", dict(group="volunteer")))

        rheader_fields = [["code", "name"],
                          ["organisation_id"],
                          ["start_date", "end_date"]
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename in ["location","demographic_data"]:
        tabs = [(T("Details"), None),
                (T("Beneficiaries"), "beneficiary"),
                (T("Demographics"), "demographic_data/"),
                (T("Contact People"), "contact"),
                ]
        rheader_fields = []
        if record.project_id is not None:
            rheader_fields.append(["project_id"])
        rheader_fields.append(["location_id"])
        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         record = record,
                                                         table = table)

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
            tabs.append((attachments_label, "document"))
        else:
            tabs.append((T("Documents"), "document"))
        rheader_fields = []
        if record.project_id is not None:
            rheader_fields.append(["project_id"])
        rheader_fields.append(["name"])
        rheader_fields.append(["location_id"])
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename == "task":
        # Tabs
        tabs = [(T("Details"), None)]
        append = tabs.append
        append((attachments_label, "document"))
        if settings.has_module("msg"):
            append((T("Notify"), "dispatch"))
        #(T("Roles"), "job_role"),
        #(T("Assignments"), "human_resource"),
        #(T("Requests"), "req")

        rheader_tabs = s3_rheader_tabs(r, tabs)

        # RHeader
        db = current.db
        ptable = s3db.project_project
        ltable = s3db.project_task_project
        query = (ltable.deleted == False) & \
                (ltable.task_id == r.id) & \
                (ltable.project_id == ptable.id)
        project = db(query).select(ptable.id,
                                   ptable.code,
                                   ptable.name,
                                   limitby=(0, 1)).first()
        if project:
            project = TR(TH("%s: " % T("Project")),
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

        if record.created_by:
            creator = TR(
                            TH("%s: " % T("Created by")),
                            s3_auth_user_represent(record.created_by),
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
            creator,
            time_estimated,
            time_actual,
            #comments,
            ), rheader_tabs)

    return rheader

# =============================================================================
def project_task_form_inject(r, output, project=True):
    """
        Inject Project, Activity & Milestone fields into a Task form
        @ToDo: Re-implement using http://eden.sahanafoundation.org/wiki/S3SQLForm
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    auth = current.auth
    s3 = current.response.s3
    settings = current.deployment_settings

    sep = ": "
    s3_formstyle = settings.get_ui_formstyle()

    table = s3db.project_task_activity
    field = table.activity_id
    default = None
    if r.component_id:
        query = (table.task_id == r.component_id)
        default = db(query).select(field,
                                   limitby=(0, 1)).first()
        if default:
            default = default.activity_id
    elif r.id:
        query = (table.task_id == r.id)
        default = db(query).select(field,
                                   limitby=(0, 1)).first()
        if default:
            default = default.activity_id
    if not default:
        default = field.default
    field_id = "%s_%s" % (table._tablename, field.name)
    if r.component:
        requires = {}
        table = db.project_activity
        query = (table.project_id == r.id)
        rows = db(query).select(table.id, table.name)
        for row in rows:
            requires[row.id] = row.name
        field.requires = IS_IN_SET(requires)
    else:
        if default:
            field.requires = IS_IN_SET([default])
        else:
            field.requires = IS_IN_SET([])
    widget = SQLFORM.widgets.options.widget(field, default)
    label = field.label
    label = LABEL(label, label and sep, _for=field_id,
                  _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
    comment = S3AddResourceLink(T("Add Activity"),
                                c="project",
                                f="activity",
                                tooltip=T("If you don't see the activity in the list, you can add a new one by clicking link 'Add Activity'."))
    if project:
        options = {
            "triggerName": "project_id",
            "targetName": "activity_id",
            "lookupPrefix": "project",
            "lookupResource": "activity",
            "optional": True,
        }
        s3.jquery_ready.append('''S3OptionsFilter(%s)''' % json.dumps(options))
    row_id = field_id + SQLFORM.ID_ROW_SUFFIX
    row = s3_formstyle(row_id, label, widget, comment)
    try:
        output["form"][0].insert(0, row[1])
    except:
        # A non-standard formstyle with just a single row
        pass
    try:
        output["form"][0].insert(0, row[0])
    except:
        pass

    # Milestones
    if settings.get_project_milestones():
        table = s3db.project_task_milestone
        field = table.milestone_id
        if project and r.id:
            query = (table.task_id == r.id)
            default = db(query).select(field,
                                       limitby=(0, 1)).first()
            if default:
                default = default.milestone_id
        else:
            default = field.default
        field_id = "%s_%s" % (table._tablename, field.name)
        # Options will be added later based on the Project
        if default:
            field.requires = IS_IN_SET({default:field.represent(default)})
        else:
            field.requires = IS_IN_SET([])
        #widget = SELECT(_id=field_id, _name=field.name)
        widget = SQLFORM.widgets.options.widget(field, default)
        label = field.label
        label = LABEL(label, label and sep, _for=field_id,
                      _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
        comment = S3AddResourceLink(T("Add Milestone"),
                                    c="project",
                                    f="milestone",
                                    tooltip=T("If you don't see the milestone in the list, you can add a new one by clicking link 'Add Milestone'."))
        options = {
            "triggerName": "project_id",
            "targetName": "milestone_id",
            "lookupPrefix": "project",
            "lookupResource": "milestone",
            "optional": True,
        }
        s3.jquery_ready.append('''S3OptionsFilter(%s)''' % json.dumps(options))
        row_id = field_id + SQLFORM.ID_ROW_SUFFIX
        row = s3_formstyle(row_id, label, widget, comment)
        try:
            output["form"][0].insert(14, row[1])
            output["form"][0].insert(14, row[0])
        except:
            # A non-standard formstyle with just a single row
            pass
        try:
            output["form"][0].insert(7, row[0])
        except:
            pass

    if project:
        vars = current.request.get_vars
        if "project" in vars:
            widget = INPUT(value=vars.project, _name="project_id")
            row = s3_formstyle("project_task_project__row", "",
                                   widget, "", hidden=True)
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
            row = s3_formstyle(row_id, label, widget, comment)
        try:
            output["form"][0].insert(0, row[1])
        except:
            # A non-standard formstyle with just a single row
            pass
        try:
            output["form"][0].insert(0, row[0])
        except:
            pass

    return output

# =============================================================================
def project_task_controller():
    """
        Tasks Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    T = current.T
    s3db = current.s3db
    auth = current.auth
    s3 = current.response.s3
    vars = current.request.get_vars

    # Pre-process
    def prep(r):
        tablename = "project_task"
        table = s3db.project_task
        statuses = s3.project_task_active_statuses
        crud_strings = s3.crud_strings[tablename]

        if r.record:
            if r.interactive:
                # Put the Comments in the RFooter
                project_ckeditor()
                s3.rfooter = LOAD("project", "comments.load",
                                  args=[r.id],
                                  ajax=True)

        elif "mine" in vars:
            # Show the Open Tasks for this User
            if auth.user:
                pe_id = auth.user.pe_id
                s3.filter = (table.pe_id == pe_id) & \
                            (table.status.belongs(statuses))
            crud_strings.title_list = T("My Open Tasks")
            crud_strings.msg_list_empty = T("No Tasks Assigned")
            s3db.configure(tablename,
                           copyable=False,
                           listadd=False)
            try:
                # Add Project
                list_fields = s3db.get_config(tablename,
                                              "list_fields")
                list_fields.insert(4, (T("Project"), "task_project.project_id"))
                # Hide the Assignee column (always us)
                list_fields.remove("pe_id")
                # Hide the Status column (always 'assigned' or 'reopened')
                list_fields.remove("status")
                s3db.configure(tablename,
                               list_fields=list_fields)
            except:
                pass

        elif "project" in vars:
            # Show Open Tasks for this Project
            project = vars.project
            ptable = s3db.project_project
            try:
                name = current.db(ptable.id == project).select(ptable.name,
                                                               limitby=(0, 1)).first().name
            except:
                current.session.error = T("Project not Found")
                redirect(URL(args=None, vars=None))
            if r.method == "search":
                # @ToDo: get working
                r.get_vars = {"task_search_project": name,
                              "task_search_status": ",".join([str(status) for status in statuses])
                              }
            else:
                ltable = s3db.project_task_project
                s3.filter = (ltable.project_id == project) & \
                            (ltable.task_id == table.id) & \
                            (table.status.belongs(statuses))
            crud_strings.title_list = T("Open Tasks for %(project)s") % dict(project=name)
            crud_strings.title_search = T("Search Open Tasks for %(project)s") % dict(project=name)
            crud_strings.msg_list_empty = T("No Open Tasks for %(project)s") % dict(project=name)
            # Add Activity
            list_fields = s3db.get_config(tablename,
                                          "list_fields")
            list_fields.insert(2, (T("Activity"), "task_activity.activity_id"))
            s3db.configure(tablename,
                           # Block Add until we get the injectable component lookups
                           insertable=False,
                           deletable=False,
                           copyable=False,
                           #search_method=task_search,
                           list_fields=list_fields)
        elif "open" in vars:
            # Show Only Open Tasks
            crud_strings.title_list = T("All Open Tasks")
            s3.filter = (table.status.belongs(statuses))
        else:
            crud_strings.title_list = T("All Tasks")
            crud_strings.title_search = T("All Tasks")
            list_fields = s3db.get_config(tablename,
                                          "list_fields")
            list_fields.insert(3, (T("Project"), "task_project.project_id"))
            list_fields.insert(4, (T("Activity"), "task_activity.activity_id"))

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
                field = table.time_actual
                field.readable = field.writable = False
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            if not r.component and \
                   r.method != "import":
                update_url = URL(args=["[id]"], vars=vars)
                current.manager.crud.action_buttons(r,
                                                    update_url=update_url)
                if not r.method in ("search", "report") and \
                   "form" in output:
                    # Insert fields to control the Project, Activity & Milestone
                    output = project_task_form_inject(r, output)

        return output
    s3.postp = postp

    return current.rest_controller("project", "task",
                                   rheader=s3db.project_rheader)

# END =========================================================================
