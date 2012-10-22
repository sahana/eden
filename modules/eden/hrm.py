# -*- coding: utf-8 -*-

""" Sahana Eden Human Resources Management

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

__all__ = ["S3HRModel",
           "S3HRSiteModel",
           "S3HRJobModel",
           "S3HRSkillModel",
           "S3HRExperienceModel",
           "S3HRProgrammeModel",
           "hrm_hr_represent",
           "hrm_human_resource_represent",
           #"hrm_position_represent",
           "hrm_vars",
           "hrm_compose",
           "hrm_map_popup",
           "hrm_service_record",
           "hrm_rheader",
           "hrm_training_event_controller",
           "hrm_training_controller",
           ]

import datetime

try:
    # try stdlib (Python 2.6)
    import json
except ImportError:
    try:
        # try external module
        import simplejson as json
    except:
        # fallback to pure-Python module
        import gluon.contrib.simplejson as json

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from eden.layouts import S3AddResourceLink

# =============================================================================
class S3HRModel(S3Model):

    names = ["hrm_human_resource",
             "hrm_human_resource_id",
             "hrm_autocomplete_search",
             "hrm_human_resource_search",
             "hrm_type_opts",
             ]

    def model(self):

        T = current.T
        db = current.db

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        ORGANISATION = messages.ORGANISATION

        add_component = self.add_component
        crud_strings = current.response.s3.crud_strings
        super_link = self.super_link

        # =========================================================================
        # Human Resource
        #
        # People who are either Staff or Volunteers
        #
        # @ToDo: Allocation Status for Events (link table)
        #

        # NB These numbers are hardcoded into KML Export stylesheet
        hrm_type_opts = {
            1: T("Staff"),
            2: T("Volunteer"),
        }

        hrm_status_opts = {
            1: T("current"),
            2: T("obsolete")
        }

        request = current.request
        controller = request.controller
        group = request.get_vars.get("group", None)
        if not group:
            if controller in ["hrm", "org", "inv", "cr", "hms"]:
                group = "staff"
            elif controller == "vol":
                group = "volunteer"

        auth = current.auth
        settings = current.deployment_settings
        job_roles = settings.get_hrm_job_roles()
        organisation_label = settings.get_hrm_organisation_label()

        if group == "volunteer":
            default_site = None
        else:
            default_site = auth.user.site_id if auth.is_logged_in() else None

        tablename = "hrm_human_resource"
        table = self.define_table(tablename,
                                  super_link("track_id", "sit_trackable"),
                                  self.org_organisation_id(
                                    label = organisation_label,
                                    requires = self.org_organisation_requires(updateable=True),
                                    widget = None,
                                    #widget=S3OrganisationAutocompleteWidget(
                                    #    default_from_profile=True),
                                    empty = False,
                                    ),
                                  super_link("site_id", "org_site",
                                             label=settings.get_org_site_label(),
                                             instance_types = auth.org_site_types,
                                             updateable = True,
                                             not_filterby = "obsolete",
                                             not_filter_opts = [True],
                                             default = default_site,
                                             readable = True,
                                             writable = True,
                                             #empty = False,
                                             represent = self.org_site_represent,
                                             ),
                                  self.pr_person_id(
                                    widget=S3AddPersonWidget(controller="hrm"),
                                    requires=IS_ADD_PERSON_WIDGET(),
                                    comment=None
                                    ),
                                  Field("type", "integer",
                                        requires = IS_IN_SET(hrm_type_opts,
                                                             zero=None),
                                        default = 1,
                                        #label = T("Type"),
                                        # Always set via the Controller we create from
                                        readable=False,
                                        writable=False,
                                        represent = lambda opt: \
                                            hrm_type_opts.get(opt,
                                                              UNKNOWN_OPT)),
                                  Field("code",
                                        #readable=False,
                                        #writable=False,
                                        label=T("Staff ID")),
                                  self.hrm_job_title_id(
                                                        #readable = False if group == "volunteer" else True,
                                                        #writable = False if group == "volunteer" else True,
                                                        ),
                                  self.hrm_multi_job_role_id(
                                                             readable = job_roles,
                                                             writable = job_roles,
                                                             ),
                                  self.hrm_department_id(),
                                  # Essential Staff
                                  Field("essential", "boolean",
                                        #readable = False,
                                        #writable = False,
                                        label = T("Essential Staff?"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Essential Staff?"),
                                                                        T("If the person counts as essential staff when evacuating all non-essential staff.")))),
                                  # Contract
                                  s3_date("start_date",
                                          label = T("Start Date"),
                                          ),
                                  s3_date("end_date",
                                          label = T("End Date"),
                                          ),
                                  # Current status
                                  Field("status", "integer",
                                        requires = IS_IN_SET(hrm_status_opts,
                                                             zero=None),
                                        default = 1,
                                        label = T("Status"),
                                        represent = lambda opt: \
                                            hrm_status_opts.get(opt,
                                                                UNKNOWN_OPT)),
                                  # Base location + Site
                                  self.gis_location_id(
                                        label=T("Base Location"),
                                        readable=False,
                                        writable=False
                                        ),
                                  Field("site_contact", "boolean",
                                        label = T("Facility Contact"),
                                        represent = lambda opt: \
                                            (T("No"),
                                             T("Yes"))[opt == True],
                                        ),
                                  *s3_meta_fields())

        crud_strings["hrm_staff"] = Storage(
            title_create = T("Add Staff Member"),
            title_display = T("Staff Member Details"),
            title_list = T("Staff"),
            title_update = T("Edit Staff Member Details"),
            title_search = T("Search Staff"),
            title_upload = T("Import Staff"),
            subtitle_create = T("Add New Staff Member"),
            label_list_button = T("List Staff Members"),
            label_create_button = T("Add Staff Member"),
            label_delete_button = T("Delete Staff Member"),
            msg_record_created = T("Staff member added"),
            msg_record_modified = T("Staff Member Details updated"),
            msg_record_deleted = T("Staff Member deleted"),
            msg_list_empty = T("No Staff currently registered"))

        crud_strings["hrm_volunteer"] = Storage(
            title_create = T("Add Volunteer"),
            title_display = T("Volunteer Details"),
            title_list = T("Volunteers"),
            title_update = T("Edit Volunteer Details"),
            title_search = T("Search Volunteers"),
            title_upload = T("Import Volunteers"),
            subtitle_create = T("Add New Volunteer"),
            label_list_button = T("List Volunteers"),
            label_create_button = T("Add Volunteer"),
            label_delete_button = T("Delete Volunteer"),
            msg_record_created = T("Volunteer added"),
            msg_record_modified = T("Volunteer Details updated"),
            msg_record_deleted = T("Volunteer deleted"),
            msg_list_empty = T("No Volunteers currently registered"))

        if group == "staff":
            label = T("Staff")
            crud_strings[tablename] = crud_strings["hrm_staff"]
            requires = IS_NULL_OR(
                        IS_ONE_OF(db, "hrm_human_resource.id",
                                  hrm_human_resource_represent,
                                  sort=True,
                                  filterby="type",
                                  filter_opts=(1,)
                                  )),
            widget = S3HumanResourceAutocompleteWidget(group="staff")
        elif group == "volunteer":
            label = T("Volunteer")
            crud_strings[tablename] = crud_strings["hrm_volunteer"]
            requires = IS_NULL_OR(
                        IS_ONE_OF(db, "hrm_human_resource.id",
                                  hrm_human_resource_represent,
                                  sort=True,
                                  filterby="type",
                                  filter_opts=(2,)
                                  )),
            widget = S3HumanResourceAutocompleteWidget(group="volunteer")
        else:
            label = T("Human Resource")
            requires = IS_NULL_OR(
                        IS_ONE_OF(db, "hrm_human_resource.id",
                                  hrm_human_resource_represent,
                                  sort=True
                                  )),
            widget = S3HumanResourceAutocompleteWidget()
            crud_strings[tablename] = Storage(
                title_create = T("Add Staff Member"),
                title_display = T("Staff Member Details"),
                title_list = T("Staff & Volunteers"),
                title_update = T("Edit Record"),
                title_search = T("Search Staff & Volunteers"),
                title_upload =T("Search Staff & Volunteers"),
                subtitle_create = T("Add New Staff Member"),
                label_list_button = T("List Staff & Volunteers"),
                label_create_button = T("Add Staff Member"),
                label_delete_button = T("Delete Record"),
                msg_record_created = T("Staff member added"),
                msg_record_modified = T("Record updated"),
                msg_record_deleted = T("Record deleted"),
                msg_list_empty = T("No staff or volunteers currently registered"))

        tooltip = DIV(_class="tooltip",
                      _title="%s|%s" % (T("Human Resource"),
                                        T("Enter some characters to bring up a list of possible matches")))
        comment = S3AddResourceLink(c = "vol" if group == "volunteer" else "hrm",
                                    f = group or "staff",
                                    label=crud_strings[tablename].label_create_button,
                                    title=label,
                                    tooltip=tooltip)

        human_resource_id = S3ReusableField("human_resource_id", table,
                                            sortby = ["type", "status"],
                                            requires = requires,
                                            represent = hrm_human_resource_represent,
                                            label = label,
                                            comment = comment,
                                            widget = widget,
                                            ondelete = "RESTRICT"
                                            )

        table.virtualfields.append(HRMVirtualFields())

        # Components
        # Availability
        #add_component("hrm_availability",
        #              hrm_human_resource="human_resource_id")
        # Hours
        #add_component("hrm_hours",
        #              hrm_human_resource="human_resource_id")

        # Volunteer Cluster
        add_component("vol_volunteer_cluster",
                      hrm_human_resource=dict(joinby="human_resource_id",
                                              multiple=False))
        # Volunteer Group
        add_component("vol_volunteer_group",
                      hrm_human_resource=dict(joinby="human_resource_id",
                                              multiple=False))

        hrm_autocomplete_search = S3HRSearch()
        human_resource_search = S3Search(
            simple=(self.human_resource_search_simple_widget("simple")),
            advanced=(self.human_resource_search_simple_widget("advanced"),
                      # S3SearchOptionsWidget(
                        # name="human_resource_search_type",
                        # label=T("Type"),
                        # field="type",
                        # cols = 2,
                        # options = hrm_type_opts,
                      # ),
                      S3SearchOptionsWidget(
                        name="human_resource_search_status",
                        label=T("Status"),
                        field="status",
                        cols = 2,
                        options = hrm_status_opts,
                      ),
                      S3SearchOptionsWidget(
                        name="human_resource_search_org",
                        label=ORGANISATION,
                        field="organisation_id",
                        represent = self.org_organisation_represent,
                        cols = 3,
                      ),
                      S3SearchOptionsWidget(
                        name="human_resource_search_L1",
                        field="location_id$L1",
                        location_level="L1",
                        cols = 3,
                      ),
                      S3SearchOptionsWidget(
                        name="human_resource_search_L2",
                        field="location_id$L2",
                        location_level="L2",
                        cols = 3,
                      ),
                      S3SearchOptionsWidget(
                        name="human_resource_search_L3",
                        field="location_id$L3",
                        location_level="L3",
                        cols = 3,
                      ),
                      S3SearchOptionsWidget(
                        name="human_resource_search_L4",
                        field="location_id$L4",
                        location_level="L4",
                        cols = 3,
                      ),
                      S3SearchLocationWidget(
                        name="human_resource_search_map",
                        label=T("Map"),
                      ),
                      # Don't change the order of this without updating controllers/vol/volunteer()
                      S3SearchOptionsWidget(
                        name="human_resource_search_site",
                        label=T("Facility"),
                        field="site_id",
                      ),
                      S3SearchOptionsWidget(
                        name="human_resource_search_training",
                        label=T("Training"),
                        field="course",
                        cols = 3,
                        options = self.hrm_course_opts,
                      ),
                      # S3SearchSkillsWidget(
                        # name="human_resource_search_skills",
                        # label=T("Skills"),
                        # field="skill_id"
                      # ),
                      # This currently breaks Requests from being able to save since this form is embedded inside the S3SearchAutocompleteWidget
                      #S3SearchMinMaxWidget(
                      #  name="human_resource_search_date",
                      #  method="range",
                      #  label=T("Contract Expiry Date"),
                      #  field="end_date"
                      #),
            )
        )

        report_fields = ["organisation_id",
                         "person_id",
                         "site_id",
                         (T("Training"), "course"),
                         "location_id$L1",
                         "location_id$L2",
                         ]

        # Redirect to the Details tabs after creation
        if controller == "vol" or \
           controller == "hrm":
            hrm_url = URL(c=controller, f="person",
                          vars={"human_resource.id":"[id]"})
        else:
            # Being added as a component to Org, Site or Project
            hrm_url = None

        # Custom Form
        crud_form = s3forms.S3SQLCustomForm("organisation_id",
                                            "site_id",
                                            "person_id",
                                            "job_title_id",
                                            "job_role_id",
                                            "department_id",
                                            "volunteer_cluster.vol_cluster_type_id",
                                            "volunteer_cluster.vol_cluster_id",
                                            "volunteer_cluster.vol_cluster_position_id",
                                            "start_date",
                                            "end_date",
                                            "status",
                                            )

        self.configure(tablename,
                       crud_form = crud_form,
                       super_entity = "sit_trackable",
                       mark_required = ["organisation_id"],
                       deletable = current.deployment_settings.get_hrm_deletable(),
                       search_method = human_resource_search,
                       onaccept = hrm_human_resource_onaccept,
                       ondelete = self.hrm_human_resource_ondelete,
                       deduplicate = self.hrm_human_resource_duplicate,
                       report_options = Storage(
                            search=[
                                  S3SearchOptionsWidget(
                                    name="human_resource_search_org",
                                    label=ORGANISATION,
                                    field="organisation_id",
                                    represent = self.org_organisation_represent,
                                    cols = 3
                                  ),
                                S3SearchOptionsWidget(
                                    name="human_resource_search_L1",
                                    field="location_id$L1",
                                    location_level="L1",
                                    cols = 3,
                                ),
                                S3SearchOptionsWidget(
                                    name="human_resource_search_L2",
                                    field="location_id$L2",
                                    location_level="L2",
                                    cols = 3,
                                ),
                                S3SearchOptionsWidget(
                                    name="human_resource_search_site",
                                    label=T("Facility"),
                                    field="site_id"
                                ),
                            ],
                            rows=report_fields,
                            cols=report_fields,
                            facts=report_fields,
                            methods=["count", "list"],
                            defaults=Storage(rows="human_resource.organisation_id",
                                             cols="human_resource.course",
                                             fact="human_resource.person_id",
                                             aggregate="count")
                       ),
                       create_next = hrm_url,
                       update_next = hrm_url,
                       realm_components = ["presence"],
                       update_realm = True,
                       )

        # ---------------------------------------------------------------------
        # Pass model-global names to s3db.*
        #
        return Storage(
                    hrm_human_resource_id = human_resource_id,
                    hrm_human_resource_search = human_resource_search,
                    hrm_autocomplete_search = hrm_autocomplete_search,
                    hrm_type_opts = hrm_type_opts,
                )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """
        human_resource_id = S3ReusableField("human_resource_id", "integer",
                                            readable=False, writable=False)
        return Storage(
                hrm_human_resource_id = human_resource_id
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def human_resource_search_simple_widget(type):

        T = current.T

        return S3SearchSimpleWidget(
                    name = "human_resource_search_simple_%s" % type,
                    label = T("Name"),
                    comment = T("You can search by job title or person name - enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
                    field = ["person_id$first_name",
                             "person_id$middle_name",
                             "person_id$last_name",
                             #"job_role_id$name",
                             "job_title_id$name",
                             ]
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_course_opts():
        """
            Provide the options for the HRM course search filter
        """

        table = current.s3db.hrm_course
        root_org = current.auth.root_org()
        if root_org:
            query = (table.deleted == False) & \
                    ((table.organisation_id == root_org) | \
                     (table.organisation_id == None))
        else:
            query = (table.deleted == False) & \
                    (table.organisation_id == None)

        opts = current.db(query).select(table.id,
                                        table.name)
        _dict = {}
        for opt in opts:
            _dict[opt.id] = opt.name
        return _dict

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_ondelete(row):
        """ On-delete routine for HR records """

        htable = current.db.hrm_human_resource

        if row and "id" in row:
            record = htable[row.id]
        else:
            return

        if record.deleted:
            try:
                fk = json.loads(record.deleted_fk)
                person_id = fk.get("person_id", None)
            except:
                return
            if not person_id:
                return

            current.s3db.pr_update_affiliations(htable, record)

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_duplicate(item):
        """
            HR record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        if item.tablename == "hrm_human_resource":
            data = item.data
            person_id = "person_id" in data and data.person_id
            org = "organisation_id" in data and data.organisation_id

            # This allows only one HR record per person and organisation,
            # if multiple HR records of the same person with the same org
            # are desired, then this needs an additional criteria in the
            # query (e.g. job title, or type):

            table = item.table

            query = (table.deleted != True) & \
                    (table.person_id == person_id)
            if org:
                query = query & (table.organisation_id == org)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3HRSiteModel(S3Model):

    names = ["hrm_human_resource_site",
             ]

    def model(self):

        T = current.T

        # =========================================================================
        # Link between Human Resources & Facilities
        # - this is used to allow the right UI interface when adding HRs to a
        #   Facility via the Staff tab
        #

        tablename = "hrm_human_resource_site"
        table = self.define_table(tablename,
                                  self.hrm_human_resource_id(ondelete = "CASCADE"),
                                  self.org_site_id,
                                  Field("site_contact", "boolean",
                                        label = T("Facility Contact"),
                                        represent = lambda opt: \
                                            (T("No"),
                                             T("Yes"))[opt == True],
                                        ),
                                  *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = self.hrm_human_resource_site_duplicate,
                       onaccept = self.hrm_human_resource_site_onaccept,
                       ondelete = self.hrm_human_resource_site_onaccept,
                       )

        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Assign Staff"),
            title_display = T("Staff Assignment Details"),
            title_list = T("Staff Assignments"),
            title_update = T("Edit Staff Assignment"),
            title_search = T("Search Staff Assignments"),
            subtitle_create = T("Add Staff Assignment"),
            label_list_button = T("List Staff Assignments"),
            label_create_button = T("Add New Staff Assignment"),
            label_delete_button = T("Delete Staff Assignment"),
            msg_record_created = T("Staff Assigned"),
            msg_record_modified = T("Staff Assignment updated"),
            msg_record_deleted = T("Staff Assignment removed"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no staff assigned"))

        # ---------------------------------------------------------------------
        # Pass model-global names to s3db.*
        #
        return Storage(
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_site_onaccept(form):
        """
            Update the Human Resource record with the site_id
        """

        # Deletion and update have a different format
        try:
            id = form.vars.id
            delete = False
        except:
            id = form.id
            delete = True

        # Get the full record
        db = current.db
        ltable = db.hrm_human_resource_site
        table = db.hrm_human_resource
        if delete:
            record = db(ltable.id == id).select(ltable.deleted_fk,
                                                limitby=(0, 1)).first()

            if record:
                deleted_fks = json.loads(record.deleted_fk)
                human_resource_id = deleted_fks["human_resource_id"]
                db(table.id == human_resource_id).update(
                                                        location_id=None,
                                                        site_id=None,
                                                        site_contact=False
                                                        )
        else:
            human_resource_id = form.vars.human_resource_id

            # Check if we have multiple records for this HR
            # (i.e. staff was assigned elsewhere previously)
            rows = db(ltable.human_resource_id == human_resource_id).select(ltable.id,
                                                                            ltable.site_id,
                                                                            ltable.human_resource_id,
                                                                            ltable.site_contact,
                                                                            orderby=~ltable.id)
            first = True
            for row in rows:
                if first:
                    first = False
                    continue
                db(ltable.id == row.id).delete()

            record = rows.first()
            db(table.id == human_resource_id).update(
                                                    site_id=record.site_id,
                                                    site_contact=record.site_contact
                                                    )
            # Fire the normal onaccept
            hrform = Storage(id=human_resource_id)
            hrm_human_resource_onaccept(hrform)

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_site_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Each HR can only be assigned to one site at a time
        """

        if item.tablename == "hrm_human_resource_site":
            data = item.data
            hr = "human_resource_id" in data and data.human_resource_id

            table = item.table
            query = (table.human_resource_id == human_resource_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3HRJobModel(S3Model):

    names = ["hrm_department",
             "hrm_department_id",
             "hrm_job_role",
             "hrm_job_role_id",
             "hrm_multi_job_role_id",
             "hrm_job_title",
             "hrm_job_title_id",
             #"hrm_position",
             #"hrm_position_id",
             ]

    def model(self):

        T = current.T
        db = current.db

        organisation_id = self.org_organisation_id

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        root_org = current.auth.root_org()
        if root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        request = current.request
        group = request.get_vars.get("group", None)
        if not group and request.controller == "vol":
            group = "volunteer"

        # =========================================================================
        # Departments
        #
        tablename = "hrm_department"
        table = define_table(tablename,
                             Field("name", notnull=True,
                                   length=64,
                                   label=T("Name")),
                             # Only included in order to be able to set
                             # realm_entity to filter appropriately
                             organisation_id(
                                             default = root_org,
                                             readable = False,
                                             writable = False,
                                             ),
                             s3_comments(label=T("Description"),
                                         comment=None),
                             *s3_meta_fields())

        label_create = T("Add New Department")
        crud_strings[tablename] = Storage(
            title_create = T("Add Department"),
            title_display = T("Department Details"),
            title_list = T("Department Catalog"),
            title_update = T("Edit Department"),
            title_search = T("Search Departments"),
            title_upload = T("Import Departments"),
            subtitle_create = T("Add Department"),
            label_list_button = T("List Departments"),
            label_create_button = label_create,
            label_delete_button = T("Delete Department"),
            msg_record_created = T("Department added"),
            msg_record_modified = T("Department updated"),
            msg_record_deleted = T("Department deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        department_id = S3ReusableField("department_id", table,
                                sortby = "name",
                                label = T("Department / Unit"),
                                requires = IS_NULL_OR(
                                            IS_ONE_OF(db, "hrm_department.id",
                                                      hrm_department_represent,
                                                      filterby="organisation_id",
                                                      filter_opts=filter_opts)),
                                represent = hrm_department_represent,
                                comment=S3AddResourceLink(c="vol" if group == "volunteer" else "hrm",
                                                          f="department",
                                                          label=label_create),
                                ondelete = "SET NULL")

        configure("hrm_department",
                  deduplicate=self.hrm_department_duplicate)

        # =========================================================================
        # Job Roles (Mayon: StaffResourceType)
        #
        tablename = "hrm_job_role"
        table = define_table(tablename,
                             Field("name", notnull=True,
                                   length=64,    # Mayon compatibility
                                   label=T("Name")),
                             # Only included in order to be able to set
                             # realm_entity to filter appropriately
                             organisation_id(
                                             default = root_org,
                                             readable = False,
                                             writable = False,
                                             ),
                             s3_comments(label=T("Description"),
                                         comment=None),
                             *s3_meta_fields())

        vars = current.request.get_vars
        if group == "volunteer":
            label = T("Volunteer Role")
            label_create = T("Add New Volunteer Role")
            tooltip = T("A volunteer may have multiple roles in addition to their formal job title.")
        else:
            label = T("Job Role")
            label_create = T("Add New Job Role")
            tooltip = T("A staff member may have multiple roles in addition to their formal job title.")

        crud_strings[tablename] = Storage(
            title_create = T("Add Job Role"),
            title_display = T("Job Role Details"),
            title_list = T("Job Role Catalog"),
            title_update = T("Edit Job Role"),
            title_search = T("Search Job Roles"),
            title_upload = T("Import Job Roles"),
            subtitle_create = T("Add Job Role"),
            label_list_button = T("List Job Roles"),
            label_create_button = label_create,
            label_delete_button = T("Delete Job Role"),
            msg_record_created = T("Job Role added"),
            msg_record_modified = T("Job Role updated"),
            msg_record_deleted = T("Job Role deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        job_role_id = S3ReusableField("job_role_id", table,
                                sortby = "name",
                                label = label,
                                requires = IS_NULL_OR(
                                            IS_ONE_OF(db, "hrm_job_role.id",
                                                      hrm_job_role_represent,
                                                      filterby="organisation_id",
                                                      filter_opts=filter_opts)),
                                represent = hrm_job_role_represent,
                                comment=S3AddResourceLink(c="vol" if group == "volunteer" else "hrm",
                                                          f="job_role",
                                                          label=label_create,
                                                          title=label,
                                                          tooltip=tooltip),
                                ondelete = "SET NULL")

        multi_job_role_id = S3ReusableField("job_role_id",
                                "list:reference hrm_job_role",
                                sortby = "name",
                                label = label,
                                requires = IS_NULL_OR(
                                            IS_ONE_OF(db, "hrm_job_role.id",
                                                      hrm_job_role_represent,
                                                      filterby="organisation_id",
                                                      filter_opts=filter_opts,
                                                      sort=True,
                                                      multiple=True)),
                                represent = hrm_job_role_multirepresent,
                                comment=S3AddResourceLink(c="vol" if group == "volunteer" else "hrm",
                                                          f="job_role",
                                                          label=label_create,
                                                          title=label,
                                                          tooltip=tooltip),
                                ondelete = "SET NULL")

        configure("hrm_job_role",
                  deduplicate=self.hrm_job_role_duplicate)

        # =========================================================================
        # Job Titles
        #
        tablename = "hrm_job_title"
        table = define_table(tablename,
                             Field("name", notnull=True,
                                   length=64,    # Mayon compatibility
                                   label=T("Name")),
                             # Only included in order to be able to set
                             # realm_entity to filter appropriately
                             organisation_id(
                                             default = root_org,
                                             readable = False,
                                             writable = False,
                                             ),
                             s3_comments(label=T("Description"),
                                         comment=None),
                             *s3_meta_fields())

        if group == "volunteer":
            label = T("Volunteer Role")
            label_create = T("Add New Volunteer Role")
            tooltip = T("The volunteer's role")
            crud_strings[tablename] = Storage(
                title_create = T("Add Volunteer Role"),
                title_display = T("Volunteer Role Details"),
                title_list = T("Volunteer Role Catalog"),
                title_update = T("Edit Volunteer Role"),
                title_search = T("Search Volunteer Roles"),
                subtitle_create = T("Add Volunteer Role"),
                label_list_button = T("List Volunteer Roles"),
                label_create_button = label_create,
                label_delete_button = T("Delete Volunteer Role"),
                msg_record_created = T("Volunteer Role added"),
                msg_record_modified = T("Volunteer Role updated"),
                msg_record_deleted = T("Volunteer Role deleted"),
                msg_list_empty = T("Currently no entries in the catalog"))
        else:
            label = T("Job Title")
            label_create = T("Add New Job Title")
            tooltip = T("The staff member's official job title")
            crud_strings[tablename] = Storage(
                title_create = T("Add Job Title"),
                title_display = T("Job Title Details"),
                title_list = T("Job Title Catalog"),
                title_update = T("Edit Job Title"),
                title_search = T("Search Job Titles"),
                subtitle_create = T("Add Job Title"),
                label_list_button = T("List Job Titles"),
                label_create_button = label_create,
                label_delete_button = T("Delete Job Title"),
                msg_record_created = T("Job Title added"),
                msg_record_modified = T("Job Title updated"),
                msg_record_deleted = T("Job Title deleted"),
                msg_list_empty = T("Currently no entries in the catalog"))

        job_title_id = S3ReusableField("job_title_id", table,
                                sortby = "name",
                                label = label,
                                requires = IS_NULL_OR(
                                            IS_ONE_OF(db, "hrm_job_title.id",
                                                      hrm_job_title_represent,
                                                      filterby="organisation_id",
                                                      filter_opts=filter_opts)),
                                represent = hrm_job_title_represent,
                                comment=S3AddResourceLink(c="vol" if group == "volunteer" else "hrm",
                                                          f="job_title",
                                                          label=label_create,
                                                          title=label,
                                                          tooltip=tooltip),
                                ondelete = "SET NULL")

        configure("hrm_job_title",
                  deduplicate=self.hrm_job_title_duplicate)

        # =========================================================================
        # Positions
        #
        # @ToDo: Shifts for use in Scenarios & during Exercises & Events
        #
        # @ToDo: Vacancies
        #

        #tablename = "hrm_position"
        #table = define_table(tablename,
        #                          job_role_id(empty=False),
        #                          organisation_id(empty=False),
        #                          site_id,
        #                          group_id(label="Team"),
        #                          *s3_meta_fields())
        #table.site_id.readable = table.site_id.writable = True

        #crud_strings[tablename] = Storage(
        #    title_create = T("Add Position"),
        #    title_display = T("Position Details"),
        #    title_list = T("Position Catalog"),
        #    title_update = T("Edit Position"),
        #    title_search = T("Search Positions"),
        #    subtitle_create = T("Add Position"),
        #    label_list_button = T("List Positions"),
        #    label_create_button = T("Add Position"),
        #    label_delete_button = T("Delete Position"),
        #    msg_record_created = T("Position added"),
        #    msg_record_modified = T("Position updated"),
        #    msg_record_deleted = T("Position deleted"),
        #    msg_list_empty = T("Currently no entries in the catalog"))

        #label_create = crud_strings[tablename].label_create_button
        #position_id = S3ReusableField("position_id", table,
        #                              sortby = "name",
        #                              label = T("Position"),
        #                              requires = IS_NULL_OR(IS_ONE_OF(db,
        #                                                              "hrm_position.id",
        #                                                              hrm_position_represent)),
        #                              represent = hrm_position_represent,
        #                              comment = DIV(A(label_create,
        #                                              _class="colorbox",
        #                                              _href=URL(f="position",
        #                                                        args="create",
        #                                                        vars=dict(format="popup")),
        #                                              _target="top",
        #                                              _title=label_create),
        #                                            DIV(DIV(_class="tooltip",
        #                                                    _title="%s|%s" % (label_create,
        #                                                                      T("Add a new job role to the catalog."))))),
        #                              ondelete = "SET NULL")

        # =========================================================================
        # Availability
        #
        #weekdays = {
            #1: T("Monday"),
            #2: T("Tuesday"),
            #3: T("Wednesday"),
            #4: T("Thursday"),
            #5: T("Friday"),
            #6: T("Saturday"),
            #7: T("Sunday")
        #}
        #weekdays_represent = lambda opt: ",".join([str(weekdays[o]) for o in opt])

        #tablename = "hrm_availability"
        #table = define_table(tablename,
                                   #human_resource_id(),
                                   #Field("date_start", "date"),
                                   #Field("date_end", "date"),
                                   #Field("day_of_week", "list:integer",
                                          #requires=IS_EMPTY_OR(IS_IN_SET(weekdays,
                                                                          #zero=None,
                                                                          #multiple=True)),
                                          #default=[1, 2, 3, 4, 5],
                                          #widget=CheckboxesWidgetS3.widget,
                                          #represent=weekdays_represent
                                          #),
                                   #Field("hours_start", "time"),
                                   #Field("hours_end", "time"),
                                   ##location_id(label=T("Available for Location"),
                                               ##requires=IS_ONE_OF(db, "gis_location.id",
                                                                  ##gis_location_represent,
                                                                  ##filterby="level",
                                                                  ### @ToDo Should this change per config?
                                                                  ##filter_opts=gis.region_level_keys,
                                                                  ##orderby="gis_location.name"),
                                               ##widget=None),
                                   #*s3_meta_fields())

        # =========================================================================
        # Hours registration
        #
        #tablename = "hrm_hours"
        #table = define_table(tablename,
                                  #human_resource_id(),
                                  #Field("timestmp_in", "datetime"),
                                  #Field("timestmp_out", "datetime"),
                                  #Field("hours", "double"),
                                  #*s3_meta_fields())

        # =========================================================================
        # Vacancy
        #
        # These are Positions which are not yet Filled
        #
        #tablename = "hrm_vacancy"
        #table = define_table(tablename,
                                  #organisation_id(),
                                  ##Field("code"),
                                  #Field("title"),
                                  #Field("description", "text"),
                                  #self.super_link("site_id", "org_site",
                                                  #label=T("Facility"),
                                                  #readable=False,
                                                  #writable=False,
                                                  #sort=True,
                                                  #represent=s3db.org_site_represent),
                                  #Field("type", "integer",
                                         #requires = IS_IN_SET(hrm_type_opts, zero=None),
                                         #default = 1,
                                         #label = T("Type"),
                                         #represent = lambda opt: \
                                                    #hrm_type_opts.get(opt, UNKNOWN_OPT)),
                                  #Field("number", "integer"),
                                  ##location_id(),
                                  #Field("from", "date"),
                                  #Field("until", "date"),
                                  #Field("open", "boolean",
                                        #default=False),
                                  #Field("app_deadline", "date",
                                        #label=T("Application Deadline")),
                                  #*s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass model-global names to s3db.*
        #
        return Storage(
                    hrm_department_id = department_id,
                    hrm_job_role_id = job_role_id,
                    hrm_multi_job_role_id = multi_job_role_id,
                    hrm_job_title_id = job_title_id,
                    #hrm_position_id = position_id
                )


    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_department_duplicate(item):
        """
        """

        if item.tablename == "hrm_department":
            data = item.data
            name = "name" in data and data.name
            org = "organisation_id" in data and data.organisation_id

            table = item.table
            query = (table.name.lower() == name.lower())
            if org:
                query  = query & (table.organisation_id == org)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_job_role_duplicate(item):
        """
        """

        if item.tablename == "hrm_job_role":
            data = item.data
            name = "name" in data and data.name
            org = "organisation_id" in data and data.organisation_id

            table = item.table
            query = (table.name.lower() == name.lower())
            if org:
                query  = query & (table.organisation_id == org)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_job_title_duplicate(item):
        """
        """

        if item.tablename == "hrm_job_title":
            data = item.data
            name = "name" in data and data.name
            org = "organisation_id" in data and data.organisation_id

            table = item.table
            query = (table.name.lower() == name.lower())
            if org:
                query  = query & (table.organisation_id == org)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3HRSkillModel(S3Model):

    names = ["hrm_skill_type",
             "hrm_skill",
             "hrm_competency_rating",
             "hrm_competency",
             "hrm_credential",
             "hrm_training",
             "hrm_training_event",
             "hrm_certificate",
             "hrm_certification",
             "hrm_certification_onaccept",
             "hrm_certificate_skill",
             "hrm_course",
             "hrm_course_certificate",
             "hrm_skill_id",
             "hrm_multi_skill_id",
             ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        settings = current.deployment_settings

        person_id = self.pr_person_id
        organisation_id = self.org_organisation_id
        site_id = self.org_site_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        ADMIN = current.session.s3.system_roles.ADMIN

        s3_string_represent = lambda str: str if str else NONE
        s3_date_represent = S3DateTime.date_represent
        s3_date_format = settings.get_L10n_date_format()

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        s3_has_role = auth.s3_has_role
        super_link = self.super_link

        root_org = auth.root_org()

        group = current.request.get_vars.get("group", None)

        # ---------------------------------------------------------------------
        # Skill Types
        # - optional hierarchy of skills
        #   disabled by default, enable with deployment_settings.hrm.skill_types = True
        #   if enabled, then each needs their own list of competency levels
        #
        tablename = "hrm_skill_type"
        table = define_table(tablename,
                             Field("name", notnull=True, unique=True,
                                   length=64,
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Skill Type"),
            title_display = T("Details"),
            title_list = T("Skill Type Catalog"),
            title_update = T("Edit Skill Type"),
            title_search = T("Search Skill Types"),
            subtitle_create = T("Add Skill Type"),
            label_list_button = T("List Skill Types"),
            label_create_button = T("Add New Skill Type"),
            label_delete_button = T("Delete Skill Type"),
            msg_record_created = T("Skill Type added"),
            msg_record_modified = T("Skill Type updated"),
            msg_record_deleted = T("Skill Type deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        skill_types = settings.get_hrm_skill_types()
        label_create = crud_strings[tablename].label_create_button
        skill_type_id = S3ReusableField("skill_type_id", table,
                            sortby = "name",
                            label = T("Skill Type"),
                            default=self.skill_type_default,
                            readable=skill_types,
                            writable=skill_types,
                            requires = IS_NULL_OR(
                                        IS_ONE_OF(db, "hrm_skill_type.id",
                                                  self.hrm_skill_type_represent
                                                  )),
                            represent = self.hrm_skill_type_represent,
                            comment=S3AddResourceLink(f="skill_type",
                                                      label=label_create,
                                                      title=label_create,
                                                      tooltip=T("Add a new skill type to the catalog.")),
                            ondelete = "RESTRICT")

        configure(tablename,
                  deduplicate=self.hrm_skill_type_duplicate)

        # ---------------------------------------------------------------------
        # Skills
        # - these can be simple generic skills or can come from certifications
        #
        tablename = "hrm_skill"
        table = define_table(tablename,
                             skill_type_id(empty=False),
                             Field("name", notnull=True, unique=True,
                                   length=64,    # Mayon compatibility
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Skill"),
            title_display = T("Skill Details"),
            title_list = T("Skill Catalog"),
            title_update = T("Edit Skill"),
            title_search = T("Search Skills"),
            subtitle_create = T("Add Skill"),
            label_list_button = T("List Skills"),
            label_create_button = T("Add New Skill"),
            label_delete_button = T("Delete Skill"),
            msg_record_created = T("Skill added"),
            msg_record_modified = T("Skill updated"),
            msg_record_deleted = T("Skill deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        autocomplete = False
        label_create = crud_strings[tablename].label_create_button
        if autocomplete:
            # NB FilterField widget needs fixing for that too
            widget = S3AutocompleteWidget(current.request.controller,
                                          "skill")
            tooltip = T("Enter some characters to bring up a list of possible matches")
        else:
            widget = None
            tooltip = None

        skill_help = S3AddResourceLink(f="skill",
                                       label=label_create,
                                       tooltip=tooltip)

        skill_id = S3ReusableField("skill_id", table,
                        sortby = "name",
                        label = T("Skill"),
                        requires = IS_NULL_OR(
                                    IS_ONE_OF(db, "hrm_skill.id",
                                              self.hrm_skill_represent,
                                              sort=True
                                              )),
                        represent = self.hrm_skill_represent,
                        comment = skill_help,
                        ondelete = "SET NULL",
                        widget = widget
                        )

        multi_skill_id = S3ReusableField("skill_id", "list:reference hrm_skill",
                                         sortby = "name",
                                         label = T("Skills"),
                                         requires = IS_NULL_OR(
                                                        IS_ONE_OF(db, "hrm_skill.id",
                                                                  self.hrm_skill_represent,
                                                                  sort=True,
                                                                  multiple=True
                                                                  )),
                                         represent = hrm_skill_multirepresent,
                                         #comment = skill_help,
                                         ondelete = "SET NULL",
                                         widget = S3MultiSelectWidget()
                                        )

        configure("hrm_skill",
                  deduplicate=self.hrm_skill_duplicate)

        # Components
        add_component("req_req_skill", hrm_skill="skill_id")

        # =====================================================================
        # Competency Ratings
        #
        # These are the levels of competency. Default is Levels 1-3.
        # The levels can vary by skill_type if deployment_settings.hrm.skill_types = True
        #
        # The textual description can vary a lot, but is important to individuals
        # Priority is the numeric used for preferential role allocation in Mayon
        #
        # http://docs.oasis-open.org/emergency/edxl-have/cs01/xPIL-types.xsd
        #
        tablename = "hrm_competency_rating"
        table = define_table(tablename,
                             skill_type_id(empty=False),
                             Field("name",
                                   label = T("Name"),
                                   length=64),       # Mayon Compatibility
                             Field("priority", "integer",
                                   label = T("Priority"),
                                   requires = IS_INT_IN_RANGE(1, 9),
                                   widget = S3SliderWidget(minval=1, maxval=9, steprange=1, value=1),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Priority"),
                                                                   T("Priority from 1 to 9. 1 is most preferred.")))),
                             s3_comments(),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Competency Rating"),
            title_display = T("Competency Rating Details"),
            title_list = T("Competency Rating Catalog"),
            title_update = T("Edit Competency Rating"),
            title_search = T("Search Competency Ratings"),
            subtitle_create = T("Add Competency Rating"),
            label_list_button = T("List Competency Ratings"),
            label_create_button = T("Add New Competency Rating"),
            label_delete_button = T("Delete Competency Rating"),
            msg_record_created = T("Competency Rating added"),
            msg_record_modified = T("Competency Rating updated"),
            msg_record_deleted = T("Competency Rating deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        competency_id = S3ReusableField("competency_id", table,
                                        sortby = "priority",
                                        label = T("Competency"),
                                        requires = IS_NULL_OR(
                                                    IS_ONE_OF(db,
                                                              "hrm_competency_rating.id",
                                                              self.hrm_competency_rating_represent,
                                                              orderby="~hrm_competency_rating.priority",
                                                              sort=True)),
                                        represent = self.hrm_competency_rating_represent,
                                        comment = self.competency_rating_comment(),
                                        ondelete = "RESTRICT")

        configure("hrm_competency_rating",
                  deduplicate=self.hrm_competency_rating_duplicate)

        # ---------------------------------------------------------------------
        # Competencies
        #
        # Link table between Persons & Skills
        # - with a competency rating & confirmation
        #
        # Users can add their own but these are confirmed only by specific roles
        #
        # Component added in the hrm person() controller
        #
        tablename = "hrm_competency"
        table = define_table(tablename,
                             person_id(),
                             skill_id(),
                             competency_id(),
                             # This field can only be filled-out by specific roles
                             # Once this has been filled-out then the other fields are locked
                             organisation_id(label = T("Confirming Organization"),
                                             widget = S3OrganisationAutocompleteWidget(
                                                        default_from_profile=True),
                                             comment = None,
                                             writable = False),
                             Field("from_certification", "boolean",
                                   default=False,
                                   readable=False,
                                   writable=False),
                             s3_comments(),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Skill"),
            title_display = T("Skill Details"),
            title_list = T("Skills"),
            title_update = T("Edit Skill"),
            title_search = T("Search Skills"),
            subtitle_create = T("Add Skill"),
            label_list_button = T("List Skills"),
            label_create_button = T("Add New Skill"),
            label_delete_button = T("Remove Skill"),
            msg_record_created = T("Skill added"),
            msg_record_modified = T("Skill updated"),
            msg_record_deleted = T("Skill removed"),
            msg_list_empty = T("Currently no Skills registered"))

        configure("hrm_competency",
                  deduplicate=self.hrm_competency_duplicate)

        # =====================================================================
        # Skill Provisions
        #
        # The minimum Competency levels in a Skill to be assigned the given Priority
        # for allocation to Mayon's shifts for the given Job Role
        #
        #tablename = "hrm_skill_provision"
        #table = define_table(tablename,
        #                          Field("name", notnull=True, unique=True,
        #                                length=32,    # Mayon compatibility
        #                                label=T("Name")),
        #                          self.hrm_job_role_id(),
        #                          skill_id(),
        #                          competency_id(),
        #                          Field("priority", "integer",
        #                                requires = IS_INT_IN_RANGE(1, 9),
        #                                widget = S3SliderWidget(minval=1, maxval=9, steprange=1, value=1),
        #                                comment = DIV(_class="tooltip",
        #                                              _title="%s|%s" % (T("Priority"),
        #                                                                T("Priority from 1 to 9. 1 is most preferred.")))),
        #                          s3_comments(),
        #                          *s3_meta_fields())

        #crud_strings[tablename] = Storage(
        #    title_create = T("Add Skill Provision"),
        #    title_display = T("Skill Provision Details"),
        #    title_list = T("Skill Provision Catalog"),
        #    title_update = T("Edit Skill Provision"),
        #    title_search = T("Search Skill Provisions"),
        #    subtitle_create = T("Add Skill Provision"),
        #    label_list_button = T("List Skill Provisions"),
        #    label_create_button = T("Add Skill Provision"),
        #    label_delete_button = T("Delete Skill Provision"),
        #    msg_record_created = T("Skill Provision added"),
        #    msg_record_modified = T("Skill Provision updated"),
        #    msg_record_deleted = T("Skill Provision deleted"),
        #    msg_list_empty = T("Currently no entries in the catalog"))

        #label_create = crud_strings[tablename].label_create_button
        #skill_group_id = S3ReusableField("skill_provision_id", table,
        #                           sortby = "name",
        #                           label = T("Skill Provision"),
        #                           requires = IS_NULL_OR(IS_ONE_OF(db,
        #                                                           "hrm_skill_provision.id",
        #                                                           self.hrm_skill_provision_represent)),
        #                           represent = self.hrm_skill_provision_represent,
        #                           comment = DIV(A(label_create,
        #                                           _class="colorbox",
        #                                           _href=URL(f="skill_provision",
        #                                                     args="create",
        #                                                     vars=dict(format="popup")),
        #                                           _target="top",
        #                                           _title=label_create),
        #                                         DIV(DIV(_class="tooltip",
        #                                                 _title="%s|%s" % (label_create,
        #                                                                   T("Add a new skill provision to the catalog."))))),
        #                           ondelete = "SET NULL")


        # =====================================================================
        # Credentials
        #
        #   This determines whether an Organisation believes a person is suitable
        #   to fulfil a role. It is determined based on a combination of
        #   experience, training & a performance rating (medical fitness to come).
        #   @ToDo: Workflow to make this easy for the person doing the credentialling
        #
        # http://www.dhs.gov/xlibrary/assets/st-credentialing-interoperability.pdf
        #
        # Component added in the hrm person() controller
        #

        # Used by Courses
        # & 6-monthly rating (Portuguese Bombeiros)
        hrm_pass_fail_opts = {
            8: T("Pass"),
            9: T("Fail")
        }
        # 12-monthly rating (Portuguese Bombeiros)
        # - this is used to determine rank progression (need 4-5 for 5 years)
        hrm_five_rating_opts = {
            1: T("Poor"),
            2: T("Fair"),
            3: T("Good"),
            4: T("Very Good"),
            5: T("Excellent")
        }
        # Lookup to represent both sorts of ratings
        hrm_performance_opts = {
            1: T("Poor"),
            2: T("Fair"),
            3: T("Good"),
            4: T("Very Good"),
            5: T("Excellent"),
            8: T("Pass"),
            9: T("Fail")
        }

        tablename = "hrm_credential"
        table = define_table(tablename,
                             person_id(),
                             self.hrm_job_title_id(),
                             organisation_id(empty=False,
                                             widget = S3OrganisationAutocompleteWidget(
                                                        default_from_profile=True),
                                             label=T("Credentialling Organization")),
                             Field("performance_rating", "integer",
                                   label = T("Performance Rating"),
                                   requires = IS_IN_SET(hrm_pass_fail_opts,  # Default to pass/fail (can override to 5-levels in Controller)
                                                        zero=None),
                                   represent = lambda opt: \
                                       hrm_performance_opts.get(opt,
                                                                UNKNOWN_OPT)),
                             s3_date("date_received",
                                     label = T("Date Received")
                                     ),
                             s3_date("date_expires",   # @ToDo: Automation based on deployment_settings, e.g.: date received + 6/12 months
                                     label = T("Expiry Date")
                                     ),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Credential"),
            title_display = T("Credential Details"),
            title_list = T("Credentials"),
            title_update = T("Edit Credential"),
            title_search = T("Search Credentials"),
            subtitle_create = T("Add Credential"),
            label_list_button = T("List Credentials"),
            label_create_button = T("Add New Credential"),
            label_delete_button = T("Delete Credential"),
            msg_record_created = T("Credential added"),
            msg_record_modified = T("Credential updated"),
            msg_record_deleted = T("Credential deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Credentials registered"))

        # =========================================================================
        # Courses
        #
        tablename = "hrm_course"
        table = define_table(tablename,
                             Field("code"),
                             Field("name", length=128, notnull=True,
                                   label=T("Name")),
                             # Only included in order to be able to set
                             # realm_entity to filter appropriately
                             organisation_id(
                                             default = root_org,
                                             readable = False,
                                             writable = False,
                                             ),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Course"),
            title_display = T("Course Details"),
            title_list = T("Course Catalog"),
            title_update = T("Edit Course"),
            title_search = T("Search Courses"),
            title_upload = T("Import Courses"),
            subtitle_create = T("Add Course"),
            label_list_button = T("List Courses"),
            label_create_button = T("Add New Course"),
            label_delete_button = T("Delete Course"),
            msg_record_created = T("Course added"),
            msg_record_modified = T("Course updated"),
            msg_record_deleted = T("Course deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no entries in the catalog"))

        if s3_has_role(ADMIN):
            label_create = crud_strings[tablename].label_create_button
            course_help = S3AddResourceLink(c="vol" if group == "volunteer" else "hrm",
                                            f="course",
                                            label=label_create)
        else:
            course_help = DIV(_class="tooltip",
                              _title="%s|%s" % (T("Course"),
                              T("Enter some characters to bring up a list of possible matches")))

        if root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)
        course_id = S3ReusableField("course_id", table,
                                    sortby = "name",
                                    label = T("Course"),
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "hrm_course.id",
                                                          self.hrm_course_represent,
                                                          filterby="organisation_id",
                                                          filter_opts=filter_opts)),
                                    represent = self.hrm_course_represent,
                                    comment = course_help,
                                    ondelete = "RESTRICT",
                                    # Comment this to use a Dropdown & not an Autocomplete
                                    #widget = S3AutocompleteWidget("hrm",
                                    #                              "course")
                                )

        configure("hrm_course",
                  create_next=URL(f="course", args=["[id]", "course_certificate"]),
                  deduplicate=self.hrm_course_duplicate)

        # Components
        add_component("hrm_course_certificate", hrm_course="course_id")

        # =========================================================================
        # Training Events
        #
        tablename = "hrm_training_event"
        table = define_table(tablename,
                             course_id(empty=False),
                             self.super_link("site_id", "org_site",
                                             label=settings.get_org_site_label(),
                                             instance_types = auth.org_site_types,
                                             updateable = True,
                                             not_filterby = "obsolete",
                                             not_filter_opts = [True],
                                             default = auth.user.site_id if auth.is_logged_in() else None,
                                             readable = True,
                                             writable = True,
                                             empty = False,
                                             represent = self.org_site_represent,
                                             ),
                             Field("start_date", "datetime",
                                   widget = S3DateWidget(),
                                   requires = IS_DATE(format=s3_date_format),
                                   represent = s3_date_represent,
                                   label=T("Start Date")),
                             Field("end_date", "datetime",
                                   widget = S3DateWidget(),
                                   requires = IS_EMPTY_OR(IS_DATE(format=s3_date_format)),
                                   represent = s3_date_represent,
                                   label=T("End Date")),
                             Field("hours", "integer",
                                   requires=IS_INT_IN_RANGE(1, 1000),
                                   label=T("Hours")),
                             # human_resource_id?
                             Field("instructor",
                                   label=T("Instructor"),
                                   represent = s3_string_represent),
                             s3_comments(),
                             *s3_meta_fields())

        # Field Options
        table.site_id.readable = True
        table.site_id.writable = True

        crud_strings[tablename] = Storage(
            title_create = T("Add Training Event"),
            title_display = T("Training Event Details"),
            title_list = T("Training Events"),
            title_update = T("Edit Training Event"),
            title_search = T("Search Training Events"),
            title_upload = T("Import Training Events"),
            subtitle_create = T("Add Training Event"),
            label_list_button = T("List Training Events"),
            label_create_button = T("Add New Training Event"),
            label_delete_button = T("Delete Training Event"),
            msg_record_created = T("Training Event added"),
            msg_record_modified = T("Training Event updated"),
            msg_record_deleted = T("Training Event deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no training events registered"))

        if s3_has_role(ADMIN):
            label_create = crud_strings[tablename].label_create_button
            course_help = S3AddResourceLink(f="training_event",
                                            label=label_create)
        else:
            course_help = DIV(_class="tooltip",
                              _title="%s|%s" % (T("Training Event"),
                              T("Enter some characters to bring up a list of possible matches")))

        training_event_search = S3Search(
            advanced=(
                      S3SearchSimpleWidget(
                        name = "training_event_search_simple",
                        label = T("Text"),
                        comment = T("You can search by course name, venue name or event comments. You may use % as wildcard. Press 'Search' without input to list all events."),
                        field = ["course_id$name",
                                 "site_id$name",
                                 "comments",
                                ]
                    ),
                    # S3SearchOptionsWidget(
                      # name="training_event_search_L1",
                      # field="site_id$L1",
                      # cols = 3,
                    # ),
                    # S3SearchOptionsWidget(
                      # name="training_event_search_L2",
                      # field="site_id$L2",
                      # cols = 3,
                    # ),
                    S3SearchLocationWidget(
                      name="training_event_search_map",
                      label=T("Map"),
                    ),
                    S3SearchOptionsWidget(
                      name="training_event_search_site",
                      label=T("Facility"),
                      field="site_id"
                    ),
                    S3SearchMinMaxWidget(
                      name="training_event_search_date",
                      method="range",
                      label=T("Date"),
                      field="start_date"
                    ),
            ))

        # Resource Configuration
        configure(tablename,
                  create_next = URL(f="training_event",
                                    args=["[id]", "participant"]),
                  search_method=training_event_search,
                  deduplicate=self.hrm_training_event_duplicate
                )

        # Participants of events
        add_component("pr_person",
                      hrm_training_event=Storage(
                                name="participant",
                                link="hrm_training",
                                joinby="training_event_id",
                                key="person_id",
                                actuate="hide"))

        # =====================================================================
        # Training Participations
        #
        # These are an element of credentials:
        # - a minimum number of hours of training need to be done each year
        #
        # Users can add their own but these are confirmed only by specific roles
        #

        participant_id_comment = self.pr_person_comment(
                                    T("Participant"),
                                    T("Type the first few characters of one of the Participant's names."),
                                    child="person_id")
        tablename = "hrm_training"
        table = define_table(tablename,
                             #@ToDo: Create a way to add new people to training as staff/volunteers
                             person_id(empty=False,
                                       comment = participant_id_comment,
                                ),
                             # Just used when created from participation in an Event
                             Field("training_event_id", db.hrm_training_event,
                                   readable = False,
                                   writable = False),
                             course_id(),
                             Field("date", "datetime",
                                   label=T("Date"),
                                   widget = S3DateWidget(),
                                   requires = IS_EMPTY_OR(IS_DATE(format=s3_date_format)),
                                   represent = s3_date_represent
                                   ),
                             Field("hours", "integer",
                                   label=T("Hours")),
                             # This field can only be filled-out by specific roles
                             # Once this has been filled-out then the other fields are locked
                             Field("grade", "integer",
                                   label = T("Grade"),
                                   requires = IS_IN_SET(hrm_pass_fail_opts,  # Default to pass/fail (can override to 5-levels in Controller)
                                                        zero=None),
                                   represent = lambda opt: \
                                       hrm_performance_opts.get(opt,
                                                                NONE),
                                   readable=False,
                                   writable=False
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # Suitable for use when adding a Training to a Person
        # The ones when adding a Participant to an Event are done in the Controller
        crud_strings[tablename] = Storage(
            title_create = T("Add Training"),
            title_display = T("Training Details"),
            title_list = T("Trainings"),
            title_update = T("Edit Training"),
            title_search = T("Search Training Participants"),
            title_report = T("Training Report"),
            title_upload = T("Import Training Participants"),
            subtitle_create = T("Add Training"),
            label_list_button = T("List Trainings"),
            label_create_button = T("Add New Training"),
            label_delete_button = T("Delete Training"),
            msg_record_created = T("Training added"),
            msg_record_modified = T("Training updated"),
            msg_record_deleted = T("Training deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Trainings registered"))

        table.virtualfields.append(HRMTrainingVirtualFields())

        training_search = S3Search(
            advanced=(
                      S3SearchSimpleWidget(
                        name = "training_search_simple",
                        label = T("Text"),
                        comment = T("You can search by trainee name, course name or comments. You may use % as wildcard. Press 'Search' without input to list all trainees."),
                        field = ["person_id$first_name",
                                 "person_id$last_name",
                                 "course_id$name",
                                 "comments",
                                ]
                    ),
                    S3SearchOptionsWidget(
                      name="training_search_course",
                      label=T("Course"),
                      field="course_id"
                    ),
                    S3SearchOptionsWidget(
                      name="training_search_L1",
                      field="person_id$L1",
                      location_level="L1",
                      cols = 3,
                    ),
                    S3SearchOptionsWidget(
                      name="training_search_L2",
                      field="person_id$L2",
                      location_level="L2",
                      cols = 3,
                    ),
                    # Needs options lookup function for virtual field
                    #S3SearchOptionsWidget(
                    #    name="training_search_organisation",
                    #    label=ORGANISATION,
                    #    field="organisation"
                    #),
                    # Needs a Virtual Field
                    # S3SearchOptionsWidget(
                      # name="training_search_site",
                      # label=T("Participant's Office"),
                      # field="person_id$site_id"
                    # ),
                    S3SearchOptionsWidget(
                        name="training_search_site",
                        label=T("Training Facility"),
                        field="training_event_id$site_id",
                        represent = self.org_site_represent,
                        cols = 2
                      ),
                    S3SearchMinMaxWidget(
                      name="training_search_date",
                      method="range",
                      label=T("Date"),
                      field="date"
                    ),
            ))

        report_fields = [
                         "training_event_id",
                         "person_id",
                         "course_id",
                         (messages.ORGANISATION, "organisation"),
                         (T("Facility"), "training_event_id$site_id"),
                         (T("Month"), "month"),
                         "person_id$L1",
                         "person_id$L2",
                         ]

        # Resource Configuration
        configure(tablename,
                  onaccept=self.hrm_training_onaccept,
                  ondelete=self.hrm_training_onaccept,
                  search_method=training_search,
                  deduplicate=self.hrm_training_duplicate,
                  report_options=Storage(
                      search=[
                        S3SearchOptionsWidget(
                            name="training_search_L1",
                            field="person_id$L1",
                            location_level="L1",
                            cols = 3,
                        ),
                        S3SearchOptionsWidget(
                            name="training_search_L2",
                            field="person_id$L2",
                            location_level="L2",
                            cols = 3,
                        ),
                        S3SearchOptionsWidget(
                            name="training_search_site",
                            field="training_event_id$site_id",
                            label = T("Facility"),
                            cols = 3,
                        ),
                        S3SearchMinMaxWidget(
                            name="training_search_date",
                            method="range",
                            label=T("Date"),
                            field="start_date"
                        ),
                      ],
                      rows=report_fields,
                      cols=report_fields,
                      facts=report_fields,
                      methods=["count", "list"],
                      defaults=Storage(rows="training.course_id",
                                      cols="training.month",
                                      fact="training.person_id",
                                      aggregate="count"),
                  ),
                  list_fields = [
                        "course_id",
                        "date",
                        "hours",
                    ]
        )

        # =====================================================================
        # Certificates
        #
        # NB Some Orgs will only trust the certificates of some Orgs
        # - we currently make no attempt to manage this trust chain
        #

        tablename = "hrm_certificate"
        table = define_table(tablename,
                             Field("name", notnull=True,
                                   length=128,   # Mayon Compatibility
                                   label=T("Name")),
                             organisation_id(widget = S3OrganisationAutocompleteWidget(
                                                        default_from_profile=True),
                                             label=T("Certifying Organization")),
                             Field("expiry", "integer",
                                   label = T("Expiry (months)")),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Certificate"),
            title_display = T("Certificate Details"),
            title_list = T("Certificate Catalog"),
            title_update = T("Edit Certificate"),
            title_search = T("Search Certificates"),
            title_upload = T("Import Certificates"),
            subtitle_create = T("Add Certificate"),
            label_list_button = T("List Certificates"),
            label_create_button = T("Add New Certificate"),
            label_delete_button = T("Delete Certificate"),
            msg_record_created = T("Certificate added"),
            msg_record_modified = T("Certificate updated"),
            msg_record_deleted = T("Certificate deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no entries in the catalog"))

        label_create = crud_strings[tablename].label_create_button
        certificate_id = S3ReusableField("certificate_id", table,
                                         sortby = "name",
                                         label = T("Certificate"),
                                         requires = IS_NULL_OR(
                                                        IS_ONE_OF(db,
                                                                  "hrm_certificate.id",
                                                                  self.hrm_certificate_represent)),
                                         represent = self.hrm_certificate_represent,
                                         comment=S3AddResourceLink(f="certificate",
                                                                   label=label_create,
                                                                   title=label_create,
                                                                   tooltip=T("Add a new certificate to the catalog.")),
                                         ondelete = "RESTRICT")

        configure("hrm_certificate",
                  create_next=URL(f="certificate", args=["[id]", "certificate_skill"]),
                  deduplicate=self.hrm_certificate_duplicate)

        # Components
        add_component("hrm_certificate_skill", hrm_certificate="certificate_id")

        # =====================================================================
        # Certifications
        #
        # Link table between Persons & Certificates
        #
        # These are an element of credentials
        #

        tablename = "hrm_certification"
        table = define_table(tablename,
                             person_id(),
                             certificate_id(),
                             Field("number", label=T("License Number")),
                             #Field("status", label=T("Status")),
                             s3_date(label=T("Expiry Date")),
                             Field("image", "upload", label=T("Scanned Copy")),
                             # This field can only be filled-out by specific roles
                             # Once this has been filled-out then the other fields are locked
                             organisation_id(label = T("Confirming Organization"),
                                             widget = S3OrganisationAutocompleteWidget(
                                                        default_from_profile=True),
                                             comment = None,
                                             writable = False),
                             Field("from_training", "boolean",
                                   default=False,
                                   readable=False,
                                   writable=False),
                             s3_comments(),
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=self.hrm_certification_onaccept,
                  ondelete=self.hrm_certification_onaccept,
                  list_fields = ["id",
                                 "certificate_id",
                                 "date",
                                 "comments",
                                ])

        crud_strings[tablename] = Storage(
            title_create = T("Add Certification"),
            title_display = T("Certification Details"),
            title_list = T("Certifications"),
            title_update = T("Edit Certification"),
            title_search = T("Search Certifications"),
            subtitle_create = T("Add Certification"),
            label_list_button = T("List Certifications"),
            label_create_button = T("Add New Certification"),
            label_delete_button = T("Delete Certification"),
            msg_record_created = T("Certification added"),
            msg_record_modified = T("Certification updated"),
            msg_record_deleted = T("Certification deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Certifications registered"))

        # =====================================================================
        # Skill Equivalence
        #
        # Link table between Certificates & Skills
        #
        # Used to auto-populate the relevant skills
        # - faster than runtime joins at a cost of data integrity
        #

        tablename = "hrm_certificate_skill"
        table = define_table(tablename,
                             certificate_id(),
                             skill_id(),
                             competency_id(),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Skill Equivalence"),
            title_display = T("Skill Equivalence Details"),
            title_list = T("Skill Equivalences"),
            title_update = T("Edit Skill Equivalence"),
            title_search = T("Search Skill Equivalences"),
            subtitle_create = T("Add Skill Equivalence"),
            label_list_button = T("List Skill Equivalences"),
            label_create_button = T("Add New Skill Equivalence"),
            label_delete_button = T("Delete Skill Equivalence"),
            msg_record_created = T("Skill Equivalence added"),
            msg_record_modified = T("Skill Equivalence updated"),
            msg_record_deleted = T("Skill Equivalence deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Skill Equivalences registered"))

        # =====================================================================
        # Course Certificates
        #
        # Link table between Courses & Certificates
        #
        # Used to auto-populate the relevant certificates
        # - faster than runtime joins at a cost of data integrity
        #

        tablename = "hrm_course_certificate"
        table = define_table(tablename,
                             course_id(),
                             certificate_id(),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Course Certificate"),
            title_display = T("Course Certificate Details"),
            title_list = T("Course Certificates"),
            title_update = T("Edit Course Certificate"),
            title_search = T("Search Course Certificates"),
            subtitle_create = T("Add Course Certificate"),
            label_list_button = T("List Course Certificates"),
            label_create_button = T("Add New Course Certificate"),
            label_delete_button = T("Delete Course Certificate"),
            msg_record_created = T("Course Certificate added"),
            msg_record_modified = T("Course Certificate updated"),
            msg_record_deleted = T("Course Certificate deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Course Certificates registered"))

        # ---------------------------------------------------------------------
        # Pass model-global names to s3db.*
        #
        return Storage(
                    hrm_skill_id = skill_id,
                    hrm_multi_skill_id = multi_skill_id,
                    hrm_certification_onaccept = self.hrm_certification_onaccept,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def skill_type_default():
        """ Lookup the default skill_type """

        if current.deployment_settings.get_hrm_skill_types():
            # We have many - don't set a default
            default = None
        else:
            # We don't use skill_types so find the default
            db = current.db
            table = db.hrm_skill_type
            skill_type = db(table.deleted == False).select(table.id,
                                                           limitby=(0, 1),
                                                           cache=current.s3db.cache).first()
            try:
                default = skill_type.id
            except:
                # Create a default skill_type
                default = table.insert(name="Default")

        return default

    # -------------------------------------------------------------------------
    @staticmethod
    def competency_rating_comment():
        """ Define the comment for the HRM Competency Rating widget """

        T = current.T
        s3 = current.response.s3

        if current.auth.s3_has_role(current.session.s3.system_roles.ADMIN):
            label_create = s3.crud_strings["hrm_competency_rating"].label_create_button
            comment = S3AddResourceLink(c="hrm",
                                        f="competency_rating",
                                        label=label_create,
                                        tooltip=T("Add a new competency rating to the catalog."))
        else:
            comment = DIV(_class="tooltip",
                          _title="%s|%s" % (T("Competency Rating"),
                                            T("Level of competency this person has with this skill.")))
        if current.deployment_settings.get_hrm_skill_types():
            s3.js_global.append("S3.i18n.no_ratings = '%s';" % T("No Ratings for Skill Type"))
            s3.jquery_ready.append(
'''S3FilterFieldChange({
 'FilterField':'skill_id',
 'Field':'competency_id',
 'FieldResource':'competency',
 'FieldPrefix':'hrm',
 'url':S3.Ap.concat('/hrm/skill_competencies/'),
 'msgNoRecords':S3.i18n.no_ratings
})''')
        return comment

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_competency_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same person_id and skill_id
        """

        if job.tablename == "hrm_competency":
            data = job.data
            person = "person_id" in data and data.person_id
            skill = "skill_id" in data and data.skill_id
            table = job.table
            query = (table.person_id == person) & \
                    (table.skill_id == skill)

            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_certificate_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        if job.tablename == "hrm_certificate":
            data = job.data
            name = "name" in data and data.name

            table = job.table
            query = (table.name.lower() == name.lower())
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_certificate_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.hrm_certificate
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_certification_onaccept(record):
        """
            Ensure that Skills are Populated from Certifications
            - called both onaccept & ondelete
        """

        # Deletion and update have a different format
        try:
            id = record.vars.id
        except:
            id = record.id

        db = current.db
        table = db.hrm_certification
        data = table(table.id == id)

        try:
            if data.deleted:
                deleted_fk = json.loads(record.deleted_fk)
                person_id = deleted_fk["person_id"]
            else:
                person_id = data["person_id"]
        except:
            return

        ctable = db.hrm_competency
        cstable = db.hrm_certificate_skill

        # Drop all existing competencies which came from certification
        # - this is a lot easier than selective deletion.
        query = (ctable.person_id == person_id) & \
                (ctable.from_certification == True)
        db(query).delete()

        # Figure out which competencies we're _supposed_ to have.
        query = (table.person_id == person_id) & \
                (table.certificate_id == cstable.certificate_id) & \
                (cstable.skill_id == db.hrm_skill.id)
        certifications = db(query).select()

        # Add these competencies back in.
        for certification in certifications:
            skill = certification["hrm_skill"]
            cert = certification["hrm_certificate_skill"]

            query = (ctable.person_id == person_id) & \
                    (ctable.skill_id == skill.id)
            existing = db(query).select()

            better = True
            for e in existing:
                if e.competency_id.priority > cert.competency_id.priority:
                    db(ctable.id == e.id).delete()
                else:
                    better = False
                    break

            if better:
                ctable.update_or_insert(
                    person_id=person_id,
                    competency_id=cert.competency_id,
                    skill_id=skill.id,
                    comments="Added by certification",
                    from_certification = True
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_competency_rating_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case and skill_type
        """

        if job.tablename == "hrm_competency_rating":
            data = job.data
            name = "name" in data and data.name
            skill = False
            for cjob in job.components:
                if cjob.tablename == "hrm_skill_type":
                    cdata = cjob.data
                    if "name" in cdata:
                        skill = cdata.name
            if skill == False:
                return

            table = job.table
            stable = current.s3db.hrm_skill_type
            query = (table.name.lower() == name.lower()) & \
                    (table.skill_type_id == stable.id) & \
                    (stable.value.lower() == skill.lower())
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_competency_rating_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.hrm_competency_rating
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_course_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        if job.tablename == "hrm_course":
            data = job.data
            name = "name" in data and data.name

            table = job.table
            query = (table.name.lower() == name.lower())
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_course_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.hrm_course
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_skill_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        if job.tablename == "hrm_skill":
            data = job.data
            name = "name" in data and data.name

            table = job.table
            query = (table.name.lower() == name.lower())
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_skill_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.hrm_skill
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_skill_type_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        if job.tablename == "hrm_skill_type":
            data = job.data
            name = "name" in data and data.name

            table = job.table
            query = (table.name.lower() == name.lower())
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_skill_type_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.hrm_skill_type
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_training_event_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same course name & date (& site, if-present)
        """

        if job.tablename == "hrm_training_event":
            data = job.data
            start_date = "start_date" in data and data.start_date
            if not start_date:
                return
            course_id = "course_id" in data and data.course_id
            site_id = "site_id" in data and data.site_id
            # Need to provide a range of dates as otherwise second differences prevent matches
            # - assume that if we have multiple training courses of the same
            #   type at the same site then they start at least a minute apart
            #
            # @ToDo: refactor into a reusable function
            year = start_date.year
            month = start_date.month
            day = start_date.day
            hour = start_date.hour
            minute = start_date.minute
            start_start_date = datetime.datetime(year, month, day, hour, minute)
            if minute < 58:
                minute = minute + 1
            elif hour < 23:
                hour = hour + 1
                minute = 0
            elif (day == 28 and month == 2) or \
                 (day == 30 and month in [4, 6, 9, 11]) or \
                 (day == 31 and month in [1, 3, 5, 7, 8, 10, 12]):
                month = month + 1
                day = 1
                hour = 0
                minute = 0
            else:
                day = day + 1
                hour = 0
                minute = 0
            start_end_date = datetime.datetime(year, month, day, hour, minute)

            table = job.table
            query = (table.course_id == course_id) & \
                    (table.start_date >= start_start_date) & \
                    (table.start_date < start_end_date)
            if site_id:
                query = query & (table.site_id == site_id)
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_training_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same person, date & course
        """

        if job.tablename == "hrm_training":
            data = job.data
            person_id = "person_id" in data and data.person_id
            course_id = "course_id" in data and data.course_id
            date = "date" in data and data.date

            table = job.table
            query = (table.person_id == person_id) & \
                    (table.course_id == course_id)
            if date:
                query = query & (table.date == date)
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_training_onaccept(form):
        """
            Ensure that Certifications & Hours are Populated from Trainings
            - called both onaccept & ondelete
        """

        # Deletion and update have a different format
        try:
            id = form.vars.id
            delete = False
        except:
            id = form.id
            delete = True

        # Get the full record
        db = current.db
        table = db.hrm_training
        record = db(table.id == id).select(table.person_id,
                                           table.course_id,
                                           table.date,
                                           table.hours,
                                           table.deleted_fk,
                                           limitby=(0, 1)).first()

        if delete:
            deleted_fks = json.loads(record.deleted_fk)
            person_id = deleted_fks["person_id"]
        else:
            person_id = record.person_id

        s3db = current.s3db
        if current.deployment_settings.get_hrm_vol_experience() == "programme":
            # Check if this person is a volunteer
            hrtable = db.hrm_human_resource
            query = (hrtable.person_id == person_id) & \
                    (hrtable.deleted == False)
            vol = db(query).select(hrtable.type,
                                   limitby=(0, 1)).first()

            if vol and vol.type == 2:
                 # Update Hours
                ptable = s3db.hrm_programme_hours
                date = record.date
                hours = record.hours
                if delete:
                    query = (ptable.person_id == person_id) & \
                            (ptable.date == date) & \
                            (ptable.hours == hours) & \
                            (ptable.training == True)
                    db(query).update(deleted=True)
                else:
                    ptable.insert(person_id = person_id,
                                  date = date,
                                  hours = hours,
                                  training = True)

        # Update Certifications
        ctable = db.hrm_certification
        cctable = db.hrm_course_certificate

        # Drop all existing certifications which came from trainings
        # - this is a lot easier than selective deletion.
        query = (ctable.person_id == person_id) & \
                (ctable.from_training == True)
        db(query).delete()

        # Figure out which certifications we're _supposed_ to have.
        query = (table.person_id == person_id) & \
                (table.course_id == cctable.course_id) & \
                (cctable.certificate_id == db.hrm_certificate.id)
        trainings = db(query).select()

        # Add these certifications back in.
        hrm_certification_onaccept = s3db.hrm_certification_onaccept
        form = Storage()
        form.vars = Storage()
        vars = form.vars
        for training in trainings:
            id = ctable.update_or_insert(
                    person_id=person_id,
                    certificate_id=training["hrm_certificate"].id,
                    comments="Added by training",
                    from_training=True
                )
            # Propagate to Skills
            vars.id = id
            hrm_certification_onaccept(form)

# =============================================================================
class S3HRExperienceModel(S3Model):
    """
        Record a person's work experience
    """

    names = ["hrm_experience",
             ]

    def model(self):

        T = current.T

        # =====================================================================
        # Professional Experience (Mission Record)
        #
        # These are an element of credentials:
        # - a minimum number of hours of active duty need to be done
        #   (e.g. every 6 months for Portuguese Bombeiros)
        #
        # This should be auto-populated out of Events
        # - as well as being updateable manually for off-system Events
        #

        tablename = "hrm_experience"
        table = self.define_table(tablename,
                                  self.pr_person_id(),
                                  self.org_organisation_id(
                                    widget = S3OrganisationAutocompleteWidget(
                                                default_from_profile=True)
                                    ),
                                  self.hrm_job_title_id(),
                                  s3_date("start_date",
                                          label=T("Start Date"),
                                          ),
                                  s3_date("end_date",
                                          label=T("End Date"),
                                          ),
                                  Field("hours", "double",
                                        label=T("Hours")),
                                  Field("place",              # We could make this an event_id?
                                        label=T("Place")),
                                  s3_comments(comment=None),
                                  *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Add Professional Experience"),
            title_display = T("Professional Experience Details"),
            title_list = T("Professional Experience"),
            title_update = T("Edit Professional Experience"),
            title_search = T("Search Professional Experience"),
            subtitle_create = T("Add Professional Experience"),
            label_list_button = T("List of Professional Experience"),
            label_create_button = T("Add New Professional Experience"),
            label_delete_button = T("Delete Professional Experience"),
            msg_record_created = T("Professional Experience added"),
            msg_record_modified = T("Professional Experience updated"),
            msg_record_deleted = T("Professional Experience deleted"),
            msg_no_match = T("No Professional Experience found"),
            msg_list_empty = T("Currently no Professional Experience entered"))

        # ---------------------------------------------------------------------
        # Pass model-global names to s3db.*
        #
        return Storage(
                )

# =============================================================================
class S3HRProgrammeModel(S3Model):
    """
        Record Volunteer Hours on Programmes
        - initially at least this doesn't link to the Project module
    """

    names = ["hrm_programme",
             "hrm_programme_hours",
             "hrm_programme_virtual_fields",
             "hrm_programme_person_virtual_fields",
             ]

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        root_org = current.auth.root_org()

        # =========================================================================
        # Progammes
        # - not sure yet whether this will map to 'Project' or 'Activity' in future
        #

        tablename = "hrm_programme"
        table = define_table(tablename,
                             Field("name", notnull=True, length=64,
                                   label=T("Name")),
                             # Only included in order to be able to set
                             # realm_entity to filter appropriately
                             self.org_organisation_id(
                                             default = root_org,
                                             readable = False,
                                             writable = False,
                                             ),
                             s3_comments(label=T("Description"),
                                         comment=None),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Programme"),
            title_display = T("Programme Details"),
            title_list = T("Programmes"),
            title_update = T("Edit Programme"),
            title_search = T("Search Programmes"),
            subtitle_create = T("Add Programme"),
            label_list_button = T("List Programmes"),
            label_create_button = T("Add New Programme"),
            label_delete_button = T("Delete Programme"),
            msg_record_created = T("Programme added"),
            msg_record_modified = T("Programme updated"),
            msg_record_deleted = T("Programme deleted"),
            msg_list_empty = T("Currently no programmes registered"))

        label_create = crud_strings[tablename].label_create_button
        if root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)
        programme_id = S3ReusableField("programme_id", table,
                                sortby = "name",
                                label = T("Programme"),
                                requires = IS_NULL_OR(
                                            IS_ONE_OF(db, "hrm_programme.id",
                                                      self.hrm_programme_represent,
                                                      filterby="organisation_id",
                                                      filter_opts=filter_opts)),
                                represent = self.hrm_programme_represent,
                                comment=S3AddResourceLink(f="programme",
                                                          label=label_create,
                                                          title=label_create,
                                                          tooltip=T("Add a new programme to the catalog.")),
                                ondelete = "SET NULL")

        self.add_component("hrm_programme_hours", hrm_programme=Storage(
                                                    name="person",
                                                    joinby="programme_id"))

        # =========================================================================
        # Link Table between Programmes & Persons
        #

        tablename = "hrm_programme_hours"
        table = define_table(tablename,
                             self.pr_person_id(
                               represent = lambda id: \
                                   self.pr_person_represent(id, show_link=True)
                               ),
                             programme_id(),
                             s3_date(future=0),
                             Field("hours", "double",
                                   label=T("Hours")),
                             # Training records are auto-populated
                             Field("training", "boolean",
                                   label = T("Type"),
                                   default=False,
                                   represent = lambda opt: \
                                        T("Training") if opt else T("Work"),
                                   readable=False,
                                   writable=False),
                             s3_comments(comment=None),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Hours"),
            title_display = T("Hours Details"),
            title_list = T("Hours"),
            title_update = T("Edit Hours"),
            title_search = T("Search Hours"),
            title_upload = T("Import Hours"),
            subtitle_create = T("Add Hours"),
            label_list_button = T("List Hours"),
            label_create_button = T("Add New Hours"),
            label_delete_button = T("Delete Hours"),
            msg_record_created = T("Hours added"),
            msg_record_modified = T("Hours updated"),
            msg_record_deleted = T("Hours deleted"),
            msg_list_empty = T("Currently no hours recorded for this volunteer"))

        self.configure(tablename,
                        list_fields=["id",
                                     "training",
                                     "programme_id",
                                     "date",
                                     "hours",
                                     ]
                        )

        # ---------------------------------------------------------------------
        # Pass model-global names to s3db.*
        #
        return Storage(
                    hrm_programme_virtual_fields = HRMProgrammeVirtualFields,
                    hrm_programme_person_virtual_fields = HRMProgrammePersonVirtualFields,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_programme_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.hrm_programme
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

# =============================================================================
def hrm_vars():
    """ Set session and response variables """

    auth = current.auth
    if not auth.is_logged_in():
        # No access to HRM for unauthenticated users
        auth.permission.fail()

    s3db = current.s3db
    session = current.session

    if session.s3.hrm is None:
        session.s3.hrm = Storage()
    hrm_vars = session.s3.hrm

    # Automatically choose an organisation
    if "orgs" not in hrm_vars:
        # Find all organisations the current user is a staff
        # member of (+all their branches)
        user = auth.user.pe_id
        branches = s3db.pr_get_role_branches(user,
                                             roles="Staff",
                                             entity_type="org_organisation")
        otable = s3db.org_organisation
        query = (otable.pe_id.belongs(branches))
        orgs = current.db(query).select(otable.id)
        orgs = [org.id for org in orgs]
        if orgs:
            hrm_vars.orgs = orgs
        else:
            hrm_vars.orgs = None

    # Set mode
    hrm_vars.mode = current.request.vars.get("mode", None)
    if hrm_vars.mode != "personal":
        sr = session.s3.system_roles
        if sr.ADMIN in session.s3.roles or \
           hrm_vars.orgs or \
           current.deployment_settings.get_security_policy() in (1, 2):
            hrm_vars.mode = None
    else:
        hrm_vars.mode = "personal"
    return

# =============================================================================
def hrm_hr_represent(id):
    """ Simple representation of HRs """

    if not id:
        return current.messages.NONE

    s3db = current.s3db
    htable = s3db.hrm_human_resource
    ptable = s3db.pr_person

    query = (htable.id == id) & \
            (ptable.id == htable.person_id)
    person = current.db(query).select(ptable.first_name,
                                      ptable.middle_name,
                                      ptable.last_name,
                                      limitby=(0, 1)).first()
    if person:
        return s3_fullname(person)
    else:
        return current.messages.UNKNOWN_OPT

# -------------------------------------------------------------------------
def hrm_human_resource_represent(id, show_link=False):
    """ Representation of human resource records """

    if not id:
        return current.messages.NONE

    s3db = current.s3db
    htable = s3db.hrm_human_resource
    ptable = s3db.pr_person

    query = (htable.id == id) & \
            (htable.person_id == ptable.id)
    row = current.db(query).select(htable.job_title_id,
                                   htable.organisation_id,
                                   htable.type,
                                   ptable.first_name,
                                   ptable.middle_name,
                                   ptable.last_name,
                                   limitby=(0, 1)).first()

    try:
        hr = row["hrm_human_resource"]
    except:
        return current.messages.UNKNOWN_OPT

    repr = ""
    if hr.organisation_id and \
       current.deployment_settings.get_hrm_show_organisation():
        repr = ", %s" % s3db.org_organisation_represent(hr.organisation_id)
    if hr.job_title_id:
        repr = ", %s%s" % (hrm_job_title_represent(hr.job_title_id), repr)
    person = row["pr_person"]
    repr = "%s%s" % (s3_fullname(person), repr)
    if show_link:
        if hr.type == 1:
            controller = "hrm"
            function = "staff"
        else:
            controller = "vol"
            function = "volunteer"
        current.request.extension = "html"
        return A(repr,
                 _href = URL(c = controller,
                             f = function,
                             args = [id]
                             )
                 )
    return repr

# =============================================================================
def hrm_job_title_represent(id, row=None):
    """ FK representation """

    if row:
        return row.name
    elif not id:
        return current.messages.NONE

    table = current.s3db.hrm_job_title
    r = current.db(table.id == id).select(table.name,
                                          limitby = (0, 1)).first()
    try:
        return r.name
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def hrm_department_represent(id, row=None):
    """ FK representation """

    if row:
        return row.name
    elif not id:
        return current.messages.NONE

    db = current.db
    table = db.hrm_department
    r = db(table.id == id).select(table.name,
                                  limitby=(0, 1)).first()
    try:
        return r.name
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def hrm_job_role_represent(id, row=None):
    """ FK representation """

    if row:
        return row.name
    elif not id:
        return current.messages.NONE

    db = current.db
    table = db.hrm_job_role
    r = db(table.id == id).select(table.name,
                                  limitby=(0, 1)).first()
    try:
        return r.name
    except:
        return current.messages.UNKNOWN_OPT

# -----------------------------------------------------------------------------
def hrm_job_role_multirepresent(opt):
    """
        Job Role representation
        for multiple=True options
    """

    table = current.s3db.hrm_job_role
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
def hrm_job_title_represent(id, row=None):
    """ FK representation """

    if row:
        return row.name
    elif not id:
        return current.messages.NONE

    db = current.db
    table = db.hrm_job_title
    r = db(table.id == id).select(table.name,
                                  limitby=(0, 1)).first()
    try:
        return r.name
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def hrm_skill_multirepresent(opt):
    """
        Skill representation
        for multiple=True options
    """

    table = current.s3db.hrm_skill
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
def hrm_training_event_represent(id, row=None):
    """ Represent a Training Event """

    if not id:
        return current.messages.NONE

    s3db = current.s3db
    table = s3db.hrm_training_event
    ctable = s3db.hrm_course
    stable = s3db.org_site
    query = (table.id == id) & \
            (table.course_id == ctable.id)
    left = table.on(table.site_id == stable.site_id)
    event = current.db(query).select(ctable.name,
                                     ctable.code,
                                     stable.name,
                                     table.start_date,
                                     table.instructor,
                                     left = left,
                                     limitby = (0, 1)).first()
    try:
        represent = event.hrm_course.name
    except:
        return current.messages.UNKNOWN_OPT

    if event.hrm_course.code:
        represent = "%s (%s)" % (represent, event.hrm_course.code)
    instructor = event.hrm_training_event.instructor
    site = event.org_site.name
    if instructor and site:
        represent = "%s (%s - %s)" % (represent, instructor, site)
    elif instructor:
        represent = "%s (%s)" % (represent, instructor)
    elif site:
        represent = "%s (%s)" % (represent, site)
    start_date = event.hrm_training_event.start_date
    if start_date:
        start_date = table.start_date.represent(start_date)
        represent = "%s [%s]" % (represent, start_date)

    return represent

# =============================================================================
#def hrm_position_represent(id):
#    """
#    """
#    if not id:
#        return current.messages.NONE
#    db = current.db
#    s3db = current.s3db
#    table = s3db.hrm_position
#    jtable = s3db.hrm_job_title
#    otable = s3db.org_organisation
#    query = (table.id == id) & \
#            (table.job_role_id == jtable.id)
#            (table.organisation_id == otable.id)
#    position = db(query).select(jtable.name,
#                                otable.name,
#                                limitby=(0, 1)).first()
#    try:
#        represent = position.hrm_job_title.name
#        if position.org_organisation:
#            represent = "%s (%s)" % (represent,
#                                     position.org_organisation.name)
#    except:
#        return current.messages.NONE
#    return represent

# =============================================================================
def hrm_human_resource_onaccept(form):
    """ On-accept for HR records """

    if "vars" in form:
        # e.g. coming from staff/create
        vars = form.vars
    elif "id" in form:
        # e.g. coming from user/create or from hrm_site_onaccept
        vars = form
    elif hasattr(form, "vars"):
        # SQLFORM e.g. ?
        vars = form.vars
    else:
        # e.g. Coming from s3_register callback
        vars = form

    id = vars.id
    if not id:
        return

    db = current.db
    s3db = current.s3db
    auth = current.auth

    # Get the full record
    htable = db.hrm_human_resource
    record = db(htable.id == id).select(htable.id,
                                        htable.type,
                                        htable.person_id,
                                        htable.organisation_id,
                                        htable.location_id,
                                        htable.site_id,
                                        htable.site_contact,
                                        htable.status,
                                        htable.deleted,
                                        htable.deleted_fk,
                                        limitby=(0, 1)).first()
    data = Storage()

    site_id = record.site_id
    organisation_id = record.organisation_id

    # Affiliation, record ownership and component ownership
    s3db.pr_update_affiliations(htable, record)

    # Realm_entity for the pr_person record
    ptable = s3db.pr_person
    person_id = record.person_id
    person = Storage(id = person_id)
    if current.deployment_settings.get_auth_person_realm_human_resource_site_then_org():
        # Set pr_person.realm_entity to the human_resource's site pe_id
        entity = s3db.pr_get_pe_id("org_site", site_id) or \
                 s3db.pr_get_pe_id("org_organisation", organisation_id) 
            
        if entity:
            auth.set_realm_entity(ptable, person,
                                  entity = entity,
                                  force_update = True)

    site_contact = record.site_contact
    if record.type == 1:
        # Staff
        # Add/update the record in the link table
        hstable = s3db.hrm_human_resource_site
        query = (hstable.human_resource_id == id)
        if site_id:
            this = db(query).select(hstable.id,
                                    limitby=(0, 1)).first()
            if this:
                db(query).update(site_id=site_id,
                                 human_resource_id=id,
                                 site_contact=site_contact)
            else:
                hstable.insert(site_id=site_id,
                               human_resource_id=id,
                               site_contact=site_contact)
            # Update the location ID from the selected site
            stable = s3db.org_site
            query = (stable._id == site_id)
            site = db(query).select(stable.location_id,
                                    limitby=(0, 1)).first()
            try:
                data.location_id = site.location_id
            except:
                # Site not found?
                pass
        else:
            db(query).delete()
            data["location_id"] = None
    elif record.type == 2:
        # Volunteer: synchronise the location ID with the Home Address
        atable = s3db.pr_address
        query = (atable.pe_id == ptable.pe_id) & \
                (ptable.id == person_id) & \
                (atable.type == 1) & \
                (atable.deleted == False)
        address = db(query).select(atable.location_id,
                                   limitby=(0, 1)).first()
        if address:
            # Use Address to update HRM
            data.location_id = address.location_id
        elif "location_id" in record and record.location_id:
            # Create Address from newly-created HRM
            query = (ptable.id == person_id)
            pe_id = db(query).select(ptable.pe_id,
                                     limitby=(0, 1)).first().pe_id
            record_id = atable.insert(type = 1,
                                      pe_id = pe_id,
                                      location_id = record.location_id)
        # request_vars = None for prepop
        if form.request_vars and "programme_id" in form.request_vars:
            programme_id = form.request_vars.programme_id
            # Have we already got a record for this programme?
            table = s3db.hrm_programme_hours
            query = (table.deleted == False) & \
                    (table.person_id == person_id)
            existing = db(query).select(table.programme_id,
                                        orderby=table.date).last()
            if existing and existing.programme_id == programme_id:
                # No action required
                pass
            else:
                # Insert new record
                table.insert(person_id=person_id,
                             date = current.request.utcnow,
                             programme_id=programme_id)

    # Add record owner (user)
    ltable = s3db.pr_person_user
    utable = auth.settings.table_user
    query = (ptable.id == person_id) & \
            (ltable.pe_id == ptable.pe_id) & \
            (utable.id == ltable.user_id)
    user = db(query).select(utable.id,
                            utable.organisation_id,
                            utable.site_id,
                            limitby=(0, 1)).first()
    if user:
        user_id = user.id
        data.owned_by_user = user_id

    if data:
        record.update_record(**data)

        # Populate the Lx fields
        s3_lx_update(ptable, person_id)

    if user and record.organisation_id:
        profile = dict()
        if not user.organisation_id:
            # Set the Organisation in the Profile, if not already set
            profile["organisation_id"] = record.organisation_id
            if not user.site_id:
                # Set the Site in the Profile, if not already set
                profile["site_id"] = site_id
        else:
            # How many active HR records does the user have?
            query = (htable.deleted == False) & \
                    (htable.status == 1) & \
                    (htable.person_id == person_id)
            rows = db(query).select(htable.id,
                                    limitby=(0, 2))
            if len(rows) == 1:
                # We can safely update
                profile["organisation_id"] = record.organisation_id
                profile["site_id"] = record.site_id
        if profile:
            query = (utable.id == user.id)
            db(query).update(**profile)

    # Ensure only one Facility Contact per Facility
    if site_contact and site_id:
        # Set all others in this Facility to not be the Site Contact
        query  = (htable.site_id == site_id) & \
                 (htable.site_contact == True) & \
                 (htable.id != id)
        # Prevent overwriting the person_id field!
        htable.person_id.update = None
        db(query).update(site_contact = False)

# =============================================================================
def hrm_active(person_id):
    """
        Whether a Volunteer counts as 'Active' based on the number of hours
        they've done (both Trainings & Programmes) per month, averaged over
        the last year.
        If nothing recorded for the last 3 months, don't penalise as assume
        that data entry hasn't yet been done.

        @ToDo: deployment_setting for formula (function in template?)
    """

    now = current.request.utcnow

    # Time spent on Programme work
    htable = current.s3db.hrm_programme_hours
    query = (htable.deleted == False) & \
            (htable.person_id == person_id) & \
            (htable.date != None)
    programmes = current.db(query).select(htable.hours,
                                          htable.date,
                                          orderby=htable.date)
    if programmes:
        # Ignore up to 3 months of records
        three_months_prior = (now - datetime.timedelta(days=92))
        end = max(programmes.last().date, three_months_prior.date())
        last_year = end - datetime.timedelta(days=365)
        # Is this the Volunteer's first year?
        if programmes.first().date > last_year:
            # Only start counting from their first month
            start = programmes.first().date
        else:
            #start from a year before the latest record
            start = last_year

        # Total hours between start and end
        programme_hours = 0
        for programme in programmes:
            if programme.date >= start and programme.date <= end and programme.hours:
                programme_hours += programme.hours

        # Average hours per month
        months = max(1, (end - start).days / 30.5)
        average = programme_hours / months

        # Active?
        if average >= 8:
            return True
        else:
            return False
    else:
        return False

# =============================================================================
def hrm_compose():
    """
        Send message to people/teams
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    vars = current.request.vars

    if "hrm_id" in vars:
        id = vars.hrm_id
        fieldname = "hrm_id"
        table = s3db.pr_person
        htable = s3db.hrm_human_resource
        query = (htable.id == id) & \
                (htable.person_id == table.id)
        title = T("Send a message to this person")
    elif "group_id" in vars:
        id = vars.group_id
        fieldname = "group_id"
        table = s3db.pr_group
        query = (table.id == id)
        title = T("Send a message to this team")
    else:
        current.session.error = T("Record not found")
        redirect(URL(f="index"))

    pe = db(query).select(table.pe_id,
                          limitby=(0, 1)).first()
    if not pe:
        current.session.error = T("Record not found")
        redirect(URL(f="index"))

    pe_id = pe.pe_id

    if "hrm_id" in vars:
        # Get the individual's communications options & preference
        ctable = s3db.pr_contact
        contact = db(ctable.pe_id == pe_id).select(ctable.contact_method,
                                                   orderby="priority",
                                                   limitby=(0, 1)).first()
        if contact:
            s3db.msg_outbox.pr_message_method.default = contact.contact_method
        else:
            current.session.error = T("No contact method found")
            redirect(URL(f="index"))

    # URL to redirect to after message sent
    url = URL(f="compose",
              vars={fieldname: id})

    # Create the form
    output = current.msg.compose(recipient = pe_id,
                                 url = url)

    output["title"] = title
    current.response.view = "msg/compose.html"
    return output

# =============================================================================
def hrm_map_popup(r):
    """
        Custom output to place inside a Map Popup
        - called from postp of human_resource controller
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    CONTACT_OPTS = current.msg.CONTACT_OPTS

    output = TABLE()
    append = output.append
    # Edit button
    append(TR(TD(A(T("Edit"),
                   _target="_blank",
                   _id="edit-btn",
                   _href=URL(args=[r.id, "update"])))))

    # First name, last name
    append(TR(TD(B("%s:" % T("Name"))),
              TD(s3_fullname(r.record.person_id))))

    # Job Title
    if r.record.job_title_id:
        append(TR(TD(B("%s:" % r.table.job_title_id.label)),
                  TD(r.table.job_title_id.represent(r.record.job_title_id))))

    # Organization (better with just name rather than Represent)
    # @ToDo: Make this configurable - some deployments will only see
    #        their staff so this is a meaningless field
    #table = s3db.org_organisation
    #query = (table.id == r.record.organisation_id)
    #name = db(query).select(table.name,
    #                        limitby=(0, 1)).first().name
    #append(TR(TD(B("%s:" % r.table.organisation_id.label)),
    #          TD(name)))

    # Components link to the Person record
    person_id = r.record.person_id

    # Skills
    table = s3db.hrm_competency
    stable = s3db.hrm_skill
    query = (table.person_id == person_id) & \
            (table.skill_id == stable.id)
    skills = db(query).select(stable.name)
    if skills:
        vals = [skill.name for skill in skills]
        if len(skills) > 1:
            represent = ", ".join(vals)
        else:
            represent = len(vals) and vals[0] or ""
        append(TR(TD(B("%s:" % T("Skills"))),
                  TD(represent)))

    # Certificates
    table = s3db.hrm_certification
    ctable = s3db.hrm_certificate
    query = (table.person_id == person_id) & \
            (table.certificate_id == ctable.id)
    certificates = db(query).select(ctable.name)
    if certificates:
        vals = [cert.name for cert in certificates]
        if len(certificates) > 1:
            represent = ", ".join(vals)
        else:
            represent = len(vals) and vals[0] or ""
        append(TR(TD(B("%s:" % T("Certificates"))),
                  TD(represent)))

    # Trainings
    table = s3db.hrm_training
    etable = s3db.hrm_training_event
    ctable = s3db.hrm_course
    query = (table.person_id == person_id) & \
            (table.training_event_id == etable.id) & \
            (etable.course_id == ctable.id)
    trainings = db(query).select(ctable.name)
    if trainings:
        vals = [train.name for train in trainings]
        if len(trainings) > 1:
            represent = ", ".join(vals)
        else:
            represent = len(vals) and vals[0] or ""
        append(TR(TD(B("%s:" % T("Trainings"))),
                  TD(represent)))

    if r.record.location_id:
        table = s3db.gis_location
        query = (table.id == r.record.location_id)
        location = db(query).select(table.path,
                                    table.addr_street,
                                    limitby=(0, 1)).first()
        # City
        # Street address
        if location.addr_street:
            append(TR(TD(B("%s:" % table.addr_street.label)),
                      TD(location.addr_street)))
    # Mobile phone number
    ptable = s3db.pr_person
    ctable = s3db.pr_contact
    query = (ptable.id == person_id) & \
            (ctable.pe_id == ptable.pe_id)
    contacts = db(query).select(ctable.contact_method,
                                ctable.value)
    email = mobile_phone = ""
    for contact in contacts:
        if contact.contact_method == "EMAIL":
            email = contact.value
        elif contact.contact_method == "SMS":
            mobile_phone = contact.value
    if mobile_phone:
        append(TR(TD(B("%s:" % CONTACT_OPTS.get("SMS"))),
                  TD(mobile_phone)))
    # Office number
    if r.record.site_id:
        table = s3db.org_office
        query = (table.site_id == r.record.site_id)
        office = db(query).select(table.phone1,
                                  limitby=(0, 1)).first()
        if office and office.phone1:
            append(TR(TD(B("%s:" % T("Office Phone"))),
                      TD(office.phone1)))
        else:
            # @ToDo: Support other Facility Types (Hospitals & Shelters)
            pass
    # Email address (as hyperlink)
    if email:
        append(TR(TD(B("%s:" % CONTACT_OPTS.get("EMAIL"))),
                  TD(A(email, _href="mailto:%s" % email))))

    return output

# =============================================================================
def hrm_service_record(r, **attr):
    """
        Generate a Volunteer Service Record
    """

    def callback(r):
        T = current.T
        db = current.db
        s3db = current.s3db

        if r.record:
            vol = r.record
        else:
            # When would we not have the record?
            vol = table[r.id]
        person_id = vol.person_id
        organisation_id = vol.organisation_id

        # Person details
        table = s3db.hrm_human_resource
        prtable = s3db.pr_person
        org_name = table.organisation_id.represent(organisation_id)
        logo = s3db.org_organisation_logo(organisation_id)
        vol_name = table.person_id.represent(person_id)
        query = (prtable.id == person_id)
        pe_id = db(query).select(prtable.pe_id,
                                 limitby=(0, 1)).first().pe_id

        innerTable = TABLE(TR(TH(T("Volunteer Service Record"))),
                           TR(TD(vol_name)),
                           TR(TD(org_name)))
        person_details = TABLE(TR(TD(logo),
                                  TD(innerTable)
                                  ))

        # Photo
        itable = s3db.pr_image
        query = (itable.pe_id == pe_id) & \
                (itable.profile == True)
        image = db(query).select(itable.image,
                                 limitby=(0, 1)).first()
        if image:
            image = image.image
            size = (160, None)
            image = s3db.pr_image_represent(image, size=size)
            size = s3db.pr_image_size(image, size)
            url = URL(c="default",
                      f="download",
                      args=image)
            avatar = IMG(_src=url,
                         _width=size[0],
                         _height=size[1],
                       )
            person_details[0].append(TD(avatar))

        # Contact Details
        contact_details = DIV()
        # Addresses
        addrtable = s3db.pr_address
        ltable = s3db.gis_location
        query = (addrtable.pe_id == pe_id) & \
                (addrtable.location_id == ltable.id)
        addresses = db(query).select(addrtable.type,
                                     ltable.addr_street,
                                     ltable.L3,
                                     ltable.L2,
                                     ltable.L1,
                                     orderby = addrtable.type,
                                     limitby=(0, 2))
        address_list = []
        for address in addresses:
            _location = address["gis_location"]
            address = TABLE(TR(TH(addrtable.type.represent(address["pr_address"].type))),
                            TR(_location.addr_street),
                            TR(_location.L3),
                            TR(_location.L2),
                            TR(_location.L1),
                            )
            address_list.append(address)

        # Contacts
        ctable = s3db.pr_contact
        query = (ctable.pe_id == pe_id)
        contacts = db(query).select(ctable.contact_method,
                                    ctable.value,
                                    orderby = ctable.priority,
                                    limitby=(0, 3))
        contact_list = TABLE()
        for contact in contacts:
            contact_list.append(TH(ctable.contact_method.represent(contact.contact_method)))
            contact_list.append(contact.value)

        # Emergency Contact
        ectable = s3db.pr_contact_emergency
        query = (ectable.pe_id == pe_id)
        emergency = db(query).select(ectable.name,
                                     ectable.relationship,
                                     ectable.phone,
                                     limitby=(0, 1)).first()
        if emergency:
            econtact = TABLE(TR(TH(T("Emergency Contact"))),
                             TR(emergency.name),
                             TR(emergency.relationship),
                             TR(emergency.phone),
                            )
        else:
            econtact = TABLE()
        contact_row = TR()
        if len(address_list) > 0:
            contact_row.append(TD(address_list[0]))
        if len(address_list) > 1:
            contact_row.append(TD(address_list[1]))
        contact_row.append(contact_list)
        contact_row.append(econtact)

        # Identity
        idtable = s3db.pr_identity
        query = (idtable.person_id == person_id) & \
                (idtable.deleted == False)
        rows = db(query).select(idtable.type,
                                idtable.value,
                                idtable.valid_until)
        id_row = TR()
        for identity in rows:
            id_row.append(TABLE(TR(TH(idtable.type.represent(identity.type))),
                                TR(identity.value),
                                TR(identity.valid_until),
                                )
                          )

        # Programme Hours
        hours = {}
        hrstable = s3db.hrm_programme_hours
        query = (hrstable.person_id == person_id) & \
                (hrstable.deleted == False) & \
                (hrstable.training == False)
        rows = db(query).select(hrstable.programme_id,
                                hrstable.date,
                                hrstable.hours,
                                orderby = ~hrstable.date)
        for row in rows:
            hours[row.date] = dict(
                                programme = hrstable.programme_id.represent(row.programme_id),
                                course = "",
                                date = hrstable.date.represent(row.date),
                                hours = row.hours,
                            )

        # Training Hours
        ttable = s3db.hrm_training
        ctable = s3db.hrm_course
        query = (ttable.person_id == person_id) & \
                (ttable.deleted == False)
        rows = db(query).select(ctable.name,
                                ttable.date,
                                ttable.hours,
                                left=ctable.on(ttable.course_id == ctable.id),
                                orderby = ~ttable.date)
        NONE = current.messages.NONE
        for row in rows:
            _row = row["hrm_training"]
            hours[_row.date.date()] = dict(
                                programme = "",
                                course = row["hrm_course"].name or NONE,
                                date = ttable.date.represent(_row.date),
                                hours = _row.hours,
                            )

        # Combined Hours
        _hours = {}
        hour_list = TABLE(TR(TD(T("Programme")), TD(T("Course")), TD(T("Date")), TD(T("Hours"))))
        for key in sorted(hours.iterkeys()):
            _hours[key] = hours[key]
        total = 0
        for hour in hours:
            hour_list.append(TR(hours[hour]["programme"],
                                hours[hour]["course"],
                                hours[hour]["date"],
                                str(hours[hour]["hours"]),
                               )
                            )
            total += hours[hour]["hours"]
        if total > 0:
            hour_list.append(TR(TD(""), TD(""), TD("Total"), TD("%d" % total)))

        output = DIV(
                     person_details,
                     TABLE(contact_row),
                     TABLE(id_row),
                     hour_list
                    )

        return output

    if r.record.type == 2:
        # Volunteer
        list_fields = ["person_id$first_name"]
        name = s3_fullname(r.record.person_id)
        exporter = S3Exporter().pdf
        return exporter(r,
                        method = "list",
                        #pdf_componentname = "inv_track_item",
                        pdf_title = "%s - %s" % \
                            (name, current.T("Volunteer Service Record")),
                        #pdf_filename = send_ref,
                        #list_fields = list_fields,
                        pdf_hide_comments = True,
                        pdf_header_padding = 12,
                        #pdf_footer = inv_send_pdf_footer,
                        #pdf_paper_alignment = "Landscape",
                        pdf_table_autogrow = "B",
                        pdf_callback = callback,
                        **attr
                       )
    else:
        # Staff
        return None

# =============================================================================
class HRMVirtualFields:
    """ Virtual fields as dimension classes for reports """

    extra_fields = ["person_id"]

    # -------------------------------------------------------------------------
    def certificate(self):
        """ Which Certificates the person has gained """
        try:
            person_id = self.hrm_human_resource.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            table = s3db.hrm_certification
            ctable = s3db.hrm_certificate
            query = (table.deleted == False) & \
                    (table.person_id == person_id) & \
                    (table.certificate_id == ctable.id)
            certs = current.db(query).select(ctable.name,
                                             distinct=True,
                                             orderby=ctable.name)
            if certs:
                names = [cert.name for cert in certs]
                return ",".join(names)

        return current.messages.NONE

    # -------------------------------------------------------------------------
    def course(self):
        """ Which Training Courses the person has attended """
        try:
            person_id = self.hrm_human_resource.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            table = s3db.hrm_training
            ctable = s3db.hrm_course
            query = (table.deleted == False) & \
                    (table.person_id == person_id) & \
                    (table.course_id == ctable.id)
            courses = current.db(query).select(ctable.name,
                                               distinct=True,
                                               orderby=ctable.name)
            if courses:
                names = [course.name for course in courses]
                return ",".join(names)

        return current.messages.NONE

    # -------------------------------------------------------------------------
    def email(self):
        """ Email addresses """
        try:
            person_id = self.hrm_human_resource.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            ptable = s3db.pr_person
            ctable = s3db.pr_contact
            query = (ctable.deleted == False) & \
                    (ctable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (ctable.contact_method == "EMAIL")
            contacts = current.db(query).select(ctable.value,
                                                orderby=ctable.priority)
            if contacts:
                values = [contact.value for contact in contacts]
                return ",".join(values)

        return current.messages.NONE

    # -------------------------------------------------------------------------
    def phone(self):
        """ Mobile phone number(s) """
        try:
            person_id = self.hrm_human_resource.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            ptable = s3db.pr_person
            ctable = s3db.pr_contact
            query = (ctable.deleted == False) & \
                    (ctable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (ctable.contact_method == "SMS")
                    #(ctable.contact_method.belongs(["SMS", "HOME_PHONE", "WORK_PHONE"]))
            contacts = current.db(query).select(ctable.value,
                                                orderby=ctable.priority)
            if contacts:
                values = [contact.value for contact in contacts]
                return ",".join(values)

        return current.messages.NONE

# =============================================================================
class HRMProgrammeVirtualFields:
    """ Virtual fields as dimension classes for reports """

    extra_fields = ["person_id"]

    # -------------------------------------------------------------------------
    def programme(self):
        """ Which Programme a Volunteer is associated with """
        try:
            person_id = self.hrm_human_resource.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            ptable = s3db.hrm_programme
            htable = s3db.hrm_programme_hours
            query = (htable.deleted == False) & \
                    (htable.person_id == person_id) & \
                    (htable.programme_id == ptable.id)
            programme = current.db(query).select(ptable.name,
                                                 orderby=htable.date).last()
            if programme:
                return programme.name

        return current.messages.NONE

    # -------------------------------------------------------------------------
    def active(self):
        """ Whether the volunteer is considered active """
        try:
            person_id = self.hrm_human_resource.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            active = hrm_active(person_id)
            args = current.request.args
            if "search" in args:
                # We can't use an HTML represent, but can use a LazyT
                # if we match in the search options
                return current.T("Yes") if active else current.T("No")
            elif "report" in args:
                # We can't use a represent
                return active
            # List view, so HTML represent is fine
            if active:
                active = DIV(current.T("Yes"),
                             _style="color:green;")
            else:
                active = DIV(current.T("No"),
                             _style="color:red;")
            return active

        return current.messages.NONE

# =============================================================================
class HRMProgrammePersonVirtualFields:
    """ Virtual fields for RHeader of Person record within HRM """

    extra_fields = []

    # -------------------------------------------------------------------------
    def programme(self):
        """ Which Programme a Volunteer is associated with """
        try:
            person_id = self.pr_person.id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            ptable = s3db.hrm_programme
            htable = s3db.hrm_programme_hours
            query = (htable.deleted == False) & \
                    (htable.person_id == person_id) & \
                    (htable.programme_id == ptable.id)
            programme = current.db(query).select(ptable.name,
                                                 orderby=htable.date).last()
            if programme:
                return programme.name

        return current.messages.NONE

    # -------------------------------------------------------------------------
    def active(self):
        """ Whether the volunteer is considered active """
        try:
            person_id = self.pr_person.id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            active = hrm_active(person_id)
            args = current.request.args
            if "search" in args:
                # We can't use an HTML represent, but can use a LazyT
                # if we match in the search options
                return current.T("Yes") if active else current.T("No")
            elif "report" in args:
                # We can't use a represent
                return active
            # List view, so HTML represent is fine
            if active:
                active = DIV(current.T("Yes"),
                             _style="color:green;")
            else:
                active = DIV(current.T("No"),
                             _style="color:red;")
            return active

        return current.messages.NONE

# =============================================================================
class HRMTrainingVirtualFields:
    """ Virtual fields as dimension classes for reports """

    extra_fields = ["date",
                    "person_id",
                    ]

    # -------------------------------------------------------------------------
    def month(self):
        """ Year/Month of the start date of the training event """
        try:
            date = self.hrm_training.date
        except AttributeError:
            # not available
            date = None
        if date:
            return "%s/%02d" % (date.year, date.month)
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    def year(self):
        """ The Year of the training event """
        try:
            date = self.hrm_training.date
        except AttributeError:
            # not available
            date = None
        if date:
            return date.year
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    def job_title(self):
        """
            Which Job Titles(s) the person is active with
        """
        try:
            person_id = self.hrm_training.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            table = s3db.hrm_human_resource
            jtable = s3db.hrm_job_title
            query = (table.person_id == person_id) & \
                    (table.status != 2) & \
                    (table.job_title_id == jtable.id)
            jobs = current.db(query).select(jtable.name,
                                            distinct=True,
                                            orderby=jtable.name)
            if jobs:
                output = ""
                for job in jobs:
                    repr = job.name
                    if output:
                        output = "%s, %s" % (output, repr)
                    else:
                        output = repr
                return output

        return current.messages.NONE

    # -------------------------------------------------------------------------
    def organisation(self):
        """
            Which Organisation(s)/Branch(es) the person is actively affiliated with
        """
        try:
            person_id = self.hrm_training.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            table = s3db.hrm_human_resource
            query = (table.person_id == person_id) & \
                    (table.status != 2)
            orgs = current.db(query).select(table.organisation_id,
                                            distinct=True)
            if orgs:
                output = ""
                represent = s3db.org_organisation_represent
                for org in orgs:
                    repr = represent(org.organisation_id)
                    if output:
                        output = "%s, %s" % (output, repr)
                    else:
                        output = repr
                return output

        return current.messages.NONE

# =============================================================================
def hrm_rheader(r, tabs=[],
                profile = False):
    """ Resource headers for component views """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None
    record = r.record
    if record is None:
        # List or Create form: rheader makes no sense here
        return None

    T = current.T
    table = r.table
    resourcename = r.name

    if resourcename == "person":
        settings = current.deployment_settings
        vars = current.request.get_vars
        hr = vars.get("human_resource.id", None)
        if hr:
            name = hrm_human_resource_represent(hr)
        else:
            name = s3_fullname(record)
        group = vars.get("group", "staff")
        experience_tab = None
        service_record = ""
        tbl = TABLE(TR(TH(name,
                          _style="padding-top:15px;")
                       ))
        if group == "volunteer":
            if settings.get_hrm_vol_experience() == "programme":
                experience_tab = (T("Hours"), "hours")
                # Show all Hours spent on both Programmes & Trainings
                # - last month & last year
                now = current.request.utcnow
                last_year = now - datetime.timedelta(days=365)
                db = current.db
                s3db = current.s3db
                ptable = s3db.hrm_programme_hours
                query = (ptable.date > last_year.date()) & \
                        (ptable.deleted == False) & \
                        (ptable.person_id == r.id)
                rows = db(query).select(ptable.date,
                                        ptable.hours,
                                        ptable.training)
                programme_hours_year = 0
                programme_hours_month = 0
                training_hours_year = 0
                training_hours_month = 0
                last_month = now - datetime.timedelta(days=30)
                last_month = last_month.date()
                for row in rows:
                    hours = row.hours
                    if hours:
                        training = row.training
                        if training:
                            training_hours_year += hours
                            if row.date > last_month:
                                training_hours_month += hours
                        else:
                            programme_hours_year += hours
                            if row.date > last_month:
                                programme_hours_month += hours

                # Already formatted as HTML
                enable_active_field = settings.set_org_dependent_field("vol_volunteer", "active", 
                                                                       enable_field = False)
                if enable_active_field:
                    active = TD(record.active)
                    tooltip = SPAN(_class="tooltip",
                                   _title="%s|%s" % \
                        (T("Active"),
                         T("A volunteer is defined as active if they've participated in an average of 8 or more hours of Programme work or Trainings per month in the last year")),
                                   _style="display:inline-block"
                                   )
                    active_cells = [TH("%s:" % T("Active?"), tooltip),
                                    active]
                else:
                    active_cells = []
                row1 = TR(TH("%s:" % T("Programme")),
                          record.programme,
                          *active_cells
                          )
                row2 = TR(TH("%s:" % T("Programme Hours (Month)")),
                          str(programme_hours_month),
                          TH("%s:" % T("Training Hours (Month)")),
                          str(training_hours_month)
                          )
                row3 = TR(TH("%s:" % T("Programme Hours (Year)")),
                          str(programme_hours_year),
                          TH("%s:" % T("Training Hours (Year)")),
                          str(training_hours_year)
                          )
                tbl = TABLE(TR(TH(name,
                                  _colspan=4)
                               ),
                            row1,
                            row2,
                            row3,
                            )
                service_record = DIV(A(T("Service Record"),
                                       _href = URL(c = "vol",
                                                   f = "human_resource",
                                                   args = [hr, "form"]
                                                   ),
                                       _id = "service_record",
                                       _class = "action-btn"
                                      ),
                                    _style="margin-bottom:10px;"
                                    )
            elif settings.get_hrm_vol_experience() == "experience":
                experience_tab = (T("Experience"), "experience")
        elif settings.get_hrm_staff_experience() == "experience":
            experience_tab = (T("Experience"), "experience")

        if settings.get_hrm_use_certificates():
            certificates_tab = (T("Certificates"), "certificate")
        else:
            certificates_tab = None

        if settings.get_hrm_use_credentials():
            credentials_tab = (T("Credentials"), "credential")
        else:
            credentials_tab = None

        if settings.get_hrm_use_description():
            description_tab = (T("Description"), "physical_description")
        else:
            description_tab = None

        if settings.get_hrm_use_education():
            education_tab = (T("Education"), "education")
        else:
            education_tab = None

        if settings.get_hrm_use_id():
            id_tab = (T("ID"), "identity")
        else:
            id_tab = None

        if settings.get_hrm_use_skills():
            skills_tab = (T("Skills"), "competency")
        else:
            skills_tab = None

        if settings.get_hrm_use_teams():
            teams_tab = (T("Teams"), "group_membership")
        else:
            teams_tab = None

        if settings.get_hrm_use_trainings():
            trainings_tab = (T("Trainings"), "training")
        else:
            trainings_tab = None

        if profile:
            # Configure for personal mode
            tabs = [(T("Person Details"), None),
                    (T("User Account"), "user"),
                    (T("Staff/Volunteer Record"), "human_resource"),
                    id_tab,
                    description_tab,
                    (T("Address"), "address"),
                    (T("Contacts"), "contacts"),
                    education_tab,
                    trainings_tab,
                    certificates_tab,
                    skills_tab,
                    credentials_tab,
                    experience_tab,
                    teams_tab,
                    #(T("Assets"), "asset"),
                   ]
        elif current.session.s3.hrm.mode is not None:
            # Configure for personal mode
            tabs = [(T("Person Details"), None),
                    id_tab,
                    description_tab,
                    (T("Address"), "address"),
                    (T("Contacts"), "contacts"),
                    trainings_tab,
                    certificates_tab,
                    skills_tab,
                    credentials_tab,
                    experience_tab,
                    (T("Positions"), "human_resource"),
                    teams_tab,
                    (T("Assets"), "asset"),
                   ]
        else:
            # Configure for HR manager mode
            if group == "staff":
                hr_record = T("Staff Record")
            elif group == "volunteer":
                hr_record = T("Volunteer Record")
            tabs = [(T("Person Details"), None),
                    (hr_record, "human_resource"),
                    id_tab,
                    description_tab,
                    (T("Address"), "address"),
                    (T("Contacts"), "contacts"),
                    education_tab,
                    trainings_tab,
                    certificates_tab,
                    skills_tab,
                    credentials_tab,
                    experience_tab,
                    teams_tab,
                    (T("Assets"), "asset"),
                   ]
            # Add role manager tab if a user record exists
            user_id = current.auth.s3_get_user_id(record.id)
            if user_id:
                tabs.append((T("Roles"), "roles"))
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(service_record,
                      A(s3_avatar_represent(record.id,
                                            "pr_person",
                                            _class="hrm_avatar"),
                        _href=URL(f="person", args=[record.id, "image"],
                                  vars = vars),
                        ),
                      tbl,
                      rheader_tabs)

    elif resourcename == "training_event":
        # Tabs
        tabs = [(T("Training Event Details"), None),
                (T("Participants"), "participant")]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.course_id.label),
                               table.course_id.represent(record.course_id)),
                            TR(TH("%s: " % table.site_id.label),
                               table.site_id.represent(record.site_id)),
                            TR(TH("%s: " % table.start_date.label),
                               table.start_date.represent(record.start_date)),
                            ),
                      rheader_tabs)

    elif resourcename == "certificate":
        # Tabs
        tabs = [(T("Certificate Details"), None),
                (T("Skill Equivalence"), "certificate_skill")]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.name.label),
                               record.name),
                            ),
                      rheader_tabs)

    elif resourcename == "course":
        # Tabs
        tabs = [(T("Course Details"), None),
                (T("Course Certificates"), "course_certificate")]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.name.label),
                               record.name),
                            ),
                      rheader_tabs)

    elif resourcename == "programme":
        # Load HR model to get CRUD string
        htable = current.s3db.hrm_human_resource
        # Tabs
        tabs = [(T("Programme Details"), None),
                (current.response.s3.crud_strings["hrm_human_resource"].title_list, "person")]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.name.label),
                               record.name),
                            ),
                      rheader_tabs)

    return rheader

