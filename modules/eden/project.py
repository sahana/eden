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
           "S3ProjectDRRModel",
           "S3ProjectTaskModel",
           "S3ProjectTaskHRMModel",
           "S3ProjectTaskIReportModel",
           "S3ProjectAnnualBudgetModel",
           "project_rheader",
           "S3ProjectTaskVirtualfields"]

import datetime

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from gluon.sqlhtml import CheckboxesWidget
from gluon.contrib import simplejson as json
from ..s3 import *
from layouts import *

try:
    from lxml import etree, html
except ImportError:
    import sys
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

# =============================================================================
class S3ProjectModel(S3Model):
    """
        Project Model

        Note: This module operates in 2 quite different modes:
         - 'drr':   suitable for use by multinational organisations tracking
                    projects at a high level
         - non-drr: suitable for use by a smaller organsiation tracking tasks
                    at a detailed level

        This class contains the tables common to both uses
        There are additional tabels in S3ProjectDRRModel and S3ProjectTaskModel
        for the other 2 use cases
        There are also additional Classes for optional Link Tables
    """

    names = ["project_theme",
             "project_hazard",
             "project_project",
             "project_activity_type",
             "project_activity",
             "project_community",
             "project_community_contact",
             "project_project_id",
             "project_activity_id",
             "project_multi_activity_id",
             "project_hfa_opts",
             "project_project_represent",
             ]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3
        settings = current.deployment_settings

        currency_type = s3.currency_type
        person_id = self.pr_person_id
        location_id = self.gis_location_id
        countries_id = self.gis_countries_id
        organisation_id = self.org_organisation_id
        sector_id = self.org_sector_id
        human_resource_id = self.hrm_human_resource_id

        s3_date_format = settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        # Enable DRR extensions?
        drr = settings.get_project_drr()
        pca = settings.get_project_community_activity()

        # Shortcuts
        add_component = self.add_component
        comments = s3.comments
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        meta_fields = s3.meta_fields
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Theme
        # @ToDo: Move to link table to move to S3ProjectDRRModel
        #
        tablename = "project_theme"
        table = define_table(tablename,
                             Field("name",
                                   length=128,
                                   notnull=True,
                                   unique=True),
                             Field("comments"),
                             format = "%(name)s",
                             *meta_fields())

        # Field configuration?

        # CRUD Strings?

        # Search Method?

        # Resource Configuration?

        # Reusable Field
        multi_theme_id = S3ReusableField("multi_theme_id",
                                         "list:reference project_theme",
                                         label = T("Themes"),
                                         sortby = "name",
                                         requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                         "project_theme.id",
                                                                         "%(name)s",
                                                                         sort=True,
                                                                         multiple=True)),
                                         represent = lambda opt, row=None: \
                                                     self.multiref_represent(opt, "project_theme"),
                                         default = [],
                                         ondelete = "RESTRICT",
                                         widget = lambda f, v: \
                                                  CheckboxesWidgetS3.widget(f, v, cols = 3))

        # ---------------------------------------------------------------------
        # Hazard
        # @ToDo: Move to link table to move to S3ProjectDRRModel
        #
        tablename = "project_hazard"
        table = define_table(tablename,
                             Field("name",
                                   length=128,
                                   notnull=True,
                                   unique=True),
                             Field("comments"),
                             format="%(name)s",
                             *meta_fields())

        # Field configuration?

        # CRUD Strings?

        # Search Method?

        # Resource Configuration?

        # Reusable Field
        multi_hazard_id = S3ReusableField("multi_hazard_id",
                                          "list:reference project_hazard",
                                          sortby = "name",
                                          label = T("Hazards"),
                                          requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                          "project_hazard.id",
                                                                          "%(name)s",
                                                                          sort=True,
                                                                          multiple=True)),
                                          represent = lambda opt, row=None: \
                                                      self.multiref_represent(opt, "project_hazard"),
                                          ondelete = "RESTRICT",
                                          widget = lambda f, v: CheckboxesWidgetS3.widget(f, v, cols = 3))

        # ---------------------------------------------------------------------
        # Project
        #

        # HFA
        # @todo: localization?
        project_hfa_opts = {
            1: "HFA1: Ensure that disaster risk reduction is a national and a local priority with a strong institutional basis for implementation.",
            2: "HFA2: Identify, assess and monitor disaster risks and enhance early warning.",
            3: "HFA3: Use knowledge, innovation and education to build a culture of safety and resilience at all levels.",
            4: "HFA4: Reduce the underlying risk factors.",
            5: "HFA5: Strengthen disaster preparedness for effective response at all levels.",
        }

        tablename = "project_project"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             # drr uses the separate project_organisation table
                             organisation_id(
                                          readable=False if drr else True,
                                          writable=False if drr else True,
                                        ),
                             Field("name",
                                   label = T("Name"),
                                   # Require unique=True if using IS_NOT_ONE_OF like here (same table,
                                   # no filter) in order to allow both automatic indexing (faster)
                                   # and key-based de-duplication (i.e. before field validation)
                                   unique = True,
                                   requires = [IS_NOT_EMPTY(error_message=T("Please fill this!")),
                                               IS_NOT_ONE_OF(db, "project_project.name")]
                                   ),
                             Field("code",
                                   label = T("Code"),
                                   readable=False,
                                   writable=False,
                                   ),
                             Field("description", "text",
                                   label = T("Description")),
                             # NB There is additional client-side validation for start/end date in the Controller
                             Field("start_date", "date",
                                   label = T("Start date"),
                                   represent = s3_date_represent,
                                   requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                   widget = S3DateWidget()
                                   ),
                             Field("end_date", "date",
                                   label = T("End date"),
                                   represent = s3_date_represent,
                                   requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                   widget = S3DateWidget()
                                   ),
                             Field("duration",
                                   readable=False,
                                   writable=False,
                                   label = T("Duration")),
                             Field("calendar",
                                   readable=False if drr else True,
                                   writable=False if drr else True,
                                   label = T("Calendar"),
                                   requires = IS_NULL_OR(IS_URL()),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Calendar"),
                                                                   T("URL to a Google Calendar to display on the project timeline.")))),
                             currency_type(
                                       readable=False if drr else True,
                                       writable=False if drr else True,
                                       ),
                             Field("budget", "double",
                                   # DRR handles on the Organisations Tab
                                   readable=False if drr else True,
                                   writable=False if drr else True,
                                   label = T("Budget"),
                                   represent=lambda v, row=None: IS_FLOAT_AMOUNT.represent(v, precision=2)),
                             sector_id(
                                       #readable=False,
                                       #writable=False,
                                       widget=lambda f, v: \
                                       CheckboxesWidget.widget(f, v, cols=3)),
                             countries_id(
                                          readable=drr,
                                          writable=drr
                                         ),
                             multi_hazard_id(
                                            readable=drr,
                                            writable=drr
                                            ),
                             multi_theme_id(
                                            readable=drr,
                                            writable=drr
                                           ),
                             Field("hfa", "list:integer",
                                   label = T("HFA Priorities"),
                                   readable=drr,
                                   writable=drr,
                                   requires = IS_NULL_OR(IS_IN_SET(project_hfa_opts,
                                                                   multiple = True)),
                                   represent = self.hfa_opts_represent,
                                   widget = CheckboxesWidgetS3.widget),
                             Field("objectives", "text",
                                   readable = drr,
                                   writable = drr,
                                   label = T("Objectives")),
                             human_resource_id(label=T("Contact Person")),
                             comments(comment=DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("Comments"),
                                                                    T("Outcomes, Impact, Challenges")))),
                             format="%(name)s",
                             *meta_fields())

        # Field configuration?

        # CRUD Strings
        ADD_PROJECT = T("Add Project")
        crud_strings[tablename] = Storage(
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

        # Search Method
        if settings.get_ui_cluster():
            sector = T("Cluster")
        else:
            sector = T("Sector")
        if drr:
            project_search = S3Search(
                    advanced = (
                        S3SearchSimpleWidget(
                            name = "project_search_text_advanced",
                            label = T("Description"),
                            comment = T("Search for a Project by description."),
                            field = [ "name",
                                      "description",
                                    ]
                        ),
                        S3SearchOptionsWidget(
                            name = "project_search_sector",
                            label = sector,
                            field = "sector_id",
                            cols = 4
                        ),
                        S3SearchOptionsWidget(
                            name = "project_search_hazard",
                            label = T("Hazard"),
                            field = "multi_hazard_id",
                            cols = 4
                        ),
                        S3SearchOptionsWidget(
                            name = "project_search_theme",
                            label = T("Theme"),
                            field = "multi_theme_id",
                            cols = 4
                        ),
                        S3SearchOptionsWidget(
                            name = "project_search_hfa",
                            label = T("HFA"),
                            field = "hfa",
                            cols = 4
                        ),
                    )
                )
        else:
            project_search = S3Search(
                    advanced = (
                        S3SearchSimpleWidget(
                            name = "project_search_text_advanced",
                            label = T("Description"),
                            comment = T("Search for a Project by description."),
                            field = [ "name",
                                      "description",
                                    ]
                        ),
                        S3SearchOptionsWidget(
                            name = "project_search_sector",
                            label = sector,
                            field = "sector_id",
                            cols = 4
                        ),
                    )
                )

        # Resource Configuration
        if drr:
            next = "organisation"
        else:
            next = "activity"

        if drr:
            table.virtualfields.append(S3ProjectVirtualfields())
            LEAD_ROLE = settings.get_project_organisation_lead_role()
            list_fields=["id",
                         "name",
                         (settings.get_project_organisation_roles()[LEAD_ROLE], "organisation"),
                         "sector_id",
                         "start_date",
                         "end_date",
                         "countries_id",
                         "multi_hazard_id",
                         "multi_theme_id",
                        ]
        else:
            list_fields=["id",
                         "name",
                         "organisation_id",
                         "start_date",
                         "end_date",
                        ]

        configure(tablename,
                  super_entity="doc_entity",
                  deduplicate=self.project_project_deduplicate,
                  onvalidation=self.project_project_onvalidation,
                  create_next=URL(c="project", f="project",
                                  args=["[id]", next]),
                  search_method=project_search,
                  list_fields=list_fields)

        # Reusable Field
        project_id = S3ReusableField("project_id", db.project_project,
                                     sortby="name",
                                     requires = IS_NULL_OR(IS_ONE_OF(db, "project_project.id",
                                                                     "%(name)s")),
                                     represent = self.project_represent,
                                     comment = S3AddResourceLink(c="project", f="project",
                                                                 tooltip=T("If you don't see the project in the list, you can add a new one by clicking link 'Add Project'.")),
                                     label = T("Project"),
                                     ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Custom Methods
        self.set_method(tablename,
                        method="timeline",
                        action=self.project_timeline)

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

        # Communities
        add_component("project_community", project_project="project_id")

        # Beneficiaries
        add_component("project_beneficiary", project_project="project_id")

        # Annual Budgets
        add_component("project_annual_budget", project_project="project_id")

        # Human Resources
        add_component("project_human_resource", project_project="project_id")

        # ---------------------------------------------------------------------
        # Project Human Resources
        #
        define_table("project_human_resource",
                     project_id(),
                     human_resource_id(),
                     *s3.meta_fields()
                    )

        configure("project_human_resource",
                  list_fields=[
                      "project_id",
                      "human_resource_id$person_id",
                      "human_resource_id$organisation_id",
                      "human_resource_id$job_title",
                      "human_resource_id$status"
                    ],
                onvalidation=self.project_human_resource_onvalidation
                )

        # ---------------------------------------------------------------------
        # Activity Type
        #
        tablename = "project_activity_type"
        table = define_table(tablename,
                             Field("name", length=128,
                                   notnull=True, unique=True),
                             format="%(name)s",
                             *meta_fields())

        # Field configuration?

        # CRUD Strings
        ADD_ACTIVITY_TYPE = T("Add Activity Type")
        LIST_ACTIVITY_TYPES = T("List of Activity Types")
        crud_strings[tablename] = Storage(
            title_create = ADD_ACTIVITY_TYPE,
            title_display = T("Activity Type"),
            title_list = LIST_ACTIVITY_TYPES,
            title_update = T("Edit Activity Type"),
            title_search = T("Search for Activity Type"),
            subtitle_create = T("Add New Activity Type"),
            subtitle_list = T("All Activity Types"),
            label_list_button = LIST_ACTIVITY_TYPES,
            label_create_button = ADD_ACTIVITY_TYPE,
            msg_record_created = T("Activity Type Added"),
            msg_record_modified = T("Activity Type Updated"),
            msg_record_deleted = T("Activity Type Deleted"),
            msg_list_empty = T("No Activity Types Found")
        )

        # Search Method?

        # Resource Configuration?

        # Reusable Fields
        activity_type_id = S3ReusableField("activity_type_id",
                                           db.project_activity_type,
                                           sortby="name",
                                           requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                           "project_activity_type.id",
                                                                           "%(name)s",
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
                                                 requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                                 "project_activity_type.id",
                                                                                 "%(name)s",
                                                                                 sort=True,
                                                                                 multiple=True)),
                                                 represent = lambda opt, row=None: \
                                                             self.multiref_represent(opt,
                                                                                     "project_activity_type"),
                                                 #comment = skill_help,
                                                 default = [],
                                                 widget = lambda f, v: \
                                                    CheckboxesWidgetS3.widget(f, v, col=3),
                                                 ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Project Activity
        #
        tablename = "project_activity"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             project_id(),
                             Field("name",
                                   label = T("Short Description"),
                                   requires=IS_NOT_EMPTY()),
                             location_id(
                                   readable = drr,
                                   writable = drr,
                                   widget = S3LocationSelectorWidget(hide_address=True)),
                             multi_activity_type_id(),
                             Field("time_estimated", "double",
                                   readable=False if drr else True,
                                   writable=False if drr else True,
                                   label = "%s (%s)" % (T("Time Estimate"),
                                                        T("hours"))),
                             Field("time_actual", "double",
                                   readable=False if drr else True,
                                   # Gets populated from constituent Tasks
                                   writable=False,
                                   label = "%s (%s)" % (T("Time Taken"),
                                                        T("hours"))),
                             comments(),
                             format="%(name)s",
                             *(s3.lx_fields() + s3.meta_fields()))

        # Field configuration
        if pca:
            table.name.label = T("Name") # for list_fields
            table.name.readable = False
            table.name.writable = False
            table.name.requires = None

        # CRUD Strings
        if pca:
            ACTIVITY = T("Community")
            ACTIVITY_TOOLTIP = T("If you don't see the community in the list, you can add a new one by clicking link 'Add Community'.")
            ADD_ACTIVITY = T("Add Community")
            LIST_ACTIVITIES = T("List Communities")
            crud_strings[tablename] = Storage(
                title_create = ADD_ACTIVITY,
                title_display = T("Community Details"),
                title_list = LIST_ACTIVITIES,
                title_update = T("Edit Community Details"),
                title_search = T("Search Community"),
                title_upload = T("Import Community Data"),
                title_report = T("Who is doing What Where"),
                subtitle_create = T("Add New Community"),
                subtitle_list = T("Communities"),
                subtitle_report = T("Communities"),
                label_list_button = LIST_ACTIVITIES,
                label_create_button = ADD_ACTIVITY,
                msg_record_created = T("Community Added"),
                msg_record_modified = T("Community Updated"),
                msg_record_deleted = T("Community Deleted"),
                msg_list_empty = T("No Communities Found")
            )
        else:
            ACTIVITY = T("Activity")
            ACTIVITY_TOOLTIP = T("If you don't see the activity in the list, you can add a new one by clicking link 'Add Activity'.")
            ADD_ACTIVITY = T("Add Activity")
            LIST_ACTIVITIES = T("List Activities")
            crud_strings[tablename] = Storage(
                title_create = ADD_ACTIVITY,
                title_display = T("Activity Details"),
                title_list = LIST_ACTIVITIES,
                title_update = T("Edit Activity"),
                title_search = T("Search Activities"),
                title_upload = T("Import Activity Data"),
                title_report = T("Who is doing What Where") if drr else T("Activity Report"),
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

        # Virtual Fields
        if drr:
            table.virtualfields.append(S3ProjectActivityVirtualfields())

        # Search Method
        if pca:
            project_activity_search = S3Search(
                    simple=(
                        S3SearchSimpleWidget(
                            name = "project_activity_search_text",
                            label = T("Name"),
                            comment = T("Search for a Community by name."),
                            field = "location_id$name"
                        ),
                    ),
                    advanced = (
                        S3SearchSimpleWidget(
                            name = "project_activity_search_text_advanced",
                            label = T("Name"),
                            comment = T("Search for a Community by name."),
                            field = "location_id$name"
                        ),
                        S3SearchLocationHierarchyWidget(
                            name="project_activity_search_L1",
                            field="L1",
                            cols = 3,
                      ),
                    )
                )
        else:
            project_activity_search = S3Search(field="name")

        # Resource Configuration
        report_fields = []
        append = report_fields.append
        if drr:
            append((T("Organization"), "organisation"))
        append((T("Project"), "project_id"))
        if not pca:
            append((T("Activity"), "name"))
        append((T("Activity Type"), "multi_activity_type_id"))
        if drr:
            append((T("Sector"), "project_id$sector_id"))
            append((T("Theme"), "project_id$multi_theme_id"))
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
        else:
            append((T("Time Estimated"), "time_estimated"))
            append((T("Time Actual"), "time_actual"))
            list_fields = ["name",
                           "project_id",
                           "multi_activity_type_id",
                           "comments"
                        ]

        if drr:
            # disabled until beneficiaries are updated to support both
            # communities and activities
            #next = "beneficiary"
            next = ""
        else:
            next = "task"
        configure(tablename,
                  super_entity="doc_entity",
                  create_next=URL(c="project", f="activity",
                                  args=["[id]", next]),
                  search_method=project_activity_search,
                  onvalidation=self.project_activity_onvalidation,
                  onaccept=self.project_activity_onaccept,
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
        activity_id = S3ReusableField("activity_id", db.project_activity,
                                      sortby="name",
                                      requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                      "project_activity.id",
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
                                            requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                            "project_activity.id",
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

        # ---------------------------------------------------------------------
        # Beneficiaries
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
        # Project Community
        #
        tablename = "project_community"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             project_id(),
                             Field("name",
                                   label = T("Short Description"),
                                   requires=IS_NOT_EMPTY()
                                   ),
                             location_id(
                                   readable = True,
                                   writable = True,
                                   widget = S3LocationSelectorWidget(hide_address=True)),
                             multi_activity_type_id(),
                             comments(),
                             format="%(name)s",
                             *(s3.lx_fields() + s3.meta_fields()))

        # CRUD Strings
        COMMUNITY = T("Community")
        COMMUNITY_TOOLTIP = T("If you don't see the community in the list, you can add a new one by clicking link 'Add Community'.")
        ADD_COMMUNITY = T("Add Community")
        LIST_COMMUNITIES = T("List Communities")
        crud_strings[tablename] = Storage(
                title_create = ADD_COMMUNITY,
                title_display = T("Community Details"),
                title_list = LIST_COMMUNITIES,
                title_update = T("Edit Community Details"),
                title_search = T("Search Community"),
                title_upload = T("Import Community Data"),
                title_report = T("Who is doing What Where"),
                subtitle_create = T("Add New Community"),
                subtitle_list = T("Communities"),
                subtitle_report = T("Communities"),
                label_list_button = LIST_COMMUNITIES,
                label_create_button = ADD_COMMUNITY,
                msg_record_created = T("Community Added"),
                msg_record_modified = T("Community Updated"),
                msg_record_deleted = T("Community Deleted"),
                msg_list_empty = T("No Communities Found")
        )

        # Search Method
        project_community_search = S3Search(
                simple=(
                    S3SearchSimpleWidget(
                        name = "project_community_search_text",
                        label = T("Name"),
                        comment = T("Search for a Community by name."),
                        field = "location_id$name"
                    ),
                ),
                advanced = (
                    S3SearchSimpleWidget(
                        name = "project_community_search_text_advanced",
                        label = T("Name"),
                        comment = T("Search for a Community by name."),
                        field = "location_id$name"
                    ),
                    S3SearchLocationHierarchyWidget(
                        name="project_community_search_L1",
                        field="L1",
                        cols = 3,
                    ),
                )
        )

        # Resource Configuration
        report_fields = [(T("Community"), "name"),
                         (T("Project"), "project_id"),
                         (T("Activity Type"), "multi_activity_type_id"),
                        ]
        list_fields = ["name",
                       "project_id",
                       "multi_activity_type_id",
                       "comments"
                       ]

        configure(tablename,
                  super_entity="doc_entity",
                  create_next=URL(c="project", f="community",
                                  args=["[id]"]),
                  search_method=project_community_search,
                  onvalidation=self.project_community_onvalidation,
                  onaccept=self.project_community_onaccept,
                  deduplicate=self.project_community_deduplicate,
                  report_options=Storage(
                                         rows=report_fields,
                                         cols=report_fields,
                                         facts=report_fields,
                                         defaults=Storage(
                                                          rows="project_id",
                                                          cols="name",
                                                          fact="multi_activity_type_id",
                                                          aggregate="list",
                                                          totals=True
                                                          )
                                         ),
                  list_fields = list_fields,
                  )

        # Reusable Field
        community_id = S3ReusableField("community_id", db.project_community,
                                      sortby="name",
                                      requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                      "project_community.id",
                                                                      "%(name)s",
                                                                      sort=True)),
                                      represent = lambda id, row=None: \
                                                  s3_get_db_field_value(tablename = "project_community",
                                                                        fieldname = "name",
                                                                        look_up_value = id),
                                      label = COMMUNITY,
                                      comment = S3AddResourceLink(ADD_COMMUNITY,
                                                                  c="project", f="community",
                                                                  tooltip=COMMUNITY_TOOLTIP),
                                      ondelete = "CASCADE")

        # Project Community Contact Persons
        add_component("pr_person",
                      project_community=Storage(
                            name="contact",
                            link="project_community_contact",
                            joinby="community_id",
                            key="person_id",
                            actuate="hide",
                            autodelete=False))

        # Beneficiaries
        add_component("project_beneficiary",
                      project_community="community_id")


        # ---------------------------------------------------------------------
        # Project Community Contact Person
        #
        tablename = "project_community_contact"
        table = define_table(tablename,
                             community_id(),
                             person_id(widget=S3AddPersonWidget(controller="pr"),
                                       requires=IS_ADD_PERSON_WIDGET(),
                                       comment=None),
                             *meta_fields())

        table.virtualfields.append(S3ProjectCommunityContactVirtualFields())

        # CRUD Strings
        ADD_CONTACT = T("Add Contact")
        LIST_CONTACTS = T("List Contacts")
        LIST_OF_CONTACTS = T("Community Contacts")
        crud_strings[tablename] = Storage(
            title_create = ADD_CONTACT,
            title_display = T("Contact Details"),
            title_list = LIST_CONTACTS,
            title_update = T("Edit Contact Details"),
            title_search = T("Search Contacts"),
            subtitle_create = T("Add New Contact"),
            subtitle_list = LIST_OF_CONTACTS,
            label_list_button = LIST_CONTACTS,
            label_create_button = ADD_CONTACT,
            msg_record_created = T("Contact Added"),
            msg_record_modified = T("Contact Updated"),
            msg_record_deleted = T("Contact Deleted"),
            msg_list_empty = T("No Contacts Found"))

        activity_contact_search = S3Search(
            advanced=(S3SearchSimpleWidget(
                            name = "community_contact_search_simple",
                            label = T("Name"),
                            comment = T("You can search by person name - enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
                            field = ["person_id$first_name",
                                     "person_id$middle_name",
                                     "person_id$last_name"
                                    ]
                        ),
                        S3SearchLocationHierarchyWidget(
                            name="community_contact_search_L1",
                            field="person_id$L1",
                            cols = 3,
                        ),
                        S3SearchLocationHierarchyWidget(
                            name="community_contact_search_L2",
                            field="person_id$L2",
                            cols = 3,
                        ),
                    ))

        # Resource configuration
        hierarchy = current.gis.get_location_hierarchy()
        configure(tablename,
                  search_method=activity_contact_search,
                  list_fields=["community_id",
                               (T("Project"), "community_id$project_id"),
                               "person_id",
                               (hierarchy["L0"], "person_id$L0"),
                               (hierarchy["L1"], "person_id$L1"),
                               (hierarchy["L2"], "person_id$L2"),
                               (hierarchy["L3"], "person_id$L3"),
                               (T("Email"), "email"),
                               (T("Mobile Phone"), "sms")])

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return dict(
            project_project_id = project_id,
            project_activity_id = activity_id,
            project_community_id = community_id,
            project_multi_activity_id = multi_activity_id,
            project_hfa_opts = project_hfa_opts,
            project_project_represent = self.project_represent,
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
            project_activity_id = lambda: dummy("activity_id"),
            project_community_id = lambda: dummy("community_id"),
            project_project_represent = lambda v, r: current.messages.NONE,
            project_multi_activity_id = multi_activity_id
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def multiref_represent(opts, tablename, represent_string = "%(name)s"):
        """
            Represent a list of references

            @param opt: the current value or list of values
            @param tablename: the referenced table
            @param represent_string: format string to represent the records
        """

        DEFAULT = ""

        db = current.db
        s3db = current.s3db
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        table = s3db.table(tablename, None)
        if table is None:
            return DEFAULT

        if not isinstance(opts, (list, tuple)):
            opts = [opts]

        rows = db(table.id.belongs(opts)).select()
        rstr = Storage([(str(row.id), row) for row in rows])
        keys = rstr.keys()
        represent = lambda o: str(o) in keys and \
                              represent_string % rstr[str(o)] or UNKNOWN_OPT
        vals = [represent(o) for o in opts]

        if len(opts) > 1:
            vals = ", ".join(vals)
        else:
            vals = len(vals) and vals[0] or DEFAULT

        return vals

    # -------------------------------------------------------------------------
    @staticmethod
    def project_represent(id, row=None, show_link=True):
        """ FK representation """

        db = current.db
        NONE = current.messages.NONE

        if id:
            val = (id and [db.project_project[id].name] or [NONE])[0]
            if not show_link:
                return val
            return A(val, _href = URL(c="project",
                                      f="project",
                                      args=[id]))
        else:
            return NONE

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

        if item.id:
            return
        if item.tablename == "project_project" and \
            "name" in item.data:
            # Match project by name (all-lowercase)
            table = item.table
            name = item.data.name
            try:
                query = (table.name.lower() == name.lower())
            except AttributeError, exception:
                s3_debug("project_deduplicate", exception.message)
            else:
                duplicate = current.db(query).select(table.id,
                                                     table.name,
                                                     limitby=(0, 1)).first()
                if duplicate:
                    item.id = duplicate.id
                    item.data.name = duplicate.name
                    item.method = item.METHOD.UPDATE
        return

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

            T = current.T
            request = current.request
            response = current.response
            session = current.session
            s3 = response.s3

            calendar = r.record.calendar

            # Add core Simile Code
            s3.scripts.append("/%s/static/scripts/simile/timeline/timeline-api.js" % request.application)

            # Pass vars to our JS code
            s3.js_global.append("S3.timeline.calendar = '%s';" % calendar)

            # Add our control script
            if session.s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.js" % request.application)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.min.js" % request.application)

            # Create the DIV
            item = DIV(_id="s3timeline", _style="height: 400px; border: 1px solid #aaa; font-family: Trebuchet MS, sans-serif; font-size: 85%;")

            output = dict(item=item)

            output["title"] = T("Project Calendar")

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
    def hfa_opts_represent(opt, row=None):
        """ Option representation """

        s3 = current.response.s3
        NONE = current.messages.NONE

        project_hfa_opts = s3.project_hfa_opts

        opts = opt
        if isinstance(opt, int):
            opts = [opt]
        elif not isinstance(opt, (list, tuple)):
            return NONE
        vals = [project_hfa_opts.get(o, NONE) for o in opts]
        return ", ".join(vals)

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_onvalidation(form):
        """
        """

        pca = current.deployment_settings.get_project_community_activity()

        if pca:
            location_id = form.vars.location_id
            if location_id:
                db = current.db
                s3db = current.s3db
                table = s3db.gis_location
                query = (table.id == form.vars.location_id)
                row = db(query).select(table.parent,
                                       limitby=(0, 1)).first()
                if row and row.parent:
                    query = (table.id == row.parent)
                    parent = db(query).select(table.name,
                                              limitby=(0, 1)).first()
                    if parent:
                        form.vars.name = parent.name
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_onaccept(form):
        """
        """

        pca = current.deployment_settings.get_project_community_activity()

        if pca:
            vars = form.vars
            location_id = vars.location_id
            if location_id:
                # Populate the Lx fields
                atable = current.s3db.project_activity
                current.response.s3.lx_update(atable, vars.id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_activity_deduplicate(item):
        """ Import item de-duplication """

        db = current.db
        settings = current.deployment_settings
        pca = settings.get_project_community_activity()

        if item.id:
            return
        if item.tablename != "project_activity":
            return
        table = item.table
        duplicate = None
        if pca:
           if "project_id" in item.data and \
              "location_id" in item.data:
                # Match activity by project_id and location_id
                project_id = item.data.project_id
                location_id = item.data.location_id
                query = (table.project_id == project_id) & \
                        (table.location_id == location_id)
                duplicate = db(query).select(table.id,
                                             limitby=(0, 1)).first()
        else:
           if "project_id" in item.data and "name" in item.data:
                # Match activity by project_id and name
                project_id = item.data.project_id
                name = item.data.name
                query = (table.project_id == project_id) & \
                        (table.name == name)
                duplicate = db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_community_onaccept(form):
        """
        """

        location_id = form.vars.location_id

        if location_id:
            # Populate the Lx fields
            ctable = current.s3db.project_community
            current.response.s3.lx_update(ctable, form.vars.id)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_community_onvalidation(form):
        """
        """

        location_id = form.vars.location_id

        if location_id:
            db = current.db
            s3db = current.s3db
            table = s3db.gis_location
            query = (table.id == form.vars.location_id)
            row = db(query).select(table.parent,
                                   limitby=(0, 1)).first()
            if row and row.parent:
                query = (table.id == row.parent)
                parent = db(query).select(table.name,
                                          limitby=(0, 1)).first()
                if parent:
                    form.vars.name = parent.name
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def project_community_deduplicate(item):
        """ Import item de-duplication """

        db = current.db

        if item.id:
            return
        if item.tablename != "project_community":
            return
        table = item.table
        duplicate = None

        if "project_id" in item.data and \
                "location_id" in item.data:
            # Match community by project_id and location_id
            project_id = item.data.project_id
            location_id = item.data.location_id
            query = (table.project_id == project_id) & \
                    (table.location_id == location_id)
            duplicate = db(query).select(table.id, limitby=(0, 1)).first()

        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

        return

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
        row = current.db(
            (hr.human_resource_id == form.vars.human_resource_id) & \
            (hr.project_id == form.request_vars.project_id)
        ).select(hr.id, limitby=(0, 1)).first()

        # If we found a row we have a duplicate. Return an error to the user.
        if row:
            form.errors.human_resource_id = current.T("Record already exists")

        return


# =============================================================================
class S3ProjectDRRModel(S3Model):
    """
        Project DRR Model

        This class contains the tabels suitable for use by multinational
        organisations tracking projects at a high level
    """

    names = ["project_organisation",
             #"project_site",
             "project_beneficiary_type",
             "project_beneficiary",
             "project_organisation_roles",
             "project_organisation_lead_role"
             ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        currency_type = s3.currency_type
        #location_id = self.gis_location_id
        organisation_id = self.org_organisation_id
        project_id = self.project_project_id
        activity_id = self.project_activity_id
        community_id = self.project_community_id
        #multi_activity_type_id = self.project_multi_activity_type_id

        pca = current.deployment_settings.get_project_community_activity()

        messages = current.messages
        NONE = messages.NONE

        # ---------------------------------------------------------------------
        # Project Organisation
        #
        project_organisation_roles = settings.get_project_organisation_roles()
        project_organisation_lead_role = settings.get_project_organisation_lead_role()

        organisation_help = T("Add all organizations which are involved in different roles in this project")

        tablename = "project_organisation"
        table = self.define_table(tablename,
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
                                        requires = IS_FLOAT_AMOUNT(),
                                        represent = lambda v, row=None: \
                                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                        widget = IS_FLOAT_AMOUNT.widget,
                                        label = T("Funds Contributed by this Organization")),
                                  currency_type(),
                                  s3.comments(),
                                  *s3.meta_fields())

        # Field configuration?

        # CRUD Strings
        ADD_PROJECT_ORG = T("Add Organization to Project")
        LIST_PROJECT_ORG = T("List Project Organizations")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PROJECT_ORG,
            title_display = T("Project Organization Details"),
            title_list = LIST_PROJECT_ORG,
            title_update = T("Edit Project Organization"),
            title_search = T("Search Project Organizations"),
            title_upload = T("Import Project Organizations"),
            title_report = T("Funding Report"),
            subtitle_create = T("Add Organization to Project"),
            subtitle_list = T("Project Organizations"),
            subtitle_report = T("Funding"),
            label_list_button = LIST_PROJECT_ORG,
            label_create_button = ADD_PROJECT_ORG,
            label_delete_button = T("Remove Organization from Project"),
            msg_record_created = T("Organization added to Project"),
            msg_record_modified = T("Project Organization updated"),
            msg_record_deleted = T("Organization removed from Project"),
            msg_list_empty = T("No Organizations for this Project"))

        # Search Method?

        # Resource Configuration
        self.configure(tablename,
                       deduplicate=self.project_organisation_deduplicate,
                       onvalidation=self.project_organisation_onvalidation,
                       onaccept=self.project_organisation_onaccept,
                       ondelete=self.project_organisation_ondelete)

        # Reusable Field

        # Components

        # ---------------------------------------------------------------------
        # Project Site
        # @ToDo: Deprecated?
        #
        # tablename = "project_site"
        # table = self.define_table(tablename,
                                  # self.super_link("site_id", "org_site"),
                                  # project_id(),
                                  # Field("name", notnull=True,
                                        # length=64, # Mayon Compatibility
                                        # label = T("Name")),
                                  # location_id(),
                                  # multi_activity_type_id(),
                                  # *(s3.address_fields() + s3.meta_fields()))


        # Field configuration
        # CRUD Strings
        # Search Method
        # Resource Configuration
        # Reusable Field

        # CRUD strings
        # ADD_PROJECT_SITE = T("Add Project Site")
        # LIST_PROJECT_SITE = T("List Project Sites")
        # s3.crud_strings[tablename] = Storage(
            # title_create = ADD_PROJECT_SITE,
            # title_display = T("Project Site Details"),
            # title_list = LIST_PROJECT_SITE,
            # title_update = T("Edit Project Site"),
            # title_search = T("Search Project Sites"),
            # title_upload = T("Import Project Sites"),
            # subtitle_create = T("Add New Project Site"),
            # subtitle_list = T("Sites"),
            # label_list_button = LIST_PROJECT_SITE,
            # label_create_button = ADD_PROJECT_SITE,
            # label_delete_button = T("Delete Project Site"),
            # msg_record_created = T("Project Site added"),
            # msg_record_modified = T("Project Site updated"),
            # msg_record_deleted = T("Project Site deleted"),
            # msg_list_empty = T("No Project Sites currently registered"))

        # project_site_id = S3ReusableField("project_site_id", db.project_site,
                                          # #sortby="default/indexname",
                                          # requires = IS_NULL_OR(IS_ONE_OF(db, "project_site.id", "%(name)s")),
                                          # represent = lambda id, row=None: \
                                                      # (id and [db(db.project_site.id == id).select(db.project_site.name,
                                                                                                   # limitby=(0, 1)).first().name] or [NONE])[0],
                                          # label = T("Project Site"),
                                          # comment = S3AddResourceLink(c="project",
                                                                      # f="site",
                                                                      # title=ADD_PROJECT_SITE,
                                                                      # tooltip=T("If you don't see the site in the list, you can add a new one by clicking link 'Add Project Site'.")),,
                                          # ondelete = "CASCADE")

        # self.configure(tablename,
                        # super_entity="org_site",
                        # onvalidation=s3.address_onvalidation)

        # ---------------------------------------------------------------------
        # Project Beneficiary Type
        #
        tablename = "project_beneficiary_type"
        table = self.define_table(tablename,
                                  Field("name",
                                        length=128,
                                        unique=True,
                                        requires = IS_NOT_IN_DB(db,
                                                                "project_beneficiary_type.name")),
                                  *s3.meta_fields())

        # Field configuration?

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

        # Search Method?

        # Resource Configuration?

        # Reusable Field
        beneficiary_type_id = S3ReusableField("beneficiary_type_id", db.project_beneficiary_type,
                                   requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                   "project_beneficiary_type.id",
                                                                   self.beneficiary_type_represent)),
                                   represent = self.beneficiary_type_represent,
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
        table = self.define_table(tablename,
                                  # populated automatically
                                  project_id(readable=False,
                                             writable=False),
                                  #activity_id(comment=None),
                                  community_id(comment=None),
                                  beneficiary_type_id(empty=False),
                                  Field("number", "integer",
                                        label = T("Quantity"),
                                        requires = IS_INT_IN_RANGE(0, 99999999),
                                        represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                                  s3.comments(),
                                  *s3.meta_fields())

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

        table.virtualfields.append(S3ProjectBeneficiaryVirtualfields())

        # Search Method?

        # Resource Configuration
        report_fields=[
                      #"activity_id",
                      "community_id",
                      (T("Beneficiary Type"), "beneficiary_type_id"),
                      "project_id",
                      "project_id$multi_hazard_id",
                      "project_id$multi_theme_id",
                      "activity_id$multi_activity_type_id"
                     ]
        lh = current.gis.get_location_hierarchy()
        lh = [(lh[opt], opt) for opt in lh]
        report_fields.extend(lh)
        self.configure(tablename,
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
                                    field=["beneficiary_type_id"],
                                    name="beneficiary_type_id",
                                    label=T("Beneficiary Type")
                                ),
                                # Can't search be VirtualFields currently
                                # S3SearchLocationHierarchyWidget(
                                    # name="beneficiary_search_L1",
                                    # field="activity_id$L1",
                                    # cols = 3,
                                # ),
                            ],
                            rows=report_fields,
                            cols=report_fields,
                            facts=["number"],
                            methods=["sum"]
                        )
        )

        # Reusable Field
        beneficiary_id = S3ReusableField("beneficiary_id", db.project_beneficiary,
                                         sortby="name",
                                         requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                         "project_beneficiary.id",
                                                                         "%(type)s",
                                                                         sort=True)),
                                         represent = lambda id, row=None: \
                                                     s3_get_db_field_value(tablename = "project_beneficiary",
                                                                           fieldname = "type",
                                                                           look_up_value = id),
                                         label = T("Beneficiaries"),
                                         comment = S3AddResourceLink(c="project",
                                                                     f="beneficiary",
                                                                     title=ADD_BNF,
                                                                     tooltip=T("If you don't see the beneficiary in the list, you can add a new one by clicking link 'Add Beneficiary'.")),
                                         ondelete = "SET NULL")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
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
    def project_organisation_onvalidation(form, lead_role=None):
        """ Form validation """

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        otable = s3db.project_organisation

        if lead_role is None:
            lead_role = s3.project_organisation_lead_role

        project_id = form.vars.project_id
        organisation_id = form.vars.organisation_id
        if str(form.vars.role) == str(lead_role) and project_id:
            query = (otable.deleted != True) & \
                    (otable.project_id == project_id) & \
                    (otable.role == lead_role) & \
                    (otable.organisation_id != organisation_id)
            row = db(query).select(otable.id, limitby=(0, 1)).first()
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

        s3 = current.response.s3

        if str(form.vars.role) == str(s3.project_organisation_lead_role):
            db = current.db

            organisation_id = form.vars.organisation_id
            project_organisation = current.s3db.project_organisation
            project_project = current.s3db.project_project

            # Query to get the project ID via the new project
            # organisation record
            project = (project_organisation.id == form.vars.id) & \
                      (project_project.id == project_organisation.project_id)
            project = db(project).select(project_project.id).first()

            if project:
                # Set the organisation property of the project
                # to match the new lead organisation
                db(project_project.id == project.id) \
                    .update(organisation_id=organisation_id)

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
        s3db = current.s3db
        s3 = current.response.s3

        potable = s3db.project_organisation
        ptable = s3db.project_project

        # Query for the row that was deleted
        deleted_record = (potable.id == row.get('id'))
        deleted_row = db(deleted_record).select(potable.deleted_fk,
                                                potable.role).first()

        # Get organisation role
        role = deleted_row.role

        if str(role) == str(s3.project_organisation_lead_role):
            # Get the project_id
            deleted_fk = json.loads(deleted_row.deleted_fk)
            project_id = deleted_fk['project_id']

            # Query to look up the project
            project = (ptable.id == project_id)

            # Set the project organisation_id to NULL (using None)
            db(project).update(organisation_id=None)

        return

    # ---------------------------------------------------------------------
    @staticmethod
    def project_organisation_deduplicate(item):
        """ Import item de-duplication """

        db = current.db

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

    # ---------------------------------------------------------------------
    @staticmethod
    def beneficiary_type_represent(type_id, row=None):
        """ FK representation """

        db = current.db
        s3db = current.s3db
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        if isinstance(type_id, Row):
            if "name" in type_id:
                return type_id.name
            elif "id" in type_id:
                type_id = type_id.id
            else:
                return UNKNOWN_OPT

        bnf_type = s3db.project_beneficiary_type
        query = bnf_type.id == type_id
        row = db(query).select(bnf_type.name, limitby=(0, 1)).first()
        if row:
            return row.name
        else:
            return UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_onaccept(form):
        """ Record creation post-processing """

        db = current.db
        s3db = current.s3db

        btable = s3db.project_beneficiary
        ctable = s3db.project_community

        record_id = form.vars.id
        query = (btable.id == record_id) & \
                (ctable.id == btable.community_id)
        community = db(query).select(ctable.project_id,
                                    limitby=(0, 1)).first()
        if community:
            db(btable.id == record_id).update(project_id=community.project_id)
        return

    # ---------------------------------------------------------------------
    @staticmethod
    def project_beneficiary_deduplicate(item):
        """ Import item de-duplication """

        db = current.db

        if item.id:
            return
        if item.tablename == "project_beneficiary" and \
            "beneficiary_type_id" in item.data and \
            "community_id" in item.data:
            # Match beneficiary by type and activity_id
            table = item.table
            beneficiary_type_id = item.data.beneficiary_type_id
            community_id = item.data.community_id
            query = (table.beneficiary_type_id == beneficiary_type_id) & \
                    (table.community_id == community_id)
            duplicate = db(query).select(table.id,
                                            limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return


# =============================================================================
class S3ProjectTaskModel(S3Model):
    """
        Project Task Model

        This class holds the tables used for a smaller Organisation to manage
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
        s3 = current.response.s3
        settings = current.deployment_settings

        person_id = self.pr_person_id
        location_id = self.gis_location_id
        site_id = self.org_site_id
        project_id = self.project_project_id
        activity_id = self.project_activity_id

        s3_date_format = settings.get_L10n_date_format()
        s3_utc_represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        # Shortcuts
        add_component = self.add_component
        comments = s3.comments
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link
        meta_fields = s3.meta_fields

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
                             Field("date", "date",
                                   label = T("Date"),
                                   represent = s3_date_represent,
                                   requires = IS_NULL_OR(IS_DATE(format = s3_date_format))),
                             comments(),
                             format="%(name)s",
                             *meta_fields())

        # CRUD Strings
        ADD_MILESTONE = T("Add Milestone")
        crud_strings[tablename] = Storage(
            title_create = ADD_MILESTONE,
            title_display = T("Milestone Details"),
            title_list = T("List Milestones"),
            title_update = T("Edit Milestone"),
            title_search = T("Search Milestones"),
            title_upload = T("Import Milestone Data"),
            subtitle_create = T("Add New Milestone"),
            subtitle_list = T("Milestones"),
            subtitle_report = T("Milestones"),
            label_list_button = T("List Milestones"),
            label_create_button = ADD_MILESTONE,
            msg_record_created = T("Milestone Added"),
            msg_record_modified = T("Milestone Updated"),
            msg_record_deleted = T("Milestone Deleted"),
            msg_list_empty = T("No Milestones Found")
        )

        # Reusable Field
        milestone_id = S3ReusableField("milestone_id", db.project_milestone,
                                       sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "project_milestone.id",
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
                             site_id,
                             location_id(label=T("Deployment Location"),
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
                                        represent = lambda id, row=None: \
                                                    project_assignee_represent(id),
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
                             *meta_fields())

        # Field configurations
        # Comment these if you don't need a Site associated with Tasks
        #table.site_id.readable = table.site_id.writable = True
        #table.site_id.label = T("Check-in at Facility") # T("Managing Office")
        table.created_on.represent = s3_date_represent

        # CRUD Strings
        ADD_TASK = T("Add Task")
        LIST_TASKS = T("List Tasks")
        crud_strings[tablename] = Storage(
            title_create = ADD_TASK,
            title_display = T("Task Details"),
            title_list = LIST_TASKS,
            title_update = T("Edit Task"),
            title_search = T("Search Tasks"),
            title_upload = T("Import Tasks"),
            subtitle_create = T("Add New Task"),
            subtitle_list = T("Tasks"),
            label_list_button = LIST_TASKS,
            label_create_button = ADD_TASK,
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task deleted"),
            msg_list_empty = T("No tasks currently registered"))

        # Virtual Fields
        # Do just for the common report
        table.virtualfields.append(S3ProjectTaskVirtualfields())

        # Search Method
        task_search = S3Search(
                advanced = (
                    # Virtual fields not supported by Search Widgets yet
                    #S3SearchOptionsWidget(
                        #name = "task_search_project",
                        #label = T("Project"),
                        #field = "project",
                        #cols = 3
                    #),
                    # This Syntax not supported by Search Widgets yet
                    #S3SearchOptionsWidget(
                    #    name = "task_search_project",
                    #    label = T("Project"),
                    #    field = "task.task_id:project_task:project_id$name",
                    #    cols = 3
                    #),
                    # Virtual fields not supported by Search Widgets yet
                    #S3SearchOptionsWidget(
                        #name = "task_search_activity",
                        #label = T("Activity"),
                        #field = "activity",
                        #cols = 3
                    #),
                    S3SearchOptionsWidget(
                        name = "task_search_priority",
                        label = T("Priority"),
                        field = "priority",
                        cols = 4
                    ),
                    S3SearchSimpleWidget(
                        name = "task_search_text_advanced",
                        label = T("Description"),
                        comment = T("Search for a Task by description."),
                        field = [ "name",
                                  "description",
                                ]
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
                )
            )
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
        task_id = S3ReusableField("task_id", db.project_task,
                                  label = T("Task"),
                                  sortby="name",
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "project_task.id", "%(name)s")),
                                  represent = lambda id, row=None: \
                                                (id and [db.project_task[id].name] or [NONE])[0],
                                  comment = S3AddResourceLink(c="project",
                                                              f="task",
                                                              title=ADD_TASK,
                                                              tooltip=T("A task is a piece of work that an individual or team can do in 1-2 days.")),
                                  ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Custom Methods
        self.set_method("project_task",
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
                             *meta_fields())

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
                             activity_id(),
                             *meta_fields())

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
                                   requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                    "project_comment.id")),
                                   readable=False),
                             #project_id(),
                             #activity_id(),
                             task_id(),
                             Field("body", "text",
                                   notnull=True,
                                   label = T("Comment")),
                             *meta_fields())

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
                             person_id(default=auth.s3_logged_in_person()),
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
                             comments(),
                             format="%(comments)s",
                             *meta_fields())

        # CRUD Strings
        ADD_TIME = T("Log Time Spent")
        crud_strings[tablename] = Storage(
            title_create = ADD_TIME,
            title_display = T("Logged Time Details"),
            title_list = T("List Logged Time"),
            title_update = T("Edit Logged Time"),
            title_search = T("Search Logged Time"),
            title_upload = T("Import Logged Time data"),
            title_report = T("Last Week's Work"),
            subtitle_create = T("Log New Time"),
            subtitle_list = T("Logged Time"),
            subtitle_report = T("Logged Time"),
            label_list_button = T("List Logged Time"),
            label_create_button = ADD_TIME,
            msg_record_created = T("Time Logged"),
            msg_record_modified = T("Time Log Updated"),
            msg_record_deleted = T("Time Log Deleted"),
            msg_list_empty = T("No Time Logged")
        )
        if "rows" in request.get_vars and request.get_vars.rows == "project":
            s3.crud_strings[tablename].title_report = T("Project Time Report")

        # Virtual Fields
        table.virtualfields.append(S3ProjectTimeVirtualfields())

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
        # Pass variables back to global scope (response.s3.*)
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

    # ---------------------------------------------------------------------
    @staticmethod
    def milestone_represent(id, row=None):
        """ FK representation """

        db = current.db
        NONE = current.messages.NONE

        if id:
            val = (id and [db.project_milestone[id].name] or [NONE])[0]
            return val
        else:
            return NONE

    # -------------------------------------------------------------------------
    @staticmethod
    def task_owner_entity(table, record):
        """ Set the task owner entity to the project's owner entity """

        db = current.db
        s3db = current.s3db

        ptable = s3db.project_project
        ltable = s3db.project_task_project

        task_id = record.id
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
        table = s3db.project_task
        if "project_id" in vars:
            # Create Link to Project
            ltable = s3db.project_task_project
            if vars.project_id:
                link_id = ltable.insert(task_id = id,
                                        project_id = _vars.project_id)

        if "activity_id" in vars:
            # Create Link to Activity
            ltable = s3db.project_task_activity
            if vars.activity_id:
                link_id = ltable.insert(task_id = id,
                                        activity_id = _vars.activity_id)

        # Make sure the task is also linked to the project
        # when created under an activity
        if id:
            lta = s3db.project_task_activity
            ltp = s3db.project_task_project
            ta = s3db.project_activity
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

        table = s3db.project_task

        changed = {}
        for var in vars:
            vvar = vars[var]
            rvar = record[var]
            if vvar != rvar:
                if table[var].type == "integer":
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
            table = s3db.project_comment
            text = s3_auth_user_represent(current.auth.user.id)
            for var in changed:
                text = "%s\n%s" % (text, changed[var])
            table.insert(task_id=id,
                         body=text)

        vars = current.request.post_vars
        if "project_id" in vars:
            ptable = s3db.project_project
            ltable = s3db.project_task_project
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
            ondelete = s3mgr.model.get_config("project_task_project",
                                              "ondelete")
            links.delete(ondelete=ondelete)

        if "activity_id" in vars:
            atable = s3db.project_activity
            ltable = s3db.project_task_activity
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
            ondelete = s3mgr.model.get_config("project_task_activity",
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

        T = current.T
        msg = current.msg
        response = current.response

        if r.representation == "html" and \
           r.name == "task" and r.id and not r.component:

            record = r.record
            text = "%s: %s" % (record.name,
                               record.description)

            # Encode the message as an OpenGeoSMS
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

            output["title"] = T("Send Task Notification")
            response.view = "msg/compose.html"
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

        s3 = current.response.s3

        task_id = self.project_task_id
        human_resource_id = self.hrm_human_resource_id
        job_role_id = self.hrm_job_role_id

        # Shortcuts
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Link Tasks <> Human Resources
        tablename = "project_task_human_resource"
        table = define_table(tablename,
                             task_id(),
                             human_resource_id(),
                             *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Link Tasks <> Job Roles
        tablename = "project_task_job_role"
        table = define_table(tablename,
                             task_id(),
                             job_role_id(),
                             *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return dict(
        )

# =============================================================================
class S3ProjectTaskIReportModel(S3Model):
    """
        Project Task IReport Model

        This class holds the table used to link Tasks with Incident Reports.
    """

    names = ["project_task_ireport",
             ]

    def model(self):

        s3 = current.response.s3

        task_id = self.project_task_id
        ireport_id = self.irs_ireport_id

        # Link Tasks <-> Incident Reports
        #
        tablename = "project_task_ireport"
        table = self.define_table(tablename,
                                  task_id(),
                                  ireport_id(),
                                  *s3.meta_fields())

        self.configure(tablename,
                       onaccept=self.task_ireport_onaccept)

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
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
        s3db = current.s3db

        # Check if we already have a Location for the Task
        table = s3db.project_task
        query = (table.id == task_id)
        record = db(query).select(table.location_id,
                                  limitby=(0, 1)).first()
        if not record or record.location_id:
            return

        # Find the Incident Location
        itable = s3db.irs_ireport
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
class S3ProjectAnnualBudgetModel(S3Model):
    """
        Project Budget Model

        This model holds the annual budget entries for projects
    """

    names = ["project_annual_budget"]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        currency_type = s3.currency_type

        self.define_table(
            "project_annual_budget",
            self.project_project_id(requires=IS_ONE_OF(db,
                                                       "project_project.id",
                                                       "%(name)s")),
            Field("year",
                  "integer",
                  default=None, # make it current year
                  required=True,
                  requires=IS_INT_IN_RANGE(1950, 3000),
                  notnull=True,
                  label="Year",
                  comment=None,
            ),
            Field("amount",
                  "double",
                  default=0.00,
                  required=True,
                  requires=IS_FLOAT_AMOUNT(),
                  notnull=True,
                  label="Amount",
                  comment=None,
            ),
            currency_type(required=True),
            *s3.meta_fields()
        )


        # CRUD Strings
        s3.crud_strings["project_annual_budget"] = Storage(
            title_create = T("New Annual Budget"),
            title_display = T("Annual Budget"),
            title_list = T("List Annual Budgets"),
            title_update = T("Edit Annual Budget"),
            title_search = T("Search Annual Budgets"),
            title_upload = T("Import Annual Budget data"),
            title_report = T("Report on Annual Budgets"),
            subtitle_create = T("Add a new annual budget"),
            subtitle_list = T("List of all annual budgets"),
            subtitle_report = T("Annual Budget Reports"),
            label_list_button = T("List Annual Budgets"),
            label_create_button = T("New Annual Budget"),
            msg_record_created = T("New annual budget created"),
            msg_record_modified = T("Annual budget updated"),
            msg_record_deleted = T("Annual budget deleted"),
            msg_list_empty = T("No annual budgets found")
        )

        self.configure("project_annual_budget",
                       list_fields=[
                            "id",
                            "year",
                            "amount",
                            "currency_type",
                        ]
        )

        self.project_annual_budget_id = S3ReusableField(
            "annual_budget_id", db.project_annual_budget,
            label = T("Annual Budget"),
            sortby="year",
            requires = IS_NULL_OR(IS_ONE_OF(db,
                                            "project_annual_budget.id",
                                            "%(name)s")),
            represent = lambda id, row=None: \
                (id and [db.project_annual_budget[id].year] or [NONE])[0],
            comment = S3AddResourceLink(c="project",
                f="annual_budget",
                title="Add an Annual Budget",
            ),
            ondelete = "CASCADE"
        )

        # Pass variables back to global scope (response.s3.*)
        return dict(
        )

# =============================================================================
def project_assignee_represent(id):
    """ Represent the Person a Task is assigned-to or list views """

    db = current.db
    s3db = current.s3db
    cache = s3db.cache
    output = current.messages.NONE

    if not id:
        return output

    if isinstance(id, Row):
        instance_type = id.instance_type
        id = id.pe_id
    else:
        etable = s3db.pr_pentity
        query = (etable.id == id)
        record = db(query).select(etable.instance_type,
                                  cache=cache,
                                  limitby=(0, 1)).first()
        if not record:
            return output

        instance_type = record.instance_type

    table = s3db[instance_type]
    query = (table.pe_id == id)
    if instance_type == "pr_person":
        record = db(query).select(table.first_name,
                                  table.middle_name,
                                  table.last_name,
                                  table.initials,
                                  cache=cache,
                                  limitby=(0, 1)).first()
        if record:
            output = record.initials or s3_fullname(record)
    elif instance_type in ("pr_group", "org_organisation"):
        # Team or Organisation
        record = db(query).select(table.name,
                                  cache=cache,
                                  limitby=(0, 1)).first()
        if record:
            output = record.name
    else:
        # Should not happen of correctly filtered, return default
        pass

    return output

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
    drr = settings.get_project_drr()
    pca = settings.get_project_community_activity()
    milestones = settings.get_project_milestones()
    if resourcename == "project":
        # Tabs
        tabs = [(T("Basic Details"), None)]
        append = tabs.append
        if drr:
            append((T("Organizations"), "organisation"))

        ADMIN = current.session.s3.system_roles.ADMIN
        admin = auth.s3_has_role(ADMIN)
        #staff = auth.s3_has_role("STAFF")
        staff = True
        if staff or drr:
            append((T("Activities"), "activity"))
        if drr:
            append((T("Communities"), "community"))
        if staff and milestones:
            append((T("Milestones"), "milestone"))
        if not drr:
            append((T("Tasks"), "task"))
        if drr:
            append((T("Documents"), "document"))
        elif staff:
            append((T("Attachments"), "document"))
        if record.calendar:
            append((T("Calendar"), "timeline"))
        if staff:
            append((T("Annual Budgets"), "annual_budget"))
        append((T("Staff"), "human_resource", dict(group="staff")))
        append((T("Volunteers"), "human_resource", dict(group="volunteer")))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        row3 = ""
        if drr:
            row2 = TR(
                TH("%s: " % table.countries_id.label),
                table.countries_id.represent(record.countries_id),
                )
        else:
            row2 = TR(
                TH("%s: " % table.organisation_id.label),
                table.organisation_id.represent(record.organisation_id)
                )
            if record.end_date:
                row3 = TR(
                    TH("%s: " % table.end_date.label),
                    table.end_date.represent(record.end_date)
                    )

        rheader = DIV(TABLE(
            TR(
               TH("%s: " % table.name.label),
               record.name
              ),
            row2,
            row3,
            ), rheader_tabs)

    elif resourcename == "activity":
        # @ToDo: integrate tabs?
        rheader_tabs = s3_rheader_tabs(r, tabs)
        tbl = TABLE()
        if record.project_id is not None:
            tbl.append(
                        TR(
                            TH("%s: " % table.project_id.label),
                            table.project_id.represent(record.project_id))
                        )
        if pca:
            tbl.append(

                        TR(
                           TH("%s: " % table.location_id.label),
                           table.location_id.represent(record.location_id)
                          )
                       )
        else:
            tbl.append(

                        TR(
                           TH("%s: " % table.name.label),
                           record.name
                          )
                       )
        rheader = DIV(tbl, rheader_tabs)

    elif resourcename == "community":
        rheader_tabs = s3_rheader_tabs(r, tabs)
        tbl = TABLE()
        if record.project_id is not None:
            tbl.append(
                        TR(
                            TH("%s: " % table.project_id.label),
                            table.project_id.represent(record.project_id))
                        )
        if True:
            tbl.append(
                        TR(
                           TH("%s: " % table.location_id.label),
                           table.location_id.represent(record.location_id)
                          )
                       )
        else:
            tbl.append(
                        TR(
                           TH("%s: " % table.name.label),
                           record.name
                          )
                       )
        rheader = DIV(tbl, rheader_tabs)

    elif resourcename == "task":
        db = current.db
        s3db = current.s3db

        # Tabs
        tabs = [(T("Details"), None)]
        append = tabs.append
        staff = auth.s3_has_role("STAFF")
        if staff:
            append((T("Time"), "time")),
        #append((T("Comments"), "discuss"))
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
        project = db(query).select(ptable.id,
                                   limitby=(0, 1)).first()
        if project:
            project = TR(
                            TH("%s: " % T("Project")),
                            s3db.project_project_represent(project.id)
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

        # Comments
        # if r.method == "discuss":
            # comments = ""
        # else:
            # ctable = s3db.project_comment
            # query = (ctable.deleted == False) & \
                    # (ctable.task_id == r.id)
            # comments = db(query).select(ctable.body).last()
            # if comments:
                # try:
                    # markup = etree.XML(comments.body)
                    # text = markup.xpath(".//text()")
                    # if text:
                        # text = " ".join(text)
                    # else:
                        # text = ""
                # except etree.XMLSyntaxError:
                    # t = html.fromstring(comments.body)
                    # text = t.text_content()
                # comments = TR(
                                # TH("%s: " % T("Latest Comment")),
                                # A(text,
                                  # _href=URL(args=[r.id, "discuss"]))
                            # )
            # else:
                # comments = ""

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
class S3ProjectVirtualfields:
    """ Virtual fields for the project_project table """

    def organisation(self):
        """ Name of the lead organisation of the project """

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        settings = current.deployment_settings
        LEAD_ROLE = settings.get_project_organisation_lead_role()

        otable = s3db.org_organisation
        ltable = s3db.project_organisation
        query = (ltable.deleted != True) & \
                (ltable.project_id == self.project_project.id) & \
                (ltable.role == LEAD_ROLE) & \
                (ltable.organisation_id == otable.id)
        org = db(query).select(otable.name,
                               limitby=(0, 1)).first()
        if org:
            return org.name
        else:
            return None

# =============================================================================
class S3ProjectActivityVirtualfields:
    """ Virtual fields for the project_activity table """

    extra_fields = ["project_id", "location_id"]

    def organisation(self):
        """ Name of the lead organisation of the project """

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        settings = current.deployment_settings
        LEAD_ROLE = settings.get_project_organisation_lead_role()

        otable = s3db.org_organisation
        ltable = s3db.project_organisation

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
class S3ProjectCommunityVirtualfields:
    """ Virtual fields for the project_community table """

    extra_fields = ["project_id", "location_id"]

    def organisation(self):
        """ Name of the lead organisation of the project """

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        otable = s3db.org_organisation
        ltable = s3db.project_organisation
        LEAD_ROLE = s3.project_organisation_lead_role
        query = (ltable.deleted != True) & \
                (ltable.project_id == self.project_community.project_id) & \
                (ltable.role == LEAD_ROLE) & \
                (ltable.organisation_id == otable.id)
        org = db(query).select(otable.name,
                               limitby=(0, 1)).first()
        if org:
            return org.name
        else:
            return None

    def L0(self):
        parents = Storage()
        parents = current.gis.get_parent_per_level(parents,
                                                   self.project_community.location_id,
                                                   ids=False,
                                                   names=True)
        if "L0" in parents:
            return parents["L0"]
        else:
            return None

    def L1(self):
        parents = Storage()
        parents = current.gis.get_parent_per_level(parents,
                                                   self.project_community.location_id,
                                                   ids=False,
                                                   names=True)
        if "L1" in parents:
            return parents["L1"]
        else:
            return None

    def L2(self):
        parents = Storage()
        parents = current.gis.get_parent_per_level(parents,
                                                   self.project_community.location_id,
                                                   ids=False,
                                                   names=True)
        if "L2" in parents:
            return parents["L2"]
        else:
            return None

    def L3(self):
        parents = Storage()
        parents = current.gis.get_parent_per_level(parents,
                                                   self.project_community.location_id,
                                                   ids=False,
                                                   names=True)
        if "L3" in parents:
            return parents["L3"]
        else:
            return None

# =============================================================================
class S3ProjectBeneficiaryVirtualfields:
    """ Virtual fields for the project_beneficiary table """

    extra_fields = ["community_id"]

    @staticmethod
    def _get_community_location(community_id):
        """
            Grab the first location from the database for this community and
            return the location tree
        """

        db = current.db
        s3db = current.s3db

        # The project_community database table
        ctable = s3db.project_community
        query = (ctable.id == community_id)


        community = db(query).select(ctable.location_id, limitby=(0,1)).first()


        parents = Storage()
        if community:
            parents = current.gis.get_parent_per_level(parents,
                                                       community.location_id,
                                                       ids=False,
                                                       names=True)

        return parents

    def L0(self):
        parents = self._get_community_location(self.project_beneficiary.community_id)

        if "L0" in parents:
            return parents["L0"]
        else:
            return current.messages.NONE


    def L1(self):
        parents = self._get_community_location(self.project_beneficiary.community_id)






        if "L1" in parents:
            return parents["L1"]
        else:
            return current.messages.NONE

    def L2(self):
        parents = self._get_community_location(self.project_beneficiary.community_id)






        if "L2" in parents:
            return parents["L2"]
        else:
            return current.messages.NONE

    def L3(self):
        parents = self._get_community_location(self.project_beneficiary.community_id)






        if "L3" in parents:
            return parents["L3"]
        else:
            return current.messages.NONE

# =============================================================================
class S3ProjectCommunityContactVirtualFields:
    """ Virtual fields for the project_activity_contact table """

    extra_fields = ["person_id"]

    def email(self):

        db = current.db
        s3db = current.s3db

        ptable = s3db.pr_person
        ctable = s3db.pr_contact

        person_id = self.project_community_contact.person_id
        query = (ctable.deleted != True) & \
                (ptable.id == person_id) & \
                (ctable.pe_id == ptable.pe_id) & \
                (ctable.contact_method == "EMAIL")
        items = db(query).select(ctable.value)
        return ", ".join([item.value for item in items])

    def sms(self):

        db = current.db
        s3db = current.s3db

        ptable = s3db.pr_person
        ctable = s3db.pr_contact

        person_id = self.project_community_contact.person_id
        query = (ctable.deleted != True) & \
                (ptable.id == person_id) & \
                (ctable.pe_id == ptable.pe_id) & \
                (ctable.contact_method == "SMS")
        items = db(query).select(ctable.value)
        return ", ".join([item.value for item in items])

# =============================================================================
class S3ProjectTaskVirtualfields:
    """ Virtual fields for the project_task table """

    extra_fields = ["id",
                    "project_task_project:project_id$name",
                    "project_task_activity:activity_id$name"]

    def project(self):
        """
            Project associated with this task
        """

        try:
            return self.project_project.name
        except AttributeError:
            return None

    def activity(self):
        """
            Activity associated with this task
        """

        try:
            return self.project_activity.name
        except AttributeError:
            return None

    def task_id(self):

        try:
            return self.project_task.id
        except AttributeError:
            return None

# =============================================================================
class S3ProjectTimeVirtualfields:
    """ Virtual fields for the project_time table """

    extra_fields = ["task_id", "person_id", "date"]

    def project(self):
        """
            Project associated with this time entry
            - used by the 'Project Time' report
        """

        db = current.db
        s3db = current.s3db

        ptable = s3db.project_project
        ltable = s3db.project_task_project
        query = (ltable.deleted != True) & \
                (ltable.task_id == self.project_time.task_id) & \
                (ltable.project_id == ptable.id)
        project = db(query).select(ptable.name,
                                   limitby=(0, 1)).first()
        if project:
            return project.name
        else:
            return None

    def day(self):
        """
            Day of the last Week this time entry relates to
            - used by the 'Last Week's Work' report
        """

        T = current.T
        now = current.request.utcnow
        thisdate = self.project_time.date

        if not thisdate:
            return "-"

        week = datetime.timedelta(days=7)
        if thisdate < (now - week):
            # Ignore data older than the last week
            # - should already be filtered in controller anyway
            return "-"

        return thisdate.date().strftime("%d %B")

# =============================================================================
def multi_activity_represent(opt):
    """
        Activity representation
        for multiple=True options
    """

    db = current.db
    s3db = current.s3db

    NONE = current.messages.NONE

    table = s3db.project_activity
    set = db(table.id > 0).select(table.id,
                                  table.name).as_dict()

    if not set:
        return NONE

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
        return NONE

    if len(opts) > 1:
        vals = ", ".join(vals)
    else:
        vals = len(vals) and vals[0] or ""
    return vals

# END =========================================================================
