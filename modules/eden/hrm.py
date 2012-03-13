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
           "S3HRJobModel",
           "S3HRSkillModel",
           "hrm_hr_represent",
           "hrm_human_resource_represent",
           #"hrm_position_represent",
           ]

from gluon import *
from gluon.storage import Storage
import gluon.contrib.simplejson as json
from ..s3 import *

# =============================================================================
class S3HRModel(S3Model):

    names = ["hrm_human_resource",
             "hrm_human_resource_id",
             "hrm_human_resource_search",
             "hrm_type_opts"
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id
        site_id = self.org_site_id

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        s3_date_represent = S3DateTime.date_represent
        s3_date_format = settings.get_L10n_date_format()

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
            #3: T("Member")
        }

        hrm_status_opts = {
            1: T("active"),
            2: T("obsolete") # retired is a better term?
        }

        tablename = "hrm_human_resource"
        table = self.define_table(tablename,
                                  self.super_link("track_id", "sit_trackable"),
                                  # Administrative data
                                  organisation_id(widget=S3OrganisationAutocompleteWidget(default_from_profile=True),
                                                  empty=False),
                                  person_id(widget=S3AddPersonWidget(controller="hrm"),
                                            requires=IS_ADD_PERSON_WIDGET(),
                                            comment=None),
                                  Field("type", "integer",
                                        requires = IS_IN_SET(hrm_type_opts,
                                                             zero=None),
                                        default = 1,
                                        label = T("Type"),
                                        represent = lambda opt: \
                                            hrm_type_opts.get(opt,
                                                              UNKNOWN_OPT)),
                                  #Field("code", label=T("Staff ID")),
                                  Field("job_title", label=T("Job Title")),
                                  # Current status
                                  Field("status", "integer",
                                        requires = IS_IN_SET(hrm_status_opts,
                                                             zero=None),
                                        default = 1,
                                        label = T("Status"),
                                        represent = lambda opt: \
                                            hrm_status_opts.get(opt,
                                                                UNKNOWN_OPT)),
                                  # Contract
                                  Field("start_date", "date",
                                        label = T("Start Date"),
                                        requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  Field("end_date", "date",
                                        label = T("End Date"),
                                        requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  # Base location + Site
                                  location_id(label=T("Base Location"),
                                              readable=False,
                                              writable=False),
                                  site_id,
                                  *(s3.lx_fields() + s3.meta_fields()))

        hrm_human_resource_requires = IS_NULL_OR(IS_ONE_OF(db,
                                            "hrm_human_resource.id",
                                            hrm_human_resource_represent,
                                            orderby="hrm_human_resource.type"))

        # Used by Scenarios, Events, Tasks & RAT
        human_resource_id = S3ReusableField("human_resource_id",
                                            db.hrm_human_resource,
                                            sortby = ["type", "status"],
                                            requires = hrm_human_resource_requires,
                                            represent = hrm_human_resource_represent,
                                            widget = S3PersonAutocompleteWidget(),
                                            comment = T("Enter some characters to bring up a list of possible matches"),
                                            #widget = S3SearchAutocompleteWidget(tablename="hrm_human_resource",
                                            #                                    represent=lambda id: \
                                            #                                        hrm_human_resource_represent(id,
                                            #                                                                     none_value = None),
                                            #                                    ),
                                            label = T("Human Resource"),
                                            ondelete = "RESTRICT")

        human_resource_search = S3Search(
            simple=(self.human_resource_search_simple_widget("simple")),
            advanced=(self.human_resource_search_simple_widget("advanced"),
                      S3SearchOptionsWidget(
                        name="human_resource_search_type",
                        label=T("Type"),
                        field=["type"],
                        cols = 3
                      ),
                      S3SearchOptionsWidget(
                        name="human_resource_search_org",
                        label=T("Organization"),
                        field=["organisation_id"],
                        represent ="%(name)s",
                        cols = 3
                      ),
                      S3SearchLocationHierarchyWidget(
                        name="human_resource_search_L1",
                        field="L1",
                        cols = 3,
                      ),
                      S3SearchLocationHierarchyWidget(
                        name="human_resource_search_L2",
                        field="L2",
                        cols = 3,
                      ),
                      S3SearchLocationWidget(
                        name="human_resource_search_map",
                        label=T("Map"),
                      ),
                      S3SearchOptionsWidget(
                        name="human_resource_search_site",
                        label=T("Facility"),
                        field=["site_id"]
                      ),
                      # S3SearchSkillsWidget(
                        # name="human_resource_search_skills",
                        # label=T("Skills"),
                        # field=["skill_id"]
                      # ),
                      # This currently breaks Requests from being able to save since this form is embedded inside the S3SearchAutocompleteWidget
                      #S3SearchMinMaxWidget(
                      #  name="human_resource_search_date",
                      #  method="range",
                      #  label=T("Contract Expiry Date"),
                      #  field=["end_date"]
                      #),
            ))

        table.virtualfields.append(HRMVirtualFields())

        hierarchy = current.gis.get_location_hierarchy()
        report_fields = [
                         #"organisation_id",
                         "person_id",
                         "site_id",
                         (T("Training"), "course"),
                         (hierarchy["L1"], "L1"),
                         (hierarchy["L2"], "L2"),
                        ]

        self.configure(tablename,
                       super_entity = "sit_trackable",
                       deletable = False,
                       search_method = human_resource_search,
                       onaccept = self.hrm_human_resource_onaccept,
                       ondelete = self.hrm_human_resource_ondelete,
                       deduplicate=self.hrm_human_resource_deduplicate,
                       report_filter=[
                            S3SearchLocationHierarchyWidget(
                                name="human_resource_search_L1",
                                field="L1",
                                cols = 3,
                            ),
                            S3SearchLocationHierarchyWidget(
                                name="human_resource_search_L2",
                                field="L2",
                                cols = 3,
                            ),
                            S3SearchOptionsWidget(
                                name="human_resource_search_site",
                                label=T("Facility"),
                                field=["site_id"]
                            ),
                        ],
                       report_rows = report_fields,
                       report_cols = report_fields,
                       report_fact = report_fields,
                       report_method=["count", "list"],
                  )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(
                    hrm_human_resource_id = human_resource_id,
                    hrm_human_resource_search = human_resource_search,
                    hrm_type_opts = hrm_type_opts
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
                             #"person_id$occupation",
                             "job_title"]
                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_update_staff_role(record, user_id):
        """
            Set/retract the Org/Site staff role

            @param record: the hrm_human_resource record
            @param user_id: the auth_user record ID of the person the
                            record belongs to.
        """

        db = current.db
        auth = current.auth

        htable = db.hrm_human_resource
        utable = auth.settings.table_user
        mtable = auth.settings.table_membership

        org_role = record.owned_by_organisation
        fac_role = record.owned_by_facility

        if record.deleted:
            try:
                fk = json.loads(record.deleted_fk)
                organisation_id = fk.get("organisation_id", None)
                site_id = fk.get("site_id", None)
                person_id = fk.get("person_id", None)
            except:
                return
        else:
            organisation_id = record.get("organisation_id", None)
            site_id = record.get("site_id", None)
            person_id = record.get("person_id", None)

        if record.deleted or record.status != 1:
            remove_org_role = True
            if org_role:
                if organisation_id and person_id:
                    # Check whether the person has another active
                    # HR record in the same organisation
                    query = (htable.person_id == person_id) & \
                            (htable.organisation_id == organisation_id) & \
                            (htable.id != record.id) & \
                            (htable.status == 1) & \
                            (htable.deleted != True)
                    if db(query).select(htable.id, limitby=(0, 1)).first():
                        remove_org_role = False
                if remove_org_role:
                    query = (mtable.user_id == user_id) & \
                            (mtable.group_id == org_role)
                    db(query).delete()
            remove_fac_role = True
            if fac_role:
                if site_id and person_id:
                    # Check whether the person has another active
                    # HR record at the same site
                    query = (htable.person_id == person_id) & \
                            (htable.site_id == site_id) & \
                            (htable.id != record.id) & \
                            (htable.status == 1) & \
                            (htable.deleted != True)
                    if db(query).select(htable.id, limitby=(0, 1)).first():
                        remove_fac_role = False
                if remove_fac_role:
                    query = (mtable.user_id == user_id) & \
                            (mtable.group_id == fac_role)
                    db(query).delete()
        else:
            if org_role:
                query = (mtable.user_id == user_id) & \
                        (mtable.group_id == org_role)
                role = db(query).select(limitby=(0, 1)).first()
                if not role:
                    mtable.insert(user_id = user_id,
                                  group_id = org_role)
            if fac_role:
                query = (mtable.user_id == user_id) & \
                        (mtable.group_id == fac_role)
                role = db(query).select(limitby=(0, 1)).first()
                if not role:
                    mtable.insert(user_id = user_id,
                                  group_id = fac_role)

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_ondelete(row):
        """ On-delete routine for HR records """

        db = current.db
        s3db = current.s3db

        htable = s3db.hrm_human_resource
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        utable = db.auth_user

        user = None

        if row:
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

            s3db.pr_update_affiliations(htable, record)

            query = (ptable.id == person_id) & \
                    (ltable.pe_id == ptable.pe_id) & \
                    (utable.id == ltable.user_id)
            user = db(query).select(utable.id,
                                    limitby=(0, 1)).first()
        if not user:
            return
        else:
            user_id = user.id
            # Set/retract the staff role
            S3HRModel.hrm_update_staff_role(record, user_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_onaccept(form):
        """ On-accept for HR records """

        db = current.db
        s3db = current.s3db
        auth = current.auth

        utable = auth.settings.table_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        htable = s3db.hrm_human_resource

        # Get the full record
        id = form.vars.id
        if id:
            query = (htable.id == id)
            record = db(query).select(htable.id,
                                      htable.type,
                                      htable.person_id,
                                      htable.site_id,
                                      htable.organisation_id,
                                      # Needed by hrm_update_staff_role()
                                      htable.owned_by_organisation,
                                      htable.owned_by_facility,
                                      htable.status,
                                      htable.deleted,
                                      htable.deleted_fk,
                                      limitby=(0, 1)).first()
        else:
            return

        data = Storage()

        # Affiliation
        s3db.pr_update_affiliations(htable, record)

        if record.type == 1 and record.site_id:
            # Staff: update the location ID from the selected site
            stable = s3db.org_site
            query = (stable._id == record.site_id)
            site = db(query).select(stable.location_id,
                                    limitby=(0, 1)).first()
            if site:
                data.location_id = site.location_id
        elif record.type == 2:
            # Volunteer: update the location ID from the Home Address
            atable = s3db.pr_address
            query = (atable.pe_id == ptable.pe_id) & \
                    (ptable.id == record.person_id) & \
                    (atable.type == 1) & \
                    (atable.deleted == False)
            address = db(query).select(atable.location_id,
                                       limitby=(0, 1)).first()
            if address:
                data.location_id = address.location_id

        # Add record owner (user)
        query = (ptable.id == record.person_id) & \
                (ltable.pe_id == ptable.pe_id) & \
                (utable.id == ltable.user_id)
        user = db(query).select(utable.id,
                                utable.organisation_id,
                                utable.site_id,
                                limitby=(0, 1)).first()
        if user:
            user_id = user.id
            data.owned_by_user = user.id

        if not data:
            return
        record.update_record(**data)

        if data.location_id:
            # Populate the Lx fields
            current.response.s3.lx_update(htable, record.id)

        if user and record.organisation_id:
            profile = dict()
            if not user.organisation_id:
                # Set the Organisation in the Profile, if not already set
                profile["organisation_id"] = record.organisation_id
            if not user.site_id:
                # Set the Site in the Profile, if not already set
                profile["site_id"] = record.site_id
            if profile:
                query = (utable.id == user.id)
                db(query).update(**profile)
            # Set/retract the staff role
            S3HRModel.hrm_update_staff_role(record, user_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_deduplicate(item):
        """
            HR record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        if item.tablename == "hrm_human_resource":

            db = current.db
            s3db = current.s3db

            hrtable = s3db.hrm_human_resource

            data = item.data

            person_id = data.person_id
            organisation_id = data.organisation_id

            # This allows only one HR record per person and organisation,
            # if multiple HR records of the same person with the same org
            # are desired, then this needs an additional criteria in the
            # query (e.g. job title, or type):

            query = (hrtable.deleted != True) & \
                    (hrtable.person_id == person_id) & \
                    (hrtable.organisation_id == organisation_id)
            row = db(query).select(hrtable.id,
                                   limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

# =============================================================================
class S3HRJobModel(S3Model):

    names = ["hrm_job_role",
             "hrm_job_role_id",
             #"hrm_position",
             #"hrm_position_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        #settings = current.deployment_settings

        #group_id = self.pr_group_id
        #location_id = self.gis_location_id
        #organisation_id = self.org_organisation_id
        #site_id = self.org_site_id
        #human_resource_id = self.human_resource_id

        messages = current.messages
        NONE = messages.NONE

        # =========================================================================
        # Job Roles (Mayon: StaffResourceType)
        #

        tablename = "hrm_job_role"
        table = self.define_table(tablename,
                                  Field("name", notnull=True, unique=True,
                                        length=64,    # Mayon compatibility
                                        label=T("Name")),
                                  s3.comments(label="Description", comment=None),
                                  *s3.meta_fields())

        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Job Role"),
            title_display = T("Job Role Details"),
            title_list = T("Job Role Catalog"),
            title_update = T("Edit Job Role"),
            title_search = T("Search Job Roles"),
            subtitle_create = T("Add Job Role"),
            subtitle_list = T("Job Roles"),
            label_list_button = T("List Job Roles"),
            label_create_button = T("Add New Job Role"),
            label_delete_button = T("Delete Job Role"),
            msg_record_created = T("Job Role added"),
            msg_record_modified = T("Job Role updated"),
            msg_record_deleted = T("Job Role deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        label_create = s3.crud_strings[tablename].label_create_button
        job_role_id = S3ReusableField("job_role_id", db.hrm_job_role,
                                      sortby = "name",
                                      label = T("Job Role"),
                                      requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                      "hrm_job_role.id",
                                                                      "%(name)s")),
                                      represent = lambda id: \
                                        (id and [db.hrm_job_role[id].name] or [NONE])[0],
                                      comment = DIV(A(label_create,
                                                      _class="colorbox",
                                                      _href=URL(c="hrm",
                                                                f="job_role",
                                                                args="create",
                                                                vars=dict(format="popup")),
                                                      _target="top",
                                                      _title=label_create),
                                                    DIV(DIV(_class="tooltip",
                                                            _title="%s|%s" % (label_create,
                                                                              T("Add a new job role to the catalog."))))),
                                      ondelete = "SET NULL")

        # =========================================================================
        # Positions
        #
        # @ToDo: Shifts for use in Scenarios & during Exercises & Events
        #
        # @ToDo: Vacancies
        #

        #tablename = "hrm_position"
        #table = self.define_table(tablename,
        #                          job_role_id(empty=False),
        #                          organisation_id(empty=False),
        #                          site_id,
        #                          group_id(label="Team"),
        #                          *s3.meta_fields())
        #table.site_id.readable = table.site_id.writable = True

        #s3.crud_strings[tablename] = Storage(
        #    title_create = T("Add Position"),
        #    title_display = T("Position Details"),
        #    title_list = T("Position Catalog"),
        #    title_update = T("Edit Position"),
        #    title_search = T("Search Positions"),
        #    subtitle_create = T("Add Position"),
        #    subtitle_list = T("Positions"),
        #    label_list_button = T("List Positions"),
        #    label_create_button = T("Add Position"),
        #    label_delete_button = T("Delete Position"),
        #    msg_record_created = T("Position added"),
        #    msg_record_modified = T("Position updated"),
        #    msg_record_deleted = T("Position deleted"),
        #    msg_list_empty = T("Currently no entries in the catalog"))

        #label_create = s3.crud_strings[tablename].label_create_button
        #position_id = S3ReusableField("position_id", db.hrm_position,
        #                              sortby = "name",
        #                              label = T("Position"),
        #                              requires = IS_NULL_OR(IS_ONE_OF(db,
        #                                                              "hrm_position.id",
        #                                                              hrm_position_represent)),
        #                              represent = hrm_position_represent,
        #                              comment = DIV(A(label_create,
        #                                              _class="colorbox",
        #                                              _href=URL(c="hrm",
        #                                                        f="position",
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

        #resourcename = "availability"
        #tablename = "hrm_availability"
        #table = self.define_table(tablename,
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
                                                                  ##gis_location_represent_row,
                                                                  ##filterby="level",
                                                                  ### @ToDo Should this change per config?
                                                                  ##filter_opts=gis.region_level_keys,
                                                                  ##orderby="gis_location.name"),
                                               ##widget=None),
                                   #*s3.meta_fields())

        ## Availability as component of human resources
        #self.add_component(table,
                           #hrm_human_resource="human_resource_id")

        # =========================================================================
        # Hours registration
        #
        #resourcename = "hours"
        #tablename = "hrm_hours"
        #table = self.define_table(tablename,
                                  #human_resource_id(),
                                  #Field("timestmp_in", "datetime"),
                                  #Field("timestmp_out", "datetime"),
                                  #Field("hours", "double"),
                                  #*s3.meta_fields())

        ## Hours as component of human resources
        #self.add_component(table,
                           #hrm_human_resource="human_resource_id")


        # =========================================================================
        # Vacancy
        #
        # These are Positions which are not yet Filled
        #
        #tablename = "hrm_vacancy"
        #table = self.define_table(tablename,
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
                                  #*s3.meta_fields())

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(
                    hrm_job_role_id = job_role_id,
                    #hrm_position_id = position_id
                )


# =============================================================================
class S3HRSkillModel(S3Model):

    names = ["hrm_skill_type",
             "hrm_skill",
             "hrm_competency",
             "hrm_credential",
             "hrm_training",
             "hrm_training_event",
             "hrm_certificate",
             "hrm_certification",
             "hrm_certificate_skill",
             "hrm_course",
             "hrm_course_certificate",
             "hrm_experience",
             "hrm_skill_id",
             "hrm_multi_skill_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        s3 = current.response.s3
        session = current.session
        settings = current.deployment_settings

        person_id = self.pr_person_id
        organisation_id = self.org_organisation_id
        site_id = self.org_site_id
        job_role_id = self.hrm_job_role_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        system_roles = session.s3.system_roles
        ADMIN = system_roles.ADMIN

        s3_date_represent = S3DateTime.date_represent
        s3_date_format = settings.get_L10n_date_format()

        # Shortcuts
        add_component = self.add_component
        comments = s3.comments
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        meta_fields = s3.meta_fields
        s3_has_role = auth.s3_has_role
        super_link = self.super_link

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
                             comments(),
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Skill Type"),
            title_display = T("Details"),
            title_list = T("Skill Type Catalog"),
            title_update = T("Edit Skill Type"),
            title_search = T("Search Skill Types"),
            subtitle_create = T("Add Skill Type"),
            subtitle_list = T("Skill Types"),
            label_list_button = T("List Skill Types"),
            label_create_button = T("Add New Skill Type"),
            label_delete_button = T("Delete Skill Type"),
            msg_record_created = T("Skill Type added"),
            msg_record_modified = T("Skill Type updated"),
            msg_record_deleted = T("Skill Type deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        skill_types = settings.get_hrm_skill_types()
        label_create = s3.crud_strings[tablename].label_create_button
        skill_type_id = S3ReusableField("skill_type_id", db.hrm_skill_type,
                                        sortby = "name",
                                        label = T("Skill Type"),
                                        default=self.skill_type_default,
                                        readable=skill_types,
                                        writable=skill_types,
                                        requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                        "hrm_skill_type.id",
                                                                        "%(name)s")),
                                        represent = lambda id: \
                                            (id and [db.hrm_skill_type[id].name] or [NONE])[0],
                                        comment = DIV(A(label_create,
                                                        _class="colorbox",
                                                        _href=URL(c="hrm",
                                                                  f="skill_type",
                                                                  args="create",
                                                                  vars=dict(format="popup")),
                                                        _target="top",
                                                        _title=label_create),
                                                      DIV(DIV(_class="tooltip",
                                                              _title="%s|%s" % (label_create,
                                                                                T("Add a new skill type to the catalog."))))),
                                        ondelete = "RESTRICT")

        configure("hrm_skill_type",
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
                             comments(),
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Skill"),
            title_display = T("Skill Details"),
            title_list = T("Skill Catalog"),
            title_update = T("Edit Skill"),
            title_search = T("Search Skills"),
            subtitle_create = T("Add Skill"),
            subtitle_list = T("Skills"),
            label_list_button = T("List Skills"),
            label_create_button = T("Add New Skill"),
            label_delete_button = T("Delete Skill"),
            msg_record_created = T("Skill added"),
            msg_record_modified = T("Skill updated"),
            msg_record_deleted = T("Skill deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        if s3_has_role(ADMIN):
            label_create = crud_strings[tablename].label_create_button
            skill_help = DIV(A(label_create,
                               _class="colorbox",
                               _href=URL(c="hrm",
                                         f="skill",
                                         args="create",
                                        vars=dict(format="popup")),
                               _target="top",
                               _title=label_create))
        else:
            skill_help = DIV(_class="tooltip",
                             _title="%s|%s" % (T("Skill"),
                             T("Enter some characters to bring up a list of possible matches")))

        skill_id = S3ReusableField("skill_id", db.hrm_skill,
                        sortby = "name",
                        label = T("Skill"),
                        requires = IS_NULL_OR(IS_ONE_OF(db,
                                                        "hrm_skill.id",
                                                        "%(name)s",
                                                        sort=True)),
                        represent = lambda id: \
                            (id and [db.hrm_skill[id].name] or [T("None")])[0],
                        comment = skill_help,
                        ondelete = "SET NULL",
                        # Uncomment this to use an Autocomplete & not a Dropdown
                        # (NB FilterField widget needs fixing for that too)
                        #widget = S3AutocompleteWidget("hrm",
                        #                              "skill")
                        )

        multi_skill_id = S3ReusableField("skill_id", "list:reference hrm_skill",
                        sortby = "name",
                        label = T("Skills"),
                        requires = IS_NULL_OR(IS_ONE_OF(db,
                                                        "hrm_skill.id",
                                                        "%(name)s",
                                                        sort=True,
                                                        multiple=True)),
                        represent = hrm_multi_skill_represent,
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
                             comments(),
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Competency Rating"),
            title_display = T("Competency Rating Details"),
            title_list = T("Competency Rating Catalog"),
            title_update = T("Edit Competency Rating"),
            title_search = T("Search Competency Ratings"),
            subtitle_create = T("Add Competency Rating"),
            subtitle_list = T("Competency Ratings"),
            label_list_button = T("List Competency Ratings"),
            label_create_button = T("Add New Competency Rating"),
            label_delete_button = T("Delete Competency Rating"),
            msg_record_created = T("Competency Rating added"),
            msg_record_modified = T("Competency Rating updated"),
            msg_record_deleted = T("Competency Rating deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        competency_id = S3ReusableField("competency_id", db.hrm_competency_rating,
                                        sortby = "priority",
                                        label = T("Competency"),
                                        requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                        "hrm_competency_rating.id",
                                                                        "%(name)s",
                                                                        orderby="~hrm_competency_rating.priority",
                                                                        sort=True)),
                                        represent = lambda id: \
                                            (id and [db.hrm_competency_rating[id].name] or [NONE])[0],
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
                                             widget = S3OrganisationAutocompleteWidget(default_from_profile = True),
                                             comment = None,
                                             writable = False),
                             comments(),
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Skill"),
            title_display = T("Skill Details"),
            title_list = T("Skills"),
            title_update = T("Edit Skill"),
            title_search = T("Search Skills"),
            subtitle_create = T("Add Skill"),
            subtitle_list = T("Skills"),
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
        #                          job_role_id(),
        #                          skill_id(),
        #                          competency_id(),
        #                          Field("priority", "integer",
        #                                requires = IS_INT_IN_RANGE(1, 9),
        #                                widget = S3SliderWidget(minval=1, maxval=9, steprange=1, value=1),
        #                                comment = DIV(_class="tooltip",
        #                                              _title="%s|%s" % (T("Priority"),
        #                                                                T("Priority from 1 to 9. 1 is most preferred.")))),
        #                          comments(),
        #                          *meta_fields())

        #crud_strings[tablename] = Storage(
        #    title_create = T("Add Skill Provision"),
        #    title_display = T("Skill Provision Details"),
        #    title_list = T("Skill Provision Catalog"),
        #    title_update = T("Edit Skill Provision"),
        #    title_search = T("Search Skill Provisions"),
        #    subtitle_create = T("Add Skill Provision"),
        #    subtitle_list = T("Skill Provisions"),
        #    label_list_button = T("List Skill Provisions"),
        #    label_create_button = T("Add Skill Provision"),
        #    label_delete_button = T("Delete Skill Provision"),
        #    msg_record_created = T("Skill Provision added"),
        #    msg_record_modified = T("Skill Provision updated"),
        #    msg_record_deleted = T("Skill Provision deleted"),
        #    msg_list_empty = T("Currently no entries in the catalog"))

        #label_create = crud_strings[tablename].label_create_button
        #skill_group_id = S3ReusableField("skill_provision_id", db.hrm_skill_provision,
        #                           sortby = "name",
        #                           label = T("Skill Provision"),
        #                           requires = IS_NULL_OR(IS_ONE_OF(db,
        #                                                           "hrm_skill_provision.id",
        #                                                           "%(name)s")),
        #                           represent = lambda id: \
        #                            (id and [db.hrm_skill_provision[id].name] or [NONE])[0],
        #                           comment = DIV(A(label_create,
        #                                           _class="colorbox",
        #                                           _href=URL(c="hrm",
        #                                                     f="skill_provision",
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
                             job_role_id(),
                             organisation_id(empty=False,
                                             widget = S3OrganisationAutocompleteWidget(default_from_profile = True),
                                             label=T("Credentialling Organization")),
                             Field("performance_rating", "integer",
                                   label = T("Performance Rating"),
                                   requires = IS_IN_SET(hrm_pass_fail_opts,  # Default to pass/fail (can override to 5-levels in Controller)
                                                        zero=None),
                                   represent = lambda opt: \
                                       hrm_performance_opts.get(opt,
                                                                UNKNOWN_OPT)),
                             Field("date_received", "date",
                                   label = T("Date Received"),
                                   requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget(),
                                   ),
                             Field("date_expires", "date",   # @ToDo: Widget to make this process easier (date received + 6/12 months)
                                   label = T("Expiry Date"),
                                   requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget(),
                                   ),
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Credential"),
            title_display = T("Credential Details"),
            title_list = T("Credentials"),
            title_update = T("Edit Credential"),
            title_search = T("Search Credentials"),
            subtitle_create = T("Add Credential"),
            subtitle_list = T("Credentials"),
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
                             Field("name",
                                   length=128,
                                   notnull=True,
                                   label=T("Name")),
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Course"),
            title_display = T("Course Details"),
            title_list = T("Course Catalog"),
            title_update = T("Edit Course"),
            title_search = T("Search Courses"),
            subtitle_create = T("Add Course"),
            subtitle_list = T("Courses"),
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
            course_help = DIV(A(label_create,
                                _class="colorbox",
                                _href=URL(c="hrm",
                                          f="course",
                                          args="create",
                                          vars=dict(format="popup")),
                                _target="top",
                                _title=label_create))
        else:
            course_help = DIV(_class="tooltip",
                              _title="%s|%s" % (T("Course"),
                              T("Enter some characters to bring up a list of possible matches")))

        course_id = S3ReusableField("course_id", db.hrm_course,
                                    sortby = "name",
                                    label = T("Course"),
                                    requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                    "hrm_course.id",
                                                                    "%(name)s")),
                                    represent = lambda id: \
                                        (id and [db.hrm_course[id].name] or [NONE])[0],
                                    comment = course_help,
                                    ondelete = "RESTRICT",
                                    # Comment this to use a Dropdown & not an Autocomplete
                                    #widget = S3AutocompleteWidget("hrm",
                                    #                              "course")
                                )

        configure("hrm_course",
                  deduplicate=self.hrm_course_duplicate)

        # Components
        add_component("hrm_course_certificate", hrm_course="course_id")

        # =========================================================================
        # Training Events
        #
        tablename = "hrm_training_event"
        table = define_table(tablename,
                             course_id(),
                             site_id,
                             Field("start_date", "datetime",
                                   widget = S3DateWidget(),
                                   requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                   represent = s3_date_represent,
                                   label=T("Start Date")),
                             Field("end_date", "datetime",
                                   widget = S3DateWidget(),
                                   requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                   represent = s3_date_represent,
                                   label=T("End Date")),
                             Field("hours", "integer",
                                   label=T("Hours")),
                             # human_resource_id?
                             #Field("instructor",
                             #      label=T("Instructor")),
                             comments(),
                             *meta_fields())

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
            subtitle_list = T("Training Events"),
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
            course_help = DIV(A(label_create,
                                _class="colorbox",
                                _href=URL(c="hrm",
                                          f="training_event",
                                          args="create",
                                          vars=dict(format="popup")),
                                _target="top",
                                _title=label_create))
        else:
            course_help = DIV(_class="tooltip",
                              _title="%s|%s" % (T("Training Event"),
                              T("Enter some characters to bring up a list of possible matches")))

        training_event_id = S3ReusableField("training_event_id", db.hrm_training_event,
                                            sortby = "start_date",
                                            label = T("Training Event"),
                                            requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                            "hrm_training_event.id",
                                                                            hrm_training_event_represent,
                                                                            orderby="~hrm_training_event.start_date",
                                                                            )),
                                            represent = hrm_training_event_represent,
                                            comment = course_help,
                                            ondelete = "RESTRICT",
                                            # Comment this to use a Dropdown & not an Autocomplete
                                            widget = S3AutocompleteWidget("hrm",
                                                                          "training_event")
                                            )

        training_event_search = S3Search(
            advanced=(
                      S3SearchSimpleWidget(
                        name = "training_event_search_simple",
                        label = T("Text"),
                        comment = T("You can search by course name or event comments. You may use % as wildcard. Press 'Search' without input to list all events."),
                        field = ["course_id$name",
                                 "comments",
                                ]
                    ),
                    # S3SearchLocationHierarchyWidget(
                      # name="training_event_search_L1",
                      # field="site_id$L1",
                      # cols = 3,
                    # ),
                    # S3SearchLocationHierarchyWidget(
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
                      field=["site_id"]
                    ),
                    S3SearchMinMaxWidget(
                      name="training_event_search_date",
                      method="range",
                      label=T("Date"),
                      field=["start_date"]
                    ),
            ))

        # Resource Configuration
        configure(tablename,
                  create_next = URL(c="hrm",
                                    f="training_event",
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

        tablename = "hrm_training"
        table = define_table(tablename,
                             person_id( #@ToDo: Create a way to add new people to training as staff/volunteers
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Participant"),
                                                                        T("Start typing the Participant's name.")
                                                                        )
                                                      )
                                            ),
                             training_event_id(),
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
                             comments(),
                             *meta_fields())

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
            subtitle_list = T("Trainings"),
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
                                 "training_event_id$course_id$name",
                                 "comments",
                                ]
                    ),
                    S3SearchLocationHierarchyWidget(
                      name="training_search_L1",
                      field="person_id$L1",
                      cols = 3,
                    ),
                    S3SearchLocationHierarchyWidget(
                      name="training_search_L2",
                      field="person_id$L2",
                      cols = 3,
                    ),
                    # Can't currently have an Options widget search through a double layer of references
                    # Anyay, would we want to search by training location?
                    # Would Office of Staff be a better filter?
                    # S3SearchOptionsWidget(
                      # name="training_search_site",
                      # label=T("Facility"),
                      # field=["training_event_id$course_id$site_id"]
                    # ),
                    S3SearchOptionsWidget(
                      name="training_search_course",
                      label=T("Course"),
                      field=["training_event_id$course_id"]
                    ),
                    S3SearchMinMaxWidget(
                      name="training_search_date",
                      method="range",
                      label=T("Date"),
                      field=["training_event_id$start_date"]
                    ),
            ))

        hierarchy = current.gis.get_location_hierarchy()
        report_fields = [
                         "training_event_id",
                         "person_id",
                         (T("Course"), "training_event_id$course_id"),
                         (T("Facility"), "training_event_id$site_id"),
                         (T("Month"), "month"),
                         (hierarchy["L1"], "person_id$L1"),
                         (hierarchy["L2"], "person_id$L2"),
                        ]

        # Resource Configuration
        configure(tablename,
                  onaccept=self.hrm_training_onaccept,
                  ondelete=self.hrm_training_onaccept,
                  search_method = training_search,
                  report_filter=[
                            S3SearchLocationHierarchyWidget(
                                name="training_search_L1",
                                field="person_id$L1",
                                cols = 3,
                            ),
                            S3SearchLocationHierarchyWidget(
                                name="training_search_L2",
                                field="person_id$L2",
                                cols = 3,
                            ),
                            S3SearchOptionsWidget(
                                name="training_search_site",
                                field=["training_event_id$site_id"],
                                label = T("Facility"),
                                cols = 3,
                            ),
                            S3SearchMinMaxWidget(
                                name="training_search_date",
                                method="range",
                                label=T("Date"),
                                field=["training_event_id$start_date"]
                            ),
                        ],
                  report_rows = report_fields,
                  report_cols = report_fields,
                  report_fact = report_fields,
                  report_method=["count", "list"])

        # =====================================================================
        # Certificates
        #
        # NB Some Orgs will only trust the certificates of some Orgs
        # - we currently make no attempt to manage this trust chain
        #

        tablename = "hrm_certificate"
        table = define_table(tablename,
                             Field("name",
                                   length=128,   # Mayon Compatibility
                                   notnull=True,
                                   label=T("Name")),
                             organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True),
                                             label=T("Certifying Organization")),
                             Field("expiry", "integer",
                                   label = T("Expiry (months)")),
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Certificate"),
            title_display = T("Certificate Details"),
            title_list = T("Certificate Catalog"),
            title_update = T("Edit Certificate"),
            title_search = T("Search Certificates"),
            subtitle_create = T("Add Certificate"),
            subtitle_list = T("Certificates"),
            label_list_button = T("List Certificates"),
            label_create_button = T("Add New Certificate"),
            label_delete_button = T("Delete Certificate"),
            msg_record_created = T("Certificate added"),
            msg_record_modified = T("Certificate updated"),
            msg_record_deleted = T("Certificate deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no entries in the catalog"))

        label_create = crud_strings[tablename].label_create_button
        certificate_id = S3ReusableField("certificate_id", db.hrm_certificate,
                                         sortby = "name",
                                         label = T("Certificate"),
                                         requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                         "hrm_certificate.id",
                                                                         hrm_certificate_represent)),
                                         represent = hrm_certificate_represent,
                                         comment = DIV(A(label_create,
                                                         _class="colorbox",
                                                         _href=URL(c="hrm",
                                                                   f="certificate",
                                                                   args="create",
                                                                   vars=dict(format="popup")),
                                                         _target="top",
                                                         _title=label_create),
                                              DIV(DIV(_class="tooltip",
                                                      _title="%s|%s" % (label_create,
                                                                        T("Add a new certificate to the catalog."))))),
                                         ondelete = "RESTRICT")

        configure("hrm_certificate",
                  deduplicate=self.hrm_certificate_duplicate)

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
                             Field("date", "date",
                                   label=T("Expiry Date"),
                                   represent = s3_date_represent,
                                   requires = IS_NULL_OR(IS_DATE(format = s3_date_format)),
                                   widget = S3DateWidget()
                                   ),
                             Field("image", "upload", label=T("Scanned Copy")),
                             # This field can only be filled-out by specific roles
                             # Once this has been filled-out then the other fields are locked
                             organisation_id(label = T("Confirming Organization"),
                                             widget = S3OrganisationAutocompleteWidget(default_from_profile = True),
                                             comment = None,
                                             writable = False),
                             comments(),
                             *meta_fields())

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
            subtitle_list = T("Certifications"),
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
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Skill Equivalence"),
            title_display = T("Skill Equivalence Details"),
            title_list = T("Skill Equivalences"),
            title_update = T("Edit Skill Equivalence"),
            title_search = T("Search Skill Equivalences"),
            subtitle_create = T("Add Skill Equivalence"),
            subtitle_list = T("Skill Equivalences"),
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
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Course Certificate"),
            title_display = T("Course Certificate Details"),
            title_list = T("Course Certificates"),
            title_update = T("Edit Course Certificate"),
            title_search = T("Search Course Certificates"),
            subtitle_create = T("Add Course Certificate"),
            subtitle_list = T("Course Certificates"),
            label_list_button = T("List Course Certificates"),
            label_create_button = T("Add New Course Certificate"),
            label_delete_button = T("Delete Course Certificate"),
            msg_record_created = T("Course Certificate added"),
            msg_record_modified = T("Course Certificate updated"),
            msg_record_deleted = T("Course Certificate deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Course Certificates registered"))

        # =====================================================================
        # Mission Record
        #
        # These are an element of credentials:
        # - a minimum number of hours of active duty need to be done
        #   (e.g. every 6 months for Portuguese Bombeiros)
        #
        # This should be auto-populated out of Events
        # - as well as being updateable manually for off-system Events
        #

        tablename = "hrm_experience"
        table = define_table(tablename,
                             person_id(),
                             organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                             Field("start_date", "date",
                                   label=T("Start Date"),
                                   requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget(),
                                   ),
                             Field("end_date", "date",
                                   label=T("End Date"),
                                   requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                   represent = s3_date_represent,
                                   widget = S3DateWidget(),
                                   ),
                             Field("hours", "integer",
                                   label=T("Hours")),
                             Field("place",              # We could make this an event_id?
                                   label=T("Place")),
                             *meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Mission"),
            title_display = T("Mission Details"),
            title_list = T("Missions"),
            title_update = T("Edit Mission"),
            title_search = T("Search Missions"),
            subtitle_create = T("Add Mission"),
            subtitle_list = T("Missions"),
            label_list_button = T("List Missions"),
            label_create_button = T("Add New Mission"),
            label_delete_button = T("Delete Mission"),
            msg_record_created = T("Mission added"),
            msg_record_modified = T("Mission updated"),
            msg_record_deleted = T("Mission deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Missions registered"))

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(
                    hrm_skill_id = skill_id,
                    hrm_multi_skill_id = multi_skill_id
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def skill_type_default():
        """ Lookup the default skill_type """

        db = current.db
        s3db = current.s3db
        cache = current.cache
        settings = current.deployment_settings

        if settings.get_hrm_skill_types():
            # We have many - don't set a default
            default = None
        else:
            # We don't use skill_types so find the default
            table = s3db.hrm_skill_type
            query = (table.deleted == False)
            skill_type = db(query).select(table.id,
                                          limitby=(0, 1),
                                          cache=(cache.ram, 10)).first()
            if skill_type:
                default = skill_type.id
            else:
                # Create a default skill_type
                default = table.insert(name="Default")
        return default

    # -------------------------------------------------------------------------
    @staticmethod
    def competency_rating_comment():
        """ Define the comment for the HRM Competency Rating widget """

        T = current.T
        auth = current.auth
        s3 = current.response.s3
        session = current.session
        settings = current.deployment_settings

        system_roles = session.s3.system_roles
        ADMIN = system_roles.ADMIN

        if auth.s3_has_role(ADMIN):
            label_create = s3.crud_strings["hrm_competency_rating"].label_create_button
            comment = DIV(A(label_create,
                            _class="colorbox",
                            _href=URL(c="hrm",
                                      f="competency_rating",
                                      args="create",
                                      vars=dict(format="popup")),
                            _target="top",
                            _title=label_create),
                      DIV(DIV(_class="tooltip",
                              _title="%s|%s" % (label_create,
                                                T("Add a new competency rating to the catalog."))))),
        else:
            comment = DIV(_class="tooltip",
                          _title="%s|%s" % (T("Competency Rating"),
                                            T("Level of competency this person has with this skill.")))
        if settings.get_hrm_skill_types():
            s3.js_global.append("S3.i18n.no_ratings = '%s';" % T("No Ratings for Skill Type"))
            s3.jquery_ready.append("""
S3FilterFieldChange({
    'FilterField':	'skill_id',
    'Field':		'competency_id',
    'FieldResource':'competency',
    'FieldPrefix':	'hrm',
    'url':		 	S3.Ap.concat('/hrm/skill_competencies/'),
    'msgNoRecords':	S3.i18n.no_ratings
});""")
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

        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "hrm_competency":
            table = job.table
            person = "person_id" in job.data and job.data.person_id
            skill = "skill_id" in job.data and job.data.skill_id
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

        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "hrm_certificate":
            table = job.table
            name = "name" in job.data and job.data.name

            query = (table.name.lower().like('%%%s%%' % name.lower()))
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_certification_onaccept(record):
        """
            Ensure that Skills are Populated from Certifications
            - called both onaccept & ondelete

            @ToDo: Support having competencies populated without certifications!
        """

        db = current.db
        s3db = current.s3db

        # Deletion and update have a different format
        try:
            id = record.vars.id
            delete = False
        except:
            id = record.id
            delete = True

        table = s3db.hrm_certification
        data = table(table.id == id)

        if delete:
            # I really wish this weren't neccesary, but I really need to get that person_id!
            def reduction(a, b):
                a.update({b["f"]: b["k"]})
                return a
            data = reduce(reduction, eval(data.deleted_fk), {})

        person_id = data["person_id"]

        ctable = s3db.hrm_competency
        cstable = s3db.hrm_certificate_skill

        # Drop all existing competencies: This is a lot easier than selective deletion.
        db(ctable.person_id == person_id).delete()

        # Figure out which competencies we're _supposed_ to have.
        query = (table.person_id == person_id) & \
                (table.certificate_id == cstable.certificate_id) & \
                (cstable.skill_id == s3db.hrm_skill.id)
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
                    comments="Added by certification"
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

        s3db = current.s3db

        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "hrm_competency_rating":
            table = job.table
            stable = s3db.hrm_skill_type
            name = "name" in job.data and job.data.name
            skill = False
            for cjob in job.components:
                if cjob.tablename == "hrm_skill_type":
                    if "name" in cjob.data:
                        skill = cjob.data.name
            if skill == False:
                return

            query = (table.name.lower().like('%%%s%%' % name.lower())) & \
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

        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "hrm_course":
            table = job.table
            name = "name" in job.data and job.data.name

            query = (table.name.lower().like('%%%s%%' % name.lower()))
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

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

        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "hrm_skill":
            table = job.table
            name = "name" in job.data and job.data.name

            query = (table.name.lower().like('%%%s%%' % name.lower()))
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

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

        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "hrm_skill_type":
            table = job.table
            name = "name" in job.data and job.data.name

            query = (table.name.lower().like('%%%s%%' % name.lower()))
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

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

        # ignore this processing if the id is set
        if job.id:
            return
        if job.tablename == "hrm_training_event":
            table = job.table
            course_id = "course_id" in job.data and job.data.course_id
            site_id = "site_id" in job.data and job.data.site_id
            start_date = "start_date" in job.data and job.data.start_date

            query = (table.course_id == course_id) & \
                    (table.start_date == start_date)
            if site_id:
                query = query & (table.site_id == site_id)
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    def hrm_training_onaccept(self, record):
        """
            Ensure that Certifications are Populated from Trainings
            - called both onaccept & ondelete

            @ToDo: Support having certifications populated without trainings!
        """

        db = current.db
        s3db = current.s3db

        # Deletion and update have a different format
        try:
            id = record.vars.id
            delete = False
        except:
            id = record.id
            delete = True

        table = s3db.hrm_training
        data = table(table.id == id)

        if delete:
            # I really wish this weren't neccesary, but I really need to get that person_id!
            def reduction(a, b):
                a.update({b["f"]: b["k"]})
                return a
            data = reduce(reduction, eval(data.deleted_fk), {})

        person_id = data["person_id"]

        ctable = s3db.hrm_certification
        cctable = s3db.hrm_course_certificate
        ttable = s3db.hrm_training_event

        # Drop all existing certifications: This is a lot easier than selective deletion.
        db(ctable.person_id == person_id).delete()

        # Figure out which certifications we're _supposed_ to have.
        query = (table.person_id == person_id) & \
                (table.training_event_id == ttable.id) & \
                (ttable.course_id == cctable.course_id) & \
                (cctable.certificate_id == s3db.hrm_certificate.id)
        trainings = db(query).select()

        # Add these certifications back in.
        for training in trainings:
            certificate = training["hrm_certificate"]

            id = ctable.update_or_insert(
                    person_id=person_id,
                    certificate_id=certificate.id,
                    comments="Added by training"
                )
            # Propagate to Skills
            form = Storage()
            form.vars = Storage()
            form.vars.id = id
            self.hrm_certification_onaccept(form)


# =============================================================================
def hrm_hr_represent(id):
    """ Simple representation of HRs """

    db = current.db
    s3db = current.s3db

    repr_str = current.messages.NONE

    htable = s3db.hrm_human_resource
    ptable = s3db.pr_person

    query = (htable.id == id) & \
            (ptable.id == htable.person_id)
    person = db(query).select(ptable.first_name,
                              ptable.middle_name,
                              ptable.last_name,
                              limitby=(0, 1)).first()
    if person:
        repr_str = s3_fullname(person)

    return repr_str

# -------------------------------------------------------------------------
def hrm_human_resource_represent(id,
                                 show_link = False,
                                 none_value = None
                                 ):
    """ Representation of human resource records """

    db = current.db
    s3db = current.s3db
    request = current.request

    if none_value:
        repr_str = none_value
    else:
        repr_str = current.messages.NONE

    htable = s3db.hrm_human_resource
    ptable = s3db.pr_person
    otable = s3db.org_organisation

    query = (htable.id == id) & \
            (otable.id == htable.organisation_id)
    row = db(query).select(htable.job_title,
                           otable.name,
                           otable.acronym,
                           ptable.first_name,
                           ptable.middle_name,
                           ptable.last_name,
                           left=htable.on(ptable.id == htable.person_id),
                           limitby=(0, 1)).first()
    if row:
        org = row[str(otable)]
        repr_str = ", %s" % org.name
        if org.acronym:
            repr_str = ", %s" % org.acronym
        hr = row[str(htable)]
        if hr.job_title:
            repr_str = ", %s%s" % (hr.job_title, repr_str)
        person = row[str(ptable)]
        repr_str = "%s%s" % (s3_fullname(person), repr_str)
    if show_link:
        local_request = request
        local_request.extension = "html"
        return A(repr_str,
                 _href = URL(r = local_request,
                             c = "hrm",
                             f = "human_resource",
                             args = [id]
                             )
                 )
    else:
        return repr_str

# =============================================================================
def hrm_multi_skill_represent(opt):
    """
        Skill representation
        for multiple=True options
    """

    db = current.db
    s3db = current.s3db

    NONE = current.messages.NONE

    table = s3db.hrm_skill
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

# -------------------------------------------------------------------------
def hrm_certificate_represent(id):

    db = current.db
    s3db = current.s3db

    table = s3db.hrm_certificate
    #otable = s3db.org_organisation
    #query = (table.id == id) & \
    #        (table.organisation_id == otable.id)
    #cert = db(query).select(table.name,
    #                        otable.name,
    #                        limitby = (0, 1)).first()
    #if cert:
    #    represent = cert.hrm_certificate.name
    #    if cert.org_organisation:
    #        represent = "%s (%s)" % (represent,
    #                                 cert.org_organisation.name)
    query = (table.id == id)
    cert = db(query).select(table.name,
                            limitby = (0, 1)).first()
    if cert:
        represent = cert.name
    else:
        represent = current.messages.NONE

    return represent

# -------------------------------------------------------------------------
def hrm_training_event_represent(id):

    db = current.db
    s3db = current.s3db

    table = s3db.hrm_training_event
    ctable = s3db.hrm_course
    query = (table.id == id) & \
            (table.course_id == ctable.id)
    event = db(query).select(ctable.name,
                             table.site_id,
                             table.start_date,
                             #table.instructor,
                             limitby = (0, 1)).first()
    if event:
        site = table.site_id.represent(event.hrm_training_event.site_id)
        start_date = table.start_date.represent(event.hrm_training_event.start_date)
        represent = "%s (%s, %s)" % (event.hrm_course.name,
                                     site,
                                     start_date)
    else:
        represent = current.messages.NONE

    return represent

# =============================================================================
#def hrm_position_represent(id):
#    db = current.db
#    s3db = current.s3db
#    table = s3db.hrm_position
#    jtable = s3db.hrm_job_role
#    otable = s3db.org_organisation
#    query = (table.id == id) & \
#            (table.job_role_id == jtable.id)
#            (table.organisation_id == otable.id)
#    position = db(query).select(jtable.name,
#                                otable.name,
#                                limitby = (0, 1)).first()
#    if position:
#        represent = position.hrm_job_role.name
#        if position.org_organisation:
#            represent = "%s (%s)" % (represent,
#                                     position.org_organisation.name)
#    else:
#        represent = current.messages.NONE
#    return represent

# =============================================================================
class HRMVirtualFields:
    """ Virtual fields as dimension classes for reports """

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
            etable = s3db.hrm_training_event
            ctable = s3db.hrm_course
            query = (table.person_id == person_id) & \
                    (table.training_event_id == etable.id) & \
                    (etable.course_id == ctable.id)
            courses = current.db(query).select(ctable.name)
            if courses:
                output = []
                for course in courses:
                    output.append(course.name)
                    return output
        return current.messages.NONE

# =============================================================================
class HRMTrainingVirtualFields:
    """ Virtual fields as dimension classes for reports """

    extra_fields = ["training_event_id$start_date",
                    ]

    def month(self):
        """ Year/Month of the start date of the training event """
        try:
            start_date = self.hrm_training_event.start_date
        except AttributeError:
            # not available
            start_date = None
        if start_date:
            return "%s/%02d" % (start_date.year, start_date.month)
        else:
            return current.messages.NONE

    def year(self):
        # The year of the training event
        try:
            start_date = self.hrm_training_event.start_date
        except AttributeError:
            # not available
            start_date = None
        if start_date:
            return start_date.year
        else:
            return current.messages.NONE

# END =========================================================================