# =============================================================================
def hrm_training_event_controller():
    """
        Training Event Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    if current.session.s3.hrm.mode is not None:
        current.session.error = T("Access denied")
        redirect(URL(f="index"))

    s3 = current.response.s3

    def prep(r):
        if r.component and \
           (r.interactive or r.extension == "aaData"):
            T = current.T
            # Use appropriate CRUD strings
            s3.crud_strings["hrm_training"] = Storage(
                title_create = T("Add Participant"),
                title_display = T("Participant Details"),
                title_list = T("Participants"),
                title_update = T("Edit Participant"),
                title_search = T("Search Participants"),
                title_upload = T("Import Participant Participants"),
                subtitle_create = T("Add Participant"),
                label_list_button = T("List Participants"),
                label_create_button = T("Add New Participant"),
                label_delete_button = T("Delete Participant"),
                msg_record_created = T("Participant added"),
                msg_record_modified = T("Participant updated"),
                msg_record_deleted = T("Participant deleted"),
                msg_no_match = T("No entries found"),
                msg_list_empty = T("Currently no Participants registered"))
            # Hide/default fields which get populated from the Event
            record = r.record
            table = current.s3db.hrm_training
            field = table.course_id
            field.readable = False
            field.writable = False
            field.default = record.course_id
            field = table.date
            field.readable = False
            field.writable = False
            field.default = record.start_date
            field = table.hours
            field.readable = False
            field.writable = False
            field.default = record.hours
            # Suitable list_fields
            list_fields = ["person_id",
                           (T("Job Title"), "job_title"),
                           (current.messages.ORGANISATION, "organisation"),
                           ]
            current.s3db.configure("hrm_training",
                                   list_fields=list_fields)
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and not r.component:
            # Set the minimum end_date to the same as the start_date
            s3.jquery_ready.append(
'''S3.start_end_date('hrm_training_event_start_date','hrm_training_event_end_date')''')
        return output
    s3.postp = postp

    output = current.rest_controller("hrm", "training_event",
                                     rheader=hrm_rheader)
    return output

# =============================================================================
def hrm_training_controller():
    """
        Training Controller, defined in the model for use from
        multiple controllers for unified menus
         - used for Searching for Participants
    """

    if current.session.s3.hrm.mode is not None:
        current.session.error = T("Access denied")
        redirect(URL(f="index"))

    def prep(r):
        if r.interactive or \
           r.extension == "aaData":
            # Suitable list_fields
            T = current.T
            list_fields = ["course_id",
                           "person_id",
                           (T("Job Title"), "job_title"),
                           (current.messages.ORGANISATION, "organisation"),
                           "date",
                           ]
            current.s3db.configure("hrm_training",
                                   insertable=False,
                                   list_fields=list_fields)
        return True
    current.response.s3.prep = prep

    output = current.rest_controller("hrm", "training")
    return output

# END =========================================================================
