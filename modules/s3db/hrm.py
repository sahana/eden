# -*- coding: utf-8 -*-

""" Sahana Eden Human Resources Management

    @copyright: 2011-2019 (c) Sahana Software Foundation
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

__all__ = ("S3HRModel",
           "S3HRSiteModel",
           "S3HRSalaryModel",
           "S3HRInsuranceModel",
           #"S3HRJobModel",
           "S3HRContractModel",
           "S3HRSkillModel",
           "S3HRTagModel",
           "S3HREventStrategyModel",
           "S3HREventProgrammeModel",
           "S3HREventProjectModel",
           "S3HREventAssessmentModel",
           "S3HRAppraisalModel",
           "S3HRExperienceModel",
           "S3HRAwardModel",
           "S3HRDisciplinaryActionModel",
           "S3HRProgrammeModel",
           "S3HRShiftModel",
           "hrm_AssignMethod",
           "hrm_HumanResourceRepresent",
           "hrm_TrainingEventRepresent",
           #"hrm_position_represent",
           "hrm_compose",
           "hrm_map_popup",
           "hrm_rheader",
           "hrm_competency_controller",
           "hrm_credential_controller",
           "hrm_experience_controller",
           "hrm_group_controller",
           "hrm_human_resource_controller",
           "hrm_person_controller",
           "hrm_training_controller",
           "hrm_training_event_controller",
           "hrm_xls_list_fields",
           "hrm_CV",
           "hrm_Record",
           "hrm_configure_pr_group_membership",
           "hrm_human_resource_onaccept",
           #"hrm_competency_list_layout",
           #"hrm_credential_list_layout",
           #"hrm_experience_list_layout",
           #"hrm_training_list_layout",
           "hrm_human_resource_filters",
           )

import datetime
import json

from gluon import *
from gluon.sqlhtml import RadioWidget
from gluon.storage import Storage

from ..s3 import *
from s3compat import long
from s3layouts import S3PopupLink

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class S3HRModel(S3Model):

    names = ("hrm_department",
             "hrm_department_id",
             "hrm_job_title",
             "hrm_job_title_id",
             "hrm_job_title_human_resource",
             "hrm_human_resource",
             "hrm_human_resource_id",
             "hrm_type_opts",
             "hrm_human_resource_represent",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        auth = current.auth
        settings = current.deployment_settings

        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        AUTOCOMPLETE_HELP = messages.AUTOCOMPLETE_HELP
        #ORGANISATION = messages.ORGANISATION

        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        organisation_id = self.org_organisation_id

        root_org = auth.root_org()
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        mix_staff = settings.get_hrm_mix_staff()

        request = current.request
        controller = request.controller
        group = request.get_vars.get("group", None)
        if not group:
            if mix_staff:
                group = None
            elif controller == "vol":
                group = "volunteer"
            elif controller == "deploy":
                group = None
            #elif controller in ("hrm", "org", "inv", "cr", "hms", "req"):
            else:
                group = "staff"

        # =====================================================================
        # Departments
        #
        tablename = "hrm_department"
        define_table(tablename,
                     Field("name", notnull=True, length=64,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     organisation_id(default = root_org,
                                     readable = is_admin,
                                     writable = is_admin,
                                     ),
                     s3_comments(label = T("Description"),
                                 comment = None,
                                 ),
                     *s3_meta_fields())

        label_create = T("Create Department")
        crud_strings[tablename] = Storage(
            label_create = label_create,
            title_display = T("Department Details"),
            title_list = T("Department Catalog"),
            title_update = T("Edit Department"),
            title_upload = T("Import Departments"),
            label_list_button = T("List Departments"),
            label_delete_button = T("Delete Department"),
            msg_record_created = T("Department added"),
            msg_record_modified = T("Department updated"),
            msg_record_deleted = T("Department deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        represent = S3Represent(lookup=tablename)
        department_id = S3ReusableField("department_id", "reference %s" % tablename,
            label = T("Department / Unit"),
            ondelete = "SET NULL",
            represent = represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "hrm_department.id",
                                  represent,
                                  filterby="organisation_id",
                                  filter_opts=filter_opts,
                                  )),
            sortby = "name",
            comment = S3PopupLink(c = "vol" if group == "volunteer" else "hrm",
                                  f = "department",
                                  label = label_create,
                                  ),
            )

        configure("hrm_department",
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("organisation_id",),
                                            ),
                  )

        # =====================================================================
        # Job Titles (Mayon: StaffResourceType)
        #
        STAFF = settings.get_hrm_staff_label()
        if settings.has_module("vol"):
            hrm_types = True
            hrm_type_opts = {1: STAFF,
                             2: T("Volunteer"),
                             3: T("Both")
                             }
            if group == "staff":
                hrm_type_default = 1
            elif group == "volunteer":
                hrm_type_default = 2
            else:
                hrm_type_default = 3
        else:
            hrm_types = False
            hrm_type_opts = {1: STAFF}
            hrm_type_default = 1

        if settings.get_hrm_job_title_deploy():
            hrm_types = True
            hrm_type_opts[4] = T("Deployment")

        if group == "volunteer":
            not_filter_opts = (1, 4)
            code_label = T("Volunteer ID")
            departments = settings.get_hrm_vol_departments()
            job_titles = settings.get_hrm_vol_roles()
        elif mix_staff:
            not_filter_opts = (4,)
            code_label = T("Organization ID")
            departments = settings.get_hrm_staff_departments()
            job_titles = True
        else:
            # Staff
            not_filter_opts = (2, 4)
            code_label = T("Staff ID")
            departments = settings.get_hrm_staff_departments()
            job_titles = True

        org_dependent_job_titles = settings.get_hrm_org_dependent_job_titles()

        tablename = "hrm_job_title"
        define_table(tablename,
                     Field("name", notnull=True,
                           length=64,    # Mayon compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     # Enable in templates as-required
                     self.org_region_id(readable = False,
                                        writable = False,
                                        ),
                     organisation_id(default = root_org if org_dependent_job_titles else None,
                                     readable = is_admin if org_dependent_job_titles else False,
                                     writable = is_admin if org_dependent_job_titles else False,
                                     ),
                     Field("type", "integer",
                           default = hrm_type_default,
                           label = T("Type"),
                           readable = hrm_types,
                           writable = hrm_types,
                           represent = lambda opt: \
                            hrm_type_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(hrm_type_opts),
                           ),
                     s3_comments(comment = None,
                                 label = T("Description"),
                                 ),
                     *s3_meta_fields())

        if group == "volunteer":
            label = T("Volunteer Role")
            label_create = T("Create Volunteer Role")
            tooltip = T("The volunteer's role")
            crud_strings[tablename] = Storage(
                label_create = label_create,
                title_display = T("Volunteer Role Details"),
                title_list = T("Volunteer Role Catalog"),
                title_update = T("Edit Volunteer Role"),
                label_list_button = T("List Volunteer Roles"),
                label_delete_button = T("Delete Volunteer Role"),
                msg_record_created = T("Volunteer Role added"),
                msg_record_modified = T("Volunteer Role updated"),
                msg_record_deleted = T("Volunteer Role deleted"),
                msg_list_empty = T("Currently no entries in the catalog"))
        else:
            label = T("Job Title")
            label_create = T("Create Job Title")
            tooltip = T("The staff member's official job title")
            crud_strings[tablename] = Storage(
                label_create = label_create,
                title_display = T("Job Title Details"),
                title_list = T("Job Title Catalog"),
                title_update = T("Edit Job Title"),
                label_list_button = T("List Job Titles"),
                label_delete_button = T("Delete Job Title"),
                msg_record_created = T("Job Title added"),
                msg_record_modified = T("Job Title updated"),
                msg_record_deleted = T("Job Title deleted"),
                msg_list_empty = T("Currently no entries in the catalog"))

        represent = S3Represent(lookup=tablename, translate=True)

        if org_dependent_job_titles:
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "hrm_job_title.id",
                                  represent,
                                  filterby="organisation_id",
                                  filter_opts=filter_opts,
                                  not_filterby="type",
                                  not_filter_opts=not_filter_opts,
                                  ))
        else:
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "hrm_job_title.id",
                                  represent,
                                  not_filterby="type",
                                  not_filter_opts=not_filter_opts,
                                  ))

        job_title_id = S3ReusableField("job_title_id", "reference %s" % tablename,
            label = label,
            ondelete = "SET NULL",
            represent = represent,
            requires = requires,
            sortby = "name",
            comment = S3PopupLink(c = "vol" if group == "volunteer" else "hrm",
                                  f = "job_title",
                                  # Add this for usecases where this is no special controller for an options lookup
                                  #vars = {"prefix": "hrm",
                                  #        "parent": "human_resource",
                                  #        },
                                  label = label_create,
                                  title = label,
                                  tooltip = tooltip,
                                  ),
            )

        configure("hrm_job_title",
                  deduplicate = self.hrm_job_title_duplicate,
                  onvalidation = self.hrm_job_title_onvalidation,
                  )

        # =====================================================================
        # Human Resource
        #
        # People who are either Staff or Volunteers
        #
        # @ToDo: Move Volunteers to a separate resource?: vol_volunteer
        #
        # @ToDo: Allocation Status for Events (link table)
        #

        STAFF = settings.get_hrm_staff_label()

        # NB These numbers are hardcoded into KML Export stylesheet
        hrm_type_opts = {1: STAFF,
                         2: T("Volunteer"),
                         }

        hrm_status_opts = {1: T("Active"),
                           2: T("Resigned"),   # They left of their own accord
                           3: T("Terminated"), # Org terminated their contract
                           4: T("Died"),
                           }

        organisation_label = settings.get_hrm_organisation_label()
        multiple_contracts = settings.get_hrm_multiple_contracts()
        use_code = settings.get_hrm_use_code()

        if group == "volunteer" or s3.bulk or not group:
            # Volunteers don't have a Site
            # Don't set a Site for Bulk Imports unless set explicitly
            default_site = None
        else:
            default_site = auth.user.site_id if auth.is_logged_in() else None

        if settings.get_org_autocomplete():
            org_widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
        else:
            org_widget = None

        if settings.get_org_site_autocomplete():
            site_widget = S3SiteAutocompleteWidget()
            site_comment = DIV(_class="tooltip",
                               _title="%s|%s" % (T("Requested By Facility"),
                                                 AUTOCOMPLETE_HELP))
        else:
            site_widget = None
            site_comment = None

        tablename = "hrm_human_resource"
        realms = auth.permission.permitted_realms(tablename, method="create")
        define_table(tablename,
                     # Instances
                     super_link("track_id", "sit_trackable"),
                     super_link("doc_id", "doc_entity"),
                     organisation_id(
                        empty = not settings.get_hrm_org_required(),
                        label = organisation_label,
                        requires = self.org_organisation_requires(required=True,
                                                                  realms=realms),
                        widget = org_widget,
                     ),
                     super_link("site_id", "org_site",
                                comment = site_comment,
                                default = default_site,
                                instance_types = auth.org_site_types,
                                #empty = False,
                                label = settings.get_org_site_label(),
                                ondelete = "SET NULL",
                                orderby = "org_site.name",
                                not_filterby = "obsolete",
                                not_filter_opts = (True,),
                                readable = True,
                                writable = True,
                                realms = realms,
                                represent = self.org_site_represent,
                                widget = site_widget,
                                ),
                     self.pr_person_id(
                        comment = None,
                        empty = False,
                        ondelete = "CASCADE",
                        widget = S3AddPersonWidget(controller="hrm"),
                        ),
                     Field("type", "integer",
                           default = 1,
                           label = T("Type"),
                           represent = lambda opt: \
                                       hrm_type_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(hrm_type_opts,
                                                zero=None),
                           widget = RadioWidget.widget,
                           # Normally set via the Controller we create from
                           readable = mix_staff,
                           writable = mix_staff,
                           ),
                     Field("code",
                           label = code_label,
                           represent = lambda v: v or messages["NONE"],
                           readable = use_code,
                           writable = use_code,
                           ),
                     job_title_id(readable = job_titles,
                                  writable = job_titles,
                                  ),
                     department_id(readable = departments,
                                   writable = departments,
                                   ),
                     Field("essential", "boolean",
                           label = T("Essential Staff?"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Essential Staff?"),
                                                           T("If the person counts as essential staff when evacuating all non-essential staff."))),
                           ),
                     # Contract
                     s3_date("start_date",
                             label = T("Start Date"),
                             set_min = "#hrm_human_resource_end_date",
                             ),
                     s3_date("end_date",
                             label = T("End Date"),
                             set_max = "#hrm_human_resource_start_date",
                             start_field = "hrm_human_resource_start_date",
                             default_interval = 12,
                             ),
                     # Current status
                     Field("status", "integer",
                           default = 1,
                           label = T("Status"),
                           represent = lambda opt: \
                            hrm_status_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(hrm_status_opts,
                                                zero=None),
                           ),
                     # Base location + Site
                     self.gis_location_id(label =T("Base Location"),
                                          readable = False,
                                          writable = False,
                                          ),
                     Field("org_contact", "boolean",
                           label = T("Organization Contact"),
                           represent = s3_yes_no_represent,
                           readable = False,
                           writable = False,
                           ),
                     Field("site_contact", "boolean",
                           label = T("Facility Contact"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # @ToDo: Move this configurability to templates rather than lots of deployment_settings
        if STAFF == T("Contacts"):
            contacts = True
            crud_strings["hrm_staff"] = Storage(
                label_create = T("Create Contact"),
                title_display = T("Contact Details"),
                title_list = STAFF,
                title_update = T("Edit Contact Details"),
                title_upload = T("Import Contacts"),
                label_list_button = T("List Contacts"),
                label_delete_button = T("Delete Contact"),
                msg_record_created = T("Contact added"),
                msg_record_modified = T("Contact Details updated"),
                msg_record_deleted = T("Contact deleted"),
                msg_list_empty = T("No Contacts currently registered"))
        else:
            contacts = False
            crud_strings["hrm_staff"] = Storage(
                label_create = T("Create Staff Member"),
                title_display = T("Staff Member Details"),
                title_list = STAFF,
                title_update = T("Edit Staff Member Details"),
                title_upload = T("Import Staff"),
                label_list_button = T("List Staff Members"),
                label_delete_button = T("Delete Staff Member"),
                msg_record_created = T("Staff Member added"),
                msg_record_modified = T("Staff Member Details updated"),
                msg_record_deleted = T("Staff Member deleted"),
                msg_list_empty = T("No Staff currently registered"))

        crud_strings["hrm_volunteer"] = Storage(
            label_create = T("Create Volunteer"),
            title_display = T("Volunteer Details"),
            title_list = T("Volunteers"),
            title_update = T("Edit Volunteer Details"),
            title_upload = T("Import Volunteers"),
            label_list_button = T("List Volunteers"),
            label_delete_button = T("Delete Volunteer"),
            msg_record_created = T("Volunteer added"),
            msg_record_modified = T("Volunteer Details updated"),
            msg_record_deleted = T("Volunteer deleted"),
            msg_list_empty = T("No Volunteers currently registered"))

        hrm_human_resource_represent = hrm_HumanResourceRepresent(show_link=True)

        if group == "staff":
            label = STAFF
            crud_strings[tablename] = crud_strings["hrm_staff"]
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "hrm_human_resource.id",
                                  hrm_human_resource_represent,
                                  sort=True,
                                  filterby="type",
                                  filter_opts=(1,)
                                  ))
            widget = S3HumanResourceAutocompleteWidget(group="staff")
        elif group == "volunteer":
            label = T("Volunteer")
            crud_strings[tablename] = crud_strings["hrm_volunteer"]
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "hrm_human_resource.id",
                                  hrm_human_resource_represent,
                                  sort=True,
                                  filterby="type",
                                  filter_opts=(2,)
                                  ))
            widget = S3HumanResourceAutocompleteWidget(group="volunteer")
        else:
            label = T("Human Resource")
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "hrm_human_resource.id",
                                  hrm_human_resource_represent,
                                  sort=True
                                  ))
            widget = S3HumanResourceAutocompleteWidget()
            if contacts:
                crud_strings[tablename] = crud_strings["hrm_staff"]
            else:
                crud_strings[tablename] = Storage(
                    label_create = T("Create Staff or Volunteer"),
                    title_display = T("Human Resource Details"),
                    title_list = T("Staff & Volunteers"),
                    title_update = T("Edit Record"),
                    title_upload =T("Search Staff & Volunteers"),
                    label_list_button = T("List Staff & Volunteers"),
                    label_delete_button = T("Delete Record"),
                    msg_record_created = T("Human Resource added"),
                    msg_record_modified = T("Record updated"),
                    msg_record_deleted = T("Record deleted"),
                    msg_list_empty = T("No staff or volunteers currently registered"))

        comment = S3PopupLink(c = "vol" if group == "volunteer" else "hrm",
                              f = group or "staff",
                              vars = {"child": "human_resource_id"},
                              label = crud_strings["hrm_%s" % group].label_create if group else \
                                      crud_strings[tablename].label_create,
                              title = label,
                              tooltip = AUTOCOMPLETE_HELP,
                              )

        human_resource_id = S3ReusableField("human_resource_id", "reference %s" % tablename,
                                            label = label,
                                            ondelete = "RESTRICT",
                                            represent = hrm_human_resource_represent,
                                            requires = requires,
                                            sortby = ["type", "status"],
                                            widget = widget,
                                            comment = comment,
                                            )

        # Custom Method for S3HumanResourceAutocompleteWidget and S3AddPersonWidget
        set_method = self.set_method
        set_method("hrm", "human_resource",
                   method = "search_ac",
                   action = self.hrm_search_ac)

        set_method("hrm", "human_resource",
                   method = "lookup",
                   action = self.hrm_lookup)

        # Components
        add_components(tablename,
                       # Contact Data
                       pr_contact = (# Email
                                     {"name": "email",
                                      "link": "pr_person",
                                      "joinby": "id",
                                      "key": "pe_id",
                                      "fkey": "pe_id",
                                      "pkey": "person_id",
                                      "filterby": {
                                          "contact_method": "EMAIL",
                                          },
                                      },
                                     # Mobile Phone
                                     {"name": "phone",
                                      "link": "pr_person",
                                      "joinby": "id",
                                      "key": "pe_id",
                                      "fkey": "pe_id",
                                      "pkey": "person_id",
                                      "filterby": {
                                          "contact_method": "SMS",
                                          },
                                      },
                                     ),
                        pr_contact_emergency = {"link": "pr_person",
                                                "joinby": "id",
                                                "key": "pe_id",
                                                "fkey": "pe_id",
                                                "pkey": "person_id",
                                                },
                        pr_address = ({"name": "home_address",
                                       "link": "pr_person",
                                       "joinby": "id",
                                       "key": "pe_id",
                                       "fkey": "pe_id",
                                       "pkey": "person_id",
                                       "filterby": {
                                           "type": "1",
                                           },
                                       },
                                      ),
                        # Experience & Skills
                        hrm_appraisal = {"link": "pr_person",
                                         "joinby": "id",
                                         "key": "id",
                                         "fkey": "person_id",
                                         "pkey": "person_id",
                                         },
                        hrm_certification = {"link": "pr_person",
                                             "joinby": "id",
                                             "key": "id",
                                             "fkey": "person_id",
                                             "pkey": "person_id",
                                             },
                        hrm_competency = {"link": "pr_person",
                                          "joinby": "id",
                                          "key": "id",
                                          "fkey": "person_id",
                                          "pkey": "person_id",
                                          },
                        hrm_contract = {"joinby": "human_resource_id",
                                        "multiple": multiple_contracts,
                                        },
                        hrm_credential = {"link": "pr_person",
                                          "joinby": "id",
                                          "key": "id",
                                          "fkey": "person_id",
                                          "pkey": "person_id",
                                          },
                        pr_education = {"link": "pr_person",
                                        "joinby": "id",
                                        "key": "id",
                                        "fkey": "person_id",
                                        "pkey": "person_id",
                                        },
                        hrm_experience = {"link": "pr_person",
                                          "joinby": "id",
                                          "key": "id",
                                          "fkey": "person_id",
                                          "pkey": "person_id",
                                          },
                        hrm_insurance = "human_resource_id",
                        hrm_salary = "human_resource_id",
                        hrm_training = {"link": "pr_person",
                                        "joinby": "id",
                                        "key": "id",
                                        "fkey": "person_id",
                                        "pkey": "person_id",
                                        },
                        hrm_trainings = {"link": "pr_person",
                                         "joinby": "id",
                                         "key": "id",
                                         "fkey": "person_id",
                                         "pkey": "person_id",
                                         "multiple": False,
                                         },
                        # Organisation Groups
                        org_group_person = {"link": "pr_person",
                                            "joinby": "id",
                                            "key": "id",
                                            "fkey": "person_id",
                                            "pkey": "person_id",
                                            },
                        # Projects
                        project_project = {"link": "project_human_resource_project",
                                           "joinby": "human_resource_id",
                                           "key": "project_id",
                                           },
                        # Application(s) for Deployment
                        deploy_application = "human_resource_id",
                        # Assignments
                        deploy_assignment = "human_resource_id",
                        # Hours
                        #hrm_hours = "human_resource_id",
                        # Tags
                        hrm_human_resource_tag = {"name": "tag",
                                                  "joinby": "human_resource_id",
                                                  },
                        )

        # Optional Components
        teams = settings.get_hrm_teams()
        if teams:
            add_components(tablename,
                           # Team Memberships
                           pr_group_membership = {"link": "pr_person",
                                                  "joinby": "id",
                                                  "key": "id",
                                                  "fkey": "person_id",
                                                  "pkey": "person_id",
                                                  },
                           )

        if group in ("volunteer", None) or mix_staff:
            add_components(tablename,
                           # Programmes
                           hrm_programme_hours = {"link": "pr_person",
                                                  "joinby": "id",
                                                  "key": "id",
                                                  "fkey": "person_id",
                                                  "pkey": "person_id",
                                                  },
                           # Availability
                           pr_person_availability = {"link": "pr_person",
                                                     "joinby": "id",
                                                     "key": "id",
                                                     "fkey": "person_id",
                                                     "pkey": "person_id",
                                                     # Will need tochange in future
                                                     "multiple": False,
                                                     },
                           # Volunteer Details
                           vol_details = {"joinby": "human_resource_id",
                                          "multiple": False,
                                          },
                           # Volunteer Cluster
                           vol_volunteer_cluster = {"joinby": "human_resource_id",
                                                    "multiple": False,
                                                    },
                           )

        if settings.get_hrm_multiple_job_titles():
            add_components(tablename,
                           # Job Titles
                           hrm_job_title_human_resource = "human_resource_id",
                           )

        crud_fields = ["organisation_id",
                       "person_id",
                       "start_date",
                       "end_date",
                       "status",
                       ]

        if use_code:
            crud_fields.insert(2, "code")

        filter_widgets = hrm_human_resource_filters(resource_type = group,
                                                    hrm_type_opts = hrm_type_opts)

        report_fields = ["organisation_id",
                         "person_id",
                         "person_id$gender",
                         (T("Training"), "training.course_id"),
                         "location_id$L1",
                         "location_id$L2",
                         ]

        if settings.get_org_branches():
            report_fields.insert(1, (settings.get_hrm_root_organisation_label(), "organisation_id$root_organisation"))

        if teams:
            report_fields.append((T(teams), "group_membership.group_id"))

        if mix_staff:
            crud_fields.insert(1, "site_id")
            crud_fields.insert(2, "type")
            posn = 4
            if use_code:
                posn += 1
            crud_fields.insert(posn, "job_title_id")
            if settings.get_hrm_staff_departments() or \
               settings.get_hrm_vol_departments():
                crud_fields.insert(posn, "department_id")
            vol_experience = settings.get_hrm_vol_experience()
            if vol_experience in ("programme", "both"):
                crud_fields.insert(posn, S3SQLInlineComponent("programme_hours",
                                                              label = "",
                                                              fields = ["programme_id"],
                                                              link = False,
                                                              multiple = False,
                                                              ))
            elif vol_experience == "activity":
                report_fields.append("person_id$activity_hours.activity_hours_activity_type.activity_type_id")
            crud_fields.append("details.volunteer_type")
            if settings.get_hrm_vol_availability_tab() is False and \
               settings.get_pr_person_availability_options() is not None:
                crud_fields.append("person_availability.options")
            crud_fields.append("details.card")
            vol_active = settings.get_hrm_vol_active()
            if vol_active and not callable(vol_active):
                # Set manually
                crud_fields.append("details.active")
            report_fields.extend(("site_id",
                                  "department_id",
                                  "job_title_id",
                                  (T("Age Group"), "person_id$age_group"),
                                  "person_id$education.level",
                                  ))
            # Needed for Age Group VirtualField to avoid extra DB calls
            report_fields_extra = ["person_id$date_of_birth"]
        elif group == "volunteer":
            # This gets copied to hrm_human_resource.location_id onaccept, faster to lookup without joins
            #location_context = "person_id$address.location_id" # When not using S3Track()
            if settings.get_hrm_vol_roles():
                crud_fields.insert(2, "job_title_id")
                report_fields.append("job_title_id")
            if settings.get_hrm_vol_departments():
                crud_fields.insert(4, "department_id")
                report_fields.append("department_id")
            vol_experience = settings.get_hrm_vol_experience()
            if vol_experience in ("programme", "both"):
                crud_fields.insert(2, S3SQLInlineComponent("programme_hours",
                                                           label = "",
                                                           fields = ["programme_id"],
                                                           link = False,
                                                           multiple = False,
                                                           ))
            elif vol_experience == "activity":
                report_fields.append("person_id$activity_hours.activity_hours_activity_type.activity_type_id")
            crud_fields.append("details.volunteer_type")
            if settings.get_hrm_vol_availability_tab() is False and \
               settings.get_pr_person_availability_options() is not None:
                crud_fields.append("person_availability.options")
            crud_fields.extend(("details.card",
                                # @ToDo: Move these to the IFRC Template (PH RC only people to use this)
                                "volunteer_cluster.vol_cluster_type_id",
                                "volunteer_cluster.vol_cluster_id",
                                "volunteer_cluster.vol_cluster_position_id",
                                ))
            vol_active = settings.get_hrm_vol_active()
            if vol_active and not callable(vol_active):
                # Set manually
                crud_fields.append("details.active")
            report_fields.extend(((T("Age Group"), "person_id$age_group"),
                                  "person_id$education.level",
                                  ))
            # Needed for Age Group VirtualField to avoid extra DB calls
            report_fields_extra = ["person_id$date_of_birth"]
        else:
            # Staff
            # This gets copied to hrm_human_resource.location_id onaccept, faster to lookup without joins
            #location_context = "site_id$location_id" # When not using S3Track()
            crud_fields.insert(1, "site_id")
            posn = 3
            if use_code:
                posn += 1
            crud_fields.insert(posn, "job_title_id")
            if settings.get_hrm_staff_departments():
                crud_fields.insert(posn, "department_id")
            report_fields.extend(("site_id",
                                  "department_id",
                                  "job_title_id",
                                  ))
            report_fields_extra = []

        # Redirect to the Details tabs after creation
        if controller in ("hrm", "vol"):
            hrm_url = URL(c=controller, f="person",
                          vars={"human_resource.id":"[id]"})
        else:
            # Being added as a component to Org, Site or Project
            hrm_url = None

        # Custom Form
        s3.hrm = Storage(crud_fields = crud_fields) # Store fields for easy ability to modify later
        crud_form = S3SQLCustomForm(*crud_fields)

        if settings.get_hrm_org_required():
            mark_required = ("organisation_id",)
        else:
            mark_required = None

        configure(tablename,
                  context = {#"location": location_context,
                             "organisation": "organisation_id",
                             "person": "person_id",
                             "project": "project.id",
                             "site": "site_id",
                             },
                  create_next = hrm_url,
                  crud_form = crud_form,
                  # This allows only one HR record per person and organisation,
                  # if multiple HR records of the same person with the same org
                  # are desired, then this needs an additional criteria in the
                  # query (e.g. job title, or type):
                  deduplicate = S3Duplicate(primary = ("person_id",),
                                            secondary = ("organisation_id",),
                                            ignore_deleted = True,
                                            ),
                  deletable = settings.get_hrm_deletable(),
                  #extra_fields = ["person_id"]
                  filter_widgets = filter_widgets,
                  mark_required = mark_required,
                  onaccept = hrm_human_resource_onaccept,
                  ondelete = self.hrm_human_resource_ondelete,
                  realm_components = ("presence",),
                  report_fields = report_fields_extra,
                  report_options = Storage(
                    rows = report_fields,
                    cols = report_fields,
                    fact = report_fields,
                    methods = ("count", "list",),
                    defaults = Storage(
                        rows = "organisation_id",
                        cols = "training.course_id",
                        fact = "count(person_id)",
                        )
                    ),
                  # Default summary
                  summary = [{"name": "addform",
                              "common": True,
                              "widgets": [{"method": "create"}],
                             },
                             {"name": "table",
                              "label": "Table",
                              "widgets": [{"method": "datatable"}]
                              },
                             {"name": "report",
                              "label": "Report",
                              "widgets": [{"method": "report",
                                           "ajax_init": True}]
                              },
                             {"name": "map",
                              "label": "Map",
                              "widgets": [{"method": "map",
                                           "ajax_init": True}],
                              },
                             ],
                  super_entity = ("sit_trackable", "doc_entity"),
                  #update_next = hrm_url,
                  update_realm = True,
                  )

        # =====================================================================
        # Job Titles <>  Human Resources link table
        #
        tablename = "hrm_job_title_human_resource"
        define_table(tablename,
                     human_resource_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     job_title_id(empty = False,
                                  ondelete = "CASCADE",
                                  ),
                     Field("main", "boolean",
                           default = True,
                           label = T("Main?"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_date(label = T("Start Date")),
                     s3_date("end_date",
                             label = T("End Date"),
                             ),
                     s3_comments(),
                     *s3_meta_fields())

        configure("hrm_job_title_human_resource",
                  onaccept = self.hrm_job_title_human_resource_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"hrm_department_id": department_id,
                "hrm_job_title_id": job_title_id,
                "hrm_human_resource_id": human_resource_id,
                "hrm_status_opts": hrm_status_opts,
                "hrm_type_opts": hrm_type_opts,
                "hrm_human_resource_represent": hrm_human_resource_represent,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return {"hrm_department_id": lambda **attr: dummy("department_id"),
                "hrm_job_title_id": lambda **attr: dummy("job_title_id"),
                "hrm_human_resource_id": lambda **attr: dummy("human_resource_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_job_title_duplicate(item):
        """
            Update detection for hrm_job_title

            @param item: the S3ImportItem
        """

        data = item.data
        name = data.get("name", None)
        if current.deployment_settings.get_hrm_org_dependent_job_titles():
            org = data.get("organisation_id", None)
        else:
            org = None
        role_type = data.get("type", None)

        table = item.table
        query = (table.name.lower() == s3_unicode(name).lower())
        if org:
            query  = query & (table.organisation_id == org)
        if role_type:
            query  = query & (table.type == role_type)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_job_title_onvalidation(form):
        """
            Ensure Job Titles are not Org-specific unless configured to be so
        """

        if not current.deployment_settings.get_hrm_org_dependent_job_titles():
            form.vars["organisation_id"] = None

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_job_title_human_resource_onaccept(form):
        """
            Record creation post-processing

            If the job title is the main, set the
            human_resource.job_title_id accordingly
        """

        formvars = form.vars

        if formvars.main:
            # Read the record
            # (safer than relying on vars which might be missing on component tabs)
            db = current.db
            ltable = db.hrm_job_title_human_resource
            record = db(ltable.id == formvars.id).select(
                                                    ltable.human_resource_id,
                                                    ltable.job_title_id,
                                                    limitby = (0, 1),
                                                    ).first()

            # Set the HR's job_title_id to the new job title
            htable = db.hrm_human_resource
            db(htable.id == record.human_resource_id).update(
                                            job_title_id = record.job_title_id,
                                            )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_search_ac(r, **attr):
        """
            JSON search method for S3HumanResourceAutocompleteWidget and S3AddPersonWidget
            - full name search
            - include Organisation & Job Role in the output
        """

        resource = r.resource
        response = current.response

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = current.request.get_vars

        # JQueryUI Autocomplete uses "term"
        # old JQuery Autocomplete uses "q"
        # what uses "value"?
        value = _vars.term or _vars.value or _vars.q or None

        if not value:
            r.error(400, "No value provided!")

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = s3_unicode(value).lower()

        if " " in value:
            # Multiple words
            # - check for match of first word against first_name
            # - & second word against either middle_name or last_name
            value1, value2 = value.split(" ", 1)
            value2 = value2.strip()
            query = ((FS("person_id$first_name").lower().like(value1 + "%")) & \
                    ((FS("person_id$middle_name").lower().like(value2 + "%")) | \
                     (FS("person_id$last_name").lower().like(value2 + "%"))))
        else:
            # Single word - check for match against any of the 3 names
            value = value.strip()
            query = ((FS("person_id$first_name").lower().like(value + "%")) | \
                     (FS("person_id$middle_name").lower().like(value + "%")) | \
                     (FS("person_id$last_name").lower().like(value + "%")))

        resource.add_filter(query)

        settings = current.deployment_settings
        limit = int(_vars.limit or 0)
        MAX_SEARCH_RESULTS = settings.get_search_max_results()
        if (not limit or limit > MAX_SEARCH_RESULTS) and resource.count() > MAX_SEARCH_RESULTS:
            output = [
                {"label": str(current.T("There are more than %(max)s results, please input more characters.") % \
                    {"max": MAX_SEARCH_RESULTS}),
                 },
                ]
        else:
            fields = ["id",
                      "person_id$first_name",
                      "person_id$middle_name",
                      "person_id$last_name",
                      "job_title_id$name",
                      ]
            show_orgs = settings.get_hrm_show_organisation()
            if show_orgs:
                fields.append("organisation_id$name")

            name_format = settings.get_pr_name_format()
            test = name_format % {"first_name": 1,
                                  "middle_name": 2,
                                  "last_name": 3,
                                  }
            test = "".join(ch for ch in test if ch in ("1", "2", "3"))
            if test[:1] == "1":
                orderby = "pr_person.first_name"
            elif test[:1] == "2":
                orderby = "pr_person.middle_name"
            else:
                orderby = "pr_person.last_name"
            rows = resource.select(fields,
                                   start=0,
                                   limit=limit,
                                   orderby=orderby)["rows"]

            output = []
            iappend = output.append
            for row in rows:
                name = Storage(first_name=row["pr_person.first_name"],
                               middle_name=row["pr_person.middle_name"],
                               last_name=row["pr_person.last_name"],
                               )
                name = s3_fullname(name)
                item = {"id"    : row["hrm_human_resource.id"],
                        "name"  : name,
                        }
                if show_orgs:
                    item["org"] = row["org_organisation.name"]
                job_title = row.get("hrm_job_title.name", None)
                if job_title:
                    item["job"] = job_title
                iappend(item)

        response.headers["Content-Type"] = "application/json"
        return json.dumps(output, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_lookup(r, **attr):
        """
            JSON lookup method for S3AddPersonWidget
        """

        hrm_id = r.id
        if not hrm_id:
            r.error(400, "No id provided!")

        db = current.db
        s3db = current.s3db
        settings = current.deployment_settings
        request_dob = settings.get_pr_request_dob()
        request_gender = settings.get_pr_request_gender()
        home_phone = settings.get_pr_request_home_phone()

        htable = db.hrm_human_resource
        ptable = db.pr_person
        ctable = s3db.pr_contact
        fields = [htable.organisation_id,
                  ptable.pe_id,
                  # We have these already from the search_ac
                  #ptable.first_name,
                  #ptable.middle_name,
                  #ptable.last_name,
                  ]
        separate_name_fields = settings.get_pr_separate_name_fields()
        if separate_name_fields:
            middle_name = separate_name_fields == 3
            fields += [ptable.first_name,
                       ptable.middle_name,
                       ptable.last_name,
                       ]

        left = None
        if request_dob:
            fields.append(ptable.date_of_birth)
        if request_gender:
            fields.append(ptable.gender)
        if current.request.controller == "vol":
            dtable = s3db.pr_person_details
            fields.append(dtable.occupation)
            left = dtable.on(dtable.person_id == ptable.id)

        query = (htable.id == hrm_id) & \
                (ptable.id == htable.person_id)
        row = db(query).select(left=left,
                               *fields).first()
        if left:
            occupation = row["pr_person_details.occupation"]
        else:
            occupation = None
        organisation_id = row["hrm_human_resource.organisation_id"]
        row = row["pr_person"]
        #first_name = row.first_name
        #middle_name = row.middle_name
        #last_name = row.last_name
        if request_dob:
            date_of_birth = row.date_of_birth
        else:
            date_of_birth = None
        if request_gender:
            gender = row.gender
        else:
            gender = None
        if separate_name_fields:
            first_name = row.first_name
            last_name = row.last_name
            if middle_name:
                middle_name = row.middle_name
        else:
            first_name = None
            middle_name = None
            last_name = None

        # Lookup contacts separately as we can't limitby here
        if home_phone:
            contact_methods = ("SMS", "EMAIL", "HOME_PHONE")
        else:
            contact_methods = ("SMS", "EMAIL")
        query = (ctable.pe_id == row.pe_id) & \
                (ctable.contact_method.belongs(contact_methods))
        rows = db(query).select(ctable.contact_method,
                                ctable.value,
                                orderby = ctable.priority,
                                )
        email = mobile_phone = None
        if home_phone:
            home_phone = None
            for row in rows:
                if not email and row.contact_method == "EMAIL":
                    email = row.value
                elif not mobile_phone and row.contact_method == "SMS":
                    mobile_phone = row.value
                elif not home_phone and row.contact_method == "HOME_PHONE":
                    home_phone = row.value
                if email and mobile_phone and home_phone:
                    break
        else:
            for row in rows:
                if not email and row.contact_method == "EMAIL":
                    email = row.value
                elif not mobile_phone and row.contact_method == "SMS":
                    mobile_phone = row.value
                if email and mobile_phone:
                    break

        # Minimal flattened structure
        item = {}
        if first_name:
            item["first_name"] = first_name
        if middle_name:
            item["middle_name"] = middle_name
        if last_name:
            item["last_name"] = last_name
        if email:
            item["email"] = email
        if mobile_phone:
            item["mphone"] = mobile_phone
        if home_phone:
            item["hphone"] = home_phone
        if gender:
            item["sex"] = gender
        if date_of_birth:
            item["dob"] = date_of_birth
        if occupation:
            item["occupation"] = occupation
        if organisation_id:
            item["org_id"] = organisation_id
        output = json.dumps(item, separators=SEPARATORS)

        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_ondelete(row):
        """ On-delete routine for HR records """

        db = current.db
        htable = db.hrm_human_resource

        # Update PE hierarchy
        person_id = row.person_id
        if person_id:
            current.s3db.pr_update_affiliations(htable, row)

# =============================================================================
class S3HRSiteModel(S3Model):

    names = ("hrm_human_resource_site",)

    def model(self):

        T = current.T

        # =========================================================================
        # Link between Human Resources & Facilities
        # - this is used to allow different Site Contacts per Sector
        # - it can be used to allow the right UI interface when adding HRs to a
        #   Facility via the Staff tab, although we use hrm_Assign for that now.
        #

        tablename = "hrm_human_resource_site"
        self.define_table(tablename,
                          self.hrm_human_resource_id(ondelete = "CASCADE"),
                          self.org_site_id(),
                          self.org_sector_id(),
                          Field("site_contact", "boolean",
                                label = T("Facility Contact"),
                                represent = lambda opt: \
                                            (T("No"), T("Yes"))[opt == True],
                                ),
                          *s3_meta_fields())

        self.configure(tablename,
                       # Each HR can only be assigned to one site at a time:
                       deduplicate = S3Duplicate(primary = ("human_resource_id",),
                                                 secondary = ("sector_id",),
                                                 ),
                       onaccept = self.hrm_human_resource_site_onaccept,
                       ondelete = self.hrm_human_resource_site_onaccept,
                       )

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Assign Staff"),
            title_display = T("Staff Assignment Details"),
            title_list = T("Staff Assignments"),
            title_update = T("Edit Staff Assignment"),
            label_list_button = T("List Staff Assignments"),
            label_delete_button = T("Delete Staff Assignment"),
            msg_record_created = T("Staff Assigned"),
            msg_record_modified = T("Staff Assignment updated"),
            msg_record_deleted = T("Staff Assignment removed"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no staff assigned"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_site_onaccept(form):
        """
            Update the Human Resource record with the site_id
        """

        # Deletion and update have a different format
        try:
            form_vars = form.vars
        except AttributeError:
            record_id = form.id
            delete = True
        else:
            record_id = form_vars.id
            delete = False

        # Get the full record
        db = current.db
        ltable = db.hrm_human_resource_site
        table = db.hrm_human_resource
        if delete:
            record = db(ltable.id == record_id).select(ltable.deleted_fk,
                                                       limitby = (0, 1),
                                                       ).first()
            if record:
                deleted_fks = json.loads(record.deleted_fk)
                human_resource_id = deleted_fks.get("human_resource_id")
                if human_resource_id:
                    db(table.id == human_resource_id).update(location_id=None,
                                                             site_id=None,
                                                             site_contact=False,
                                                             )
                    # Update realm_entity of HR
                    current.auth.set_realm_entity(table,
                                                  human_resource_id,
                                                  force_update = True,
                                                  )
        else:
            human_resource_id = form_vars.human_resource_id

            # Remove any additional records for this HR
            # (i.e. staff was assigned elsewhere previously)
            # @ToDo: Allow one person to be the Site Contact for multiple sectors
            rows = db(ltable.human_resource_id == human_resource_id).select(ltable.id,
                                                                            ltable.site_id,
                                                                            #ltable.sector_id,
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
            site_id = record.site_id
            db(table.id == human_resource_id).update(site_id = site_id,
                                                     site_contact = record.site_contact
                                                     )
            # Update realm_entity of HR
            entity = current.s3db.pr_get_pe_id("org_site", site_id)
            if entity:
                current.auth.set_realm_entity(table, human_resource_id,
                                              entity = entity,
                                              force_update = True)
            # Fire the normal onaccept
            hrform = Storage(id=human_resource_id)
            hrm_human_resource_onaccept(hrform)

# =============================================================================
class S3HRSalaryModel(S3Model):
    """ Data Model to track salaries of staff """

    names = ("hrm_staff_level",
             "hrm_salary_grade",
             "hrm_salary",
             )

    def model(self):

        db = current.db
        T = current.T
        define_table = self.define_table
        configure = self.configure

        organisation_id = self.org_organisation_id
        organisation_requires = self.org_organisation_requires

        # =====================================================================
        # Staff Level
        #
        tablename = "hrm_staff_level"
        define_table(tablename,
                     organisation_id(
                        requires = organisation_requires(updateable=True),
                     ),
                     Field("name",
                           label = T("Staff Level"),
                     ),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",
                                                       "organisation_id",
                                                       ),
                                            ),
                  )

        staff_level_represent = hrm_OrgSpecificTypeRepresent(lookup=tablename)

        # =====================================================================
        # Salary Grades
        #
        tablename = "hrm_salary_grade"
        define_table(tablename,
                     organisation_id(
                        requires = organisation_requires(updateable=True),
                     ),
                     Field("name",
                           label = T("Salary Grade"),
                     ),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",
                                                       "organisation_id",
                                                       ),
                                            ),
                  )

        salary_grade_represent = hrm_OrgSpecificTypeRepresent(lookup=tablename)

        # =====================================================================
        # Salary
        #
        tablename = "hrm_salary"
        define_table(tablename,
                     self.pr_person_id(),
                     self.hrm_human_resource_id(label = T("Staff Record"),
                                                widget = None,
                                                comment = None,
                                                ),
                     Field("staff_level_id", "reference hrm_staff_level",
                           label = T("Staff Level"),
                           represent = staff_level_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db,
                                                  "hrm_staff_level.id",
                                                  staff_level_represent,
                                                  )),
                           comment = S3PopupLink(f = "staff_level",
                                                 label = T("Create Staff Level"),
                                                 ),
                           ),
                     Field("salary_grade_id", "reference hrm_salary_grade",
                           label = T("Salary Grade"),
                           represent = salary_grade_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db,
                                                  "hrm_salary_grade.id",
                                                  salary_grade_represent,
                                                  )),
                           comment = S3PopupLink(f = "salary_grade",
                                                 label = T("Create Salary Grade"),
                                                 ),
                           ),
                     s3_date("start_date",
                             default = "now",
                             label = T("Start Date"),
                             set_min = "#hrm_salary_end_date",
                             ),
                     s3_date("end_date",
                             label = T("End Date"),
                             set_max = "#hrm_salary_start_date",
                             ),
                     Field("monthly_amount", "double",
                           represent = lambda v: \
                                       IS_FLOAT_AMOUNT.represent(v,
                                                                 precision = 2,
                                                                 ),
                           requires = IS_EMPTY_OR(
                                        IS_FLOAT_AMOUNT(minimum=0.0)
                                        ),
                           default = 0.0,
                           ),
                     *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Salary"),
            title_display = T("Salary Details"),
            title_list = T("Salaries"),
            title_update = T("Edit Salary"),
            label_list_button = T("List Salaries"),
            label_delete_button = T("Delete Salary"),
            msg_record_created = T("Salary added"),
            msg_record_modified = T("Salary updated"),
            msg_record_deleted = T("Salary removed"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no salary registered"))

        configure(tablename,
                  onvalidation = self.hrm_salary_onvalidation,
                  orderby = "%s.start_date desc" % tablename,
                  )

        # =====================================================================
        # Salary Coefficient
        #
        # @todo: implement

        # =====================================================================
        # Allowance Level
        #
        # @todo: implement

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_salary_onvalidation(form):

        try:
            form_vars = form.vars
            start_date = form_vars.get("start_date")
            end_date = form_vars.get("end_date")
        except AttributeError:
            return

        if start_date and end_date and start_date > end_date:
            form.errors["end_date"] = current.T("End date must be after start date.")
        return

# =============================================================================
class hrm_OrgSpecificTypeRepresent(S3Represent):
    """ Representation of organisation-specific taxonomic categories """

    def __init__(self, lookup=None):
        """ Constructor """

        if lookup is None:
            raise SyntaxError("must specify a lookup table")

        fields = ("name", "organisation_id")
        super(hrm_OrgSpecificTypeRepresent, self).__init__(lookup = lookup,
                                                           fields = fields,
                                                           )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        s3db = current.s3db

        table = self.table
        otable = s3db.org_organisation

        left = otable.on(otable.id == table.organisation_id)
        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(table.id,
                                        table.name,
                                        otable.id,
                                        otable.name,
                                        otable.acronym,
                                        left = left,
                                        )
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        try:
            name = row[self.tablename].name
        except AttributeError:
            return row.name
        try:
            organisation = row["org_organisation"]
        except AttributeError:
            return name

        if organisation.acronym:
            return "%s (%s)" % (name, organisation.acronym)
        elif organisation.name:
            return "%s (%s)" % (name, organisation.name)
        else:
            return name

# =============================================================================
class S3HRInsuranceModel(S3Model):
    """ Data Model to track insurance information of staff members """

    names = ("hrm_insurance",
             )

    def model(self):

        T = current.T

        insurance_types = {"SOCIAL": T("Social Insurance"),
                           "HEALTH": T("Health Insurance"),
                           }
        insurance_type_represent = S3Represent(options = insurance_types)

        # =====================================================================
        # Insurance Information
        #
        tablename = "hrm_insurance"
        self.define_table(tablename,
                          self.hrm_human_resource_id(),
                          Field("type",
                                label = T("Type"),
                                represent = insurance_type_represent,
                                requires = IS_IN_SET(insurance_types),
                                ),
                          Field("insurance_number",
                                length = 128,
                                label = T("Insurance Number"),
                                requires = IS_LENGTH(128),
                                ),
                          Field("insurer",
                                length = 255,
                                label = T("Insurer"),
                                requires = IS_LENGTH(255),
                                ),
                          Field("provider",
                                length = 255,
                                label = T("Provider"),
                                requires = IS_LENGTH(255),
                                ),
                          #Field("beneficiary",
                          #      label = T("Beneficiary"),
                          #      ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("human_resource_id",
                                                            "type",
                                                            ),
                                                 ),
                       )

        return {}

# =============================================================================
class S3HRContractModel(S3Model):
    """ Data model to track employment contract details of staff members """

    names = ("hrm_contract",
             )

    def model(self):

        T = current.T

        contract_terms = {"SHORT": T("Short-term"),
                          "LONG": T("Long-term"),
                          "PERMANENT": T("Permanent")
                          }
        contract_term_represent = S3Represent(options = contract_terms)

        hours_models = {"PARTTIME": T("Part-time"),
                        "FULLTIME": T("Full-time"),
                        }
        hours_model_represent = S3Represent(options = hours_models)

        # =====================================================================
        # Employment Contract Details
        #
        tablename = "hrm_contract"
        self.define_table(tablename,
                          self.hrm_human_resource_id(),
                          Field("name",
                                label = T("Name"),
                                ),
                          s3_date(label = T("Start Date"),
                                  ),
                          #s3_date("end_date",
                          #        label = T("End Date"),
                          #        ),
                          Field("term",
                                requires = IS_IN_SET(contract_terms),
                                represent = contract_term_represent,
                                ),
                          Field("hours",
                                requires = IS_IN_SET(hours_models),
                                represent = hours_model_represent,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("human_resource_id",)),
                       )

        return {}

# =============================================================================
class S3HRJobModel(S3Model):
    """
        Unused
    """

    names = ("hrm_position",
             "hrm_position_id",
             )

    def model(self):

        s3db = current.s3db
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        define_table = self.define_table

        job_title_id = self.hrm_job_title_id
        organisation_id = self.org_organisation_id
        site_id = self.org_site_id
        group_id = self.pr_group_id
        human_resource_id = self.hrm_human_resource_id
        hrm_type_opts = self.hrm_type_opts

        # =========================================================================
        # Positions
        #
        # @ToDo: Shifts for use in Scenarios & during Exercises & Events
        #
        # @ToDo: Vacancies
        #

        tablename = "hrm_position"
        table = define_table(tablename,
                            job_title_id(empty = False),
                            organisation_id(empty = False),
                            site_id,
                            group_id(label = "Team"),
                            *s3_meta_fields())
        table.site_id.readable = table.site_id.writable = True

        #crud_strings[tablename] = Storage(
        #   label_create = T("Add Position"),
        #   title_display = T("Position Details"),
        #   title_list = T("Position Catalog"),
        #   title_update = T("Edit Position"),
        #   label_list_button = T("List Positions"),
        #   label_delete_button = T("Delete Position"),
        #   msg_record_created = T("Position added"),
        #   msg_record_modified = T("Position updated"),
        #   msg_record_deleted = T("Position deleted"),
        #   msg_list_empty = T("Currently no entries in the catalog"))

        #label_create = crud_strings[tablename].label_create
        position_id = S3ReusableField("position_id", "reference %s" % tablename,
                                      label = T("Position"),
                                      ondelete = "SET NULL",
                                      #represent = hrm_position_represent,
                                      requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                       "hrm_position.id",
                                                                       #hrm_position_represent,
                                                                       )),
                                      sortby = "name",
                                      #comment = DIV(A(label_create,
                                      #                _class="s3_add_resource_link",
                                      #                _href=URL(f="position",
                                      #                          args="create",
                                      #                          vars={"format": "popup"}
                                      #                          ),
                                      #                _target="top",
                                      #                _title=label_create),
                                      #              DIV(_class="tooltip",
                                      #                  _title="%s|%s" % (label_create,
                                      #                                    T("Add a new job role to the catalog.")))),
                                      )

        # =========================================================================
        # Availability
        #
        # unused - see PRAvailabilityModel
        #
        weekdays = {1: T("Monday"),
                    2: T("Tuesday"),
                    3: T("Wednesday"),
                    4: T("Thursday"),
                    5: T("Friday"),
                    6: T("Saturday"),
                    7: T("Sunday")
                    }
        weekdays_represent = lambda opt: ",".join([str(weekdays[o]) for o in opt])

        tablename = "hrm_availability"
        define_table(tablename,
                     human_resource_id(),
                     Field("date_start", "date"),
                     Field("date_end", "date"),
                     Field("day_of_week", "list:integer",
                           default = [1, 2, 3, 4, 5],
                           represent = weekdays_represent,
                           requires = IS_EMPTY_OR(IS_IN_SET(weekdays,
                                                            zero=None,
                                                            multiple=True)),
                           widget = CheckboxesWidgetS3.widget,
                           ),
                     Field("hours_start", "time"),
                     Field("hours_end", "time"),
                     #location_id(label=T("Available for Location"),
                     #            requires=IS_ONE_OF(db, "gis_location.id",
                     #                               gis_LocationRepresent(),
                     #                               filterby="level",
                     #                               # @ToDo Should this change per config?
                     #                               filter_opts=gis.region_level_keys,
                     #                               orderby="gis_location.name"),
                     #            widget=None),
                     *s3_meta_fields())

        # =========================================================================
        # Hours registration
        #
        tablename = "hrm_hours"
        define_table(tablename,
                     human_resource_id(),
                     Field("timestmp_in", "datetime"),
                     Field("timestmp_out", "datetime"),
                     Field("hours", "double"),
                     *s3_meta_fields())

        # =========================================================================
        # Vacancy
        #
        # These are Positions which are not yet Filled
        #
        tablename = "hrm_vacancy"
        define_table(tablename,
                     organisation_id(),
                     #Field("code"),
                     Field("title"),
                     Field("description", "text"),
                     self.super_link("site_id", "org_site",
                                     label = T("Facility"),
                                     readable = False,
                                     writable = False,
                                     sort = True,
                                     represent = s3db.org_site_represent,
                                     ),
                     Field("type", "integer",
                           default = 1,
                           label = T("Type"),
                           represent = lambda opt: \
                                       hrm_type_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(hrm_type_opts, zero=None),
                           ),
                     Field("number", "integer"),
                     #location_id(),
                     Field("from", "date"),
                     Field("until", "date"),
                     Field("open", "boolean",
                           default = False,
                           ),
                     Field("app_deadline", "date",
                           #label = T("Application Deadline"),
                           ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"hrm_position_id": position_id,
                }

# =============================================================================
class S3HRSkillModel(S3Model):

    names = ("hrm_skill_type",
             "hrm_skill",
             "hrm_competency_rating",
             "hrm_competency",
             #"hrm_competency_id",
             "hrm_credential",
             "hrm_training",
             "hrm_trainings",
             "hrm_event_type",
             "hrm_training_event",
             "hrm_training_event_id",
             "hrm_event_location",
             "hrm_event_tag",
             "hrm_training_event_report",
             "hrm_certificate",
             "hrm_certification",
             "hrm_certification_onaccept",
             "hrm_certificate_skill",
             "hrm_course",
             "hrm_course_certificate",
             "hrm_course_job_title",
             "hrm_course_sector",
             "hrm_course_id",
             "hrm_skill_id",
             "hrm_multi_skill_id",
             "hrm_multi_skill_represent",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        request = current.request
        folder = request.folder
        s3 = current.response.s3
        settings = current.deployment_settings

        job_title_id = self.hrm_job_title_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id
        person_id = self.pr_person_id

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        AUTOCOMPLETE_HELP = messages.AUTOCOMPLETE_HELP
        ORGANISATION = settings.get_hrm_organisation_label()

        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)

        float_represent = IS_FLOAT_AMOUNT.represent

        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        root_org = auth.root_org()
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        group = request.get_vars.get("group", None)

        c = current.request.controller
        if c not in ("hrm", "vol"):
            c = "hrm"

        if settings.get_org_autocomplete():
            widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
        else:
            widget = None

        # ---------------------------------------------------------------------
        # Skill Types
        # - optional hierarchy of skills
        #   disabled by default, enable with deployment_settings.hrm.skill_types = True
        #   if enabled, then each needs their own list of competency levels
        #
        tablename = "hrm_skill_type"
        define_table(tablename,
                     Field("name", notnull=True, unique=True, length=64,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Skill Type"),
            title_display = T("Details"),
            title_list = T("Skill Type Catalog"),
            title_update = T("Edit Skill Type"),
            label_list_button = T("List Skill Types"),
            label_delete_button = T("Delete Skill Type"),
            msg_record_created = T("Skill Type added"),
            msg_record_modified = T("Skill Type updated"),
            msg_record_deleted = T("Skill Type deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        skill_types = settings.get_hrm_skill_types()
        label_create = crud_strings[tablename].label_create
        represent = S3Represent(lookup=tablename)
        skill_type_id = S3ReusableField("skill_type_id", "reference %s" % tablename,
            default = self.skill_type_default,
            label = T("Skill Type"),
            ondelete = "RESTRICT",
            readable = skill_types,
            writable = skill_types,
            represent = represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "hrm_skill_type.id",
                                  represent
                                  )),
            sortby = "name",
            comment = S3PopupLink(c = c,
                                  f = "skill_type",
                                  label = label_create,
                                  title = label_create,
                                  tooltip = T("Add a new skill type to the catalog."),
                                  ),
            )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # Components
        add_components(tablename,
                       hrm_competency_rating = "skill_type_id",
                       )

        # ---------------------------------------------------------------------
        # Skills
        # - these can be simple generic skills or can come from certifications
        #
        tablename = "hrm_skill"
        define_table(tablename,
                     skill_type_id(empty = False),
                     Field("name", notnull=True, unique=True,
                           length=64,    # Mayon compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Skill"),
            title_display = T("Skill Details"),
            title_list = T("Skill Catalog"),
            title_update = T("Edit Skill"),
            label_list_button = T("List Skills"),
            label_delete_button = T("Delete Skill"),
            msg_record_created = T("Skill added"),
            msg_record_modified = T("Skill updated"),
            msg_record_deleted = T("Skill deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        autocomplete = False
        label_create = crud_strings[tablename].label_create
        if autocomplete:
            # NB FilterField widget needs fixing for that too
            widget = S3AutocompleteWidget(request.controller,
                                          "skill")
            tooltip = AUTOCOMPLETE_HELP
        else:
            widget = None
            tooltip = None

        skill_help = S3PopupLink(c = c,
                                 f = "skill",
                                 label = label_create,
                                 tooltip = tooltip,
                                 )

        represent = S3Represent(lookup=tablename, translate=True)
        skill_id = S3ReusableField("skill_id", "reference %s" % tablename,
                                   label = T("Skill"),
                                   ondelete = "SET NULL",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "hrm_skill.id",
                                                          represent,
                                                          sort=True
                                                          )),
                                   sortby = "name",
                                   comment = skill_help,
                                   widget = widget
                                   )

        multi_skill_represent = S3Represent(lookup = tablename,
                                            multiple = True,
                                            )
        multi_skill_id = S3ReusableField("skill_id", "list:reference hrm_skill",
                                         label = T("Skills"),
                                         ondelete = "SET NULL",
                                         represent = multi_skill_represent,
                                         requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "hrm_skill.id",
                                                                  represent,
                                                                  sort=True,
                                                                  multiple=True
                                                                  )),
                                         sortby = "name",
                                         #comment = skill_help,
                                         widget = S3MultiSelectWidget(header="",
                                                                      selectedList=3),
                                         )

        configure("hrm_skill",
                  deduplicate = S3Duplicate(),
                  )

        # Components
        add_components(tablename,
                       # Requests
                       req_req_skill = "skill_id",
                       )

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
        define_table(tablename,
                     skill_type_id(empty = False),
                     Field("name",
                           length=64, # Mayon Compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("priority", "integer",
                           default = 1,
                           label = T("Priority"),
                           requires = IS_INT_IN_RANGE(1, 10),
                           widget = S3SliderWidget(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Priority"),
                                                           T("Priority from 1 to 9. 1 is most preferred.")))
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Competency Rating"),
            title_display = T("Competency Rating Details"),
            title_list = T("Competency Rating Catalog"),
            title_update = T("Edit Competency Rating"),
            label_list_button = T("List Competency Ratings"),
            label_delete_button = T("Delete Competency Rating"),
            msg_record_created = T("Competency Rating added"),
            msg_record_modified = T("Competency Rating updated"),
            msg_record_deleted = T("Competency Rating deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        represent = S3Represent(lookup=tablename, translate=True)
        competency_id = S3ReusableField("competency_id", "reference %s" % tablename,
                                        label = T("Competency"),
                                        ondelete = "RESTRICT",
                                        represent = represent,
                                        requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db,
                                                              "hrm_competency_rating.id",
                                                              represent,
                                                              orderby="hrm_competency_rating.priority desc",
                                                              sort=True)),
                                        sortby = "priority",
                                        comment = self.competency_rating_comment(),
                                        )

        configure("hrm_competency_rating",
                  deduplicate = self.hrm_competency_rating_duplicate,
                  )

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
        define_table(tablename,
                     person_id(ondelete = "CASCADE"),
                     skill_id(),
                     competency_id(),
                     # This field can only be filled-out by specific roles
                     # Once this has been filled-out then the other fields are locked
                     organisation_id(label = T("Confirming Organization"),
                                     comment = None,
                                     widget = widget,
                                     writable = False,
                                     ),
                     Field("from_certification", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Skill"),
            title_display = T("Skill Details"),
            title_list = T("Skills"),
            title_update = T("Edit Skill"),
            label_list_button = T("List Skills"),
            label_delete_button = T("Remove Skill"),
            msg_record_created = T("Skill added"),
            msg_record_modified = T("Skill updated"),
            msg_record_deleted = T("Skill removed"),
            msg_list_empty = T("Currently no Skills registered"))

        configure("hrm_competency",
                  context = {"person": "person_id",
                             },
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "skill_id",
                                                       ),
                                            ),
                  list_fields = ["id",
                                 # Normally accessed via component
                                 #"person_id",
                                 "skill_id",
                                 "competency_id",
                                 "comments",
                                 ],
                  list_layout = hrm_competency_list_layout,
                  )

        # =====================================================================
        # Skill Provisions
        #
        # The minimum Competency levels in a Skill to be assigned the given Priority
        # for allocation to Mayon's shifts for the given Job Role
        #
        #tablename = "hrm_skill_provision"
        #define_table(tablename,
        #             Field("name", notnull=True, unique=True,
        #                   length=32,    # Mayon compatibility
        #                   label = T("Name"),
        #                   requires = [IS_NOT_EMPTY(),
        #                               IS_LENGTH(32),
        #                               ],
        #                   ),
        #             job_title_id(),
        #             skill_id(),
        #             competency_id(),
        #             Field("priority", "integer",
        #                   default = 1,
        #                   requires = IS_INT_IN_RANGE(1, 10),
        #                   widget = S3SliderWidget(),
        #                   comment = DIV(_class="tooltip",
        #                                 _title="%s|%s" % (T("Priority"),
        #                                                   T("Priority from 1 to 9. 1 is most preferred.")))
        #                   ),
        #             s3_comments(),
        #             *s3_meta_fields())

        #crud_strings[tablename] = Storage(
        #    label_create = T("Add Skill Provision"),
        #    title_display = T("Skill Provision Details"),
        #    title_list = T("Skill Provision Catalog"),
        #    title_update = T("Edit Skill Provision"),
        #    label_list_button = T("List Skill Provisions"),
        #    label_delete_button = T("Delete Skill Provision"),
        #    msg_record_created = T("Skill Provision added"),
        #    msg_record_modified = T("Skill Provision updated"),
        #    msg_record_deleted = T("Skill Provision deleted"),
        #    msg_list_empty = T("Currently no entries in the catalog"))

        #label_create = crud_strings[tablename].label_create
        #represent = S3Represent(lookup=tablename)
        #skill_group_id = S3ReusableField("skill_provision_id", "reference %s" % tablename,
        #                           label = T("Skill Provision"),
        #                           ondelete = "SET NULL",
        #                           represent = represent,
        #                           requires = IS_EMPTY_OR(IS_ONE_OF(db,
        #                                                           "hrm_skill_provision.id",
        #                                                           represent)),
        #                           sortby = "name",
        #                           comment = DIV(A(label_create,
        #                                           _class="s3_add_resource_link",
        #                                           _href=URL(f="skill_provision",
        #                                                     args="create",
        #                                                     vars={"format": "popup"},
        #                                                     ),
        #                                           _target="top",
        #                                           _title=label_create),
        #                                         DIV(_class="tooltip",
        #                                             _title="%s|%s" % (label_create,
        #                                                               T("Add a new skill provision to the catalog.")))),
        #                           )


        # =========================================================================
        # Courses
        #
        external_courses = settings.get_hrm_trainings_external()
        course_pass_marks = settings.get_hrm_course_pass_marks()
        hrm_course_types = settings.get_hrm_course_types()

        tablename = "hrm_course"
        define_table(tablename,
                     Field("code", length=64,
                           label = T("Code"),
                           requires = IS_LENGTH(64),
                           ),
                     Field("name", length=128, notnull=True,
                           label = T("Name"),
                           represent = lambda v: T(v) if v is not None \
                                                      else NONE,
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     # Optionally restrict to Staff/Volunteers/Members
                     Field("type", "integer",
                           label = T("Type"),
                           represent = lambda opt: \
                                       hrm_course_types.get(opt, UNKNOWN_OPT) \
                                       if opt is not None else NONE,
                           requires = IS_EMPTY_OR(IS_IN_SET(hrm_course_types)),
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     # @ToDo: Option to see multiple Training Centers even as non_admin
                     organisation_id(default = root_org,
                                     readable = is_admin,
                                     writable = is_admin,
                                     ),
                     Field("external", "boolean",
                           default = False,
                           label = T("External"),
                           represent = s3_yes_no_represent,
                           readable = external_courses,
                           writable = external_courses,
                           ),
                     Field("hours", "integer",
                           label = T("Hours"),
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(0, None)
                                        ),
                           ),
                     Field("pass_mark", "float",
                           default = 0.0,
                           label = T("Pass Mark"),
                           represent = lambda v: \
                                       float_represent(v, precision=2),
                           requires = IS_EMPTY_OR(
                                        IS_FLOAT_AMOUNT(minimum=0.0)
                                        ),
                           readable = course_pass_marks,
                           writable = course_pass_marks,
                           ),
                     s3_comments(label = T("Description"),
                                 comment = None,
                                 ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Course"),
            title_display = T("Course Details"),
            title_list = T("Course Catalog"),
            title_update = T("Edit Course"),
            title_upload = T("Import Courses"),
            label_list_button = T("List Courses"),
            label_delete_button = T("Delete Course"),
            msg_record_created = T("Course added"),
            msg_record_modified = T("Course updated"),
            msg_record_deleted = T("Course deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no entries in the catalog"))

        if is_admin:
            label_create = crud_strings[tablename].label_create
            course_help = S3PopupLink(c = c,
                                      f = "course",
                                      label = label_create,
                                      )
        else:
            course_help = None
            #course_help = DIV(_class="tooltip",
            #                  _title="%s|%s" % (T("Course"),
            #                                    AUTOCOMPLETE_HELP))

        course_represent = S3Represent(lookup=tablename, translate=True)
        course_id = S3ReusableField("course_id", "reference %s" % tablename,
                                    label = T("Course"),
                                    ondelete = "RESTRICT",
                                    represent = course_represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "hrm_course.id",
                                                          course_represent,
                                                          filterby = "organisation_id",
                                                          filter_opts = filter_opts,
                                                          )),
                                    sortby = "name",
                                    comment = course_help,
                                    # Comment this to use a Dropdown & not an Autocomplete
                                    #widget = S3AutocompleteWidget("hrm", "course")
                                    )

        if settings.get_hrm_create_certificates_from_courses():
            onaccept = self.hrm_course_onaccept
        else:
            onaccept = None

        configure(tablename,
                  create_next = URL(f="course",
                                    args=["[id]", "course_certificate"]),
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("organisation_id",),
                                            ),
                  onaccept = onaccept,
                  )

        # Components
        add_components(tablename,
                       # Certificates
                       hrm_course_certificate = "course_id",
                       # Job Titles
                       hrm_course_job_title = "course_id",
                       # Sectors
                       org_sector = {"link": "hrm_course_sector",
                                     "joinby": "course_id",
                                     "key": "sector_id",
                                     "actuate": "hide",
                                     },
                       # Format for filter_widget
                       hrm_course_sector = "course_id",
                       # Trainees
                       hrm_training = "course_id",
                       )

        # ---------------------------------------------------------------------
        # Event Types
        # - Trainings, Workshops, Meetings
        #
        tablename = "hrm_event_type"
        define_table(tablename,
                     Field("name", notnull=True,
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Event Type"),
            title_display = T("Event Type Details"),
            title_list = T("Event Types"),
            title_update = T("Edit Event Type"),
            label_list_button = T("List Event Types"),
            label_delete_button = T("Delete Event Type"),
            msg_record_created = T("Event Type added"),
            msg_record_modified = T("Event Type updated"),
            msg_record_deleted = T("Event Type deleted"),
            msg_list_empty = T("Currently no entries in the catalog"))

        event_types = settings.get_hrm_event_types()
        label_create = crud_strings[tablename].label_create
        represent = S3Represent(lookup=tablename)
        event_type_id = S3ReusableField("event_type_id", "reference %s" % tablename,
            label = T("Event Type"),
            ondelete = "RESTRICT",
            readable = event_types,
            writable = event_types,
            represent = represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "hrm_event_type.id",
                                  represent
                                  )),
            sortby = "name",
            comment = S3PopupLink(c = "hrm",
                                  f = "event_type",
                                  label = label_create,
                                  title = label_create,
                                  tooltip = T("Add a new event type to the catalog."),
                                  ),
            )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # =========================================================================
        # (Training) Events
        # - can include Meetings, Workshops, etc
        #

        #site_label = settings.get_org_site_label()
        site_label = T("Venue")

        course_mandatory = settings.get_hrm_event_course_mandatory()
        event_site = settings.get_hrm_event_site()

        # Instructor settings
        INSTRUCTOR = T("Instructor")
        instructors = settings.get_hrm_training_instructors()

        int_instructor = ext_instructor = False
        int_instructor_tooltip = None
        ext_instructor_label = INSTRUCTOR
        ext_instructor_tooltip = None

        if instructors in ("internal", "both"):
            int_instructor = True
            int_instructor_tooltip = DIV(_class="tooltip",
                                         _title="%s|%s" % (INSTRUCTOR,
                                                           AUTOCOMPLETE_HELP),
                                         )
            if instructors == "both":
                ext_instructor = True
                ext_instructor_label = T("External Instructor")
                ext_instructor_tooltip = DIV(_class="tooltip",
                                             _title="%s|%s" % (T("External Instructor"),
                                                               T("Enter the name of the external instructor")),
                                             )
        elif instructors == "external":
            ext_instructor = True

        tablename = "hrm_training_event"
        define_table(tablename,
                     # Instance
                     super_link("pe_id", "pr_pentity"),
                     event_type_id(),
                     Field("name",
                           label = T("Name"),
                           readable = event_types,
                           writable = event_types,
                           ),
                     course_id(empty = not course_mandatory),
                     organisation_id(label = T("Organized By")),
                     location_id(widget = S3LocationSelector(), # show_address = False
                                 readable = not event_site,
                                 writable = not event_site,
                                 ),
                     # Component, not instance
                     super_link("site_id", "org_site",
                                label = site_label,
                                instance_types = auth.org_site_types,
                                updateable = True,
                                not_filterby = "obsolete",
                                not_filter_opts = (True,),
                                default = auth.user.site_id if auth.is_logged_in() else None,
                                readable = event_site,
                                writable = event_site,
                                empty = not event_site,
                                represent = self.org_site_represent,
                                ),
                     s3_datetime("start_date",
                                 label = T("Start Date"),
                                 min = datetime.datetime(2000, 1, 1),
                                 set_min = "#hrm_training_event_end_date",
                                 ),
                     s3_datetime("end_date",
                                 label = T("End Date"),
                                 min = datetime.datetime(2000, 1, 1),
                                 set_max = "#hrm_training_event_start_date",
                                 ),
                     # @ToDo: Auto-populate from course
                     Field("hours", "integer",
                           label = T("Hours"),
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(1, None),
                                        ),
                           ),
                     person_id(label = INSTRUCTOR,
                               comment = int_instructor_tooltip,
                               readable = int_instructor,
                               writable = int_instructor,
                               ),
                     Field("instructor",
                           label = ext_instructor_label,
                           comment = ext_instructor_tooltip,
                           represent = lambda s: s if s else NONE,
                           readable = ext_instructor,
                           writable = ext_instructor,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_TRAINING_EVENT = T("Create Training Event")
        crud_strings[tablename] = Storage(
            label_create = ADD_TRAINING_EVENT,
            title_display = T("Training Event Details"),
            title_list = T("Training Events"),
            title_update = T("Edit Training Event"),
            title_upload = T("Import Training Events"),
            label_list_button = T("List Training Events"),
            label_delete_button = T("Delete Training Event"),
            msg_record_created = T("Training Event added"),
            msg_record_modified = T("Training Event updated"),
            msg_record_deleted = T("Training Event deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no training events registered"))

        represent = hrm_TrainingEventRepresent()
        training_event_id = S3ReusableField("training_event_id", "reference %s" % tablename,
                                            label = T("Training Event"),
                                            ondelete = "RESTRICT",
                                            represent = represent,
                                            requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "hrm_training_event.id",
                                                                  represent,
                                                                  #filterby="organisation_id",
                                                                  #filter_opts=filter_opts,
                                                                  )),
                                            sortby = "course_id",
                                            comment = S3PopupLink(c = c,
                                                                  f = "training_event",
                                                                  label = ADD_TRAINING_EVENT,
                                                                  ),
                                            # Comment this to use a Dropdown & not an Autocomplete
                                            #widget = S3AutocompleteWidget("hrm", "training_event")
                                            )

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        if event_site:
            filter_widgets = [S3TextFilter(["name",
                                            "course_id$name",
                                            "site_id$name",
                                            "comments",
                                            ],
                                           label = T("Search"),
                                           comment = T("You can search by course name, venue name or event comments. You may use % as wildcard. Press 'Search' without input to list all events."),
                                           ),
                              S3LocationFilter("site_id$location_id",
                                               levels = levels,
                                               hidden = True,
                                               ),
                              S3OptionsFilter("site_id",
                                              label = site_label,
                                              hidden = True,
                                              ),
                              S3DateFilter("start_date",
                                           label = T("Date"),
                                           hide_time = True,
                                           hidden = True,
                                           )
                              ]
        else:
            filter_widgets = [S3TextFilter(["name",
                                            "course_id$name",
                                            "location_id$name",
                                            "comments",
                                            ],
                                           label = T("Search"),
                                           comment = T("You can search by course name, venue name or event comments. You may use % as wildcard. Press 'Search' without input to list all events."),
                                           ),
                              S3LocationFilter("location_id",
                                               levels = levels,
                                               hidden = True,
                                               ),
                              S3DateFilter("start_date",
                                           label = T("Date"),
                                           hide_time = True,
                                           hidden = True,
                                           )
                              ]

        # Resource Configuration
        configure(tablename,
                  create_next = URL(f="training_event",
                                    args=["[id]", "participant"],
                                    ),
                  deduplicate = S3Duplicate(primary = ("course_id",
                                                       "start_date",
                                                       ),
                                            secondary = ("site_id",),
                                            ),
                  filter_widgets = filter_widgets,
                  realm_entity = self.hrm_training_event_realm_entity,
                  super_entity = "pr_pentity",
                  )

        # Components
        add_components(tablename,
                       gis_location = {"link": "hrm_event_location",
                                       "joinby": "training_event_id",
                                       "key": "location_id",
                                       "actuate": "hide",
                                       },
                       pr_person = [# Instructors
                                    {"name": "instructor",
                                    #"joinby": "person_id",
                                    "link": "hrm_training_event_instructor",
                                    "joinby": "training_event_id",
                                    "key": "person_id",
                                    "actuate": "hide",
                                    },
                                    # Participants
                                    {"name": "participant",
                                    "link": "hrm_training",
                                    "joinby": "training_event_id",
                                    "key": "person_id",
                                    "actuate": "hide",
                                    },
                                    ],
                       hrm_event_tag = "training_event_id",
                       # This format is better for permissions on the link table
                       hrm_training = "training_event_id",
                       # Format for list_fields
                       hrm_training_event_instructor = "training_event_id",

                       hrm_training_event_report = {"joinby": "training_event_id",
                                                    "multiple": False,
                                                    },

                       hrm_programme = {"link": "hrm_event_programme",
                                        "joinby": "training_event_id",
                                        "key": "programme_id",
                                        "actuate": "hide",
                                        },
                       project_project = {"link": "hrm_event_project",
                                          "joinby": "training_event_id",
                                          "key": "project_id",
                                          "actuate": "hide",
                                          },
                       project_strategy = {"link": "hrm_event_strategy",
                                           "joinby": "training_event_id",
                                           "key": "strategy_id",
                                           "actuate": "hide",
                                           },

                       dc_target = {"link": "hrm_event_target",
                                    "joinby": "training_event_id",
                                    "key": "target_id",
                                    "actuate": "replace",
                                    },
                       )

        # =====================================================================
        # Training Event Locations
        # - e.g. used for showing which Locations an Event is relevant for
        #

        tablename = "hrm_event_location"
        define_table(tablename,
                     training_event_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     location_id(empty = False,
                                 ondelete = "CASCADE",
                                 widget = S3LocationSelector(#show_address = False,
                                                             ),
                                 ),
                     #s3_comments(),
                     *s3_meta_fields())

        # =====================================================================
        # Training Event Tags

        tablename = "hrm_event_tag"
        define_table(tablename,
                     training_event_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     # key is a reserved word in MySQL
                     Field("tag",
                           label = T("Key"),
                           ),
                     Field("value",
                           label = T("Value"),
                           ),
                     #s3_comments(),
                     *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("training_event_id",
                                                            "tag",
                                                            ),
                                                 ),
                       )

        # =====================================================================
        # Training Event Report
        # - this is currently configured for RMS Americas
        #   (move custom labels there if need to make this more generic)
        #

        tablename = "hrm_training_event_report"
        define_table(tablename,
                     # Instance
                     super_link("doc_id", "doc_entity"),
                     training_event_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     person_id(),
                     self.hrm_job_title_id(label = T("Position"),
                                           ),
                     organisation_id(),
                     Field("purpose",
                           label = T("Training Purpose"),
                           ),
                     Field("code",
                           label = T("Code"),
                           ),
                     s3_date(label = T("Report Date")),
                     Field("objectives",
                           label = T("Objectives"),
                           widget = s3_comments_widget,
                           ),
                     Field("methodology",
                           label = T("Methodology"),
                           widget = s3_comments_widget,
                           ),
                     Field("actions",
                           label = T("Implemented Actions"),
                           widget = s3_comments_widget,
                           ),
                     Field("participants",
                           label = T("About the participants"),
                           widget = s3_comments_widget,
                           ),
                     Field("results",
                           label = T("Results and Lessons Learned"),
                           widget = s3_comments_widget,
                           ),
                     Field("followup",
                           label = T("Follow-up Required"),
                           widget = s3_comments_widget,
                           ),
                     Field("additional",
                           label = T("Additional relevant information"),
                           widget = s3_comments_widget,
                           ),
                     s3_comments(label = T("General Comments")),
                     *s3_meta_fields())

        configure(tablename,
                  super_entity = "doc_entity",
                  )

        # =====================================================================
        # Training Intructors
        # - used if there can be multiple per-event
        #

        tablename = "hrm_training_event_instructor"
        define_table(tablename,
                     training_event_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     person_id(comment = self.pr_person_comment(INSTRUCTOR,
                                                                AUTOCOMPLETE_HELP,
                                                                child="person_id"),
                               empty = False,
                               label = INSTRUCTOR,
                               ondelete = "CASCADE",
                               ),
                     #s3_comments(),
                     *s3_meta_fields())

        # =====================================================================
        # (Training) Participations (Trainees)
        #
        # These are an element of credentials:
        # - a minimum number of hours of training need to be done each year
        #
        # Users can add their own but these are confirmed only by specific roles
        #
        course_grade_opts = settings.get_hrm_course_grades()

        # @ToDo: configuration setting once-required
        role_opts = {1: T("Participant"),
                     2: T("Facilitator"),
                     3: T("Observer"),
                     }

        # @ToDo: configuration setting once-required
        status_opts = {1: T("Applied"),
                       2: T("Approved"),
                       3: T("Rejected"),
                       4: T("Invited"),
                       5: T("Accepted"),
                       6: T("Declined"),
                       }

        tablename = "hrm_training"
        define_table(tablename,
                     # @ToDo: Create a way to add new people to training as staff/volunteers
                     person_id(comment = self.pr_person_comment(
                                  T("Participant"),
                                  T("Type the first few characters of one of the Participant's names."),
                                  child="person_id"),
                               empty = False,
                               ondelete = "CASCADE",
                               ),
                     # Just used when created from participation in an Event
                     training_event_id(ondelete = "SET NULL",
                                       readable = False,
                                       writable = False,
                                       ),
                     course_id(empty = not course_mandatory,
                               ),
                     Field("role", "integer",
                           default = 1,
                           label = T("Role"),
                           represent = lambda opt: \
                                       role_opts.get(opt, NONE),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(role_opts,
                                                  zero=None)),
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     s3_datetime(),
                     s3_datetime("end_date",
                                 label = T("End Date"),
                                 ),
                     Field("hours", "integer",
                           label = T("Hours"),
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(0, None)
                                        ),
                           ),
                     Field("status", "integer",
                           default = 4, # Invited
                           label = T("Status"),
                           represent = S3Represent(options=status_opts),
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(status_opts)),
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     # This field can only be filled-out by specific roles
                     # Once this has been filled-out then the other fields are locked
                     Field("grade", "integer",
                           label = T("Grade"),
                           represent = lambda opt: \
                                       course_grade_opts.get(opt, NONE),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(course_grade_opts,
                                                  zero=None)),
                           readable = False,
                           writable = False,
                           ),
                     # Can store specific test result here & then auto-calculate the Pass/Fail
                     Field("grade_details", "float",
                           default = 0.0,
                           label = T("Grade Details"),
                           represent = lambda v: \
                                       float_represent(v, precision=2),
                           requires = IS_EMPTY_OR(
                                        IS_FLOAT_AMOUNT(minimum=0.0)
                                        ),
                           readable = course_pass_marks,
                           writable = course_pass_marks,
                           ),
                     Field("qualitative_feedback",
                           label = T("Qualitative Feedback"),
                           widget = s3_comments_widget,
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("file", "upload",
                           autodelete = True,
                           length = current.MAX_FILENAME_LENGTH,
                           represent = self.hrm_training_file_represent,
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(folder,
                                                       "uploads"),
                           # Enable (& label) in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field.Method("job_title", hrm_training_job_title),
                     Field.Method("organisation", hrm_training_organisation),
                     s3_comments(),
                     *s3_meta_fields())

        # Suitable for use when adding a Training to a Person
        # The ones when adding a Participant to an Event are done in the Controller
        crud_strings[tablename] = Storage(
            label_create = T("Add Training"),
            title_display = T("Training Details"),
            title_list = T("Trainings"),
            title_update = T("Edit Training"),
            title_report = T("Training Report"),
            title_upload = T("Import Training Participants"),
            label_list_button = T("List Trainings"),
            label_delete_button = T("Delete Training"),
            msg_record_created = T("Training added"),
            msg_record_modified = T("Training updated"),
            msg_record_deleted = T("Training deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("No entries currently registered"))

        filter_widgets = [
            S3TextFilter(["person_id$first_name",
                          "person_id$last_name",
                          "course_id$name",
                          "training_event_id$name",
                          "comments",
                          ],
                         label = T("Search"),
                         comment = T("You can search by trainee name, course name or comments. You may use % as wildcard. Press 'Search' without input to list all trainees."),
                         _class="filter-search",
                         ),
            S3OptionsFilter("person_id$human_resource.organisation_id",
                            # Doesn't support translations
                            #represent = "%(name)s",
                            ),
            S3LocationFilter("person_id$location_id",
                             levels = levels,
                             ),
            S3OptionsFilter("course_id",
                            # Doesn't support translations
                            #represent="%(name)s",
                            ),
            S3OptionsFilter("training_event_id$site_id",
                            label = T("Training Facility"),
                            represent = self.org_site_represent,
                            ),
            S3OptionsFilter("grade",
                            ),
            S3DateFilter("date",
                         hide_time=True,
                         ),
            ]

        # NB training_event_controller overrides these for Participants
        list_fields = ["course_id",
                       "person_id",
                       #(T("Job Title"), "job_title"),
                       (ORGANISATION, "organisation"),
                       "grade",
                       ]
        if course_pass_marks:
            list_fields.append("grade_details")
        list_fields.append("date")

        report_fields = [(T("Training Event"), "training_event_id"),
                         "person_id",
                         "course_id",
                         "grade",
                         (ORGANISATION, "organisation"),
                         (T("Facility"), "training_event_id$site_id"),
                         (T("Month"), "month"),
                         (T("Year"), "year"),
                         ]
        rappend = report_fields.append

        for level in levels:
            rappend("person_id$location_id$%s" % level)

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = report_fields,
                                 methods = ["count", "list"],
                                 defaults = Storage(
                                    rows = "training.course_id",
                                    cols = "training.month",
                                    fact = "count(training.person_id)",
                                    totals = True,
                                    )
                                 )

        # Resource Configuration
        configure(tablename,
                  context = {"person": "person_id",
                             },
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "course_id",
                                                       ),
                                            secondary = ("date",),
                                            ),
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  list_layout = hrm_training_list_layout,
                  onaccept = hrm_training_onaccept,
                  ondelete = hrm_training_onaccept,
                  # Only used in Imports
                  #onvalidation = hrm_training_onvalidation,
                  orderby = "hrm_training.date desc",
                  report_options = report_options,
                  )

        # Components
        add_components(tablename,
                       hrm_certification = {"name": "certification_from_training", # Distinguish from that linked to the Person
                                            "joinby": "training_id",
                                            "multiple": False,
                                            },
                       )

        # =====================================================================
        # Trainings
        #
        # A list:reference table to support Contains queries:
        #   - people who have attended both Course A & Course B
        #

        tablename = "hrm_trainings"
        define_table(tablename,
                     person_id(empty = False,
                               ondelete = "CASCADE",
                               ),
                     Field("course_id", "list:reference hrm_course",
                           label = T("Courses Attended"),
                           ondelete = "SET NULL",
                           represent = S3Represent(lookup="hrm_course",
                                                   multiple=True,
                                                   translate=True
                                                   ),
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "hrm_course.id",
                                                  course_represent,
                                                  sort=True,
                                                  multiple=True
                                                  )),
                           widget = S3MultiSelectWidget(header="",
                                                        selectedList=3),

                           ),
                     *s3_meta_fields())

        # =====================================================================
        # Certificates
        #
        # NB Some Orgs will only trust the certificates of some Orgs
        # - we currently make no attempt to manage this trust chain
        #
        filter_certs = settings.get_hrm_filter_certificates()
        if filter_certs:
            label = ORGANISATION
        else:
            label = T("Certifying Organization")

        tablename = "hrm_certificate"
        define_table(tablename,
                     Field("name", notnull=True,
                           length=128,   # Mayon Compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     organisation_id(default = root_org if filter_certs else None,
                                     label = label,
                                     readable = is_admin or not filter_certs,
                                     writable = is_admin or not filter_certs,
                                     widget = widget,
                                     ),
                     Field("expiry", "integer",
                           label = T("Expiry (months)"),
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(1, None)
                                        ),
                           ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Certificate"),
            title_display = T("Certificate Details"),
            title_list = T("Certificate Catalog"),
            title_update = T("Edit Certificate"),
            title_upload = T("Import Certificates"),
            label_list_button = T("List Certificates"),
            label_delete_button = T("Delete Certificate"),
            msg_record_created = T("Certificate added"),
            msg_record_modified = T("Certificate updated"),
            msg_record_deleted = T("Certificate deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no entries in the catalog"))

        label_create = crud_strings[tablename].label_create
        represent = S3Represent(lookup=tablename)
        certificate_id = S3ReusableField("certificate_id", "reference %s" % tablename,
             label = T("Certificate"),
             ondelete = "RESTRICT",
             represent = represent,
             requires = IS_EMPTY_OR(
                            IS_ONE_OF(db,
                                      "hrm_certificate.id",
                                      represent,
                                      filterby="organisation_id" if filter_certs else None,
                                      filter_opts=filter_opts
                                      )),
             sortby = "name",
             comment = S3PopupLink(c = c,
                                   f = "certificate",
                                   label = label_create,
                                   title = label_create,
                                   tooltip = T("Add a new certificate to the catalog."),
                                   ),
             )

        if settings.get_hrm_use_skills():
            create_next = URL(f="certificate",
                              args=["[id]", "certificate_skill"])
        else:
            create_next = None

        configure(tablename,
                  create_next = create_next,
                  deduplicate = S3Duplicate(),
                  )

        # Components
        add_components(tablename,
                       hrm_certificate_skill = "certificate_id",
                       )

        # =====================================================================
        # Certifications
        #
        # Link table between Persons & Certificates
        #
        # These are an element of credentials
        #

        tablename = "hrm_certification"
        define_table(tablename,
                     person_id(empty = False,
                               ondelete = "CASCADE",
                               ),
                     certificate_id(empty = False,
                                    ),
                     # @ToDo: Option to auto-generate (like Waybills: SiteCode-CourseCode-UniqueNumber)
                     Field("number",
                           label = T("License Number"),
                           ),
                     #Field("status", label = T("Status")),
                     s3_date(label = T("Expiry Date")),
                     Field("image", "upload",
                           autodelete = True,
                           label = T("Scanned Copy"),
                           length = current.MAX_FILENAME_LENGTH,
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(folder,
                                                       "uploads"),
                           ),
                     # This field can only be filled-out by specific roles
                     # Once this has been filled-out then the other fields are locked
                     organisation_id(comment = None,
                                     label = T("Confirming Organization"),
                                     widget = widget,
                                     writable = False,
                                     ),
                     # Optional: When certification comes from a training
                     Field("training_id", "reference hrm_training",
                           readable = False,
                           writable = False,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "hrm_training.id",
                                                  )),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  context = {"person": "person_id",
                             },
                  list_fields = ["id",
                                 "certificate_id",
                                 "number",
                                 "date",
                                 #"comments",
                                 ],
                  onaccept = self.hrm_certification_onaccept,
                  ondelete = self.hrm_certification_onaccept,
                  )

        crud_strings[tablename] = Storage(
            label_create = T("Add Certification"),
            title_display = T("Certification Details"),
            title_list = T("Certifications"),
            title_update = T("Edit Certification"),
            label_list_button = T("List Certifications"),
            label_delete_button = T("Delete Certification"),
            msg_record_created = T("Certification added"),
            msg_record_modified = T("Certification updated"),
            msg_record_deleted = T("Certification deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("No entries currently registered"))

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
        hrm_pass_fail_opts = {8: T("Pass"),
                              9: T("Fail"),
                              }
        # 12-monthly rating (Portuguese Bombeiros)
        # - this is used to determine rank progression (need 4-5 for 5 years)
        #hrm_five_rating_opts = {1: T("Poor"),
        #                        2: T("Fair"),
        #                        3: T("Good"),
        #                        4: T("Very Good"),
        #                        5: T("Excellent"),
        #                        }
        # Lookup to represent both sorts of ratings
        hrm_performance_opts = {1: T("Poor"),
                                2: T("Fair"),
                                3: T("Good"),
                                4: T("Very Good"),
                                5: T("Excellent"),
                                8: T("Pass"),
                                9: T("Fail"),
                                }

        tablename = "hrm_credential"
        define_table(tablename,
                     person_id(ondelete = "CASCADE"),
                     job_title_id(),
                     organisation_id(label = T("Credentialling Organization"),
                                     widget = widget,
                                     ),
                     Field("performance_rating", "integer",
                           label = T("Performance Rating"),
                           represent = lambda opt: \
                                       hrm_performance_opts.get(opt,
                                                                UNKNOWN_OPT),
                           # Default to pass/fail (can override to 5-levels in Controller)
                           # @ToDo: Build this onaccept of hrm_appraisal
                           requires = IS_EMPTY_OR(IS_IN_SET(hrm_pass_fail_opts)),
                           ),
                     s3_date("start_date",
                             default = "now",
                             label = T("Date Received"),
                             set_min = "#hrm_credential_end_date",
                             ),
                     s3_date("end_date",
                             label = T("Expiry Date"),
                             set_max = "#hrm_credential_start_date",
                             start_field = "hrm_credential_start_date",
                             default_interval = 12,
                             default_explicit = True,
                             ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Credential"),
            title_display = T("Credential Details"),
            title_list = T("Credentials"),
            title_update = T("Edit Credential"),
            label_list_button = T("List Credentials"),
            label_delete_button = T("Delete Credential"),
            msg_record_created = T("Credential added"),
            msg_record_modified = T("Credential updated"),
            msg_record_deleted = T("Credential deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Credentials registered"))

        configure(tablename,
                  context = {"person": "person_id",
                             },
                  list_fields = ["job_title_id",
                                 "start_date",
                                 "end_date",
                                 ],
                  list_layout = hrm_credential_list_layout,
                  )

        # =====================================================================
        # Skill Equivalence
        #
        # Link table between Certificates & Skills
        #
        # Used to auto-populate the relevant skills
        # - faster than runtime joins at a cost of data integrity
        #

        tablename = "hrm_certificate_skill"
        define_table(tablename,
                     certificate_id(empty = False,
                                    ondelete = "CASCADE",
                                    ),
                     skill_id(empty = False,
                              ondelete = "CASCADE",
                              ),
                     competency_id(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Skill Equivalence"),
            title_display = T("Skill Equivalence Details"),
            title_list = T("Skill Equivalences"),
            title_update = T("Edit Skill Equivalence"),
            label_list_button = T("List Skill Equivalences"),
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
        define_table(tablename,
                     course_id(empty = False,
                               ondelete = "CASCADE",
                               ),
                     certificate_id(empty = False,
                                    ondelete = "CASCADE",
                                    ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Certificate for Course"),
            title_display = T("Course Certificate Details"),
            title_list = T("Course Certificates"),
            title_update = T("Edit Course Certificate"),
            label_list_button = T("List Course Certificates"),
            label_delete_button = T("Delete Course Certificate"),
            msg_record_created = T("Course Certificate added"),
            msg_record_modified = T("Course Certificate updated"),
            msg_record_deleted = T("Course Certificate deleted"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no Course Certificates registered"))

        # =====================================================================
        # Course <> Job Titles link table
        #
        # Show which courses a person has done that are relevant to specific job roles
        #
        tablename = "hrm_course_job_title"
        define_table(tablename,
                     course_id(empty = False,
                               ondelete = "CASCADE",
                               ),
                     job_title_id(empty = False,
                                  ondelete = "CASCADE",
                                  ),
                     *s3_meta_fields())

        # =====================================================================
        # Course <> Sectors link table
        #
        # Show which courses a person has done that are relevant to specific sectors
        #
        tablename = "hrm_course_sector"
        define_table(tablename,
                     course_id(empty = False,
                               ondelete = "CASCADE",
                               ),
                     self.org_sector_id(empty = False,
                                        ondelete = "CASCADE",
                                        ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {#"hrm_competency_id": competency_id,
                "hrm_course_id": course_id,
                "hrm_skill_id": skill_id,
                "hrm_multi_skill_id": multi_skill_id,
                "hrm_multi_skill_represent": multi_skill_represent,
                "hrm_training_event_id": training_event_id,
                "hrm_certification_onaccept": self.hrm_certification_onaccept,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        dummy_listref = S3ReusableField("dummy_id", "list:reference",
                                        readable = False,
                                        writable = False)

        return {#"hrm_competency_id": lambda **attr: dummy("competency_id"),
                "hrm_course_id": lambda **attr: dummy("course_id"),
                "hrm_skill_id": lambda **attr: dummy("skill_id"),
                "hrm_multi_skill_id": lambda **attr: dummy_listref("skill_id"),
                }

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
                                                           limitby=(0, 1)
                                                           ).first()
            try:
                default = skill_type.id
            except AttributeError:
                # Create a default skill_type
                default = table.insert(name="Default")

        return default

    # -------------------------------------------------------------------------
    @staticmethod
    def competency_rating_comment():
        """ Define the comment for the HRM Competency Rating widget """

        T = current.T
        s3 = current.response.s3

        if current.request.controller == "vol":
            controller = "vol"
        else:
            controller = "hrm"
        if current.auth.s3_has_role(current.session.s3.system_roles.ADMIN):
            label_create = s3.crud_strings["hrm_competency_rating"].label_create
            comment = S3PopupLink(c = controller,
                                  f = "competency_rating",
                                  vars = {"child":"competency_id"},
                                  label = label_create,
                                  tooltip = T("Add a new competency rating to the catalog."),
                                  )
        else:
            comment = DIV(_class="tooltip",
                          _title="%s|%s" % (T("Competency Rating"),
                                            T("Level of competency this person has with this skill.")))
        if current.deployment_settings.get_hrm_skill_types():
            script = \
'''$.filterOptionsS3({
 'trigger':'skill_id',
 'target':'competency_id',
 'lookupResource':'competency',
 'lookupURL':S3.Ap.concat('/%s/skill_competencies/'),
 'msgNoRecords':'%s'
})''' % (controller, T("No Ratings for Skill Type"))
            comment = TAG[""](comment,
                              S3ScriptItem(script=script))

        return comment

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_course_onaccept(form):
        """
            Ensure that there is a Certificate created for each Course
            - only called when create_certificates_from_courses in (True, "organisation_id")
        """

        form_vars = form.vars
        course_id = form_vars.id

        db = current.db
        s3db = current.s3db
        ltable = s3db.hrm_course_certificate
        exists = db(ltable.course_id == course_id).select(ltable.id,
                                                          limitby = (0, 1)
                                                          )
        if not exists:
            name = form_vars.get("name")
            organisation_id = form_vars.get("organisation_id")
            if not name or not organisation_id:
                table = s3db.hrm_course
                course = db(table.id == course_id).select(table.name,
                                                          table.organisation_id,
                                                          limitby = (0, 1)
                                                          ).first()
                name = course.name
                organisation_id = course.organisation_id
            ctable = s3db.hrm_certificate
            certificate = db(ctable.name == name).select(ctable.id,
                                                         limitby = (0, 1)
                                                         ).first()
            if certificate:
                certificate_id = certificate.id
            else:
                if current.deployment_settings.get_hrm_create_certificates_from_courses() is True:
                    # Don't limit to Org
                    organisation_id = None
                certificate_id = ctable.insert(name = name,
                                               organisation_id = organisation_id,
                                               )

            ltable.insert(course_id = course_id,
                          certificate_id = certificate_id,
                          )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_certification_onaccept(form):
        """
            Ensure that Skills are Populated from Certifications
            - called both onaccept & ondelete
        """

        # Deletion and update have a different format
        try:
            record_id = form.vars.id
        except AttributeError:
            # Delete
            record_id = form.id

        # Read the full record
        db = current.db
        table = db.hrm_certification
        record = db(table.id == record_id).select(table.person_id,
                                                  table.deleted,
                                                  table.deleted_fk,
                                                  table.training_id,
                                                  table.number,
                                                  limitby = (0, 1),
                                                  ).first()
        if record.deleted:
            try:
                deleted_fk = json.loads(record.deleted_fk)
            except JSONERRORS:
                person_id = None
            else:
                person_id = deleted_fk.get("person_id")
            if not person_id:
                return
        else:
            person_id = record.person_id

        if not person_id:
            # This record is being created as a direct component of the Training,
            # in order to set the Number (RMS Americas usecase).
            training_id = record.training_id
            # Find the other record (created onaccept of training)
            query = (table.training_id == training_id) & \
                    (table.id != record_id)
            original = db(query).select(table.id,
                                        limitby = (0, 1),
                                        ).first()
            if original:
                # Update it with the number
                number = record.number
                original.update_record(number = number)
                # Delete this extraneous record
                db(table.id == record_id).delete()

            # Don't update any competencies
            return

        ctable = db.hrm_competency
        cstable = db.hrm_certificate_skill

        # Drop all existing competencies which came from certification
        # - this is a lot easier than selective deletion
        # @ToDo: Avoid this method as it will break Inline Component Updates
        #        if we ever use those (see hrm_training_onaccept)
        query = (ctable.person_id == person_id) & \
                (ctable.from_certification == True)
        db(query).delete()

        # Figure out which competencies we're _supposed_ to have.
        # FIXME unlimited select
        query = (table.person_id == person_id) & \
                (table.certificate_id == cstable.certificate_id) & \
                (cstable.skill_id == db.hrm_skill.id)
        certifications = db(query).select()

        # Add these competencies back in.
        # FIXME unlimited select inside loop
        # FIXME multiple implicit db queries inside nested loop
        # FIXME db.delete inside nested loop
        # FIXME unnecessary select (sub-select in Python loop)
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
    def hrm_competency_rating_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case and skill_type
        """

        name = item.data.get("name")
        skill = False
        for citem in item.components:
            if citem.tablename == "hrm_skill_type":
                cdata = citem.data
                if "name" in cdata:
                    skill = cdata.name
        if skill == False:
            return

        table = item.table
        stable = current.s3db.hrm_skill_type
        query = (table.name.lower() == s3_unicode(name).lower()) & \
                (table.skill_type_id == stable.id) & \
                (stable.value.lower() == s3_unicode(skill).lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_training_file_represent(value):
        """ File representation """

        if value:
            try:
                # Read the filename from the field value
                filename = current.db.hrm_training.file.retrieve(value)[0]
            except IOError:
                return current.T("File not found")
            else:
                return A(filename,
                         _href=URL(c="default", f="download", args=[value]))
        else:
            return current.messages["NONE"]

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_training_event_realm_entity(table, record):
        """
            Set the training_event realm entity
            - to the root Org of the Site
        """

        db = current.db
        stable = db.org_site
        query = (stable.site_id == record.site_id)
        if current.deployment_settings.get_org_branches():
            site = db(query).select(stable.organisation_id,
                                    limitby=(0, 1)).first()
            if site:
                org_id = site.organisation_id
                root_org = current.cache.ram(
                    # Common key for all users of this org & vol_service_record()
                    "root_org_%s" % org_id,
                    lambda: current.s3db.org_root_organisation(org_id),
                    time_expire=120
                    )
                otable = db.org_organisation
                org = db(otable.id == root_org).select(otable.realm_entity,
                                                       limitby=(0, 1)
                                                       ).first()
                if org:
                    return org.realm_entity
        else:
            otable = db.org_organisation
            query &= (stable.organisation_id == otable.id)
            org = db(query).select(otable.realm_entity,
                                   limitby=(0, 1)).first()
            if org:
                return org.realm_entity

        return None

# =============================================================================
def hrm_training_onvalidation(form):
    """
        If the Training is created from a Training Event (e.g. during Import),
        then auto-populate the fields from that
    """

    form_vars = form.vars
    training_event_id = form_vars.get("training_event_id", None)
    if not training_event_id:
        # Nothing to do
        return

    db = current.db
    table = db.hrm_training_event
    record = db(table.id == training_event_id).select(table.course_id,
                                                      table.start_date,
                                                      table.end_date,
                                                      table.hours,
                                                      cache = current.s3db.cache,
                                                      limitby = (0, 1),
                                                      ).first()
    try:
        form_vars.course_id = record.course_id
        form_vars.date = record.start_date
        form_vars.end_date = record.end_date
        form_vars.hours = record.hours
    except AttributeError:
        # Record not found
        return

# =============================================================================
def hrm_training_onaccept(form):
    """
        Ensure that Certifications, Hours & list:Trainings are Populated from Trainings
        Provide a Pass/Fail rating based on the Course's Pass Mark
        - called both onaccept & ondelete
    """

    # Deletion and update have a different format
    delete = False
    try:
        training_id = form.vars.id
    except AttributeError:
        training_id = form.id
        delete = True

    # Get the full record
    db = current.db
    table = db.hrm_training
    record = db(table.id == training_id).select(table.id,
                                                table.person_id,
                                                table.course_id,
                                                table.date,
                                                table.hours,
                                                table.grade,
                                                table.grade_details,
                                                table.deleted_fk,
                                                limitby=(0, 1)).first()

    if delete:
        deleted_fks = json.loads(record.deleted_fk)
        course_id = deleted_fks.get("course_id")
        person_id = deleted_fks["person_id"]
    else:
        course_id = record.course_id
        person_id = record.person_id

    s3db = current.s3db
    course_table = db.hrm_course
    settings = current.deployment_settings

    if course_id:
        course_pass_marks = settings.get_hrm_course_pass_marks()
        if course_pass_marks and not record.grade and record.grade_details:
            # Provide a Pass/Fail rating based on the Course's Pass Mark
            course = db(course_table.id == course_id).select(course_table.pass_mark,
                                                             limitby=(0, 1)
                                                             ).first()
            if course:
                if record.grade_details >= course.pass_mark:
                    # Pass
                    record.update_record(grade=8)
                else:
                    # Fail
                    record.update_record(grade=9)

    vol_experience = settings.get_hrm_vol_experience()
    if vol_experience in ("programme", "both"):
        # Check if this person is a volunteer
        hrtable = db.hrm_human_resource
        query = (hrtable.person_id == person_id) & \
                (hrtable.deleted == False)
        vol = db(query).select(hrtable.type,
                               limitby=(0, 1)).first()

        if vol and vol.type == 2:
            # Update Hours
            ptable = s3db.hrm_programme_hours
            query = (ptable.training_id == training_id)
            if delete:
                resource = s3db.resource("hrm_programme_hours", filter=query)
                # Automatically propagates to Active Status
                resource.delete()
            else:
                date = record.date
                hours = record.hours
                # Update or Insert?
                exists = db(query).select(ptable.id,
                                          ptable.date,
                                          ptable.hours,
                                          limitby=(0, 1)).first()

                if exists:
                    if date != exists.date or \
                       hours != exists.hours:
                        db(query).update(date=date, hours=hours)
                        ph_id = exists.id
                    else:
                        # Nothing to propagate
                        ph_id = None
                else:
                    ph_id = ptable.insert(training_id = training_id,
                                          person_id = person_id,
                                          date = date,
                                          hours = hours,
                                          training = True)
                if ph_id:
                    # Propagate to Active Status
                    form = Storage()
                    form.vars = Storage()
                    form.vars.id = ph_id
                    hrm_programme_hours_onaccept(form)

    # Update Trainings list:reference for Contains filter
    ltable = db.hrm_trainings

    query = (table.person_id == person_id) & \
            (table.deleted == False)
    courses = db(query).select(table.course_id,
                               distinct = True,
                               )
    courses = [c.course_id for c in courses if c.course_id is not None]
    exists = db(ltable.person_id == person_id).select(ltable.id,
                                                      limitby=(0, 1)).first()
    if exists:
        exists.update_record(course_id = courses)
    else:
        ltable.insert(person_id = person_id,
                      course_id = courses,
                      )

    # Update Certifications
    ctable = db.hrm_certification
    ltable = db.hrm_course_certificate

    # Old: Breaks Inline Component Updates since record_id changes
    # Drop all existing certifications which came from trainings
    # - this is a lot easier than selective deletion.

    if delete:
        # Remove certifications if provided by this training and no other
        # training led to it
        query = (ctable.training_id == training_id) & \
                (ctable.deleted == False)
        certifications = db(query).select(ctable.id,
                                          ctable.certificate_id)
        for certification in certifications:
            query = (ltable.certificate_id == certification.certificate_id) & \
                    (ltable.deleted == False) & \
                    (ltable.course_id == table.course_id) & \
                    (table.deleted == False)
            trainings = db(query).select(table.id,
                                         table.date,
                                         limitby = (0, 1),
                                         orderby = "date desc",
                                         )
            if trainings:
                # Update the training_id
                certification.update_record(training_id = trainings.first().id)
            else:
                # Remove the certification
                query = (ctable.id == certification.id)
                resource = s3db.resource("hrm_certification", filter=query)
                # Automatically propagates to Skills
                resource.delete()
    else:
        if course_id:
            # Which certificates does this course give?
            query = (ltable.course_id == course_id) & \
                    (ltable.deleted == False)
            certificates = db(query).select(ltable.certificate_id)
            # Lookup user_id to allow the user to see their certifications
            ptable = db.pr_person
            putable = s3db.pr_person_user
            query = (ptable.id == person_id) & \
                    (putable.pe_id == ptable.pe_id)
            user = db(query).select(putable.user_id,
                                    limitby = (0, 1)
                                    ).first()
            if user:
                user_id = user.user_id
            else:
                # Record has no special ownership
                user_id = None
            # Add any missing certifications
            hrm_certification_onaccept = s3db.hrm_certification_onaccept
            for certificate in certificates:
                certification_id = ctable.update_or_insert(
                        person_id = person_id,
                        certificate_id = certificate.certificate_id,
                        training_id = training_id,
                        comments = "Added by training",
                        owned_by_user = user_id,
                        )
                # Propagate to Skills
                form = Storage()
                form.vars = Storage()
                form.vars.id = certification_id
                hrm_certification_onaccept(form)

# =============================================================================
class S3HREventStrategyModel(S3Model):
    """
        (Training) Events <> Strategies Link Table
    """

    names = ("hrm_event_strategy",
             )

    def model(self):

        # =====================================================================
        # (Training) Events <> Strategies Link Table
        #
        tablename = "hrm_event_strategy"
        self.define_table(tablename,
                          self.hrm_training_event_id(empty = False,
                                                     ondelete = "CASCADE",
                                                     ),
                          self.project_strategy_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3HREventProgrammeModel(S3Model):
    """
        (Training) Events <> Programmes Link Table
    """

    names = ("hrm_event_programme",
             )

    def model(self):

        # =====================================================================
        # (Training) Events <> Programmes Link Table
        #
        tablename = "hrm_event_programme"
        self.define_table(tablename,
                          self.hrm_training_event_id(empty = False,
                                                     ondelete = "CASCADE",
                                                     ),
                          self.hrm_programme_id(empty = False,
                                                ondelete = "CASCADE",
                                                ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3HREventProjectModel(S3Model):
    """
        (Training) Events <> Projects Link Table
    """

    names = ("hrm_event_project",
             )

    def model(self):

        # =====================================================================
        # (Training) Events <> Projects Link Table
        #
        tablename = "hrm_event_project"
        self.define_table(tablename,
                          self.hrm_training_event_id(empty = False,
                                                     ondelete = "CASCADE",
                                                     ),
                          self.project_project_id(empty = False,
                                                  ondelete = "CASCADE",
                                                  ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3HREventAssessmentModel(S3Model):
    """
        (Training) Events <> Data Collection Assessments Link Table
         Can be used for:
            * Needs Assessment / Readiness checklist
            * Tests (either for checking learning/application or for final grade)
            * Evaluation (currently the only use case - for IFRC's Bangkok CCST)
    """

    names = ("hrm_event_target",
             )

    def model(self):

        T = current.T

        # @ToDo: Deployment_setting if use expanded beyond Bangkok CCST
        type_opts = {1: T("Other"),
                     3: T("3-month post-event Evaluation"),
                     12: T("12-month post-event Evaluation"),
                     }

        # =====================================================================
        # (Training) Events <> DC Targets Link Table
        #
        tablename = "hrm_event_target"
        self.define_table(tablename,
                          self.hrm_training_event_id(empty = False,
                                                     ondelete = "CASCADE",
                                                     ),
                          self.dc_target_id(empty = False,
                                            ondelete = "CASCADE",
                                            ),
                          Field("survey_type",
                                default = 1,
                                label = T("Type"),
                                requires = IS_EMPTY_OR(IS_IN_SET(type_opts)),
                                represent = S3Represent(options = type_opts),
                                ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3HRAppraisalModel(S3Model):
    """
        Appraisal for an HR
        - can be for a specific Mission or routine annual appraisal
    """

    names = ("hrm_appraisal",
             "hrm_appraisal_document",
             )

    def model(self):

        T = current.T
        configure = self.configure
        define_table = self.define_table
        person_id = self.pr_person_id

        if current.deployment_settings.get_org_autocomplete():
            org_widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
        else:
            org_widget = None

        # =====================================================================
        # Appraisal
        #

        tablename = "hrm_appraisal"
        define_table(tablename,
                     person_id(),
                     # For Mission or Event
                     Field("code",
                           label = T("Code"),
                           readable = False,
                           writable = False,
                           ),
                     self.org_organisation_id(widget = org_widget),
                     self.hrm_job_title_id(),
                     s3_date(),
                     Field("rating", "float",
                           label = T("Rating"),
                           # @ToDo: make this configurable
                           # 1 to 4
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(1, 5)
                                      ),
                           widget = S3SliderWidget(step=0.1,
                                                   type="float"),
                           ),
                     person_id("supervisor_id",
                               label = T("Supervisor"),
                               widget = S3AddPersonWidget(),
                               ),
                     s3_comments(),
                     *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Appraisal"),
            title_display = T("Appraisal Details"),
            title_list = T("Appraisals"),
            title_update = T("Edit Appraisal"),
            label_list_button = T("List of Appraisals"),
            label_delete_button = T("Delete Appraisal"),
            msg_record_created = T("Appraisal added"),
            msg_record_modified = T("Appraisal updated"),
            msg_record_deleted = T("Appraisal deleted"),
            msg_no_match = T("No Appraisals found"),
            msg_list_empty = T("Currently no Appraisals entered"))

        crud_form = S3SQLCustomForm("organisation_id",
                                    "job_title_id",
                                    "date",
                                    "rating",
                                    "supervisor_id",
                                    S3SQLInlineComponent("document",
                                                         label = T("Files"),
                                                         link = False,
                                                         fields = ["file"],
                                                         ),
                                    "comments",
                                    )

        configure(tablename,
                  context = {"person": "person_id",
                             #"organisation": "organisation_id",
                             },
                  create_onaccept = self.hrm_appraisal_create_onaccept,
                  crud_form = crud_form,
                  list_fields = ["id",
                                 # Normally accessed via component
                                 #"person_id",
                                 "date",
                                 "organisation_id",
                                 "job_title_id",
                                 "supervisor_id",
                                 "comments",
                                 "document.file",
                                 ],
                  #list_layout = hrm_render_appraisal,
                  orderby = "hrm_appraisal.date desc",
                  )

        # Components
        self.add_components(tablename,
                            # Appraisal Documents
                            doc_document={"link": "hrm_appraisal_document",
                                          "joinby": "appraisal_id",
                                          "key": "document_id",
                                          "autodelete": False,
                                         },
                           )

        # =====================================================================
        # Appraisal Documents
        #

        tablename = "hrm_appraisal_document"
        define_table(tablename,
                     Field("appraisal_id", "reference hrm_appraisal"),
                     self.doc_document_id(empty=False),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.hrm_appraisal_document_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_appraisal_create_onaccept(form):
        """
            Link Appraisal to Assignment
        """

        mission_id = current.request.get_vars.get("mission_id", None)
        if not mission_id:
            return

        record_id = form.vars.id
        db = current.db
        s3db = current.s3db
        atable = s3db.deploy_assignment
        hatable = db.hrm_appraisal
        hrtable = db.hrm_human_resource
        query = (hatable.id == record_id) & \
                (hrtable.person_id == hatable.person_id) & \
                (atable.human_resource_id == hrtable.id) & \
                (atable.mission_id == mission_id)
        assignment = db(query).select(atable.id,
                                      limitby=(0, 1)
                                      ).first()
        if not assignment:
            return
        db.deploy_assignment_appraisal.insert(assignment_id = assignment.id,
                                              appraisal_id = record_id,
                                              )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_appraisal_document_onaccept(form):
        """
            Set the doc_id to that of the HRM, so that it also appears there
        """

        db = current.db
        s3db = current.s3db
        atable = db.hrm_appraisal
        ltable = db.hrm_appraisal_document
        htable = s3db.hrm_human_resource
        query = (ltable.id == form.vars.id) & \
                (ltable.appraisal_id == atable.id) & \
                (atable.person_id == htable.person_id) & \
                (htable.deleted != False)
        row = db(query).select(htable.doc_id,
                               ltable.document_id,
                               limitby=(0, 1)).first()
        if row:
            document_id = row["hrm_appraisal_document.document_id"]
            doc_id = row["hrm_human_resource.doc_id"]
            db(db.doc_document.id == document_id).update(doc_id = doc_id)

# =============================================================================
class S3HRExperienceModel(S3Model):
    """
        Record a person's work experience
    """

    names = ("hrm_experience",)

    def model(self):

        T = current.T
        person_id = self.pr_person_id

        settings = current.deployment_settings

        if settings.get_org_autocomplete():
            org_widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
        else:
            org_widget = None

        site_label = settings.get_org_site_label()
        if settings.get_org_site_autocomplete():
            site_widget = S3SiteAutocompleteWidget()
            site_comment = DIV(_class="tooltip",
                               _title="%s|%s" % (site_label,
                                                 current.messages.AUTOCOMPLETE_HELP))
        else:
            site_widget = None
            site_comment = None

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
        hr_type = self.hrm_human_resource.type

        activity_types = settings.get_hrm_activity_types()
        if not isinstance(activity_types, dict):
            activity_type_requires = None
            activity_type_represent = None
            use_activity_types = False
        else:
            activity_type_opts = {} #{"other": T("Other")}
            for k, v in activity_types.items():
                activity_type_opts[k] = T(v)
            activity_type_requires = IS_EMPTY_OR(IS_IN_SET(activity_type_opts))
            activity_type_represent = S3Represent(options=activity_type_opts)
            use_activity_types = True

        tablename = "hrm_experience"
        self.define_table(tablename,
                          person_id(),
                          # Employment type (staff or volunteer)
                          Field("employment_type", "integer",
                                default = hr_type.default,
                                represent = hr_type.represent,
                                requires = hr_type.requires,
                                ),
                          # Activity type (e.g. "RDRT Mission")
                          Field("activity_type",
                                represent = activity_type_represent,
                                requires = activity_type_requires,
                                # Expose only when there are options defined
                                readable = use_activity_types,
                                writable = use_activity_types,
                                ),
                          # For Events
                          Field("code",
                                label = T("Code"),
                                readable = False,
                                writable = False,
                                ),
                          self.org_organisation_id(widget = org_widget),
                          self.hrm_department_id(readable=False,
                                                 writable=False,
                                                 ),
                          # Alternate free-text form especially suitable for volunteers
                          Field("organisation",
                                label = T("Organization"),
                                readable = False,
                                writable = False,
                                ),
                          # Component, not instance
                          self.super_link("site_id", "org_site",
                                          comment = site_comment,
                                          label = site_label,
                                          orderby = "org_site.name",
                                          #readable = True,
                                          represent = self.org_site_represent,
                                          widget = site_widget,
                                          #writable = True,
                                          ),
                          self.hrm_job_title_id(),
                          # Alternate free-text form especially suitable for volunteers
                          Field("job_title",
                                label = T("Position"),
                                readable = False,
                                writable = False,
                                ),
                          Field("responsibilities",
                                label = T("Key Responsibilities"),
                                ),
                          s3_date("start_date",
                                  label = T("Start Date"),
                                  set_min = "#hrm_experience_end_date",
                                  ),
                          s3_date("end_date",
                                  label = T("End Date"),
                                  set_max = "#hrm_experience_start_date",
                                  start_field = "hrm_experience_start_date",
                                  default_interval = 12,
                                  ),
                          Field("hours", "float",
                                label = T("Hours"),
                                ),
                          #Field("place",
                          #      label = T("Place"),
                          #      ),
                          self.gis_location_id(),
                          person_id("supervisor_id",
                                    label = T("Supervisor"),
                                    widget = S3AddPersonWidget(),
                                    ),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Professional Experience"),
            title_display = T("Professional Experience Details"),
            title_list = T("Professional Experience"),
            title_update = T("Edit Professional Experience"),
            label_list_button = T("List of Professional Experience"),
            label_delete_button = T("Delete Professional Experience"),
            msg_record_created = T("Professional Experience added"),
            msg_record_modified = T("Professional Experience updated"),
            msg_record_deleted = T("Professional Experience deleted"),
            msg_no_match = T("No Professional Experience found"),
            msg_list_empty = T("Currently no Professional Experience entered"))

        self.configure(tablename,
                       context = {"person": "person_id",
                                  "organisation": "organisation_id",
                                  },
                       list_fields = ["id",
                                      # Normally accessed via component
                                      #"person_id",
                                      "start_date",
                                      "end_date",
                                      "organisation_id",
                                      "employment_type",
                                      "job_title_id",
                                      "location_id",
                                      "comments",
                                      ],
                       list_layout = hrm_experience_list_layout,
                       orderby = "hrm_experience.start_date desc",
                       )

        # Components
        self.add_components(tablename,
                            # Assignments
                            deploy_assignment = {"name": "assignment",
                                                 "link": "deploy_assignment_experience",
                                                 "joinby": "experience_id",
                                                 "key": "assignment_id",
                                                 "autodelete": False,
                                                 },
                            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3HRAwardModel(S3Model):
    """ Data model for staff awards """

    names = ("hrm_award_type",
             "hrm_award",
             )

    def model(self):

        T = current.T
        db = current.db

        define_table = self.define_table

        # =====================================================================
        # Award types
        #
        tablename = "hrm_award_type"
        define_table(tablename,
                     self.org_organisation_id(
                        requires = self.org_organisation_requires(updateable=True),
                     ),
                     Field("name",
                           label = T("Award Type"),
                           ),
                     *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("name",
                                                            "organisation_id",
                                                            ),
                                                 ),
                       )

        ADD_AWARD_TYPE = T("Create Award Type")
        award_type_represent = hrm_OrgSpecificTypeRepresent(lookup="hrm_award_type")

        # =====================================================================
        # Awards
        #
        tablename = "hrm_award"
        define_table(tablename,
                     self.pr_person_id(),
                     s3_date(),
                     Field("awarding_body",
                           label = T("Awarding Body"),
                           ),
                     Field("award_type_id", "reference hrm_award_type",
                           label = T("Award Type"),
                           represent = award_type_represent,
                           requires = IS_ONE_OF(db,
                                                "hrm_award_type.id",
                                                award_type_represent,
                                                ),
                           comment = S3PopupLink(f = "award_type",
                                                 label = ADD_AWARD_TYPE,
                                                 ),
                           ),
                     *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Award"),
            title_display = T("Award Details"),
            title_list = T("Awards"),
            title_update = T("Edit Award"),
            label_list_button = T("List Awards"),
            label_delete_button = T("Delete Award"),
            msg_record_created = T("Award added"),
            msg_record_modified = T("Award updated"),
            msg_record_deleted = T("Award removed"),
            msg_no_match = T("No entries found"),
            msg_list_empty = T("Currently no awards registered"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3HRDisciplinaryActionModel(S3Model):
    """ Data model for staff disciplinary record """

    names = ("hrm_disciplinary_type",
             "hrm_disciplinary_action",
             )

    def model(self):

        T = current.T

        define_table = self.define_table

        # =====================================================================
        # Types of disciplinary action
        #
        tablename = "hrm_disciplinary_type"
        define_table(tablename,
                     self.org_organisation_id(
                        requires = self.org_organisation_requires(updateable=True),
                     ),
                     Field("name",
                           label = T("Disciplinary Action Type"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("name",
                                                            "organisation_id",
                                                            ),
                                                 ),
                       )

        disciplinary_type_represent = hrm_OrgSpecificTypeRepresent(lookup=tablename)

        # =====================================================================
        # Disciplinary record
        tablename = "hrm_disciplinary_action"
        define_table(tablename,
                     self.pr_person_id(),
                     s3_date(),
                     Field("disciplinary_body"),
                     Field("disciplinary_type_id", "reference hrm_disciplinary_type",
                           label = T("Disciplinary Action Type"),
                           represent = disciplinary_type_represent,
                           requires = IS_ONE_OF(current.db,
                                                "hrm_disciplinary_type.id",
                                                disciplinary_type_represent,
                                                ),
                           comment = S3PopupLink(f = "disciplinary_type",
                                                 label = T("Add Disciplinary Action Type"),
                                                 ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3HRTagModel(S3Model):
    """ Arbitrary Key:Value Tags for Human Resources """

    names = ("hrm_human_resource_tag",
             )

    def model(self):

        T = current.T

        # =====================================================================
        # Human Resource Tags
        #
        tablename = "hrm_human_resource_tag"
        self.define_table(tablename,
                          self.hrm_human_resource_id(empty = False,
                                                     ondelete = "CASCADE",
                                                     ),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("human_resource_id",
                                                            "tag",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3HRProgrammeModel(S3Model):
    """
        Programmes
            - record Volunteer Hours
            - categorise (Training) Events
        These are separate to the Project module's Programmes
        - @ToDo: setting to make them the same?
    """

    names = ("hrm_programme",
             "hrm_programme_hours",
             "hrm_programme_id",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        root_org = auth.root_org()

        # =====================================================================
        # Progammes
        #

        tablename = "hrm_programme"
        define_table(tablename,
                     Field("name", notnull=True, length=64,
                           label = T("Name"),
                           represent = T,
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("name_long",
                           label = T("Long Name"),
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     self.org_organisation_id(default = root_org,
                                              readable = is_admin,
                                              writable = is_admin,
                                              ),
                     s3_comments(comment = None,
                                 label = T("Description"),
                                 ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Program"),
            title_display = T("Program Details"),
            title_list = T("Programs"),
            title_update = T("Edit Program"),
            label_list_button = T("List Programs"),
            label_delete_button = T("Delete Program"),
            msg_record_created = T("Program added"),
            msg_record_modified = T("Program updated"),
            msg_record_deleted = T("Program deleted"),
            msg_list_empty = T("Currently no programs registered"))

        label_create = crud_strings[tablename].label_create
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        represent = S3Represent(lookup=tablename, translate=True)
        programme_id = S3ReusableField("programme_id", "reference %s" % tablename,
            label = T("Program"),
            ondelete = "SET NULL",
            represent = represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "hrm_programme.id",
                                  represent,
                                  filterby="organisation_id",
                                  filter_opts=filter_opts)),
            sortby = "name",
            comment = S3PopupLink(f = "programme",
                                  label = label_create,
                                  title = label_create,
                                  tooltip = T("Add a new program to the catalog."),
                                  ),
            )

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",
                                                       "organisation_id",
                                                       ),
                                            ),
                  )

        # Components
        self.add_components(tablename,
                            hrm_programme_hours = {"name": "person",
                                                   "joinby": "programme_id",
                                                   },
                            # Uncomment if-required for reporting
                            #hrm_training_event = {"link": "hrm_event_programme",
                            #                      "joinby": "programme_id",
                            #                      "key": "training_event_id",
                            #                      "actuate": "hide",
                            #                      },
                            )

        # =====================================================================
        # Programmes <> Persons Link Table
        #
        vol_roles = current.deployment_settings.get_hrm_vol_roles()

        tablename = "hrm_programme_hours"
        define_table(tablename,
                     self.pr_person_id(
                        ondelete = "CASCADE",
                        represent = self.pr_PersonRepresent(show_link=True)
                        ),
                     programme_id(),
                     self.hrm_job_title_id(readable = vol_roles,
                                           writable = vol_roles,
                                           ),
                     Field("contract",
                           label = T("Contract Number"),
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("event",
                           label = T("Event Name"),
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("place",
                           label = T("Place"),
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     s3_date(future = 0),
                     s3_date("end_date",
                             label = T("End Date"),
                             ),
                     Field("hours", "float",
                           label = T("Hours"),
                           ),
                     # Training records are auto-populated
                     Field("training", "boolean",
                           default = False,
                           label = T("Type"),
                           represent = lambda opt: \
                                       T("Training") if opt else T("Work"),
                           writable = False,
                           ),
                     Field("training_id", self.hrm_training,
                           label = T("Course"),
                           represent = hrm_TrainingRepresent(),
                           writable = False,
                           ),
                     Field.Method("month", hrm_programme_hours_month),
                     s3_comments(comment = None),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Hours"),
            title_display = T("Hours Details"),
            title_list = T("Hours"),
            title_update = T("Edit Hours"),
            title_upload = T("Import Hours"),
            label_list_button = T("List Hours"),
            label_delete_button = T("Delete Hours"),
            msg_record_created = T("Hours added"),
            msg_record_modified = T("Hours updated"),
            msg_record_deleted = T("Hours deleted"),
            msg_list_empty = T("Currently no hours recorded for this volunteer"))

        filter_widgets = [
            S3OptionsFilter("person_id$human_resource.organisation_id",
                            # Doesn't support translations
                            #represent="%(name)s",
                            ),
            S3OptionsFilter("programme_id",
                            # Doesn't support translation
                            #represent = "%(name)s",
                            ),
            S3OptionsFilter("job_title_id",
                            #label = T("Volunteer Role"),
                            # Doesn't support translation
                            #represent = "%(name)s",
                            ),
            S3DateFilter("date",
                         hide_time = True,
                         ),
            ]

        report_fields = ["training",
                         "programme_id",
                         "job_title_id",
                         "training_id",
                         (T("Month"), "month"),
                         "hours",
                         "person_id$gender",
                         ]

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = report_fields,
                                 defaults = Storage(rows = "programme_id",
                                                    cols = "month",
                                                    fact = "sum(hours)",
                                                    totals = True,
                                                    )
                                 )

        configure(tablename,
                  context = {"person": "person_id",
                             },
                  extra_fields = ["date"],
                  filter_widgets = filter_widgets,
                  list_fields = ["training",
                                 "programme_id",
                                 "job_title_id",
                                 "training_id",
                                 "date",
                                 "hours",
                                 ],
                  onaccept = hrm_programme_hours_onaccept,
                  ondelete = hrm_programme_hours_onaccept,
                  orderby = "hrm_programme_hours.date desc",
                  report_options = report_options,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"hrm_programme_id": programme_id,
                }

# =============================================================================
class S3HRShiftModel(S3Model):
    """
        Shifts
    """

    names = ("hrm_shift_template",
             "hrm_shift",
             "hrm_shift_id",
             "hrm_human_resource_shift",
             )

    def model(self):

        

        T = current.T

        #configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method

        job_title_id = self.hrm_job_title_id
        skill_id = self.hrm_skill_id

        db = current.db

        DAYS_OF_WEEK = {1: T("Monday"),
                        2: T("Tuesday"),
                        3: T("Wednesday"),
                        4: T("Thursday"),
                        5: T("Friday"),
                        6: T("Saturday"),
                        7: T("Sunday"),
                        }

        # ---------------------------------------------------------------------
        # Shift Templates
        #
        tablename = "hrm_shift_template"
        define_table(tablename,
                     job_title_id(),
                     skill_id(),
                     Field("day_of_week", "integer",
                           requires = IS_IN_SET(DAYS_OF_WEEK),
                           represent = S3Represent(options = DAYS_OF_WEEK),
                           ),
                     s3_time("start_time",
                             empty = False,
                             label = T("Start Time"),
                             # Could be the next day
                             #set_min = "#hrm_shift_template_end_time",
                             ),
                     s3_time("end_time",
                             empty = False,
                             label = T("End Time"),
                             # Could be the next day
                             #set_max = "#hrm_shift_template_start_time",
                             ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("New Shift"),
            title_display = T("Shift Details"),
            title_list = T("Shifts"),
            title_update = T("Edit Shift"),
            #title_upload = T("Import Shift data"),
            label_list_button = T("List Shifts"),
            msg_record_created = T("Shift added"),
            msg_record_modified = T("Shift updated"),
            msg_record_deleted = T("Shift deleted"),
            msg_list_empty = T("No Shifts defined"),
            )

        # ---------------------------------------------------------------------
        # Shifts
        #
        tablename = "hrm_shift"
        define_table(tablename,
                     job_title_id(),
                     skill_id(),
                     s3_datetime("start_date",
                                 label = T("Start Date"),
                                 set_min = "#hrm_shift_end_date",
                                 ),
                     s3_datetime("end_date",
                                 label = T("End Date"),
                                 set_max = "#hrm_shift_start_date",
                                 ),
                     s3_comments(),
                     *s3_meta_fields())

        represent = S3Represent(lookup=tablename, fields=["start_date", "end_date"])
        shift_id = S3ReusableField("shift_id", "reference %s" % tablename,
                                   label = T("Shift"),
                                   ondelete = "RESTRICT",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "hrm_shift.id",
                                                          represent)),
                                   comment = S3PopupLink(c = "hrm",
                                                         f = "shift",
                                                         label = T("Create Shift"),
                                                         ),
                                   )

        self.add_components(tablename,
                            hrm_human_resource_shift = {"joinby": "shift_id",
                                                        "multiple": False,
                                                        }
                            )

        crud_form = S3SQLCustomForm("job_title_id",
                                    "skill_id",
                                    "start_date",
                                    "end_date",
                                    "comments",
                                    (T("Assigned"), "human_resource_shift.human_resource_id"),
                                    )

        list_fields = ["job_title_id",
                       "skill_id",
                       "start_date",
                       "end_date",
                       "comments",
                       (T("Assigned"), "human_resource_shift.human_resource_id"),
                       ]

        self.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )
        
        # Custom Method to Assign HRs
        STAFF = current.deployment_settings.get_hrm_staff_label()
        filter_widgets = [S3DateFilter("available",
                                       label = T("Available"),
                                       # Use custom selector to prevent automatic
                                       # parsing (which would result in an error)
                                       selector = "available",
                                       hide_time = False,
                                       ),
                          #if settings.get_hrm_use_skills():
                          S3OptionsFilter("competency.skill_id",
                                          # Better to default (easier to customise/consistency)
                                          #label = T("Skill"),
                                          ),
                          S3OptionsFilter("job_title_id",
                                          ),
                          S3OptionsFilter("type",
                                          label = T("Type"),
                                          options = {1: STAFF,
                                                     2: T("Volunteer"),
                                                     },
                                          cols = 2,
                                          hidden = True,
                                          ),
                          ]
        #if settings.get_hrm_multiple_orgs():
        #    if settings.get_org_branches():
        #        append_filter(S3HierarchyFilter("organisation_id",
        #                                        leafonly = False,
        #                                        ))
        #    else:
        #        append_filter(S3OptionsFilter("organisation_id",
        #                                      search = True,
        #                                      header = "",
        #                                      #hidden = True,
        #                                      ))

        list_fields = ["id",
                       "person_id",
                       "job_title_id",
                       "start_date",
                       (T("Skills"), "person_id$competency.skill_id"),
                       ]

        set_method("hrm", "shift",
                   method = "assign",
                   action = self.hrm_AssignMethod(component = "human_resource_shift",
                                                  next_tab = "facility",
                                                  filter_widgets = filter_widgets,
                                                  list_fields = list_fields,
                                                  rheader = hrm_rheader,
                                                  ))

        def facility_redirect(r, **attr):
            """
                Redirect to the Facility's Shifts tab 
            """

            s3db = current.s3db

            # Find the Facility
            ltable = s3db.org_site_shift
            ftable = s3db.org_facility
            query = (ltable.shift_id == r.id) & \
                    (ltable.site_id == ftable.site_id)
            facility = current.db(query).select(ftable.id,
                                                limitby = (0, 1)
                                                ).first()
            redirect(URL(c = "org",
                         f = "facility",
                         args = [facility.id, "shift"],
                         ))

        set_method("hrm", "shift",
                   method = "facility",
                   action = facility_redirect)

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("New Shift"),
            title_display = T("Shift Details"),
            title_list = T("Shifts"),
            title_update = T("Edit Shift"),
            #title_upload = T("Import Shift data"),
            label_list_button = T("List Shifts"),
            msg_record_created = T("Shift added"),
            msg_record_modified = T("Shift updated"),
            msg_record_deleted = T("Shift deleted"),
            msg_list_empty = T("No Shifts defined"),
            )

        # ---------------------------------------------------------------------
        # Shifts <> Human Resources
        #
        # @ToDo: Replace with hrm_shift_person as it's the Person who should be
        #        busy, not just the HR
        #
        tablename = "hrm_human_resource_shift"
        define_table(tablename,
                     shift_id(),
                     self.hrm_human_resource_id(writable = False),
                     #s3_comments(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"hrm_shift_id": shift_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return {"hrm_shift_id": lambda **attr: dummy("shift_id"),
                }

# =============================================================================
def hrm_programme_hours_month(row):
    """
        Virtual field for hrm_programme_hours - returns the date of the first
        day of the month of this entry, used for programme hours report.

        Requires "date" to be in the additional report_fields

        @param row: the Row
    """

    try:
        thisdate = row["hrm_programme_hours.date"]
    except AttributeError:
        return current.messages["NONE"]
    if not thisdate:
        return current.messages["NONE"]

    #thisdate = thisdate.date()
    month = thisdate.month
    year = thisdate.year
    first = datetime.date(year, month, 1)

    return first.strftime("%y-%m")

# =============================================================================
def hrm_programme_hours_onaccept(form):
    """
        Update the Active Status for the volunteer
        - called both onaccept & ondelete
    """

    vol_active = current.deployment_settings.get_hrm_vol_active()
    if not callable(vol_active):
        # Nothing to do (either field is disabled or else set manually)
        return

    # Deletion and update have a different format
    delete = False
    try:
        record_id = form.vars.id
    except AttributeError:
        record_id = form.id
        delete = True

    # Get the full record
    db = current.db
    table = db.hrm_programme_hours
    record = db(table.id == record_id).select(table.person_id,
                                              table.deleted_fk,
                                              limitby=(0, 1),
                                              ).first()

    if delete:
        deleted_fks = json.loads(record.deleted_fk)
        person_id = deleted_fks["person_id"]
    else:
        person_id = record.person_id

    # Recalculate the Active Status for this Volunteer
    active = vol_active(person_id)

    # Read the current value
    s3db = current.s3db
    dtable = s3db.vol_details
    htable = s3db.hrm_human_resource
    query = (htable.person_id == person_id) & \
            (dtable.human_resource_id == htable.id)
    row = db(query).select(dtable.id,
                           dtable.active,
                           limitby=(0, 1),
                           ).first()
    if row:
        if row.active != active:
            # Update
            db(dtable.id == row.id).update(active=active)
    else:
        # Create record
        row = db(htable.person_id == person_id).select(htable.id,
                                                       limitby=(0, 1),
                                                       ).first()
        if row:
            dtable.insert(human_resource_id = row.id,
                          active = active,
                          )

# =============================================================================
class hrm_AssignMethod(S3Method):
    """
        Custom Method to allow human resources to be assigned to something
        e.g. Incident, Project, Site, Vehicle

        @ToDo: be able to filter by deployable status for the role
    """

    # -------------------------------------------------------------------------
    def __init__(self,
                 component,
                 next_tab = "human_resource",
                 types = None,
                 filter_widgets = None,
                 list_fields = None,
                 rheader = None,
                 ):
        """
            @param component: the Component in which to create records
            @param next_tab: the component/method to redirect to after assigning
            @param types: a list of types to pick from: Staff, Volunteers, Deployables
            @param filter_widgets: a custom list of FilterWidgets to show
            @param list_fields: a custom list of Fields to show
            @param rheader: an rheader to show
        """

        self.component = component
        self.next_tab = next_tab
        self.types = types
        self.filter_widgets = filter_widgets
        self.list_fields = list_fields
        self.rheader = rheader

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        try:
            component = r.resource.components[self.component]
        except KeyError:
            current.log.error("Invalid Component!")
            raise

        if component.link:
            component = component.link

        tablename = component.tablename

        # Requires permission to create component
        authorised = current.auth.s3_has_permission("create", tablename)
        if not authorised:
            r.unauthorised()

        settings = current.deployment_settings

        types = self.types
        if not types:
            if settings.has_module("vol"):
                types = (1, 2)
            else:
                # Staff
                types = (1,)
        if types == (2,):
            controller = "vol"
        else:
            controller = "hrm"

        T = current.T
        db = current.db
        s3db = current.s3db

        table = s3db[tablename]
        fkey = component.fkey
        record = r.record
        if fkey in record:
            # SuperKey
            record_id = record[fkey]
        else:
            record_id = r.id

        get_vars = r.get_vars
        response = current.response
        output = None

        if r.http == "POST":
            added = 0
            post_vars = r.post_vars
            if all([n in post_vars for n in ("assign", "selected", "mode")]):

                selected = post_vars.selected
                if selected:
                    selected = selected.split(",")
                else:
                    selected = []

                if post_vars.mode == "Exclusive":
                    # 'Select All' ticked or all rows selected manually
                    if "filterURL" in post_vars:
                        filters = S3URLQuery.parse_url(post_vars.filterURL)
                    else:
                        filters = None
                    query = ~(FS("id").belongs(selected))
                    resource = s3db.resource("hrm_human_resource",
                                             alias = self.component,
                                             filter = query,
                                             vars = filters)
                    rows = resource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

                if component.multiple:
                    # Prevent multiple entries in the link table
                    query = (table.human_resource_id.belongs(selected)) & \
                            (table[fkey] == record_id) & \
                            (table.deleted != True)
                    rows = db(query).select(table.id)
                    rows = dict((row.id, row) for row in rows)
                    onaccept = component.get_config("create_onaccept",
                                                    component.get_config("onaccept", None))
                    for human_resource_id in selected:
                        try:
                            hr_id = int(human_resource_id.strip())
                        except ValueError:
                            continue
                        if hr_id not in rows:
                            link = Storage(human_resource_id = human_resource_id)
                            link[fkey] = record_id
                            _id = table.insert(**link)
                            if onaccept:
                                link["id"] = _id
                                form = Storage(vars = link)
                                onaccept(form)
                            added += 1
                else:
                    human_resource_id = selected[0]
                    exists = db(table[fkey] == record_id).select(table.id,
                                                                 limitby = (0, 1)
                                                                 ).first()
                    if exists:
                        onaccept = component.get_config("update_onaccept",
                                                        component.get_config("onaccept", None))
                        
                        exists.update_record(human_resource_id = human_resource_id)
                        if onaccept:
                            link = Storage(id = exists.id,
                                           human_resource_id = human_resource_id)
                            link[fkey] = record_id
                            form = Storage(vars = link)
                            onaccept(form)
                    else:
                        onaccept = component.get_config("create_onaccept",
                                                        component.get_config("onaccept", None))
                        link = Storage(human_resource_id = human_resource_id)
                        link[fkey] = record_id
                        _id = table.insert(**link)
                        if onaccept:
                            link["id"] = _id
                            form = Storage(vars = link)
                            onaccept(form)
                    added += 1

            if r.representation == "popup":
                # Don't redirect, so we retain popup extension & so close popup
                response.confirmation = T("%(number)s assigned") % \
                                            {"number": added}
                output = {}
            else:
                current.session.confirmation = T("%(number)s assigned") % \
                                                    {"number": added}
                if added > 0:
                    redirect(URL(args=[r.id, self.next_tab], vars={}))
                else:
                    redirect(URL(args=r.args, vars={}))

        elif r.http == "GET":

            representation = r.representation

            # Filter widgets
            if self.filter_widgets is not None:
                filter_widgets = self.filter_widgets
            else:
                if controller == "vol":
                    resource_type = "volunteer"
                elif len(types) == 1:
                    resource_type = "staff"
                else:
                    # Both
                    resource_type = None
                if r.controller == "req":
                    module = "req"
                else:
                    module = controller

                filter_widgets = hrm_human_resource_filters(resource_type = resource_type,
                                                            module = module)

            # List fields
            if self.list_fields is not None:
                list_fields = self.list_fields
            else:
                list_fields = ["id",
                               "person_id",
                               "organisation_id",
                               ]
                if len(types) == 2:
                    list_fields.append((T("Type"), "type"))
                list_fields.append("job_title_id")
                if settings.get_hrm_use_certificates():
                    list_fields.append((T("Certificates"), "person_id$certification.certificate_id"))
                if settings.get_hrm_use_skills():
                    list_fields.append((T("Skills"), "person_id$competency.skill_id"))
                if settings.get_hrm_use_trainings():
                    list_fields.append((T("Trainings"), "person_id$training.course_id"))

            # Data table
            resource = s3db.resource("hrm_human_resource",
                                     alias = r.component.alias if r.component else None,
                                     vars = get_vars)
            totalrows = resource.count()
            if "pageLength" in get_vars:
                display_length = get_vars["pageLength"]
                if display_length == "None":
                    display_length = None
                else:
                    display_length = int(display_length)
            else:
                display_length = 25
            if display_length:
                limit = 4 * display_length
            else:
                limit = None
            filter_, orderby, left = resource.datatable_filter(list_fields,
                                                               get_vars)
            resource.add_filter(filter_)

            # Hide people already in the link table
            query = (table[fkey] == record_id) & \
                    (table.deleted != True)
            rows = db(query).select(table.human_resource_id)
            already = [row.human_resource_id for row in rows]
            filter_ = (~db.hrm_human_resource.id.belongs(already))
            resource.add_filter(filter_)

            ajax_vars = dict(get_vars)
            if settings.get_hrm_unavailability():
                apply_availability_filter = False
                if get_vars.get("available__ge") or \
                   get_vars.get("available__le"):
                    apply_availability_filter = True
                elif representation != "aadata":
                    available_defaults = response.s3.filter_defaults["hrm_human_resource"]["available"]
                    if available_defaults:
                        apply_availability_filter = True
                        ge = available_defaults.get("ge")
                        if ge is not None:
                            ajax_vars["available__ge"] = s3_format_datetime(ge) # Used by dt_ajax_url
                            get_vars["available__ge"] = s3_format_datetime(ge)  # Popped in pr_availability_filter
                        le = available_defaults.get("le")
                        if le is not None:
                            ajax_vars["available__le"] = s3_format_datetime(le) # Used by dt_ajax_url
                            get_vars["available__le"] = s3_format_datetime(le)  # Popped in pr_availability_filter

                if apply_availability_filter:
                    # Apply availability filter
                    request = Storage(get_vars = get_vars,
                                      resource = resource,
                                      tablename = "hrm_human_resource",
                                      )
                    s3db.pr_availability_filter(request)

            dt_id = "datatable"

            # Bulk actions
            dt_bulk_actions = [(T("Assign"), "assign")]

            if representation in ("html", "popup"):
                # Page load
                resource.configure(deletable = False)

                profile_url = URL(c = controller,
                                  f = "human_resource",
                                  args = ["[id]", "profile"])
                S3CRUD.action_buttons(r,
                                      deletable = False,
                                      read_url = profile_url,
                                      update_url = profile_url)

                response.s3.no_formats = True

                # Filter form
                if filter_widgets:

                    # Where to retrieve filtered data from:
                    submit_url_vars = resource.crud._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars = submit_url_vars)

                    # Default Filters (before selecting data!)
                    resource.configure(filter_widgets = filter_widgets)
                    S3FilterForm.apply_filter_defaults(r, resource)

                    # Where to retrieve updated filter options from:
                    filter_ajax_url = URL(f = "human_resource",
                                          args = ["filter.options"],
                                          vars = {})

                    get_config = resource.get_config
                    filter_clear = get_config("filter_clear", True)
                    filter_formstyle = get_config("filter_formstyle", None)
                    filter_submit = get_config("filter_submit", True)
                    filter_form = S3FilterForm(filter_widgets,
                                               clear = filter_clear,
                                               formstyle = filter_formstyle,
                                               submit = filter_submit,
                                               ajax = True,
                                               url = filter_submit_url,
                                               ajaxurl = filter_ajax_url,
                                               _class = "filter-form",
                                               _id = "datatable-filter-form",
                                               )
                    fresource = current.s3db.resource(resource.tablename)
                    alias = r.component.alias if r.component else None
                    ff = filter_form.html(fresource,
                                          r.get_vars,
                                          target = "datatable",
                                          alias = alias)
                else:
                    ff = ""

                # Data table (items)
                data = resource.select(list_fields,
                                       start = 0,
                                       limit = limit,
                                       orderby = orderby,
                                       left = left,
                                       count = True,
                                       represent = True)
                filteredrows = data["numrows"]
                dt = S3DataTable(data["rfields"], data["rows"])
                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_ajax_url = r.url(representation = "aadata",
                                                    vars = ajax_vars),
                                dt_bulk_actions = dt_bulk_actions,
                                dt_bulk_single = not component.multiple,
                                dt_pageLength = display_length,
                                dt_pagination = "true",
                                dt_searching = "false",
                                )

                STAFF = settings.get_hrm_staff_label()

                response.view = "list_filter.html"

                rheader = self.rheader
                if callable(rheader):
                    rheader = rheader(r)

                output = {"items": items,
                          "title": T("Assign %(staff)s") % {"staff": STAFF},
                          "list_filter_form": ff,
                          "rheader": rheader,
                          }

            elif representation == "aadata":
                # Ajax refresh
                if "draw" in get_vars:
                    echo = int(get_vars.draw)
                else:
                    echo = None

                data = resource.select(list_fields,
                                       start = 0,
                                       limit = limit,
                                       orderby = orderby,
                                       left = left,
                                       count = True,
                                       represent = True)
                filteredrows = data["numrows"]
                dt = S3DataTable(data["rfields"], data["rows"])
                items = dt.json(totalrows,
                                filteredrows,
                                dt_id,
                                echo,
                                dt_bulk_actions = dt_bulk_actions)

                response.headers["Content-Type"] = "application/json"
                output = items

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

# =============================================================================
class hrm_HumanResourceRepresent(S3Represent):
    """ Representation of human resource IDs """

    def __init__(self, show_link=False):
        """
            Constructor

            @param show_link: whether to add a URL to representations
        """

        super(hrm_HumanResourceRepresent, self).__init__(
                                        lookup = "hrm_human_resource",
                                        show_link = show_link)

        self.job_title_represent = S3Represent(lookup = "hrm_job_title")
        self.types = {}

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link

            @param k: the key (hrm_human_resource.id)
            @param v: the representation of the key
            @param row: the row with this key (unused here)
        """

        # Link to specific controller for type
        types = self.types
        if types.get(k) == 1:
            url = URL(c="hrm", f="staff", args=[k])
        else:
            url = URL(c="vol", f="volunteer", args=[k])
        return A(v, _href = url)

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        s3db = current.s3db

        htable = s3db.hrm_human_resource
        ptable = s3db.pr_person

        left = ptable.on(ptable.id == htable.person_id)
        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(htable.id,
                                        htable.job_title_id,
                                        htable.organisation_id,
                                        htable.type,
                                        ptable.first_name,
                                        ptable.middle_name,
                                        ptable.last_name,
                                        limitby = (0, count),
                                        left = left)
        self.queries += 1

        # Remember HR types
        types = self.types
        for row in rows:
            types[row["hrm_human_resource.id"]] = row["hrm_human_resource.type"]

        # Bulk-represent job_title_ids
        job_title_id = str(htable.job_title_id)
        job_title_ids = [row[job_title_id] for row in rows]
        if job_title_ids:
            self.job_title_represent.bulk(job_title_ids)

        # Bulk-represent organisation_ids
        if current.deployment_settings.get_hrm_show_organisation():
            organisation_id = str(htable.organisation_id)
            organisation_ids = [row[organisation_id] for row in rows]
            if organisation_ids:
                htable.organisation_id.represent.bulk(organisation_ids)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        # Start with the person name
        representation = [s3_str(s3_fullname(row.pr_person))]
        append = representation.append

        hr = row.hrm_human_resource

        # Append the job title if present
        if hr.job_title_id:
            append(self.job_title_represent(hr.job_title_id, show_link=False))

        # Append the organisation if present (and configured)
        if hr.organisation_id and \
           current.deployment_settings.get_hrm_show_organisation():
            htable = current.s3db.hrm_human_resource
            append(htable.organisation_id.represent(hr.organisation_id,
                                                    show_link=False))

        return ", ".join(representation)

# =============================================================================
class hrm_TrainingRepresent(S3Represent):
    """
        Represent a Training by its Course
           - used from within hrm_programme_hours
    """

    def __init__(self):
        """
            Constructor
        """

        super(hrm_TrainingRepresent, self).__init__(lookup = "hrm_training")

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        ttable = self.table
        ctable = current.s3db.hrm_course

        left = [ctable.on(ctable.id == ttable.course_id)]
        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        rows = current.db(query).select(ttable.id,
                                        ctable.name,
                                        left = left,
                                        )
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):

        name = row["hrm_course.name"]
        if not name:
            name = current.messages.UNKNOWN_OPT
        return name

# =============================================================================
class hrm_TrainingEventRepresent(S3Represent):
    """ Representation of training_event_id """

    def __init__(self):
        """
            Constructor
        """

        super(hrm_TrainingEventRepresent, self).__init__(
                                                lookup = "hrm_training_event")

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None, pe_id=False):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
            @param pe_id: whether to include pe_id in the output rows
                          (True when called from pr_PersonEntityRepresent)
        """

        s3db = current.s3db

        etable = self.table
        ctable = s3db.hrm_course
        stable = s3db.org_site

        left = [ctable.on(ctable.id == etable.course_id),
                stable.on(stable.site_id == etable.site_id),
                ]
        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        fields = [etable.id,
                  etable.name,
                  etable.start_date,
                  etable.instructor,
                  etable.person_id,
                  ctable.name,
                  ctable.code,
                  stable.name,
                  ]
        if pe_id:
            fields.insert(0, etable.pe_id)

        rows = current.db(query).select(*fields,
                                        left = left)

        instructors = current.deployment_settings.get_hrm_training_instructors()
        if instructors in ("internal", "both"):
            # Bulk-represent internal instructors to suppress
            # per-row DB lookups in represent_row:
            key = str(etable.person_id)
            etable.person_id.represent.bulk([row[key] for row in rows])

        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            NB This needs to be machine-parseable by training.xsl

            @param row: the Row
        """

        # Do we have a Name?
        name = row.get("hrm_training_event.name")
        if name:
            return name

        # Course Details
        course = row.get("hrm_course")
        if not course:
            return current.messages.UNKNOWN_OPT
        name = course.get("name")
        if not name:
            name = current.messages.UNKNOWN_OPT
        representation = ["%s --" % name]
        append = representation.append
        code = course.get("code")
        if code:
            append("(%s)" % code)

        # Venue and instructor
        event = row.hrm_training_event
        try:
            site = row.org_site.name
        except AttributeError:
            site = None

        instructors = current.deployment_settings.get_hrm_training_instructors()

        instructor = None
        if instructors in ("internal", "both"):
            person_id = event.get("person_id")
            if person_id:
                instructor = self.table.person_id.represent(person_id)
        if instructor is None and instructors in ("external", "both"):
            instructor = event.get("instructor")

        if instructor and site:
            append("%s - {%s}" % (instructor, site))
        elif instructor:
            append("%s" % instructor)
        elif site:
            append("{%s}" % site)

        # Start date
        start_date = event.start_date
        if start_date:
            # Easier for users & machines
            start_date = S3DateTime.date_represent(start_date, format="%Y-%m-%d")
            append("[%s]" % start_date)

        return " ".join(representation)

# =============================================================================
#def hrm_position_represent(id, row=None):
#    """
#    """
#    if row:
#        id = row.id
#    elif not id:
#        return current.messages["NONE"]
#    db = current.db
#    s3db = current.s3db
#    table = s3db.hrm_position
#    jtable = s3db.hrm_job_title
#    otable = s3db.org_organisation
#    query = (table.id == id) & \
#            (table.job_title_id == jtable.id)
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
#        return current.messages["NONE"]
#    return represent
#
# =============================================================================
def hrm_human_resource_onaccept(form):
    """ On-accept for HR records """

    if "vars" in form:
        # e.g. coming from staff/create
        form_vars = form.vars
    elif "id" in form:
        # e.g. coming from user/create or from hrm_site_onaccept or req_onaccept
        form_vars = form
    elif hasattr(form, "vars"):
        # SQLFORM e.g. ?
        form_vars = form.vars
    else:
        # e.g. Coming from s3_register callback
        form_vars = form

    record_id = form_vars.get("id")
    if not record_id:
        return

    db = current.db
    s3db = current.s3db
    auth = current.auth
    request = current.request
    settings = current.deployment_settings

    # Get the 'full' record
    htable = db.hrm_human_resource
    record = db(htable.id == record_id).select(htable.id, # needed for update_record
                                               htable.type,
                                               htable.person_id,
                                               htable.organisation_id,
                                               htable.location_id,
                                               htable.job_title_id,
                                               htable.site_id,
                                               htable.site_contact,
                                               htable.status,
                                               htable.deleted,
                                               htable.deleted_fk,
                                               limitby=(0, 1),
                                               ).first()

    job_title_id = record.job_title_id
    if job_title_id and settings.get_hrm_multiple_job_titles():
        # Update the link table
        ltable = db.hrm_job_title_human_resource
        query = (ltable.human_resource_id == record_id) & \
                (ltable.job_title_id == job_title_id)
        exists = db(query).select(ltable.id, # needed for update_record
                                  ltable.main,
                                  limitby=(0, 1)).first()
        if exists:
            if not exists.main:
                exists.update_record(main=True)
        else:
            # Insert record
            ltable.insert(human_resource_id = record_id,
                          job_title_id = job_title_id,
                          main = True,
                          start_date = request.utcnow,
                          )

    data = Storage()

    site_id = record.site_id
    organisation_id = record.organisation_id

    # Affiliation, record ownership and component ownership
    s3db.pr_update_affiliations(htable, record)

    # Realm_entity for the pr_person record
    ptable = s3db.pr_person
    person_id = record.person_id
    person = Storage(id = person_id)
    if settings.get_auth_person_realm_human_resource_site_then_org():
        # Set pr_person.realm_entity to the human_resource's site pe_id or organisation_pe_id
        entity = s3db.pr_get_pe_id("org_site", site_id) or \
                 s3db.pr_get_pe_id("org_organisation", organisation_id)

        if entity:
            auth.set_realm_entity(ptable, person,
                                  entity = entity,
                                  force_update = True)

    tracker = S3Tracker()
    if person_id:
        # Set person record to follow HR record
        # (Person base location remains untouched)
        pr_tracker = tracker(ptable, person_id)
        pr_tracker.check_in(htable, record_id, timestmp = request.utcnow)

    if record.type == 1:
        # Staff
        vol = False
        location_lookup = settings.get_hrm_location_staff()
    elif record.type == 2:
        # Volunteer
        vol = True
        location_lookup = settings.get_hrm_location_vol()

    # Add deploy_application when creating inside deploy module
    if request.controller == "deploy":
        user_organisation_id = auth.user.organisation_id
        ltable = s3db.deploy_application
        if user_organisation_id:
            query = (ltable.human_resource_id == record_id) & \
                    ((ltable.organisation_id == None) |
                     (ltable.organisation_id == user_organisation_id))
        else:
            query = (ltable.human_resource_id == record_id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)).first()
        if not exists:
            # Is there a Deployable Team for this user_org?
            dotable = s3db.deploy_organisation
            exists = db(dotable.organisation_id == user_organisation_id)
            if exists:
                # Insert record in this Deployable Team
                ltable.insert(human_resource_id = record_id,
                              organisation_id = user_organisation_id,
                              )
            else:
                # Insert record in the global Deployable Team
                ltable.insert(human_resource_id = record_id,
                              )

    # Determine how the HR is positioned
    address = None
    update_location_from_site = False

    site_contact = record.site_contact

    hstable = s3db.hrm_human_resource_site
    query = (hstable.human_resource_id == record_id)
    if site_id:
        # Add/update the record in the link table
        this = db(query).select(hstable.id,
                                limitby = (0, 1),
                                ).first()
        if this:
            db(query).update(site_id = site_id,
                             human_resource_id = record_id,
                             site_contact = site_contact,
                             )
        else:
            hstable.insert(site_id = site_id,
                           human_resource_id = record_id,
                           site_contact = site_contact,
                           )

        if location_lookup == "site_id" or location_lookup[0] == "site_id":
            # Use site location as HR base location
            update_location_from_site = True

        elif location_lookup[0] == "person_id":
            # Only use site location as HR base location if the Person
            # has no Home Address
            atable = s3db.pr_address
            query = (atable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (atable.type == 1) & \
                    (atable.deleted == False)
            address = db(query).select(atable.id,
                                       atable.location_id,
                                       limitby=(0, 1),
                                       ).first()
            if not address:
                update_location_from_site = True
        else:
            # location_lookup == "person_id"
            # Use home address to determine HR base location
            # Current Address preferred, otherwise Permanent if present
            atable = s3db.pr_address
            query = (atable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (atable.type.belongs(1, 2)) & \
                    (atable.deleted == False)
            address = db(query).select(atable.id,
                                       atable.location_id,
                                       limitby = (0, 1),
                                       orderby = atable.type,
                                       ).first()
    else:
        # Delete any links in the link table
        db(query).delete()

        if "person_id" in location_lookup:
            # Use home address to determine HR base location
            # Current Address preferred, otherwise Permanent if present
            atable = s3db.pr_address
            query = (atable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (atable.type.belongs(1, 2)) & \
                    (atable.deleted == False)
            address = db(query).select(atable.id,
                                       atable.location_id,
                                       limitby = (0, 1),
                                       orderby = atable.type,
                                       ).first()

    if update_location_from_site:

        # Use the site location as base location of the HR
        stable = db.org_site
        site = db(stable.site_id == site_id).select(stable.location_id,
                                                    limitby = (0, 1),
                                                    ).first()
        try:
            data.location_id = location_id = site.location_id
        except AttributeError:
            current.log.error("Can't find site with site_id ", site_id)
            data.location_id = location_id = None

    elif address:

        # Use the address as base location of the HR
        data.location_id = location_id = address.location_id

    elif vol:

        # No known address and not updating location from site
        # => fall back to the HR's location_id if known
        if record.location_id:

            # Add a new Address for the person from the HR location
            location_id = record.location_id
            pe = db(ptable.id == person_id).select(ptable.pe_id,
                                                   limitby = (0, 1),
                                                   ).first()
            try:
                pe_id = pe.pe_id
            except AttributeError:
                current.log.error("Can't find person with id ", person_id)
            else:
                atable.insert(type = 1,
                              pe_id = pe_id,
                              location_id = location_id,
                              )
        else:
            data.location_id = location_id = None
    else:
        data.location_id = location_id = None

    # Update HR base location
    hrm_tracker = tracker(htable, record_id)
    if location_id:
        # Set Base Location
        hrm_tracker.set_base_location(location_id)
    else:
        # Unset Base Location
        hrm_tracker.set_base_location(None)

    if settings.get_hrm_site_contact_unique():
        # Ensure only one Site Contact per Site
        if site_contact and site_id:
            # Set all others in this Facility to not be the Site Contact
            # @ToDo: deployment_setting to allow multiple site contacts
            query  = (htable.site_id == site_id) & \
                     (htable.site_contact == True) & \
                     (htable.id != record_id)
            # Prevent overwriting the person_id field!
            htable.person_id.update = None
            db(query).update(site_contact = False)

    if vol:
        request_vars = request.vars
        programme_id = request_vars.get("programme_id", None)
        if programme_id:
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
                             date = request.utcnow,
                             programme_id = programme_id)

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

    if user and organisation_id:
        profile = {}
        if not user.organisation_id:
            # Set the Organisation in the Profile, if not already set
            profile["organisation_id"] = organisation_id
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
                profile["organisation_id"] = organisation_id
                profile["site_id"] = site_id
        if profile:
            db(utable.id == user_id).update(**profile)

# =============================================================================
def hrm_compose():
    """
        Send message to people/teams/participants

        @ToDo: Better rewritten as an S3Method
    """

    s3db = current.s3db
    get_vars = current.request.get_vars
    pe_id = None

    if "human_resource.id" in get_vars:
        fieldname = "human_resource.id"
        record_id = get_vars.get(fieldname)
        table = s3db.pr_person
        htable = s3db.hrm_human_resource
        query = (htable.id == record_id) & \
                (htable.person_id == table.id)
        title = current.T("Send a message to this person")
        # URL to redirect to after message sent
        url = URL(f="compose",
                  vars={fieldname: record_id})
    elif "group_id" in get_vars:
        fieldname = "group_id"
        record_id = get_vars.group_id
        table = s3db.pr_group
        query = (table.id == record_id)
        title = current.T("Send a message to this team")
        # URL to redirect to after message sent
        url = URL(f="compose",
                  vars={fieldname: record_id})
    elif "training_event.id" in get_vars:
        fieldname = "training_event.id"
        record_id = get_vars.get(fieldname)
        pe_id = get_vars.pe_id
        title = current.T("Message Participants")
        # URL to redirect to after message sent
        url = URL(f="training_event", args=record_id)

    else:
        current.session.error = current.T("Record not found")
        redirect(URL(f="index"))

    if not pe_id:
        db = current.db
        pe = db(query).select(table.pe_id,
                              limitby=(0, 1)).first()
        if not pe:
            current.session.error = current.T("Record not found")
            redirect(URL(f="index"))

        pe_id = pe.pe_id

    if "hrm_id" in get_vars:
        # Get the individual's communications options & preference
        ctable = s3db.pr_contact
        contact = db(ctable.pe_id == pe_id).select(ctable.contact_method,
                                                   orderby="priority",
                                                   limitby=(0, 1)).first()
        if contact:
            s3db.msg_outbox.contact_method.default = contact.contact_method
        else:
            current.session.error = current.T("No contact method found")
            redirect(URL(f="index"))

    # Create the form
    output = current.msg.compose(recipient = pe_id,
                                 url = url)

    output["title"] = title

    response = current.response
    representation = s3_get_extension()
    response.headers["Content-Type"] = \
        response.s3.content_type.get(representation, "text/html")
    response.view = "msg/compose.html"

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

    record = r.record
    if not record:
        return ""
    person_id = record.person_id

    output = TABLE()
    append = output.append
    # Edit button
    append(TR(TD(A(T("Edit"),
                   _target="_blank",
                   _id="edit-btn",
                   _href=URL(args=[r.id, "update"])))))

    # First name, last name
    append(TR(TD(B("%s:" % T("Name"))),
              TD(s3_fullname(person_id))))

    # Job Title
    if record.job_title_id:
        field = r.table.job_title_id
        append(TR(TD(B("%s:" % field.label)),
                  TD(field.represent(record.job_title_id))))

    # Organization (better with just name rather than Represent)
    # @ToDo: Make this configurable - some deployments will only see
    #        their staff so this is a meaningless field
    #table = s3db.org_organisation
    #query = (table.id == record.organisation_id)
    #name = db(query).select(table.name,
    #                        limitby=(0, 1)).first().name
    #append(TR(TD(B("%s:" % r.table.organisation_id.label)),
    #          TD(name)))

    # Components link to the Person record
    # Skills
    table = s3db.hrm_competency
    stable = s3db.hrm_skill
    query = (table.person_id == person_id) & \
            (table.deleted == False) & \
            (table.skill_id == stable.id)
    skills = db(query).select(stable.name)
    if skills:
        vals = [skill.name for skill in skills]
        if len(skills) > 1:
            represent = ", ".join(vals)
        else:
            represent = vals[0] if vals else ""
        append(TR(TD(B("%s:" % T("Skills"))),
                  TD(represent)))

    # Certificates
    table = s3db.hrm_certification
    ctable = s3db.hrm_certificate
    query = (table.person_id == person_id) & \
            (table.deleted == False) & \
            (table.certificate_id == ctable.id)
    certificates = db(query).select(ctable.name)
    if certificates:
        vals = [cert.name for cert in certificates]
        if len(certificates) > 1:
            represent = ", ".join(vals)
        else:
            represent = vals[0] if vals else ""
        append(TR(TD(B("%s:" % T("Certificates"))),
                  TD(represent)))

    # Trainings
    table = s3db.hrm_training
    etable = s3db.hrm_training_event
    ctable = s3db.hrm_course
    query = (table.person_id == person_id) & \
            (table.deleted == False) & \
            (table.training_event_id == etable.id) & \
            (etable.course_id == ctable.id)
    trainings = db(query).select(ctable.name)
    if trainings:
        vals = [train.name for train in trainings]
        if len(trainings) > 1:
            represent = ", ".join(vals)
        else:
            represent = vals[0] if vals else ""
        append(TR(TD(B("%s:" % T("Trainings"))),
                  TD(represent)))

    if record.location_id:
        table = s3db.gis_location
        query = (table.id == record.location_id)
        location = db(query).select(table.path,
                                    table.addr_street,
                                    limitby=(0, 1)).first()
        # City
        # Street address
        if location.addr_street:
            append(TR(TD(B("%s:" % table.addr_street.label)),
                      TD(location.addr_street)))
    # Mobile phone number & Email address
    ptable = s3db.pr_person
    ctable = s3db.pr_contact
    query = (ptable.id == person_id) & \
            (ctable.pe_id == ptable.pe_id) & \
            (ctable.deleted == False)
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
    if record.site_id:
        table = s3db.org_office
        query = (table.site_id == record.site_id)
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
def hrm_training_month(row):
    """ Year/Month of the start date of the training event """
    if hasattr(row, "hrm_training"):
        row = row.hrm_training
    try:
        date = row.date
    except AttributeError:
        # not available
        date = None
    if date:
        return "%s/%02d" % (date.year, date.month)
    else:
        return current.messages["NONE"]

# -------------------------------------------------------------------------
def hrm_training_year(row):
    """ The Year of the training event """
    if hasattr(row, "hrm_training"):
        row = row.hrm_training
    try:
        date = row.date
    except AttributeError:
        # not available
        date = None
    if date:
        return date.year
    else:
        return current.messages["NONE"]

# =============================================================================
def hrm_training_job_title(row):
    """
        Which Job Titles(s) the person is active with
    """

    try:
        person_id = row.hrm_training.person_id
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
                jobtitle = job.name
                if output:
                    output = "%s, %s" % (output, jobtitle)
                else:
                    output = jobtitle
            return output

    return current.messages["NONE"]

# =============================================================================
def hrm_training_organisation(row):
    """
        Which Organisation(s)/Branch(es) the person is actively affiliated with
    """

    try:
        person_id = row.hrm_training.person_id
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
            represent = s3db.org_OrganisationRepresent()
            for org in orgs:
                org_repr = represent(org.organisation_id)
                if output:
                    output = "%s, %s" % (output, org_repr)
                else:
                    output = org_repr
            return output

    return current.messages["NONE"]

# =============================================================================
def hrm_rheader(r, tabs=None, profile=False):
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
        record_id = r.id
        db = current.db
        s3db = current.s3db
        htable = s3db.hrm_human_resource
        settings = current.deployment_settings
        get_vars = r.get_vars

        hr = get_vars.get("human_resource.id", None)
        if hr:
            name = s3db.hrm_human_resource_represent(int(hr))
        else:
            # Look up HR record ID (required for link URL construction)
            # @ToDo handle multiple HR records (which one are we looking at?)
            query = (htable.person_id == record_id) & \
                    (htable.deleted == False)
            hr = db(query).select(htable.id, limitby=(0, 1)).first()
            if hr:
                hr = hr.id
            name = s3_fullname(record)

        group = get_vars.get("group", None)
        if group is None:
            controller = r.controller
            if controller == "vol":
                group = "volunteer"
            else:
                group = "staff"
        use_cv = settings.get_hrm_cv_tab()
        record_tab = settings.get_hrm_record_tab()
        experience_tab = None
        service_record = ""
        tbl = TABLE(TR(TH(name,
                          # @ToDo: Move to CSS
                          _style="padding-top:15px")
                       ))
        experience_tab2 = None
        if group == "volunteer":
            vol_experience = settings.get_hrm_vol_experience()
            if vol_experience in ("programme", "both", "activity"):
                # Integrated into Record tab
                #experience_tab = (T("Hours"), "hours")
                # Show all Hours spent on both Programmes/Activities & Trainings
                # - last month & last year
                now = r.utcnow
                last_year = now - datetime.timedelta(days=365)
                if vol_experience == "activity":
                    ahtable = db.vol_activity_hours
                    attable = db.vol_activity_hours_activity_type
                    bquery = (ahtable.deleted == False) & \
                             (ahtable.person_id == record_id)
                    bleft = [attable.on(ahtable.id == attable.activity_hours_id),
                             ]
                    dfield = ahtable.date
                    fields = [dfield,
                              ahtable.hours,
                              ahtable.id,
                              #ahtable.training,
                              attable.activity_type_id,
                              ]
                else:
                    ptable = s3db.hrm_programme
                    phtable = db.hrm_programme_hours
                    bquery = (phtable.deleted == False) & \
                             (phtable.person_id == record_id)
                    bleft = None
                    query = (phtable.programme_id == ptable.id)
                    query &= bquery
                    row = db(query).select(ptable.name,
                                           phtable.date,
                                           orderby=phtable.date).last()
                    if row:
                        programme = row.hrm_programme.name
                    else:
                        programme = ""
                    dfield = phtable.date
                    fields = [dfield,
                              phtable.hours,
                              phtable.training,
                              ]
                    training_hours_year = 0
                    training_hours_month = 0

                query = bquery & \
                        (dfield > last_year.date())
                rows = db(query).select(*fields,
                                        left = bleft)
                programme_hours_year = 0
                programme_hours_month = 0
                last_month = now - datetime.timedelta(days=30)
                last_month = last_month.date()
                if vol_experience == "activity":
                    activity_hour_ids = []
                    ahappend = activity_hour_ids.append
                    activity_type_ids = []
                    atappend = activity_type_ids.append
                    for row in rows:
                        atappend(row["vol_activity_hours_activity_type.activity_type_id"])
                        ah_id = row["vol_activity_hours.id"]
                        if ah_id in activity_hour_ids:
                            # Don't double-count when more than 1 Activity Type
                            continue
                        ahappend(ah_id)
                        hours = row["vol_activity_hours.hours"]
                        if hours:
                            programme_hours_year += hours
                            if row["vol_activity_hours.date"] > last_month:
                                programme_hours_month += hours
                    # Uniquify
                    activity_type_ids = list(set(activity_type_ids))
                    # Represent
                    activity_types = s3db.vol_activity_activity_type.activity_type_id.represent.bulk(activity_type_ids)
                    NONE = current.messages["NONE"]
                    if activity_types == [NONE]:
                        activity_types = NONE
                    else:
                        activity_types = list(activity_types.values())
                        activity_types.remove(NONE)
                        activity_types = ", ".join([s3_str(v) for v in activity_types])
                else:
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

                vol_active = settings.get_hrm_vol_active()
                if vol_active:
                    if hr:
                        dtable = s3db.vol_details
                        row = db(dtable.human_resource_id == hr).select(dtable.active,
                                                                        limitby=(0, 1)
                                                                        ).first()
                        if row and row.active:
                            active = TD(DIV(T("Yes"),
                                            # @ToDo: Move to CSS
                                            _style="color:green"))
                        else:
                            active = TD(DIV(T("No"),
                                            # @ToDo: Move to CSS
                                            _style="color:red"))
                    else:
                        active = TD(DIV(T("No"),
                                        # @ToDo: Move to CSS
                                        _style="color:red"))
                    vol_active_tooltip = settings.get_hrm_vol_active_tooltip()
                    if vol_active_tooltip:
                        tooltip = SPAN(_class="tooltip",
                                       _title="%s|%s" % (T("Active"),
                                                         T(vol_active_tooltip)),
                                       _style="display:inline-block"
                                       )
                    else:
                        tooltip = ""
                    active_cells = [TH("%s:" % T("Active?"), tooltip),
                                    active]
                else:
                    active_cells = []
                if vol_experience == "activity":
                    row1 = TR(*active_cells
                              )
                    row2 = TR(TH("%s:" % T("Activity Types")),
                              str(activity_types),
                              )
                    row3 = TR(TH("%s:" % T("Activity Hours (Month)")),
                              str(programme_hours_month),
                              )
                    row4 = TR(TH("%s:" % T("Activity Hours (Year)")),
                              str(programme_hours_year),
                              )
                else:
                    if programme:
                        row1 = TR(TH("%s:" % T("Program")),
                                  programme,
                                  *active_cells
                                  )
                    else:
                        row1 = TR(*active_cells
                                  )
                    row2 = TR(TH("%s:" % T("Program Hours (Month)")),
                              str(programme_hours_month),
                              TH("%s:" % T("Training Hours (Month)")),
                              str(training_hours_month)
                              )
                    row3 = TR(TH("%s:" % T("Program Hours (Year)")),
                              str(programme_hours_year),
                              TH("%s:" % T("Training Hours (Year)")),
                              str(training_hours_year)
                              )
                    row4 = ""

                tbl = TABLE(TR(TH(name,
                                  _colspan=4)
                               ),
                            row1,
                            row2,
                            row3,
                            row4,
                            )
                service_record = A(T("Service Record"),
                                   _href = URL(c = "vol",
                                               f = "human_resource",
                                               args = [hr, "form"]
                                               ),
                                   _id = "service_record",
                                   _class = "action-btn"
                                   )
                if vol_experience == "both" and not use_cv:
                    experience_tab2 = (T("Experience"), "experience")
            elif vol_experience == "experience" and not use_cv:
                experience_tab = (T("Experience"), "experience")
        elif settings.get_hrm_staff_experience() == "experience" and not use_cv:
            experience_tab = (T("Experience"), "experience")

        if settings.get_hrm_id_cards():
            card_button = A(T("ID Card"),
                            data = {"url": URL(f = "human_resource",
                                               args = ["%s.card" % hr]
                                               ),
                                    },
                            _class = "action-btn s3-download-button",
                            _script = "alert('here')",
                            )
        else:
            card_button = ""

        if settings.get_hrm_use_certificates() and not use_cv:
            certificates_tab = (T("Certificates"), "certification")
        else:
            certificates_tab = None

        if settings.get_hrm_use_credentials():
            credentials_tab = (T("Credentials"), "credential")
        else:
            credentials_tab = None

        if settings.get_hrm_vol_availability_tab():
            availability_tab = (T("Availability"), "availability")
        else:
            availability_tab = None

        if settings.get_hrm_unavailability():
            unavailability_tab = (T("Availability"), "unavailability", {}, "organize")
        else:
            unavailability_tab = None

        description_tab = settings.get_hrm_use_description() or None
        if description_tab:
            description_tab = (T(description_tab), "physical_description")

        if settings.get_hrm_use_education() and not use_cv:
            education_tab = (T("Education"), "education")
        else:
            education_tab = None

        if settings.get_hrm_use_id():
            id_tab = (T("ID"), "identity")
        else:
            id_tab = None

        if settings.get_hrm_use_address():
            address_tab = (T("Address"), "address")
        else:
            address_tab = None

        if settings.get_hrm_salary():
            salary_tab = (T("Salary"), "salary")
        else:
            salary_tab = None

        if settings.get_hrm_use_skills() and not use_cv:
            skills_tab = (T("Skills"), "competency")
        else:
            skills_tab = None

        if record_tab != "record":
            teams = settings.get_hrm_teams()
            if teams:
                teams_tab = (T(teams), "group_membership")
            else:
                teams_tab = None
        else:
            teams_tab = None

        trainings_tab = instructor_tab = None
        if settings.get_hrm_use_trainings():
            if not use_cv:
                trainings_tab = (T("Trainings"), "training")
            if settings.get_hrm_training_instructors() in ("internal", "both"):
                instructor_tab = (T("Instructor"), "training_event")

        if use_cv:
            trainings_tab = (T("CV"), "cv")

        hr_tab = None
        duplicates_tab = None
        if not record_tab:
            record_method = None
        elif record_tab == "record":
            record_method = "record"
            if not profile and current.auth.s3_has_role("ADMIN"):
                query = (htable.person_id == record_id) & \
                        (htable.deleted == False)
                hr_records = db(query).count()
                if hr_records > 1:
                    duplicates_tab = (T("Duplicates"), "human_resource", {"hr":"all"}) # Ensure no &human_resource.id=XXXX
        else:
            # Default
            record_method = "human_resource"

        record_label = settings.get_hrm_record_label()

        if profile:
            # Configure for personal mode
            if record_method:
                hr_tab = (T(record_label), record_method)
            tabs = [(T("Person Details"), None),
                    (T("User Account"), "user"),
                    hr_tab,
                    id_tab,
                    description_tab,
                    address_tab,
                    ]
            contacts_tabs = settings.get_pr_contacts_tabs()
            if "all" in contacts_tabs:
                tabs.append((settings.get_pr_contacts_tab_label("all"),
                             "contacts",
                             ))
            if "public" in contacts_tabs:
                tabs.append((settings.get_pr_contacts_tab_label("public_contacts"),
                             "public_contacts",
                             ))
            if "private" in contacts_tabs:
                tabs.append((settings.get_pr_contacts_tab_label("private_contacts"),
                             "private_contacts",
                             ))
            tabs += [availability_tab,
                     education_tab,
                     trainings_tab,
                     certificates_tab,
                     skills_tab,
                     credentials_tab,
                     experience_tab,
                     experience_tab2,
                     instructor_tab,
                     teams_tab,
                     unavailability_tab,
                     #(T("Assets"), "asset"),
                     ]
        #elif current.session.s3.hrm.mode is not None:
        #    # Configure for personal mode
        #    tabs = [(T("Person Details"), None),
        #            id_tab,
        #            description_tab,
        #            address_tab,
        #            ]
        #    contacts_tabs = settings.get_pr_contacts_tabs()
        #    if "all" in contacts_tabs:
        #        tabs.append((settings.get_pr_contacts_tab_label("all"),
        #                     "contacts",
        #                     ))
        #    if "public" in contacts_tabs:
        #        tabs.append((settings.get_pr_contacts_tab_label("public_contacts"),
        #                     "public_contacts",
        #                     ))
        #    if "private" in contacts_tabs:
        #        tabs.append((settings.get_pr_contacts_tab_label("private_contacts"),
        #                     "private_contacts",
        #                     ))
        #    if record_method is not None:
        #        hr_tab = (T("Positions"), "human_resource")
        #    tabs += [availability_tab,
        #             trainings_tab,
        #             certificates_tab,
        #             skills_tab,
        #             credentials_tab,
        #             experience_tab,
        #             experience_tab2,
        #             hr_tab,
        #             teams_tab,
        #             (T("Assets"), "asset"),
        #             ]
        else:
            # Configure for HR manager mode
            hr_record = record_label
            if group == "staff":
                awards_tab = None
            elif group == "volunteer":
                if settings.get_hrm_use_awards() and not use_cv:
                    awards_tab = (T("Awards"), "award")
                else:
                    awards_tab = None
            if record_method:
                hr_tab = (T(hr_record), record_method)

            tabs = [(T("Person Details"), None, {"native": True}),
                    hr_tab,
                    duplicates_tab,
                    id_tab,
                    description_tab,
                    address_tab,
                    ]
            contacts_tabs = settings.get_pr_contacts_tabs()
            if "all" in contacts_tabs:
                tabs.append((settings.get_pr_contacts_tab_label("all"),
                             "contacts",
                             ))
            if "public" in contacts_tabs:
                tabs.append((settings.get_pr_contacts_tab_label("public_contacts"),
                             "public_contacts",
                             ))
            if "private" in contacts_tabs:
                tabs.append((settings.get_pr_contacts_tab_label("private_contacts"),
                             "private_contacts",
                             ))
            tabs += [availability_tab,
                     salary_tab,
                     education_tab,
                     trainings_tab,
                     certificates_tab,
                     skills_tab,
                     credentials_tab,
                     experience_tab,
                     experience_tab2,
                     instructor_tab,
                     awards_tab,
                     teams_tab,
                     unavailability_tab,
                     (T("Assets"), "asset"),
                     ]
            # Add role manager tab if a user record exists
            user_id = current.auth.s3_get_user_id(record_id)
            if user_id:
                tabs.append((T("Roles"), "roles"))
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader_btns = DIV(service_record, card_button,
                           # @ToDo: Move to CSS
                           _style="margin-bottom:10px",
                           _class="rheader-btns",
                           )
        rheader = DIV(rheader_btns,
                      A(s3_avatar_represent(record_id,
                                            "pr_person",
                                            _class="rheader-avatar"),
                        _href=URL(f="person", args=[record_id, "image"],
                                  vars = get_vars),
                        ),
                      tbl,
                      rheader_tabs)

    elif resourcename == "activity":
        # Tabs
        tabs = [(T("Activity Details"), None),
                (T("Hours"), "hours"),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name),
                            TR(TH("%s: " % table.sector_id.label),
                               table.sector_id.represent(record.sector_id)),
                            # @ToDo: (ltable)
                            #TR(TH("%s: " % table.activity_type_id.label),
                            #   table.activity_type_id.represent(record.activity_type_id)),
                            TR(TH("%s: " % table.location_id.label),
                               table.location_id.represent(record.location_id)),
                            TR(TH("%s: " % table.date.label),
                               table.date.represent(record.date)),
                            ),
                      rheader_tabs)

    elif resourcename == "training_event":
        settings = current.deployment_settings
        # Tabs
        if not tabs:
            tabs = [(T("Training Event Details"), None),
                    (T("Participants"), "participant"),
                    ]
            if settings.has_module("dc"):
                label = settings.get_dc_response_label()
                if label == "Survey":
                    label = T("Surveys")
                else:
                    label = T("Assessments")
                tabs.append((label, "target"),)
        rheader_tabs = s3_rheader_tabs(r, tabs)
        action = ""
        if settings.has_module("msg"):
            permit = current.auth.permission.has_permission
            if permit("update", c="hrm", f="compose") and permit("update", c="msg"):
                # @ToDo: Be able to see who has been messaged, whether messages bounced, receive confirmation responses, etc
                action = A(T("Message Participants"),
                           _href = URL(f = "compose",
                                       vars = {"training_event.id": record.id,
                                               "pe_id": record.pe_id,
                                               },
                                       ),
                           _class = "action-btn send"
                           )

        if settings.get_hrm_event_types():
            event_type = TR(TH("%s: " % table.event_type_id.label),
                            table.event_type_id.represent(record.event_type_id))
            event_name = TR(TH("%s: " % table.name.label),
                            record.name)
        else:
            event_type = ""
            event_name = ""

        instructors = settings.get_hrm_training_instructors()
        if instructors == "internal":
            instructors = TR(TH("%s: " % table.person_id.label),
                             table.person_id.represent(record.person_id))
        elif instructors == "external":
            instructors = TR(TH("%s: " % table.instructor.label),
                             table.instructor.represent(record.instructor))
        elif instructors == "both":
            instructors = TAG[""](TR(TH("%s: " % table.person_id.label),
                                     table.person_id.represent(record.person_id)),
                                  TR(TH("%s: " % table.instructor.label),
                                     table.instructor.represent(record.instructor)))
        elif instructors == "multiple":
            itable = current.s3db.hrm_training_event_instructor
            pfield = itable.person_id
            instructors = current.db(itable.training_event_id == r.id).select(pfield)
            represent = pfield.represent
            instructors = ",".join([represent(i.person_id) for i in instructors])
            instructors = TR(TH("%s: " % T("Instructors")),
                             instructors)
        else:
            instructors = ""

        rheader = DIV(TABLE(event_type,
                            event_name,
                            TR(TH("%s: " % table.organisation_id.label),
                               table.organisation_id.represent(record.organisation_id)),
                            TR(TH("%s: " % table.course_id.label),
                               table.course_id.represent(record.course_id)),
                            TR(TH("%s: " % table.site_id.label),
                               table.site_id.represent(record.site_id)),
                            TR(TH("%s: " % table.start_date.label),
                               table.start_date.represent(record.start_date)),
                            instructors,
                            TR(TH(action, _colspan=2)),
                            ),
                      rheader_tabs)

    elif resourcename == "certificate":
        # Tabs
        tabs = [(T("Certificate Details"), None),
                ]
        settings = current.deployment_settings
        if settings.get_hrm_use_skills() and settings.get_hrm_certificate_skill():
            tabs.append((T("Skill Equivalence"), "certificate_skill"))
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name),
                            ),
                      rheader_tabs)

    elif resourcename == "certification":
        # Tabs
        tabs = [(T("Certification Details"), None),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(TH("%s: " % table.person_id.label),
                               table.person_id.represent(record.person_id)),
                            TR(TH("%s: " % table.certificate_id.label),
                               table.certificate_id.represent(record.certificate_id)),
                            ),
                      rheader_tabs)

    elif resourcename == "course":
        # Tabs
        tabs = [(T("Course Details"), None),
                (T("Course Certificates"), "course_certificate"),
                (T("Trainees"), "training"),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name),
                            ),
                      rheader_tabs)

    elif resourcename == "programme":
        # Tabs
        tabs = [(T("Program Details"), None),
                (T("Volunteer Hours"), "person"),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name),
                            ),
                      rheader_tabs)
    elif resourcename == "shift":
        db = current.db
        s3db = current.s3db
        record_id = r.id
        # Look up Site
        stable = s3db.org_site_shift
        link = db(stable.shift_id == record_id).select(stable.site_id,
                                                       limitby = (0, 1),
                                                       ).first()
        if link:
            site_id = link.site_id
        else:
            site_id = None
        # Look up Assigned
        htable = s3db.hrm_human_resource_shift
        link = db(htable.shift_id == record_id).select(htable.human_resource_id,
                                                       limitby = (0, 1),
                                                       ).first()
        if link:
            human_resource_id = link.human_resource_id
        else:
            human_resource_id = None
        rheader = DIV(TABLE(TR(TH("%s: " % stable.site_id.label),
                               stable.site_id.represent(site_id),
                               ),
                            TR(TH("%s: " % table.skill_id.label),
                               table.skill_id.represent(record.skill_id),
                               TH("%s: " % table.job_title_id.label),
                               table.job_title_id.represent(record.job_title_id),
                               ),
                            TR(TH("%s: " % table.start_date.label),
                               table.start_date.represent(record.start_date),
                               TH("%s: " % table.end_date.label),
                               table.end_date.represent(record.end_date),
                               ),
                            TR(TH("%s: " % htable.human_resource_id.label),
                               htable.human_resource_id.represent(human_resource_id),
                               ),
                            ),
                      )
    else:
        rheader = None

    return rheader

# =============================================================================
def hrm_competency_controller():
    """
        RESTful CRUD controller
         - used for Searching for people by Skill
         - used for Adding/Editing on Profile page
    """

    T = current.T
    s3db = current.s3db
    s3 = current.response.s3

    def prep(r):
        if r.method in ("create", "create.popup", "update", "update.popup"):
            # Coming from Profile page?
            table = r.table
            get_vars = r.get_vars
            person_id = get_vars.get("~.person_id", None)
            if person_id:
                try:
                    person_id = int(person_id)
                except ValueError:
                    pass
                else:
                    field = table.person_id
                    field.default = person_id
                    field.readable = field.writable = False

                # Additional filtering of the profile section by skill type
                skill_type_name = get_vars.get("~.skill_id$skill_type_id$name")
                if skill_type_name:
                    ttable = s3db.hrm_skill_type
                    query = (ttable.name == skill_type_name)
                    rows = current.db(query).select(ttable.id)
                    skill_type_ids = [row.id for row in rows]
                    if skill_type_ids:
                        field = table.skill_id
                        requires = field.requires
                        if isinstance(requires, IS_EMPTY_OR):
                            requires = requires.other
                        if hasattr(requires, "set_filter"):
                            requires.set_filter(filterby="skill_type_id",
                                                filter_opts=skill_type_ids,
                                                )

        elif not r.id:
            filter_widgets = [
                S3TextFilter(["person_id$first_name",
                              "person_id$middle_name",
                              "person_id$last_name",
                              "person_id$hrm_human_resource.job_title_id$name",
                             ],
                             label = T("Search"),
                             comment = T("You can search by job title or person name - enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
                             ),
                S3OptionsFilter("skill_id",
                                label = T("Skills"),
                                options = lambda: \
                                    s3_get_filter_opts("hrm_skill", translate=True),
                                ),
                S3OptionsFilter("competency_id",
                                label = T("Competency"),
                                options = lambda: \
                                    s3_get_filter_opts("hrm_competency_rating", translate=True),
                                ),
                ]
            s3db.configure("hrm_competency",
                           filter_widgets = filter_widgets,
                           list_fields = ["person_id",
                                          "skill_id",
                                          "competency_id",
                                          "comments",
                                          ],
                           )

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            # Custom action button to add the member to a team
            S3CRUD.action_buttons(r)

            args = ["[id]", "group_membership"]
            s3.actions.append({"label": str(T("Add to a Team")),
                               "_class": "action-btn",
                               "url": URL(f = "person",
                                          args = args),
                               }
                              )
        return output
    s3.postp = postp

    return current.rest_controller("hrm", "competency",
                                   # @ToDo: Create these if-required
                                   #csv_stylesheet = ("hrm", "competency.xsl"),
                                   #csv_template = ("hrm", "competency"),
                                   )

# =============================================================================
def hrm_credential_controller():
    """
        RESTful CRUD controller
         - could be used for Searching for people by Skill
         - used for Adding/Editing on Profile page
    """

    s3 = current.response.s3

    def prep(r):
        table = r.table
        if r.method in ("create", "create.popup", "update", "update.popup"):
            # Coming from Profile page?
            person_id = r.get_vars.get("~.person_id", None)
            if person_id:
                field = table.person_id
                field.default = person_id
                field.readable = field.writable = False
        if r.record:
            table.person_id.comment = None
            table.person_id.writable = False
        return True
    s3.prep = prep

    return current.rest_controller("hrm", "credential",
                                   # @ToDo: Create these if-required
                                   #csv_stylesheet = ("hrm", "credential.xsl"),
                                   #csv_template = ("hrm", "credential"),
                                   )

# =============================================================================
def hrm_experience_controller():
    """
        Experience Controller, defined in the model for use from
        multiple controllers for unified menus
         - used for Adding/Editing on Profile page
    """

    def prep(r):
        if r.method in ("create", "update"):
            # Coming from Profile page?
            field = current.s3db.hrm_experience.person_id
            person_id = current.request.get_vars.get("~.person_id", None)
            if person_id:
                field.default = person_id
                field.readable = field.writable = False
            elif r.method == "update":
                # Workaround until generic solution available:
                refresh = r.get_vars.get("refresh")
                if refresh and refresh.startswith("profile-list-hrm_experience"):
                    field.readable = field.writable = False
        return True
    current.response.s3.prep = prep

    return current.rest_controller("hrm", "experience",
                                   # @ToDo: Create these if-required
                                   #csv_stylesheet = ("hrm", "experience.xsl"),
                                   #csv_template = ("hrm", "experience"),
                                   )

# =============================================================================
def hrm_group_controller():
    """
        Team controller
        - uses the group table from PR
    """

    T = current.T
    s3db = current.s3db
    s3 = current.response.s3
    settings = current.deployment_settings
    team_name = settings.get_hrm_teams()

    tablename = "pr_group"
    table = s3db[tablename]

    _group_type = table.group_type
    if team_name == "Teams":
        _group_type.label = T("Team Type")
        table.description.label = T("Team Description")
        table.name.label = T("Team Name")
    # Default anyway
    #elif team_name == "Groups":
    #    _group_type.label = T("Group Type")
    #    table.description.label = T("Group Description")
    #    table.name.label = T("Group Name")

    # Set Defaults
    _group_type.default = 3  # 'Relief Team'
    # We use crud_form
    #_group_type.readable = _group_type.writable = False

    # Only show Relief Teams
    # Do not show system groups
    s3.filter = (table.system == False) & \
                (_group_type == 3)

    if team_name == "Teams":
        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            label_create = T("Add Team"),
            title_display = T("Team Details"),
            title_list = T("Teams"),
            title_update = T("Edit Team"),
            label_list_button = T("List Teams"),
            label_search_button = T("Search Teams"),
            msg_record_created = T("Team added"),
            msg_record_modified = T("Team updated"),
            msg_record_deleted = T("Team deleted"),
            msg_list_empty = T("No Teams currently registered"))

    # Format for filter_widgets & imports
    s3db.add_components("pr_group",
                        org_organisation_team = "group_id")

    # Pre-process
    def prep(r):
        # Redirect to member list when a new group has been created
        create_next = URL(f="group",
                          args=["[id]", "group_membership"])
        teams_orgs = settings.get_hrm_teams_orgs()
        if teams_orgs:
            if teams_orgs == 1:
                multiple = False
            else:
                multiple = True
            ottable = s3db.org_organisation_team
            label = ottable.organisation_id.label
            ottable.organisation_id.label = ""
            crud_form = S3SQLCustomForm("name",
                                        "description",
                                        S3SQLInlineComponent("organisation_team",
                                                             label = label,
                                                             fields = ["organisation_id"],
                                                             multiple = multiple,
                                                             ),
                                        "comments",
                                        )

            filter_widgets = [
                S3TextFilter(["name",
                              "description",
                              "comments",
                              "organisation_team.organisation_id$name",
                              "organisation_team.organisation_id$acronym",
                              ],
                             label = T("Search"),
                             comment = T("You can search by by group name, description or comments and by organization name or acronym. You may use % as wildcard. Press 'Search' without input to list all."),
                             #_class="filter-search",
                             ),
                S3OptionsFilter("organisation_team.organisation_id",
                                label = T("Organization"),
                                #hidden=True,
                                ),
                ]

            list_fields = ["organisation_team.organisation_id",
                           "name",
                           "description",
                           "comments",
                           ]

            s3db.configure("pr_group",
                           create_next = create_next,
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           list_fields = list_fields,
                           )
        else:
            s3db.configure("pr_group",
                           create_next = create_next,
                           )

        if r.interactive or r.representation in ("aadata", "xls", "pdf"):
            if r.component_name == "group_membership":
                hrm_configure_pr_group_membership()
                if r.representation == "xls":
                    # Modify Title of Report to show Team Name
                    s3.crud_strings.pr_group_membership.title_list = r.record.name
                    # Make it match Import sheets
                    tablename = "pr_group_membership"
                    list_fields = s3db.get_config(tablename, "list_fields")
                    # Remove "id" as XLS exporter doesn't like this not being first & has complicated skipping routines
                    try:
                        list_fields.remove("id")
                    except ValueError:
                        pass
                    # Separate Facility Type from Facility Name
                    s3db.hrm_human_resource.site_id.represent = s3db.org_SiteRepresent(show_type = False)
                    i = 0
                    for f in list_fields:
                        i += 1
                        if f == "site_id":
                            break

                    list_fields.insert(i,
                                       (T("Facility Type"),
                                        "person_id$human_resource.site_id$instance_type"))
                    # Split person_id into first/middle/last
                    try:
                        list_fields.remove("person_id")
                    except ValueError:
                        pass
                    list_fields = ["person_id$first_name",
                                   "person_id$middle_name",
                                   "person_id$last_name",
                                   ] + list_fields
                    s3db.configure(tablename,
                                   list_fields = list_fields,
                                   )

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            if not r.component:
                update_url = URL(args=["[id]", "group_membership"])
                S3CRUD.action_buttons(r, update_url=update_url)
                if current.deployment_settings.has_module("msg") and \
                   current.auth.permission.has_permission("update", c="hrm",
                                                          f="compose"):
                    s3.actions.append({
                        "url": URL(f="compose",
                                   vars = {"group_id": "[id]"}),
                        "_class": "action-btn send",
                        "label": s3_str(T("Send Message"))})

        return output
    s3.postp = postp

    if team_name == "Team":
        label = T("Team Details")
    elif team_name == "Group":
        label = T("Group Details")
    else:
        label = T("Basic Details")

    tabs = [(label, None),
            # Team should be contacted either via the Leader or
            # simply by sending a message to the group as a whole.
            #(T("Contact Data"), "contact"),
            (T("Members"), "group_membership"),
            (T("Documents"), "document"),
            ]

    return current.rest_controller("pr", "group",
                                   csv_stylesheet = ("hrm", "group.xsl"),
                                   csv_template = "group",
                                   rheader = lambda r: \
                                                s3db.pr_rheader(r, tabs=tabs),
                                   )

# =============================================================================
def hrm_human_resource_controller(extra_filter = None):
    """
        Human Resources Controller, defined in the model for use from
        multiple controllers for unified menus
         - used for Summary & Profile views, Imports and S3AddPersonWidget
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    s3 = current.response.s3
    settings = current.deployment_settings

    def prep(r):

        # Apply extra filter from controller
        if extra_filter is not None:
            r.resource.add_filter(extra_filter)

        c = r.controller
        deploy = c == "deploy"
        vol = c == "vol"

        if deploy:
            # Apply availability filter
            s3db.deploy_availability_filter(r)
        elif settings.get_hrm_unavailability():
            # Apply availability filter
            s3db.pr_availability_filter(r)

        if s3.rtl:
            # Ensure that + appears at the beginning of the number
            # - using table alias to only apply to filtered component
            f = s3db.get_aliased(s3db.pr_contact, "pr_phone_contact").value
            f.represent = s3_phone_represent
            f.widget = S3PhoneWidget()

        method = r.method
        if method in ("form", "lookup"):
            return True

        elif method == "profile":

            # Adapt list_fields for pr_address
            s3db.table("pr_address") # must load model before get_config
            list_fields = s3db.get_config("pr_address", "list_fields")
            list_fields.append("comments")

            # Show training date without time
            s3db.hrm_training.date.represent = lambda d: \
                S3DateTime.date_represent(d, utc=True)

            # Adapt list_fields for hrm_training
            list_fields = ["course_id",
                           "training_event_id$site_id",
                           "date",
                           "hours",
                           "grade",
                           "comments",
                           ]
            if deploy:
                list_fields.append("course_id$course_job_title.job_title_id")

            s3db.configure("hrm_training",
                           list_fields = list_fields,
                           )

            # Adapt list_fields for hrm_experience
            s3db.table("hrm_experience") # Load normal model
            s3db.configure("hrm_experience",
                           list_fields = [#"code",
                                          "employment_type",
                                          "activity_type",
                                          "organisation_id",
                                          "organisation",
                                          "job_title_id",
                                          "job_title",
                                          "responsibilities",
                                          "start_date",
                                          "end_date",
                                          "hours",
                                          "location_id",
                                          "supervisor_id",
                                          "comments",
                                          ],
                           )

            # Get the person's full name for header, and pe_id for
            # context filtering
            table = r.table
            record = r.record
            person_id = record.person_id
            ptable = db.pr_person
            person = db(ptable.id == person_id).select(ptable.first_name,
                                                       ptable.middle_name,
                                                       ptable.last_name,
                                                       ptable.pe_id,
                                                       limitby=(0, 1)
                                                       ).first()
            name = s3_fullname(person)
            pe_id = person.pe_id

            comments = table.organisation_id.represent(record.organisation_id)
            if record.job_title_id:
                comments = (SPAN("%s, " % \
                                 s3_str(table.job_title_id.represent(record.job_title_id))),
                            comments)

            # Configure widgets
            contacts_widget = {"label": "Contacts",
                               "label_create": "Add Contact",
                               "tablename": "pr_contact",
                               "type": "datalist",
                               "filter": FS("pe_id") == pe_id,
                               "icon": "phone",
                               # Default renderer:
                               #"list_layout": s3db.pr_render_contact,
                               "orderby": "priority asc",
                               # Can't do this as this is the HR perspective, not Person perspective
                               #"create_controller": c,
                               #"create_function": "person",
                               #"create_component": "contact",
                               }
            address_widget = {"label": "Address",
                              "label_create": "Add Address",
                              "type": "datalist",
                              "tablename": "pr_address",
                              "filter": FS("pe_id") == pe_id,
                              "icon": "home",
                              # Default renderer:
                              #"list_layout": s3db.pr_render_address,
                              # Can't do this as this is the HR perspective, not Person perspective
                              #"create_controller": c,
                              #"create_function": "person",
                              #"create_component": "address",
                              }
            skills_widget = {"label": "Skills",
                             "label_create": "Add Skill",
                             "type": "datalist",
                             "tablename": "hrm_competency",
                             "filter": FS("person_id") == person_id,
                             "icon": "comment-alt",
                             # Default renderer:
                             #"list_layout": hrm_competency_list_layout,
                             "create_controller": c,
                             # Can't do this as this is the HR perspective, not Person perspective
                             #"create_function": "person",
                             #"create_component": "competency",
                             }
            trainings_widget = {"label": "Trainings",
                                "label_create": "Add Training",
                                "type": "datalist",
                                "tablename": "hrm_training",
                                "filter": FS("person_id") == person_id,
                                "icon": "wrench",
                                # Default renderer:
                                #"list_layout": hrm_training_list_layout,
                                "create_controller": c,
                                # Can't do this as this is the HR perspective, not Person perspective
                                #"create_function": "person",
                                #"create_component": "training",
                                }
            experience_widget = {"label": "Experience",
                                 "label_create": "Add Experience",
                                 "type": "datalist",
                                 "tablename": "hrm_experience",
                                 "filter": FS("person_id") == person_id,
                                 "icon": "truck",
                                 # Default renderer:
                                 #"list_layout": hrm_experience_list_layout,
                                 "create_controller": c,
                                 # Can't do this as this is the HR perspective, not Person perspective
                                 #"create_function": "person",
                                 #"create_component": "experience",
                                 }
            docs_widget = {"label": "Documents",
                           "label_create": "Add Document",
                           "type": "datalist",
                           "tablename": "doc_document",
                           "filter": FS("doc_id") == record.doc_id,
                           "icon": "attachment",
                           # Default renderer:
                           #"list_layout": s3db.doc_document_list_layout,
                           }

            profile_widgets = [contacts_widget,
                               address_widget,
                               skills_widget,
                               trainings_widget,
                               experience_widget,
                               docs_widget,
                               ]

            if settings.get_hrm_use_education():
                education_widget = {"label": "Education",
                                    "label_create": "Add Education",
                                    "type": "datalist",
                                    "tablename": "pr_education",
                                    "filter": FS("person_id") == person_id,
                                    "icon": "book",
                                    # Can't do this as this is the HR perspective, not Person perspective
                                    #"create_controller": c,
                                    #"create_function": "person",
                                    #"create_component": "education",
                                    }
                profile_widgets.insert(-1, education_widget)

            if deploy:
                credentials_widget = {# @ToDo: deployment_setting for Labels
                                      "label": "Sectors",
                                      "label_create": "Add Sector",
                                      "type": "datalist",
                                      "tablename": "hrm_credential",
                                      "filter": FS("person_id") == person_id,
                                      "icon": "tags",
                                      # Default renderer:
                                      #"list_layout": hrm_credential_list_layout,
                                      "create_controller": c,
                                      # Can't do this as this is the HR perspective, not Person perspective
                                      #"create_function": "person",
                                      #"create_component": "credential",
                                      }
                profile_widgets.insert(2, credentials_widget)
                # Organizer-widget to record periods of unavailability:
                #profile_widgets.append({"label": "Unavailability",
                #                        "type": "organizer",
                #                        "tablename": "deploy_unavailability",
                #                        "master": "pr_person/%s" % person_id,
                #                        "component": "unavailability",
                #                        "icon": "calendar",
                #                        "url": URL(c="deploy", f="person",
                #                                   args = [person_id, "unavailability"],
                #                                   ),
                #                        })

            if settings.get_hrm_unavailability():
                unavailability_widget = {"label": "Unavailability",
                                         "type": "organizer",
                                         "tablename": "pr_unavailability",
                                         "master": "pr_person/%s" % person_id,
                                         "component": "unavailability",
                                         "icon": "calendar",
                                         "url": URL(c="pr", f="person",
                                                    args = [person_id, "unavailability"],
                                                    ),
                                         }
                profile_widgets.insert(-1, unavailability_widget)

            # Configure resource
            s3db.configure("hrm_human_resource",
                           profile_cols = 1,
                           profile_header = DIV(A(s3_avatar_represent(person_id,
                                                                      tablename="pr_person",
                                                                      _class="media-object"),
                                                  _class="pull-left",
                                                  #_href=event_url,
                                                  ),
                                                H2(name),
                                                P(comments),
                                                _class="profile-header",
                                                ),
                           profile_title = "%s : %s" % (
                               s3_str(s3.crud_strings["hrm_human_resource"].title_display),
                               s3_str(name),
                               ),
                           profile_widgets = profile_widgets,
                           )

        elif method == "summary":

            # CRUD Strings
            if deploy:
                deploy_team = settings.get_deploy_team_label()
                s3.crud_strings["hrm_human_resource"]["title_list"] = \
                    T("%(team)s Members") % {"team": T(deploy_team)}
            else:
                s3.crud_strings["hrm_human_resource"]["title_list"] = \
                    T("Staff & Volunteers")

            # Filter Widgets
            filter_widgets = hrm_human_resource_filters(resource_type = "both",
                                                        hrm_type_opts = s3db.hrm_type_opts)

            # List Fields
            list_fields = ["person_id",
                           "job_title_id",
                           "organisation_id",
                           ]

            # Report Options
            report_fields = ["organisation_id",
                             "person_id",
                             "person_id$gender",
                             "job_title_id",
                             (T("Training"), "training.course_id"),
                             ]
            rappend = report_fields.append

            if settings.get_hrm_use_national_id():
                list_fields.append((T("National ID"), "person_id$national_id.value"))

            use_code = settings.get_hrm_use_code()
            if use_code is True or use_code and not vol:
                list_fields.append("code")

            if vol:
                vol_active = settings.get_hrm_vol_active()
                if vol_active:
                    list_fields.append((T("Active"), "details.active"))
                    rappend((T("Active"), "details.active"))
                vol_experience = settings.get_hrm_vol_experience()
                if vol_experience in ("programme", "both"):
                    list_fields.append((T("Program"), "person_id$hours.programme_id"))
                    rappend((T("Program"), "person_id$hours.programme_id"))
            elif settings.get_hrm_staff_departments():
                list_fields.extend(("department_id",
                                    "site_id"))
                report_fields.extend(("site_id",
                                      "department_id"))
            else:
                list_fields.append("site_id")
                rappend("site_id")

            list_fields.extend(((T("Email"), "email.value"),
                                (settings.get_ui_label_mobile_phone(), "phone.value"),
                                ))

            # Which levels of Hierarchy are we using?
            levels = current.gis.get_relevant_hierarchy_levels()

            for level in levels:
                rappend("location_id$%s" % level)
            if deploy:
                rappend((T("Credential"), "credential.job_title_id"))
            teams = settings.get_hrm_teams()
            if teams:
                if teams == "Teams":
                    teams = "Team"
                elif teams == "Groups":
                    teams = "Group"
                rappend((teams, "group_membership.group_id"))
            if settings.get_org_regions():
                rappend("organisation_id$region_id")

            report_options = Storage(rows = report_fields,
                                     cols = report_fields,
                                     fact = report_fields,
                                     defaults = Storage(
                                        rows = "organisation_id",
                                        cols = "training.course_id",
                                        fact = "count(person_id)",
                                        totals = True,
                                        )
                                     )

            # Configure resource
            s3db.configure("hrm_human_resource",
                           filter_widgets = filter_widgets,
                           list_fields = list_fields,
                           report_options = report_options,
                           )

            # Remove controller filter
            #s3.filter = None

        #elif r.representation in ("geojson", "plain") or deploy:
        #    # No filter
        #    pass

        #else:
        #    if vol:
        #        # Default to Volunteers
        #        type_filter = FS("type") == 2
        #    else:
        #        # Default to Staff
        #        type_filter = FS("type") == 1
        #    r.resource.add_filter(type_filter)

        # Others
        if r.interactive:
            if method == "create" and not r.component:
                if not settings.get_hrm_mix_staff():
                    # Need to either create a Staff or a Volunteer through separate forms
                    if vol:
                        c = "vol"
                        f = "volunteer"
                    else:
                        c = "hrm"
                        f = "staff"
                    redirect(URL(c=c, f=f,
                                 args=r.args,
                                 vars=r.vars))

            elif method == "delete":
                if deploy:
                    # Delete the Application, not the HR
                    atable = s3db.deploy_application
                    app = db(atable.human_resource_id == r.id).select(atable.id,
                                                                      limitby=(0, 1)
                                                                      ).first()
                    if not app:
                        current.session.error = "Cannot find Application to delete!"
                        redirect(URL(args="summary"))
                    redirect(URL(f="application", args=[app.id, "delete"]))
                else:
                    # Don't redirect
                    pass

            elif method == "profile":
                # Don't redirect
                pass

            elif method == "deduplicate":
                # Don't use AddPersonWidget here
                from gluon.sqlhtml import OptionsWidget
                field = r.table.person_id
                field.requires = IS_ONE_OF(db, "pr_person.id",
                                           label = field.represent)
                field.widget = OptionsWidget.widget

            elif r.id:
                # Redirect to person controller
                if r.record.type == 2:
                    group = "volunteer"
                else:
                    group = "staff"
                if r.function == "trainee":
                    fn = "trainee_person"
                else:
                    fn = "person"
                redirect(URL(f = fn,
                             args = [method] if method else [],
                             vars = {"human_resource.id" : r.id,
                                     "group" : group
                                     },
                             ))

        elif r.representation == "xls" and not r.component:
            hrm_xls_list_fields(r)

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                if r.controller == "deploy":
                    # Application is deleted, not HR
                    deletable = True
                    # Open Profile page
                    read_url = URL(args = ["[id]", "profile"])
                    update_url = URL(args = ["[id]", "profile"])
                else:
                    deletable = settings.get_hrm_deletable()
                    # Standard CRUD buttons
                    read_url = None
                    update_url = None
                S3CRUD.action_buttons(r,
                                      deletable = deletable,
                                      read_url = read_url,
                                      update_url = update_url)
                if "msg" in settings.modules and \
                   settings.get_hrm_compose_button() and \
                   current.auth.permission.has_permission("update",
                                                          c="hrm",
                                                          f="compose"):
                    s3.actions.append({
                        "url": URL(f="compose",
                                   vars = {"human_resource.id": "[id]"}),
                        "_class": "action-btn send",
                        "label": str(T("Send Message"))
                        })

        elif r.representation == "plain":
            # Map Popups
            output = hrm_map_popup(r)

        return output
    s3.postp = postp

    return current.rest_controller("hrm", "human_resource")

# =============================================================================
def hrm_person_controller(**attr):
    """
        Persons Controller, defined in the model for use from
        multiple controllers for unified menus
         - used for access to component Tabs, Personal Profile & Imports
         - includes components relevant to HRM
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    #auth = current.auth
    response = current.response
    session = current.session
    settings = current.deployment_settings
    s3 = response.s3

    configure = s3db.configure
    set_method = s3db.set_method

    # Custom Method(s) for Contacts
    contacts_tabs = settings.get_pr_contacts_tabs()
    if "all" in contacts_tabs:
        set_method("pr", "person",
                   method = "contacts",
                   action = s3db.pr_Contacts)
    if "public" in contacts_tabs:
        set_method("pr", "person",
                   method = "public_contacts",
                   action = s3db.pr_Contacts)
    if "private" in contacts_tabs:
        set_method("pr", "person",
                   method = "private_contacts",
                   action = s3db.pr_Contacts)

    # Custom Method for CV
    set_method("pr", "person",
               method = "cv",
               action = hrm_CV)

    # Custom Method for HR Record
    set_method("pr", "person",
               method = "record",
               action = hrm_Record)

    if settings.has_module("asset"):
        # Assets as component of people
        s3db.add_components("pr_person", asset_asset="assigned_to_id")
        # Edits should always happen via the Asset Log
        # @ToDo: Allow this method too, if we can do so safely
        configure("asset_asset",
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )

    get_vars = current.request.get_vars
    group = get_vars.get("group", "staff")
    hr_id = get_vars.get("human_resource.id", None)
    if not str(hr_id).isdigit():
        hr_id = None

    # Configure human resource table
    table = s3db.hrm_human_resource
    table.type.default = 1
    get_vars["xsltmode"] = "staff"
    if hr_id:
        hr = db(table.id == hr_id).select(table.type,
                                          limitby=(0, 1)).first()
        if hr:
            group = "volunteer" if hr.type == 2 else "staff"
            # Also inform the back-end of this finding
            get_vars["group"] = group

    # Configure person table
    table = db.pr_person
    tablename = "pr_person"
    configure(tablename,
              deletable = False,
              )

    #mode = session.s3.hrm.mode
    #if mode is not None:
    #    # Configure for personal mode
    #    s3.crud_strings[tablename].update(
    #        title_display = T("Personal Profile"),
    #        title_update = T("Personal Profile"))
    #    # People can view their own HR data, but not edit it
    #    # - over-ride in Template if need to make any elements editable
    #    configure("hrm_human_resource",
    #              deletable = False,
    #              editable = False,
    #              insertable = False,
    #              )
    #    configure("hrm_certification",
    #              deletable = False,
    #              editable = False,
    #              insertable = False,
    #              )
    #    configure("hrm_credential",
    #              deletable = False,
    #              editable = False,
    #              insertable = False,
    #              )
    #    configure("hrm_competency",
    #              deletable = False,
    #              editable = False,
    #              insertable = True,  # Can add unconfirmed
    #              )
    #    configure("hrm_training",    # Can add but not provide grade
    #              deletable = False,
    #              editable = False,
    #              insertable = True,
    #              )
    #    configure("hrm_experience",
    #              deletable = False,
    #              editable = False,
    #              insertable = False,
    #              )
    #    configure("pr_group_membership",
    #              deletable = False,
    #              editable = False,
    #              insertable = False,
    #              )
    #else:
    # Configure for HR manager mode
    if settings.get_hrm_staff_label() == T("Contacts"):
        s3.crud_strings[tablename].update(
                title_upload = T("Import Contacts"),
                title_display = T("Contact Details"),
                title_update = T("Contact Details")
                )
    elif group == "volunteer":
        s3.crud_strings[tablename].update(
                title_upload = T("Import Volunteers"),
                title_display = T("Volunteer Details"),
                title_update = T("Volunteer Details")
                )
    else:
        s3.crud_strings[tablename].update(
                title_upload = T("Import Staff"),
                title_display = T("Staff Member Details"),
                title_update = T("Staff Member Details")
                )
    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: {"ReplaceOption": T("Remove existing data before import")}

    # Import pre-process
    def import_prep(data, group=group):
        """
            Deletes all HR records (of the given group) of the
            organisation/branch before processing a new data import
        """
        resource, tree = data
        xml = current.xml
        tag = xml.TAG
        att = xml.ATTRIBUTE
        if s3.import_replace:
            if tree is not None:
                if group == "staff":
                    group = 1
                elif group == "volunteer":
                    group = 2
                else:
                    return # don't delete if no group specified

                root = tree.getroot()
                expr = "/%s/%s[@%s='org_organisation']/%s[@%s='name']" % \
                       (tag.root, tag.resource, att.name, tag.data, att.field)
                orgs = root.xpath(expr)
                for org in orgs:
                    org_name = org.get("value", None) or org.text
                    if org_name:
                        try:
                            org_name = json.loads(xml.xml_decode(org_name))
                        except:
                            pass
                    if org_name:
                        htable = s3db.hrm_human_resource
                        otable = s3db.org_organisation
                        query = (otable.name == org_name) & \
                                (htable.organisation_id == otable.id) & \
                                (htable.type == group)
                        resource = s3db.resource("hrm_human_resource", filter=query)
                        # Use cascade=True so that the deletion gets
                        # rolled back if the import fails:
                        resource.delete(format="xml", cascade=True)

    s3.import_prep = import_prep

    # CRUD pre-process
    def prep(r):
        # Plug-in role matrix for Admins/OrgAdmins
        S3PersonRoleManager.set_method(r, entity="pr_person")

        if s3.rtl:
            # Ensure that + appears at the beginning of the number
            # - using table alias to only apply to filtered component
            f = s3db.get_aliased(s3db.pr_contact, "pr_phone_contact").value
            f.represent = s3_phone_represent
            f.widget = S3PhoneWidget()

        method = r.method
        if r.representation == "s3json":
            current.xml.show_ids = True
        elif r.interactive and method != "import":
            if not r.component:
                table = r.table
                table.pe_label.readable = table.pe_label.writable = False
                table.missing.readable = table.missing.writable = False
                table.age_group.readable = table.age_group.writable = False
                # Assume volunteers only between 5-120
                dob = table.date_of_birth
                dob.widget = S3CalendarWidget(past_months = 1440,
                                              future_months = -60,
                                              )

                person_details_table = s3db.pr_person_details
                # No point showing the 'Occupation' field - that's the Job Title in the Staff Record
                person_details_table.occupation.readable = person_details_table.occupation.writable = False

                # Organisation Dependent Fields
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("pr_person", "middle_name")
                set_org_dependent_field("pr_person_details", "father_name")
                set_org_dependent_field("pr_person_details", "mother_name")
                set_org_dependent_field("pr_person_details", "grandfather_name")
                set_org_dependent_field("pr_person_details", "affiliations")
                set_org_dependent_field("pr_person_details", "company")
            else:
                component_name = r.component_name
                if component_name == "physical_description":
                    # Hide all but those details that we want
                    # Lock all the fields
                    table = r.component.table
                    for field in table.fields:
                        table[field].writable = table[field].readable = False
                    # Now enable those that we want
                    table.ethnicity.writable = table.ethnicity.readable = True
                    table.blood_type.writable = table.blood_type.readable = True
                    table.medical_conditions.writable = table.medical_conditions.readable = True
                    table.other_details.writable = table.other_details.readable = True

                elif component_name == "appraisal":
                    mission_id = r.get_vars.get("mission_id", None)
                    if mission_id:
                        hatable = r.component.table
                        # Lookup Code
                        mtable = s3db.deploy_mission
                        mission = db(mtable.id == mission_id).select(mtable.code,
                                                                     limitby=(0, 1)
                                                                     ).first()
                        if mission:
                            hatable.code.default = mission.code
                        # Lookup Job Title
                        atable = db.deploy_assignment
                        htable = db.hrm_human_resource
                        query = (atable.mission_id == mission_id) & \
                                (atable.human_resource_id == htable.id) & \
                                (htable.person_id == r.id)
                        assignment = db(query).select(atable.job_title_id,
                                                      limitby=(0, 1)
                                                      ).first()
                        if assignment:
                            hatable.job_title_id.default = assignment.job_title_id

                elif component_name == "asset":
                    # Edits should always happen via the Asset Log
                    # @ToDo: Allow this method too, if we can do so safely
                    configure("asset_asset",
                              insertable = False,
                              editable = False,
                              deletable = False,
                              )

                elif component_name == "group_membership":
                    hrm_configure_pr_group_membership()

                elif component_name == "salary":
                    hrm_configure_salary(r)

            if method == "record" or r.component_name == "human_resource":
                table = s3db.hrm_human_resource
                table.person_id.writable = table.person_id.readable = False
                table.site_id.readable = table.site_id.writable = True
                #org = session.s3.hrm.org
                #f = table.organisation_id
                #if org is None:
                #    f.widget = None
                #    f.writable = False
                #else:
                #    f.default = org
                #    f.readable = f.writable = False
                #    table.site_id.requires = IS_EMPTY_OR(
                #        IS_ONE_OF(db,
                #                  "org_site.%s" % s3db.super_key(db.org_site),
                #                  s3db.org_site_represent,
                #                  filterby="organisation_id",
                #                  filter_opts=(session.s3.hrm.org,),
                #                  ))
            elif method == "cv" or r.component_name == "training":
                list_fields = ["course_id",
                               "grade",
                               ]
                if settings.get_hrm_course_pass_marks:
                    list_fields.append("grade_details")
                list_fields.append("date")
                s3db.configure("hrm_training",
                               list_fields = list_fields,
                               )

            resource = r.resource
            #if mode is not None:
            #    resource.build_query(id=auth.s3_logged_in_person())
            if method not in ("deduplicate", "search_ac"):
                if not r.id and not hr_id:
                    # pre-action redirect => must retain prior errors
                    if response.error:
                        session.error = response.error
                    redirect(URL(r=r, f="staff"))
                if resource.count() == 1:
                    resource.load()
                    r.record = resource.records().first()
                    if r.record:
                        r.id = r.record.id
                if not r.record:
                    session.error = T("Record not found")
                    redirect(URL(f="staff"))
                if hr_id and r.component_name == "human_resource":
                    r.component_id = hr_id
                configure("hrm_human_resource",
                          insertable = False,
                          )

        elif r.representation == "aadata":
            if r.component_name == "group_membership":
                hrm_configure_pr_group_membership()
            elif method == "cv" or r.component_name == "training":
                list_fields = ["course_id",
                               "grade",
                               ]
                if settings.get_hrm_course_pass_marks:
                    list_fields.append("grade_details")
                list_fields.append("date")
                s3db.configure("hrm_training",
                               list_fields = list_fields,
                               )
        return True
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "asset":
                # Provide a link to assign a new Asset
                # @ToDo: Proper Widget to do this inline
                output["add_btn"] = A(T("Assign Asset"),
                                      _href=URL(c="asset", f="asset"),
                                      _id="add-btn",
                                      _class="action-btn")
        return output
    s3.postp = postp

    # REST Interface
    #orgname = session.s3.hrm.orgname

    _attr = {"csv_stylesheet": ("hrm", "person.xsl"),
             "csv_template": "staff",
             "csv_extra_fields": [{"label": "Type",
                                   "field": s3db.hrm_human_resource.type,
                                   },
                                 ],
             # Better in the native person controller (but this isn't always accessible):
             #"deduplicate": "",
             #"orgname": orgname,
             "replace_option": T("Remove existing data before import"),
             "rheader": hrm_rheader,
             }
    _attr.update(attr)

    return current.rest_controller("pr", "person", **_attr)

# =============================================================================
def hrm_training_controller():
    """
        Training Controller, defined in the model for use from
        multiple controllers for unified menus
         - used for Searching for Participants
         - used for Adding/Editing on Profile page
    """

    s3db = current.s3db

    def prep(r):
        method = r.method
        if r.interactive or r.representation == "aadata":
            s3db.configure("hrm_training",
                           #insertable = False,
                           listadd = False,
                           )

            if method in ("create", "update"):
                # Coming from Profile page?
                person_id = r.get_vars.get("~.person_id", None)
                if person_id:
                    field = s3db.hrm_training.person_id
                    field.default = person_id
                    field.readable = field.writable = False

            # @ToDo: Complete
            #elif method == "import":
            #    # Allow course to be populated onaccept from training_event_id
            #    table = s3db.hrm_training
            #    s3db.configure("hrm_training",
            #                   onvalidation = hrm_training_onvalidation,
            #                   )
            #    table.course_id.requires = IS_EMPTY_OR(table.course_id.requires)
            #    f = table.training_event_id
            #    training_event_id = r.get_vars.get("~.training_event_id", None)
            #    if training_event_id:
            #        f.default = training_event_id
            #    else:
            #        f.writable = True

        if method == "report":
            # Configure virtual fields for reports
            s3db.configure("hrm_training", extra_fields=["date"])
            table = s3db.hrm_training
            table.year = Field.Method("year", hrm_training_year)
            table.month = Field.Method("month", hrm_training_month)

        # Can't reliably link to persons as these are imported in random order
        # - do this postimport if desired (see RMSAmericas)
        #elif method == "import":
        #    # If users accounts are created for imported participants
        #    s3db.configure("auth_user",
        #                   create_onaccept = lambda form: current.auth.s3_approve_user(form.vars),
        #                   )

        return True
    current.response.s3.prep = prep

    return current.rest_controller("hrm", "training",
                                   csv_stylesheet = ("hrm", "training.xsl"),
                                   csv_template = ("hrm", "training"),
                                   csv_extra_fields = [{"label": "Training Event",
                                                        "field": s3db.hrm_training.training_event_id,
                                                        },
                                                       ],
                                   )

# =============================================================================
def hrm_training_event_controller():
    """
        Training Event Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    s3 = current.response.s3

    def prep(r):
        if r.component_name == "target":

            tablename = "dc_target"

            # Simplify
            table = r.component.table
            table.location_id.readable = table.location_id.writable = False
            #table.organisation_id.readable = table.organisation_id.writable = False
            #table.comments.readable = table.comments.writable = False

            # CRUD strings
            T = current.T
            label = current.deployment_settings.get_dc_response_label()
            if label == "Survey":
                #label = T("Survey")
                s3.crud_strings[tablename] = Storage(
                    label_create = T("Create Survey"),
                    title_display = T("Survey Details"),
                    title_list = T("Surveys"),
                    title_update = T("Edit Survey"),
                    title_upload = T("Import Surveys"),
                    label_list_button = T("List Surveys"),
                    label_delete_button = T("Delete Survey"),
                    msg_record_created = T("Survey added"),
                    msg_record_modified = T("Survey updated"),
                    msg_record_deleted = T("Survey deleted"),
                    msg_list_empty = T("No Surveys currently registered"))
            else:
                #label = T("Assessment")
                s3.crud_strings[tablename] = Storage(
                    label_create = T("Create Assessment"),
                    title_display = T("Assessment Details"),
                    title_list = T("Assessments"),
                    title_update = T("Edit Assessment"),
                    title_upload = T("Import Assessments"),
                    label_list_button = T("List Assessments"),
                    label_delete_button = T("Delete Assessment"),
                    msg_record_created = T("Assessment added"),
                    msg_record_modified = T("Assessment updated"),
                    msg_record_deleted = T("Assessment deleted"),
                    msg_list_empty = T("No Assessments currently registered"))

            # Open in native controller
            current.s3db.configure(tablename,
                                   linkto = lambda record_id: URL(c="dc", f="target", args=[record_id, "read"]),
                                   linkto_update = lambda record_id: URL(c="dc", f="target", args=[record_id, "update"]),
                                   )

        elif r.component_name == "participant" and \
           (r.interactive or \
            r.representation in ("aadata", "pdf", "xls")):

            # Use appropriate CRUD strings
            T = current.T
            s3.crud_strings["hrm_training"] = Storage(
                label_create = T("Add Participant"),
                title_display = T("Participant Details"),
                title_list = T("Participants"),
                title_update = T("Edit Participant"),
                title_upload = T("Import Participants"),
                label_list_button = T("List Participants"),
                label_delete_button = T("Remove Participant"),
                msg_record_created = T("Participant added"),
                msg_record_modified = T("Participant updated"),
                msg_record_deleted = T("Participant removed"),
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
            settings = current.deployment_settings
            list_fields = ["person_id",
                           ]
            if settings.get_hrm_use_job_titles():
                list_fields.append((T("Job Title"), "job_title"))                       # Field.Method
            list_fields += [(settings.get_hrm_organisation_label(), "organisation"),    # Field.Method
                            "grade",
                            ]
            if settings.get_hrm_course_pass_marks():
                list_fields.append("grade_details")
            if settings.get_hrm_use_certificates():
                list_fields.append("certification_from_training.number")

            current.s3db.configure("hrm_training",
                                   list_fields = list_fields
                                   )
        return True
    s3.prep = prep

    #def postp(r, output):
    #    if r.interactive:
    #        # @ToDo: Restore once the other part is working
    #        if r.component_name == "participant" and \
    #            isinstance(output, dict):
    #           showadd_btn = output.get("showadd_btn", None)
    #           if showadd_btn:
    #               # Add an Import button
    #               if s3.crud.formstyle == "bootstrap":
    #                   _class = "s3_modal"
    #               else:
    #                   _class = "action-btn s3_modal"
    #               import_btn = S3CRUD.crud_button(label=current.T("Import Participants"),
    #                                               _class=_class,
    #                                               _href=URL(f="training", args="import.popup",
    #                                                         vars={"~.training_event_id":r.id}),
    #                                               )
    #               output["showadd_btn"] = TAG[""](showadd_btn, import_btn)
    #    return output
    #s3.postp = postp

    return current.rest_controller("hrm", "training_event",
                                   rheader = hrm_rheader,
                                   )

# =============================================================================
def hrm_xls_list_fields(r, staff=True, vol=True):
    """
        Configure Human Resource list_fields for XLS Export
        - match the XLS Import
         - no l10n if column labels
         - simple represents
    """

    s3db = current.s3db
    settings = current.deployment_settings
    table = r.table
    table.organisation_id.represent = s3db.org_OrganisationRepresent(acronym=False,
                                                                     parent=False)
    table.site_id.represent = s3db.org_SiteRepresent(show_type=False)

    current.messages["NONE"] = "" # Don't want to see "-"
    ptable = s3db.pr_person
    ptable.middle_name.represent = lambda v: v or ""
    ptable.last_name.represent = lambda v: v or ""
    list_fields = [("First Name", "person_id$first_name"),
                   ("Middle Name", "person_id$middle_name"),
                   ("Last Name", "person_id$last_name"),
                   ]
    if staff and vol:
        list_fields.insert(0, ("Type", "type"))
    if settings.get_hrm_use_code():
        list_fields.append(("Staff ID", "code"))
    list_fields.append(("Sex", "person_id$gender"))
    #if settings.get_hrm_multiple_orgs():
    if settings.get_org_branches():
        # @ToDo: Smart Handling for emptying the Root if org == root
        # @ToDo: Smart Handling for when we have Sub-Branches
        list_fields += [(settings.get_hrm_root_organisation_label(), "organisation_id$root_organisation"), # Not imported
                        ("Organisation", "organisation_id"),
                        ]
    else:
        list_fields.append(("Organisation", "organisation_id"))
    if (staff and settings.get_hrm_use_job_titles()) or \
       (vol and settings.get_hrm_vol_roles()):
        table.job_title_id.represent = S3Represent("hrm_job_title", translate=True) # Need to reinitialise to get the new value for NONE
        list_fields.append(("Job Title", "job_title_id"))
    if (staff and settings.get_hrm_staff_departments()) or \
       (vol and settings.get_hrm_vol_departments()):
        table.department_id.represent = S3Represent("hrm_department") # Need to reinitialise to get the new value for NONE
        list_fields.append(("Department", "department_id"))
    if staff or ("site_id" in settings.get_hrm_location_vol()):
        list_fields += [("Office", "site_id"),
                        ("Facility Type", "site_id$instance_type"),
                        ]

    list_fields += [("Email", "email.value"),
                    ("Mobile Phone", "phone.value"),
                    ("DOB", "person_id$date_of_birth"),
                    ("Start Date", "start_date"),
                    ("End Date", "end_date"), # Not reimported
                    ("Status", "status"),
                    ("Essential", "essential"), # Not reimported
                    ]

    gtable = s3db.gis_location
    levels = current.gis.get_relevant_hierarchy_levels()
    for level in levels:
        gtable[level].represent = lambda v: v or ""
        if level == "L0":
            list_fields.append(("Home Country", "home_address.location_id$%s" % level))
        else:
            list_fields.append(("Home %s" % level, "home_address.location_id$%s" % level))
    gtable.addr_street.represent = lambda v: v or ""
    list_fields.append(("Home Address", "home_address.location_id$addr_street"))
    if settings.get_gis_postcode_selector():
        gtable.addr_postcode.represent = lambda v: v or ""
        list_fields.append(("Home Postcode", "home_address.location_id$addr_postcode"))

    if settings.get_hrm_use_trainings():
        s3db.hrm_training.course_id.represent = S3Represent("hrm_course", translate=True) # Need to reinitialise to get the new value for NONE
        list_fields.append(("Trainings", "person_id$training.course_id"))
    if settings.get_hrm_use_certificates():
        # @ToDo: Make Importable
        s3db.hrm_certification.certificate_id.represent = S3Represent("hrm_certificate") # Need to reinitialise to get the new value for NONE
        list_fields.append(("Certificates", "person_id$certification.certificate_id"))
    if settings.get_hrm_use_skills():
        s3db.hrm_competency.skill_id.represent = S3Represent("hrm_skill") # Need to reinitialise to get the new value for NONE
        list_fields.append(("Skills", "person_id$competency.skill_id"))
    if settings.get_hrm_use_education():
        etable = s3db.pr_education
        etable.level_id.represent = S3Represent("pr_education_level") # Need to reinitialise to get the new value for NONE
        etable.award.represent = lambda v: v or ""
        etable.major.represent = lambda v: v or ""
        etable.grade.represent = lambda v: v or ""
        etable.year.represent = lambda v: v or ""
        etable.institute.represent = lambda v: v or ""
        list_fields.extend((("Education Level", "person_id$education.level_id"),
                            ("Degree Name", "person_id$education.award"),
                            ("Major", "person_id$education.major"),
                            ("Grade", "person_id$education.grade"),
                            ("Year", "person_id$education.year"),
                            ("Institute", "person_id$education.institute"),
                           ))

    if vol:
        if settings.get_hrm_vol_active():
            list_fields.append(("Active", "details.active"))
        if settings.get_hrm_vol_experience() in ("programme", "both"):
            # @ToDo: Make Importable
            s3db.hrm_programme_hours.programme_id.represent = S3Represent("hrm_programme") # Need to reinitialise to get the new value for NONE
            list_fields.append(("Programs", "person_id$hours.programme_id"))
        if settings.get_hrm_use_awards():
            list_fields.append(("Awards", "person_id$award.award_id"))
    list_fields.append(("Comments", "comments"))

    r.resource.configure(list_fields = list_fields)

    return list_fields

# =============================================================================
class hrm_CV(S3Method):
    """
        Curriculum Vitae, custom profile page with multiple DataTables:
            * Awards
            * Education
            * Experience
            * Training
            * Skills
    """

    def __init__(self, form=None):
        """
            Constructor

            @param form: widget config to inject at the top of the CV,
                         or a callable to produce such a widget config
        """

        self.form = form

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "person" and \
           r.id and \
           not r.component and \
           r.representation in ("html", "aadata"):

            T = current.T
            s3db = current.s3db
            get_config = s3db.get_config
            settings = current.deployment_settings
            tablename = r.tablename
            if r.controller == "vol":
                controller = "vol"
                vol = True
            elif r.controller == "deploy":
                controller = "deploy"
                vol = False
            elif r.controller == "member":
                controller = "member"
                vol = False
            else:
                controller = "hrm"
                vol = False

            def dt_row_actions(component, tablename):
                def row_actions(r, list_id):
                    editable = get_config(tablename, "editable")
                    if editable is None:
                        editable = True
                    deletable = get_config(tablename, "deletable")
                    if deletable is None:
                        deletable = True
                    if editable:
                        # HR Manager
                        actions = [{"label": T("Open"),
                                    "url": r.url(component=component,
                                                 component_id="[id]",
                                                 method="update.popup",
                                                 vars={"refresh": list_id}),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    else:
                        # Typically the User's personal profile
                        actions = [{"label": T("Open"),
                                    "url": r.url(component=component,
                                                 component_id="[id]",
                                                 method="read.popup",
                                                 vars={"refresh": list_id}),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    if deletable:
                        actions.append({"label": T("Delete"),
                                        "_ajaxurl": r.url(component=component,
                                                          component_id="[id]",
                                                          method="delete.json",
                                                          ),
                                        "_class": "action-btn delete-btn-ajax dt-ajax-delete",
                                        })
                    return actions
                return row_actions

            profile_widgets = []
            form = self.form
            if form:
                if callable(form):
                    form = form(r)
                if form is not None:
                    profile_widgets.append(form)

            if vol and settings.get_hrm_use_awards():
                tablename = "vol_volunteer_award"
                r.customise_resource(tablename)
                widget = {# Use CRUD Strings (easier to customise)
                          #"label": "Awards",
                          #"label_create": "Add Award",
                          "type": "datatable",
                          "actions": dt_row_actions("award", tablename),
                          "tablename": tablename,
                          "context": "person",
                          "create_controller": "vol",
                          "create_function": "person",
                          "create_component": "award",
                          "pagesize": None, # all records
                          }
                profile_widgets.append(widget)

            if settings.get_hrm_use_education():
                tablename = "pr_education"
                widget = {"label": "Education",
                          "label_create": "Add Education",
                          "type": "datatable",
                          "actions": dt_row_actions("education", tablename),
                          "tablename": tablename,
                          "context": "person",
                          "create_controller": controller,
                          "create_function": "person",
                          "create_component": "education",
                          "pagesize": None, # all records
                          }
                profile_widgets.append(widget)

            if vol:
                vol_experience = settings.get_hrm_vol_experience()
                experience = vol_experience in ("both", "experience")
                missions = None
            else:
                staff_experience = settings.get_hrm_staff_experience()
                experience = staff_experience in ("both", "experience")
                missions = staff_experience in ("both", "missions")

            if experience:
                tablename = "hrm_experience"
                r.customise_resource(tablename)
                widget = {# Use CRUD Strings (easier to customise)
                          #"label": "Experience",
                          #"label_create": "Add Experience",
                          "type": "datatable",
                          "actions": dt_row_actions("experience", tablename),
                          "tablename": tablename,
                          "context": "person",
                          "filter": FS("assignment__link.assignment_id") == None,
                          "create_controller": controller,
                          "create_function": "person",
                          "create_component": "experience",
                          "pagesize": None, # all records
                          # Settings suitable for RMSAmericas
                          "list_fields": ["start_date",
                                          "end_date",
                                          "employment_type",
                                          "organisation",
                                          "job_title",
                                          ],
                          }
                profile_widgets.append(widget)

            if missions:
                tablename = "hrm_experience"
                widget = {"label": "Missions",
                          "type": "datatable",
                          "actions": dt_row_actions("experience", tablename),
                          "tablename": tablename,
                          "context": "person",
                          "filter": FS("assignment__link.assignment_id") != None,
                          "insert": False,
                          "pagesize": None, # all records
                          # Settings suitable for RMSAmericas
                          "list_fields": ["start_date",
                                          "end_date",
                                          "location_id",
                                          #"organisation_id",
                                          "job_title_id",
                                          "job_title",
                                          ],
                          }
                profile_widgets.append(widget)

            if settings.get_hrm_use_trainings():
                tablename = "hrm_training"
                if settings.get_hrm_trainings_external():
                    widget = {"label": "Internal Training",
                              "label_create": "Add Internal Training",
                              "type": "datatable",
                              "actions": dt_row_actions("training", tablename),
                              "tablename": tablename,
                              "context": "person",
                              "filter": FS("course_id$external") == False,
                              "create_controller": controller,
                              "create_function": "person",
                              "create_component": "training",
                              "pagesize": None, # all records
                              }
                    profile_widgets.append(widget)
                    widget = {"label": "External Training",
                              "label_create": "Add External Training",
                              "type": "datatable",
                              "actions": dt_row_actions("training", tablename),
                              "tablename": tablename,
                              "context": "person",
                              "filter": FS("course_id$external") == True,
                              "create_controller": controller,
                              "create_function": "person",
                              "create_component": "training",
                              "pagesize": None, # all records
                              }
                    profile_widgets.append(widget)
                else:
                    widget = {"label": "Training",
                              "label_create": "Add Training",
                              "type": "datatable",
                              "actions": dt_row_actions("training", tablename),
                              "tablename": tablename,
                              "context": "person",
                              "create_controller": controller,
                              "create_function": "person",
                              "create_component": "training",
                              "pagesize": None, # all records
                              }
                    profile_widgets.append(widget)

            if settings.get_hrm_use_skills():
                tablename = "hrm_competency"
                r.customise_resource(tablename)
                widget = {# Use CRUD Strings (easier to customise)
                          #"label": label,
                          #"label_create": "Add Skill",
                          "type": "datatable",
                          "actions": dt_row_actions("competency", tablename),
                          "tablename": tablename,
                          "context": "person",
                          "create_controller": controller,
                          "create_function": "person",
                          "create_component": "competency",
                          "pagesize": None, # all records
                          }
                profile_widgets.append(widget)

            if settings.get_hrm_use_certificates():
                tablename = "hrm_certification"
                widget = {"label": "Certificates",
                          "label_create": "Add Certificate",
                          "type": "datatable",
                          "actions": dt_row_actions("certification", tablename),
                          "tablename": tablename,
                          "context": "person",
                          "create_controller": controller,
                          "create_function": "person",
                          "create_component": "certification",
                          "pagesize": None, # all records
                          }
                profile_widgets.append(widget)

            # Person isn't a doc_id
            #if settings.has_module("doc"):
            #    tablename = "doc_document"
            #    widget = {"label": "Documents",
            #              "label_create": "Add Document",
            #              "type": "datatable",
            #              "actions": dt_row_actions("document", tablename),
            #              "tablename": tablename,
            #              "filter": FS("doc_id") == record.doc_id,
            #              "icon": "attachment",
            #              "create_controller": controller,
            #              "create_function": "person",
            #              "create_component": "document",
            #              "pagesize": None, # all records
            #              }
            #    profile_widgets.append(widget)

            if r.representation == "html":
                response = current.response
                # Maintain normal rheader for consistency
                rheader = attr["rheader"]
                profile_header = TAG[""](H2(response.s3.crud_strings["pr_person"].title_display),
                                         DIV(rheader(r), _id="rheader"),
                                         )
            else:
                profile_header = None

            s3db.configure(tablename,
                           profile_cols = 1,
                           profile_header = profile_header,
                           profile_widgets = profile_widgets,
                           )

            profile = S3Profile()
            profile.tablename = tablename
            profile.request = r
            output = profile.profile(r, **attr)
            if r.representation == "html":
                output["title"] = response.title = T("CV")
            return output

        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class hrm_Record(S3Method):
    """
        HR Record, custom profile page with multiple DataTables:
            * Human Resource
            * Hours (for volunteers)
            * Teams
    """

    def __init__(self,
                 salary=False,
                 awards=False,
                 disciplinary_record=False,
                 org_experience=False,
                 other_experience=False):
        """
            Constructor

            @param salary: show a Salary widget
            @param awards: show an Awards History widget
            @param disciplinary_record: show a Disciplinary Record widget
            @param org_experience: show widget with Professional Experience
                                   within registered organisations, can be a
                                   dict with overrides for widget defaults
            @param other_experience: show widget with Other Experience, can
                                     be a dict with overrides for widget defaults
        """

        self.salary = salary
        self.awards = awards
        self.disciplinary_record = disciplinary_record
        self.org_experience = org_experience
        self.other_experience = other_experience

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name != "person" or not r.id or r.component:
            r.error(405, current.ERROR.BAD_METHOD)
        representation = r.representation
        if representation not in ("html", "aadata"):
            r.error(405, current.ERROR.BAD_METHOD)

        r.customise_resource("hrm_human_resource")

        T = current.T
        s3db = current.s3db
        response = current.response
        crud_strings = response.s3.crud_strings
        settings = current.deployment_settings

        tablename = r.tablename
        if r.controller == "vol":
            VOL = True
            controller = "vol"
        else:
            VOL = r.get_vars["group"] == "volunteer"
            controller = "hrm"

        # @ToDo: Check editable/deletable config if-necessary (see hrm_CV)
        def dt_row_actions(component):
            return lambda r, list_id: [
                {"label": T("Open"),
                 "url": r.url(component=component,
                              component_id="[id]",
                              method="update.popup",
                              vars={"refresh": list_id},
                              ),
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

        table = s3db.hrm_human_resource
        label = settings.get_hrm_record_label()
        code = table.code
        if VOL:
            widget_filter = FS("type") == 2
            if settings.get_hrm_use_code() is True:
                code.readable = code.writable = True
        #elif controller = "hrm":
        else:
            #widget_filter = FS("type") == 1
            widget_filter = None
            if settings.get_hrm_use_code():
                code.readable = code.writable = True

        profile_widgets = [
            {"label": label,
             "type": "form",
             "tablename": "hrm_human_resource",
             "context": "person",
             "filter": widget_filter,
             },
            ]

        if VOL:
            vol_experience = settings.get_hrm_vol_experience()
            if vol_experience in ("programme", "both"):
                tablename = "hrm_programme_hours"
                # Exclude records which are just to link to Programme
                filter_ = (FS("hours") != None)
                list_fields = ["id",
                               "date",
                               ]
                phtable = s3db.hrm_programme_hours
                r.customise_resource(tablename)
                if phtable.programme_id.readable:
                    list_fields.append("programme_id")
                    # Exclude Training Hours
                    filter_ &= (FS("programme_id") != None)
                if phtable.place.readable:
                    # RMSAmericas
                    list_fields += ["place",
                                    "event",
                                    ]
                if phtable.job_title_id.readable:
                    list_fields.append("job_title_id")
                list_fields.append("hours")
                crud_strings_ = crud_strings[tablename]
                hours_widget = {"label": crud_strings_["title_list"],
                                "label_create": crud_strings_["label_create"],
                                "type": "datatable",
                                "actions": dt_row_actions("hours"),
                                "tablename": tablename,
                                "context": "person",
                                "filter": filter_,
                                "list_fields": list_fields,
                                "create_controller": controller,
                                "create_function": "person",
                                "create_component": "hours",
                                "pagesize": None, # all records
                                }
                profile_widgets.append(hours_widget)
            elif vol_experience == "activity":
                # Exclude records which are just to link to Activity & also Training Hours
                #filter_ = (FS("hours") != None) & \
                #          (FS("activity_id") != None)
                list_fields = ["id",
                               "date",
                               "activity_id",
                               "job_title_id",
                               "hours",
                               ]
                #if s3db.vol_activity_hours.job_title_id.readable:
                #    list_fields.append("job_title_id")
                #list_fields.append("hours")
                hours_widget = {"label": "Activity Hours",
                                # Don't Add Hours here since the Activity List will be very hard to find the right one in
                                "insert": False,
                                #"label_create": "Add Activity Hours",
                                "type": "datatable",
                                "actions": dt_row_actions("hours"),
                                "tablename": "vol_activity_hours",
                                "context": "person",
                                #"filter": filter_,
                                "list_fields": list_fields,
                                #"create_controller": controller,
                                #"create_function": "person",
                                #"create_component": "activity_hours",
                                "pagesize": None, # all records
                                }
                profile_widgets.append(hours_widget)

        teams = settings.get_hrm_teams()
        if teams:
            hrm_configure_pr_group_membership()
            if teams == "Teams":
                label_create = "Add Team"
            elif teams == "Groups":
                label_create = "Add Group"
            teams_widget = {"label": teams,
                            "label_create": label_create,
                            "type": "datatable",
                            "actions": dt_row_actions("group_membership"),
                            "tablename": "pr_group_membership",
                            "context": "person",
                            "create_controller": controller,
                            "create_function": "person",
                            "create_component": "group_membership",
                            "pagesize": None, # all records
                            }
            profile_widgets.append(teams_widget)

        if controller == "hrm":

            org_experience = self.org_experience
            if org_experience:
                # Use primary hrm/experience controller
                # (=> defaults to staff-style experience form)

                # Need different action URLs
                def experience_row_actions(component):
                    return lambda r, list_id: [
                        {"label": T("Open"),
                        "url": URL(f="experience",
                                   args=["[id]", "update.popup"],
                                   vars={"refresh": list_id},
                                   ),
                        "_class": "action-btn edit s3_modal",
                        },
                        {"label": T("Delete"),
                        "_ajaxurl": URL(f="experience",
                                        args=["[id]", "delete.json"],
                                        ),
                        "_class": "action-btn delete-btn-ajax dt-ajax-delete",
                        },
                    ]

                # Configure widget, apply overrides
                widget = {"label": T("Experience"),
                          "label_create": T("Add Experience"),
                          "type": "datatable",
                          "actions": experience_row_actions("experience"),
                          "tablename": "hrm_experience",
                          "pagesize": None, # all records
                          }
                if isinstance(org_experience, dict):
                    widget.update(org_experience)

                # Retain the person filter
                person_filter = FS("person_id") == r.id
                widget_filter = widget.get("filter")
                if widget_filter:
                    widget["filter"] = person_filter & widget_filter
                else:
                    widget["filter"] = person_filter

                profile_widgets.append(widget)

            other_experience = self.other_experience
            if other_experience:
                # Use experience component in hrm/person controller
                # (=> defaults to vol-style experience form)

                # Configure widget and apply overrides
                widget = {"label": "Experience",
                          "label_create": "Add Experience",
                          "type": "datatable",
                          "actions": dt_row_actions("experience"),
                          "tablename": "hrm_experience",
                          "context": "person",
                          "create_controller": controller,
                          "create_function": "person",
                          "create_component": "experience",
                          "pagesize": None, # all records
                          }
                if isinstance(other_experience, dict):
                    widget.update(other_experience)

                profile_widgets.append(widget)

            if self.awards:
                widget = {"label": T("Awards"),
                          "label_create": T("Add Award"),
                          "type": "datatable",
                          "actions": dt_row_actions("staff_award"),
                          "tablename": "hrm_award",
                          "context": "person",
                          "create_controller": controller,
                          "create_function": "person",
                          "create_component": "staff_award",
                          "pagesize": None, # all records
                          }
                profile_widgets.append(widget)

            if self.disciplinary_record:
                widget = {"label": T("Disciplinary Record"),
                          "label_create": T("Add Disciplinary Action"),
                          "type": "datatable",
                          "actions": dt_row_actions("disciplinary_action"),
                          "tablename": "hrm_disciplinary_action",
                          "context": "person",
                          "create_controller": controller,
                          "create_function": "person",
                          "create_component": "disciplinary_action",
                          "pagesize": None, # all records
                          }
                profile_widgets.append(widget)

            if self.salary:
                widget = {"label": T("Salary"),
                          "label_create": T("Add Salary"),
                          "type": "datatable",
                          "actions": dt_row_actions("salary"),
                          "tablename": "hrm_salary",
                          "context": "person",
                          "create_controller": controller,
                          "create_function": "person",
                          "create_component": "salary",
                          "pagesize": None, # all records
                          }
                profile_widgets.append(widget)

        if representation == "html":
            # Maintain normal rheader for consistency
            title = crud_strings["pr_person"].title_display
            profile_header = TAG[""](H2(title),
                                     DIV(hrm_rheader(r),
                                     _id="rheader"))
        else:
            profile_header = None

        s3db.configure(tablename,
                       profile_cols = 1,
                       profile_header = profile_header,
                       profile_widgets = profile_widgets,
                       )

        profile = S3Profile()
        profile.tablename = tablename
        profile.request = r
        output = profile.profile(r, **attr)
        if representation == "html":
            output["title"] = response.title = title
        return output

# =============================================================================
def hrm_configure_salary(r):
    """
        Configure the salary tab

        @param r: the S3Request
    """

    hr_id = None
    multiple = False

    # Get all accessible HR records of this person
    resource = r.resource
    rows = resource.select(["human_resource.id",
                            "human_resource.type",
                            ], as_rows=True)

    # Only staff records, of course
    rows = [row for row in rows if row["hrm_human_resource.type"] == 1]

    HR_ID = "hrm_human_resource.id"
    if len(rows) == 1:
        hr_id = rows[0][HR_ID]
        multiple = False
    else:
        hr_id = [row[HR_ID] for row in rows]
        multiple = True

    component = r.component
    ctable = component.table

    field = ctable.human_resource_id
    list_fields = [fs for fs in component.list_fields() if fs != "person_id"]

    if multiple or not hr_id:
        # Default to the staff record selected in URL
        default_hr_id = hr_id
        if "human_resource.id" in r.get_vars:
            try:
                default_hr_id = long(r.get_vars["human_resource.id"])
            except ValueError:
                pass
        if default_hr_id in hr_id:
            field.default = default_hr_id

        # Filter field options
        field.requires = IS_ONE_OF(current.db, "hrm_human_resource.id",
                                   current.s3db.hrm_human_resource_represent,
                                   sort=True,
                                   filterby="id",
                                   filter_opts = hr_id,
                                   )
        # Show the list_field
        if "human_resource_id" not in list_fields:
            list_fields.insert(1, "human_resource_id")
    else:
        # Only one HR record => set as default and make read-only
        field.default = hr_id
        field.writable = False

        # Hiding the field can be confusing if there are mixed single/multi HR
        #field.readable = False

        # Hide the list field
        if "human_resource_id" in list_fields:
            list_fields.remove("human_resource_id")

    component.configure(list_fields=list_fields)

# =============================================================================
def hrm_configure_pr_group_membership():
    """
        Configures the labels and CRUD Strings of pr_group_membership
    """

    T = current.T
    s3db = current.s3db
    settings = current.deployment_settings
    request = current.request
    function = request.function
    tablename = "pr_group_membership"

    table = s3db.pr_group_membership
    if settings.get_hrm_teams() == "Teams":
        table.group_id.label = T("Team Name")
        table.group_head.label = T("Team Leader")

        if function == "person":
            ADD_MEMBERSHIP = T("Add Membership")
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = ADD_MEMBERSHIP,
                title_display = T("Membership Details"),
                title_list = T("Memberships"),
                title_update = T("Edit Membership"),
                label_list_button = T("List Memberships"),
                label_delete_button = T("Delete Membership"),
                msg_record_created = T("Added to Team"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Removed from Team"),
                msg_list_empty = T("Not yet a Member of any Team"))

        elif function in ("group", "group_membership"):
            ADD_MEMBER = T("Add Team Member")
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = ADD_MEMBER,
                title_display = T("Membership Details"),
                title_list = T("Team Members"),
                title_update = T("Edit Membership"),
                label_list_button = T("List Members"),
                label_delete_button = T("Remove Person from Team"),
                msg_record_created = T("Person added to Team"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Person removed from Team"),
                msg_list_empty = T("This Team has no Members yet"))
    else:
        table.group_head.label = T("Group Leader")

    if function in ("group", "group_membership"):
        # Don't create Persons here as they need to be HRMs
        table.person_id.comment = None
        phone_label = settings.get_ui_label_mobile_phone()
        site_label = settings.get_org_site_label()
        list_fields = ["id",
                       "person_id",
                       "group_head",
                       (T("Email"), "person_id$email.value"),
                       (phone_label, "person_id$phone.value"),
                       (current.messages.ORGANISATION,
                       "person_id$human_resource.organisation_id"),
                       (site_label, "person_id$human_resource.site_id"),
                       ]
        name_format = settings.get_pr_name_format()
        test = name_format % {"first_name": 1,
                              "middle_name": 2,
                              "last_name": 3,
                              }
        test = "".join(ch for ch in test if ch in ("1", "2", "3"))
        if test[:1] == "1":
            orderby = "pr_person.first_name"
        elif test[:1] == "2":
            orderby = "pr_person.middle_name"
        else:
            orderby = "pr_person.last_name"
    else:
        # Person
        list_fields = ["id",
                       "group_id",
                       "group_head",
                       "group_id$description",
                       ]
        orderby = table.group_id

    s3db.configure(tablename,
                   list_fields = list_fields,
                   orderby = orderby,
                   )

# =============================================================================
def hrm_competency_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Skills on the HRM Profile

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["hrm_competency.id"]
    item_class = "thumbnail"

    raw = record._row
    title = record["hrm_competency.skill_id"]
    organisation = raw["hrm_competency.organisation_id"] or ""
    if organisation:
        #org_url = URL(c="org", f="organisation", args=[organisation, "profile"])
        org_url = URL(c="org", f="organisation", args=[organisation])
        organisation = P(ICON("organisation"),
                         " ",
                         SPAN(A(record["hrm_competency.organisation_id"],
                                _href=org_url)
                              ),
                         " ",
                         _class="card_1_line",
                         )
    competency = raw["hrm_competency.competency_id"] or ""
    if competency:
        competency = P(ICON("certificate"),
                       " ",
                       SPAN(record["hrm_competency.competency_id"]),
                       " ",
                       _class="card_1_line",
                       )
    comments = raw["hrm_competency.comments"] or ""

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.s3db.hrm_competency
    if permit("update", table, record_id=record_id):
        controller = current.request.controller
        if controller not in ("vol", "deploy"):
            controller = "hrm"
        edit_btn = A(ICON("edit"),
                     _href=URL(c=controller, f="competency",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.T("Edit Skill"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(ICON("icon"),
                   SPAN(" %s" % title,
                        _class="card-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(DIV(organisation,
                           competency,
                           P(SPAN(comments),
                             " ",
                             _class="card_manylines",
                             ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def hrm_credential_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Credentials on the HRM Profile

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["hrm_credential.id"]
    item_class = "thumbnail"

    raw = record["_row"]

    start_date = raw["hrm_credential.start_date"]
    end_date = raw["hrm_credential.end_date"]
    if start_date or end_date:
        if start_date and end_date:
            dates = "%s - %s" % (record["hrm_credential.start_date"],
                                 record["hrm_credential.end_date"],
                                 )
        elif start_date:
            dates = "%s - " % record["hrm_credential.start_date"]
        else:
            dates = " - %s" % record["hrm_credential.end_date"]
        date = P(ICON("calendar"),
                 " ",
                 SPAN(dates),
                 " ",
                 _class="card_1_line",
                 )
    else:
        date = ""

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.s3db.hrm_credential
    if permit("update", table, record_id=record_id):
        controller = current.request.controller
        if controller not in ("vol", "deploy"):
            controller = "hrm"
        edit_btn = A(ICON("edit"),
                     _href=URL(c=controller, f="credential",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings["hrm_credential"].title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(ICON("icon"),
                   SPAN(" %s" % record["hrm_credential.job_title_id"],
                        _class="card-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(DIV(date,
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def hrm_experience_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Experience on the HRM Profile

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["hrm_experience.id"]
    item_class = "thumbnail"

    raw = record._row

    card_line = lambda icon, item: P(ICON(icon),
                                     SPAN(item),
                                     _class="card_1_line",
                                     )

    # Organisation
    colname = "hrm_experience.organisation_id"
    organisation_id = raw[colname]
    if organisation_id:
        org_url = URL(c="org", f="organisation", args=[organisation_id])
        organisation = A(record[colname], _href=org_url)
    else:
        # Try free-text field
        organisation = raw["hrm_experience.organisation"]
    if organisation:
        organisation = card_line("organisation", organisation)
    else:
        organisation = ""

    # Activity Type
    colname = "hrm_experience.activity_type"
    activity_type = raw[colname]
    if activity_type:
        activity_type = card_line("activity", record[colname])
    else:
        activity_type = ""

    # Key Responsibilities
    colname = "hrm_experience.responsibilities"
    responsibilities = raw[colname]
    if responsibilities:
        responsibilities = card_line("responsibility", record[colname])
    else:
        responsibilities = ""

    # Location
    colname = "hrm_experience.location_id"
    location_id = raw[colname]
    if location_id:
        #location_url = URL(c="gis", f="location", args=[location_id, "profile"])
        location_url = URL(c="gis", f="location", args=[location_id])
        location = card_line("location",
                             A(record[colname], _href=location_url))
    else:
        location = ""

    # Hours
    hours = raw["hrm_experience.hours"]
    if hours:
        hours = card_line("time", hours)
    else:
        hours = ""

    # Start and End Dates
    colname_start = "hrm_experience.start_date"
    colname_end = "hrm_experience.end_date"
    start_date = raw[colname_start]
    end_date = raw[colname_end]
    if start_date or end_date:
        if start_date and end_date:
            dates = "%s - %s" % (record[colname_start],
                                 record[colname_end],
                                 )
        elif start_date:
            dates = "%s - " % record[colname_start]
        else:
            dates = " - %s" % record[colname_end]
        date = card_line("calendar", dates)
    else:
        date = ""

    # Supervisor
    colname = "hrm_experience.supervisor_id"
    supervisor_id = raw[colname]
    if supervisor_id:
        #person_url = URL(c="hrm", f="person", args=[supervisor_id, "profile"])
        person_url = URL(c="hrm", f="person", args=[supervisor_id])
        supervisor = card_line("user",
                               A(record[colname], _href=person_url))
    else:
        supervisor = ""

    # Comments
    comments = raw["hrm_experience.comments"] or ""

    # Job title as card title, indicate employment type if given
    colname = "hrm_experience.job_title_id"
    if raw[colname]:
        title = record[colname]
        job_title = card_line("star", title)
    else:
        title = ""
        job_title = ""
    position = raw["hrm_experience.job_title"]
    if position:
        title = position
    else:
        job_title = ""
    colname = "hrm_experience.employment_type"
    if raw[colname]:
        employment_type = record[colname]
        if title:
            title = "%s (%s)" % (title, employment_type)
        else:
            title = employment_type

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.s3db.hrm_experience
    if permit("update", table, record_id=record_id):
        controller = current.request.controller
        if controller not in ("vol", "deploy"):
            controller = "hrm"
        edit_btn = A(ICON("edit"),
                     _href=URL(c=controller, f="experience",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.T("Edit Experience"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(ICON("icon"),
                   SPAN(title, _class="card-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(DIV(organisation,
                           location,
                           date,
                           hours,
                           supervisor,
                           activity_type,
                           job_title,
                           responsibilities,
                           P(SPAN(comments),
                             " ",
                             _class="card_manylines",
                             ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def hrm_training_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Trainings on the HRM Profile

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["hrm_training.id"]
    item_class = "thumbnail"

    raw = record._row
    title = record["hrm_training.course_id"]

    date = raw["hrm_training.date"] or ""
    if date:
        date = P(ICON("calendar"),
                 " ",
                 SPAN(record["hrm_training.date"]),
                 " ",
                 _class="card_1_line",
                 )

    grade = raw["hrm_training.grade"] or ""
    if grade:
        grade = P(ICON("certificate"),
                  " ",
                  SPAN(record["hrm_training.grade"]),
                  " ",
                  _class="card_1_line",
                  )

    hours = raw["hrm_training.hours"] or ""
    if hours:
        hours = P(ICON("time"),
                  " ",
                  SPAN(hours),
                  " ",
                  _class="card_1_line",
                  )

    site = raw["hrm_training_event.site_id"] or ""
    if site:
        #site_id = raw["hrm_training_event.site_id"]
        #site_url = URL(c="org", f="site", args=[site_id, "profile"])
        site_url = "#"
        site = P(ICON("site"),
                 " ",
                 SPAN(A(record["hrm_training_event.site_id"],
                        _href=site_url)
                      ),
                 " ",
                 _class="card_1_line",
                 )

    job_title = raw["hrm_course_job_title.job_title_id"] or ""
    if job_title:
        job_title = P(ICON("star"),
                      " ",
                      SPAN(record["hrm_course_job_title.job_title_id"],
                           ),
                      " ",
                      _class="card_1_line",
                      )
    else:
        job_title = ""

    comments = raw["hrm_training.comments"] or ""

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.s3db.hrm_training
    if permit("update", table, record_id=record_id):
        controller = current.request.controller
        if controller not in ("vol", "deploy"):
            controller = "hrm"
        edit_btn = A(ICON("edit"),
                     _href=URL(c=controller, f="training",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.T("Edit Training"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(ICON("icon"),
                   SPAN(" %s" % title,
                        _class="card-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(DIV(job_title,
                           site,
                           date,
                           hours,
                           grade,
                           P(SPAN(comments),
                             " ",
                             _class="card_manylines",
                             ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def hrm_human_resource_filters(resource_type = None,
                               module = None,
                               hrm_type_opts = None):
    """
        Get filter widgets for human resources

        @param resource_type: the HR type (staff/volunteer/both) if
                              pre-determined, otherwise None to render a
                              filter widget
        @param module: the controller prefix of the request to render
                       module-specific widgets, defaults to
                       current.request.controller
    """

    T = current.T
    settings = current.deployment_settings

    if not module:
        module = current.request.controller

    text_search_fields = ["person_id$first_name",
                          "person_id$middle_name",
                          "person_id$last_name",
                          "person_id$email.value",
                          #"organisation_id",
                          ]

    use_code = settings.get_hrm_use_code()
    if use_code is True or use_code and resource_type != "volunteer":
        text_search_fields.append("code")

    if settings.get_hrm_use_national_id():
        text_search_fields.append("person_id$national_id.value")

    filter_widgets = [S3TextFilter(text_search_fields,
                                   label = T("Search"),
                                   ),
                      ]
    append_filter = filter_widgets.append

    if module == "deploy" and current.auth.s3_has_role("ADMIN"):
        dotable = current.s3db.deploy_organisation
        deploying_orgs = current.db(dotable.deleted == False).count()
        if deploying_orgs > 1:
            append_filter(S3OptionsFilter("application.organisation_id",
                                          label = T("Deployment Team"),
                                          ))

    # Type filter (only if not pre-filtered)
    if not resource_type in ("staff", "volunteer"):
        append_filter(S3OptionsFilter("type",
                                      label = T("Type"),
                                      options = hrm_type_opts,
                                      cols = 2,
                                      hidden = True,
                                      ))

    # Region filter (only if using regions in template)
    if settings.get_org_regions():
        if settings.get_org_regions_hierarchical():
            if module == "deploy":
                hidden = False
            else:
                hidden = True
            append_filter(S3HierarchyFilter("organisation_id$region_id",
                                            label = T("Region"),
                                            hidden = hidden,
                                            ))
        else:
            append_filter(S3OptionsFilter("organisation_id$region_id",
                                          label = T("Region"),
                                          hidden = True,
                                          ))

    # Organisation filter
    if settings.get_hrm_multiple_orgs():
        if settings.get_org_branches():
            append_filter(S3HierarchyFilter("organisation_id",
                                            leafonly = False,
                                            ))
        else:
            append_filter(S3OptionsFilter("organisation_id",
                                          search = True,
                                          header = "",
                                          #hidden = True,
                                          ))

    # Location filter (always)
    append_filter(S3LocationFilter("location_id",
                                   label = T("Location"),
                                   hidden = True,
                                   ))

    # Active / Activity / Programme filters (volunteer only)
    if module == "vol" or resource_type in ("both", "volunteer"):
        vol_active = settings.get_hrm_vol_active()
        if vol_active:
            # Active filter
            append_filter(S3OptionsFilter("details.active",
                                          label = T("Active?"),
                                          cols = 2, #3,
                                          options = {True: T("Yes"),
                                                     False: T("No"),
                                                     #None: T("Unknown"),
                                                     },
                                          hidden = True,
                                          #none = True,
                                          ))
        vol_experience = settings.get_hrm_vol_experience()
        if vol_experience in ("programme", "both"):
            # Programme filter
            append_filter(S3OptionsFilter("person_id$hours.programme_id",
                                          label = T("Program"),
                                          #options = lambda: \
                                          #  s3_get_filter_opts("hrm_programme",
                                          #                     org_filter=True),
                                          hidden = True,
                                          ))
        elif vol_experience == "activity":
            # Programme filter
            append_filter(S3OptionsFilter("person_id$activity_hours.activity_hours_activity_type.activity_type_id",
                                          label = T("Activity Types"),
                                          hidden = True,
                                          ))

        if settings.get_hrm_unavailability():
            # Availability Filter
            append_filter(S3DateFilter("available",
                                       label = T("Available"),
                                       # Use custom selector to prevent automatic
                                       # parsing (which would result in an error)
                                       selector = "available",
                                       hide_time = False,
                                       hidden = True,
                                       ))

    else:
        # Site filter (staff only)
        filter_widgets.append(S3OptionsFilter("site_id",
                                              hidden = True,
                                              ))

    if module == "deploy":
        # Deployment-specific filters

        # Availability Filter
        append_filter(S3DateFilter("available",
                                   label = T("Available for Deployment"),
                                   # Use custom selector to prevent automatic
                                   # parsing (which would result in an error)
                                   selector = "available",
                                   hide_time = True,
                                   hidden = True,
                                   ))

        # Job title filter
        append_filter(S3OptionsFilter("credential.job_title_id",
                                      # @ToDo: deployment_setting for label (this is RDRT-specific)
                                      #label = T("Credential"),
                                      label = T("Sector"),
                                      hidden = True,
                                      ))

        # Last-deployment-date filter
        append_filter(S3DateFilter("human_resource_id:deploy_assignment.start_date",
                                   label = T("Deployed"),
                                   hide_time = True,
                                   hidden = True,
                                   ))

        # Last-response-date filter
        append_filter(S3DateFilter("human_resource_id:deploy_response.created_on",
                                   label = T("Responded"),
                                   hide_time = True,
                                   hidden = True,
                                   ))

    # Certificate filter
    if settings.get_hrm_use_certificates():
        append_filter(S3OptionsFilter("certification.certificate_id",
                                      # Better to default (easier to customise/consistency)
                                      #label = T("Certificate"),
                                      hidden = True,
                                      ))

    # Skills filter
    if settings.get_hrm_use_skills():
        append_filter(S3OptionsFilter("competency.skill_id",
                                      # Better to default (easier to customise/consistency)
                                      #label = T("Skill"),
                                      hidden = module != "req",
                                      ))

    # Training filter
    if settings.get_hrm_use_trainings():
        if settings.get_hrm_training_filter_and():
            append_filter(S3OptionsFilter("trainings.course_id",
                                          label = T("Training"),
                                          hidden = True,
                                          operator = "contains",
                                          ))
        else:
            append_filter(S3OptionsFilter("training.course_id",
                                          label = T("Training"),
                                          hidden = True,
                                          ))

    # Group (team) membership filter
    teams = settings.get_hrm_teams()
    if teams:
        if teams == "Teams":
            teams = "Team"
        elif teams == "Groups":
            teams = "Group"
        append_filter(S3OptionsFilter("group_membership.group_id",
                                      label = T(teams),
                                      hidden = True,
                                      ))

    return filter_widgets

# END =========================================================================
