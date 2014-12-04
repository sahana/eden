# -*- coding: utf-8 -*-

""" Sahana Eden Human Resources Management

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

__all__ = ("S3HRModel",
           "S3HRSiteModel",
           "S3HRSalaryModel",
           "S3HRInsuranceModel",
           "S3HRContractModel",
           "S3HRSkillModel",
           "S3HRAppraisalModel",
           "S3HRExperienceModel",
           "S3HRAwardModel",
           "S3HRDisciplinaryActionModel",
           "S3HRProgrammeModel",
           "hrm_AssignMethod",
           "hrm_HumanResourceRepresent",
           #"hrm_TrainingEventRepresent",
           #"hrm_position_represent",
           "hrm_vars",
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
from s3layouts import S3AddResourceLink

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
        ORGANISATION = messages.ORGANISATION

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

        request = current.request
        controller = request.controller
        group = request.get_vars.get("group", None)
        if not group:
            if controller == "vol":
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
            comment = S3AddResourceLink(c="vol" if group == "volunteer" else "hrm",
                                        f="department",
                                        label=label_create),
            )

        configure("hrm_department",
                  deduplicate = self.hrm_department_duplicate,
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

        if settings.has_module("deploy"):
            hrm_types = True
            hrm_type_opts[4] = T("Deployment")

        if group == "volunteer":
            not_filter_opts = (1, 4)
            code_label = T("Volunteer ID")
        else:
            # Staff
            not_filter_opts = (2, 4)
            code_label = T("Staff ID")

        org_dependent_job_titles = settings.get_hrm_org_dependent_job_titles()

        tablename = "hrm_job_title"
        define_table(tablename,
                     Field("name", notnull=True,
                           length=64,    # Mayon compatibility
                           label=T("Name")),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     organisation_id(default = root_org if org_dependent_job_titles else None,
                                     readable = is_admin if org_dependent_job_titles else False,
                                     writable = is_admin if org_dependent_job_titles else False,
                                     ),
                     Field("type", "integer",
                           default = hrm_type_default,
                           readable = hrm_types,
                           writable = hrm_types,
                           requires = IS_IN_SET(hrm_type_opts),
                           represent = lambda opt: \
                           hrm_type_opts.get(opt, UNKNOWN_OPT),
                           label=T("Type"),
                           ),
                     s3_comments(label=T("Description"),
                                 comment=None),
                     *s3_meta_fields())

        if group == "volunteer":
            label = T("Volunteer Role")
            label_create = T("Add Volunteer Role")
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

        if  org_dependent_job_titles:
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
            comment = S3AddResourceLink(c="vol" if group == "volunteer" else "hrm",
                                        f="job_title",
                                        label=label_create,
                                        title=label,
                                        tooltip=tooltip),
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

        hrm_status_opts = {1: T("current"),
                           2: T("obsolete"),
                           }

        organisation_label = settings.get_hrm_organisation_label()

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
                        ondelete = "CASCADE",
                        requires = IS_ADD_PERSON_WIDGET2(),
                        widget = S3AddPersonWidget2(controller="hrm"),
                     ),
                     Field("type", "integer",
                           default = 1,
                           #label = T("Type"),
                           represent = lambda opt: \
                                       hrm_type_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(hrm_type_opts,
                                                zero=None),
                           # Always set via the Controller we create from
                           readable = False,
                           writable = False,
                           ),
                     Field("code",
                           label = code_label,
                           represent = lambda v: v or messages["NONE"],
                           ),
                     job_title_id(),
                     department_id(),
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
                             ),
                     s3_date("end_date",
                             label = T("End Date"),
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
                     Field("site_contact", "boolean",
                           label = T("Facility Contact"),
                           represent = lambda opt: \
                            (T("No"), T("Yes"))[opt == True],
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
                    label_create = T("Create Staff Member"),
                    title_display = T("Staff Member Details"),
                    title_list = T("Staff & Volunteers"),
                    title_update = T("Edit Record"),
                    title_upload =T("Search Staff & Volunteers"),
                    label_list_button = T("List Staff & Volunteers"),
                    label_delete_button = T("Delete Record"),
                    msg_record_created = T("Staff member added"),
                    msg_record_modified = T("Record updated"),
                    msg_record_deleted = T("Record deleted"),
                    msg_list_empty = T("No staff or volunteers currently registered"))

        tooltip = DIV(_class="tooltip",
                      _title="%s|%s" % (T("Human Resource"),
                                        AUTOCOMPLETE_HELP))
        comment = S3AddResourceLink(c = "vol" if group == "volunteer" else "hrm",
                                    f = group or "staff",
                                    vars = dict(child="human_resource_id"),
                                    label=crud_strings["hrm_%s" % group].label_create if group else \
                                          crud_strings[tablename].label_create,
                                    title=label,
                                    tooltip=tooltip)

        human_resource_id = S3ReusableField("human_resource_id", "reference %s" % tablename,
                                            label = label,
                                            ondelete = "RESTRICT",
                                            represent = hrm_human_resource_represent,
                                            requires = requires,
                                            sortby = ["type", "status"],
                                            widget = widget,
                                            comment = comment,
                                            )

        # Custom Method for S3HumanResourceAutocompleteWidget and S3AddPersonWidget2
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
                        # Skills
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
                        hrm_credential = {"link": "pr_person",
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
                        hrm_salary = "human_resource_id",
                        hrm_insurance = "human_resource_id",
                        hrm_contract = {"joinby": "human_resource_id",
                                        "multiple": False,
                                        },
                        hrm_training = {"link": "pr_person",
                                        "joinby": "id",
                                        "key": "id",
                                        "fkey": "person_id",
                                        "pkey": "person_id",
                                        },
                        # Organisation Groups
                        org_group_person = {"link": "pr_person",
                                            "joinby": "id",
                                            "key": "id",
                                            "fkey": "person_id",
                                            "pkey": "person_id",
                                            },
                        # Application for Deployment (RDRT)
                        deploy_application = "human_resource_id",
                        # Availability
                        #hrm_availability = "human_resource_id",
                        # Hours
                        #hrm_hours = "human_resource_id",
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

        if group == "volunteer":
            add_components(tablename,
                           # Programmes
                           hrm_programme_hours = {"link": "pr_person",
                                                  "joinby": "id",
                                                  "key": "id",
                                                  "fkey": "person_id",
                                                  "pkey": "person_id",
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
                       "job_title_id",
                       "start_date",
                       "end_date",
                       "status",
                       ]

        filter_widgets = hrm_human_resource_filters(resource_type=group,
                                                    hrm_type_opts=hrm_type_opts)

        report_fields = ["organisation_id",
                         "person_id",
                         "person_id$gender",
                         "job_title_id",
                         (T("Training"), "training.course_id"),
                         "location_id$L1",
                         "location_id$L2",
                         ]
        if teams:
            report_fields.append((T(teams), "group_membership.group_id"))

        if settings.get_hrm_use_code():
            crud_fields.append("code")

        if group == "volunteer":
            # This gets copied to hrm_human_resource.location_id onaccept, faster to lookup without joins
            #location_context = "person_id$address.location_id" # When not using S3Track()
            crud_fields.extend(("details.availability",
                                "details.card",
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
            crud_fields.insert(4, "department_id")
            report_fields.extend(("site_id",
                                  "department_id",
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
        crud_form = S3SQLCustomForm(*crud_fields)

        if settings.get_hrm_org_required():
            mark_required = ("organisation_id",)
        else:
            mark_required = None

        configure(tablename,
                  context = {#"location": location_context,
                             "organisation": "organisation_id",
                             "person": "person_id",
                             "site": "site_id",
                             },
                  create_next = hrm_url,
                  crud_form = crud_form,
                  deduplicate = self.hrm_human_resource_duplicate,
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
        return dict(hrm_department_id = department_id,
                    hrm_job_title_id = job_title_id,
                    hrm_human_resource_id = human_resource_id,
                    hrm_type_opts = hrm_type_opts,
                    hrm_human_resource_represent = hrm_human_resource_represent,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(hrm_department_id = lambda **attr: dummy("department_id"),
                    hrm_job_title_id = lambda **attr: dummy("job_title_id"),
                    hrm_human_resource_id = lambda **attr: dummy("human_resource_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_department_duplicate(item):
        """
            Update detection for hrm_department

            @param item: the S3ImportItem
        """

        data = item.data
        name = data.get("name", None)
        org = data.get("organisation_id", None)

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
        query = (table.name.lower() == name.lower())
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

        vars = form.vars

        if vars.main:
            # Read the record
            # (safer than relying on vars which might be missing on component tabs)
            db = current.db
            ltable = db.hrm_job_title_human_resource
            record = db(ltable.id == vars.id).select(ltable.human_resource_id,
                                                     ltable.job_title_id,
                                                     limitby=(0, 1)
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
            JSON search method for S3HumanResourceAutocompleteWidget and S3AddPersonWidget2
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
            output = current.xml.json_message(False, 400, "No value provided!")
            raise HTTP(400, body=output)

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = value.lower()

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
            output = json.dumps([
                dict(label=str(current.T("There are more than %(max)s results, please input more characters.") % dict(max=MAX_SEARCH_RESULTS)))
                ], separators=SEPARATORS)
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
            test = name_format % dict(first_name=1,
                                      middle_name=2,
                                      last_name=3,
                                      )
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

            items = []
            iappend = items.append
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
            output = json.dumps(items, separators=SEPARATORS)

        response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_lookup(r, **attr):
        """
            JSON lookup method for S3AddPersonWidget2
        """

        id = r.id
        if not id:
            output = current.xml.json_message(False, 400, "No id provided!")
            raise HTTP(400, body=output)

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

        left = None
        if request_dob:
            fields.append(ptable.date_of_birth)
        if request_gender:
            fields.append(ptable.gender)
        if current.request.controller == "vol":
            dtable = s3db.pr_person_details
            fields.append(dtable.occupation)
            left = dtable.on(dtable.person_id == ptable.id)

        query = (htable.id == id) & \
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

        if row and "id" in row:
            record = db(htable.id == row.id).select(htable.deleted,
                                                    htable.deleted_fk,
                                                    htable.person_id,
                                                    limitby=(0, 1)
                                                    ).first()
        else:
            return

        if record.deleted:
            try:
                fk = json.loads(record.deleted_fk)
                person_id = fk.get("person_id", None)
            except:
                return

            if person_id:
                current.s3db.pr_update_affiliations(htable, record)

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_duplicate(item):
        """
            HR record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        data = item.data
        person_id = data.get("person_id")
        if not person_id:
            return

        # This allows only one HR record per person and organisation,
        # if multiple HR records of the same person with the same org
        # are desired, then this needs an additional criteria in the
        # query (e.g. job title, or type):

        table = item.table
        query = (table.deleted != True) & \
                (table.person_id == person_id)
        org = data.get("organisation_id")
        if org:
            query = query & (table.organisation_id == org)
        row = current.db(query).select(table.id,
                                       limitby=(0, 1)).first()
        if row:
            item.id = row.id
            item.method = item.METHOD.UPDATE

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
                          self.org_site_id,
                          self.org_sector_id(),
                          Field("site_contact", "boolean",
                                label = T("Facility Contact"),
                                represent = lambda opt: \
                                            (T("No"), T("Yes"))[opt == True],
                                ),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = self.hrm_human_resource_site_duplicate,
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
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_human_resource_site_onaccept(form):
        """
            Update the Human Resource record with the site_id
        """

        # Deletion and update have a different format
        try:
            form_vars = form.vars
        except:
            _id = form.id
            delete = True
        else:
            _id = form_vars.id
            delete = False

        # Get the full record
        db = current.db
        ltable = db.hrm_human_resource_site
        table = db.hrm_human_resource
        if delete:
            record = db(ltable.id == _id).select(ltable.deleted_fk,
                                                 limitby=(0, 1)).first()

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

        data = item.data
        human_resource_id = data.get("human_resource_id")
        if not human_resource_id:
            return

        table = item.table
        query = (table.human_resource_id == human_resource_id)
        sector_id = data.get("sector_id")
        if sector_id:
            query &= (table.sector_id == sector_id)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

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
        table = define_table(tablename,
                             organisation_id(
                                requires = organisation_requires(updateable=True),
                             ),
                             Field("name",
                                   label = T("Staff Level"),
                             ),
                             *s3_meta_fields())

        configure(tablename,
                  deduplicate = self.staff_level_duplicate,
                  )

        ADD_STAFF_LEVEL = T("Add Staff Level")
        staff_level_represent = hrm_OrgSpecificTypeRepresent(lookup="hrm_staff_level")

        # =====================================================================
        # Salary Grades
        #
        tablename = "hrm_salary_grade"
        table = define_table(tablename,
                             organisation_id(
                                requires = organisation_requires(updateable=True),
                             ),
                             Field("name",
                                   label = T("Salary Grade"),
                             ),
                             *s3_meta_fields())

        configure(tablename,
                  deduplicate = self.salary_grade_duplicate,
                  )

        ADD_SALARY_GRADE = T("Add Salary Grade")
        salary_grade_represent = hrm_OrgSpecificTypeRepresent(lookup="hrm_salary_grade")

        # =====================================================================
        # Salary
        #
        tablename = "hrm_salary"
        table = define_table(tablename,
                             self.pr_person_id(),
                             self.hrm_human_resource_id(
                                label = T("Staff Record"),
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
                                   comment = S3AddResourceLink(f = "staff_level",
                                                               label = ADD_STAFF_LEVEL),
                                   ),
                             Field("salary_grade_id", "reference hrm_salary_grade",
                                   label = T("Salary Grade"),
                                   represent = salary_grade_represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db,
                                                          "hrm_salary_grade.id",
                                                          salary_grade_represent,
                                                          )),
                                   comment = S3AddResourceLink(f = "salary_grade",
                                                               label = ADD_SALARY_GRADE),
                                   ),
                             s3_date("start_date",
                                     default = "now",
                                     label = T("Start Date"),
                                     widget = S3DateTimeWidget(hide_time=True,
                                                               set_min="hrm_salary_end_date",
                                                               ),
                                     ),
                             s3_date("end_date",
                                     label = T("End Date"),
                                     widget = S3DateTimeWidget(hide_time=True,
                                                               set_max="hrm_salary_start_date",
                                                               ),
                                     ),
                             Field("monthly_amount", "double",
                                   requires = IS_EMPTY_OR(
                                              IS_FLOAT_IN_RANGE(minimum=0.0)),
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
    def defaults(self):

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

    # -------------------------------------------------------------------------
    @staticmethod
    def staff_level_duplicate(item):
        """ Callback to identify the original of an update import item """

        data = item.data
        organisation_id = data.organisation_id
        name = data.name

        if organisation_id and name:

            table = item.table
            query = (table.organisation_id == organisation_id) & \
                    (table.name == name)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def salary_grade_duplicate(item):
        """ Callback to identify the original of an update import item """

        data = item.data
        organisation_id = data.organisation_id
        name = data.name

        if organisation_id and name:

            table = item.table
            query = (table.organisation_id == organisation_id) & \
                    (table.name == name)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
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
    def lookup_rows(self, key, values, fields=[]):
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
                                        left = left)
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
        table = self.define_table(tablename,
                                  self.hrm_human_resource_id(),
                                  Field("type",
                                        requires = IS_IN_SET(insurance_types),
                                        represent = insurance_type_represent,
                                        ),
                                  Field("insurance_number",
                                        length = 128,
                                        ),
                                  Field("insurer",
                                        length = 255,
                                        ),
                                  Field("provider",
                                        length = 255,
                                        ),
                                  s3_comments(),
                                  *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = self.insurance_duplicate,
                       )

        return {}

    # -------------------------------------------------------------------------
    def defaults(self):

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def insurance_duplicate(item):
        """ Callback to identify the original of an update import item """

        data = item.data
        human_resource_id = data.human_resource_id
        insurance_type = data.type

        if human_resource_id and insurance_type:

            table = item.table
            query = (table.human_resource_id == human_resource_id) & \
                    (table.type == insurance_type)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3HRContractModel(S3Model):
    """ Data model to track employment contract details of staff members """

    names = ("hrm_contract",
             )

    def model(self):

        T = current.T

        contract_terms = {"SHORT": T("short-term"),
                          "LONG": T("long-term"),
                          "PERMANENT": T("permanent")
                          }
        contract_term_represent = S3Represent(options = contract_terms)

        hours_models = {"PARTTIME": T("part-time"),
                        "FULLTIME": T("full-time"),
                        }
        hours_model_represent = S3Represent(options = hours_models)

        # =====================================================================
        # Employment Contract Details
        #
        tablename = "hrm_contract"
        table = self.define_table(tablename,
                                  self.hrm_human_resource_id(),
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
                       deduplicate = self.contract_duplicate,
                       )

        return {}

    # -------------------------------------------------------------------------
    def defaults(self):

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def contract_duplicate(item):
        """ Callback to identify the original of an update import item """

        data = item.data
        human_resource_id = data.human_resource_id

        if human_resource_id:

            table = item.table
            query = (table.human_resource_id == human_resource_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3HRJobModel(S3Model):
    """
        Unused
    """

    names = ("hrm_position",
             "hrm_position_id",
             )

    def model(self):

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
                                      represent = hrm_position_represent,
                                      requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                       "hrm_position.id",
                                                                       hrm_position_represent)),
                                      sortby = "name",
                                      #comment = DIV(A(label_create,
                                      #                _class="s3_add_resource_link",
                                      #                _href=URL(f="position",
                                      #                          args="create",
                                      #                          vars=dict(format="popup")),
                                      #                _target="top",
                                      #                _title=label_create),
                                      #              DIV(_class="tooltip",
                                      #                  _title="%s|%s" % (label_create,
                                      #                                    T("Add a new job role to the catalog.")))),
                                      )

        # =========================================================================
        # Availability
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
        table = define_table(tablename,
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
                                               #requires=IS_ONE_OF(db, "gis_location.id",
                                                                  #gis_LocationRepresent(),
                                                                  #filterby="level",
                                                                  ## @ToDo Should this change per config?
                                                                  #filter_opts=gis.region_level_keys,
                                                                  #orderby="gis_location.name"),
                                               #widget=None),
                                   *s3_meta_fields())

        # =========================================================================
        # Hours registration
        #
        tablename = "hrm_hours"
        table = define_table(tablename,
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
        table = define_table(tablename,
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
        return dict(hrm_position_id = position_id,
                    )

# =============================================================================
class S3HRSkillModel(S3Model):

    names = ("hrm_skill_type",
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
        s3 = current.response.s3
        settings = current.deployment_settings

        job_title_id = self.hrm_job_title_id
        organisation_id = self.org_organisation_id
        person_id = self.pr_person_id

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        AUTOCOMPLETE_HELP = messages.AUTOCOMPLETE_HELP

        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)

        s3_string_represent = lambda s: s if s else NONE

        # Shortcuts
        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table

        root_org = auth.root_org()
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        group = request.get_vars.get("group", None)

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
                     Field("name", notnull=True, unique=True,
                           length=64,
                           label = T("Name"),
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
            comment=S3AddResourceLink(f="skill_type",
                                      label=label_create,
                                      title=label_create,
                                      tooltip=T("Add a new skill type to the catalog.")),
            )

        configure(tablename,
                  deduplicate = self.hrm_skill_type_duplicate,
                  )

        # ---------------------------------------------------------------------
        # Skills
        # - these can be simple generic skills or can come from certifications
        #
        tablename = "hrm_skill"
        define_table(tablename,
                     skill_type_id(empty=False),
                     Field("name", notnull=True, unique=True,
                           length=64,    # Mayon compatibility
                           label = T("Name"),
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

        skill_help = S3AddResourceLink(f="skill",
                                       label=label_create,
                                       tooltip=tooltip)

        represent = S3Represent(lookup=tablename)
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

        multi_skill_represent = S3Represent(lookup=tablename,
                                            multiple=True)
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
                  deduplicate = self.hrm_skill_duplicate,
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
                     skill_type_id(empty=False),
                     Field("name",
                           length=64, # Mayon Compatibility
                           label = T("Name"),
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

        represent = S3Represent(lookup=tablename)
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
                     person_id(),
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
            label_create = T("Create Skill"),
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
                  deduplicate = self.hrm_competency_duplicate,
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
        #table = define_table(tablename,
        #                     Field("name", notnull=True, unique=True,
        #                           length=32,    # Mayon compatibility
        #                           label = T("Name"),
        #                           ),
        #                     job_title_id(),
        #                     skill_id(),
        #                     competency_id(),
        #                     Field("priority", "integer",
        #                           default = 1,
        #                           requires = IS_INT_IN_RANGE(1, 10),
        #                           widget = S3SliderWidget(),
        #                           comment = DIV(_class="tooltip",
        #                                         _title="%s|%s" % (T("Priority"),
        #                                                           T("Priority from 1 to 9. 1 is most preferred.")))
        #                           ),
        #                     s3_comments(),
        #                     *s3_meta_fields())

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
        #                                                     vars=dict(format="popup")),
        #                                           _target="top",
        #                                           _title=label_create),
        #                                         DIV(_class="tooltip",
        #                                             _title="%s|%s" % (label_create,
        #                                                               T("Add a new skill provision to the catalog.")))),
        #                           )


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
                     person_id(),
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
                             label = T("Date Received")
                             ),
                     s3_date("end_date",
                             # @ToDo: Automation based on deployment_settings, e.g.: date received + 6/12 months
                             label = T("Expiry Date")
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

        # =========================================================================
        # Courses
        #
        tablename = "hrm_course"
        define_table(tablename,
                     Field("code", length=64,
                           label = T("Code"),
                           ),
                     Field("name", length=128, notnull=True,
                           label = T("Name"),
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     organisation_id(default = root_org,
                                     readable = is_admin,
                                     writable = is_admin,
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
            course_help = S3AddResourceLink(c="vol" if group == "volunteer" else "hrm",
                                            f="course",
                                            label=label_create)
        else:
            course_help = DIV(_class="tooltip",
                              _title="%s|%s" % (T("Course"),
                                                AUTOCOMPLETE_HELP))

        represent = S3Represent(lookup=tablename)
        course_id = S3ReusableField("course_id", "reference %s" % tablename,
                                    label = T("Course"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "hrm_course.id",
                                                          represent,
                                                          filterby="organisation_id",
                                                          filter_opts=filter_opts)),
                                    sortby = "name",
                                    comment = course_help,
                                    # Comment this to use a Dropdown & not an Autocomplete
                                    #widget = S3AutocompleteWidget("hrm", "course")
                                    )

        configure(tablename,
                  create_next = URL(f="course",
                                    args=["[id]", "course_certificate"]),
                  deduplicate = self.hrm_course_duplicate,
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
                       )

        # =========================================================================
        # Training Events
        #

        #site_label = settings.get_org_site_label()
        site_label = T("Venue")

        tablename = "hrm_training_event"
        define_table(tablename,
                     course_id(empty = False),
                     organisation_id(label = T("Organized By")),
                     self.super_link("site_id", "org_site",
                                     label = site_label,
                                     instance_types = auth.org_site_types,
                                     updateable = True,
                                     not_filterby = "obsolete",
                                     not_filter_opts = (True,),
                                     default = auth.user.site_id if auth.is_logged_in() else None,
                                     readable = True,
                                     writable = True,
                                     empty = False,
                                     represent = self.org_site_represent,
                                     ),
                     s3_datetime("start_date",
                                 label = T("Start Date"),
                                 ),
                     s3_datetime("end_date",
                                 label = T("End Date"),
                                 ),
                     Field("hours", "integer",
                           label = T("Hours"),
                           requires = IS_INT_IN_RANGE(1, 1000),
                           ),
                     # human_resource_id?
                     Field("instructor",
                           label = T("Instructor"),
                           represent = s3_string_represent,
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
                                            comment = S3AddResourceLink(f="training_event",
                                                                        label=ADD_TRAINING_EVENT),
                                            # Comment this to use a Dropdown & not an Autocomplete
                                            #widget = S3AutocompleteWidget("hrm", "training_event")
                                            )

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        filter_widgets = [
            S3TextFilter(["course_id$name",
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

        # Resource Configuration
        configure(tablename,
                  create_next = URL(f="training_event",
                                    args=["[id]", "participant"]),
                  deduplicate = self.hrm_training_event_duplicate,
                  filter_widgets = filter_widgets,
                  )

        # Components
        add_components(tablename,
                       # Participants
                       pr_person = {"name": "participant",
                                    "link": "hrm_training",
                                    "joinby": "training_event_id",
                                    "key": "person_id",
                                    "actuate": "hide",
                                    },
                       )

        # =====================================================================
        # Training Participations
        #
        # These are an element of credentials:
        # - a minimum number of hours of training need to be done each year
        #
        # Users can add their own but these are confirmed only by specific roles
        #

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
                     training_event_id(readable = False,
                                       writable = False,
                                       ),
                     course_id(empty=False),
                     s3_datetime(),
                     s3_datetime("end_date",
                                 label = T("End Date"),
                                 ),
                     Field("hours", "integer",
                           label = T("Hours"),
                           ),
                     # This field can only be filled-out by specific roles
                     # Once this has been filled-out then the other fields are locked
                     Field("grade", "integer",
                           label = T("Grade"),
                           represent = lambda opt: \
                                       hrm_performance_opts.get(opt, NONE),
                           # Default to pass/fail (can override to 5-levels in Controller)
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hrm_pass_fail_opts,
                                                  zero=None)),
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
            msg_list_empty = T("Currently no Trainings registered"))

        filter_widgets = [
            S3TextFilter(["person_id$first_name",
                          "person_id$last_name",
                          "course_id$name",
                          "comments",
                          ],
                         label = T("Search"),
                         comment = T("You can search by trainee name, course name or comments. You may use % as wildcard. Press 'Search' without input to list all trainees."),
                         _class="filter-search",
                         ),
            S3OptionsFilter("person_id$human_resource.organisation_id",
                            represent = "%(name)s",
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
            S3DateFilter("date",
                         hide_time=True,
                         ),
            ]

        report_fields = [(T("Training Event"), "training_event_id"),
                         "person_id",
                         "course_id",
                         (messages.ORGANISATION, "organisation"),
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
                  deduplicate = self.hrm_training_duplicate,
                  filter_widgets = filter_widgets,
                  list_fields = ["date",
                                 "course_id",
                                 "hours",
                                 ],
                  list_layout = hrm_training_list_layout,
                  onaccept = hrm_training_onaccept,
                  ondelete = hrm_training_onaccept,
                  # Only used in Imports
                  #onvalidation = hrm_training_onvalidation,
                  orderby = "hrm_training.date desc",
                  report_options = report_options,
                  )

        # =====================================================================
        # Certificates
        #
        # NB Some Orgs will only trust the certificates of some Orgs
        # - we currently make no attempt to manage this trust chain
        #
        filter_certs = settings.get_hrm_filter_certificates()
        if filter_certs:
            label = messages.ORGANISATION
        else:
            label = T("Certifying Organization")

        tablename = "hrm_certificate"
        define_table(tablename,
                     Field("name", notnull=True,
                           length=128,   # Mayon Compatibility
                           label = T("Name"),
                           ),
                     organisation_id(default = root_org if filter_certs else None,
                                     label = label,
                                     readable = is_admin or not filter_certs,
                                     writable = is_admin or not filter_certs,
                                     widget = widget,
                                     ),
                     Field("expiry", "integer",
                           label = T("Expiry (months)"),
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
             comment = S3AddResourceLink(f="certificate",
                                         label=label_create,
                                         title=label_create,
                                         tooltip=T("Add a new certificate to the catalog.")),
             )

        if settings.get_hrm_use_skills():
            create_next = URL(f="certificate",
                              args=["[id]", "certificate_skill"])
        else:
            create_next = None

        configure(tablename,
                  create_next = create_next,
                  deduplicate = self.hrm_certificate_duplicate,
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
                     Field("number",
                           label = T("License Number"),
                           ),
                     #Field("status", label=T("Status")),
                     s3_date(label = T("Expiry Date")),
                     Field("image", "upload",
                           autodelete = True,
                           label = T("Scanned Copy"),
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(request.folder,
                                                       "uploads"),
                           ),
                     # This field can only be filled-out by specific roles
                     # Once this has been filled-out then the other fields are locked
                     organisation_id(comment = None,
                                     label = T("Confirming Organization"),
                                     widget = widget,
                                     writable = False,
                                     ),
                     Field("from_training", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  list_fields = ["id",
                                 "certificate_id",
                                 "date",
                                 "comments",
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
        return dict(hrm_course_id = course_id,
                    hrm_skill_id = skill_id,
                    hrm_multi_skill_id = multi_skill_id,
                    hrm_multi_skill_represent = multi_skill_represent,
                    hrm_certification_onaccept = self.hrm_certification_onaccept,
                    )

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

        return dict(hrm_course_id = lambda **attr: dummy("course_id"),
                    hrm_skill_id = lambda **attr: dummy("skill_id"),
                    hrm_multi_skill_id = lambda **attr: dummy_listref("skill_id"),
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
                                                           limitby=(0, 1)
                                                           ).first()
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

        if current.request.controller == "vol":
            controller = "vol"
        else:
            controller = "hrm"
        if current.auth.s3_has_role(current.session.s3.system_roles.ADMIN):
            label_create = s3.crud_strings["hrm_competency_rating"].label_create
            comment = S3AddResourceLink(c=controller,
                                        f="competency_rating",
                                        vars={"child":"competency_id"},
                                        label=label_create,
                                        tooltip=T("Add a new competency rating to the catalog."))
        else:
            comment = DIV(_class="tooltip",
                          _title="%s|%s" % (T("Competency Rating"),
                                            T("Level of competency this person has with this skill.")))
        if current.deployment_settings.get_hrm_skill_types():
            s3.js_global.append('''i18n.no_ratings="%s"''' % T("No Ratings for Skill Type"))
            s3.jquery_ready.append(
'''$.filterOptionsS3({
 'trigger':'skill_id',
 'target':'competency_id',
 'lookupResource':'competency',
 'lookupURL':S3.Ap.concat('/%s/skill_competencies/'),
 'msgNoRecords':i18n.no_ratings
})''' % controller)

        return comment

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_competency_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same person_id and skill_id
        """

        data = item.data
        person = data.get("person_id")
        skill = data.get("skill_id")
        table = item.table
        query = (table.person_id == person) & \
                (table.skill_id == skill)

        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_certificate_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        name = item.data.get("name")

        table = item.table
        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

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
        query = (table.name.lower() == name.lower()) & \
                (table.skill_type_id == stable.id) & \
                (stable.value.lower() == skill.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_course_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        name = item.data.get("name")

        table = item.table
        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_skill_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        name = item.data.get("name")

        table = item.table
        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_skill_type_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        name = item.data.get("name")

        table = item.table
        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_training_event_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same course name & date (& site, if-present)
        """

        data = item.data
        # Mandatory Data
        course_id = data.get("course_id", None)
        start_date = data.get("start_date", None)
        if not course_id or not start_date:
            return
        # Optional Data
        site_id = data.get("site_id", None)

        # No longer required since Imports don't add seconds:
        # Need to provide a range of dates as otherwise second differences prevent matches
        # - assume that if we have multiple training courses of the same
        #   type at the same site then they start at least a minute apart
        #
        # @ToDo: refactor into a reusable function
        #year = start_date.year
        #month = start_date.month
        #day = start_date.day
        #hour = start_date.hour
        #minute = start_date.minute
        #start_start_date = datetime.datetime(year, month, day, hour, minute)
        #if minute < 58:
        #    minute = minute + 1
        #elif hour < 23:
        #    hour = hour + 1
        #    minute = 0
        #elif (day == 28 and month == 2) or \
        #     (day == 30 and month in [4, 6, 9, 11]) or \
        #     (day == 31 and month in [1, 3, 5, 7, 8, 10, 12]):
        #    month = month + 1
        #    day = 1
        #    hour = 0
        #    minute = 0
        #else:
        #    day = day + 1
        #    hour = 0
        #    minute = 0
        #start_end_date = datetime.datetime(year, month, day, hour, minute)

        table = item.table
        query = (table.course_id == course_id) & \
                (table.start_date == start_date)
        if site_id:
            query = query & (table.site_id == site_id)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_training_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same person, date & course
        """

        data = item.data
        person_id = data.get("person_id")
        course_id = data.get("course_id")
        date = data.get("date")

        table = item.table
        query = (table.person_id == person_id) & \
                (table.course_id == course_id)
        if date:
            query = query & (table.date == date)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

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
                                                      limitby = (0, 1)
                                                      ).first()
    try:
        form_vars.course_id = record.course_id
        form_vars.date = record.start_date
        form_vars.end_date = record.end_date
        form_vars.hours = record.hours
    except:
        # Record not found
        return

# =============================================================================
def hrm_training_onaccept(form):
    """
        Ensure that Certifications & Hours are Populated from Trainings
        - called both onaccept & ondelete
    """

    # Deletion and update have a different format
    try:
        _id = form.vars.id
        delete = False
    except:
        _id = form.id
        delete = True

    # Get the full record
    db = current.db
    table = db.hrm_training
    record = db(table.id == _id).select(table.person_id,
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
    vol_experience = current.deployment_settings.get_hrm_vol_experience()
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
            query = (ptable.training_id == _id)
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
                        _id = exists.id
                    else:
                        # Nothing to propagate
                        _id = None
                else:
                    _id = ptable.insert(training_id = _id,
                                        person_id = person_id,
                                        date = date,
                                        hours = hours,
                                        training = True)
                if _id:
                    # Propagate to Active Status
                    form = Storage()
                    form.vars = Storage()
                    form.vars.id = _id
                    hrm_programme_hours_onaccept(form)

    # Update Certifications
    ctable = db.hrm_certification
    cctable = db.hrm_course_certificate
    _ctable = db.hrm_certificate

    # Drop all existing certifications which came from trainings
    # - this is a lot easier than selective deletion.
    query = (ctable.person_id == person_id) & \
            (ctable.from_training == True)
    db(query).delete()

    # Figure out which certifications we're _supposed_ to have.
    query = (table.person_id == person_id) & \
            (table.course_id == cctable.course_id) & \
            (cctable.certificate_id == _ctable.id)
    trainings = db(query).select(_ctable.id)

    # Add these certifications back in.
    hrm_certification_onaccept = s3db.hrm_certification_onaccept
    form = Storage()
    form.vars = Storage()
    form_vars = form.vars
    for training in trainings:
        _id = ctable.update_or_insert(
                person_id = person_id,
                certificate_id = training.id,
                comments = "Added by training",
                from_training = True
                )
        # Propagate to Skills
        form_vars.id = _id
        hrm_certification_onaccept(form)

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
                               requires = IS_ADD_PERSON_WIDGET2(allow_empty=True),
                               widget = S3AddPersonWidget2(),
                               ),
                     s3_comments(),
                     *s3_meta_fields())

        ADD_APPRAISAL = T("Add Appraisal")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_APPRAISAL,
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
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_appraisal_create_onaccept(form):
        """
            Link Appraisal to Assignment
        """

        mission_id = current.request.get_vars.get("mission_id", None)
        if not mission_id:
            return

        id = form.vars.id
        db = current.db
        s3db = current.s3db
        atable = s3db.deploy_assignment
        hatable = db.hrm_appraisal
        hrtable = db.hrm_human_resource
        query = (hatable.id == id) & \
                (hrtable.person_id == hatable.person_id) & \
                (atable.human_resource_id == hrtable.id) & \
                (atable.mission_id == mission_id)
        assignment = db(query).select(atable.id,
                                      limitby=(0, 1)
                                      ).first()
        if not assignment:
            return
        db.deploy_assignment_appraisal.insert(assignment_id = assignment.id,
                                              appraisal_id = id,
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
            site_widget = S3SiteAutocompleteWidget(),
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
                                  ),
                          s3_date("end_date",
                                  label = T("End Date"),
                                  ),
                          Field("hours", "double",
                                label = T("Hours"),
                                ),
                          #Field("place",
                          #      label = T("Place"),
                          #      ),
                          self.gis_location_id(),
                          person_id("supervisor_id",
                                    label = T("Supervisor"),
                                    requires = IS_ADD_PERSON_WIDGET2(allow_empty=True),
                                    widget = S3AddPersonWidget2(),
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
                            deploy_assignment = "experience_id",
                            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

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
        table = define_table(tablename,
                             self.org_organisation_id(
                                requires = self.org_organisation_requires(updateable=True),
                             ),
                             Field("name",
                                   label = T("Award Type"),
                             ),
                             *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = self.award_type_duplicate,
                       )

        ADD_AWARD_TYPE = T("Add Award Type")
        award_type_represent = hrm_OrgSpecificTypeRepresent(lookup="hrm_award_type")

        # =====================================================================
        # Awards
        #
        tablename = "hrm_award"
        table = define_table(tablename,
                             self.pr_person_id(),
                             s3_date(),
                             Field("awarding_body"),
                             Field("award_type_id", "reference hrm_award_type",
                                   label = T("Award Type"),
                                   represent = award_type_represent,
                                   requires = IS_ONE_OF(db,
                                                        "hrm_award_type.id",
                                                        award_type_represent,
                                                        ),
                                   comment = S3AddResourceLink(f = "award_type",
                                                               label = ADD_AWARD_TYPE),
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
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def award_type_duplicate(item):
        """ Callback to identify the original of an update import item """

        data = item.data
        organisation_id = data.organisation_id
        name = data.name

        if organisation_id and name:

            table = item.table
            query = (table.organisation_id == organisation_id) & \
                    (table.name == name)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

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
                       deduplicate = self.disciplinary_type_duplicate,
                       )

        ADD_DISCIPLINARY_TYPE = T("Add Disciplinary Action Type")
        disciplinary_type_represent = hrm_OrgSpecificTypeRepresent(lookup="hrm_disciplinary_type")

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
                           comment = S3AddResourceLink(f = "disciplinary_type",
                                                       label = ADD_DISCIPLINARY_TYPE,
                                                       ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def disciplinary_type_duplicate(item):
        """ Callback to identify the original of an update import item """

        data = item.data
        organisation_id = data.organisation_id
        name = data.name

        if organisation_id and name:

            table = item.table
            query = (table.organisation_id == organisation_id) & \
                    (table.name == name)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3HRProgrammeModel(S3Model):
    """
        Record Volunteer Hours on Programmes
        - initially at least this doesn't link to the Project module

        @ToDo: Move to modules/eden/vol.py
    """

    names = ("hrm_programme",
             "hrm_programme_hours",
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
        # - not sure yet whether this will map to 'Project' or 'Activity' in future
        #

        tablename = "hrm_programme"
        define_table(tablename,
                     Field("name", notnull=True, length=64,
                           label = T("Name"),
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

        represent = S3Represent(lookup=tablename)
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
            comment = S3AddResourceLink(f="programme",
                                        label=label_create,
                                        title=label_create,
                                        tooltip=T("Add a new program to the catalog.")),
            )

        configure(tablename,
                  deduplicate = self.hrm_programme_duplicate,
                  )

        # Components
        self.add_components(tablename,
                            hrm_programme_hours = {"name": "person",
                                                   "joinby": "programme_id",
                                                   },
                            )

        # =====================================================================
        # Programmes <> Persons Link Table
        #
        tablename = "hrm_programme_hours"
        define_table(tablename,
                     self.pr_person_id(
                        ondelete = "CASCADE",
                        represent = self.pr_PersonRepresent(show_link=True)
                        ),
                     programme_id(),
                     self.hrm_job_title_id(),
                     s3_date(future=0),
                     Field("hours", "double",
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
                  list_fields = ["id",
                                 "training",
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
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm_programme_duplicate(item):
        """
            HR record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        data = item.data
        name = data.get("name")
        org = data.get("organisation_id")

        table = item.table
        query = (table.deleted != True) & \
                (table.name == name) & \
                (table.organisation_id == org)
        row = current.db(query).select(table.id,
                                       limitby=(0, 1)).first()
        if row:
            item.id = row.id
            item.method = item.METHOD.UPDATE

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
    try:
        id = form.vars.id
        delete = False
    except:
        id = form.id
        delete = True

    # Get the full record
    db = current.db
    table = db.hrm_programme_hours
    record = db(table.id == id).select(table.person_id,
                                       table.deleted_fk,
                                       limitby=(0, 1)).first()

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
                           limitby=(0, 1)).first()
    if row:
        if row.active != active:
            # Update
            db(dtable.id == row.id).update(active=active)
    else:
        # Create record
        row = db(htable.person_id == person_id).select(htable.id,
                                                       limitby=(0, 1)
                                                       ).first()
        if row:
            dtable.insert(human_resource_id = row.id,
                          active = active)

# =============================================================================
class hrm_AssignMethod(S3Method):
    """
        Custom Method to allow human resources to be assigned to something
        e.g. Incident, Project, Site, Vehicle

        @ToDo: be able to filter by deployable status for the role
    """

    def __init__(self, component, types=None):
        """
            @param component: the Component in which to create records
            @param types: a list of types to pick from: Staff, Volunteers, Deployables
        """

        self.component = component
        self.types = types

    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        component = self.component
        components = r.resource.components
        for c in components:
            if c == component:
                component = components[c]
                break
        try:
            if component.link:
                component = component.link
        except:
            current.log.error("Invalid Component!")
            raise

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
        s3db = current.s3db

        get_vars = r.get_vars
        response = current.response

        if r.http == "POST":
            added = 0
            post_vars = r.post_vars
            if all([n in post_vars for n in ("assign", "selected", "mode")]):
                fkey = component.fkey
                record = r.record
                if fkey in record:
                    # SuperKey
                    record_id = r.record[fkey]
                else:
                    record_id = r.id
                selected = post_vars.selected
                if selected:
                    selected = selected.split(",")
                else:
                    selected = []

                db = current.db
                table = s3db[tablename]

                # Handle exclusion filter
                if post_vars.mode == "Exclusive":
                    if "filterURL" in post_vars:
                        filters = S3URLQuery.parse_url(post_vars.filterURL)
                    else:
                        filters = None
                    query = ~(FS("id").belongs(selected))
                    hresource = s3db.resource("hrm_human_resource",
                                              alias = self.component,
                                              filter=query, vars=filters)
                    rows = hresource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

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
                            form = Storage(vars=link)
                            onaccept(form)
                        added += 1
            current.session.confirmation = T("%(number)s assigned") % \
                                           dict(number=added)
            if added > 0:
                redirect(URL(args=[r.id, "human_resource"], vars={}))
            else:
                redirect(URL(args=r.args, vars={}))

        elif r.http == "GET":

            # Filter widgets
            if controller == "vol":
                resource_type = "volunteer"
            elif len(types) == 1:
                resource_type = "staff"
            else:
                # Both
                resource_type = None
            filter_widgets = hrm_human_resource_filters(resource_type=resource_type,
                                                        module=controller)

            # List fields
            list_fields = ["id",
                           "person_id",
                           "organisation_id",
                           ]
            if len(types) == 2:
                list_fields.append("type")
            list_fields.append("job_title_id")
            if settings.get_hrm_use_certificates():
                list_fields.append(("Certificates", "person_id$certification.certificate_id"))
            if settings.get_hrm_use_skills():
                list_fields.append(("Skills", "person_id$competency.skill_id"))
            if settings.get_hrm_use_trainings():
                list_fields.append(("Trainings", "person_id$training.course_id"))

            # Data table
            resource = s3db.resource("hrm_human_resource",
                                     alias=r.component.alias if r.component else None,
                                     vars=get_vars)
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
            filter, orderby, left = resource.datatable_filter(list_fields, get_vars)
            resource.add_filter(filter)
            data = resource.select(list_fields,
                                   start=0,
                                   limit=limit,
                                   orderby=orderby,
                                   left=left,
                                   count=True,
                                   represent=True)
            filteredrows = data["numrows"]
            dt = S3DataTable(data["rfields"], data["rows"])
            dt_id = "datatable"

            # Bulk actions
            dt_bulk_actions = [(T("Assign"), "assign")]

            if r.representation == "html":
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

                # Data table (items)
                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_ajax_url=r.url(representation="aadata"),
                                dt_bulk_actions=dt_bulk_actions,
                                dt_pageLength=display_length,
                                dt_pagination="true",
                                dt_searching="false",
                                )

                # Filter form
                if filter_widgets:

                    # Where to retrieve filtered data from:
                    _vars = resource.crud._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars=_vars)

                    # Where to retrieve updated filter options from:
                    filter_ajax_url = URL(f="human_resource",
                                          args=["filter.options"],
                                          vars={})

                    get_config = resource.get_config
                    filter_clear = get_config("filter_clear", True)
                    filter_formstyle = get_config("filter_formstyle", None)
                    filter_submit = get_config("filter_submit", True)
                    filter_form = S3FilterForm(filter_widgets,
                                               clear=filter_clear,
                                               formstyle=filter_formstyle,
                                               submit=filter_submit,
                                               ajax=True,
                                               url=filter_submit_url,
                                               ajaxurl=filter_ajax_url,
                                               _class="filter-form",
                                               _id="datatable-filter-form",
                                               )
                    fresource = current.s3db.resource(resource.tablename)
                    alias = r.component.alias if r.component else None
                    ff = filter_form.html(fresource,
                                          r.get_vars,
                                          target="datatable",
                                          alias=alias)
                else:
                    ff = ""

                STAFF = settings.get_hrm_staff_label()
                output = dict(items = items,
                              title = T("Assign %(staff)s") % dict(staff=STAFF),
                              list_filter_form = ff)

                response.view = "list_filter.html"
                return output

            elif r.representation == "aadata":
                # Ajax refresh
                if "draw" in get_vars:
                    echo = int(get_vars.draw)
                else:
                    echo = None
                items = dt.json(totalrows,
                                filteredrows,
                                dt_id,
                                echo,
                                dt_bulk_actions=dt_bulk_actions)
                response.headers["Content-Type"] = "application/json"
                return items

            else:
                r.error(501, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

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
    def lookup_rows(self, key, values, fields=[]):
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
        if len(values) == 1:
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
        representation = [s3_unicode(s3_fullname(row.pr_person))]
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
    def lookup_rows(self, key, values, fields=[]):
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
                                        left = left)
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
    def lookup_rows(self, key, values, fields=[]):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
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

        rows = current.db(query).select(etable.id,
                                        etable.start_date,
                                        etable.instructor,
                                        ctable.name,
                                        ctable.code,
                                        stable.name,
                                        left = left)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            NB This needs to be machine-parseable by training.xsl

            @param row: the Row
        """

        # Course details
        course = row.get("hrm_course")
        if not course:
            return current.messages.UNKNOWN_OPT
        name = course.get("name")
        if not name:
            name = current.messages.UNKNOWN_OPT
        code = course.get("code")
        if code:
            representation = ["%s (%s)" % (name, code)]
        else:
            representation = [name]
        append = representation.append

        # Venue and instructor
        event = row.hrm_training_event
        try:
            site = row.org_site.name
        except:
            site = None
        instructor = event.get("instructor")
        if instructor and site:
            append(" %s - {%s}" % (instructor, site))
        elif instructor:
            append(" %s" % instructor)
        elif site:
            append(" {%s}" % site)

        # Start date
        start_date = event.start_date
        if start_date:
            # Easier for users & machines
            start_date = S3DateTime.date_represent(start_date, format="%Y-%m-%d")
            append(" [%s]" % start_date)

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

    id = form_vars.id
    if not id:
        return

    db = current.db
    s3db = current.s3db
    auth = current.auth
    request = current.request
    settings = current.deployment_settings

    # Get the 'full' record
    htable = db.hrm_human_resource
    record = db(htable.id == id).select(htable.id, # needed for update_record
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
                                        limitby=(0, 1)).first()

    job_title_id = record.job_title_id
    if job_title_id and settings.get_hrm_multiple_job_titles():
        # Update the link table
        ltable = db.hrm_job_title_human_resource
        query = (ltable.human_resource_id == id) & \
                (ltable.job_title_id == job_title_id)
        exists = db(query).select(ltable.id, # needed for update_record
                                  ltable.main,
                                  limitby=(0, 1)).first()
        if exists:
            if not exists.main:
                exists.update_record(main=True)
        else:
            # Insert record
            ltable.insert(human_resource_id=id,
                          job_title_id=job_title_id,
                          main=True,
                          start_date=request.utcnow,
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
        # Set pr_person.realm_entity to the human_resource's site pe_id
        entity = s3db.pr_get_pe_id("org_site", site_id) or \
                 s3db.pr_get_pe_id("org_organisation", organisation_id)

        if entity:
            auth.set_realm_entity(ptable, person,
                                  entity = entity,
                                  force_update = True)

    # Set person record to follow HR record
    tracker = S3Tracker()
    pr_tracker = tracker(ptable, person_id)
    pr_tracker.check_in(htable, id, timestmp = request.utcnow)

    if record.type == 1:
        # Staff
        vol = False
        location_lookup = settings.get_hrm_location_staff()
    elif record.type == 2:
        # Volunteer
        vol = True
        location_lookup = settings.get_hrm_location_vol()

    # Determine how the HR is positioned
    address = None
    site_contact = record.site_contact
    update_location_from_site = False
    hstable = s3db.hrm_human_resource_site
    query = (hstable.human_resource_id == id)
    if site_id:
        # Add/update the record in the link table
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
        if location_lookup == "site_id" or location_lookup[0] == "site_id":
            update_location_from_site = True
        elif location_lookup[0] == "person_id":
            # Update Location from Site only if the Person has no Home Address
            atable = s3db.pr_address
            query = (atable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (atable.type == 1) & \
                    (atable.deleted == False)
            address = db(query).select(atable.location_id,
                                       limitby=(0, 1)).first()
            if not address:
                update_location_from_site = True
        else:
            # location_lookup == "person_id"
            # Set to the Home Address (if-present)
            atable = s3db.pr_address
            query = (atable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (atable.type == 1) & \
                    (atable.deleted == False)
            address = db(query).select(atable.location_id,
                                       limitby=(0, 1)).first()
    else:
        # Delete any links in the link table
        db(query).delete()
        if "person_id" in location_lookup:
            # Set to the Home Address (if-present)
            atable = s3db.pr_address
            query = (atable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (atable.type == 1) & \
                    (atable.deleted == False)
            address = db(query).select(atable.location_id,
                                       limitby=(0, 1)).first()

    if update_location_from_site:
        stable = db.org_site
        site = db(stable.site_id == site_id).select(stable.location_id,
                                                    limitby=(0, 1)).first()
        try:
            data.location_id = location_id = site.location_id
        except:
            current.log.error("Can't find site with site_id", site_id)
            data.location_id = location_id = None

    elif address:
        data.location_id = location_id = address.location_id

    elif vol and record.location_id:
        # Add Address from newly-created HRM
        query = (ptable.id == person_id)
        pe = db(query).select(ptable.pe_id,
                              limitby=(0, 1)).first()
        try:
            record_id = atable.insert(type = 1,
                                      pe_id = pe.pe_id,
                                      location_id = location_id)
        except:
            current.log.error("Can't find person with id", person_id)

    else:
        data.location_id = location_id = None

    if location_id:
        # Set Base Location
        hrm_tracker = tracker(htable, id)
        hrm_tracker.set_base_location(location_id)
    else:
        # Unset Base Location
        hrm_tracker = tracker(htable, id)
        hrm_tracker.set_base_location(None)

    if settings.get_hrm_site_contact_unique():
        # Ensure only one Site Contact per Site
        if site_contact and site_id:
            # Set all others in this Facility to not be the Site Contact
            # @ToDo: deployment_setting to allow multiple site contacts
            query  = (htable.site_id == site_id) & \
                     (htable.site_contact == True) & \
                     (htable.id != id)
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

    if user and organisation_id:
        profile = dict()
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
            db(utable.id == user.id).update(**profile)

# =============================================================================
def hrm_compose():
    """
        Send message to people/teams
    """

    T = current.T
    s3db = current.s3db
    req_vars = current.request.vars

    if "human_resource.id" in req_vars:
        fieldname = "human_resource.id"
        id = req_vars.get(fieldname)
        table = s3db.pr_person
        htable = s3db.hrm_human_resource
        query = (htable.id == id) & \
                (htable.person_id == table.id)
        title = T("Send a message to this person")
    elif "group_id" in req_vars:
        id = req_vars.group_id
        fieldname = "group_id"
        table = s3db.pr_group
        query = (table.id == id)
        title = T("Send a message to this team")
    else:
        current.session.error = T("Record not found")
        redirect(URL(f="index"))

    db = current.db
    pe = db(query).select(table.pe_id,
                          limitby=(0, 1)).first()
    if not pe:
        current.session.error = T("Record not found")
        redirect(URL(f="index"))

    pe_id = pe.pe_id

    if "hrm_id" in req_vars:
        # Get the individual's communications options & preference
        ctable = s3db.pr_contact
        contact = db(ctable.pe_id == pe_id).select(ctable.contact_method,
                                                   orderby="priority",
                                                   limitby=(0, 1)).first()
        if contact:
            s3db.msg_outbox.contact_method.default = contact.contact_method
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
            represent = len(vals) and vals[0] or ""
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
            represent = len(vals) and vals[0] or ""
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
            represent = len(vals) and vals[0] or ""
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
                repr = job.name
                if output:
                    output = "%s, %s" % (output, repr)
                else:
                    output = repr
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
                repr = represent(org.organisation_id)
                if output:
                    output = "%s, %s" % (output, repr)
                else:
                    output = repr
            return output

    return current.messages["NONE"]

# =============================================================================
def hrm_rheader(r, tabs=[],
                profile=False):
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
        get_vars = r.get_vars
        hr = get_vars.get("human_resource.id", None)
        if hr:
            name = current.s3db.hrm_human_resource_represent(int(hr))
        else:
            name = s3_fullname(record)
        group = get_vars.get("group", None)
        if group is None:
            controller = r.controller
            if controller == "vol":
                group = "volunteer"
            else:
                group = "staff"
        use_cv = settings.get_hrm_cv_tab()
        use_record = settings.get_hrm_record_tab()
        experience_tab = None
        service_record = ""
        tbl = TABLE(TR(TH(name,
                          # @ToDo: Move to CSS
                          _style="padding-top:15px")
                       ))
        experience_tab2 = None
        if group == "volunteer":
            vol_experience = settings.get_hrm_vol_experience()
            if vol_experience in ("programme", "both"):
                # Integrated into Record tab
                #experience_tab = (T("Hours"), "hours")
                # Show all Hours spent on both Programmes & Trainings
                # - last month & last year
                now = r.utcnow
                last_year = now - datetime.timedelta(days=365)
                db = current.db
                s3db = current.s3db
                ptable = s3db.hrm_programme
                phtable = db.hrm_programme_hours
                bquery = (phtable.deleted == False) & \
                         (phtable.person_id == r.id)
                query = bquery & \
                        (phtable.programme_id == ptable.id)
                row = db(query).select(ptable.name,
                                       phtable.date,
                                       orderby=phtable.date).last()
                if row:
                    programme = row.hrm_programme.name
                else:
                    programme = ""
                query = bquery & \
                        (phtable.date > last_year.date())
                rows = db(query).select(phtable.date,
                                        phtable.hours,
                                        phtable.training)
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

                vol_active = settings.get_hrm_vol_active()
                if vol_active:
                    if not hr:
                        # @ToDo: Handle multiple active HR records
                        htable = s3db.hrm_human_resource
                        query = (htable.person_id == r.id) & \
                                (htable.deleted == False)
                        hr = db(query).select(htable.id, limitby=(0, 1)).first()
                        if hr:
                            hr = hr.id
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
                row1 = TR(TH("%s:" % T("Program")),
                          programme,
                          *active_cells
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
                                    # @ToDo: Move to CSS
                                    _style="margin-bottom:10px"
                                    )
                if vol_experience == "both" and not use_cv:
                    experience_tab2 = (T("Experience"), "experience")
            elif vol_experience == "experience" and not use_cv:
                experience_tab = (T("Experience"), "experience")
        elif settings.get_hrm_staff_experience() == "experience" and not use_cv:
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

        if settings.get_hrm_use_education() and not use_cv:
            education_tab = (T("Education"), "education")
        else:
            education_tab = None

        if settings.get_hrm_use_id():
            id_tab = (T("ID"), "identity")
        else:
            id_tab = None

        if settings.get_hrm_salary():
            salary_tab = (T("Salary"), "salary")
        else:
            salary_tab = None

        if settings.get_hrm_use_skills() and not use_cv:
            skills_tab = (T("Skills"), "competency")
        else:
            skills_tab = None

        if not use_record:
            teams = settings.get_hrm_teams()
            if teams:
                teams_tab = (T(teams), "group_membership")
            else:
                teams_tab = None
        else:
            teams_tab = None

        if settings.get_hrm_use_trainings() and not use_cv:
            trainings_tab = (T("Trainings"), "training")
        else:
            trainings_tab = None

        if use_cv:
            trainings_tab = (T("CV"), "cv")

        if use_record:
            record_method = "record"
        else:
            record_method = "human_resource"

        if profile:
            # Configure for personal mode
            tabs = [(T("Person Details"), None),
                    (T("User Account"), "user"),
                    (T("Staff/Volunteer Record"), record_method),
                    id_tab,
                    description_tab,
                    (T("Address"), "address"),
                    ]
            contacts_tabs = settings.get_pr_contacts_tabs()
            if "all" in contacts_tabs:
                tabs.append((T("Contacts"), "contacts"))
            if "public" in contacts_tabs:
                tabs.append((T("Public Contacts"), "public_contacts"))
            if "private" in contacts_tabs:
                tabs.append((T("Private Contacts"), "private_contacts"))
            tabs += [education_tab,
                     trainings_tab,
                     certificates_tab,
                     skills_tab,
                     credentials_tab,
                     experience_tab,
                     experience_tab2,
                     teams_tab,
                     #(T("Assets"), "asset"),
                     ]
        elif current.session.s3.hrm.mode is not None:
            # Configure for personal mode
            tabs = [(T("Person Details"), None),
                    id_tab,
                    description_tab,
                    (T("Address"), "address"),
                    ]
            contacts_tabs = settings.get_pr_contacts_tabs()
            if "all" in contacts_tabs:
                tabs.append((T("Contacts"), "contacts"))
            if "public" in contacts_tabs:
                tabs.append((T("Public Contacts"), "public_contacts"))
            if "private" in contacts_tabs:
                tabs.append((T("Private Contacts"), "private_contacts"))
            tabs += [trainings_tab,
                     certificates_tab,
                     skills_tab,
                     credentials_tab,
                     experience_tab,
                     experience_tab2,
                     (T("Positions"), "human_resource"),
                     teams_tab,
                     (T("Assets"), "asset"),
                     ]
        else:
            # Configure for HR manager mode
            if group == "staff":
                hr_record = T("Staff Record")
                awards_tab = None
            elif group == "volunteer":
                hr_record = T("Volunteer Record")
                if settings.get_hrm_use_awards() and not use_cv:
                    awards_tab = (T("Awards"), "award")
                else:
                    awards_tab = None
            tabs = [(T("Person Details"), None),
                    (hr_record, record_method),
                    id_tab,
                    description_tab,
                    (T("Address"), "address"),
                    ]
            contacts_tabs = settings.get_pr_contacts_tabs()
            if "all" in contacts_tabs:
                tabs.append((T("Contacts"), "contacts"))
            if "public" in contacts_tabs:
                tabs.append((T("Public Contacts"), "public_contacts"))
            if "private" in contacts_tabs:
                tabs.append((T("Private Contacts"), "private_contacts"))
            tabs += [salary_tab,
                     education_tab,
                     trainings_tab,
                     certificates_tab,
                     skills_tab,
                     credentials_tab,
                     experience_tab,
                     experience_tab2,
                     awards_tab,
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
                                            _class="rheader-avatar"),
                        _href=URL(f="person", args=[record.id, "image"],
                                  vars = get_vars),
                        ),
                      tbl,
                      rheader_tabs)

    elif resourcename == "training_event":
        # Tabs
        tabs = [(T("Training Event Details"), None),
                (T("Participants"), "participant"),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(TH("%s: " % table.course_id.label),
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
                ]
        if current.deployment_settings.get_hrm_use_skills():
            tabs.append((T("Skill Equivalence"), "certificate_skill"))
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name),
                            ),
                      rheader_tabs)

    elif resourcename == "course":
        # Tabs
        tabs = [(T("Course Details"), None),
                (T("Course Certificates"), "course_certificate"),
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

    return rheader

# =============================================================================
def hrm_competency_controller():
    """
        RESTful CRUD controller
         - used for Searching for people by Skill
         - used for Adding/Editing on Profile page
    """

    if current.session.s3.hrm.mode is not None:
        current.session.error = current.T("Access denied")
        redirect(URL(f="index"))

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
                                    get_s3_filter_opts("hrm_skill", translate=True),
                                ),
                S3OptionsFilter("competency_id",
                                label = T("Competency"),
                                options = lambda: \
                                    get_s3_filter_opts("hrm_competency_rating", translate=True),
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

    def postp(r,output):
        if r.interactive:
            # Custom action button to add the member to a team
            S3CRUD.action_buttons(r)

            args = ["[id]", "group_membership"]
            s3.actions.append(dict(label=str(T("Add to a Team")),
                                             _class="action-btn",
                                             url = URL(f = "person",
                                                       args = args))
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

    if current.session.s3.hrm.mode is not None:
        current.session.error = current.T("Access denied")
        redirect(URL(f="index"))

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
    current.response.s3.prep = prep

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

    if current.session.s3.hrm.mode is not None:
        current.session.error = current.T("Access denied")
        redirect(URL(f="index"))

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

    output = current.rest_controller("hrm", "experience",
                                     # @ToDo: Create these if-required
                                     #csv_stylesheet = ("hrm", "experience.xsl"),
                                     #csv_template = ("hrm", "experience"),
                                     )
    return output

# =============================================================================
def hrm_group_controller():
    """
        Team controller
        - uses the group table from PR
    """

    T = current.T
    s3db = current.s3db
    s3 = current.response.s3
    team_name = current.deployment_settings.get_hrm_teams()

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
        ADD_TEAM = T("Add Team")
        s3.crud_strings[tablename] = Storage(
            label_create = ADD_TEAM,
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
        ottable = s3db.org_organisation_team
        label = ottable.organisation_id.label
        ottable.organisation_id.label = ""
        crud_form = S3SQLCustomForm("name",
                                    "description",
                                    S3SQLInlineComponent("organisation_team",
                                                         label = label,
                                                         fields = ["organisation_id"],
                                                         # @ToDo: Make this optional?
                                                         multiple = False,
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

        list_fields = ["id",
                       "organisation_team.organisation_id",
                       "name",
                       "description",
                       "comments",
                       ]

        s3db.configure("pr_group",
                       # Redirect to member list when a new group has been created
                       create_next = URL(f="group",
                                         args=["[id]", "group_membership"]),
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

        if r.interactive or r.representation in ("aadata", "xls"):
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
                                   list_fields=list_fields)

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
                        "label": str(T("Send Message"))})

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

    output = current.rest_controller("pr", "group",
                                     csv_stylesheet = ("hrm", "group.xsl"),
                                     csv_template = "group",
                                     rheader = lambda r: \
                                        s3db.pr_rheader(r, tabs=tabs)
                                     )

    return output

# =============================================================================
def hrm_human_resource_controller(extra_filter=None):
    """
        Human Resources Controller, defined in the model for use from
        multiple controllers for unified menus
         - used for Summary & Profile views, Imports and S3AddPersonWidget2
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

        method = r.method
        if method in ("form", "lookup"):
            return True

        # Profile
        elif method == "profile":

            # Adapt list_fields for pr_address
            s3db.pr_address # must load model before get_config
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
            s3db.hrm_experience # Load normal model
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
                                 s3_unicode(table.job_title_id.represent(record.job_title_id))),
                            comments)

            # Configure widgets
            # @todo: put into separate function
            contacts_widget = dict(label = "Contacts",
                                   label_create = "Create Contact",
                                   tablename = "pr_contact",
                                   type = "datalist",
                                   filter = FS("pe_id") == pe_id,
                                   icon = "icon-phone",
                                   # Default renderer:
                                   #list_layout = s3db.pr_render_contact,
                                   orderby = "priority asc",
                                   )
            address_widget = dict(label = "Address",
                                  label_create = "Add Address",
                                  type = "datalist",
                                  tablename = "pr_address",
                                  filter = FS("pe_id") == pe_id,
                                  icon = "icon-home",
                                  # Default renderer:
                                  #list_layout = s3db.pr_render_address,
                                  )
            credentials_widget = dict(# @ToDo: deployment_setting for Labels
                                      label = "Sectors",
                                      label_create = "Create Sector",
                                      type = "datalist",
                                      tablename = "hrm_credential",
                                      filter = FS("person_id") == person_id,
                                      icon = "icon-tags",
                                      # Default renderer:
                                      #list_layout = hrm_credential_list_layout,
                                      )
            skills_widget = dict(label = "Skills",
                                 label_create = "Create Skill",
                                 type = "datalist",
                                 tablename = "hrm_competency",
                                 filter = FS("person_id") == person_id,
                                 icon = "icon-comment-alt",
                                 # Default renderer:
                                 #list_layout = hrm_competency_list_layout,
                                 )
            trainings_widget = dict(label = "Trainings",
                                    label_create = "Add Training",
                                    type = "datalist",
                                    tablename = "hrm_training",
                                    filter = FS("person_id") == person_id,
                                    icon = "icon-wrench",
                                    # Default renderer:
                                    #list_layout = hrm_training_list_layout,
                                    )
            experience_widget = dict(label = "Experience",
                                     label_create = "Add New Experience",
                                     type = "datalist",
                                     tablename = "hrm_experience",
                                     filter = FS("person_id") == person_id,
                                     icon = "icon-truck",
                                     # Default renderer:
                                     #list_layout = hrm_experience_list_layout,
                                     )
            docs_widget = dict(label = "Documents",
                               label_create = "Add New Document",
                               type = "datalist",
                               tablename = "doc_document",
                               filter = FS("doc_id") == record.doc_id,
                               icon = "icon-paperclip",
                               # Default renderer:
                               #list_layout = s3db.doc_document_list_layout,
                               )
            education_widget = dict(label = "Education",
                                    label_create = "Add Education",
                                    type = "datalist",
                                    tablename = "pr_education",
                                    filter = FS("person_id") == person_id,
                                    icon = "icon-book",
                                    )
            profile_widgets = [contacts_widget,
                               address_widget,
                               skills_widget,
                               trainings_widget,
                               experience_widget,
                               docs_widget,
                               ]

            if deploy:
                profile_widgets.insert(2, credentials_widget)
                if settings.get_hrm_use_education():
                    profile_widgets.insert(-1, education_widget)

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
                           profile_title = "%s : %s" % (s3.crud_strings["hrm_human_resource"].title_display,
                                                        name),
                           profile_widgets = profile_widgets,
                           )

        # Summary
        elif method == "summary":

            # CRUD Strings
            s3.crud_strings["hrm_human_resource"]["title_list"] = T("Staff & Volunteers")

            # Filter Widgets
            filter_widgets = hrm_human_resource_filters(resource_type="both",
                                                        hrm_type_opts=s3db.hrm_type_opts)

            # List Fields
            list_fields = ["id",
                           "person_id",
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

            if vol:
                vol_active = settings.get_hrm_vol_active()
                if vol_active:
                    list_fields.append((T("Active"), "details.active"))
                    rappend((T("Active"), "details.active"))
                vol_experience = settings.get_hrm_vol_experience()
                if vol_experience in ("programme", "both"):
                    list_fields.append((T("Program"), "person_id$hours.programme_id"))
                    rappend((T("Program"), "person_id$hours.programme_id"))
            else:
                list_fields.extend(("department_id",
                                    "site_id"))
                report_fields.extend(("site_id",
                                      "department_id"))

            list_fields.extend(((T("Email"), "email.value"),
                                (settings.get_ui_label_mobile_phone(), "phone.value")))

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
                vars = {"human_resource.id" : r.id,
                        "group" : "staff"
                        }
                redirect(URL(f="person",
                             vars=vars))

        elif r.representation == "xls" and not r.component:
            # Export format should match Import format as far as possible
            # @ToDo: Handle XLS wrappers with e.g. localised field names
            # @ToDo: Vary for Staff / Volunteers
            # @ToDo: DRY with routines in controllers/hrm & controllers/vol
            r.table.organisation_id.represent = \
                s3db.org_OrganisationRepresent(acronym=False, parent=False)
            r.table.site_id.represent = s3db.org_SiteRepresent(show_type=False)
            # @ToDo: Get NONE as "" working
            current.messages["NONE"] = ""
            list_fields = [("Type", "type"),
                           ("First Name", "person_id$first_name"),
                           ("Middle Name", "person_id$middle_name"),
                           ("Last Name", "person_id$last_name"),
                           ("Job Title", "job_title_id"),
                           # @ToDo: Organisation or Branch (using custom Represent options)
                           #("Organisation", "organisation_id$parent"),
                           #("Branch", "organisation_id"),
                           ("Organisation", "organisation_id"),
                           ("Department", "department_id"),
                           ("Office", "site_id"),
                           ("Facility Type", "site_id$instance_type"),
                           ("Staff ID", "code"),
                           ("Email", "email.value"),
                           ("Mobile Phone", "phone.value"),
                           ("Sex", "person_id$gender"),
                           ("DOB", "person_id$date_of_birth"),
                           ("Start Date", "start_date"),
                           ("End Date", "end_date"), # Not reimported
                           ("Status", "status"),
                           ("Essential", "essential"), # Not reimported
                           ]
            if settings.get_hrm_use_trainings():
                list_fields.append(("Trainings", "person_id$training.course_id"))
            if settings.get_hrm_use_certificates():
                # @ToDo: Make Importable
                list_fields.append(("Certificates", "person_id$certification.certificate_id"))
            if settings.get_hrm_vol_experience() in ("programme", "both"):
                # @ToDo: Make Importable
                list_fields.append(("Programs", "person_id$hours.programme_id"))
            list_fields.append(("Comments", "comments"))
            r.resource.configure(list_fields = list_fields)

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_human_resource_start_date','hrm_human_resource_end_date')''')

                if r.controller == "deploy":
                    # Application is deleted, not HR
                    deletable = True
                    # Open Profile page
                    read_url = URL(args = ["[id]", "profile"])
                    update_url = URL(args = ["[id]", "profile"])
                else:
                    deletable = settings.get_hrm_deletable(),
                    # Standard CRUD buttons
                    read_url = None
                    update_url = None
                S3CRUD.action_buttons(r,
                                      deletable = deletable,
                                      read_url = read_url,
                                      update_url = update_url)
                if "msg" in settings.modules and \
                   current.auth.permission.has_permission("update",
                                                          c="hrm",
                                                          f="compose"):
                    s3.actions.append({
                        "url": URL(f="compose",
                                   vars = {"human_resource.id": "[id]"}),
                        "_class": "action-btn send",
                        "label": str(T("Send Message"))})

        elif r.representation == "plain":
            # Map Popups
            output = hrm_map_popup(r)

        return output
    s3.postp = postp

    output = current.rest_controller("hrm", "human_resource")
    return output

# =============================================================================
def hrm_person_controller(**attr):
    """
        Persons Controller, defined in the model for use from
        multiple controllers for unified menus
         - used for access to component Tabs, Personal Profile & Imports
         - includes components relevant to HRM
    """

    T = current.T
    auth = current.auth
    db = current.db
    s3db = current.s3db
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
                   action = s3db.pr_contacts)
    if "public" in contacts_tabs:
        set_method("pr", "person",
                   method = "public_contacts",
                   action = s3db.pr_contacts)
    if "private" in contacts_tabs:
        set_method("pr", "person",
                   method = "private_contacts",
                   action = s3db.pr_contacts)

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
            group = hr.type == 2 and "volunteer" or "staff"
            # Also inform the back-end of this finding
            get_vars["group"] = group

    # Configure person table
    table = db.pr_person
    tablename = "pr_person"
    configure(tablename,
              deletable=False)

    mode = session.s3.hrm.mode
    if mode is not None:
        # Configure for personal mode
        s3.crud_strings[tablename].update(
            title_display = T("Personal Profile"),
            title_update = T("Personal Profile"))
        # People can view their own HR data, but not edit it
        configure("hrm_human_resource",
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )
        configure("hrm_certification",
                  deletable = True,
                  editable = True,
                  insertable = True,
                  )
        configure("hrm_credential",
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )
        configure("hrm_competency",
                  deletable = False,
                  editable = False,
                  insertable = True,  # Can add unconfirmed
                  )
        configure("hrm_training",    # Can add but not provide grade
                  deletable = False,
                  editable = False,
                  insertable = True,
                  )
        configure("hrm_experience",
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )
        configure("pr_group_membership",
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )
    else:
        # Configure for HR manager mode
        if settings.get_hrm_staff_label() == T("Contacts"):
            s3.crud_strings[tablename].update(
                    title_upload = T("Import Contacts"),
                    title_display = T("Contact Details"),
                    title_update = T("Contact Details")
                    )
        else:
            s3.crud_strings[tablename].update(
                    title_upload = T("Import Staff"),
                    title_display = T("Staff Member Details"),
                    title_update = T("Staff Member Details")
                    )
    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: dict(ReplaceOption=T("Remove existing data before import"))

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
                table.date_of_birth.widget = S3DateWidget(past=1440, future=-60)

                person_details_table = s3db.pr_person_details
                # No point showing the 'Occupation' field - that's the Job Title in the Staff Record
                person_details_table.occupation.readable = person_details_table.occupation.writable = False

                # Organisation Dependent Fields
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("pr_person", "middle_name")
                set_org_dependent_field("pr_person_details", "father_name")
                set_org_dependent_field("pr_person_details", "mother_name")
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
                              deletable = False)

                elif component_name == "group_membership":
                    hrm_configure_pr_group_membership()

                elif component_name == "salary":
                    hrm_configure_salary(r)

            if method == "record" or r.component_name == "human_resource":
                table = s3db.hrm_human_resource
                table.person_id.writable = table.person_id.readable = False
                table.site_id.readable = table.site_id.writable = True
                org = session.s3.hrm.org
                f = table.organisation_id
                if org is None:
                    f.widget = None
                else:
                    f.default = org
                    f.readable = f.writable = False
                    table.site_id.requires = IS_EMPTY_OR(
                        IS_ONE_OF(db,
                                  "org_site.%s" % s3db.super_key(db.org_site),
                                  s3db.org_site_represent,
                                  filterby="organisation_id",
                                  filter_opts=(session.s3.hrm.org,)))
            elif method == "private_contacts":
                # Flag to pass into s3db.pr_contacts()
                s3.pr_contacts = 1
            elif method == "public_contacts":
                # Flag to pass into s3db.pr_contacts()
                s3.pr_contacts = 2

            resource = r.resource
            if mode is not None:
                resource.build_query(id=auth.s3_logged_in_person())
            elif method not in ("deduplicate", "search_ac"):
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
                configure("hrm_human_resource", insertable = False)

        elif r.component_name == "group_membership" and r.representation == "aadata":
            hrm_configure_pr_group_membership()

        return True
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "human_resource":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_human_resource_start_date','hrm_human_resource_end_date')''')
            if r.component_name == "experience":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_experience_start_date','hrm_experience_end_date')''')
            elif r.component_name == "asset":
                # Provide a link to assign a new Asset
                # @ToDo: Proper Widget to do this inline
                output["add_btn"] = A(T("Assign Asset"),
                                      _href=URL(c="asset", f="asset"),
                                      _id="add-btn",
                                      _class="action-btn")
        return output
    s3.postp = postp

    # REST Interface
    if session.s3.hrm.orgname and mode is None:
        orgname = session.s3.hrm.orgname
    else:
        orgname = None

    _attr = dict(csv_stylesheet = ("hrm", "person.xsl"),
                 csv_template = "staff",
                 csv_extra_fields = [dict(label="Type",
                                          field=s3db.hrm_human_resource.type),
                                     ],
                 # Better in the native person controller (but this isn't always accessible):
                 #deduplicate = "",
                 orgname = orgname,
                 replace_option = T("Remove existing data before import"),
                 rheader = hrm_rheader,
                 )
    _attr.update(attr)

    output = current.rest_controller("pr", "person", **_attr)
    return output

# =============================================================================
def hrm_training_controller():
    """
        Training Controller, defined in the model for use from
        multiple controllers for unified menus
         - used for Searching for Participants
         - used for Adding/Editing on Profile page
    """

    if current.session.s3.hrm.mode is not None:
        current.session.error = current.T("Access denied")
        redirect(URL(f="index"))

    s3db = current.s3db

    def prep(r):
        if r.interactive or \
           r.extension == "aadata":
            # Suitable list_fields
            T = current.T
            list_fields = ["course_id",
                           "person_id",
                           (T("Job Title"), "job_title"),
                           (current.messages.ORGANISATION, "organisation"),
                           "date",
                           ]
            s3db.configure("hrm_training",
                           #insertable = False,
                           listadd = False,
                           list_fields = list_fields,
                           )

            if r.method in ("create", "create.popup", "update", "update.popup"):
                # Coming from Profile page?
                person_id = r.get_vars.get("~.person_id", None)
                if person_id:
                    field = s3db.hrm_training.person_id
                    field.default = person_id
                    field.readable = field.writable = False

            elif r.method == "report":
                s3db.configure("hrm_training",
                               extra_fields=["date"])
                table = s3db.hrm_training
                table.year = Field.Method("year", hrm_training_year)
                table.month = Field.Method("month", hrm_training_month)

            # @ToDo: Complete
            #elif r.method in ("import", "import.popup"):
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

        return True
    current.response.s3.prep = prep

    output = current.rest_controller("hrm", "training",
                                     csv_stylesheet = ("hrm", "training.xsl"),
                                     csv_template = ("hrm", "training"),
                                     csv_extra_fields=[dict(label="Training Event",
                                        field=s3db.hrm_training.training_event_id),
                                        ],
                                     )
    return output

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
           (r.interactive or \
            r.representation in ("aadata", "pdf", "xls")):

            T = current.T
            # Use appropriate CRUD strings
            s3.crud_strings["hrm_training"] = Storage(
                label_create = T("Add Participant"),
                title_display = T("Participant Details"),
                title_list = T("Participants"),
                title_update = T("Edit Participant"),
                title_upload = T("Import Participants"),
                label_list_button = T("List Participants"),
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
                                   list_fields = list_fields
                                   )
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_training_event_start_date','hrm_training_event_end_date')''')
            # @ToDo: Restore once the other part is working
            #elif r.component_name == "participant" and \
            #     isinstance(output, dict):
            #    showadd_btn = output.get("showadd_btn", None)
            #    if showadd_btn:
            #        # Add an Import button
            #        if s3.crud.formstyle == "bootstrap":
            #            _class = "s3_modal"
            #        else:
            #            _class = "action-btn s3_modal"
            #        import_btn = S3CRUD.crud_button(label=current.T("Import Participants"),
            #                                        _class=_class,
            #                                        _href=URL(f="training", args="import.popup",
            #                                                  vars={"~.training_event_id":r.id}),
            #                                        )
            #        output["showadd_btn"] = TAG[""](showadd_btn, import_btn)
        return output
    s3.postp = postp

    output = current.rest_controller("hrm", "training_event",
                                     rheader = hrm_rheader)
    return output

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

            profile_widgets = []
            form = self.form
            if form:
                if callable(form):
                    form = form(r)
                if form is not None:
                    profile_widgets.append(form)
            if vol and settings.get_hrm_use_awards():
                awards_widget = dict(label = "Awards",
                                     label_create = "Create Award",
                                     type = "datatable",
                                     actions = dt_row_actions("award"),
                                     tablename = "vol_volunteer_award",
                                     context = "person",
                                     create_controller = "vol",
                                     create_function = "person",
                                     create_component = "award",
                                     pagesize = None, # all records
                                     )
                profile_widgets.append(awards_widget)
            if settings.get_hrm_use_education():
                education_widget = dict(label = "Education",
                                        label_create = "Add Education",
                                        type = "datatable",
                                        actions = dt_row_actions("education"),
                                        tablename = "pr_education",
                                        context = "person",
                                        create_controller = controller,
                                        create_function = "person",
                                        create_component = "education",
                                        pagesize = None, # all records
                                        )
                profile_widgets.append(education_widget)
            if vol:
                vol_experience = settings.get_hrm_vol_experience()
                experience = vol_experience in ("both", "experience")
            else:
                experience = settings.get_hrm_staff_experience()
            if experience:
                experience_widget = dict(label = "Experience",
                                         label_create = "Add Experience",
                                         type = "datatable",
                                         actions = dt_row_actions("experience"),
                                         tablename = "hrm_experience",
                                         context = "person",
                                         create_controller = controller,
                                         create_function = "person",
                                         create_component = "experience",
                                         pagesize = None, # all records
                                         )
                profile_widgets.append(experience_widget)
            if settings.get_hrm_use_trainings():
                training_widget = dict(label = "Training",
                                       label_create = "Add Training",
                                       type = "datatable",
                                       actions = dt_row_actions("training"),
                                       tablename = "hrm_training",
                                       context = "person",
                                       create_controller = controller,
                                       create_function = "person",
                                       create_component = "training",
                                       pagesize = None, # all records
                                       )
                profile_widgets.append(training_widget)
            if settings.get_hrm_use_skills():
                skills_widget = dict(label = "Skills",
                                     label_create = "Create Skill",
                                     type = "datatable",
                                     actions = dt_row_actions("competency"),
                                     tablename = "hrm_competency",
                                     context = "person",
                                     create_controller = controller,
                                     create_function = "person",
                                     create_component = "competency",
                                     pagesize = None, # all records
                                     )
                profile_widgets.append(skills_widget)

            if r.representation == "html":
                response = current.response
                # Maintain normal rheader for consistency
                profile_header = TAG[""](H2(response.s3.crud_strings["pr_person"].title_display),
                                         DIV(hrm_rheader(r), _id="rheader"),
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
            raise HTTP(501, current.ERROR.BAD_METHOD)

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

        if r.name == "person" and r.id and not r.component and \
           r.representation in ("html", "aadata"):
            T = current.T
            s3db = current.s3db
            settings = current.deployment_settings
            tablename = r.tablename
            if r.controller == "vol":
                controller = "vol"
            else:
                controller = "hrm"

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

            if controller == "vol":
                label = "Volunteer Record"
            else:
                label = "Staff Record"

            table = s3db.hrm_human_resource
            profile_widgets = [
                dict(label = label,
                     type = "form",
                     tablename = "hrm_human_resource",
                     context = "person",
                     )
                ]

            if controller == "vol":
                vol_experience = settings.get_hrm_vol_experience()
                if vol_experience in ("programme", "both"):
                    # Exclude records which are just to link to Programme & also Training Hours
                    filter = (FS("hours") != None) & \
                             (FS("programme_id") != None)
                    list_fields = ["id",
                                   "date",
                                   "programme_id",
                                   ]
                    if s3db.hrm_programme_hours.job_title_id.readable:
                        list_fields.append("job_title_id")
                    list_fields.append("hours")
                    hours_widget = dict(label = "Program Hours",
                                        label_create = "Add Program Hours",
                                        type = "datatable",
                                        actions = dt_row_actions("hours"),
                                        tablename = "hrm_programme_hours",
                                        context = "person",
                                        filter = filter,
                                        list_fields = list_fields,
                                        create_controller = controller,
                                        create_function = "person",
                                        create_component = "hours",
                                        pagesize = None, # all records
                                        )
                    profile_widgets.append(hours_widget)

            teams = settings.get_hrm_teams()
            if teams:
                hrm_configure_pr_group_membership()
                if teams == "Teams":
                    label_create = "Add Team"
                elif teams == "Groups":
                    label_create = "Create Group"
                teams_widget = dict(label = teams,
                                    label_create = label_create,
                                    type = "datatable",
                                    actions = dt_row_actions("group_membership"),
                                    tablename = "pr_group_membership",
                                    context = "person",
                                    create_controller = controller,
                                    create_function = "person",
                                    create_component = "group_membership",
                                    pagesize = None, # all records
                                    )
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
                    widget = dict(label = T("Experience"),
                                  label_create = T("Add Experience"),
                                  type = "datatable",
                                  actions = experience_row_actions("experience"),
                                  tablename = "hrm_experience",
                                  pagesize = None, # all records
                                  )
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
                    widget = dict(label = "Experience",
                                  label_create = "Add Experience",
                                  type = "datatable",
                                  actions = dt_row_actions("experience"),
                                  tablename = "hrm_experience",
                                  context = "person",
                                  create_controller = controller,
                                  create_function = "person",
                                  create_component = "experience",
                                  pagesize = None, # all records
                                  )
                    if isinstance(other_experience, dict):
                        widget.update(other_experience)

                    profile_widgets.append(widget)

                if self.awards:
                    widget = dict(label = T("Awards"),
                                  label_create = T("Add Award"),
                                  type = "datatable",
                                  actions = dt_row_actions("staff_award"),
                                  tablename = "hrm_award",
                                  context = "person",
                                  create_controller = controller,
                                  create_function = "person",
                                  create_component = "staff_award",
                                  pagesize = None, # all records
                                  )
                    profile_widgets.append(widget)

                if self.disciplinary_record:
                    widget = dict(label = T("Disciplinary Record"),
                                  label_create = T("Add Disciplinary Action"),
                                  type = "datatable",
                                  actions = dt_row_actions("disciplinary_action"),
                                  tablename = "hrm_disciplinary_action",
                                  context = "person",
                                  create_controller = controller,
                                  create_function = "person",
                                  create_component = "disciplinary_action",
                                  pagesize = None, # all records
                                  )
                    profile_widgets.append(widget)

                if self.salary:
                    widget = dict(label = T("Salary"),
                                  label_create = T("Add Salary"),
                                  type = "datatable",
                                  actions = dt_row_actions("salary"),
                                  tablename = "hrm_salary",
                                  context = "person",
                                  create_controller = controller,
                                  create_function = "person",
                                  create_component = "salary",
                                  pagesize = None, # all records
                                  )
                    profile_widgets.append(widget)

            if r.representation == "html":
                # Maintain normal rheader for consistency
                response = current.response
                title = response.s3.crud_strings["pr_person"].title_display
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
            if r.representation == "html":
                output["title"] = response.title = title
            return output

        else:
            raise HTTP(501, current.ERROR.BAD_METHOD)

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
    return

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
        test = name_format % dict(first_name=1,
                                  middle_name=2,
                                  last_name=3,
                                  )
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
        organisation = P(I(_class="icon-sitemap"),
                         " ",
                         SPAN(A(record["hrm_competency.organisation_id"],
                                _href=org_url)
                              ),
                         " ",
                         _class="card_1_line",
                         )
    competency = raw["hrm_competency.competency_id"] or ""
    if competency:
        competency = P(I(_class="icon-certificate"),
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
        edit_btn = A(I(" ", _class="icon icon-edit"),
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
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(I(_class="icon"),
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
        date = P(I(_class="icon-calendar"),
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
        edit_btn = A(I(" ", _class="icon icon-edit"),
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
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(I(_class="icon"),
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

    card_line = lambda icon, item: P(I(" ", _class=icon),
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
        organisation = card_line("icon-sitemap", organisation)
    else:
        organisation = ""

    # Activity Type
    colname = "hrm_experience.activity_type"
    activity_type = raw[colname]
    if activity_type:
        activity_type = card_line("icon-tag", record[colname])
    else:
        activity_type = ""

    # Key Responsibilities
    colname = "hrm_experience.responsibilities"
    responsibilities = raw[colname]
    if responsibilities:
        responsibilities = card_line("icon-briefcase", record[colname])
    else:
        responsibilities = ""

    # Location
    colname = "hrm_experience.location_id"
    location_id = raw[colname]
    if location_id:
        #location_url = URL(c="gis", f="location", args=[location_id, "profile"])
        location_url = URL(c="gis", f="location", args=[location_id])
        location = card_line("icon-globe",
                             A(record[colname],
                               _href=location_url,
                               ),
                             )
    else:
        location = ""

    # Hours
    hours = raw["hrm_experience.hours"]
    if hours:
        hours = card_line("icon-time", hours)
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
        date = card_line("icon-calendar", dates)
    else:
        date = ""

    # Supervisor
    colname = "hrm_experience.supervisor_id"
    supervisor_id = raw[colname]
    if supervisor_id:
        #person_url = URL(c="hrm", f="person", args=[supervisor_id, "profile"])
        person_url = URL(c="hrm", f="person", args=[supervisor_id])
        supervisor = card_line("icon-user",
                               A(record[colname],
                                 _href=person_url,
                                 ),
                              )
    else:
        supervisor = ""

    # Comments
    comments = raw["hrm_experience.comments"] or ""

    # Job title as card title, indicate employment type if given
    colname = "hrm_experience.job_title_id"
    if raw[colname]:
        title = record[colname]
        job_title = card_line("icon-star", title)
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
        edit_btn = A(I(" ", _class="icon icon-edit"),
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
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(I(_class="icon"),
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
        date = P(I(_class="icon-calendar"),
                 " ",
                 SPAN(record["hrm_training.date"]),
                 " ",
                 _class="card_1_line",
                 )

    grade = raw["hrm_training.grade"] or ""
    if grade:
        grade = P(I(_class="icon-certificate"),
                  " ",
                  SPAN(record["hrm_training.grade"]),
                  " ",
                  _class="card_1_line",
                  )

    hours = raw["hrm_training.hours"] or ""
    if hours:
        hours = P(I(_class="icon-time"),
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
        site = P(I(_class="icon-home"),
                 " ",
                 SPAN(A(record["hrm_training_event.site_id"],
                        _href=site_url)
                      ),
                 " ",
                 _class="card_1_line",
                 )

    job_title = raw["hrm_course_job_title.job_title_id"] or ""
    if job_title:
        job_title = P(I(_class="icon-tags"),
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
        edit_btn = A(I(" ", _class="icon icon-edit"),
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
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(I(_class="icon"),
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
def hrm_human_resource_filters(resource_type=None,
                               module=None,
                               hrm_type_opts=None):
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
    s3 = current.response.s3
    settings = current.deployment_settings

    if not module:
        module = current.request.controller

    filter_widgets = [S3TextFilter(["person_id$first_name",
                                    "person_id$middle_name",
                                    "person_id$last_name",
                                    ],
                                   label = T("Search"),
                                   ),
                      ]
    append_filter = filter_widgets.append

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

    # Organisation filter (always)
    if settings.get_org_branches():
        append_filter(S3HierarchyFilter("organisation_id",
                                        leafonly = False,
                                        ))
    else:
        append_filter(S3OptionsFilter("organisation_id",
                                      filter = True,
                                      header = "",
                                      #hidden = True,
                                      ))

    # Location filter (always)
    append_filter(S3LocationFilter("location_id",
                                   label = T("Location"),
                                   hidden = True,
                                   ))

    # Active Filter / Programme filter (volunteer only)
    if module == "vol" or resource_type == "volunteer":
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
                                          options = lambda: \
                                            get_s3_filter_opts("hrm_programme",
                                                               org_filter=True),
                                          hidden = True,
                                          ))

    else:
        # Site filter (staff only)
        filter_widgets.append(S3OptionsFilter("site_id",
                                              hidden = True,
                                              ))

    if module == "deploy":
        # Deployment-specific filters

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

    # Training filter (always)
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
