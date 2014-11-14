# -*- coding: utf-8 -*-

""" Sahana Eden Project Model

    @copyright: 2011-2014 (c) Sahana Software Foundation
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

__all__ = ("S3ProjectModel",
           "S3ProjectActivityModel",
           "S3ProjectActivityTypeModel",
           "S3ProjectActivityOrganisationModel",
           "S3ProjectActivitySectorModel",
           "S3ProjectAnnualBudgetModel",
           "S3ProjectBeneficiaryModel",
           "S3ProjectCampaignModel",
           "S3ProjectFrameworkModel",
           "S3ProjectHazardModel",
           "S3ProjectHRModel",
           "S3ProjectLocationModel",
           "S3ProjectOrganisationModel",
           "S3ProjectOutputModel",
           "S3ProjectSectorModel",
           "S3ProjectStatusModel",
           "S3ProjectThemeModel",
           "S3ProjectDRRModel",
           "S3ProjectDRRPPModel",
           "S3ProjectTaskModel",
           "S3ProjectTaskHRMModel",
           "S3ProjectTaskIReportModel",
           "project_ActivityRepresent",
           "project_activity_year_options",
           "project_rheader",
           "project_task_controller",
           "project_theme_help_fields",
           "project_hazard_help_fields",
           "project_hfa_opts",
           "project_jnap_opts",
           "project_pifacc_opts",
           "project_rfa_opts",
           "project_project_filters",
           "project_project_list_layout",
           "project_task_list_layout",
           "project_ckeditor",
           )

import datetime

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import *
try:
    from gluon.dal.objects import Row
except ImportError:
    # old web2py
    from gluon.dal import Row
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3AddResourceLink

# Compact JSON encoding
SEPARATORS = (",", ":")

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

    names = ("project_project",
             "project_project_id",
             "project_project_represent",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        NONE = current.messages["NONE"]

        settings = current.deployment_settings
        mode_3w = settings.get_project_mode_3w()
        mode_task = settings.get_project_mode_task()
        mode_drr = settings.get_project_mode_drr()
        use_codes = settings.get_project_codes()
        use_sectors = settings.get_project_sectors()
        multi_budgets = settings.get_project_multiple_budgets()
        multi_orgs = settings.get_project_multiple_organisations()

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Projects
        #

        LEAD_ROLE = settings.get_project_organisation_lead_role()
        org_label = settings.get_project_organisation_roles()[LEAD_ROLE]

        tablename = "project_project"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     # multi_orgs deployments use the separate project_organisation table
                     # - although Lead Org is still cached here to avoid the need for a virtual field to lookup
                     self.org_organisation_id(
                        default = auth.root_org(),
                        label = org_label,
                        requires = self.org_organisation_requires(
                                    required = True,
                                    # Only allowed to add Projects for Orgs
                                    # that the user has write access to
                                    updateable = True,
                                    ),
                        ),
                     Field("name", unique=True, length=255,
                           label = T("Project Name"),
                           # Require unique=True if using IS_NOT_ONE_OF like here (same table,
                           # no filter) in order to allow both automatic indexing (faster)
                           # and key-based de-duplication (i.e. before field validation)
                           requires = [IS_NOT_EMPTY(error_message=T("Please fill this!")),
                                       IS_NOT_ONE_OF(db, "project_project.name")]
                           ),
                     Field("code", length=128,
                           label = T("Short Title / ID"),
                           readable = use_codes,
                           writable = use_codes,
                           ),
                     Field("description", "text",
                           label = T("Description"),
                           ),
                     self.project_status_id(),
                     # NB There is additional client-side validation for start/end date in the Controller
                     s3_date("start_date",
                             label = T("Start Date")
                             ),
                     s3_date("end_date",
                             label = T("End Date")
                             ),
                     # Free-text field with no validation (used by OCHA template currently)
                     Field("duration",
                           label = T("Duration"),
                           readable = False,
                           writable = False,
                           ),
                     Field("calendar",
                           label = T("Calendar"),
                           readable = mode_task,
                           writable = mode_task,
                           requires = IS_EMPTY_OR(IS_URL()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Calendar"),
                                                           T("URL to a Google Calendar to display on the project timeline."))),
                           ),
                     # multi_budgets deployments handle on the Budgets Tab
                     Field("budget", "double",
                           label = T("Budget"),
                           represent = lambda v: \
                            IS_FLOAT_AMOUNT.represent(v, precision=2),
                           readable = False if multi_budgets else True,
                           writable = False if multi_budgets else True,
                           ),
                     s3_currency(readable = False if multi_budgets else True,
                                 writable = False if multi_budgets else True,
                                 ),
                     Field("objectives", "text",
                           label = T("Objectives"),
                           represent = lambda v: v or NONE,
                           readable = mode_3w,
                           writable = mode_3w,
                           ),
                     self.hrm_human_resource_id(label = T("Contact Person"),
                                                ),
                     Field.Method("total_organisation_amount",
                                   self.project_total_organisation_amount),
                     Field.Method("total_annual_budget",
                                   self.project_total_annual_budget),
                     s3_comments(comment=DIV(_class="tooltip",
                                             _title="%s|%s" % (T("Comments"),
                                                               T("Outcomes, Impact, Challenges")))),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_PROJECT = T("Create Project")
        crud_strings[tablename] = Storage(
            label_create = ADD_PROJECT,
            title_display = T("Project Details"),
            title_list = T("Projects"),
            title_update = T("Edit Project"),
            title_report = T("Project Report"),
            title_upload = T("Import Projects"),
            label_list_button = T("List Projects"),
            label_delete_button = T("Delete Project"),
            msg_record_created = T("Project added"),
            msg_record_modified = T("Project updated"),
            msg_record_deleted = T("Project deleted"),
            msg_list_empty = T("No Projects currently registered"))

        # Filter widgets
        filter_widgets = project_project_filters(org_label=org_label)

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
            append((T("Total Funding Amount"), "total_organisation_amount"))
        if multi_budgets:
            append((T("Total Annual Budget"), "total_annual_budget"))
        list_fields += ["start_date",
                        "end_date",
                        "location.location_id",
                        ]

        report_fields = list_fields
        report_col_default = "location.location_id"
        report_fact_fields = [(field, "count") for field in report_fields]
        report_fact_default = "project.organisation_id"
        #report_fact_default = "theme.name"

        configure(tablename,
                  context = {"location": "location.location_id",
                             "organisation": "organisation_id",
                             },
                  create_next = create_next,
                  deduplicate = self.project_project_deduplicate,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  list_layout = project_project_list_layout,
                  onaccept = self.project_project_onaccept,
                  realm_components = ("human_resource",
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
                                      ),
                  report_options = Storage(
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
                  super_entity = "doc_entity",
                  update_realm = True,
                  )

        # Reusable Field
        if use_codes:
            project_represent = S3Represent(lookup=tablename,
                                            field_sep = ": ",
                                            fields=["code", "name"])
        else:
            project_represent = S3Represent(lookup=tablename)
        project_id = S3ReusableField("project_id", "reference %s" % tablename,
            label = T("Project"),
            ondelete = "CASCADE",
            represent = project_represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "project_project.id",
                                  project_represent,
                                  updateable = True,
                                  )
                        ),
            sortby = "name",
            comment = S3AddResourceLink(c="project", f="project",
                                        tooltip=T("If you don't see the project in the list, you can add a new one by clicking link 'Create Project'.")),
            )

        # Custom Methods
        set_method("project", "project",
                   method = "assign",
                   action = self.hrm_AssignMethod(component="human_resource"))

        set_method("project", "project",
                   method = "timeline",
                   action = self.project_timeline)

        set_method("project", "project",
                   method = "map",
                   action = self.project_map)

        # Components
        add_components(tablename,
                       # Sites
                       #project_site = "project_id",
                       # Activities
                       project_activity = "project_id",
                       # Activity Types
                       project_activity_type = {"link": "project_activity_type_project",
                                                "joinby": "project_id",
                                                "key": "activity_type_id",
                                                "actuate": "link",
                                                },
                       # Milestones
                       project_milestone = "project_id",
                       # Outputs
                       project_output = "project_id",
                       # Tasks
                       project_task = {"link": "project_task_project",
                                       "joinby": "project_id",
                                       "key": "task_id",
                                       "actuate": "replace",
                                       "autocomplete": "name",
                                       "autodelete": False,
                                       },
                       # Annual Budgets
                       project_annual_budget = "project_id",
                       # Beneficiaries
                       project_beneficiary = "project_id",
                       # Hazards
                       project_hazard = {"link": "project_hazard_project",
                                         "joinby": "project_id",
                                         "key": "hazard_id",
                                         "actuate": "hide",
                                         },
                       # Human Resources
                       project_human_resource = "project_id",
                       hrm_human_resource = {"link": "project_human_resource",
                                             "joinby": "project_id",
                                             "key": "human_resource_id",
                                             "actuate": "hide",
                                             },
                       # Locations
                       project_location = "project_id",
                       # Sectors
                       org_sector = {"link": "project_sector_project",
                                     "joinby": "project_id",
                                     "key": "sector_id",
                                     "actuate": "hide",
                                     },
                       # Format needed by S3Filter
                       project_sector_project = ("project_id",
                                                 {"joinby": "project_id",
                                                  "multiple": False,
                                                  },
                                                 ),
                       # Themes
                       project_theme = {"link": "project_theme_project",
                                        "joinby": "project_id",
                                        "key": "theme_id",
                                        "actuate": "hide",
                                        },
                       # Format needed by S3Filter
                       project_theme_project = "project_id",
                       )

        if multi_orgs:
            add_components(tablename,
                           project_organisation = (# Organisations
                                                   "project_id",
                                                   # Donors
                                                   {"name": "donor",
                                                    "joinby": "project_id",
                                                    "filterby": "role",
                                                    # Works for IFRC & DRRPP:
                                                    "filterfor": (3,),
                                                    },
                                                   # Partners
                                                   {"name": "partner",
                                                    "joinby": "project_id",
                                                    "filterby": "role",
                                                    # Works for IFRC & DRRPP:
                                                    "filterfor": (2, 9),
                                                    },
                                                   ),
                          )
        # DRR
        if mode_drr:
            add_components(tablename,
                           project_drr = {"joinby": "project_id",
                                          "multiple": False,
                                          },
                           )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(project_project_id = project_id,
                    project_project_represent = project_represent,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for model-global names if module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(project_project_id = lambda **attr: dummy("project_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_total_organisation_amount(row):
        """ Total of project_organisation amounts for project"""

        if not current.deployment_settings.get_project_multiple_organisations():
            return 0
        if "project_project" in row:
            project_id = row["project_project.id"]
        elif "id" in row:
            project_id = row["id"]
        else:
            return 0

        table = current.s3db.project_organisation
        query = (table.deleted != True) & \
                (table.project_id == project_id)
        sum_field = table.amount.sum()
        return current.db(query).select(sum_field).first()[sum_field]

    # -------------------------------------------------------------------------
    @staticmethod
    def project_total_annual_budget(row):
        """ Total of all annual budgets for project"""

        if not current.deployment_settings.get_project_multiple_budgets():
            return 0
        if "project_project" in row:
            project_id = row["project_project.id"]
        elif "id" in row:
            project_id = row["id"]
        else:
            return 0

        table = current.s3db.project_annual_budget
        query = (table.deleted != True) & \
                (table.project_id == project_id)
        sum_field = table.amount.sum()
        return current.db(query).select(sum_field).first()[sum_field] or \
               current.messages["NONE"]

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
            id = vars.id
            organisation_id = vars.organisation_id or \
                              current.request.post_vars.organisation_id
            if organisation_id:
                lead_role = settings.get_project_organisation_lead_role()

                otable = current.s3db.project_organisation
                query = (otable.project_id == id) & \
                        (otable.role == lead_role)

                # Update the lead organisation
                count = current.db(query).update(organisation_id = organisation_id)
                if not count:
                    # If there is no record to update, then create a new one
                    otable.insert(project_id = id,
                                  organisation_id = organisation_id,
                                  role = lead_role,
                                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_project_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        # If we have a code, then assume this is unique, however the same
        # project name may be used in multiple locations
        code = data.get("code")
        if code:
            table = item.table
            query = (table.code.lower() == code.lower())
        else:
            name = data.get("name")
            if name:
                table = item.table
                query = (table.name.lower() == name.lower())
            else:
                # Nothing we can work with
                return

        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

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
            layer = {"name"      : T("Projects"),
                     "id"        : "projects",
                     "tablename" : "project_location",
                     "url"       : url,
                     "active"    : True,
                     #"marker"   : None,
                     }

            map = current.gis.show_map(collapsed = True,
                                       feature_resources = [layer],
                                       )

            output = dict(title = T("Projects Map"),
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
            raise HTTP(501, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_polygons(r, **attr):
        """
            Export Projects as GeoJSON Polygons to view on the map
            - currently assumes that theme_percentages=True

            @ToDo: complete
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
                    budget = project.project_project.total_annual_budget()
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
                    budget = project.project_project.total_annual_budget()
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
                       _style="s3-timeline")

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
            raise HTTP(501, current.ERROR.BAD_METHOD)

