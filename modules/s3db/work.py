# -*- coding: utf-8 -*-

""" Sahana Eden Simple Volunteer Jobs Management

    @copyright: 2015-2016 (c) Sahana Software Foundation
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

__all__ = ("WorkContextModel",
           "WorkJobModel",
           "work_rheader",
           )

from gluon import *
from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class WorkContextModel(S3Model):
    """ @todo: implement """

    names = ("work_context",
             )

    def model(self):

        db = current.db
        T = current.T

        settings = current.deployment_settings

        # ---------------------------------------------------------------------
        # Work Context
        #
        tablename = "work_context"
        self.define_table(tablename,
                          Field("name"),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():

        return {}

# =============================================================================
class WorkJobModel(S3Model):
    """ Model for Jobs """

    names = ("work_job_type",
             "work_job",
             "work_assignment",
             )

    def model(self):

        db = current.db
        T = current.T
        s3 = current.response.s3

        settings = current.deployment_settings

        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure
        add_components = self.add_components
        set_method = self.set_method

        # ---------------------------------------------------------------------
        tablename = "work_job_type"
        define_table(tablename,
                     Field("name",
                           label = T("Title"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Job Type"),
            title_display = T("Job Type Details"),
            title_list = T("Job Types"),
            title_update = T("Edit Job Type"),
            label_list_button = T("List Job Types"),
            msg_record_created = T("Job Type added"),
            msg_record_modified = T("Job Type updated"),
            msg_record_deleted = T("Job Type deleted"),
            msg_list_empty = T("No Job Types currently registered")
        )

        # Reusable field
        represent = S3Represent(lookup=tablename)
        job_type_id = S3ReusableField("job_type_id", "reference %s" % tablename,
                                      label = T("Job Type"),
                                      represent = represent,
                                      requires = IS_EMPTY_OR(IS_ONE_OF(
                                                        db, "work_job_type.id",
                                                        represent,
                                                        )),
                                      sortby = "name",
                                      comment = S3PopupLink(c="work",
                                                            f="job_type",
                                                            tooltip=T("Create a new job type"),
                                                            ),
                                      )

        # ---------------------------------------------------------------------
        # Job Priorities
        #
        job_priority = {1: T("Urgent"),
                        2: T("High"),
                        3: T("Normal"),
                        4: T("Low"),
                        }

        # ---------------------------------------------------------------------
        # Job Statuses
        #
        job_status = (("OPEN", T("Open")),
                      ("STARTED", T("Started")),
                      ("ONHOLD", T("On Hold")),
                      ("COMPLETED", T("Completed")),
                      ("CANCELLED", T("Cancelled")),
                      )

        # ---------------------------------------------------------------------
        # Job
        #
        tablename = "work_job"
        define_table(tablename,
                     job_type_id(),
                     Field("name",
                           label = T("Title"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("details", "text",
                           label = T("Details"),
                           represent = s3_text_represent,
                           ),
                     Field("priority", "integer",
                           default = 3, # normal priority
                           requires = IS_IN_SET(job_priority, zero=None),
                           represent = S3Represent(options=job_priority),
                           ),
                     Field("status",
                           default = "OPEN",
                           requires = IS_IN_SET(job_status, zero=None, sort=False),
                           represent = S3Represent(options=dict(job_status)),
                           ),
                     self.super_link("site_id", "org_site",
                                     label = T("Place"),
                                     orderby = "org_site.name",
                                     readable = True,
                                     writable = True,
                                     represent = self.org_site_represent,
                                     ),
                     s3_datetime("start_date"),
                     Field("duration", "double",
                           label = T("Hours Planned"),
                           requires = IS_EMPTY_OR(IS_FLOAT_IN_RANGE(0, None)),
                           ),
                     Field("workers_min", "integer",
                           default = 1,
                           label = T("Helpers needed"),
                           requires = IS_INT_IN_RANGE(1, None),
                           ),
                     # @todo: onvalidation to check max>=min
                     Field("workers_max", "integer",
                           label = T("Helpers needed (max)"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1, None)),
                           ),
                     Field("workers_assigned", "integer",
                           default = 0,
                           label = T("Helpers assigned"),
                           requires = IS_INT_IN_RANGE(0, None),
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Job"),
            title_display = T("Job Details"),
            title_list = T("Jobs"),
            title_update = T("Edit Job"),
            label_list_button = T("List Jobs"),
            msg_record_created = T("Job added"),
            msg_record_modified = T("Job updated"),
            msg_record_deleted = T("Job deleted"),
            msg_list_empty = T("No Jobs currently registered")
        )

        # Filter widgets
        filter_widgets = [S3TextFilter(["name",
                                        "details",
                                        "job_type_id$name",
                                        "site_id$name",
                                        ],
                                        label = T("Search"),
                                       ),
                          S3OptionsFilter("job_type_id"),
                          S3OptionsFilter("status"),
                          S3OptionsFilter("site_id",
                                          hidden = True,
                                          ),
                          S3DateFilter("start_date",
                                       hidden = True,
                                       ),
                          ]

        # List fields
        list_fields = ["priority",
                       "job_type_id",
                       "name",
                       "site_id",
                       "start_date",
                       "duration",
                       "status",
                       "workers_min",
                       "workers_assigned",
                       ]

        # Table configuration
        configure(tablename,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  list_layout = work_JobListLayout(),
                  )

        # Custom methods
        set_method("work", "job",
                   method = "signup",
                   action = work_SignUp,
                   )
        set_method("work", "job",
                   method = "cancel",
                   action = work_SignUp,
                   )

        # Components
        add_components(tablename,
                       work_assignment = "job_id",
                       )

        # Reusable field
        represent = S3Represent(lookup=tablename, show_link=True)
        job_id = S3ReusableField("job_id", "reference %s" % tablename,
                                 label = T("Job"),
                                 represent = represent,
                                 requires = IS_ONE_OF(db, "work_job.id",
                                                      represent,
                                                      ),
                                 sortby = "name",
                                 comment = S3PopupLink(c="work",
                                                       f="job",
                                                       tooltip=T("Create a new job"),
                                                       ),
                                 )

        # ---------------------------------------------------------------------
        # Linktable person<=>job
        #
        auth = current.auth
        tablename = "work_assignment"
        define_table(tablename,
                     job_id(),
                     self.pr_person_id(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Assignment"),
            title_display = T("Assignment Details"),
            title_list = T("Assignments"),
            title_update = T("Edit Assignment"),
            label_list_button = T("List Assignments"),
            msg_record_created = T("Assignment added"),
            msg_record_modified = T("Assignment updated"),
            msg_record_deleted = T("Assignment deleted"),
            msg_list_empty = T("No Assignments currently registered")
        )

        # Table configuration
        configure(tablename,
                  onaccept = self.assignment_onaccept,
                  ondelete = self.assignment_ondelete,
                  onvalidation = self.assignment_onvalidation,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {"work_job_id": job_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"work_job_id": lambda **attr: dummy("job_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def assignment_onvalidation(form):
        """
            Validation callback for work assignments:
            - a worker can only be assigned once to the same job

            @param form: the FORM
        """

        db = current.db
        s3db = current.s3db

        table = s3db.work_assignment

        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        # Get job_id and person_id
        try:
            job_id = form_vars.job_id
        except AttributeError:
            job_id = None
        try:
            person_id = form_vars.person_id
        except AttributeError:
            person_id = None

        if (job_id is None or person_id is None):
            if record_id:
                # Reload the record
                query = (table.id == record_id) & \
                        (table.deleted != True)
                record = db(query).select(table.job_id,
                                          table.person_id,
                                          limitby = (0, 1)).first()
                if record:
                    job_id = record.job_id
                    person_id = record.person_id
            else:
                # Check for defaults (e.g. component link)
                if job_id is None:
                    job_id = table.job_id.default
                if person_id is None:
                    person_id = table.person_id.default

        if job_id and person_id:
            # Verify this person is not already assigned to this job
            query = (table.job_id == job_id) & \
                    (table.person_id == person_id) & \
                    (table.deleted != True)
            if record_id:
                query = (table.id != record_id) & query

            duplicate = db(query).select(table.id, limitby=(0, 1)).first()
            if duplicate:
                msg = current.T("This person is already assigned to the job")
                form.errors["person_id"] = msg

    # -------------------------------------------------------------------------
    @classmethod
    def assignment_onaccept(cls, form):
        """
            Onaccept callback for work assignments

            @param form: the FORM
        """

        try:
            formvars = form.vars
        except AttributeError:
            return

        db = current.db
        atable = current.s3db.work_assignment

        if "job_id" not in formvars:
            if "id" not in formvars:
                return
            record_id = formvars.id
            row = db(atable.id == record_id).select(atable.job_id,
                                                    limitby = (0, 1)).first()
            if not row:
                return
            job_id = row.job_id
        else:
            job_id = formvars.job_id

        if job_id:
            cls.update_workers_assigned(job_id)

        return

    # -------------------------------------------------------------------------
    @classmethod
    def assignment_ondelete(cls, row):
        """
            Ondelete callback for work assignments

            @param row: the Row
        """

        try:
            record_id = row.id
        except AttributeError:
            return

        db = current.db
        atable = current.s3db.work_assignment

        row = db(atable.id == record_id).select(atable.deleted_fk,
                                                limitby = (0, 1)).first()

        if row and row.deleted_fk:
            data = json.loads(row.deleted_fk)
            job_id = data.get("job_id")
            if job_id:
                cls.update_workers_assigned(job_id)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def update_workers_assigned(job_id):
        """
            Update the number of workers assigned to a job

            @param job_id: the job record id
        """

        if not job_id:
            return

        db = current.db
        s3db = current.s3db
        jtable = s3db.work_job
        atable = s3db.work_assignment

        query = (atable.job_id == job_id) & \
                (atable.deleted != True)
        count = atable.id.count()
        row = db(query).select(count, limitby=(0, 1)).first()
        if not row:
            workers_assigned = 0
        else:
            workers_assigned = row[count]

        db(jtable.id == job_id).update(workers_assigned=workers_assigned,
                                       # Prevent update of modified_on and
                                       # modified_by (not a workflow action):
                                       modified_by = jtable.modified_by,
                                       modified_on = jtable.modified_on,
                                       )
        return

# =============================================================================
def work_rheader(r, tabs=[]):
    """ Work module resource headers """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    tablename = r.tablename
    record = r.record

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "work_job":

            if not tabs:
                tabs = [(T("Basic Details"), ""),
                        (T("Assignments"), "assignment"),
                        ]

            rheader_fields = [["name"],
                              ["site_id"],
                              ["start_date", "duration"],
                              ["status"],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r)

    return rheader

# =============================================================================
class work_SignUp(S3Method):
    """ Signup logic for job list """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}
        if r.http == "POST":
            if r.representation == "json":
                method = r.method
                if method == "signup":
                    output = self.signup(r, **attr)
                elif method == "cancel":
                    output = self.cancel(r, **attr)
                else:
                    r.error(405, current.ERROR.BAD_METHOD)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def signup(self, r, **attr):
        """
            Sign up the current user for this a job

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        s3db = current.s3db

        # Get the job ID
        job_id = self.record_id
        if not job_id:
            r.error(404, current.ERROR.BAD_RECORD)

        atable = s3db.work_assignment

        # Get the person ID
        auth = current.auth
        person_id = auth.s3_logged_in_person()
        if not person_id or not auth.s3_has_permission("create", atable):
            auth.permission.fail()

        # Add assignment if not assigned yet
        query = (atable.job_id == job_id) & \
                (atable.person_id == person_id) & \
                (atable.deleted != True)
        row = current.db(query).select(atable.id, limitby=(0, 1)).first()
        if not row:
            assignment = {"job_id": job_id,
                          "person_id": person_id,
                          }
            assignment_id = atable.insert(**assignment)
            if assignment_id:
                current.audit("create", "work", "assignment",
                              record = assignment_id,
                              representation = r.representation,
                              )
                assignment["id"] = assignment_id
                # Post-process create
                s3db.update_super(atable, assignment)
                auth.s3_set_record_owner(atable, assignment_id)
                auth.s3_make_session_owner(atable, assignment_id)
                s3db.onaccept(atable, assignment)

        output = current.xml.json_message(True)
        return output

    # -------------------------------------------------------------------------
    def cancel(self, r, **attr):
        """
            Cancel a job assignment of the current user

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        s3db = current.s3db

        # Get the job ID
        job_id = self.record_id
        if not job_id:
            r.error(404, current.ERROR.BAD_RECORD)

        atable = s3db.work_assignment

        # Get the person ID
        auth = current.auth
        person_id = auth.s3_logged_in_person()
        if not person_id or not auth.s3_has_permission("delete", atable):
            auth.permission.fail()

        query = (FS("job_id") == job_id) & \
                (FS("person_id") == person_id)

        assignments = s3db.resource("work_assignment", filter=query)
        success = assignments.delete()
        if not success:
            error = assignments.error or current.ERROR.NOT_PERMITTED
            r.error(403, error)

        output = current.xml.json_message(True)

        return output

# =============================================================================
class work_JobListLayout(S3DataListLayout):
    """ Data List Layout for Job Lists """

    list_fields = ["priority",
                   "job_type_id",
                   "name",
                   "details",
                   "site_id",
                   "start_date",
                   "duration",
                   "status",
                   "workers_min",
                   "workers_max",
                   "workers_assigned",
                   "modified_on",
                   ]

    # ---------------------------------------------------------------------
    def __init__(self, profile="work_job"):
        """ Constructor """

        super(work_JobListLayout, self).__init__(profile=profile)

        self.current_assignments = set()

    # ---------------------------------------------------------------------
    def prep(self, resource, records):

        logged_in_person = current.auth.s3_logged_in_person()
        if not logged_in_person:
            self.logged_in = False
            return

        self.logged_in = True

        db = current.db
        atable = current.s3db.work_assignment

        # Get all jobs the current user is assigned to
        record_ids = [record["_row"]["work_job.id"] for record in records]
        query = (atable.job_id.belongs(record_ids)) & \
                (atable.person_id == logged_in_person) & \
                (atable.deleted != True)
        rows = db(query).select(atable.job_id)
        self.current_assignments = set(row.job_id for row in rows)

    # ---------------------------------------------------------------------
    def render_header(self, list_id, item_id, resource, rfields, record):
        """
            Render the card header

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        T = current.T

        toolbox = self.render_toolbox(list_id,
                                      resource,
                                      record,
                                      )
        if not toolbox:
            toolbox = ""

        place = record["work_job.site_id"]
        date = record["work_job.start_date"]
        hours_planned = record["work_job.duration"]
        job_type = record["work_job.job_type_id"]

        header = DIV(SPAN(place,
                          _class="location-title",
                          ),
                     SPAN(date,
                          _class="date-title",
                          ),
                     SPAN("%s %s" % (hours_planned, T("Hours")),
                          _class="date-title",
                          ),
                     SPAN(job_type,
                          _class="date-title",
                          ),
                     toolbox,
                     _class="card-header",
                     )
        return header

    # ---------------------------------------------------------------------
    def render_body(self, list_id, item_id, resource, rfields, record):
        """
            Render the card body

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        T = current.T

        # Title and Description
        title = record["work_job.name"]
        details = record["work_job.details"]

        # Priority, Job Type and Last Update
        status = record["work_job.status"]
        priority = record["work_job.priority"]
        last_modified = record["work_job.modified_on"]

        date_line = DIV(LABEL(T("Status"),
                              _class="dl-inline-label",
                              ),
                        SPAN(status,
                             _class="dl-inline-value",
                             ),
                        LABEL(T("Priority"),
                              _class="dl-inline-label",
                              ),
                        SPAN(priority,
                             _class="dl-inline-value",
                             ),
                        LABEL(T("Last Updated"),
                              _class="dl-inline-label",
                              ),
                        SPAN(last_modified,
                             _class="dl-inline-value",
                             ),
                        _class="dl-inline-data",
                        )

        footer = self.render_footer(list_id,
                                    item_id,
                                    resource,
                                    rfields,
                                    record,
                                    )

        # Compose card body
        body = DIV(DIV(title,
                       _class="card-subtitle"
                       ),
                   details,
                   date_line,
                   footer,
                   _class="media-body",
                   )

        return DIV(body, _class="media")

    # ---------------------------------------------------------------------
    def render_footer(self, list_id, item_id, resource, rfields, record):
        """
            Render the card footer (including card action button)

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        T = current.T

        raw = record["_row"]

        button = ""
        actionable = False

        # Check job status
        status = raw["work_job.status"]
        if status == "STARTED":
            button_text = T("Job has started")
        elif status == "COMPLETED":
            button_text = T("Job has been completed")
        elif status == "CANCELLED":
            button_text = T("Job has been cancelled")
        else:
            button_text = ""
            actionable = True

        if actionable:
            if not self.logged_in:
                button = A(T("Login to sign up for this job"),
                           _href = URL(c="default", f="user",
                                       args = ["login"],
                                       vars = {"_next": URL(c="work", f="job",
                                                            args = ["datalist"],
                                                            ),
                                               },
                                       ),
                           _class = "action-btn",
                           )
            else:
                record_id = raw["work_job.id"]
                if record_id in self.current_assignments:
                    button = A("Cancel my assignment",
                               _class="delete-btn-ajax job-cancel",
                               )
                elif status != "ONHOLD":
                    start_date = raw["work_job.start_date"]
                    duration = raw["work_job.duration"]
                    if start_date:
                        # Calculate hours before end of planned time window
                        delta = (start_date - current.request.utcnow)
                        hours = (delta.days * 86400 + delta.seconds) / 3600
                        hours += duration if duration else 1
                        if hours < 0:
                            # Can no longer sign up
                            actionable = False
                            button_text = T("Job date has passed")
                    if actionable:
                        workers_needed = raw["work_job.workers_max"]
                        if not workers_needed:
                            workers_needed = raw["work_job.workers_min"]
                        workers_assigned = raw["work_job.workers_assigned"]
                        if workers_assigned < workers_needed:
                            button = A(T("Sign me up"),
                                       _class="action-btn job-signup",
                                       )
                        else:
                            actionable = False
                            button_text = T("No more helpers needed")
                else:
                    actionable = False
                    button_text = T("Job is on hold")

        if not actionable:
            button = A(button_text,
                       _class = "action-btn",
                       _disabled = "disabled",
                       )

        return DIV(button, _class="card-footer")

    # ---------------------------------------------------------------------
    def render_toolbox(self, list_id, resource, record):
        """
            Render the toolbox

            @param list_id: the HTML ID of the list
            @param resource: the S3Resource to render
            @param record: the record as dict
        """

        T = current.T

        # Get the record ID
        record_id = record["_row"]["work_job.id"]

        has_permission = current.auth.s3_has_permission
        table = current.db.work_job

        # Edit button (popup)
        if has_permission("update", table, record_id=record_id):
            edit_btn = A(ICON("edit"),
                         _href=URL(c="work", f="job",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id,
                                     }
                               ),
                         _class="s3_modal",
                         _title=T("Edit Job"),
                         )
        else:
            edit_btn = ""

        # Delete button (Ajax)
        if has_permission("delete", table, record_id=record_id):
            delete_btn = A(ICON("delete"),
                           _class="dl-item-delete",
                           )
        else:
            delete_btn = ""

        return DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

# END =========================================================================