# =============================================================================
class S3ProjectActivityModel(S3Model):
    """
        Project Activity Model

        This model holds the specific Activities for Projects
        - currently used in mode_task but not mode_3w
    """

    names = ("project_activity",
             "project_activity_id",
             "project_activity_activity_type",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        add_components = self.add_components
        crud_strings = s3.crud_strings
        define_table = self.define_table

        settings = current.deployment_settings
        mode_task = settings.get_project_mode_task()

        # ---------------------------------------------------------------------
        # Project Activity
        #
        tablename = "project_activity"
        define_table(tablename,
                     # Instance
                     self.super_link("doc_id", "doc_entity"),
                     # Component (each Activity can link to a single Project)
                     self.project_project_id(),
                     Field("name",
                           label = T("Description"),
                           # Activity can simply be a Distribution
                           #requires = IS_NOT_EMPTY(),
                           ),
                     self.project_status_id(),
                     # An Activity happens at a single Location
                     self.gis_location_id(readable = not mode_task,
                                          writable = not mode_task,
                                          ),
                     s3_date("date",
                             label = T("Start Date"),
                             ),
                     s3_date("end_date",
                             label = T("End Date"),
                             ),
                     # Which contact is this?
                     # Implementing Org should be a human_resource_id
                     # Beneficiary could be a person_id
                     # Either way label should be clear
                     self.pr_person_id(label = T("Contact Person"),
                                       requires = IS_ADD_PERSON_WIDGET2(allow_empty=True),
                                       widget = S3AddPersonWidget2(controller="pr"),
                                       ),
                     Field("time_estimated", "double",
                           label = "%s (%s)" % (T("Time Estimate"),
                                                T("hours")),
                           readable = mode_task,
                           writable = mode_task,
                           ),
                     Field("time_actual", "double",
                           label = "%s (%s)" % (T("Time Taken"),
                                                T("hours")),
                           readable = mode_task,
                           # Gets populated from constituent Tasks
                           writable = False,
                           ),
                     # @ToDo: Move to compute using stats_year
                     Field.Method("year", self.project_activity_year),
                     #Field("year", "list:integer",
                     #      compute = lambda row: \
                     #        self.stats_year(row, "project_activity"),
                     #      label = T("Year"),
                     #      ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ACTIVITY_TOOLTIP = T("If you don't see the activity in the list, you can add a new one by clicking link 'Create Activity'.")
        ADD_ACTIVITY = T("Create Activity")
        crud_strings[tablename] = Storage(
            label_create = ADD_ACTIVITY,
            title_display = T("Activity Details"),
            title_list = T("Activities"),
            title_update = T("Edit Activity"),
            title_upload = T("Import Activity Data"),
            title_report = T("Activity Report"),
            label_list_button = T("List Activities"),
            msg_record_created = T("Activity Added"),
            msg_record_modified = T("Activity Updated"),
            msg_record_deleted = T("Activity Deleted"),
            msg_list_empty = T("No Activities Found")
        )

        # Search Method
        filter_widgets = [S3OptionsFilter("status_id",
                                          label = T("Status"),
                                          # Doesn't support translation
                                          #represent = "%(name)s",
                                          # @ToDo: Introspect cols
                                          cols = 3,
                                          ),
                          ]

        # Resource Configuration
        use_projects = settings.get_project_projects()
        list_fields = ["id",
                       "name",
                       "comments",
                       ]

        default_row = "project_id"
        default_col = "name"
        default_fact = "count(id)"
        report_fields = [(T("Activity"), "name"),
                         (T("Year"), "year"),
                         ]
        rappend = report_fields.append

        fact_fields = [(T("Number of Activities"), "count(id)"),
                       ]

        if settings.get_project_activity_types():
            list_fields.insert(1, "activity_type.name")
            rappend((T("Activity Type"), "activity_type.name"))
            default_col = "activity_type.name"
            filter_widgets.append(
                S3OptionsFilter("activity_activity_type.activity_type_id",
                                label = T("Type"),
                                # Doesn't support translation
                                #represent="%(name)s",
                                ))
        if use_projects:
            list_fields.insert(0, "project_id")
            rappend((T("Project"), "project_id"))
            filter_widgets.insert(1,
                S3OptionsFilter("project_id",
                                represent = "%(name)s",
                                ))
        if settings.get_project_sectors():
            rappend("sector_activity.sector_id")
            default_col = "sector_activity.sector_id"
            filter_widgets.append(
                S3OptionsFilter("sector_activity.sector_id",
                                # Doesn't support translation
                                #represent = "%(name)s",
                                ))
        if settings.get_project_themes():
            rappend("theme_activity.theme_id")
            filter_widgets.append(
                S3OptionsFilter("theme_activity.theme_id",
                                # Doesn't support translation
                                #represent = "%(name)s",
                                ))
        # @ToDo: deployment_setting
        if settings.has_module("stats"):
            rappend("beneficiary.parameter_id")
            fact_fields.insert(0,
                               (T("Number of Beneficiaries"), "sum(beneficiary.value)")
                               )
            default_fact = "sum(beneficiary.value)"
            filter_widgets.append(
                    S3OptionsFilter("beneficiary.parameter_id",
                                    # Doesn't support translation
                                    #represent = "%(name)s",
                                    ))
        # @ToDo: deployment_setting
        filter_widgets.append(
            S3OptionsFilter("year",
                            label = T("Year"),
                            #operator = "anyof",
                            #options = lambda: \
                            #    self.stats_year_options("project_activity"),
                            options = project_activity_year_options,
                            ),
            )

        if use_projects and settings.get_project_mode_drr():
            rappend(("project_id$hazard_project.hazard_id"))
            rappend((T("HFA"), "project_id$drr.hfa"))
        if mode_task:
            list_fields.insert(3, "time_estimated")
            list_fields.insert(4, "time_actual")
            rappend((T("Time Estimated"), "time_estimated"))
            rappend((T("Time Actual"), "time_actual"))
            default_fact = "sum(time_actual)"
            #create_next = URL(c="project", f="activity",
            #                  args=["[id]", "task"])
        else:
            #create_next = URL(c="project", f="activity", args=["[id]"])
            # Which levels of Hierarchy are we using?
            levels = current.gis.get_relevant_hierarchy_levels()

            filter_widgets.insert(0,
                S3LocationFilter("location_id",
                                 levels = levels,
                                 ))

            posn = 2
            for level in levels:
                lfield = "location_id$%s" % level
                list_fields.insert(posn, lfield)
                report_fields.append(lfield)
                posn += 1

            # Highest-level of Hierarchy
            default_row = "location_id$%s" % levels[0]

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = fact_fields,
                                 defaults = Storage(rows = default_row,
                                                    cols = default_col,
                                                    fact = default_fact,
                                                    totals = True,
                                                    )
                                 )
        self.configure(tablename,
                       # Leave these workflows for Templates
                       #create_next = create_next,
                       deduplicate = self.project_activity_deduplicate,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       #onaccept = self.project_activity_onaccept,
                       report_options = report_options,
                       super_entity = "doc_entity",
                       )

        # Reusable Field
        represent = project_ActivityRepresent()
        activity_id = S3ReusableField("activity_id", "reference %s" % tablename,
                        comment = S3AddResourceLink(ADD_ACTIVITY,
                                                    c="project", f="activity",
                                                    tooltip=ACTIVITY_TOOLTIP),
                        label = T("Activity"),
                        ondelete = "CASCADE",
                        represent = represent,
                        requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db, "project_activity.id",
                                              represent,
                                              sort=True)),
                        sortby="name",
                        )

        # Also use this Represent for Report drilldowns
        # @todo: make lazy_table
        table = db[tablename]
        table.id.represent = represent

        # Components
        add_components(tablename,
                       # Activity Types
                       project_activity_type = {"link": "project_activity_activity_type",
                                                "joinby": "activity_id",
                                                "key": "activity_type_id",
                                                "actuate": "replace",
                                                "autocomplete": "name",
                                                "autodelete": False,
                                                },
                       # Format for InlineComponent/filter_widget
                       project_activity_activity_type = "activity_id",
                       # Beneficiaries
                       project_beneficiary = {"link": "project_beneficiary_activity",
                                              "joinby": "activity_id",
                                              "key": "beneficiary_id",
                                              "actuate": "hide",
                                              },
                       # Format for InlineComponent/filter_widget
                       project_beneficiary_activity = "activity_id",
                       # Distributions
                       supply_distribution = "activity_id",
                       # Events
                       event_event = {"link": "event_activity",
                                      "joinby": "activity_id",
                                      "key": "event_id",
                                      "actuate": "hide",
                                      },
                       # Organisations
                       org_organisation = {"link": "project_activity_organisation",
                                           "joinby": "activity_id",
                                           "key": "organisation_id",
                                           "actuate": "hide",
                                           },
                       # Format for InlineComponent/filter_widget
                       project_activity_organisation = "activity_id",
                       # Organisation Groups (Coalitions/Networks)
                       org_group = {"link": "project_activity_group",
                                    "joinby": "activity_id",
                                    "key": "group_id",
                                    "actuate": "hide",
                                    },
                       # Format for InlineComponent/filter_widget
                       project_activity_group = "activity_id",
                       # Sectors
                       org_sector = {"link": "project_sector_activity",
                                     "joinby": "activity_id",
                                     "key": "sector_id",
                                     "actuate": "hide",
                                     },
                       # Format for InlineComponent/filter_widget
                       project_sector_activity = "activity_id",
                       # Tasks
                       project_task = {"link": "project_task_activity",
                                       "joinby": "activity_id",
                                       "key": "task_id",
                                       "actuate": "replace",
                                       "autocomplete": "name",
                                       "autodelete": False,
                                       },
                       # Themes
                       project_theme = {"link": "project_theme_activity",
                                        "joinby": "activity_id",
                                        "key": "theme_id",
                                        "actuate": "hide",
                                        },
                       # Format for InlineComponent/filter_widget
                       project_theme_activity = "activity_id",
                       )

        # ---------------------------------------------------------------------
        # Activity Type - Activity Link Table
        #
        tablename = "project_activity_activity_type"
        define_table(tablename,
                     activity_id(empty = False,
                                 ondelete = "CASCADE",
                                 ),
                     self.project_activity_type_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Activity Type"),
            title_display = T("Activity Type"),
            title_list = T("Activity Types"),
            title_update = T("Edit Activity Type"),
            title_upload = T("Import Activity Type data"),
            label_list_button = T("List Activity Types"),
            msg_record_created = T("Activity Type added to Activity"),
            msg_record_modified = T("Activity Type Updated"),
            msg_record_deleted = T("Activity Type removed from Activity"),
            msg_list_empty = T("No Activity Types found for this Activity")
        )

        # Pass names back to global scope (s3.*)
        return dict(project_activity_id = activity_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for model-global names if module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(project_activity_id = lambda **attr: dummy("activity_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        project_id = data.get("project_id")
        name = data.get("name")
        # Match activity by project_id and name
        if project_id and name:
            table = item.table
            query = (table.project_id == project_id) & \
                    (table.name == name)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # ---------------------------------------------------------------------
    @staticmethod
    def project_activity_year(row):
        """
            Virtual field for the project_activity table
            @ToDo: Deprecate: replace with computed field
        """

        if hasattr(row, "project_activity"):
            row = row.project_activity

        try:
            activity_id = row.id
        except AttributeError:
            return []

        if hasattr(row, "date"):
            start_date = row.date
        else:
            start_date = False
        if hasattr(row, "end_date"):
            end_date = row.end_date
        else:
            end_date = False

        if start_date is False or end_date is False:
            s3db = current.s3db
            table = s3db.project_activity
            activity = current.db(table.id == activity_id).select(table.date,
                                                                  table.end_date,
                                                                  cache=s3db.cache,
                                                                  limitby=(0, 1)
                                                                  ).first()
            if activity:
                start_date = activity.date
                end_date = activity.end_date

        if not start_date and not end_date:
            return []
        elif not end_date:
            return [start_date.year]
        elif not start_date:
            return [end_date.year]
        else:
            return list(xrange(start_date.year, end_date.year + 1))

# =============================================================================
class S3ProjectActivityTypeModel(S3Model):
    """
        Project Activity Type Model

        This model holds the Activity Types for Projects
        - it is useful where we don't have the details on the actual Activities,
          but just this summary of Types
    """

    names = ("project_activity_type",
             "project_activity_type_location",
             "project_activity_type_project",
             "project_activity_type_sector",
             "project_activity_type_id",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Activity Types
        #
        tablename = "project_activity_type"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           represent = lambda v: T(v) if v is not None \
                                                      else NONE,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_ACTIVITY_TYPE = T("Create Activity Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_ACTIVITY_TYPE,
            title_display = T("Activity Type"),
            title_list = T("Activity Types"),
            title_update = T("Edit Activity Type"),
            label_list_button = T("List Activity Types"),
            msg_record_created = T("Activity Type Added"),
            msg_record_modified = T("Activity Type Updated"),
            msg_record_deleted = T("Activity Type Deleted"),
            msg_list_empty = T("No Activity Types Found")
        )

        # Reusable Fields
        represent = S3Represent(lookup=tablename, translate=True)
        activity_type_id = S3ReusableField("activity_type_id", "reference %s" % tablename,
                                           label = T("Activity Type"),
                                           ondelete = "SET NULL",
                                           represent = represent,
                                           requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "project_activity_type.id",
                                                                  represent,
                                                                  sort=True)),
                                           sortby = "name",
                                           comment = S3AddResourceLink(title=ADD_ACTIVITY_TYPE,
                                                                       c="project",
                                                                       f="activity_type",
                                                                       tooltip=T("If you don't see the type in the list, you can add a new one by clicking link 'Create Activity Type'.")),
                                           )

        if current.deployment_settings.get_project_sectors():
            # Component (for Custom Form)
            self.add_components(tablename,
                                project_activity_type_sector = "activity_type_id",
                                )

            crud_form = S3SQLCustomForm(
                            "name",
                            # Sectors
                            S3SQLInlineComponent(
                                "activity_type_sector",
                                label=T("Sectors to which this Activity Type can apply"),
                                fields=["sector_id"],
                            ),
                            "comments",
                        )

            self.configure(tablename,
                           crud_form = crud_form,
                           list_fields = ["id",
                                          "name",
                                          (T("Sectors"), "activity_type_sector.sector_id"),
                                          "comments",
                                          ],
                           )

        # ---------------------------------------------------------------------
        # Activity Type - Sector Link Table
        #
        tablename = "project_activity_type_sector"
        define_table(tablename,
                     activity_type_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                     self.org_sector_id(label = "",
                                        empty = False,
                                        ondelete = "CASCADE",
                                        ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Activity Type - Project Location Link Table
        #
        tablename = "project_activity_type_location"
        define_table(tablename,
                     activity_type_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                     self.project_location_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Activity Type - Project Link Table
        #
        tablename = "project_activity_type_project"
        define_table(tablename,
                     activity_type_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                     self.project_project_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Activity Type"),
            title_display = T("Activity Type"),
            title_list = T("Activity Types"),
            title_update = T("Edit Activity Type"),
            title_upload = T("Import Activity Type data"),
            label_list_button = T("List Activity Types"),
            msg_record_created = T("Activity Type added to Project Location"),
            msg_record_modified = T("Activity Type Updated"),
            msg_record_deleted = T("Activity Type removed from Project Location"),
            msg_list_empty = T("No Activity Types found for this Project Location")
        )

        # Pass names back to global scope (s3.*)
        return dict(project_activity_type_id = activity_type_id,
                    )

# =============================================================================
class S3ProjectActivityOrganisationModel(S3Model):
    """
        Project Activity Organisation Model

        This model allows Activities to link to Organisations
                                           &/or Organisation Groups
        - useful when we don't have the details of the Projects
    """

    names = ("project_activity_organisation",
             "project_activity_group",
             )

    def model(self):

        T = current.T

        configure = self.configure
        define_table = self.define_table
        project_activity_id = self.project_activity_id

        # ---------------------------------------------------------------------
        # Activities <> Organisations - Link table
        #
        tablename = "project_activity_organisation"
        define_table(tablename,
                     project_activity_id(empty = False,
                                         ondelete = "CASCADE",
                                         ),
                     self.org_organisation_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                     *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Organization to Activity"),
            title_display = T("Activity Organization"),
            title_list = T("Activity Organizations"),
            title_update = T("Edit Activity Organization"),
            label_list_button = T("List Activity Organizations"),
            msg_record_created = T("Activity Organization Added"),
            msg_record_modified = T("Activity Organization Updated"),
            msg_record_deleted = T("Activity Organization Deleted"),
            msg_list_empty = T("No Activity Organizations Found")
        )

        configure(tablename,
                  deduplicate = self.project_activity_organisation_deduplicate,
                  )

        # ---------------------------------------------------------------------
        # Activities <> Organisation Groups - Link table
        #
        tablename = "project_activity_group"
        define_table(tablename,
                     project_activity_id(empty = False,
                                         ondelete = "CASCADE",
                                         ),
                     self.org_group_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = self.project_activity_group_deduplicate,
                  )

        # Pass names back to global scope (s3.*)
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_organisation_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        activity_id = data.get("activity_id")
        organisation_id = data.get("organisation_id")
        if activity_id and organisation_id:
            table = item.table
            query = (table.activity_id == activity_id) & \
                    (table.organisation_id == organisation_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_group_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        activity_id = data.get("activity_id")
        group_id = data.get("group_id")
        if activity_id and group_id:
            table = item.table
            query = (table.activity_id == activity_id) & \
                    (table.group_id == group_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectActivitySectorModel(S3Model):
    """
        Project Activity Sector Model

        An Activity can be classified to 1 or more Sectors
    """

    names = ("project_sector_activity",)

    def model(self):

        # ---------------------------------------------------------------------
        # Project Activities <> Sectors Link Table
        #
        # @ToDo" When Activity is linked to a Project, ensure these stay in sync
        #
        tablename = "project_sector_activity"
        self.define_table(tablename,
                          self.org_sector_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                          self.project_activity_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = self.project_sector_activity_deduplicate,
                       )

        # Pass names back to global scope (s3.*)
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def project_sector_activity_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        activity_id = data.get("activity_id")
        sector_id = data.get("sector_id")
        if activity_id and sector_id:
            table = item.table
            query = (table.activity_id == activity_id) & \
                    (table.sector_id == sector_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectAnnualBudgetModel(S3Model):
    """
        Project Budget Model

        This model holds the annual budget entries for projects
    """

    names = ("project_annual_budget",)

    def model(self):

        T = current.T
        db = current.db

        # ---------------------------------------------------------------------
        # Annual Budgets
        #
        tablename = "project_annual_budget"
        self.define_table(tablename,
                          self.project_project_id(
                                # Override requires so that update access to the projects isn't required
                                requires = IS_ONE_OF(db, "project_project.id",
                                                     self.project_project_represent
                                                     )
                                ),
                          Field("year", "integer", notnull=True,
                                default = None, # make it current year
                                label = T("Year"),
                                requires = IS_INT_IN_RANGE(1950, 3000),
                                ),
                          Field("amount", "double", notnull=True,
                                default = 0.00,
                                label = T("Amount"),
                                requires = IS_FLOAT_AMOUNT(),
                                ),
                          s3_currency(required=True),
                          *s3_meta_fields())


        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Annual Budget"),
            title_display = T("Annual Budget"),
            title_list = T("Annual Budgets"),
            title_update = T("Edit Annual Budget"),
            title_upload = T("Import Annual Budget data"),
            title_report = T("Report on Annual Budgets"),
            label_list_button = T("List Annual Budgets"),
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
        return dict()

# =============================================================================
class S3ProjectBeneficiaryModel(S3Model):
    """
        Project Beneficiary Model
        - depends on Stats module
    """

    names = ("project_beneficiary_type",
             "project_beneficiary",
             "project_beneficiary_activity",
             "project_beneficiary_activity_type",
             )

    def model(self):

        if not current.deployment_settings.has_module("stats"):
            current.log.warning("Project Beneficiary Model needs Stats module enabling")
            return dict()

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Project Beneficiary Type
        #
        tablename = "project_beneficiary_type"
        define_table(tablename,
                     super_link("parameter_id", "stats_parameter"),
                     Field("name", length=128, unique=True,
                           label = T("Name"),
                           represent = lambda v: T(v) if v is not None \
                                                      else NONE,
                           requires = IS_NOT_IN_DB(db,
                                                   "project_beneficiary_type.name"),
                           ),
                     s3_comments("description",
                                 label = T("Description"),
                                 ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_BNF_TYPE = T("Create Beneficiary Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_BNF_TYPE,
            title_display = T("Beneficiary Type"),
            title_list = T("Beneficiary Types"),
            title_update = T("Edit Beneficiary Type"),
            label_list_button = T("List Beneficiary Types"),
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
        # @ToDo: Split project_id & project_location_id to separate Link Tables
        #
        tablename = "project_beneficiary"
        define_table(tablename,
                     # Instance
                     super_link("data_id", "stats_data"),
                     # Link Fields
                     # populated automatically
                     self.project_project_id(readable = False,
                                             writable = False,
                                             ),
                     self.project_location_id(comment = None),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter",
                                empty = False,
                                instance_types = ("project_beneficiary_type",),
                                label = T("Beneficiary Type"),
                                represent = S3Represent(lookup="stats_parameter",
                                                        translate=True,
                                                        ),
                                readable = True,
                                writable = True,
                                comment = S3AddResourceLink(c="project",
                                                            f="beneficiary_type",
                                                            vars = dict(child = "parameter_id"),
                                                            title=ADD_BNF_TYPE,
                                                            tooltip=T("Please record Beneficiary according to the reporting needs of your project")),
                                ),
                     # Populated automatically from project_location
                     self.gis_location_id(readable = False,
                                          writable = False),
                     Field("value", "integer",
                           label = T("Number"),
                           represent = lambda v: \
                            IS_INT_AMOUNT.represent(v),
                           requires = IS_INT_IN_RANGE(0, 99999999),
                           ),
                     s3_date("date",
                             #empty = False,
                             label = T("Start Date"),
                             ),
                     s3_date("end_date",
                             #empty = False,
                             label = T("End Date"),
                             ),
                     Field("year", "list:integer",
                           compute = lambda row: \
                             self.stats_year(row, "project_beneficiary"),
                           label = T("Year"),
                           ),
                     #self.stats_source_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_BNF = T("Add Beneficiaries")
        crud_strings[tablename] = Storage(
            label_create = ADD_BNF,
            title_display = T("Beneficiaries Details"),
            title_list = T("Beneficiaries"),
            title_update = T("Edit Beneficiaries"),
            title_report = T("Beneficiary Report"),
            label_list_button = T("List Beneficiaries"),
            msg_record_created = T("Beneficiaries Added"),
            msg_record_modified = T("Beneficiaries Updated"),
            msg_record_deleted = T("Beneficiaries Deleted"),
            msg_list_empty = T("No Beneficiaries Found")
        )

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        # Normally only used in Report
        filter_widgets = [
            #S3TextFilter(["project_id$name",
            #              "project_id$code",
            #              "project_id$description",
            #              "project_id$organisation.name",
            #              "project_id$organisation.acronym",
            #              ],
            #             label = T("Search"),
            #             _class = "filter-search",
            #             ),
            #S3OptionsFilter("project_id",
            #                hidden = True,
            #                ),
            S3OptionsFilter("parameter_id",
                            label = T("Beneficiary Type"),
                            #hidden = True,
                            ),
            S3OptionsFilter("year",
                            operator = "anyof",
                            options = lambda: \
                                      self.stats_year_options("project_beneficiary"),
                            hidden = True,
                            ),
            S3LocationFilter("location_id",
                             levels = levels,
                             #hidden = True,
                             ),
            ]

        list_fields = ["project_id",
                       (T("Beneficiary Type"), "parameter_id"),
                       "value",
                       "year",
                       ]

        report_fields = [(T("Beneficiary Type"), "parameter_id"),
                         "project_id",
                         #"project_location_id",
                         "year",
                         ]

        if settings.get_project_sectors():
            report_fields.append("project_id$sector_project.sector_id")
            filter_widgets.insert(0,
                S3OptionsFilter("project_id$sector_project.sector_id",
                                # Doesn't allow translation
                                #represent = "%(name)s",
                                #hidden = True,
                                ))

        if settings.get_project_hazards():
            report_fields.append("project_id$hazard_project.hazard_id")

        if settings.get_project_themes():
            report_fields.append("project_id$theme_project.theme_id")
            filter_widgets.append(
                S3OptionsFilter("project_id$theme_project.theme_id",
                                # Doesn't allow translation
                                #represent = "%(name)s",
                                #hidden = True,
                                ))

        for level in levels:
            lfield = "location_id$%s" % level
            list_fields.append(lfield)
            report_fields.append(lfield)

        if "L0" in levels:
            default_row = "location_id$L0"
        elif "L1" in levels:
            default_row = "location_id$L1"
        else:
            default_row = "beneficiary.project_id"

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = [(T("Number of Beneficiaries"),
                                          "sum(value)"),
                                         ],
                                 defaults = Storage(rows=default_row,
                                                    cols="beneficiary.parameter_id",
                                                    fact="sum(beneficiary.value)",
                                                    totals=True
                                                    ),
                                 )

        configure(tablename,
                  deduplicate = self.project_beneficiary_deduplicate,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.project_beneficiary_onaccept,
                  report_options = report_options,
                  super_entity = "stats_data",
                  )

        # Reusable Field
        beneficiary_id = S3ReusableField("beneficiary_id", "reference %s" % tablename,
            label = T("Beneficiaries"),
            ondelete = "SET NULL",
            represent = self.project_beneficiary_represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "project_beneficiary.id",
                                  self.project_beneficiary_represent,
                                  sort=True)),
            sortby = "name",
            comment = S3AddResourceLink(c="project", f="beneficiary",
                                        title=ADD_BNF,
                                        tooltip=\
                T("If you don't see the beneficiary in the list, you can add a new one by clicking link 'Add Beneficiary'.")),
            )

        self.add_components(tablename,
                            # Activity Types
                            project_activity_type = {"link": "project_beneficiary_activity_type",
                                                     "joinby": "beneficiary_id",
                                                     "key": "activity_type_id",
                                                     "actuate": "hide",
                                                     },
                            # Format for OptionsFilter
                            project_beneficiary_activity_type = "beneficiary_id",
                            )

        # ---------------------------------------------------------------------
        # Beneficiary <> Activity Link Table
        #
        tablename = "project_beneficiary_activity"
        define_table(tablename,
                     self.project_activity_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                     beneficiary_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                     #s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = self.project_beneficiary_activity_deduplicate,
                  )

        # ---------------------------------------------------------------------
        # Beneficiary <> Activity Type Link Table
        #
        tablename = "project_beneficiary_activity_type"
        define_table(tablename,
                     self.project_activity_type_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                     beneficiary_id(empty = False,
                                    ondelete = "CASCADE",
                                    ),
                     #s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = self.project_beneficiary_activity_type_deduplicate,
                  )

        # Pass names back to global scope (s3.*)
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_represent(id, row=None):
        """
            FK representation
            @ToDo: Bulk
        """

        if row:
            return row.type
        if not id:
            return current.messages["NONE"]

        db = current.db
        table = db.project_beneficiary
        ttable = db.project_beneficiary_type
        query = (table.id == id) & \
                (table.parameter_id == ttable.id)
        r = db(query).select(table.value,
                             ttable.name,
                             limitby = (0, 1)).first()
        try:
            return "%s %s" % (r["project_beneficiary.value"],
                              r["project_beneficiary_type.name"])
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

    # ---------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        parameter_id = data.get("parameter_id")
        project_location_id = data.get("project_location_id")
        # Match beneficiary by type and project_location
        if parameter_id and project_location_id:
            table = item.table
            query = (table.parameter_id == parameter_id) & \
                    (table.project_location_id == project_location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # ---------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_activity_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        parameter_id = data.get("parameter_id")
        activity_id = data.get("activity_id")
        # Match beneficiary by type and activity
        if parameter_id and activity_id:
            table = item.table
            query = (table.parameter_id == parameter_id) & \
                    (table.activity_id == activity_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # ---------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_activity_type_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        parameter_id = data.get("parameter_id")
        activity_type_id = data.get("activity_type_id")
        # Match beneficiary by type and activity_type
        if parameter_id and activity_type_id:
            table = item.table
            query = (table.parameter_id == parameter_id) & \
                    (table.activity_type_id == activity_type_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectCampaignModel(S3Model):
    """
        Project Campaign Model
        - used for TERA integration:
          http://www.ifrc.org/en/what-we-do/beneficiary-communications/tera/
        - depends on Stats module
    """

    names = ("project_campaign",
             "project_campaign_message",
             "project_campaign_keyword",
             #"project_campaign_response",
             "project_campaign_response_summary",
             )

    def model(self):

        if not current.deployment_settings.has_module("stats"):
            # Campaigns Model needs Stats module enabling
            return dict()

        T = current.T
        db = current.db

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        location_id = self.gis_location_id

        # ---------------------------------------------------------------------
        # Project Campaign
        #
        tablename = "project_campaign"
        define_table(tablename,
                     #self.project_project_id(),
                     Field("name", length=128, #unique=True,
                           label = T("Name"),
                           #requires = IS_NOT_IN_DB(db,
                           #                        "project_campaign.name")
                           ),
                     s3_comments("description",
                                 label = T("Description"),
                                 ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_CAMPAIGN = T("Create Campaign")
        crud_strings[tablename] = Storage(
            label_create = ADD_CAMPAIGN,
            title_display = T("Campaign"),
            title_list = T("Campaigns"),
            title_update = T("Edit Campaign"),
            label_list_button = T("List Campaigns"),
            msg_record_created = T("Campaign Added"),
            msg_record_modified = T("Campaign Updated"),
            msg_record_deleted = T("Campaign Deleted"),
            msg_list_empty = T("No Campaigns Found")
        )

        # Reusable Field
        represent = S3Represent(lookup=tablename)
        campaign_id = S3ReusableField("campaign_id", "reference %s" % tablename,
                                      sortby="name",
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "project_campaign.id",
                                                              represent,
                                                              sort=True)),
                                      represent = represent,
                                      label = T("Campaign"),
                                      comment = S3AddResourceLink(c="project",
                                                                  f="campaign",
                                                                  title=ADD_CAMPAIGN,
                                                                  tooltip=\
                                        T("If you don't see the campaign in the list, you can add a new one by clicking link 'Add Campaign'.")),
                                      ondelete = "CASCADE")

        add_components(tablename,
                       project_campaign_message = "campaign_id",
                       )

        # ---------------------------------------------------------------------
        # Project Campaign Message
        # - a Message to broadcast to a geographic location (Polygon)
        #
        tablename = "project_campaign_message"
        define_table(tablename,
                     campaign_id(),
                     Field("name", length=128, #unique=True,
                           #requires = IS_NOT_IN_DB(db,
                           #                        "project_campaign.name")
                           ),
                     s3_comments("message",
                                 label = T("Message")),
                     location_id(
                        widget = S3LocationSelectorWidget2(
                           catalog_layers = True,
                           points = False,
                           polygons = True,
                        )
                     ),
                     # @ToDo: Allow selection of which channel message should be sent out on
                     #self.msg_channel_id(),
                     # @ToDo: Record the Message sent out
                     #self.msg_message_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Campaign Message"),
            title_display = T("Campaign Message"),
            title_list = T("Campaign Messages"),
            title_update = T("Edit Campaign Message"),
            label_list_button = T("List Campaign Messages"),
            msg_record_created = T("Campaign Message Added"),
            msg_record_modified = T("Campaign Message Updated"),
            msg_record_deleted = T("Campaign Message Deleted"),
            msg_list_empty = T("No Campaign Messages Found")
        )

        # Reusable Field
        represent = S3Represent(lookup=tablename)
        message_id = S3ReusableField("campaign_message_id", "reference %s" % tablename,
                                     sortby="name",
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "project_campaign_message.id",
                                                              represent,
                                                              sort=True)),
                                     represent = represent,
                                     label = T("Campaign Message"),
                                     ondelete = "CASCADE")

        # Components
        add_components(tablename,
                       # Responses
                       #project_campaign_response = "campaign_message_id",
                       # Summary
                       project_campaign_response_summary = "campaign_message_id",
                       )

        # ---------------------------------------------------------------------
        # Project Campaign Keyword
        # - keywords in responses which are used in Stats reporting
        #
        tablename = "project_campaign_keyword"
        define_table(tablename,
                     super_link("parameter_id", "stats_parameter"),
                     Field("name", length=128, unique=True,
                           label = T("Name"),
                           requires = IS_NOT_IN_DB(db,
                                                   "project_campaign_keyword.name"),
                           ),
                     s3_comments("description",
                                 label = T("Description"),
                                 ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_CAMPAIGN_KW = T("Add Keyword")
        crud_strings[tablename] = Storage(
            label_create = ADD_CAMPAIGN_KW,
            title_display = T("Keyword"),
            title_list = T("Keywords"),
            title_update = T("Edit Keyword"),
            label_list_button = T("List Keywords"),
            msg_record_created = T("Keyword Added"),
            msg_record_modified = T("Keyword Updated"),
            msg_record_deleted = T("Keyword Deleted"),
            msg_list_empty = T("No Keywords Found")
        )

        # Resource Configuration
        configure(tablename,
                  super_entity = "stats_parameter",
                  )

        # ---------------------------------------------------------------------
        # Project Campaign Response
        # - individual response (unused for TERA)
        # - this can be populated by parsing raw responses
        # - these are aggregated into project_campaign_response_summary
        #
        #tablename = "project_campaign_response"
        #define_table(tablename,
        #             message_id(),
                      # This is a component, so needs to be a super_link
                      # - can't override field name, ondelete or requires
        #             super_link("parameter_id", "stats_parameter",
        #                        label = T("Keyword"),
        #                        instance_types = ("project_campaign_keyword",),
        #                        represent = S3Represent(lookup="stats_parameter"),
        #                        readable = True,
        #                        writable = True,
        #                        empty = False,
        #                        ),
                      # Getting this without TERA may be hard!
                      #location_id(writable = False),
                      # @ToDo: Link to the raw Message received
                      #self.msg_message_id(),
        #             s3_datetime(),
        #             s3_comments(),
        #             *s3_meta_fields())

        # CRUD Strings
        #ADD_CAMPAIGN_RESP = T("Add Response")
        #crud_strings[tablename] = Storage(
        #    label_create = ADD_CAMPAIGN_RESP,
        #    title_display = T("Response Details"),
        #    title_list = T("Responses"),
        #    title_update = T("Edit Response"),
        #    title_report = T("Response Report"),
        #    label_list_button = T("List Responses"),
        #    msg_record_created = T("Response Added"),
        #    msg_record_modified = T("Response Updated"),
        #    msg_record_deleted = T("Response Deleted"),
        #    msg_list_empty = T("No Responses Found")
        #)

        # ---------------------------------------------------------------------
        # Project Campaign Response Summary
        # - aggregated responses (by Keyword/Location)
        # - TERA data comes in here
        #
        tablename = "project_campaign_response_summary"
        define_table(tablename,
                     message_id(),
                     # Instance
                     super_link("data_id", "stats_data"),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter",
                                label = T("Keyword"),
                                instance_types = ("project_campaign_keyword",),
                                represent = S3Represent(lookup="stats_parameter"),
                                readable = True,
                                writable = True,
                                empty = False,
                                ),
                     # Populated automatically (by TERA)
                     # & will be a msg_basestation?
                     location_id(writable = False),
                     Field("value", "integer",
                           label = T("Number of Responses"),
                           represent = lambda v: \
                            IS_INT_AMOUNT.represent(v),
                           requires = IS_INT_IN_RANGE(0, 99999999),
                           ),
                     # @ToDo: Populate automatically from time Message is sent?
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
        ADD_CAMPAIGN_RESP_SUMM = T("Add Response Summary")
        crud_strings[tablename] = Storage(
            label_create = ADD_CAMPAIGN_RESP_SUMM,
            title_display = T("Response Summary Details"),
            title_list = T("Response Summaries"),
            title_update = T("Edit Response Summary"),
            title_report = T("Response Summary Report"),
            label_list_button = T("List Response Summaries"),
            msg_record_created = T("Response Summary Added"),
            msg_record_modified = T("Response Summary Updated"),
            msg_record_deleted = T("Response Summary Deleted"),
            msg_list_empty = T("No Response Summaries Found")
        )

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3ProjectFrameworkModel(S3Model):
    """
        Project Framework Model
    """

    names = ("project_framework",
             "project_framework_organisation",
             )

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
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     Field("name", length=255, unique=True,
                           label = T("Name"),
                           ),
                      s3_comments("description",
                                  label = T("Description"),
                                  comment = None,
                                  ),
                      Field("time_frame",
                            label = T("Time Frame"),
                            represent = lambda v: v or messages.NONE,
                            ),
                      *s3_meta_fields())

        # CRUD Strings
        if current.deployment_settings.get_auth_record_approval():
            msg_record_created = T("Policy or Strategy added, awaiting administrator's approval")
        else:
            msg_record_created = T("Policy or Strategy added")
        crud_strings[tablename] = Storage(
            label_create = T("Create Policy or Strategy"),
            title_display = T("Policy or Strategy"),
            title_list = T("Policies & Strategies"),
            title_update = T("Edit Policy or Strategy"),
            title_upload = T("Import Policies & Strategies"),
            label_list_button = T("List Policies & Strategies"),
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

        #filter_widgets = [
        #    S3TextFilter(["name",
        #                  "description",
        #                 ],
        #                 label = T("Name"),
        #                 comment = T("Search for a Policy or Strategy by name or description."),
        #                ),
        #]

        self.configure(tablename,
                       super_entity="doc_entity",
                       crud_form = crud_form,
                       #filter_widgets = filter_widgets,
                       list_fields = ["name",
                                      (ORGANISATIONS, "framework_organisation.organisation_id"),
                                      "description",
                                      "time_frame",
                                      (T("Files"), "document.file"),
                                      ]
                       )

        represent = S3Represent(lookup=tablename)
        framework_id = S3ReusableField("framework_id", "reference %s" % tablename,
                                       label = ORGANISATION,
                                       ondelete = "CASCADE",
                                       represent = represent,
                                       requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "project_framework.id",
                                                              represent
                                                              )),
                                       )

        self.add_components(tablename,
                            project_framework_organisation = "framework_id",
                            )

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
            label_create = T("New Organization"),
            title_display = ORGANISATION,
            title_list = T("Organizations"),
            title_update = T("Edit Organization"),
            label_list_button = T("List Organizations"),
            msg_record_created = T("Organization added to Policy/Strategy"),
            msg_record_modified = T("Organization updated"),
            msg_record_deleted = T("Organization removed from Policy/Strategy"),
            msg_list_empty = T("No Organizations found for this Policy/Strategy")
        )

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3ProjectHazardModel(S3Model):
    """
        Project Hazard Model
    """

    names = ("project_hazard",
             "project_hazard_project",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        NONE = current.messages["NONE"]

        # ---------------------------------------------------------------------
        # Hazard
        #
        tablename = "project_hazard"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           represent = lambda v: T(v) if v is not None \
                                                      else NONE,
                           ),
                     s3_comments(
                        represent = lambda v: T(v) if v is not None \
                                                   else NONE,
                        ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_HAZARD = T("Create Hazard")
        crud_strings[tablename] = Storage(
            label_create = ADD_HAZARD,
            title_display = T("Hazard Details"),
            title_list = T("Hazards"),
            title_update = T("Edit Hazard"),
            title_upload = T("Import Hazards"),
            label_list_button = T("List Hazards"),
            label_delete_button = T("Delete Hazard"),
            msg_record_created = T("Hazard added"),
            msg_record_modified = T("Hazard updated"),
            msg_record_deleted = T("Hazard deleted"),
            msg_list_empty = T("No Hazards currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename, translate=True)
        hazard_id = S3ReusableField("hazard_id", "reference %s" % tablename,
                                    sortby = "name",
                                    label = T("Hazards"),
                                    requires = IS_EMPTY_OR(
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
            label_create = T("New Hazard"),
            title_display = T("Hazard"),
            title_list = T("Hazards"),
            title_update = T("Edit Hazard"),
            title_upload = T("Import Hazard data"),
            label_list_button = T("List Hazards"),
            msg_record_created = T("Hazard added to Project"),
            msg_record_modified = T("Hazard updated"),
            msg_record_deleted = T("Hazard removed from Project"),
            msg_list_empty = T("No Hazards found for this Project"))

        self.configure(tablename,
                       deduplicate = self.project_hazard_project_deduplicate,
                       )

        # Pass names back to global scope (s3.*)
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def project_hazard_project_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        project_id = data.get("project_id")
        hazard_id = data.get("hazard_id")
        if project_id and hazard_id:
            table = item.table
            query = (table.project_id == project_id) & \
                    (table.hazard_id == hazard_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectHRModel(S3Model):
    """
        Optionally link Projects <> Human Resources
    """

    names = ("project_human_resource",)

    def model(self):

        T = current.T

        status_opts = {1: T("Assigned"),
                       #2: T("Standing By"),
                       #3: T("Active"),
                       4: T("Left"),
                       #5: T("Unable to activate"),
                       }

        # ---------------------------------------------------------------------
        # Projects <> Human Resources
        #
        tablename = "project_human_resource"
        self.define_table(tablename,
                          # Instance table
                          self.super_link("cost_item_id", "budget_cost_item"),
                          self.project_project_id(empty = False,
                                                  ondelete = "CASCADE",
                                                  ),
                          self.hrm_human_resource_id(empty = False,
                                                     ondelete = "CASCADE",
                                                     ),
                          Field("status", "integer",
                                default = 1,
                                represent = lambda opt: \
                                       status_opts.get(opt, current.messages.UNKNOWN_OPT),
                                requires = IS_IN_SET(status_opts),
                                ),
                          *s3_meta_fields()
                          )

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Assign Human Resource"),
            title_display = T("Human Resource Details"),
            title_list = T("Assigned Human Resources"),
            title_update = T("Edit Human Resource"),
            label_list_button = T("List Assigned Human Resources"),
            label_delete_button = T("Remove Human Resource from this project"),
            msg_record_created = T("Human Resource assigned"),
            msg_record_modified = T("Human Resource Assignment updated"),
            msg_record_deleted = T("Human Resource unassigned"),
            msg_list_empty = T("No Human Resources currently assigned to this project"))

        if current.deployment_settings.has_module("budget"):
            crud_form = S3SQLCustomForm("project_id",
                                        "human_resource_id",
                                        "status",
                                        S3SQLInlineComponent("allocation",
                                                             label = T("Budget"),
                                                             fields = ["budget_id",
                                                                       "start_date",
                                                                       "end_date",
                                                                       "daily_cost",
                                                                       ],
                                                             ),
                                        )
        else:
            crud_form = None

        self.configure(tablename,
                       crud_form = crud_form,
                       list_fields = [#"project_id", # Not being dropped in component view
                                      "human_resource_id",
                                      "status",
                                      "allocation.budget_id",
                                      "allocation.start_date",
                                      "allocation.end_date",
                                      "allocation.daily_cost",
                                      ],
                       onvalidation = self.project_human_resource_onvalidation,
                       super_entity = "budget_cost_item",
                       )

        # Pass names back to global scope (s3.*)
        return dict()

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
class S3ProjectLocationModel(S3Model):
    """
        Project Location Model
        - these can simply be ways to display a Project on the Map
          or these can be 'Communities'
    """

    names = ("project_location",
             "project_location_id",
             "project_location_contact",
             "project_location_represent",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        settings = current.deployment_settings
        community = settings.get_project_community()
        mode_3w = settings.get_project_mode_3w()

        messages = current.messages
        NONE = messages["NONE"]
        COUNTRY = messages.COUNTRY

        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table

         # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        # ---------------------------------------------------------------------
        # Project Location ('Community')
        #
        tablename = "project_location"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     # Populated onaccept - used for map popups
                     Field("name",
                           writable = False,
                           ),
                     self.project_project_id(),
                     # Enable in templates which desire this:
                     self.project_status_id(readable = False,
                                            writable = False,
                                            ),
                     self.gis_location_id(
                        represent = self.gis_LocationRepresent(sep=", "),
                        requires = IS_LOCATION(),
                        widget = S3LocationAutocompleteWidget(),
                        comment = S3AddResourceLink(c="gis",
                                                    f="location",
                                                    label = T("Create Location"),
                                                    title=T("Location"),
                                                    tooltip=messages.AUTOCOMPLETE_HELP),
                     ),
                     # % breakdown by location
                     Field("percentage", "decimal(3,2)",
                           comment = T("Amount of the Project Budget spent at this location"),
                           default = 0,
                           label = T("Percentage"),
                           readable = mode_3w,
                           requires = IS_DECIMAL_IN_RANGE(0, 1),
                           writable = mode_3w,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        if community:
            LOCATION = T("Community")
            LOCATION_TOOLTIP = T("If you don't see the community in the list, you can add a new one by clicking link 'Create Community'.")
            ADD_LOCATION = T("Create Community")
            crud_strings[tablename] = Storage(
                    label_create = ADD_LOCATION,
                    title_display = T("Community Details"),
                    title_list = T("Communities"),
                    title_update = T("Edit Community Details"),
                    title_upload = T("Import Community Data"),
                    title_report = T("3W Report"),
                    title_map = T("Map of Communities"),
                    label_list_button = T("List Communities"),
                    msg_record_created = T("Community Added"),
                    msg_record_modified = T("Community Updated"),
                    msg_record_deleted = T("Community Deleted"),
                    msg_list_empty = T("No Communities Found")
            )
        else:
            LOCATION = T("Location")
            LOCATION_TOOLTIP = T("If you don't see the location in the list, you can add a new one by clicking link 'Create Location'.")
            ADD_LOCATION = T("Create Location")
            crud_strings[tablename] = Storage(
                    label_create = ADD_LOCATION,
                    title_display = T("Location Details"),
                    title_list = T("Locations"),
                    title_update = T("Edit Location Details"),
                    title_upload = T("Import Location Data"),
                    title_report = T("3W Report"),
                    title_map = T("Map of Projects"),
                    label_list_button = T("List Locations"),
                    msg_record_created = T("Location Added"),
                    msg_record_modified = T("Location updated"),
                    msg_record_deleted = T("Location Deleted"),
                    msg_list_empty = T("No Locations Found")
            )

        # Fields to search by Text
        text_fields = []
        tappend = text_fields.append

        # List fields
        list_fields = ["location_id",
                       ]
        lappend = list_fields.append

        # Report options
        report_fields = []
        rappend = report_fields.append

        for level in levels:
            loc_field = "location_id$%s" % level
            lappend(loc_field)
            rappend(loc_field)
            tappend(loc_field)

        lappend("project_id")
        if settings.get_project_theme_percentages():
            lappend((T("Themes"), "project_id$theme_project.theme_id"))
        else:
            lappend((T("Activity Types"), "activity_type.activity_type_id"))
        lappend("comments")

        # Filter widgets
        if community:
            filter_widgets = [
                S3TextFilter(text_fields,
                             label = T("Name"),
                             comment = T("Search for a Project Community by name."),
                             )
                ]
        else:
            text_fields.extend(("project_id$name",
                                "project_id$code",
                                "project_id$description",
                                ))
            filter_widgets = [
                S3TextFilter(text_fields,
                             label = T("Text"),
                             comment = T("Search for a Project by name, code, location, or description."),
                             )
                ]

        if settings.get_project_sectors():
            filter_widgets.append(S3OptionsFilter("project_id$sector.name",
                                                  label = T("Sector"),
                                                  hidden = True,
                                                  ))

        filter_widgets.extend((
            # This is only suitable for deployments with a few projects
            #S3OptionsFilter("project_id",
            #                label = T("Project"),
            #                hidden = True,
            #                ),
            S3OptionsFilter("project_id$theme_project.theme_id",
                            label = T("Theme"),
                            options = lambda: \
                                get_s3_filter_opts("project_theme",
                                                   translate=True),
                            hidden = True,
                            ),
            S3LocationFilter("location_id",
                             levels = levels,
                             hidden = True,
                             ),
            ))

        report_fields.extend(((messages.ORGANISATION, "project_id$organisation_id"),
                              (T("Project"), "project_id"),
                              (T("Activity Types"), "activity_type.activity_type_id"),
                              ))

        report_options = Storage(rows=report_fields,
                                 cols=report_fields,
                                 fact=report_fields,
                                 defaults=Storage(rows="location.location_id$%s" % levels[0], # Highest-level of Hierarchy
                                                  cols="location.project_id",
                                                  fact="activity_type.activity_type_id",
                                                  aggregate="list",
                                                  totals=True
                                                  )
                                 )

        # Resource Configuration
        configure(tablename,
                  create_next = URL(c="project", f="location",
                                    args=["[id]", "beneficiary"]),
                  deduplicate = self.project_location_deduplicate,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.project_location_onaccept,
                  report_options = report_options,
                  super_entity = "doc_entity",
                  )

        # Components
        add_components(tablename,
                       # Activity Types
                       project_activity_type = {"link": "project_activity_type_location",
                                                "joinby": "project_location_id",
                                                "key": "activity_type_id",
                                                "actuate": "hide",
                                                },
                       # Beneficiaries
                       project_beneficiary = "project_location_id",
                       # Contacts
                       pr_person = {"name": "contact",
                                    "link": "project_location_contact",
                                    "joinby": "project_location_id",
                                    "key": "person_id",
                                    "actuate": "hide",
                                    "autodelete": False,
                                    },
                       # Distributions
                       supply_distribution = "project_location_id",
                       # Themes
                       project_theme = {"link": "project_theme_location",
                                        "joinby": "project_location_id",
                                        "key": "theme_id",
                                        "actuate": "hide",
                                        },
                      )

        # Reusable Field
        project_location_represent = project_LocationRepresent()
        project_location_id = S3ReusableField("project_location_id", "reference %s" % tablename,
            label = LOCATION,
            ondelete = "CASCADE",
            represent = project_location_represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "project_location.id",
                                  project_location_represent,
                                  updateable = True,
                                  sort=True)),
            comment = S3AddResourceLink(ADD_LOCATION,
                                        c="project", f="location",
                                        tooltip=LOCATION_TOOLTIP),
            )

        # ---------------------------------------------------------------------
        # Project Community Contact Person
        #
        tablename = "project_location_contact"
        define_table(tablename,
                     project_location_id(),
                     self.pr_person_id(
                        comment = None,
                        requires = IS_ADD_PERSON_WIDGET2(),
                        widget = S3AddPersonWidget2(controller="pr"),
                        ),
                     *s3_meta_fields())

        # CRUD Strings
        LIST_OF_CONTACTS = T("Community Contacts")
        crud_strings[tablename] = Storage(
            label_create = T("Add Contact"), # Better language for 'Select or Create'
            title_display = T("Contact Details"),
            title_list = T("Contacts"),
            title_update = T("Edit Contact Details"),
            label_list_button = T("List Contacts"),
            msg_record_created = T("Contact Added"),
            msg_record_modified = T("Contact Updated"),
            msg_record_deleted = T("Contact Deleted"),
            msg_list_empty = T("No Contacts Found"))

        # Filter Widgets
        filter_widgets = [
            S3TextFilter(["person_id$first_name",
                          "person_id$middle_name",
                          "person_id$last_name"
                         ],
                         label = T("Name"),
                         comment = T("You can search by person name - enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
                        ),
            S3LocationFilter("project_location_id$location_id",
                             levels = levels,
                             hidden = True,
                             ),
            ]

        # Resource configuration
        configure(tablename,
                  filter_widgets = filter_widgets,
                  list_fields = ["person_id",
                                 (T("Email"), "email.value"),
                                 (T("Mobile Phone"), "phone.value"),
                                 "project_location_id",
                                 (T("Project"), "project_location_id$project_id"),
                                 ],
                  )

        # Components
        add_components(tablename,
                       # Contact Information
                       pr_contact = (# Email
                                     {"name": "email",
                                      "link": "pr_person",
                                      "joinby": "id",
                                      "key": "pe_id",
                                      "fkey": "pe_id",
                                      "pkey": "person_id",
                                      "filterby": "contact_method",
                                      "filterfor": ("EMAIL",),
                                      },
                                     # Mobile Phone
                                     {"name": "phone",
                                      "link": "pr_person",
                                      "joinby": "id",
                                      "key": "pe_id",
                                      "fkey": "pe_id",
                                      "pkey": "person_id",
                                      "filterby": "contact_method",
                                      "filterfor": ("SMS",),
                                      },
                                     ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(project_location_id = project_location_id,
                    project_location_represent = project_location_represent,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for model-global names if module is disabled """

        project_location_id = S3ReusableField("dummy_id", "integer",
                                              readable = False,
                                              writable = False)

        return dict(project_location_id = lambda **attr: dummy("project_location_id"),
                    project_location_represent = lambda v, row=None: "",
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
            name = current.s3db.project_location_represent(None, vars)
        elif id:
            name = current.s3db.project_location_represent(id)
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

        data = item.data
        project_id = data.get("project_id")
        location_id = data.get("location_id")
        if project_id and location_id:
            table = item.table
            query = (table.project_id == project_id) & \
                    (table.location_id == location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectOrganisationModel(S3Model):
    """
        Project Organisation Model
    """

    names = ("project_organisation",)

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
        self.define_table(tablename,
                          self.project_project_id(
                            comment=S3AddResourceLink(c="project",
                                                      f="project",
                                                      vars = dict(prefix="project"),
                                                      tooltip=T("If you don't see the project in the list, you can add a new one by clicking link 'Create Project'."),
                                                      )
                          ),
                          self.org_organisation_id(
                          requires = self.org_organisation_requires(
                                         required=True,
                                         # Need to be able to add Partners/Donors not just Lead org
                                         #updateable=True,
                                         ),
                          widget = None,
                          comment=S3AddResourceLink(c="org",
                                                    f="organisation",
                                                    label=T("Create Organization"),
                                                    title=messages.ORGANISATION,
                                                    tooltip=organisation_help)
                          ),
                          Field("role", "integer",
                                label = T("Role"),
                                requires = IS_EMPTY_OR(
                                             IS_IN_SET(project_organisation_roles)
                                           ),
                                represent = lambda opt: \
                                            project_organisation_roles.get(opt,
                                                                           NONE)),
                          Field("amount", "double",
                                requires = IS_EMPTY_OR(
                                             IS_FLOAT_AMOUNT()),
                                represent = lambda v: \
                                            IS_FLOAT_AMOUNT.represent(v, precision=2),
                                widget = IS_FLOAT_AMOUNT.widget,
                                label = T("Funds Contributed")),
                          s3_currency(),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Organization to Project"),
            title_display = T("Project Organization Details"),
            title_list = T("Project Organizations"),
            title_update = T("Edit Project Organization"),
            title_upload = T("Import Project Organizations"),
            title_report = T("Funding Report"),
            label_list_button = T("List Project Organizations"),
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
                                 defaults = Storage(rows = "organisation_id",
                                                    cols = "currency",
                                                    fact = "sum(amount)",
                                                    totals = False
                                                    )
                                 )

        # Resource Configuration
        self.configure(tablename,
                       deduplicate = self.project_organisation_deduplicate,
                       onaccept = self.project_organisation_onaccept,
                       ondelete = self.project_organisation_ondelete,
                       onvalidation = self.project_organisation_onvalidation,
                       report_options = report_options,
                       )

        # Pass names back to global scope (s3.*)
        return dict()

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
                form.errors.role = \
                    current.T("Lead Implementer for this project is already set, please choose another role.")

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

            # Read the record
            # (safer than relying on vars which might be missing on component tabs)
            db = current.db
            ltable = db.project_organisation
            record = db(ltable.id == vars.id).select(ltable.project_id,
                                                     ltable.organisation_id,
                                                     limitby=(0, 1)
                                                     ).first()

            # Set the Project's organisation_id to the new lead organisation
            organisation_id = record.organisation_id
            ptable = db.project_project
            db(ptable.id == record.project_id).update(
                                organisation_id = organisation_id,
                                realm_entity = \
                                    current.s3db.pr_get_pe_id("org_organisation",
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

    # ---------------------------------------------------------------------
    @staticmethod
    def project_organisation_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        project_id = data.get("project_id")
        organisation_id = data.get("organisation_id")
        if project_id and organisation_id:
            table = item.table
            query = (table.project_id == project_id) & \
                    (table.organisation_id == organisation_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectOutputModel(S3Model):
    """
        Project Output Model
    """

    names = ("project_output",)

    def model(self):

        T = current.T
        db = current.db

        NONE = current.messages["NONE"]

        # ---------------------------------------------------------------------
        # Outputs
        #
        tablename = "project_output"
        self.define_table(tablename,
                          self.project_project_id(
                            # Override requires so that update access to the projects isn't required
                            requires = IS_ONE_OF(db, "project_project.id",
                                                 self.project_project_represent
                                                 )
                            ),
                          Field("name",
                                label = T("Output"),
                                represent = lambda v: v or NONE,
                                ),
                          Field("status",
                                label = T("Status"),
                                represent = lambda v: v or NONE,
                                ),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("New Output"),
            title_display = T("Output"),
            title_list = T("Outputs"),
            title_update = T("Edit Output"),
            label_list_button = T("List Outputs"),
            msg_record_created = T("Output added"),
            msg_record_modified = T("Output updated"),
            msg_record_deleted = T("Output removed"),
            msg_list_empty = T("No outputs found")
        )

        self.configure(tablename,
                       deduplicate = self.project_output_deduplicate,
                       )

        # Pass names back to global scope (s3.*)
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def project_output_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        name = data.get("name")
        if name:
            table = item.table
            query = (table.name == name)
            project_id = data.get("project_id")
            if project_id:
                query &= ((table.project_id == project_id) | \
                          (table.project_id == None))

            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectSectorModel(S3Model):
    """
        Project Sector Model
    """

    names = ("project_sector_project",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Projects <> Sectors Link Table
        #
        tablename = "project_sector_project"
        self.define_table(tablename,
                          self.org_sector_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                          self.project_project_id(empty = False,
                                                  ondelete = "CASCADE",
                                                  ),
                          *s3_meta_fields()
                          )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Sector"),
            title_display = T("Sector"),
            title_list = T("Sectors"),
            title_update = T("Edit Sector"),
            title_upload = T("Import Sector data"),
            label_list_button = T("List Sectors"),
            msg_record_created = T("Sector added to Project"),
            msg_record_modified = T("Sector updated"),
            msg_record_deleted = T("Sector removed from Project"),
            msg_list_empty = T("No Sectors found for this Project")
        )

        # Pass names back to global scope (s3.*)
        return dict()

# =============================================================================
class S3ProjectStatusModel(S3Model):
    """
        Project Status Model
        - used by both Projects & Activities
    """

    names = ("project_status",
             "project_status_id",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Project Statuses
        #
        tablename = "project_status"
        self.define_table(tablename,
                          Field("name", length=128, notnull=True, unique=True,
                                label = T("Name"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD Strings
        ADD_STATUS = T("Create Status")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_STATUS,
            title_display = T("Status Details"),
            title_list = T("Statuses"),
            title_update = T("Edit Status"),
            #title_upload = T("Import Statuses"),
            label_list_button = T("List Statuses"),
            label_delete_button = T("Delete Status"),
            msg_record_created = T("Status added"),
            msg_record_modified = T("Status updated"),
            msg_record_deleted = T("Status deleted"),
            msg_list_empty = T("No Statuses currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename, translate=True)
                                #none = T("Unknown"))
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                        comment = S3AddResourceLink(title=ADD_STATUS,
                                                    c="project",
                                                    f="status"),
                        label = T("Status"),
                        ondelete = "SET NULL",
                        represent = represent,
                        requires = IS_EMPTY_OR(
                                    IS_ONE_OF(current.db, "project_status.id",
                                              represent,
                                              sort=True)),
                        sortby = "name",
                        )

        # Pass names back to global scope (s3.*)
        return dict(project_status_id = status_id,
                    )

# =============================================================================
class S3ProjectThemeModel(S3Model):
    """
        Project Theme Model
    """

    names = ("project_theme",
             "project_theme_id",
             "project_theme_sector",
             "project_theme_project",
             "project_theme_activity",
             "project_theme_location",
             )

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        theme_percentages = current.deployment_settings.get_project_theme_percentages()

        NONE = current.messages["NONE"]

        # ---------------------------------------------------------------------
        # Themes
        #
        tablename = "project_theme"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           represent = lambda v: T(v) if v is not None \
                                                      else NONE,
                           ),
                     s3_comments(
                        represent = lambda v: T(v) if v is not None \
                                                   else NONE,
                        ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_THEME = T("Create Theme")
        crud_strings[tablename] = Storage(
            label_create = ADD_THEME,
            title_display = T("Theme Details"),
            title_list = T("Themes"),
            title_update = T("Edit Theme"),
            #title_upload = T("Import Themes"),
            label_list_button = T("List Themes"),
            label_delete_button = T("Delete Theme"),
            msg_record_created = T("Theme added"),
            msg_record_modified = T("Theme updated"),
            msg_record_deleted = T("Theme deleted"),
            msg_list_empty = T("No Themes currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename, translate=True)
        theme_id = S3ReusableField("theme_id", "reference %s" % tablename,
                                   label = T("Theme"),
                                   ondelete = "CASCADE",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "project_theme.id",
                                                          represent,
                                                          sort=True)),
                                   sortby = "name",
                                   )

        # Components
        add_components(tablename,
                       # Projects
                       project_theme_project = "theme_id",
                       # Sectors
                       project_theme_sector = "theme_id",
                       # For Sync Filter
                       org_sector = {"link": "project_theme_sector",
                                     "joinby": "theme_id",
                                     "key": "sector_id",
                                     },
                       )

        crud_form = S3SQLCustomForm(
                        "name",
                        # Project Sectors
                        S3SQLInlineComponent(
                            "theme_sector",
                            label = T("Sectors to which this Theme can apply"),
                            fields = ["sector_id"],
                        ),
                        "comments"
                    )

        configure(tablename,
                  crud_form = crud_form,
                  list_fields = ["id",
                                 "name",
                                 (T("Sectors"), "theme_sector.sector_id"),
                                 "comments",
                                 ],
                  )

        # ---------------------------------------------------------------------
        # Theme <> Sector Link Table
        #
        tablename = "project_theme_sector"
        define_table(tablename,
                     theme_id(empty = False,
                              ondelete = "CASCADE",
                              ),
                     self.org_sector_id(label = "",
                                        empty = False,
                                        ondelete = "CASCADE",
                                        ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Sector"),
            title_display = T("Sector"),
            title_list = T("Sectors"),
            title_update = T("Edit Sector"),
            title_upload = T("Import Sector data"),
            label_list_button = T("List Sectors"),
            msg_record_created = T("Sector added to Theme"),
            msg_record_modified = T("Sector updated"),
            msg_record_deleted = T("Sector removed from Theme"),
            msg_list_empty = T("No Sectors found for this Theme")
        )

        # ---------------------------------------------------------------------
        # Theme <> Project Link Table
        #
        tablename = "project_theme_project"
        define_table(tablename,
                     theme_id(empty = False,
                              ondelete = "CASCADE",
                              ),
                     self.project_project_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                     # % breakdown by theme (sector in IATI)
                     Field("percentage", "integer",
                           default = 0,
                           label = T("Percentage"),
                           requires = IS_INT_IN_RANGE(0, 101),
                           readable = theme_percentages,
                           writable = theme_percentages,
                           ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Theme"),
            title_display = T("Theme"),
            title_list = T("Themes"),
            title_update = T("Edit Theme"),
            #title_upload = T("Import Theme data"),
            label_list_button = T("List Themes"),
            msg_record_created = T("Theme added to Project"),
            msg_record_modified = T("Theme updated"),
            msg_record_deleted = T("Theme removed from Project"),
            msg_list_empty = T("No Themes found for this Project")
        )

        configure(tablename,
                  deduplicate = self.project_theme_project_deduplicate,
                  onaccept = self.project_theme_project_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Theme <> Activity Link Table
        #
        tablename = "project_theme_activity"
        define_table(tablename,
                     theme_id(empty = False,
                              ondelete = "CASCADE",
                              ),
                     self.project_activity_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                     # % breakdown by theme (sector in IATI)
                     #Field("percentage", "integer",
                     #      label = T("Percentage"),
                     #      default = 0,
                     #      requires = IS_INT_IN_RANGE(0, 101),
                     #      readable = theme_percentages,
                     #      writable = theme_percentages,
                     #      ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("New Theme"),
            title_display = T("Theme"),
            title_list = T("Themes"),
            title_update = T("Edit Theme"),
            #title_upload = T("Import Theme data"),
            label_list_button = T("List Themes"),
            msg_record_created = T("Theme added to Activity"),
            msg_record_modified = T("Theme updated"),
            msg_record_deleted = T("Theme removed from Activity"),
            msg_list_empty = T("No Themes found for this Activity")
        )

        configure(tablename,
                  deduplicate = self.project_theme_activity_deduplicate,
                  #onaccept = self.project_theme_activity_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Theme <> Project Location Link Table
        #
        tablename = "project_theme_location"
        define_table(tablename,
                     theme_id(empty = False,
                              ondelete = "CASCADE",
                              ),
                     self.project_location_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                     # % breakdown by theme (sector in IATI)
                     Field("percentage", "integer",
                           default = 0,
                           label = T("Percentage"),
                           requires = IS_INT_IN_RANGE(0, 101),
                           readable = theme_percentages,
                           writable = theme_percentages,
                           ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("New Theme"),
            title_display = T("Theme"),
            title_list = T("Themes"),
            title_update = T("Edit Theme"),
            title_upload = T("Import Theme data"),
            label_list_button = T("List Themes"),
            msg_record_created = T("Theme added to Project Location"),
            msg_record_modified = T("Theme updated"),
            msg_record_deleted = T("Theme removed from Project Location"),
            msg_list_empty = T("No Themes found for this Project Location")
        )

        # Pass names back to global scope (s3.*)
        return dict()

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

    # -------------------------------------------------------------------------
    @staticmethod
    def project_theme_project_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        project_id = data.get("project_id")
        theme_id = data.get("theme_id")
        if project_id and theme_id:
            table = item.table
            query = (table.project_id == project_id) & \
                    (table.theme_id == theme_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def project_theme_activity_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        activity_id = data.get("activity_id")
        theme_id = data.get("theme_id")
        if activity_id and theme_id:
            table = item.table
            query = (table.activity_id == activity_id) & \
                    (table.theme_id == theme_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()

            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3ProjectDRRModel(S3Model):
    """
        Models for DRR (Disaster Risk Reduction) extensions
    """

    names = ("project_drr",)

    def model(self):

        T = current.T

        hfa_opts = project_hfa_opts()
        options = dict((opt, "HFA %s" % opt) for opt in hfa_opts)

        tablename = "project_drr"
        self.define_table(tablename,
                          self.project_project_id(empty=False),
                          Field("hfa", "list:integer",
                                label = T("HFA Priorities"),
                                represent = S3Represent(options=options,
                                                        multiple=True),
                                requires = IS_EMPTY_OR(IS_IN_SET(
                                            options,
                                            multiple = True)),
                                widget = S3GroupedOptionsWidget(
                                            cols=1,
                                            help_field=hfa_opts
                                         ),
                                ),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def hfa_opts_represent(opt):
        """ Option representation """

        if not opt:
            return current.messages["NONE"]
        if isinstance(opt, int):
            opts = [opt]
        elif not isinstance(opt, (list, tuple)):
            return current.messages["NONE"]
        else:
            opts = opt
        if opts[0] is None:
            return current.messages["NONE"]
        vals = ["HFA %s" % o for o in opts]
        return ", ".join(vals)

# =============================================================================
class S3ProjectDRRPPModel(S3Model):
    """
        Models for DRR Project Portal extensions
        - injected into custom Project CRUD forms
    """

    names = ("project_drrpp",)

    def model(self):

        T = current.T
        db = current.db

        NONE = current.messages["NONE"]

        local_currencies = current.deployment_settings.get_fin_currencies().keys()
        try:
            local_currencies.remove("USD")
        except ValueError:
            # Already removed
            pass

        project_rfa_opts = self.project_rfa_opts()
        project_pifacc_opts = self.project_pifacc_opts()
        project_jnap_opts = self.project_jnap_opts()

        tablename = "project_drrpp"
        self.define_table(tablename,
                          self.project_project_id(
                                # Override requires so that update access to the projects isn't required
                                requires = IS_ONE_OF(db, "project_project.id",
                                                     self.project_project_represent
                                                     )
                                ),
                          Field("parent_project",
                                label =  T("Name of a programme or another project which this project is implemented as part of"),
                                represent = lambda v: v or NONE,
                                #comment = DIV(_class="tooltip",
                                #              _title="%s|%s" % (T("Parent Project"),
                                #                                T("The parent project or programme which this project is implemented under"))),
                                ),
                          Field("duration", "integer",
                                label = T("Duration (months)"),
                                represent = lambda v: v or NONE,
                                ),
                          Field("local_budget", "double",
                                label = T("Total Funding (Local Currency)"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                ),
                          s3_currency("local_currency",
                                      label = T("Local Currency"),
                                      requires = IS_IN_SET(local_currencies,
                                                           zero=None)
                                      ),
                          Field("activities", "text",
                                label = T("Activities"),
                                represent = lambda v: v or NONE,
                                ),
                          Field("rfa", "list:integer",
                                label = T("RFA Priorities"),
                                represent = lambda opt: \
                                    self.opts_represent(opt, "RFA"),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(project_rfa_opts.keys(),
                                                      labels = ["RFA %s" % \
                                                                rfa for rfa in project_rfa_opts.keys()],
                                                      multiple = True)),
                                widget = S3GroupedOptionsWidget(help_field = project_rfa_opts,
                                                                cols = 1,
                                                                ),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("RFA Priorities"),
                                                                T("Applicable to projects in Pacific countries only"))),
                                ),
                          Field("pifacc", "list:integer",
                                label = T("PIFACC Priorities"),
                                represent = lambda opt: \
                                    self.opts_represent(opt, "PIFACC"),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(project_pifacc_opts.keys(),
                                                      labels = ["PIFACC %s" % \
                                                                pifacc for pifacc in project_pifacc_opts.keys()],
                                                      multiple = True)),
                                widget = S3GroupedOptionsWidget(help_field = project_pifacc_opts,
                                                                cols = 1,
                                                                ),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("PIFACC Priorities"),
                                                                T("Pacific Islands Framework for Action on Climate Change. Applicable to projects in Pacific countries only"))),
                                ),
                          Field("jnap", "list:integer",
                                label = T("JNAP Priorities"),
                                represent = lambda opt: \
                                    self.opts_represent(opt, "JNAP"),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(project_jnap_opts.keys(),
                                                      labels = ["JNAP %s" % \
                                                                jnap for jnap in project_jnap_opts.keys()],
                                                      multiple = True)),
                                widget = S3GroupedOptionsWidget(help_field = project_jnap_opts,
                                                                cols = 1,
                                                                ),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("JNAP Priorities"),
                                                                T("Joint National Action Plan for Disaster Risk Management and Climate Change Adaptation. Applicable to Cook Islands only"))),
                                ),
                          Field("L1", "list:integer",
                                label = T("Cook Islands"),
                                represent = S3Represent(lookup="gis_location",
                                                        multiple=True),
                                requires = IS_EMPTY_OR(
                                            IS_ONE_OF(db, "gis_location.id",
                                                      S3Represent(lookup="gis_location"),
                                                      filterby = "L0",
                                                      filter_opts = ("Cook Islands",),
                                                      not_filterby = "name",
                                                      not_filter_opts = ("Cook Islands",),
                                                      multiple=True)),
                                widget = S3GroupedOptionsWidget(size = None, # do not group by letter
                                                                cols = 4,
                                                                ),
                                ),
                          Field("outputs", "text",
                                label = "%s (Old - do NOT use)" % T("Outputs"),
                                represent = lambda v: v or NONE,
                                readable = False,
                                writable = False,
                                ),
                          Field("focal_person",
                                label = T("Focal Person"),
                                represent = lambda v: v or NONE,
                                requires = IS_NOT_EMPTY(),
                                ),
                          self.org_organisation_id(label = T("Organization")),
                          Field("email",
                                label = T("Email"),
                                represent = lambda v: v or NONE,
                                requires = IS_EMPTY_OR(IS_EMAIL()),
                                ),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            title_display = T("DRRPP Extensions"),
            title_update = T("Edit DRRPP Extensions"),
        )

        self.configure(tablename,
                       onaccept = self.project_drrpp_onaccept,
                       )

        # Pass names back to global scope (s3.*)
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def project_drrpp_onaccept(form):
        """
            After DB I/O tasks for Project DRRPP records
        """

        db = current.db
        vars = form.vars
        id = vars.id
        project_id = vars.project_id

        dtable = db.project_drrpp

        if not project_id:
            # Most reliable way to get the project_id is to read the record
            project_id = db(dtable.id == id).select(dtable.project_id,
                                                    limitby=(0, 1)
                                                    ).first().project_id

        table = db.project_project
        hr_id = db(table.id == project_id).select(table.human_resource_id,
                                                  limitby=(0, 1)
                                                  ).first().human_resource_id
        if hr_id:
            s3db = current.s3db
            htable = db.hrm_human_resource
            ctable = s3db.pr_contact
            ptable = db.pr_person
            query = (htable.id == hr_id) & \
                    (ptable.id == htable.person_id)
            left = ctable.on((ctable.pe_id == ptable.pe_id) & \
                             (ctable.contact_method == "EMAIL"))
            row = db(query).select(htable.organisation_id,
                                   ptable.first_name,
                                   ptable.middle_name,
                                   ptable.last_name,
                                   ctable.value,
                                   left=left,
                                   limitby=(0, 1)).first()
            focal_person = s3_fullname(row[ptable])
            organisation_id = row[htable].organisation_id
            email = row[ctable].value
            db(dtable.id == id).update(focal_person = focal_person,
                                       organisation_id = organisation_id,
                                       email = email,
                                       )

    # -------------------------------------------------------------------------
    @staticmethod
    def opts_represent(opt, prefix):
        """ Option representation """

        if isinstance(opt, int):
            opts = [opt]
        if isinstance(opt, (list, tuple)):
            if not opt or opt[0] is None:
                return current.messages["NONE"]
            else:
                return ", ".join(["%s %s" % (prefix, o) for o in opt])
        else:
            return current.messages["NONE"]

# =============================================================================
class S3ProjectTaskModel(S3Model):
    """
        Project Task Model

        This class holds the tables used for an Organisation to manage
        their Tasks in detail.
    """

    names = ("project_milestone",
             "project_tag",
             "project_task",
             "project_task_id",
             "project_time",
             "project_comment",
             "project_task_project",
             "project_task_activity",
             "project_task_milestone",
             "project_task_tag",
             "project_task_represent_w_project",
             "project_task_active_statuses",
             "project_task_project_opts",
             )

    def model(self):

        db = current.db
        T = current.T
        auth = current.auth
        request = current.request
        s3 = current.response.s3
        settings = current.deployment_settings

        project_id = self.project_project_id

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Project Milestone
        #
        tablename = "project_milestone"
        define_table(tablename,
                     # Stage Report
                     super_link("doc_id", "doc_entity"),
                     project_id(),
                     Field("name",
                           label = T("Short Description"),
                           requires = IS_NOT_EMPTY()
                           ),
                     s3_date(),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_MILESTONE = T("Create Milestone")
        crud_strings[tablename] = Storage(
            label_create = ADD_MILESTONE,
            title_display = T("Milestone Details"),
            title_list = T("Milestones"),
            title_update = T("Edit Milestone"),
            #title_upload = T("Import Milestones"),
            label_list_button = T("List Milestones"),
            msg_record_created = T("Milestone Added"),
            msg_record_modified = T("Milestone Updated"),
            msg_record_deleted = T("Milestone Deleted"),
            msg_list_empty = T("No Milestones Found")
        )

        # Reusable Field
        represent = S3Represent(lookup=tablename,
                                fields=["name", "date"],
                                labels="%(name)s: %(date)s",
                                )
        milestone_id = S3ReusableField("milestone_id", "reference %s" % tablename,
                                       label = T("Milestone"),
                                       ondelete = "RESTRICT",
                                       represent = represent,
                                       requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "project_milestone.id",
                                                              represent)),
                                       sortby = "name",
                                       comment = S3AddResourceLink(c="project",
                                                                   f="milestone",
                                                                   title=ADD_MILESTONE,
                                                                   tooltip=T("A project milestone marks a significant date in the calendar which shows that progress towards the overall objective is being made.")),
                                       )

        configure(tablename,
                  deduplicate = self.project_milestone_duplicate,
                  orderby = "project_milestone.date",
                  )

        # ---------------------------------------------------------------------
        # Project Tags
        #
        tablename = "project_tag"
        define_table(tablename,
                     Field("name",
                           label = T("Tag"),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_TAG = T("Create Tag")
        crud_strings[tablename] = Storage(
            label_create = ADD_TAG,
            title_display = T("Tag Details"),
            title_list = T("Tags"),
            title_update = T("Edit Tag"),
            title_upload = T("Import Tags"),
            label_list_button = T("List Tags"),
            msg_record_created = T("Tag added"),
            msg_record_modified = T("Tag updated"),
            msg_record_deleted = T("Tag deleted"),
            msg_list_empty = T("No tags currently defined"))

        # Reusable Field
        represent = S3Represent(lookup=tablename)

        tag_id = S3ReusableField("tag_id", "reference %s" % tablename,
                                 label = T("Tag"),
                                 ondelete = "RESTRICT",
                                 represent = represent,
                                 requires = IS_EMPTY_OR(
                                              IS_ONE_OF(db, "project_tag.id",
                                                        represent)),
                                 sortby = "name",
                                 comment = S3AddResourceLink(c="project",
                                                             f="tag",
                                                             title=ADD_TAG,
                                                             tooltip=T("A project tag helps to assosiate keywords with projects/tasks.")),
                                 )

        # ---------------------------------------------------------------------
        # Tasks
        #
        # Tasks can be linked to Activities or directly to Projects
        # - they can also be used by the Event/Scenario modules
        #
        # @ToDo: Task templates
        # @ToDo: Recurring tasks
        #

        project_task_priority_opts = settings.get_project_task_priority_opts()
        project_task_status_opts = settings.get_project_task_status_opts()
        # Which options for the Status for a Task count as the task being 'Active'
        project_task_active_statuses = [2, 3, 4, 11]

        #staff = auth.s3_has_role("STAFF")
        staff = auth.is_logged_in()

        tablename = "project_task"
        define_table(tablename,
                     super_link("doc_id", "doc_entity"),
                     Field("template", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("name", length=100, notnull=True,
                           label = T("Short Description"),
                           requires = IS_LENGTH(maxsize=100, minsize=1),
                           ),
                     Field("description", "text",
                           label = T("Detailed Description/URL"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Detailed Description/URL"),
                                                           T("Please provide as much detail as you can, including the URL(s) where the bug occurs or you'd like the new feature to go."))),
                           ),
                     self.org_site_id,
                     self.gis_location_id(
                            # Can be enabled & labelled within a Template as-required
                            #label = T("Deployment Location"),
                            readable = False,
                            writable = False
                            ),
                     Field("source",
                           label = T("Source"),
                           ),
                     Field("source_url",
                           label = T("Source Link"),
                           represent = s3_url_represent,
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("priority", "integer",
                           default = 3,
                           label = T("Priority"),
                           represent = lambda opt: \
                                       project_task_priority_opts.get(opt,
                                                                      UNKNOWN_OPT),
                           requires = IS_IN_SET(project_task_priority_opts,
                                                zero=None),
                           ),
                     # Could be a Person, Team or Organisation
                     super_link("pe_id", "pr_pentity",
                                readable = staff,
                                writable = staff,
                                label = T("Assigned to"),
                                filterby = "instance_type",
                                filter_opts = ("pr_person", "pr_group", "org_organisation"),
                                represent = self.project_assignee_represent,
                                # @ToDo: Widget
                                #widget = S3PentityWidget(),
                                #comment = DIV(_class="tooltip",
                                #              _title="%s|%s" % (T("Assigned to"),
                                #                                messages.AUTOCOMPLETE_HELP))
                                ),
                     s3_datetime("date_due",
                                 label = T("Date Due"),
                                 represent = "date",
                                 readable = staff,
                                 writable = staff,
                                 ),
                     Field("time_estimated", "double",
                           label = "%s (%s)" % (T("Time Estimate"),
                                                T("hours")),
                           represent = lambda v: v or "",
                           readable = staff,
                           writable = staff,
                           ),
                     Field("time_actual", "double",
                           label = "%s (%s)" % (T("Time Taken"),
                                                T("hours")),
                           readable = staff,
                           # This comes from the Time component
                           writable = False,
                           ),
                     Field("status", "integer",
                           default = 2,
                           label = T("Status"),
                           represent = lambda opt: \
                                    project_task_status_opts.get(opt,
                                                                 UNKNOWN_OPT),
                           requires = IS_IN_SET(project_task_status_opts,
                                                zero=None),
                           readable = staff,
                           writable = staff,
                           ),
                     Field.Method("task_id", self.project_task_task_id),
                     *s3_meta_fields())

        # Field configurations
        # Comment these if you don't need a Site associated with Tasks
        #table.site_id.readable = table.site_id.writable = True
        #table.site_id.label = T("Check-in at Facility") # T("Managing Office")
        # @todo: make lazy_table
        table = db[tablename]
        table.created_on.represent = lambda dt: \
                                        S3DateTime.date_represent(dt, utc=True)

        # CRUD Strings
        ADD_TASK = T("Create Task")
        crud_strings[tablename] = Storage(
            label_create = ADD_TASK,
            title_display = T("Task Details"),
            title_list = T("All Tasks"),
            title_update = T("Edit Task"),
            title_upload = T("Import Tasks"),
            label_list_button = T("List Tasks"),
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task deleted"),
            msg_list_empty = T("No tasks currently registered"))

        list_fields = ["id",
                       (T("ID"), "task_id"),
                       "priority",
                       ]
        lappend = list_fields.append

        filter_widgets = [S3TextFilter(["name",
                                        "description",
                                        ],
                                       label = T("Search"),
                                       _class = "filter-search",
                                       ),
                          S3OptionsFilter("priority",
                                          options = project_task_priority_opts,
                                          cols = 4,
                                          ),
                          ]
        fappend = filter_widgets.append

        crud_fields = []
        cappend = crud_fields.append
        jquery_ready_append = s3.jquery_ready.append

        use_projects = settings.get_project_projects()
        if use_projects and current.request.function != "project":
            jquery_ready_append = s3.jquery_ready.append
            lappend("task_project.project_id")
            fappend(S3OptionsFilter("task_project.project_id",
                                    options = self.project_task_project_opts,
                                    ))
            cappend(S3SQLInlineComponent("task_project",
                                         label = T("Project"),
                                         fields = [("", "project_id")],
                                         multiple = False,
                                         ))

        if settings.get_project_activities():
            lappend("task_activity.activity_id")
            fappend(S3OptionsFilter("task_activity.activity_id",
                                    options = self.project_task_activity_opts,
                                    ))
            cappend(S3SQLInlineComponent("task_activity",
                                         label = T("Activity"),
                                         fields = [("", "activity_id")],
                                         multiple = False,
                                         ))
            if use_projects:
                # Filter Activity List to just those for the Project
                options = {"trigger": {"alias": "task_project",
                                       "name": "project_id",
                                       },
                           "target": {"alias": "task_activity",
                                      "name": "activity_id",
                                      },
                           "scope": "form",
                           "lookupPrefix": "project",
                           "lookupResource": "activity",
                           "optional": True,
                           }
                jquery_ready_append('''$.filterOptionsS3(%s)''' % \
                                    json.dumps(options, separators=SEPARATORS))

        if settings.get_project_task_tag():
            lappend("task_tag.tag_id")
            fappend(S3OptionsFilter("task_tag.tag_id",
                                    ))
            cappend(S3SQLInlineComponent("task_tag",
                                         label = T("Tags"),
                                         fields = [("", "tag_id")],
                                         ))

        crud_fields.extend(("name",
                            "description",
                            "source",
                            "priority",
                            "pe_id",
                            "date_due",
                            ))

        if settings.get_project_milestones():
            # Use the field in this format to get the custom represent
            lappend("task_milestone.milestone_id")
            fappend(S3OptionsFilter("task_milestone.milestone_id",
                                    options = self.project_task_milestone_opts,
                                    ))
            cappend(S3SQLInlineComponent("task_milestone",
                                         label = T("Milestone"),
                                         fields = [("", "milestone_id")],
                                         multiple = False,
                                         ))
            if use_projects:
                # Filter Milestone List to just those for the Project
                options = {"trigger": {"alias": "task_project",
                                       "name": "project_id",
                                       },
                           "target": {"alias": "task_milestone",
                                      "name": "milestone_id",
                                      },
                           "scope": "form",
                           "lookupPrefix": "project",
                           "lookupResource": "milestone",
                           "optional": True,
                           }
                jquery_ready_append('''$.filterOptionsS3(%s)''' % \
                                    json.dumps(options, separators=SEPARATORS))

        list_fields.extend(("name",
                            "pe_id",
                            "date_due",
                            "time_estimated",
                            "time_actual",
                            "created_on",
                            "status",
                            #"site_id"
                            ))

        filter_widgets.extend((S3OptionsFilter("pe_id",
                                               label = T("Assigned To"),
                                               none = T("Unassigned"),
                                               ),
                               S3OptionsFilter("status",
                                               options = project_task_status_opts,
                                               ),
                               S3OptionsFilter("created_by",
                                               label = T("Created By"),
                                               hidden = True,
                                               ),
                               S3DateFilter("created_on",
                                            label = T("Date Created"),
                                            hide_time = True,
                                            hidden = True,
                                            ),
                               S3DateFilter("date_due",
                                            hide_time = True,
                                            hidden = True,
                                            ),
                               S3DateFilter("modified_on",
                                            label = T("Date Modified"),
                                            hide_time = True,
                                            hidden = True,
                                            ),
                               ))

        crud_fields.extend(("time_estimated",
                            "status",
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
                            ))

        # Custom Form
        crud_form = S3SQLCustomForm(*crud_fields)

        report_options = Storage(rows = list_fields,
                                 cols = list_fields,
                                 fact = list_fields,
                                 defaults = Storage(rows = "task.project",
                                                    cols = "task.pe_id",
                                                    fact = "sum(task.time_estimated)",
                                                    totals = True
                                                    ),
                                 )

        # Resource Configuration
        configure(tablename,
                  context = {#"event": "event.event_id",
                             "incident": "incident.incident_id",
                             "location": "location_id",
                             # Assignee instead?
                             "organisation": "created_by$organisation_id",
                             },
                  copyable = True,
                  #create_next = URL(f="task", args=["[id]"]),
                  create_onaccept = self.project_task_create_onaccept,
                  crud_form = crud_form,
                  extra = "description",
                  extra_fields = ["id"],
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  list_layout = project_task_list_layout,
                  onvalidation = self.project_task_onvalidation,
                  orderby = "project_task.priority,project_task.date_due asc",
                  realm_entity = self.project_task_realm_entity,
                  report_options = report_options,
                  super_entity = "doc_entity",
                  update_onaccept = self.project_task_update_onaccept,
                  )

        # Reusable field
        represent = project_TaskRepresent(show_link=True)
        task_id = S3ReusableField("task_id", "reference %s" % tablename,
                                  label = T("Task"),
                                  ondelete = "CASCADE",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "project_task.id",
                                                          represent)),
                                  sortby = "name",
                                  comment = S3AddResourceLink(c="project",
                                                              f="task",
                                                              title=ADD_TASK,
                                                              tooltip=T("A task is a piece of work that an individual or team can do in 1-2 days.")),
                                  )

        # Representation with project name, for time log form
        project_task_represent_w_project = project_TaskRepresent(show_project=True)

        # Custom Methods
        set_method("project", "task",
                   method = "dispatch",
                   action = self.project_task_dispatch)

        # Components
        add_components(tablename,
                       # Projects (for imports)
                       project_project = {"link": "project_task_project",
                                          "joinby": "task_id",
                                          "key": "project_id",
                                          "actuate": "embed",
                                          "autocomplete": "name",
                                          "autodelete": False,
                                          },
                       # Format for S3SQLInlineComponent
                       project_task_project = "task_id",
                       #project_activity_group = "activity_id",
                       # Activities
                       project_activity = {"link": "project_task_activity",
                                           "joinby": "task_id",
                                           "key": "activity_id",
                                           "actuate": "embed",
                                           "autocomplete": "name",
                                           "autodelete": False,
                                           },
                       # Format for S3SQLInlineComponent
                       project_task_activity = "task_id",
                       # Incidents
                       #event_incident = {"link": "event_task",
                       #                  "joinby": "task_id",
                       #                  "key": "incident_id",
                       #                  "actuate": "embed",
                       #                  "autocomplete": "name",
                       #                  "autodelete": False,
                       #                  },
                       # Format for InlineComponent
                       event_task = {"name": "incident",
                                     "joinby": "task_id",
                                     },
                       # Milestones
                       project_milestone = {"link": "project_task_milestone",
                                            "joinby": "task_id",
                                            "key": "milestone_id",
                                            "actuate": "embed",
                                            "autocomplete": "name",
                                            "autodelete": False,
                                            },
                       # Format for S3SQLInlineComponent
                       project_task_milestone = "task_id",
                       # Tags
                       project_tag = {"link": "project_task_tag",
                                      "joinby": "task_id",
                                      "key": "tag_id",
                                      "actuate": "embed",
                                      "autocomplete": "name",
                                      "autodelete": False,
                                      },
                       # Format for S3SQLInlineComponent
                       project_task_tag = "task_id",
                       # Job titles
                       hrm_job_title = {"link": "project_task_job_title",
                                        "joinby": "task_id",
                                        "key": "job_title_id",
                                        "actuate": "embed",
                                        "autocomplete": "name",
                                        "autodelete": False,
                                        },
                       # Human Resources (assigned)
                       hrm_human_resource = {"link": "project_task_human_resource",
                                             "joinby": "task_id",
                                             "key": "human_resource_id",
                                             "actuate": "embed",
                                             "autocomplete": "name",
                                             "autodelete": False
                                             },
                       # Requests
                       req_req = {"link": "project_task_req",
                                  "joinby": "task_id",
                                  "key": "req_id",
                                  "actuate": "embed",
                                  "autocomplete": "request_number",
                                  "autodelete": False,
                                  },
                       # Time
                       project_time = "task_id",
                       # Comments (for imports))
                       project_comment = "task_id",
                       )

        # ---------------------------------------------------------------------
        # Link Tasks <-> Projects
        #
        tablename = "project_task_project"
        define_table(tablename,
                     task_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     project_id(
                        empty = False,
                        ondelete = "CASCADE",
                        # Override requires so that update access to the projects isn't required
                        requires = IS_ONE_OF(db, "project_project.id",
                                             self.project_project_represent
                                             )
                        ),
                      *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Link task <-> activity
        #
        # Tasks <> Activities
        tablename = "project_task_activity"
        define_table(tablename,
                     task_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     self.project_activity_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Link task <-> milestone
        #
        # Tasks <> Milestones
        tablename = "project_task_milestone"
        define_table(tablename,
                     task_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     milestone_id(empty = False,
                                  ondelete = "CASCADE",
                                  ),
                     *s3_meta_fields())
        # ---------------------------------------------------------------------
        # Link task <-> tags
        #
        # Tasks <> Tags
        tablename = "project_task_tag"
        define_table(tablename,
                     task_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     tag_id(empty = False,
                            ondelete = "CASCADE",
                            ),
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
        define_table(tablename,
                     Field("parent", "reference project_comment",
                           readable = False,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "project_comment.id"
                                       )),
                           ),
                     task_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     Field("body", "text", notnull=True,
                           label = T("Comment"),
                           ),
                     *s3_meta_fields())

        # Resource Configuration
        configure(tablename,
                  list_fields = ["id",
                                 "task_id",
                                 "created_by",
                                 "modified_on"
                                 ],
                  )

        # ---------------------------------------------------------------------
        # Project Time
        # - used to Log hours spent on a Task
        #
        tablename = "project_time"
        define_table(tablename,
                     task_id(
                       requires = IS_ONE_OF(db, "project_task.id",
                                            project_task_represent_w_project,
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
                     Field.Method("day", project_time_day),
                     Field.Method("week", project_time_week),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Log Time Spent"),
            title_display = T("Logged Time Details"),
            title_list = T("Logged Time"),
            title_update = T("Edit Logged Time"),
            title_upload = T("Import Logged Time data"),
            title_report = T("Project Time Report"),
            label_list_button = T("List Logged Time"),
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

        filter_widgets = [
            S3OptionsFilter("person_id",
                            #label = T("Person"),
                            ),
            S3OptionsFilter("task_id$task_project.project_id",
                            #label = T("Project"),
                            options = self.project_task_project_opts,
                            ),
            S3OptionsFilter("task_id$task_activity.activity_id",
                            #label = T("Activity"),
                            options = self.project_task_activity_opts,
                            hidden = True,
                            ),
            S3DateFilter("date",
                         #label = T("Date"),
                         hide_time = True,
                         hidden = True,
                         ),
            ]

        if settings.get_project_milestones():
            # Use the field in this format to get the custom represent
            list_fields.insert(3, (T("Milestone"), "task_id$task_milestone.milestone_id"))
            filter_widgets.insert(3, S3OptionsFilter("task_id$task_milestone.milestone_id",
                                                     #label = T("Milestone"),
                                                     hidden = True,
                                                     ))

        report_fields = list_fields + \
                        [(T("Day"), "day"),
                         (T("Week"), "week")]

        if settings.get_project_sectors():
            report_fields.insert(3, (T("Sector"),
                                     "task_id$task_project.project_id$sector_project.sector_id"))
            filter_widgets.insert(1, S3OptionsFilter("task_id$task_project.project_id$sector_project.sector_id",
                                                     #label = T("Sector"),
                                                     ))

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = report_fields,
                                 defaults = Storage(
                                    rows = "task_id$task_project.project_id",
                                    cols = "person_id",
                                    fact = "sum(hours)",
                                    totals = True,
                                    ),
                                 )

        configure(tablename,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.project_time_onaccept,
                  report_fields = ["date"],
                  report_options = report_options,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(
            project_task_id = task_id,
            project_task_active_statuses = project_task_active_statuses,
            project_task_represent_w_project = project_task_represent_w_project,
            project_task_project_opts = self.project_task_project_opts
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for model-global names if module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(project_task_id = lambda **attr: dummy("task_id"),
                    project_task_active_statuses = [],
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def project_task_task_id(row):
        """ The record ID of a task as separate column in the data table """

        if hasattr(row, "project_task"):
            row = row.project_task
        try:
            return row.id
        except AttributeError:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def project_task_project_opts():
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
        return dict((row.id, row.name) for row in rows)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_task_activity_opts():
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
        rows = db(query).select(atable.id, atable.name)
        return dict((row.id, row.name) for row in rows)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_task_milestone_opts():
        """
            Provide the options for the Milestone search filter
            - all Milestones with Tasks
        """

        db = current.db
        mtable = db.project_milestone
        ttable = db.project_task
        ltable = db.project_task_milestone
        query = (ttable.deleted == False) & \
                (ltable.task_id == ttable.id) & \
                (ltable.milestone_id == mtable.id)
        rows = db(query).select(mtable.id, mtable.name)
        return dict((row.id, row.name) for row in rows)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_assignee_represent(id, row=None):
        """
            FK representation

            @ToDo: Migrate to S3Represent
        """

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

    # -------------------------------------------------------------------------
    @staticmethod
    def project_task_realm_entity(table, record):
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
    def project_task_onvalidation(form):
        """ Task form validation """

        vars = form.vars
        if str(vars.status) == "3" and not vars.pe_id:
            form.errors.pe_id = \
                current.T("Status 'assigned' requires the %(fieldname)s to not be blank") % \
                    dict(fieldname=current.db.project_task.pe_id.label)
        elif vars.pe_id and str(vars.status) == "2":
            # Set the Status to 'Assigned' if left at default 'New'
            vars.status = 3

    # -------------------------------------------------------------------------
    @staticmethod
    def project_task_create_onaccept(form):
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

        if session.s3.incident:
            # Create a link between this Task & the active Incident
            etable = s3db.event_task
            etable.insert(incident_id=session.s3.incident,
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

    # -------------------------------------------------------------------------
    @staticmethod
    def project_task_update_onaccept(form):
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
            links.delete()

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
            links.delete()

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
            links.delete()

        # Notify Assignee
        task_notify(form)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_task_dispatch(r, **attr):
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
            raise HTTP(501, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_milestone_duplicate(item):
        """
            Import item de-duplication
            - Duplicate if same Name & Project
        """

        data = item.data
        name = data.get("name")
        if not name:
            # Nothing we can work with
            return

        table = item.table
        query = (table.name.lower() == name.lower())
        project_id = data.get("project_id")
        if project_id:
            query &= (table.project_id == project_id)

        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def project_time_onaccept(form):
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

# =============================================================================
class S3ProjectTaskHRMModel(S3Model):
    """
        Project Task HRM Model

        This class holds the tables used to link Tasks to Human Resources
        - either individuals or Job Roles
    """

    names = ("project_task_job_title",
             "project_task_human_resource",
             )

    def model(self):

        define_table = self.define_table
        task_id = self.project_task_id

        # ---------------------------------------------------------------------
        # Link Tasks <> Human Resources
        tablename = "project_task_human_resource"
        define_table(tablename,
                     task_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     self.hrm_human_resource_id(empty = False,
                                                # @ToDo: Flag that there are open Tasks Assigned
                                                ondelete = "CASCADE",
                                                ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Link Tasks <> Job Roles
        tablename = "project_task_job_title"
        define_table(tablename,
                     task_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     self.hrm_job_title_id(empty = False,
                                           # @ToDo: Flag that there are open Tasks Assigned
                                           ondelete = "CASCADE",
                                           ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

# =============================================================================
class S3ProjectTaskIReportModel(S3Model):
    """
        Project Task IReport Model

        This class holds the table used to link Tasks with Incident Reports.
        @ToDo: Deprecate as we link to Incidents instead: S3EventTaskModel
    """

    names = ("project_task_ireport",)

    def model(self):

        # Link Tasks <-> Incident Reports
        #
        tablename = "project_task_ireport"
        self.define_table(tablename,
                          self.project_task_id(empty = False,
                                               ondelete = "CASCADE",
                                               ),
                          self.irs_ireport_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                          *s3_meta_fields())

        self.configure(tablename,
                       onaccept=self.task_ireport_onaccept)

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

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
class project_LocationRepresent(S3Represent):
    """ Representation of Project Locations """

    def __init__(self,
                 translate=False,
                 show_link=False,
                 multiple=False,
                 ):

        settings = current.deployment_settings
        if settings.get_project_community():
            # Community is the primary resource
            self.community = True
        else:
            # Location is just a way to display Projects on a map
            self.community = False
        if settings.get_gis_countries() == 1:
            self.multi_country = False
        else:
            self.multi_country = True
        self.use_codes = settings.get_project_codes()

        self.lookup_rows = self.custom_lookup_rows

        super(project_LocationRepresent,
              self).__init__(lookup="project_location",
                             show_link=show_link,
                             translate=translate,
                             multiple=multiple)

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for organisation rows, does a
            join with the projects and locations. Parameters
            key and fields are not used, but are kept for API
            compatiblity reasons.

            @param values: the project_location IDs
        """

        db = current.db
        ltable = current.s3db.project_location
        gtable = db.gis_location
        fields = [ltable.id,    # pkey is needed for the cache
                  gtable.name,
                  gtable.level,
                  gtable.L0,
                  gtable.L1,
                  gtable.L2,
                  gtable.L3,
                  gtable.L4,
                  gtable.L5,
                  ]

        if len(values) == 1:
            query = (ltable.id == values[0]) & \
                    (ltable.location_id == gtable.id)
            limitby = (0, 1)
        else:
            query = (ltable.id.belongs(values)) & \
                    (ltable.location_id == gtable.id)
            limitby = None

        if not self.community:
            ptable = db.project_project
            query &= (ltable.project_id == ptable.id)
            fields.append(ptable.name)
            if self.use_codes:
                fields.append(ptable.code)

        rows = db(query).select(*fields,
                                limitby=limitby)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the joined Row
        """

        community = self.community
        if not self.community:
            prow = row["project_project"]
        row = row["gis_location"]

        name = row.name
        level = row.level
        if level == "L0":
            location = name
        elif name:
            locations = [name]
            lappend = locations.append
            matched = False
            L5 = row.L5
            if L5:
                if L5 == name:
                    matched = True
                else:
                    lappend(L5)
            L4 = row.L4
            if L4:
                if L4 == name:
                    if matched:
                        lappend(L4)
                    matched = True
                else:
                    lappend(L4)
            L3 = row.L3
            if L3:
                if L3 == name:
                    if matched:
                        lappend(L3)
                    matched = True
                else:
                    lappend(L3)
            L2 = row.L2
            if L2:
                if L2 == name:
                    if matched:
                        lappend(L2)
                    matched = True
                else:
                    lappend(L2)
            L1 = row.L1
            if L1:
                if L1 == name:
                    if matched:
                        lappend(L1)
                    matched = True
                else:
                    lappend(L1)
            if self.multi_country:
                L0 = row.L0
                if L0:
                    if L0 == name:
                        if matched:
                            lappend(L0)
                        matched = True
                    else:
                        lappend(L0)
            location = ", ".join(locations)
        else:
            locations = [row[level] for level in ("L5", "L4", "L3", "L2", "L1") if row[level]]
            if self.multi_country:
                L0 = row.L0
                if L0:
                    locations.append(L0)
            location = ", ".join(locations)

        if community:
            return s3_unicode(location)
        else:
            if self.use_codes and prow.code:
                project =  "%s: %s" % (prow.code, prow.name)
            else:
                project = prow.name
            name = "%s (%s)" % (project, location)
            return s3_unicode(name)

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
class project_TaskRepresent(S3Represent):
    """ Representation of project tasks """

    def __init__(self,
                 show_link=False,
                 show_project=False,
                 project_first=True):
        """
            Constructor

            @param show_link: render representation as link to the task
            @param show_project: show the project name in the representation
            @param project_first: show the project name before the task name
        """

        task_url = URL(c="project", f="task", args=["[id]"])

        super(project_TaskRepresent, self).__init__(lookup = "project_task",
                                                    show_link = show_link,
                                                    linkto = task_url,
                                                    )

        self.show_project = show_project
        if show_project:
            self.project_represent = S3Represent(lookup = "project_project")

        self.project_first = project_first

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=[]):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        s3db = current.s3db

        ttable = s3db.project_task
        fields = [ttable.id, ttable.name]

        show_project = self.show_project
        if show_project:
            ltable = s3db.project_task_project
            left = ltable.on(ltable.task_id == ttable.id)
            fields.append(ltable.project_id)
        else:
            left = None

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(left = left, *fields)
        self.queries += 1

        if show_project and rows:
            # Bulk-represent the project_ids
            project_ids = [row.project_task_project.project_id
                           for row in rows]
            if project_ids:
                self.project_represent.bulk(project_ids)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        output = row["project_task.name"]

        if self.show_project:

            project_id = row["project_task_project.project_id"]
            if self.project_first:
                if project_id:
                    strfmt = "%(project)s: %(task)s"
                else:
                    strfmt = "- %(task)s"
            else:
                if project_id:
                    strfmt = "%(task)s (%(project)s)"
                else:
                    strfmt = "%(task)s"

            output = strfmt % {"task": s3_unicode(output),
                               "project": self.project_represent(project_id),
                               }

        return output

# =============================================================================
class project_ActivityRepresent(S3Represent):
    """ Representation of Project Activities """

    def __init__(self,
                 translate=False,
                 show_link=False,
                 multiple=False):

        if current.deployment_settings.get_project_projects():
            # Need a custom lookup
            self.code = True
            self.lookup_rows = self.custom_lookup_rows
            fields = ["project_activity.name",
                      "project_project.code",
                      ]
        else:
            # Can use standard lookup of fields
            self.code = False
            fields = ["name"]

        super(project_ActivityRepresent,
              self).__init__(lookup="project_activity",
                             fields=fields,
                             show_link=show_link,
                             translate=translate,
                             multiple=multiple)

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=[]):
        """
            Custom lookup method for activity rows, does a
            left join with the parent project. Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the activity IDs
        """

        db = current.db
        s3db = current.s3db
        atable = s3db.project_activity
        ptable = s3db.project_project

        left = ptable.on(ptable.id == atable.project_id)

        qty = len(values)
        if qty == 1:
            query = (atable.id == values[0])
            limitby = (0, 1)
        else:
            query = (atable.id.belongs(values))
            limitby = (0, qty)

        rows = db(query).select(atable.id,
                                atable.name,
                                ptable.code,
                                left=left,
                                limitby=limitby)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the project_activity Row
        """

        if self.code:
            # Custom Row (with the project left-joined)
            name = row["project_activity.name"]
            code = row["project_project.code"]
            if not name:
                return row["project_activity.id"]
        else:
            # Standard row (from fields)
            name = row["name"]
            if not name:
                return row["id"]

        if self.code and code:
            name = "%s > %s" % (code, name)
        return s3_unicode(name)

# =============================================================================
def project_activity_year_options():
    """
        returns a dict of the options for the year virtual field
        used by the search widget

        orderby needed for postgres

        @ToDo: Migrate to stats_year_options()
    """

    db = current.db
    table = current.s3db.project_activity
    query = (table.deleted == False)
    min_field = table.date.min()
    start_date_min = db(query).select(min_field,
                                      orderby=min_field,
                                      limitby=(0, 1)
                                      ).first()[min_field]
    if start_date_min:
        start_year = start_date_min.year
    else:
        start_year = None

    max_field = table.end_date.max()
    end_date_max = db(query).select(max_field,
                                    orderby=max_field,
                                    limitby=(0, 1)
                                    ).first()[max_field]
    if end_date_max:
        end_year = end_date_max.year
    else:
        end_year = None

    if not start_year or not end_year:
        return {start_year:start_year} or {end_year:end_year}
    years = {}
    for year in xrange(start_year, end_year + 1):
        years[year] = year
    return years

# =============================================================================
class S3ProjectThemeVirtualFields:
    """ Virtual fields for the project table """

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

    try:
        thisdate = row["project_time.date"]
    except AttributeError:
        return current.messages["NONE"]
    if not thisdate:
        return current.messages["NONE"]

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

    try:
        thisdate = row["project_time.date"]
    except AttributeError:
        return current.messages["NONE"]
    if not thisdate:
        return current.messages["NONE"]

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
    # @ToDo: Move to Static
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
    #auth = current.auth
    settings = current.deployment_settings

    attachments_label = settings.get_ui_label_attachments()
    if resourcename == "project":
        mode_3w = settings.get_project_mode_3w()
        mode_task = settings.get_project_mode_task()

        # Tabs
        #ADMIN = current.session.s3.system_roles.ADMIN
        #admin = auth.s3_has_role(ADMIN)
        #staff = auth.s3_has_role("STAFF")
        #staff = True

        tabs = [(T("Basic Details"), None)]
        append = tabs.append
        if settings.get_project_multiple_organisations():
            append((T("Organizations"), "organisation"))
        if settings.get_project_community():
            append((T("Communities"), "location"))
        elif not mode_task:
            append((T("Locations"), "location"))
        if settings.get_project_theme_percentages():
            append((T("Themes"), "theme"))
        if mode_3w:
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
            STAFF = settings.get_hrm_staff_label()
            #append((STAFF, "human_resource", dict(group="staff")))
            append((STAFF, "human_resource"))
            if current.auth.s3_has_permission("create", "project_human_resource"):
                append((T("Assign %(staff)s") % dict(staff=STAFF), "assign"))
        #if settings.has_module("vol"):
        #    append((T("Volunteers"), "human_resource", dict(group="volunteer")))

        rheader_fields = [["code", "name"],
                          ["organisation_id"],
                          ["start_date", "end_date"]
                          ]
        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    elif resourcename in ["location", "demographic_data"]:
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
                (T("Contact People"), "contact")]
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
        #(T("Roles"), "job_title"),
        #(T("Assignments"), "human_resource"),
        #(T("Requests"), "req")

        rheader_tabs = s3_rheader_tabs(r, tabs)

        # RHeader
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
            project = ""

        atable = s3db.project_activity
        ltable = s3db.project_task_activity
        query = (ltable.deleted == False) & \
                (ltable.task_id == r.id) & \
                (ltable.activity_id == atable.id)
        activity = db(query).select(atable.name,
                                    limitby=(0, 1)).first()
        if activity:
            activity = TR(TH("%s: " % T("Activity")),
                          activity.name
                          )
        else:
            activity = ""

        if record.description:
            description = TR(TH("%s: " % table.description.label),
                             record.description
                             )
        else:
            description = ""

        if record.site_id:
            facility = TR(TH("%s: " % table.site_id.label),
                          table.site_id.represent(record.site_id),
                          )
        else:
            facility = ""

        if record.location_id:
            location = TR(TH("%s: " % table.location_id.label),
                          table.location_id.represent(record.location_id),
                          )
        else:
            location = ""

        if record.created_by:
            creator = TR(TH("%s: " % T("Created By")),
                         s3_auth_user_represent(record.created_by),
                         )
        else:
            creator = ""

        if record.time_estimated:
            time_estimated = TR(TH("%s: " % table.time_estimated.label),
                                record.time_estimated
                                )
        else:
            time_estimated = ""

        if record.time_actual:
            time_actual = TR(TH("%s: " % table.time_actual.label),
                             record.time_actual
                             )
        else:
            time_actual = ""

        rheader = DIV(TABLE(project,
                            activity,
                            TR(TH("%s: " % table.name.label),
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
def project_task_controller():
    """
        Tasks Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    T = current.T
    s3db = current.s3db
    auth = current.auth
    s3 = current.response.s3
    get_vars = current.request.get_vars

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

        if r.method == "datalist":
            # Set list_fields for renderer (project_task_list_layout)
            list_fields = ["name",
                           "description",
                           "location_id",
                           "date_due",
                           "pe_id",
                           #"organisation_id$logo",
                           "modified_by",
                           ]
            if current.deployment_settings.get_project_projects():
                list_fields.insert(5, (T("Project"), "task_project.project_id"))
            s3db.configure("project_task",
                           list_fields = list_fields,
                           )

        elif r.method in ("create", "create.popup"):
            project_id = r.get_vars.get("task_project.project_id", None)
            if project_id:
                # Coming from a profile page
                s3db.project_task_project.project_id.default = project_id
                # Can't do this for an inline form
                #field.readable = field.writable = False

        elif "mine" in get_vars:
            # Show the Open Tasks for this User
            if auth.user:
                pe_id = auth.user.pe_id
                s3.filter = (table.pe_id == pe_id) & \
                            (table.status.belongs(statuses))
            crud_strings.title_list = T("My Open Tasks")
            crud_strings.msg_list_empty = T("No Tasks Assigned")
            s3db.configure(tablename,
                           copyable = False,
                           listadd = False,
                           )

            # No need for assignee (always us) or status (always "assigned"
            # or "reopened") in list fields:
            list_fields = s3db.get_config(tablename, "list_fields")
            if list_fields:
                list_fields[:] = (fn for fn in list_fields
                                     if fn not in ("pe_id", "status"))

        elif "project" in get_vars:
            # Show Open Tasks for this Project
            project = get_vars.project
            ptable = s3db.project_project
            try:
                name = current.db(ptable.id == project).select(ptable.name,
                                                               limitby=(0, 1)
                                                               ).first().name
            except:
                current.session.error = T("Project not Found")
                redirect(URL(args=None, vars=None))
            s3.filter = (FS("task_id:project_task_project.project_id") == project) & \
                        (FS("status").belongs(statuses))
            crud_strings.title_list = T("Open Tasks for %(project)s") % dict(project=name)
            crud_strings.msg_list_empty = T("No Open Tasks for %(project)s") % dict(project=name)
            # Add Activity
            list_fields = s3db.get_config(tablename,
                                          "list_fields")
            try:
                # Hide the project column since we know that already
                list_fields.remove((T("Project"), "task_project.project_id"))
            except ValueError:
                # Already removed
                pass
            s3db.configure(tablename,
                           copyable = False,
                           deletable = False,
                           # Block Add until we get the injectable component lookups
                           insertable = False,
                           list_fields = list_fields,
                           )
        elif "open" in get_vars:
            # Show Only Open Tasks
            crud_strings.title_list = T("All Open Tasks")
            s3.filter = (table.status.belongs(statuses))

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
            if not r.component and r.method != "import":
                # Maintain vars: why?
                update_url = URL(args=["[id]"], vars=get_vars)
                S3CRUD.action_buttons(r, update_url=update_url)
        return output
    s3.postp = postp

    if "mine" in get_vars or "project" in get_vars:
        # Show no filters in pre-filtered views
        hide_filter = True
    else:
        hide_filter = None

    return current.rest_controller("project", "task",
                                   hide_filter = hide_filter,
                                   rheader = s3db.project_rheader,
                                   )

# =============================================================================
def project_theme_help_fields(options):
    """
        Provide the tooltips for the Theme filter

        @param options: the options to generate tooltips for, from
                        S3GroupedOptionsWidget: list of tuples (key, represent)
    """

    table = current.s3db.project_theme
    keys = dict(options).keys()
    rows = current.db(table.id.belongs(keys)).select(table.id,
                                                     table.comments)
    T = current.T
    translated = lambda string: T(string) if string else ""
    tooltips = {}
    for row in rows:
        tooltips[row.id] = translated(row.comments)
    return tooltips

# =============================================================================
def project_hazard_help_fields(options):
    """
        Provide the tooltips for the Hazard filter

        @param options: the options to generate tooltips for, from
                        S3GroupedOptionsWidget: list of tuples (key, represent)
    """

    table = current.s3db.project_hazard
    keys = dict(options).keys()
    rows = current.db(table.id.belongs(keys)).select(table.id,
                                                     table.comments)

    T = current.T
    translated = lambda string: T(string) if string else ""
    tooltips = {}
    for row in rows:
        tooltips[row.id] = translated(row.comments)
    return tooltips

# =============================================================================
def project_hfa_opts():
    """
        Provide the options for the HFA filter

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

# =============================================================================
def project_jnap_opts():
    """
        Provide the options for the JNAP filter (currently unused)

        JNAP (Joint National Action Plan for Disaster Risk Management
        and Climate Change Adaptation): applies to Cook Islands only
    """

    T = current.T
    return {
        1: T("JNAP-1: Strategic Area 1: Governance"),
        2: T("JNAP-2: Strategic Area 2: Monitoring"),
        3: T("JNAP-3: Strategic Area 3: Disaster Management"),
        4: T("JNAP-4: Strategic Area 4: Risk Reduction and Climate Change Adaptation"),
    }

# =============================================================================
def project_pifacc_opts():
    """
        Provide the options for the PIFACC filter (currently unused)

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

# =============================================================================
def project_rfa_opts():
    """
        Provide the options for the RFA filter

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

# =============================================================================
def project_project_filters(org_label):
    """
        Filter widgets for project_project

        @param org_label: the label to use for organisation_id
    """

    T = current.T
    settings = current.deployment_settings

    filter_widgets = [
        S3TextFilter(["name",
                      "code",
                      "description",
                     ],
                     label = T("Search"),
                     comment = T("Search for a Project by name, code, or description."),
                     ),
        S3OptionsFilter("status_id",
                        label = T("Status"),
                        cols = 4,
                        ),
        S3OptionsFilter("organisation_id",
                        label = org_label,
                        # Can be unhidden in customise_xx_resource if there is a need to use a default_filter
                        hidden = True,
                        ),
        S3LocationFilter("location.location_id",
                         # Default should introspect
                         #levels = ("L0", "L1", "L2"),
                         hidden = True,
                         )
        ]

    append_filter = filter_widgets.append

    if settings.get_project_sectors():
        if settings.get_ui_label_cluster():
            sector = T("Cluster")
        else:
            sector = T("Sector")
        append_filter(
            S3OptionsFilter("sector_project.sector_id",
                            label = sector,
                            location_filter = True,
                            none = True,
                            hidden = True,
                            )
        )

    mode_drr = settings.get_project_mode_drr()
    if mode_drr:
        append_filter(
            S3OptionsFilter("hazard_project.hazard_id",
                            label = T("Hazard"),
                            help_field = project_hazard_help_fields,
                            cols = 4,
                            hidden = True,
                            )
        )

    if settings.get_project_mode_3w():
        append_filter(
            S3OptionsFilter("theme_project.theme_id",
                            label = T("Theme"),
                            help_field = project_theme_help_fields,
                            cols = 4,
                            hidden = True,
                            )
        )

    if mode_drr:
        hfa_opts = project_hfa_opts()
        options = dict((key, "HFA %s" % key) for key in hfa_opts)
        #options[None] = current.messages["NONE"] # to search NO HFA
        append_filter(
            S3OptionsFilter("drr.hfa",
                            label = T("HFA"),
                            options = options,
                            help_field = hfa_opts,
                            cols = 5,
                            hidden = True,
                            )
        )

    if settings.get_project_multiple_organisations():
        append_filter(
            S3OptionsFilter("partner.organisation_id",
                            label = T("Partners"),
                            hidden = True,
                            )
        )
        append_filter(
            S3OptionsFilter("donor.organisation_id",
                            label = T("Donors"),
                            hidden = True,
                            )
        )

    return filter_widgets

# =============================================================================
def project_project_list_layout(list_id, item_id, resource, rfields, record,
                                icon="tasks"):
    """
        Default dataList item renderer for Projects on Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["project_project.id"]
    item_class = "thumbnail"

    raw = record._row
    author = record["project_project.modified_by"]
    date = record["project_project.modified_on"]

    name = record["project_project.name"]
    description = record["project_project.description"]
    start_date = record["project_project.start_date"]

    organisation = record["project_project.organisation_id"]
    organisation_id = raw["project_project.organisation_id"]
    location = record["project_location.location_id"]
    location_id = raw["project_location.location_id"]

    comments = raw["project_project.comments"]

    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    org_logo = raw["org_organisation.logo"]
    if org_logo:
        org_logo = A(IMG(_src=URL(c="default", f="download", args=[org_logo]),
                         _class="media-object",
                         ),
                     _href=org_url,
                     _class="pull-left",
                     )
    else:
        # @ToDo: use a dummy logo image
        org_logo = A(IMG(_class="media-object"),
                     _href=org_url,
                     _class="pull-left",
                     )

    # Edit Bar
    # @ToDo: Consider using S3NavigationItem to hide the auth-related parts
    permit = current.auth.s3_has_permission
    table = current.db.project_project
    if permit("update", table, record_id=record_id):
        vars = {"refresh": list_id,
                "record": record_id,
                }
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="project", f="project",
                               args=[record_id, "update.popup"]
                               ),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.project_project.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       _title=current.response.s3.crud_strings.project_project.label_delete_button,
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(I(_class="icon icon-%s" % icon),
                   SPAN(A(name,
                          _href =  URL(c="project", f="project",
                                       args=[record_id, "profile"])),
                        _class="card-title"),
                   SPAN(location, _class="location-title"),
                   SPAN(start_date, _class="date-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(org_logo,
                   DIV(DIV((description or ""),
                           DIV(author or "",
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def project_task_list_layout(list_id, item_id, resource, rfields, record,
                             icon="tasks"):
    """
        Default dataList item renderer for Tasks on Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["project_task.id"]
    item_class = "thumbnail"

    raw = record._row
    author = record["project_task.modified_by"]
    date = record["project_task.modified_on"]

    name = record["project_task.name"]
    assigned_to = record["project_task.pe_id"] or ""
    description = record["project_task.description"]
    date_due = record["project_task.date_due"]
    source_url = raw["project_task.source_url"]
    status = raw["project_task.status"]
    priority = raw["project_task.priority"]

    project_id = raw["project_task_project.project_id"]
    if project_id:
        project = record["project_task_project.project_id"]
        project = SPAN(A(project,
                         _href = URL(c="project", f="project",
                                     args=[project_id, "profile"])
                         ),
                       " > ",
                       _class="task_project_title"
                       )
    else:
        project = ""

    if priority in (1, 2):
        # Urgent / High
        priority_icon = DIV(I(" ", _class="icon-exclamation"),
                            _class="task_priority")
    elif priority == 4:
        # Low
        priority_icon = DIV(I(" ", _class ="icon-arrow-down"),
                            _class="task_priority")
    else:
        priority_icon = ""
    # @ToDo: Support more than just the Wrike/MCOP statuses
    status_icon_colour = {2:  "#AFC1E5",
                          6:  "#C8D571",
                          7:  "#CEC1FF",
                          12: "#C6C6C6",
                          }
    active_statuses = current.s3db.project_task_active_statuses
    status_icon  = DIV(I(" ", _class="icon-check%s" %
                         ("-empty" if status in active_statuses else "" )),
                       _class="task_status",
                       _style="background-color:%s" % (status_icon_colour.get(status, "none"))
                       )

    location = record["project_task.location_id"]
    location_id = raw["project_task.location_id"]

    comments = raw["project_task.comments"]

    org_logo = ""
    #org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    #org_logo = raw["org_organisation.logo"]
    #if org_logo:
    #    org_logo = A(IMG(_src=URL(c="default", f="download", args=[org_logo]),
    #                     _class="media-object",
    #                     ),
    #                 _href=org_url,
    #                 _class="pull-left",
    #                 )
    #else:
    #    # @ToDo: use a dummy logo image
    #    org_logo = A(IMG(_class="media-object"),
    #                 _href=org_url,
    #                 _class="pull-left",
    #                 )

    # Edit Bar
    # @ToDo: Consider using S3NavigationItem to hide the auth-related parts
    permit = current.auth.s3_has_permission
    table = current.db.project_task
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="project", f="task",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id},
                               ),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.project_task.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       _title=current.response.s3.crud_strings.project_task.label_delete_button,
                       )
    else:
        delete_btn = ""

    if source_url:
        source_btn =  A(I(" ", _class="icon icon-link"),
                       _title=source_url,
                       _href=source_url,
                       _target="_blank"
                       )
    else:
        source_btn = ""

    edit_bar = DIV(edit_btn,
                   delete_btn,
                   source_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(I(_class="icon icon-%s" % icon),
                   SPAN(location, _class="location-title"),
                   SPAN(date_due, _class="date-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(org_logo,
                   priority_icon,
                   DIV(project,
                        name, _class="card-title task_priority"),
                   status_icon,
                   DIV(DIV((description or ""),
                           DIV(author,
                               " - ",
                               assigned_to,
                               #A(organisation,
                               #  _href=org_url,
                               #  _class="card-organisation",
                               #  ),
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# END =========================================================================
