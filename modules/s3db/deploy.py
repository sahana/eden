# -*- coding: utf-8 -*-

""" Sahana Eden Deployments Model

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

__all__ = ("S3DeploymentOrganisationModel",
           "S3DeploymentModel",
           "S3DeploymentAlertModel",
           "deploy_rheader",
           "deploy_apply",
           "deploy_alert_select_recipients",
           "deploy_Inbox",
           "deploy_response_select_mission",
           "deploy_availability_filter",
           )

from gluon import *
from gluon.tools import callback

from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class S3DeploymentOrganisationModel(S3Model):
    """
        Split into separate model to avoid circular deadlock in HRModel
    """

    names = ("deploy_organisation",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Organisation
        # - which Organisations/Branches have deployment teams
        #
        tablename = "deploy_organisation"
        self.define_table(tablename,
                          self.org_organisation_id(),
                          s3_comments(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3DeploymentModel(S3Model):

    names = ("deploy_mission",
             "deploy_mission_id",
             "deploy_mission_document",
             "deploy_mission_status_opts",
             "deploy_application",
             "deploy_assignment",
             "deploy_assignment_appraisal",
             "deploy_assignment_experience",
             "deploy_unavailability",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        human_resource_id = self.hrm_human_resource_id
        organisation_id = self.org_organisation_id

        # ---------------------------------------------------------------------
        # Mission
        #

        mission_status_opts = {1 : T("Closed"),
                               2 : T("Open"),
                               }

        tablename = "deploy_mission"
        define_table(tablename,
                     super_link("doc_id", "doc_entity"),
                     # Limit to deploy_organisation in template if-required
                     organisation_id(),
                     Field("name",
                           label = T("Name"),
                           represent = self.deploy_mission_name_represent,
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_date(default = "now",
                             ),
                     # @ToDo: Link to location via link table
                     # link table could be event_event_location for IFRC
                     # (would still allow 1 multi-country event to have multiple missions)
                     self.gis_location_id(widget = S3LocationSelector(),
                                          ),
                     # @ToDo: Link to event_type via event_id link table instead of duplicating
                     self.event_type_id(),
                     Field("code", length=24,
                           represent = lambda v: s3_unicode(v) if v else NONE,
                           requires = IS_LENGTH(24),
                           ),
                     Field("status", "integer",
                           default = 2,
                           label = T("Status"),
                           represent = lambda opt: \
                                       mission_status_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(mission_status_opts),
                           ),
                     # @todo: change into real fields written onaccept?
                     Field.Method("hrquantity",
                                  deploy_mission_hrquantity),
                     Field.Method("response_count",
                                  deploy_mission_response_count),
                     s3_comments(),
                     *s3_meta_fields())


        # Profile
        list_layout = deploy_MissionProfileLayout()

        hr_label = settings.get_deploy_hr_label()
        if hr_label == "Member":
            label = "Members Deployed"
            label_create = "Deploy New Member"
        elif hr_label == "Staff":
            label = "Staff Deployed"
            label_create = "Deploy New Staff"
        elif hr_label == "Volunteer":
            label = "Volunteers Deployed"
            label_create = "Deploy New Volunteer"

        assignment_widget = {"label": label,
                             "insert": lambda r, list_id, title, url: \
                                              A(title,
                                                _href=r.url(component = "assignment",
                                                            method = "create",
                                                            ),
                                                _class="action-btn profile-add-btn",
                                                ),
                             "label_create": label_create,
                             "tablename": "deploy_assignment",
                             "type": "datalist",
                             #"type": "datatable",
                             #"actions": dt_row_actions,
                             "list_fields": [
                                 "human_resource_id$id",
                                 "human_resource_id$person_id",
                                 "human_resource_id$organisation_id",
                                 "start_date",
                                 "end_date",
                                 "job_title_id",
                                 "job_title",
                                 "appraisal.rating",
                                 "mission_id",
                                 ],
                             "context": "mission",
                             "list_layout": list_layout,
                             "pagesize": None, # all records
                             }

        docs_widget = {"label": "Documents & Links",
                       "label_create": "Add New Document / Link",
                       "type": "datalist",
                       "tablename": "doc_document",
                       "context": ("~.doc_id", "doc_id"),
                       "icon": "attachment",
                       # Default renderer:
                       #"list_layout": s3db.doc_document_list_layouts,
                       }

        if settings.get_deploy_alerts():
            alert_widget = {"label": "Alerts",
                            "insert": lambda r, list_id, title, url: \
                                             A(title,
                                               _href = r.url(component = "alert",
                                                             method = "create"),
                                               _class = "action-btn profile-add-btn",
                                               ),
                            "label_create": "Create Alert",
                            "type": "datalist",
                            "list_fields": ["modified_on",
                                            "mission_id",
                                            "message_id",
                                            "subject",
                                            "body",
                                            ],
                            "tablename": "deploy_alert",
                            "context": "mission",
                            "list_layout": list_layout,
                            "pagesize": 10,
                            }

            response_widget = {"label": "Responses",
                               "insert": False,
                               "type": "datalist",
                               "tablename": "deploy_response",
                               # Can't be 'response' as this clobbers web2py global
                               "function": "response_message",
                               "list_fields": [
                                   "created_on",
                                   "mission_id",
                                   "comments",
                                   "human_resource_id$id",
                                   "human_resource_id$person_id",
                                   "human_resource_id$organisation_id",
                                   "message_id$body",
                                   "message_id$from_address",
                                   "message_id$attachment.document_id$file",
                                   ],
                               "context": "mission",
                               "list_layout": list_layout,
                               # The popup datalist isn't currently functional
                               # (needs card layout applying) and not ideal UX anyway
                               #"pagesize": 10,
                               "pagesize": None,
                               }

            profile_widgets = [alert_widget,
                               response_widget,
                               assignment_widget,
                               docs_widget,
                               ]
        else:
            profile_widgets = [assignment_widget,
                               docs_widget,
                               ]

        # Table configuration
        profile_url = URL(c="deploy", f="mission", args=["[id]", "profile"])
        configure(tablename,
                  create_next = profile_url,
                  create_onaccept = self.deploy_mission_create_onaccept,
                  delete_next = URL(c="deploy", f="mission", args="summary"),
                  list_fields = ["name",
                                 "date",
                                 "location_id",
                                 "event_type_id",
                                 "status",
                                 ],
                  orderby = "deploy_mission.date desc",
                  profile_cols = 1,
                  profile_header = lambda r: \
                                   deploy_rheader(r, profile=True),
                  profile_widgets = profile_widgets,
                  summary = [{"name": "rheader",
                              "common": True,
                              "widgets": [{"method": self.add_button},
                                          ],
                              },
                             {"name": "table",
                              "label": "Table",
                              "widgets": [{"method": "datatable"},
                                          ],
                              },
                             {"name": "report",
                              "label": "Report",
                              "widgets": [{"method": "report",
                                           "ajax_init": True,
                                           },
                                          ],
                              },
                             {"name": "map",
                              "label": "Map",
                              "widgets": [{"method": "map",
                                           "ajax_init": True,
                                           },
                                          ],
                              },
                             ],
                  super_entity = "doc_entity",
                  update_next = profile_url,
                  )

        # Components
        add_components(tablename,
                       deploy_assignment = "mission_id",
                       deploy_alert = "mission_id",
                       deploy_response = "mission_id",
                       )

        # CRUD Strings
        label_create = T("Create Mission")
        crud_strings[tablename] = Storage(
            label_create = label_create,
            title_display = T("Mission"),
            title_list = T("Missions"),
            title_update = T("Edit Mission Details"),
            title_upload = T("Import Missions"),
            label_list_button = T("List Missions"),
            label_delete_button = T("Delete Mission"),
            msg_record_created = T("Mission added"),
            msg_record_modified = T("Mission Details updated"),
            msg_record_deleted = T("Mission deleted"),
            msg_list_empty = T("No Missions currently registered"))

        # Reusable field
        represent = S3Represent(lookup = tablename,
                                linkto = URL(f="mission",
                                             args=["[id]", "profile"]),
                                show_link = True,
                                )

        mission_id = S3ReusableField("mission_id", "reference %s" % tablename,
                                     label = T("Mission"),
                                     ondelete = "CASCADE",
                                     represent = represent,
                                     requires = IS_ONE_OF(db,
                                                          "deploy_mission.id",
                                                          represent),
                                     comment = S3PopupLink(c = "deploy",
                                                           f = "mission",
                                                           label = label_create,
                                                           ),
                                     )

        # ---------------------------------------------------------------------
        # Link table to link documents to missions, responses or assignments
        #
        tablename = "deploy_mission_document"
        define_table(tablename,
                     mission_id(),
                     self.msg_message_id(),
                     self.doc_document_id(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Application of human resources
        # - agreement that an HR is available for assignments ('on the roster')
        #

        # Categories for IFRC AP region
        status_opts = \
            {1 : "I",   # Qualified RDRT team member and ready for deployment:Passed RDRT Induction training (and specialized training); assessed (including re-assessment after deployment) and recommended for deployment
             2 : "II",  # Passed RDRT Induction training; yet to deploy/assess
             3 : "III", # Passed RDRT Specialist training; did not pass/not yet taken RDRT Induction training
             4 : "IV",  # Attended RDRT Induction training, failed in assessment or re-assessment after deployment but still have potential for follow up training
             5 : "V",   # ERU trained personnel, requires RDRT Induction training
             }

        tablename = "deploy_application"
        define_table(tablename,
                     organisation_id(),
                     # @ToDo: This makes a lot more sense as person_id not human_resource_id
                     human_resource_id(empty = False,
                                       label = T(hr_label),
                                       ),
                     Field("active", "boolean",
                           default = True,
                           label = T("Roster Status"),
                           represent = lambda opt: T("active") if opt else T("inactive"),
                           ),
                     Field("status", "integer",
                           default = 5,
                           label = T("Category"),
                           represent = lambda opt: \
                                       status_opts.get(opt,
                                                       UNKNOWN_OPT),
                           requires = IS_IN_SET(status_opts),
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  delete_next = URL(c="deploy", f="human_resource", args="summary"),
                  )

        # ---------------------------------------------------------------------
        # Unavailability
        # - periods where an HR is not available for deployments
        #
        # @ToDo: Replace with pr_unavailability with "use_time": False
        #
        tablename = "deploy_unavailability"
        define_table(tablename,
                     self.pr_person_id(ondelete="CASCADE"),
                     s3_date("start_date",
                             label = T("Start Date"),
                             set_min = "#deploy_unavailability_end_date",
                             ),
                     s3_date("end_date",
                             label = T("End Date"),
                             set_max = "#deploy_unavailability_start_date",
                             ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table Configuration
        configure(tablename,
                  organize = {"start": "start_date",
                              "end": "end_date",
                              "title": "comments",
                              "description": ["start_date",
                                              "end_date",
                                              ],
                              },
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Period of Unavailability"),
            title_display = T("Unavailability"),
            title_list = T("Periods of Unavailability"),
            title_update = T("Edit Unavailability"),
            label_list_button = T("List Periods of Unavailability"),
            label_delete_button = T("Delete Unavailability"),
            msg_record_created = T("Unavailability added"),
            msg_record_modified = T("Unavailability updated"),
            msg_record_deleted = T("Unavailability deleted"),
            msg_list_empty = T("No Unavailability currently registered"))

        # ---------------------------------------------------------------------
        # Assignment of human resources
        # - actual assignment of an HR to a mission
        #
        tablename = "deploy_assignment"
        define_table(tablename,
                     mission_id(),
                     human_resource_id(empty = False,
                                       label = T(hr_label),
                                       ),
                     self.hrm_job_title_id(),
                     Field("job_title",
                           label = T("Position"),
                           ),
                     # These get copied to hrm_experience
                     # rest of fields may not be filled-out, but are in attachments
                     s3_date("start_date", # Only field visible when deploying from Mission profile
                             label = T("Start Date"),
                             ),
                     s3_date("end_date",
                             label = T("End Date"),
                             start_field = "deploy_assignment_start_date",
                             default_interval = 12,
                             ),
                     *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  context = {"mission": "mission_id",
                             },
                  onaccept = self.deploy_assignment_onaccept,
                  filter_widgets = [
                    S3TextFilter(["human_resource_id$person_id$first_name",
                                  "human_resource_id$person_id$middle_name",
                                  "human_resource_id$person_id$last_name",
                                  "mission_id$code",
                                  ],
                                 label = T("Search")
                                 ),
                    S3OptionsFilter("mission_id$event_type_id",
                                    widget = "multiselect",
                                    hidden = True,
                                    ),
                    S3LocationFilter("mission_id$location_id",
                                     label = messages.COUNTRY,
                                     widget = "multiselect",
                                     levels = ["L0"],
                                     hidden = True,
                                     ),
                    S3OptionsFilter("job_title_id",
                                    widget = "multiselect",
                                    hidden = True,
                                    ),
                    S3DateFilter("start_date",
                                 hide_time = True,
                                 hidden = True,
                                 ),
                    ],
                  summary = [
                    {"name": "table",
                     "label": "Table",
                     "widgets": [{"method": "datatable"},
                                 ],
                     },
                    {"name": "report",
                     "label": "Report",
                     "widgets": [{"method": "report",
                                  "ajax_init": True,
                                  },
                                 ]
                     },
                    ],
                  )

        # Components
        add_components(tablename,
                       hrm_appraisal = {"name": "appraisal",
                                        "link": "deploy_assignment_appraisal",
                                        "joinby": "assignment_id",
                                        "key": "appraisal_id",
                                        "autodelete": False,
                                        },
                       hrm_experience = {"name": "experience",
                                         "link": "deploy_assignment_experience",
                                         "joinby": "assignment_id",
                                         "key": "experience_id",
                                         "autodelete": False,
                                         },
                       )

        assignment_id = S3ReusableField("assignment_id",
                                        "reference %s" % tablename,
                                        ondelete = "CASCADE",
                                        )

        # ---------------------------------------------------------------------
        # Link Assignments to Appraisals
        #
        tablename = "deploy_assignment_appraisal"
        define_table(tablename,
                     assignment_id(empty = False),
                     Field("appraisal_id", self.hrm_appraisal),
                     *s3_meta_fields())

        configure(tablename,
                  ondelete_cascade = \
                    self.deploy_assignment_appraisal_ondelete_cascade,
                  )

        # ---------------------------------------------------------------------
        # Link Assignments to Experience
        #
        tablename = "deploy_assignment_experience"
        define_table(tablename,
                     assignment_id(empty = False),
                     Field("experience_id", self.hrm_experience),
                     *s3_meta_fields())

        configure(tablename,
                  ondelete_cascade = \
                    self.deploy_assignment_experience_ondelete_cascade,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"deploy_mission_id": mission_id,
                "deploy_mission_status_opts": mission_status_opts,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return {"deploy_mission_id": lambda **attr: dummy("mission_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def add_button(r, widget_id=None, visible=True, **attr):
        """
            @todo: docstring?
        """

        # Check permission only here, i.e. when the summary is
        # actually being rendered:
        if current.auth.s3_has_permission("create", r.tablename):
            return A(S3Method.crud_string(r.tablename, "label_create"),
                     _href = r.url(method="create", id=0, vars={}),
                     _class = "action-btn",
                     )
        else:
            return ""

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_mission_name_represent(name):
        """
            @todo: docstring?
        """

        table = current.s3db.deploy_mission
        mission = current.db(table.name == name).select(table.id,
                                                        limitby = (0, 1),
                                                        ).first()
        if not mission:
            return name

        return A(name,
                 _href=URL(c = "deploy",
                           f = "mission",
                           args = [mission.id, "profile"],
                           ),
                 )

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_mission_create_onaccept(form):
        """
            See if we can auto-populate the Date/Location/Event Type in imported records

            @param form: the form
        """

        if not current.response.s3.bulk:
            # Only relevant to imported records
            return

        # Load the complete record
        db = current.db
        s3db = current.s3db
        table = s3db.deploy_mission
        record = db(table.id == form.vars.id).select(table.id,
                                                     table.name,
                                                     #table.date,
                                                     table.location_id,
                                                     table.event_type_id,
                                                     limitby = (0, 1),
                                                     ).first()
        name = record.name
        if " " not in name:
            # Nothing we can do
            return

        location = record.name.split(" ", 1)[1]
        if " " in location:
            location, event_type = location.split(" ", 1)
        else:
            event_type = None

        update = {}

        # Not possible as date defaults :/
        #if not record.date:
        #    try:
        #        year = int(year)
        #    except:
        #        # Doesn't seem to be a year
        #        pass
        #    else:
        #        update["date"] = year

        if not record.location_id:
            gtable = s3db.gis_location
            matches = db(gtable.name == location).select(gtable.id)
            if len(matches) == 1:
                update["location_id"] = matches.first().id
            elif event_type and len(matches) == 0:
                matches = db(gtable.name == "%s %s" % (location, event_type)).select(gtable.id)
                if len(matches) == 1:
                    update["location_id"] = matches.first().id

        if event_type and not record.event_type_id:
            if event_type == "EQ":
                event_type = "Earthquake"
            elif event_type == "Flood":
                event_type = "Floods"
            etable = s3db.event_event_type
            event_type = db(etable.name == event_type).select(etable.id,
                                                              limitby=(0, 1)
                                                              ).first()
            if event_type:
                update["event_type_id"] = event_type.id

        if update:
            record.update_record(**update)

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_assignment_onaccept(form):
        """
            Create/update linked hrm_experience record for assignment

            @param form: the form
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars
        assignment_id = form_vars.id

        fields = ("human_resource_id",
                  "mission_id",
                  "job_title",
                  "job_title_id",
                  "start_date",
                  "end_date",
                  )

        if any(key not in form_vars for key in fields):
            # Need to reload the record
            atable = db.deploy_assignment
            query = (atable.id == assignment_id)
            qfields = [atable[f] for f in fields]
            row = db(query).select(limitby=(0, 1), *qfields).first()
            if row:
                data = dict((k, row[k]) for k in fields)
            else:
                # No such record
                return
        else:
            # Can use form vars
            data = dict((k, form_vars[k]) for k in fields)

        hr = mission = None

        # Lookup person details
        human_resource_id = data.pop("human_resource_id")
        if human_resource_id:
            hrtable = s3db.hrm_human_resource
            hr = db(hrtable.id == human_resource_id).select(hrtable.person_id,
                                                            hrtable.type,
                                                            limitby = (0, 1),
                                                            ).first()
            if hr:
                person_id = hr.person_id
                data["person_id"] = person_id
                data["employment_type"] = hr.type

                # Lookup User Account
                ltable = s3db.pr_person_user
                ptable = s3db.pr_person
                query = (ptable.id == person_id) & \
                        (ptable.pe_id == ltable.pe_id)
                link = db(query).select(ltable.user_id,
                                        limitby = (0, 1),
                                        ).first()
                if link:
                    data["owned_by_user"] = link.user_id

        # Lookup mission details
        mission_id = data.pop("mission_id")
        if mission_id:
            mtable = db.deploy_mission
            mission = db(mtable.id == mission_id).select(mtable.location_id,
                                                         mtable.organisation_id,
                                                         limitby = (0, 1),
                                                         ).first()
            if mission:
                data["location_id"] = mission.location_id
                data["organisation_id"] = mission.organisation_id

        if hr and mission:
            etable = s3db.hrm_experience

            # Lookup experience record for this assignment
            ltable = s3db.deploy_assignment_experience
            query = (ltable.assignment_id == assignment_id)
            link = db(query).select(ltable.experience_id,
                                    limitby = (0, 1),
                                    ).first()
            if link:
                # Update experience
                db(etable.id == link.experience_id).update(**data)
            else:
                # Create experience record
                experience_id = etable.insert(**data)

                # Create link
                ltable.insert(assignment_id = assignment_id,
                              experience_id = experience_id,
                              )
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_assignment_experience_ondelete_cascade(row, tablename=None):
        """
            Remove linked hrm_experience record

            @param row: the link to be deleted
            @param tablename: the tablename (ignored)
        """

        s3db = current.s3db

        # Lookup experience ID
        table = s3db.deploy_assignment_experience
        link = current.db(table.id == row.id).select(table.id,
                                                     table.experience_id,
                                                     limitby = (0, 1),
                                                     ).first()
        if not link:
            return
        else:
            # Prevent infinite cascade
            link.update_record(experience_id=None)

        s3db.resource("hrm_experience", id=link.experience_id).delete()

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_assignment_appraisal_ondelete_cascade(row, tablename=None):
        """
            Remove linked hrm_appraisal record

            @param row: the link to be deleted
            @param tablename: the tablename (ignored)
        """

        s3db = current.s3db

        # Lookup experience ID
        table = s3db.deploy_assignment_appraisal
        link = current.db(table.id == row.id).select(table.id,
                                                     table.appraisal_id,
                                                     limitby = (0, 1),
                                                     ).first()
        if not link:
            return
        else:
            # Prevent infinite cascade
            link.update_record(appraisal_id=None)

        s3db.resource("hrm_appraisal", id=link.appraisal_id).delete()

# =============================================================================
class S3DeploymentAlertModel(S3Model):

    names = ("deploy_alert",
             "deploy_alert_recipient",
             "deploy_response",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        NONE = current.messages["NONE"]

        human_resource_id = self.hrm_human_resource_id
        message_id = self.msg_message_id
        mission_id = self.deploy_mission_id

        hr_label = settings.get_deploy_hr_label()

        contact_method_opts = {1: T("Email"),
                               2: T("SMS"),
                               #3: T("Twitter"),
                               #9: T("All"),
                               9: T("Both"),
                               }

        # ---------------------------------------------------------------------
        # Alert
        # - also the PE representing its Recipients
        #
        cc_groups = settings.get_deploy_cc_groups()

        tablename = "deploy_alert"
        define_table(tablename,
                     self.super_link("pe_id", "pr_pentity"),
                     mission_id(
                        requires = IS_ONE_OF(db,
                                             "deploy_mission.id",
                                             S3Represent(lookup="deploy_mission"),
                                             filterby="status",
                                             filter_opts=(2,),
                                             ),
                        ),
                     human_resource_id(
                        label = T("Requesting Manager"),
                        widget = S3HumanResourceAutocompleteWidget(group="staff"),
                        ),
                     s3_date("date_requested",
                             default = "now",
                             label = T("Date Requested"),
                             ),
                     s3_date("expected_start_date",
                             label = T("Expected Start Date"),
                             ),
                     Field("contact_method", "integer",
                           default = 1,
                           label = T("Send By"),
                           represent = lambda opt: \
                            contact_method_opts.get(opt, NONE),
                           requires = IS_IN_SET(contact_method_opts),
                           ),
                     Field("cc", "boolean",
                           default = True,
                           # Define in template if-required
                           #label = T("cc: Group?"),
                           represent = s3_yes_no_represent,
                           readable = cc_groups,
                           writable = cc_groups,
                           ),
                     Field("subject", length=78,    # RFC 2822
                           label = T("Subject"),
                           # Not used by SMS
                           requires = IS_LENGTH(78),
                           ),
                     Field("body", "text",
                           label = T("Message"),
                           represent = lambda v: v or NONE,
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_date("date_alert_sent",
                             default = "now",
                             label = T("Date Alert Sent"),
                             ),
                     s3_date("date_cvs_sent",
                             label = T("Date CVs sent to DM"),
                             ),
                     s3_date("date_approval_meeting",
                             label = T("Date DM talked to President"),
                             ),
                     s3_date("date_approved",
                             label = T("Date President approved"),
                             ),
                     s3_date("date_selected",
                             label = T("Date Applicant selected"),
                             ),
                     # Link to the Message once sent
                     message_id(readable = False,
                                writable = False,
                                ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Alert"),
            title_display = T("Alert Details"),
            title_list = T("Alerts"),
            title_update = T("Edit Alert Details"),
            title_upload = T("Import Alerts"),
            label_list_button = T("List Alerts"),
            label_delete_button = T("Delete Alert"),
            msg_record_created = T("Alert added"),
            msg_record_modified = T("Alert Details updated"),
            msg_record_deleted = T("Alert deleted"),
            msg_list_empty = T("No Alerts currently registered"))

        # Table Configuration
        if settings.get_deploy_manual_recipients():
            alert_onaccept = None
        else:
            alert_onaccept = self.deploy_alert_onaccept
        configure(tablename,
                  context = {"mission": "mission_id"},
                  create_onaccept = alert_onaccept,
                  super_entity = "pr_pentity",
                  )

        # Components
        add_components(tablename,
                       deploy_alert_recipient = {"name": "recipient",
                                                 "joinby": "alert_id",
                                                 },
                       deploy_response = "alert_id",
                       hrm_human_resource = {"name": "select",
                                             "link": "deploy_alert_recipient",
                                             "joinby": "alert_id",
                                             "key": "human_resource_id",
                                             "autodelete": False,
                                             },
                       )

        # Custom method to send alerts
        self.set_method("deploy", "alert",
                        method = "send",
                        action = self.deploy_alert_send,
                        )

        # Reusable field
        represent = S3Represent(lookup=tablename)
        alert_id = S3ReusableField("alert_id", "reference %s" % tablename,
                                   label = T("Alert"),
                                   ondelete = "CASCADE",
                                   represent = represent,
                                   requires = IS_ONE_OF(db, "deploy_alert.id",
                                                        represent,
                                                        ),
                                   )

        # ---------------------------------------------------------------------
        # Recipients of the Alert
        #
        tablename = "deploy_alert_recipient"
        define_table(tablename,
                     alert_id(),
                     human_resource_id(empty = False,
                                       label = T(hr_label),
                                       ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Recipient"),
            title_display = T("Recipient Details"),
            title_list = T("Recipients"),
            title_update = T("Edit Recipient Details"),
            title_upload = T("Import Recipients"),
            label_list_button = T("List Recipients"),
            label_delete_button = T("Delete Recipient"),
            msg_record_created = T("Recipient added"),
            msg_record_modified = T("Recipient Details updated"),
            msg_record_deleted = T("Recipient removed"),
            msg_list_empty = T("No Recipients currently defined"))

        # ---------------------------------------------------------------------
        # Responses to Alerts
        #
        tablename = "deploy_response"
        define_table(tablename,
                     mission_id(),
                     alert_id(),
                     human_resource_id(
                        label = T(hr_label),
                        ),
                     message_id(label = T("Message"),
                                writable = False,
                                ),
                     # Filled-out by Applicant
                     Field("approval_status", "boolean",
                           label = T("Approved?"),
                           represent = s3_yes_no_represent,
                           ),
                     # Uploaded by Manager
                     Field("approval_letter", "upload",
                           label = T("Approval Letter"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        insertable = settings.get_deploy_responses_via_web()

        configure(tablename,
                  context = {"mission": "mission_id"},
                  #editable = insertable,
                  insertable = insertable,
                  update_onaccept = self.deploy_response_update_onaccept,
                  )

        NO_MESSAGES = T("No Messages found")
        crud_strings[tablename] = Storage(
            label_create = T("Apply"),
            title_display = T("Response Message"),
            title_list = T("Response Messages"),
            title_update = T("Edit Response Details"),
            label_list_button = T("All Response Messages"),
            label_delete_button = T("Delete Message"),
            msg_record_deleted = T("Message deleted"),
            msg_no_match = NO_MESSAGES,
            msg_list_empty = NO_MESSAGES,
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_alert_onaccept(form):
        """
            Add all Deployment Team members to the Recipients of the Alert
            - only runs if settings.deploy.manual_recipients is False
        """

        db = current.db
        s3db = current.s3db

        alert_id = form.vars.id

        # Find all Deployables
        atable = s3db.deploy_application
        query = (atable.active == True) & (atable.deleted == False)
        rows = db(query).select(atable.human_resource_id)

        # Add them to the Alert
        insert = s3db.deploy_alert_recipient.insert
        for row in rows:
            insert(alert_id = alert_id,
                   human_resource_id = row.human_resource_id,
                   )

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_alert_send(r, **attr):
        """
            Custom Method to send an Alert
        """

        alert_id = r.id
        if r.representation != "html" or not alert_id or r.component:
            r.error(405, current.ERROR.BAD_METHOD)

        auth = current.auth

        # Must have permission to update the alert in order to send it
        authorised = auth.s3_has_permission("update", "deploy_alert",
                                            record_id = alert_id,
                                            )
        if not authorised:
            r.unauthorised()

        record = r.record
        mission_id = record.mission_id

        # Always redirect to the Mission Profile
        next_url = URL(f="mission", args=[mission_id, "profile"])

        # Check whether the alert has already been sent
        # - alerts should be read-only after creation
        if record.message_id:
            current.session.error = current.T("This Alert has already been sent!")
            redirect(next_url)

        db = current.db
        s3db = current.s3db
        table = s3db.deploy_alert

        contact_method = record.contact_method

        # Check whether there are recipients
        ltable = db.deploy_alert_recipient
        query = (ltable.alert_id == alert_id) & \
                (ltable.deleted == False)
        if contact_method == 9:
            # Save a subsequent query
            recipients = db(query).select(ltable.human_resource_id)
        else:
            recipients = db(query).select(ltable.id,
                                          limitby = (0, 1),
                                          ).first()
        if not recipients:
            current.session.error = current.T("This Alert has no Recipients yet!")
            redirect(next_url)

        settings = current.deployment_settings

        # cc: list(s)
        if record.cc:
            cc_groups = settings.get_deploy_cc_groups()
            if cc_groups:
                # Lookup pe_ids
                gtable = s3db.pr_group
                cc_groups = db(gtable.name.belongs(cc_groups)).select(gtable.pe_id)
                cc_groups = [g.pe_id for g in cc_groups]
        else:
            cc_groups = []

        # Send Message
        message = record.body
        msg = current.msg

        if contact_method == 2:
            # Send SMS
            message_id = msg.send_by_pe_id(record.pe_id,
                                           contact_method = "SMS",
                                           message = message,
                                           )
            for g in cc_groups:
                msg.send_by_pe_id(g.pe_id,
                                  contact_method = "SMS",
                                  message = message,
                                  )

        elif contact_method == 9:
            # Send both
            # Create separate alert for this
            new_alert_id = table.insert(body = message,
                                        contact_method = 2,
                                        mission_id = mission_id,
                                        created_by = record.created_by,
                                        created_on = record.created_on,
                                        )
            new_alert = {"id": new_alert_id}
            s3db.update_super(table, new_alert)

            # Add Recipients
            for row in recipients:
                ltable.insert(alert_id = new_alert_id,
                              human_resource_id = row.human_resource_id,
                              )

            # Send SMS
            message_id = msg.send_by_pe_id(new_alert["pe_id"],
                                           contact_method = "SMS",
                                           message = message,
                                           )
            for g in cc_groups:
                msg.send_by_pe_id(g.pe_id,
                                  contact_method = "SMS",
                                  message = message,
                                  )

            # Update the Alert to show it's been Sent
            db(table.id == new_alert_id).update(message_id=message_id)

        if contact_method in (1, 9):
            # Send Email

            # Embed the mission_id to parse replies
            # = @ToDo: Use a Message Template to add Footer (very simple one for RDRT)
            message = "%s\n:mission_id:%s:" % (message, mission_id)

            # Lookup from_address
            organisation_id = auth.user.organisation_id
            ctable = s3db.msg_email_channel
            query = (ctable.deleted == False) & \
                    (ctable.enabled == True)
            if organisation_id:
                query &= ((ctable.organisation_id == None) | \
                          (ctable.organisation_id == organisation_id))
            channels = db(query).select(ctable.username,
                                        ctable.server,
                                        )
            if not channels:
                current.session.error = current.T("Need to configure an Email Address!")
                redirect(URL(f="email_channel"))
            elif organisation_id and len(channels) > 1:
                _channels = channels.find(lambda row: row.organisation_id == organisation_id)
                if not _channels:
                    _channels = channels.find(lambda row: row.organisation_id == None)
                channel = _channels.first()
            else:
                channel = channels.first()

            username = channel.username
            if "@" in username:
                from_address = username
            else:
                from_address = "%s@%s" % (username, channel.server)

            message_id = msg.send_by_pe_id(record.pe_id,
                                           subject = record.subject,
                                           message = message,
                                           from_address = from_address,
                                           )
            for g in cc_groups:
                msg.send_by_pe_id(g.pe_id,
                                  subject = record.subject,
                                  message = message,
                                  from_address = from_address,
                                  )

        if settings.get_deploy_post_to_twitter():
            # Post Alert to Twitter
            try:
                import tweepy
            except ImportError:
                current.log.debug("tweepy module needed for sending tweets")
            else:
                # @ToDo: Handle the multi-message nicely?
                try:
                    msg.send_tweet(text=message)
                except tweepy.error.TweepError as e:
                    current.log.debug("Sending tweets failed: %s" % e)

        # Update the Alert to show it's been Sent
        data = {"message_id": message_id}
        if contact_method == 2:
            # Clear the Subject
            data["subject"] = None
        elif contact_method == 9:
            # Also modify the contact_method to show that this is the email one
            data["contact_method"] = 1

        db(table.id == alert_id).update(**data)

        # Return to the Mission Profile
        current.session.confirmation = current.T("Alert Sent")
        redirect(next_url)

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_response_update_onaccept(form):
        """
            Update the doc_id in all attachments (doc_document) to the
            hrm_human_resource the response is linked to.

            @param form: the form
        """

        form_vars = form.vars
        if not form_vars or "id" not in form_vars:
            return

        db = current.db
        s3db = current.s3db

        # Get message ID and human resource ID
        if "human_resource_id" not in form_vars or \
           "message_id" not in form_vars:
            rtable = s3db.deploy_response
            response = db(rtable.id == form_vars.id).select(rtable.human_resource_id,
                                                            rtable.message_id,
                                                            limitby = (0, 1),
                                                            ).first()
            if not response:
                return
            human_resource_id = response.human_resource_id
            message_id = response.message_id
        else:
            human_resource_id = form_vars.human_resource_id
            message_id = form_vars.message_id

        # Update doc_id in all attachments (if any)
        dtable = s3db.doc_document
        ltable = s3db.deploy_mission_document
        query = (ltable.message_id == message_id) & \
                (dtable.id == ltable.document_id) & \
                (ltable.deleted == False) & \
                (dtable.deleted == False)
        attachments = db(query).select(dtable.id)
        if attachments:
            # Get the doc_id from the hrm_human_resource
            doc_id = None
            if human_resource_id:
                htable = s3db.hrm_human_resource
                hr = db(htable.id == human_resource_id).select(htable.doc_id,
                                                               limitby = (0, 1),
                                                               ).first()
                if hr:
                    doc_id = hr.doc_id
            db(dtable.id.belongs(attachments)).update(doc_id=doc_id)

# =============================================================================
def deploy_availability_filter(r):
    """
        Filter requested resource (hrm_human_resource or pr_person) for
        availability for deployment during a selected interval
            - uses special filter selector "available" from GET vars
            - called from prep of the respective controller
            - adds resource filter for r.resource

        @param r: the S3Request
    """

    get_vars = r.get_vars

    # Parse start/end date
    calendar = current.calendar
    start = get_vars.pop("available__ge", None)
    if start:
        start = calendar.parse_date(start)
    end = get_vars.pop("available__le", None)
    if end:
        end = calendar.parse_date(end)

    utable = current.s3db.deploy_unavailability

    # Construct query for unavailability
    query = (utable.deleted == False)
    if start and end:
        query &= ((utable.start_date >= start) & (utable.start_date <= end)) | \
                 ((utable.end_date >= start) & (utable.end_date <= end)) | \
                 ((utable.start_date < start) & (utable.end_date > end))
    elif start:
        query &= (utable.end_date >= start) | (utable.start_date >= start)
    elif end:
        query &= (utable.start_date <= end) | (utable.end_date <= end)
    else:
        return

    # Get person_ids of unavailability-entries
    rows = current.db(query).select(utable.person_id,
                                    groupby = utable.person_id,
                                    )
    if rows:
        person_ids = set(row.person_id for row in rows)

        # Filter r.resource for non-match
        if r.tablename == "hrm_human_resource":
            r.resource.add_filter(~(FS("person_id").belongs(person_ids)))
        elif r.tablename == "pr_person":
            r.resource.add_filter(~(FS("id").belongs(person_ids)))

# =============================================================================
def deploy_rheader(r, tabs=None, profile=False):
    """ Deployment Resource Headers """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    record = r.record
    if not record:
        # List or Create form: rheader makes no sense here
        return None

    settings = current.deployment_settings
    has_permission = current.auth.s3_has_permission
    T = current.T

    table = r.table
    tablename = r.tablename

    rheader = None

    resourcename = r.name

    if resourcename == "alert":
        alert_id = r.id
        db = current.db
        ltable = db.deploy_alert_recipient
        query = (ltable.alert_id == alert_id) & \
                (ltable.deleted == False)
        recipients = db(query).count()

        unsent = not r.record.message_id
        authorised = has_permission("update", tablename, record_id=alert_id)

        if unsent and authorised:
            send_button = BUTTON(T("Send Alert"), _class="alert-send-btn")
            if recipients:
                send_button.update(_onclick = "window.location.href='%s'" %
                                              URL(c = "deploy",
                                                  f = "alert",
                                                  args = [alert_id, "send"],
                                                  ),
                                   )
            else:
                send_button.update(_disabled="disabled")
        else:
            send_button = ""

        if settings.get_deploy_cc_groups():
            cc = TR(TH("%s: " % table.cc.label),
                    s3_yes_no_represent(record.cc),
                    )
        else:
            cc = ""

        # Tabs
        tabs = [(T("Message"), None),
                (T("Recipients (%(number)s Total)") % \
                    {"number": recipients},
                 "recipient",
                 ),
                ]
        if unsent and authorised and settings.get_deploy_manual_recipients():
            # Insert tab to select recipients
            tabs.insert(1, (T("Select Recipients"), "select"))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(TR(TH("%s: " % table.mission_id.label),
                               table.mission_id.represent(record.mission_id),
                               send_button,
                               ),
                            TR(TH("%s: " % table.subject.label),
                               record.subject
                               ),
                            cc,
                            ),
                      rheader_tabs,
                      _class = "alert-rheader",
                      )

    elif resourcename == "mission":
        if not profile and not r.component:
            rheader = ""
        else:
            crud_string = S3Method.crud_string
            record = r.record
            title = crud_string(r.tablename, "title_display")
            if record:
                title = "%s: %s" % (title, record.name)
                edit_btn = ""
                if profile and has_permission("update",
                                              "deploy_mission",
                                              record_id = r.id,
                                              ):
                    crud_button = S3CRUD.crud_button
                    edit_btn = crud_button(T("Edit"),
                                           _href = r.url(method="update"),
                                           )

                label = lambda f, table=table, record=record, **attr: \
                               TH("%s: " % table[f].label, **attr)
                value = lambda f, table=table, record=record, **attr: \
                               TD(table[f].represent(record[f]), **attr)
                if settings.has_module("event"):
                    row1 = TR(label("event_type_id"),
                              value("event_type_id"),
                              label("location_id"),
                              value("location_id"),
                              label("code"),
                              value("code"),
                              )
                else:
                    row1 = TR(label("location_id"),
                              value("location_id"),
                              label("code"),
                              value("code"),
                              )
                rheader = DIV(H2(title),
                              TABLE(row1,
                                    TR(label("date"),
                                       value("date"),
                                       label("status"),
                                       value("status"),
                                       ),
                                    TR(label("comments"),
                                       value("comments",
                                             _class = "mission-comments",
                                             _colspan = "6",
                                             ),
                                       ),
                                    ),
                              _class = "mission-rheader"
                              )
                if edit_btn:
                    rheader[-1][0].append(edit_btn)
            else:
                rheader = H2(title)

    return rheader

# =============================================================================
def deploy_mission_hrquantity(row):
    """ Number of human resources deployed """

    if hasattr(row, "deploy_mission"):
        row = row.deploy_mission
    try:
        mission_id = row.id
    except AttributeError:
        return 0

    db = current.db
    table = db.deploy_assignment
    count = table.id.count()
    row = db(table.mission_id == mission_id).select(count).first()
    if row:
        return row[count]
    else:
        return 0

# =============================================================================
def deploy_mission_response_count(row):
    """ Number of responses to a mission """

    if hasattr(row, "deploy_mission"):
        row = row.deploy_mission
    try:
        mission_id = row.id
    except AttributeError:
        return 0

    table = current.s3db.deploy_response
    count = table.id.count()
    row = current.db(table.mission_id == mission_id).select(count).first()
    if row:
        return row[count]
    else:
        return 0

# =============================================================================
def deploy_member_filters(status=False):
    """
        Filter widgets for members (hrm_human_resource), used in
        custom methods for member selection, e.g. deploy_apply
        or deploy_alert_select_recipients
    """

    T = current.T
    widgets = [S3TextFilter(["person_id$first_name",
                             "person_id$middle_name",
                             "person_id$last_name",
                             ],
                            label = T("Name"),
                            ),
               S3OptionsFilter("organisation_id",
                               search = True,
                               hidden = True,
                               ),
               S3OptionsFilter("credential.job_title_id",
                               # @ToDo: Label setting
                               label = T("Sector"),
                               hidden = True,
                               ),
               ]

    settings = current.deployment_settings
    if settings.get_hrm_teams():
        widgets.append(S3OptionsFilter("group_membership.group_id",
                                       label = T("Teams"),
                                       hidden = True,
                                       ))

    if settings.get_org_regions():
        if settings.get_org_regions_hierarchical():
            widgets.insert(1, S3HierarchyFilter("organisation_id$region_id",
                                                lookup = "org_region",
                                                hidden = True,
                                                none = T("No Region"),
                                                ))
        else:
            widgets.insert(1, S3OptionsFilter("organisation_id$region_id",
                                              widget = "multiselect",
                                              search = True,
                                              ))
    if status:
        # Additional filter for roster status (default=active), allows
        # to explicitly include inactive roster members when selecting
        # alert recipients (only used there)
        widgets.insert(1, S3OptionsFilter("application.active",
                                          cols = 2,
                                          default = True,
                                          # Don't hide otherwise default
                                          # doesn't apply:
                                          #hidden = False,
                                          label = T("Status"),
                                          options = {"True": T("active"),
                                                     "False": T("inactive"),
                                                     },
                                          ))

        if settings.get_deploy_select_ratings():
            rating_opts = {1: 1,
                           2: 2,
                           3: 3,
                           4: 4,
                           }
            widgets.extend((S3OptionsFilter("application.status",
                                            label = T("Category"),
                                            options = {1: "I",
                                                       2: "II",
                                                       3: "III",
                                                       4: "IV",
                                                       5: "V",
                                                       },
                                            cols = 5,
                                            ),
                            S3OptionsFilter("training.grade",
                                            label = T("Training Grade"),
                                            options = rating_opts,
                                            cols = 4,
                                            ),
                            S3OptionsFilter("appraisal.rating",
                                            label = T("Deployment Rating"),
                                            options = rating_opts,
                                            cols = 4,
                                            ),
                            ))

    return widgets

# =============================================================================
class deploy_Inbox(S3Method):

    def apply_method(self, r, **attr):
        """
            Custom method for email inbox, provides a datatable with bulk-delete
            option

            @param r: the S3Request
            @param attr: the controller attributes
        """

        T = current.T
        s3db = current.s3db

        response = current.response
        s3 = response.s3

        resource = self.resource
        if r.http == "POST":

            deleted = 0
            post_vars = r.post_vars

            if all([n in post_vars for n in ("delete", "selected", "mode")]):
                selected = post_vars.selected
                if selected:
                    selected = selected.split(",")
                else:
                    selected = []

                if selected:
                    # Handle exclusion filter
                    if post_vars.mode == "Exclusive":
                        if "filterURL" in post_vars:
                            filters = S3URLQuery.parse_url(post_vars.ajaxURL)
                        else:
                            filters = None
                        query = ~(FS("id").belongs(selected))
                        mresource = s3db.resource("msg_email",
                                                  filter = query,
                                                  vars = filters,
                                                  )
                        if response.s3.filter:
                            mresource.add_filter(response.s3.filter)
                        rows = mresource.select(["id"], as_rows=True)
                        selected = [str(row.id) for row in rows]
                    query = (FS("id").belongs(selected))
                    mresource = s3db.resource("msg_email", filter=query)
                else:
                    mresource = resource

                # Delete the messages
                deleted = mresource.delete(format=r.representation)
                if deleted:
                    response.confirmation = T("%(number)s messages deleted") % \
                                            {"number": deleted}
                else:
                    response.warning = T("No messages could be deleted")

        # List fields
        list_fields = ["id",
                       "date",
                       "from_address",
                       "subject",
                       "body",
                       (T("Attachments"), "attachment.document_id"),
                       ]

        # Truncate message body
        table = resource.table
        table.body.represent = lambda body: DIV(XML(body),
                                                _class = "s3-truncate",
                                                )
        s3_trunk8()

        # Data table filter & sorting
        get_vars = r.get_vars
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
        dtfilter, orderby, left = resource.datatable_filter(list_fields,
                                                            get_vars,
                                                            )
        if not orderby:
            # Most recent messages on top
            orderby = "msg_email.date desc"
        resource.add_filter(dtfilter)

        # Extract the data
        data = resource.select(list_fields,
                               start = 0,
                               limit = limit,
                               orderby = orderby,
                               left = left,
                               count = True,
                               represent = True,
                               )

        # Instantiate the data table
        filteredrows = data["numrows"]
        dt = S3DataTable(data["rfields"], data["rows"], orderby=orderby)
        dt_id = "datatable"

        # Bulk actions
        # @todo: user confirmation
        dt_bulk_actions = [(T("Delete"), "delete")]

        if r.representation == "html":
            # Action buttons
            s3.actions = [{"label": str(T("Link to Mission")),
                           "_class": "action-btn link",
                           "url": URL(f="email_inbox", args=["[id]", "select"]),
                           },
                          ]
            S3CRUD.action_buttons(r,
                                  editable = False,
                                  read_url = r.url(method = "read",
                                                   id = "[id]",
                                                   ),
                                  delete_url = r.url(method = "delete",
                                                     id = "[id]",
                                                     ),
                                  )

            # Export not needed
            s3.no_formats = True

            # Render data table
            items = dt.html(totalrows,
                            filteredrows,
                            dt_id,
                            dt_ajax_url= URL(c = "deploy",
                                             f = "email_inbox",
                                             extension = "aadata",
                                             vars = {},
                                             ),
                            dt_bulk_actions = dt_bulk_actions,
                            dt_pageLength = display_length,
                            dt_pagination = "true",
                            dt_searching = "true",
                            )

            response.view = "list_filter.html"
            return {"items": items,
                    "title": S3CRUD.crud_string(resource.tablename, "title_list"),
                    }

        elif r.representation == "aadata":
            # Ajax refresh
            draw = int(get_vars.draw) if "draw" in get_vars else None

            response = current.response
            response.headers["Content-Type"] = "application/json"

            return dt.json(totalrows,
                           filteredrows,
                           dt_id,
                           draw,
                           dt_bulk_actions = dt_bulk_actions,
                           )

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

# =============================================================================
def deploy_apply(r, **attr):
    """
        Custom method to select new Deployables (e.g. RDRT/RIT Members)

        @todo: make workflow re-usable for manual assignments
    """

    # Requires permission to create deploy_application
    authorised = current.auth.s3_has_permission("create", "deploy_application")
    if not authorised:
        r.unauthorised()

    T = current.T
    db = current.db
    auth = current.auth
    s3db = current.s3db

    get_vars = r.get_vars
    response = current.response
    s3 = response.s3
    settings = current.deployment_settings

    deploy_team = settings.get_deploy_team_label()

    otable = s3db.org_organisation
    dotable = s3db.deploy_organisation
    query = (dotable.deleted == False) & \
            (dotable.organisation_id == otable.id)
    deploying_orgs = db(query).select(otable.id,
                                      otable.name,
                                      )
    deploying_orgs = dict([(o.id, o.name) for o in deploying_orgs])

    is_admin = auth.s3_has_role("ADMIN")
    organisation_id = auth.user.organisation_id

    if not is_admin and organisation_id in deploying_orgs:
        # Default to this organisation_id
        pass
    else:
        # Manually choose the Deployment Organisation (or leave unset)
        organisation_id = None

    if r.http == "POST":
        added = 0
        post_vars = r.post_vars
        if all([n in post_vars for n in ("add", "selected", "mode")]):
            selected = post_vars.selected
            if selected:
                selected = selected.split(",")
            else:
                selected = []

            atable = s3db.deploy_application
            if selected:
                # Handle exclusion filter
                if post_vars.mode == "Exclusive":
                    if "filterURL" in post_vars:
                        filters = S3URLQuery.parse_url(post_vars.ajaxURL)
                    else:
                        filters = None
                    query = ~(FS("id").belongs(selected))
                    hresource = s3db.resource("hrm_human_resource",
                                              filter = query,
                                              vars = filters,
                                              )
                    rows = hresource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

                if not organisation_id:
                    organisation_id = post_vars.get("organisation_id")

                query = (atable.human_resource_id.belongs(selected)) & \
                        (atable.deleted != True)
                rows = db(query).select(atable.id,
                                        atable.active)
                rows = dict((row.id, row) for row in rows)
                # onaccept is undefined in the default config
                # but can be defined in templates, e.g. RMS Americas
                # We are running in the hrm_human_resource controller so customise the deploy_application resource
                tablename = "deploy_application"
                r.customise_resource(tablename)
                onaccept = s3db.get_config(tablename, "create_onaccept",
                                s3db.get_config(tablename, "onaccept", None))
                for human_resource_id in selected:
                    try:
                        hr_id = int(human_resource_id.strip())
                    except ValueError:
                        continue
                    if hr_id in rows:
                        row = rows[hr_id]
                        if not row.active:
                            row.update_record(active=True)
                            added += 1
                    else:
                        data = {"organisation_id": organisation_id,
                                "human_resource_id": hr_id,
                                "active": True,
                                }
                        application_id = atable.insert(**data)
                        if onaccept:
                            data["id"] = application_id
                            form = Storage(vars = data)
                            callback(onaccept, form, tablename=tablename)
                        added += 1
        current.session.confirmation = T("%(number)s %(team)s members added") % \
                                       {"number": added,
                                        "team": T(deploy_team),
                                        }
        if added > 0:
            redirect(URL(f="human_resource", args=["summary"], vars={}))
        else:
            redirect(URL(f="application", vars={}))

    elif r.http == "GET":

        # Filter widgets
        filter_widgets = settings.get_deploy_member_filters() or \
                         deploy_member_filters()

        # List fields
        list_fields = ["id",
                       "person_id",
                       "job_title_id",
                       "organisation_id",
                       ]

        # Data table
        resource = r.resource
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
        # Sorting by person_id requires introspection => use datatable_filter
        if r.representation != "aadata":
            get_vars = dict(get_vars)
            dt_sorting = {"iSortingCols": "1",
                          "bSortable_0": "false",
                          "iSortCol_0": "1",
                          "sSortDir_0": "asc",
                          }
            get_vars.update(dt_sorting)
        filter_, orderby, left = resource.datatable_filter(list_fields,
                                                           get_vars)
        resource.add_filter(filter_)
        data = resource.select(list_fields,
                               start = 0,
                               limit = limit,
                               orderby = orderby,
                               left = left,
                               count = True,
                               represent = True,
                               )
        filteredrows = data.numrows
        dt = S3DataTable(data.rfields, data.rows, orderby=orderby)
        dt_id = "datatable"

        # Bulk actions
        dt_bulk_actions = [(T("Add as %(team)s Members") % \
                            {"team": T(deploy_team)},
                            "add"
                            ),
                           ]

        if r.representation == "html":
            # Page load
            resource.configure(deletable = False)

            #dt.defaultActionButtons(resource)
            profile_url = URL(f = "human_resource",
                              args = ["[id]", "profile"],
                              )
            S3CRUD.action_buttons(r,
                                  deletable = False,
                                  read_url = profile_url,
                                  update_url = profile_url,
                                  )
            s3.no_formats = True

            # Selection of Deploying Organisation
            if not organisation_id and len(deploying_orgs) > 1:
                opts = [OPTION(v, _value=k)
                        for k, v in deploying_orgs.items()
                        ]
                form = SELECT(_id = "deploy_application_organisation_id",
                              _name = "organisation_id",
                              *opts)
                s3.scripts.append("/%s/static/scripts/S3/s3.deploy.js" % r.application)
            else:
                form = ""

            # Data table (items)
            items = dt.html(totalrows,
                            filteredrows,
                            dt_id,
                            dt_pageLength = display_length,
                            dt_ajax_url = URL(c = "deploy",
                                              f = "application",
                                              extension = "aadata",
                                              vars = {},
                                              ),
                            dt_searching = "false",
                            dt_pagination = "true",
                            dt_bulk_actions = dt_bulk_actions,
                            )

            # Filter form
            if filter_widgets:

                # Where to retrieve filtered data from:
                submit_url_vars = resource.crud._remove_filters(r.get_vars)
                filter_submit_url = r.url(vars=submit_url_vars)

                # Where to retrieve updated filter options from:
                filter_ajax_url = URL(f = "human_resource",
                                      args = ["filter.options"],
                                      vars = {},
                                      )

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
                fresource = s3db.resource(resource.tablename)
                alias = resource.alias if r.component else None
                ff = filter_form.html(fresource,
                                      r.get_vars,
                                      target = "datatable",
                                      alias = alias,
                                      )
            else:
                ff = ""

            response.view = "list_filter.html"

            return {"form": form,
                    "items": items,
                    "list_filter_form": ff,
                    "title": T("Add %(team)s Members") % \
                              {"team": T(deploy_team)},
                    }

        elif r.representation == "aadata":
            # Ajax refresh
            if "draw" in get_vars:
                draw = int(get_vars.draw)
            else:
                draw = None
            items = dt.json(totalrows,
                            filteredrows,
                            dt_id,
                            draw,
                            dt_bulk_actions = dt_bulk_actions,
                            )
            response.headers["Content-Type"] = "application/json"
            return items

        else:
            r.error(415, current.ERROR.BAD_FORMAT)
    else:
        r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
def deploy_alert_select_recipients(r, **attr):
    """
        Custom method to select Recipients for an Alert
    """

    alert_id = r.id
    if r.representation not in ("html", "aadata") or \
       not alert_id or \
       not r.component:
        r.error(405, current.ERROR.BAD_METHOD)

    # Must have permission to update the alert in order to add recipients
    authorised = current.auth.s3_has_permission("update", "deploy_alert",
                                                record_id = alert_id,
                                                )
    if not authorised:
        r.unauthorised()

    T = current.T
    s3db = current.s3db
    response = current.response
    s3 = response.s3

    member_query = s3.member_query or (FS("application.active") != None)

    if r.http == "POST":

        added = 0
        post_vars = r.post_vars
        if all([n in post_vars for n in ("select", "selected", "mode")]):
            selected = post_vars.selected
            if selected:
                selected = selected.split(",")
            else:
                selected = []

            db = current.db
            # Handle exclusion filter
            if post_vars.mode == "Exclusive":
                if "filterURL" in post_vars:
                    filters = S3URLQuery.parse_url(post_vars.filterURL)
                else:
                    filters = None
                query = member_query & \
                        (~(FS("id").belongs(selected)))

                hresource = s3db.resource("hrm_human_resource",
                                          filter = query,
                                          vars = filters,
                                          )
                rows = hresource.select(["id"], as_rows=True)
                selected = [str(row.id) for row in rows]

            rtable = s3db.deploy_alert_recipient
            query = (rtable.alert_id == alert_id) & \
                    (rtable.human_resource_id.belongs(selected)) & \
                    (rtable.deleted != True)
            rows = db(query).select(rtable.human_resource_id)
            skip = set(row.human_resource_id for row in rows)

            for human_resource_id in selected:
                try:
                    hr_id = int(human_resource_id.strip())
                except ValueError:
                    continue
                if hr_id in skip:
                    continue
                rtable.insert(alert_id = alert_id,
                              human_resource_id = human_resource_id,
                              )
                added += 1
        if not selected:
            response.warning = T("No Recipients Selected!")
        else:
            response.confirmation = T("%(number)s Recipients added to Alert") % \
                                        {"number": added}

    get_vars = r.get_vars or {}
    representation = r.representation
    resource = s3db.resource("hrm_human_resource",
                             filter = member_query,
                             vars = r.get_vars,
                             )

    # Filter widgets (including roster status)
    filter_widgets = current.deployment_settings.get_deploy_member_filters() or \
                     deploy_member_filters(status=True)

    if filter_widgets and representation == "html":
        # Apply filter defaults
        resource.configure(filter_widgets = filter_widgets)
        S3FilterForm.apply_filter_defaults(r, resource)

    # List fields
    list_fields = ["id",
                   "person_id",
                   "job_title_id",
                   "organisation_id",
                   ]

    # Data table
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
    # Sorting by person_id requires introspection => use datatable_filter
    if r.representation != "aadata":
        get_vars = dict(get_vars)
        dt_sorting = {"iSortingCols": "1",
                      "bSortable_0": "false",
                      "iSortCol_0": "1",
                      "sSortDir_0": "desc",
                      }
        get_vars.update(dt_sorting)
    dtfilter, orderby, left = resource.datatable_filter(list_fields, get_vars)
    resource.add_filter(dtfilter)
    resource.add_filter(s3.filter)
    data = resource.select(list_fields,
                           start = 0,
                           limit = limit,
                           orderby = orderby,
                           left = left,
                           count = True,
                           represent = True,
                           )

    filteredrows = data.numrows
    dt = S3DataTable(data.rfields, data.rows, orderby=orderby)
    dt_id = "datatable"

    # Bulk actions
    dt_bulk_actions = [(T("Select as Recipients"), "select")]

    if representation == "html":
        # Page load
        resource.configure(deletable = False)

        #dt.defaultActionButtons(resource)
        s3.no_formats = True

        # Data table (items)
        items = dt.html(totalrows,
                        filteredrows,
                        dt_id,
                        dt_ajax_url = r.url(representation="aadata"),
                        dt_bulk_actions = dt_bulk_actions,
                        dt_pageLength = display_length,
                        dt_pagination = "true",
                        dt_searching = "false",
                        )

        # Filter form
        if filter_widgets:

            # Where to retrieve filtered data from:
            _vars = resource.crud._remove_filters(r.get_vars)
            filter_submit_url = r.url(vars=_vars)

            # Where to retrieve updated filter options from:
            filter_ajax_url = URL(f = "human_resource",
                                  args = ["filter.options"],
                                  vars = {},
                                  )

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
            fresource = s3db.resource(resource.tablename)
            alias = resource.alias if r.component else None
            ff = filter_form.html(fresource,
                                  r.get_vars,
                                  target = "datatable",
                                  alias = alias,
                                  )
        else:
            ff = ""

        output = {"items": items,
                  "title": T("Select Recipients"),
                  "list_filter_form": ff,
                  }

        # Maintain RHeader for consistency
        if attr.get("rheader"):
            rheader = attr["rheader"](r)
            if rheader:
                output["rheader"] = rheader

        response.view = "list_filter.html"
        return output

    elif representation == "aadata":
        # Ajax refresh
        if "draw" in get_vars:
            draw = int(get_vars.draw)
        else:
            draw = None
        items = dt.json(totalrows,
                        filteredrows,
                        dt_id,
                        draw,
                        dt_bulk_actions = dt_bulk_actions,
                        )
        response.headers["Content-Type"] = "application/json"
        return items

    else:
        r.error(415, current.ERROR.BAD_FORMAT)

# =============================================================================
def deploy_response_select_mission(r, **attr):
    """
        Custom method to Link a Response to a Mission &/or Human Resource
    """

    message_id = r.record.message_id if r.record else None

    if r.representation not in ("html", "aadata") or \
       not message_id or \
       not r.component:
        r.error(405, current.ERROR.BAD_METHOD)

    T = current.T
    db = current.db
    s3db = current.s3db

    atable = s3db.msg_attachment
    dtable = db.doc_document
    query = (atable.message_id == message_id) & \
            (atable.document_id == dtable.id)
    atts = db(query).select(dtable.id,
                            dtable.file,
                            dtable.name,
                            )

    response = current.response
    mission_query = FS("mission.status") == 2

    get_vars = r.get_vars or {}
    mission_id = get_vars.get("mission_id", None)
    if mission_id:
        hr_id = get_vars.get("hr_id", None)
        if not hr_id:
            # @ToDo: deployment_setting for 'Member' label
            current.session.warning = T("No Member Selected!")
            # Can still link to the mission, member can be set
            # manually in the mission profile
            s3db.deploy_response.insert(message_id = message_id,
                                        mission_id = mission_id,
                                        )
        else:
            s3db.deploy_response.insert(message_id = message_id,
                                        mission_id = mission_id,
                                        human_resource_id = hr_id,
                                        )
        # Are there any attachments?
        if atts:
            ltable = s3db.deploy_mission_document
            if hr_id:
                # Set documents to the Member's doc_id
                hrtable = s3db.hrm_human_resource
                doc_id = db(hrtable.id == hr_id).select(hrtable.doc_id,
                                                        limitby=(0, 1)
                                                        ).first().doc_id
            for a in atts:
                # Link to Mission
                document_id = a.id
                ltable.insert(mission_id = mission_id,
                              message_id = message_id,
                              document_id = document_id)
                if hr_id:
                    db(dtable.id == document_id).update(doc_id = doc_id)

        #mission = XML(A(T("Mission"),
        #                _href=URL(c="deploy", f="mission",
        #                          args=[mission_id, "profile"])))
        #current.session.confirmation = T("Response linked to %(mission)s") % \
        #                                    {"mission": mission}
        current.session.confirmation = T("Response linked to Mission")
        redirect(URL(c="deploy", f="email_inbox"))

    resource = s3db.resource("deploy_mission",
                             filter = mission_query,
                             vars = get_vars,
                             )

    # Filter widgets
    filter_widgets = s3db.get_config("deploy_mission", "filter_widgets")

    # List fields
    list_fields = s3db.get_config("deploy_mission", "list_fields")
    list_fields.insert(0, "id")

    # Data table
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
    dtfilter, orderby, left = resource.datatable_filter(list_fields, get_vars)
    if not orderby:
        # Most recent missions on top
        orderby = "deploy_mission.created_on desc"
    resource.add_filter(dtfilter)
    data = resource.select(list_fields,
                           start = 0,
                           limit = limit,
                           orderby = orderby,
                           left = left,
                           count = True,
                           represent = True,
                           )

    filteredrows = data.numrows
    dt = S3DataTable(data.rfields, data.rows, orderby=orderby)
    dt_id = "datatable"

    if r.representation == "html":
        # Page load
        resource.configure(deletable=False)

        record = r.record
        action_vars = {"mission_id": "[id]"}

        # Can we identify the Member?
        from ..s3.s3parser import S3Parsing
        from_address = record.from_address
        hr_id = S3Parsing().lookup_human_resource(from_address)
        if hr_id:
            action_vars["hr_id"] = hr_id

        s3 = response.s3
        s3.actions = [{"label": str(T("Select Mission")),
                       "_class": "action-btn link",
                       "url": URL(f = "email_inbox",
                                  args = [r.id, "select"],
                                  vars = action_vars,
                                  ),
                       },
                      ]
        s3.no_formats = True

        # Data table (items)
        items = dt.html(totalrows,
                        filteredrows,
                        dt_id,
                        dt_ajax_url = r.url(representation="aadata"),
                        dt_pageLength = display_length,
                        dt_pagination = "true",
                        dt_searching = "false",
                        )

        # Filter form
        if filter_widgets:

            # Where to retrieve filtered data from:
            submit_url_vars = resource.crud._remove_filters(get_vars)
            filter_submit_url = r.url(vars=submit_url_vars)

            # Where to retrieve updated filter options from:
            filter_ajax_url = URL(f="mission",
                                  args=["filter.options"],
                                  vars={})

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
            fresource = s3db.resource(resource.tablename)
            alias = resource.alias if r.component else None
            ff = filter_form.html(fresource,
                                  get_vars,
                                  target = "datatable",
                                  alias = alias,
                                  )
        else:
            ff = ""

        output = {"items": items,
                  "title": T("Select Mission"),
                  "list_filter_form": ff,
                  }

        # Add RHeader
        if hr_id:
            from_address = A(from_address,
                             _href = URL(c = "deploy",
                                         f = "human_resource",
                                         args = [hr_id, "profile"],
                                         )
                             )
            row = ""
        else:
            row_id = "deploy_response_human_resource_id__row"
            # @ToDo: deployment_setting for 'Member' label
            title = T("Select Member")
            label = LABEL("%s:" % title)
            field = s3db.deploy_response.human_resource_id
            # @ToDo: Get fancier & auto-click if there is just a single Mission
            script = \
'''S3.update_links=function(){
 var value=$('#deploy_response_human_resource_id').val()
 if(value){
  $('.action-btn.link').each(function(){
   var url=this.href
   var posn=url.indexOf('&hr_id=')
   if(posn>0){url=url.split('&hr_id=')[0]+'&hr_id='+value
   }else{url+='&hr_id='+value}
   $(this).attr('href',url)})}}'''
            s3.js_global.append(script)
            post_process = '''S3.update_links()'''
            widget = S3HumanResourceAutocompleteWidget(post_process=post_process)
            widget = widget(field, None)
            comment = DIV(_class = "tooltip",
                          _title = "%s|%s" % (title,
                                              current.messages.AUTOCOMPLETE_HELP,
                                              ),
                          )
            # @ToDo: Handle non-callable formstyles
            row = s3.crud.formstyle(row_id, label, widget, comment)
            if isinstance(row, tuple):
                row = TAG[""](row[0], row[1])

        # Any attachments?
        if atts:
            attachments = TABLE(TR(TH("%s: " % T("Attachments"))))
            for a in atts:
                url = URL(c = "default",
                          f = "download",
                          args = a.file,
                          )
                attachments.append(TR(TD(A(ICON("attachment"),
                                           a.name,
                                           _href = url,
                                           ),
                                         ),
                                      ))
        else:
            attachments = ""
        # @ToDo: Add Reply button
        rheader = DIV(FORM(row,
                           _class = "select-member-form",
                           ),
                      TABLE(TR(TH("%s: " % T("From")),
                               from_address,
                               ),
                            TR(TH("%s: " % T("Date")),
                               record.created_on,
                               ),
                            TR(TH("%s: " % T("Subject")),
                               record.subject,
                               ),
                            TR(TH("%s: " % T("Message Text")),
                               ),
                            ),
                      DIV(record.body,
                          _class = "message-body s3-truncate",
                          ),
                      attachments,
                      )
        output["rheader"] = rheader
        s3_trunk8(lines=5)

        response.view = "list_filter.html"
        return output

    elif r.representation == "aadata":
        # Ajax refresh
        if "draw" in get_vars:
            draw = int(get_vars.draw)
        else:
            draw = None
        items = dt.json(totalrows,
                        filteredrows,
                        dt_id,
                        draw,
                        )
        response.headers["Content-Type"] = "application/json"
        return items

    else:
        r.error(415, current.ERROR.BAD_FORMAT)

# =============================================================================
class deploy_MissionProfileLayout(S3DataListLayout):
    """ DataList layout for Mission Profile """

    # -------------------------------------------------------------------------
    def __init__(self, profile="deploy_mission"):
        """ Constructor """

        super(deploy_MissionProfileLayout, self).__init__(profile=profile)

        self.dcount = {}
        self.avgrat = {}
        self.deployed = set()
        self.appraisals = {}

        self.use_regions = current.deployment_settings.get_org_regions()

    # -------------------------------------------------------------------------
    def prep(self, resource, records):
        """
            Bulk lookups for cards

            @param resource: the resource
            @param records: the records as returned from S3Resource.select
        """

        db = current.db
        s3db = current.s3db

        tablename = resource.tablename
        if tablename == "deploy_alert":

            # Recipients, aggregated by alert
            record_ids = set(record["_row"]["deploy_alert.id"]
                             for record in records
                             )

            htable = s3db.hrm_human_resource
            number_of_recipients = htable.id.count()

            rtable = s3db.deploy_alert_recipient
            alert_id = rtable.alert_id

            use_regions = self.use_regions
            if use_regions:
                otable = s3db.org_organisation
                region_id = otable.region_id
                fields = [alert_id, region_id, number_of_recipients]
                left = [htable.on(htable.id == rtable.human_resource_id),
                        otable.on(otable.id == htable.organisation_id),
                        ]
                groupby = [alert_id, region_id]
            else:
                fields = [alert_id, number_of_recipients]
                left = [htable.on(htable.id == rtable.human_resource_id),
                        ]
                groupby = [alert_id]

            query = (alert_id.belongs(record_ids)) & \
                    (rtable.deleted != True)
            rows = current.db(query).select(left = left,
                                            groupby = groupby,
                                            *fields)

            recipient_numbers = {}
            for row in rows:
                alert = row[alert_id]
                if alert in recipient_numbers:
                    recipient_numbers[alert].append(row)
                else:
                    recipient_numbers[alert] = [row]
            self.recipient_numbers = recipient_numbers

            # Representations of the region_ids
            if use_regions:
                # not needed with regions = False
                represent = otable.region_id.represent
                represent.none = current.T("No Region")
                region_ids = [row[region_id] for row in rows]
                self.region_names = represent.bulk(region_ids)
            else:
                self.region_names = {}

        elif tablename == "deploy_response":

            dcount = self.dcount
            avgrat = self.avgrat
            deployed = self.deployed

            mission_id = None

            for record in records:
                raw = record["_row"]
                human_resource_id = raw["hrm_human_resource.id"]
                if human_resource_id:
                    dcount[human_resource_id] = 0
                    avgrat[human_resource_id] = None
                if not mission_id:
                    # Should be the same for all rows
                    mission_id = raw["deploy_response.mission_id"]

            hr_ids = list(dcount.keys())
            if hr_ids:

                # Number of previous deployments
                table = s3db.deploy_assignment
                human_resource_id = table.human_resource_id
                deployment_count = table.id.count()

                query = (human_resource_id.belongs(hr_ids)) & \
                        (table.deleted != True)
                rows = db(query).select(human_resource_id,
                                        deployment_count,
                                        groupby = human_resource_id,
                                        )
                for row in rows:
                    dcount[row[human_resource_id]] = row[deployment_count]

                # Members deployed for this mission
                query = (human_resource_id.belongs(hr_ids)) & \
                        (table.mission_id == mission_id) & \
                        (table.deleted != True)
                rows = db(query).select(human_resource_id)
                for row in rows:
                    deployed.add(row[human_resource_id])

                # Average appraisal rating
                atable = s3db.hrm_appraisal
                htable = s3db.hrm_human_resource
                human_resource_id = htable.id
                average_rating = atable.rating.avg()

                query = (human_resource_id.belongs(hr_ids)) & \
                        (htable.person_id == atable.person_id) & \
                        (atable.deleted != True) & \
                        (atable.rating != None) & \
                        (atable.rating > 0)

                rows = db(query).select(human_resource_id,
                                        average_rating,
                                        groupby = human_resource_id,
                                        )
                for row in rows:
                    avgrat[row[human_resource_id]] = row[average_rating]

        elif tablename == "deploy_assignment":

            record_ids = set(record["_row"]["deploy_assignment.id"]
                             for record in records
                             )

            atable = s3db.hrm_appraisal
            ltable = s3db.deploy_assignment_appraisal
            query = (ltable.assignment_id.belongs(record_ids)) & \
                    (ltable.deleted != True) & \
                    (atable.id == ltable.appraisal_id)
            rows = current.db(query).select(ltable.assignment_id,
                                            ltable.appraisal_id,
                                            )
            appraisals = {}
            for row in rows:
                appraisals[row.assignment_id] = row.appraisal_id
            self.appraisals = appraisals

        return

    # -------------------------------------------------------------------------
    def render_header(self, list_id, item_id, resource, rfields, record):
        """
            Render the card header

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        # No card header in this layout
        return None

    # -------------------------------------------------------------------------
    def render_body(self, list_id, item_id, resource, rfields, record):
        """
            Render the card body

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        db = current.db
        s3db = current.s3db
        has_permission = current.auth.s3_has_permission

        table = resource.table
        tablename = resource.tablename

        T = current.T
        pkey = str(resource._id)
        raw = record["_row"]
        record_id = raw[pkey]

        # Specific contents and workflow
        contents = workflow = None

        if tablename == "deploy_alert":

            # Message subject as title
            subject = record["deploy_alert.subject"]

            total_recipients = 0

            rows = self.recipient_numbers.get(record_id)
            if rows:

                # Labels
                hr_label = current.deployment_settings.get_deploy_hr_label()
                HR_LABEL = T(hr_label)
                if hr_label == "Member":
                    HRS_LABEL = T("Members")
                elif hr_label == "Staff":
                    HRS_LABEL = HR_LABEL
                elif hr_label == "Volunteer":
                    HRS_LABEL = T("Volunteers")

                htable = s3db.hrm_human_resource
                rcount = htable.id.count()

                if not self.use_regions:
                    total_recipients = rows[0][rcount]
                    label = HR_LABEL if total_recipients == 1 else HRS_LABEL
                    link = URL(f="alert", args=[record_id, "recipient"])
                    recipients = SPAN(A("%s %s" % (total_recipients, label),
                                        _href = link,
                                        ),
                                      )
                else:
                    region = s3db.org_organisation.region_id
                    region_names = self.region_names
                    UNKNOWN_OPT = current.messages.UNKNOWN_OPT

                    recipients = []
                    no_region = None
                    for row in rows:
                        # Region
                        region_id = row[region]
                        region_name = region_names.get(region_id, UNKNOWN_OPT)
                        region_filter = {
                            "recipient.human_resource_id$" \
                            "organisation_id$region_id__belongs": region_id
                        }

                        # Number of recipients
                        num = row[rcount]
                        total_recipients += num
                        label = HR_LABEL if num == 1 else HRS_LABEL

                        # Link
                        link = URL(f = "alert",
                                   args = [record_id, "recipient"],
                                   vars = region_filter,
                                   )

                        # Recipient list item
                        recipient = SPAN("%s (" % region_name,
                                         A("%s %s" % (num, label),
                                           _href=link,
                                           ),
                                         ")",
                                         )
                        if region_id:
                            recipients.extend([recipient, ", "])
                        else:
                            no_region = [recipient, ", "]

                    # Append "no region" at the end of the list
                    if no_region:
                        recipients.extend(no_region)
                    recipients = TAG[""](recipients[:-1])
            else:
                recipients = T("No Recipients Selected")

            # Modified-date corresponds to sent-date
            modified_on = record["deploy_alert.modified_on"]

            # Has this alert been sent?
            sent = True if raw["deploy_alert.message_id"] else False
            if sent:
                status = SPAN(ICON("sent"),
                              T("sent"),
                              _class="alert-status",
                              )
            else:
                status = SPAN(ICON("unsent"),
                              T("not sent"),
                              _class="red alert-status",
                              )

            # Message
            message = record["deploy_alert.body"]

            # Contents
            contents = DIV(DIV(DIV(subject,
                                   _class = "card-title",
                                   ),
                               DIV(recipients,
                                   _class = "card-category",
                                   ),
                               _class = "media-heading"
                               ),
                           DIV(modified_on,
                               status,
                               _class = "card-subtitle",
                               ),
                           DIV(message,
                               _class = "message-body s3-truncate",
                               ),
                           _class = "media-body",
                           )

            # Workflow
            if not sent and total_recipients and \
               has_permission("update", table, record_id=record_id):
                send = A(ICON("mail"),
                         SPAN(T("Send this Alert"),
                              _class = "card-action"),
                         _onclick = "window.location.href='%s'" %
                                    URL(c = "deploy",
                                        f = "alert",
                                        args = [record_id, "send"],
                                        ),
                         _class = "action-lnk",
                         )
                workflow = [send]

        elif tablename == "deploy_response":

            human_resource_id = raw["hrm_human_resource.id"]

            # Title linked to member profile
            if human_resource_id:
                person_id = record["hrm_human_resource.person_id"]
                profile_url = URL(f = "human_resource",
                                  args = [human_resource_id, "profile"],
                                  )
                profile_title = T("Open Member Profile (in a new tab)")
                person = A(person_id,
                           _href = profile_url,
                           _target = "_blank",
                           _title = profile_title,
                           )
            else:
                person = "%s (%s)" % \
                         (T("Unknown"), record["msg_message.from_address"])

            # Organisation
            organisation = record["hrm_human_resource.organisation_id"]

            # Created_on corresponds to received-date
            created_on = record["deploy_response.created_on"]

            # Message Data
            message = record["msg_message.body"]

            # Dropdown of available documents
            documents = raw["doc_document.file"]
            if documents:
                if not isinstance(documents, list):
                    documents = [documents]
                bootstrap = current.response.s3.formstyle == "bootstrap"
                if bootstrap:
                    docs = UL(_class="dropdown-menu",
                              _role="menu",
                              )
                else:
                    docs = SPAN(_id="attachments",
                                _class="profile-data-value",
                                )
                retrieve = db.doc_document.file.retrieve
                for doc in documents:
                    try:
                        doc_name = retrieve(doc)[0]
                    except (IOError, TypeError):
                        doc_name = current.messages["NONE"]
                    doc_url = URL(c = "default",
                                  f = "download",
                                  args=[doc],
                                  )
                    if bootstrap:
                        doc_item = LI(A(ICON("file"),
                                        " ",
                                        doc_name,
                                        _href = doc_url,
                                        ),
                                      _role="menuitem",
                                      )
                    else:
                        doc_item = A(ICON("file"),
                                     " ",
                                     doc_name,
                                     _href = doc_url,
                                     )
                    docs.append(doc_item)
                    docs.append(", ")
                if bootstrap:
                    docs = DIV(A(ICON("attachment"),
                                 SPAN(_class="caret"),
                                 _class = "btn dropdown-toggle",
                                 _href = "#",
                                 data = {"toggle": "dropdown"},
                                 ),
                               docs,
                               _class = "btn-group attachments dropdown pull-right",
                               )
                else:
                    # Remove final comma
                    docs.components.pop()
                    docs = DIV(LABEL("%s:" % T("Attachments"),
                                     _class = "profile-data-label",
                                     _for = "attachments",
                                     ),
                               docs,
                               _class = "profile-data",
                               )
            else:
                docs = ""

            # Number of previous deployments and average rating
            # (looked up in-bulk in self.prep)
            if hasattr(self, "dcount"):
                dcount = self.dcount.get(human_resource_id, 0)
            if hasattr(self, "avgrat"):
                avgrat = self.avgrat.get(human_resource_id)
            dcount_id = "profile-data-dcount-%s" % record_id
            avgrat_id = "profile-data-avgrat-%s" % record_id
            dinfo = DIV(LABEL("%s:" % T("Previous Deployments"),
                              _for = dcount_id,
                              _class = "profile-data-label",
                              ),
                        SPAN(dcount,
                             _id = dcount_id,
                             _class = "profile-data-value",
                             ),
                        LABEL("%s:" % T("Average Rating"),
                              _for = avgrat_id,
                              _class = "profile-data-label",
                              ),
                        SPAN(avgrat,
                             _id = avgrat_id,
                             _class = "profile-data-value",
                             ),
                        _class = "profile-data",
                        )

            # Comments
            comments_id = "profile-data-comments-%s" % record_id
            comments = DIV(LABEL("%s:" % T("Comments"),
                                 _for = comments_id,
                                 _class = "profile-data-label",
                                 ),
                           SPAN(record["deploy_response.comments"],
                                _id = comments_id,
                                _class = "profile-data-value s3-truncate",
                                ),
                           _class = "profile-data",
                           )

            # Contents
            contents = DIV(DIV(DIV(person,
                                   _class = "card-title",
                                   ),
                               DIV(organisation,
                                   _class = "card-category",
                                   ),
                               _class = "media-heading",
                               ),
                           DIV(created_on,
                               _class = "card-subtitle",
                               ),
                           DIV(message,
                               _class = "message-body s3-truncate",
                               ),
                           docs,
                           dinfo,
                           comments,
                           _class = "media-body",
                           )

            # Workflow
            if human_resource_id:
                if hasattr(self, "deployed") and human_resource_id in self.deployed:
                    deploy = A(ICON("deployed"),
                               SPAN(T("Member Deployed"),
                                    _class = "card-action",
                                    ),
                               _class = "action-lnk",
                               )
                elif has_permission("create", "deploy_assignment"):
                    mission_id = raw["deploy_response.mission_id"]
                    url = URL(f = "mission",
                              args = [mission_id, "assignment", "create"],
                              vars = {"member_id": human_resource_id},
                              )
                    deploy = A(ICON("deploy"),
                               SPAN(T("Deploy this Member"),
                                    _class = "card-action",
                                    ),
                               _href = url,
                               _class = "action-lnk"
                               )
                else:
                    deploy = None
                if deploy:
                    workflow = [deploy]

        elif tablename == "deploy_assignment":

            human_resource_id = raw["hrm_human_resource.id"]

            # Title linked to member profile
            profile_url = URL(f = "human_resource",
                              args = [human_resource_id, "profile"],
                              )
            profile_title = T("Open Member Profile (in a new tab)")
            person = A(record["hrm_human_resource.person_id"],
                       _href = profile_url,
                       _target = "_blank",
                       _title = profile_title,
                       )

            # Organisation
            organisation = record["hrm_human_resource.organisation_id"]

            fields = dict((rfield.colname, rfield) for rfield in rfields)
            render = lambda colname: self.render_column(item_id,
                                                        fields[colname],
                                                        record,
                                                        )

            # Contents
            contents = DIV(DIV(DIV(person,
                                   _class = "card-title",
                                   ),
                               DIV(organisation,
                                   _class = "card-category",
                                   ),
                               _class = "media-heading",
                               ),
                           render("deploy_assignment.start_date"),
                           render("deploy_assignment.end_date"),
                           render("deploy_assignment.job_title_id"),
                           render("deploy_assignment.job_title"),
                           render("hrm_appraisal.rating"),
                           _class = "media-body",
                           )

            # Workflow actions
            appraisal = self.appraisals.get(record_id)
            person_id = raw["hrm_human_resource.person_id"]
            if appraisal and \
               has_permission("update", "hrm_appraisal", record_id=appraisal.id):
                # Appraisal already uploaded => edit
                EDIT_APPRAISAL = T("Open Appraisal")
                url = URL(c = "deploy",
                          f = "person",
                          args = [person_id,
                                  "appraisal",
                                  appraisal.id,
                                  "update.popup"
                                  ],
                          vars = {"refresh": list_id,
                                  "record": record_id
                                  },
                          )
                edit = A(ICON("attachment"),
                         SPAN(EDIT_APPRAISAL,
                              _class = "card-action",
                              ),
                         _href = url,
                         _class = "s3_modal action-lnk",
                         _title = EDIT_APPRAISAL,
                         )
                workflow = [edit]

            elif has_permission("update", table, record_id=record_id):
                # No appraisal uploaded yet => upload
                # Currently we assume that anyone who can edit the
                # assignment can upload the appraisal
                _class = "action-lnk"
                UPLOAD_APPRAISAL = T("Upload Appraisal")
                mission_id = raw["deploy_assignment.mission_id"]
                url = URL(c = "deploy",
                          f = "person",
                          args = [person_id,
                                  "appraisal",
                                  "create.popup"
                                  ],
                          vars = {"mission_id": mission_id,
                                  "refresh": list_id,
                                  "record": record_id,
                                  },
                          )
                upload = A(ICON("upload"),
                           SPAN(UPLOAD_APPRAISAL,
                                _class = "card-action",
                                ),
                           _href = url,
                           _class = "s3_modal action-lnk",
                           _title = UPLOAD_APPRAISAL,
                           )
                workflow = [upload]

        body = DIV(_class="media")

        # Body icon
        icon = self.render_icon(list_id, resource)
        if icon:
            body.append(icon)

        # Toolbox and workflow actions
        toolbox = self.render_toolbox(list_id, resource, record)
        if toolbox:
            if workflow:
                toolbox.insert(0, DIV(workflow, _class="card-actions"))
            body.append(toolbox)

        # Contents
        if contents:
            body.append(contents)

        return body

    # -------------------------------------------------------------------------
    def render_icon(self, list_id, resource):
        """
            Render the body icon

            @param list_id: the list ID
            @param resource: the S3Resource
        """

        tablename = resource.tablename

        if tablename == "deploy_alert":
            icon = "alert.png"
        elif tablename == "deploy_response":
            icon = "email.png"
        elif tablename == "deploy_assignment":
            icon = "member.png"
        else:
            return None

        return A(IMG(_src = URL(c = "static",
                                f = "themes",
                                args = ["IFRC", "img", icon],
                                ),
                     _class = "media-object",
                     ),
                 _class = "pull-left",
                 )

    # -------------------------------------------------------------------------
    def render_toolbox(self, list_id, resource, record):
        """
            Render the toolbox

            @param list_id: the HTML ID of the list
            @param resource: the S3Resource to render
            @param record: the record as dict
        """

        table = resource.table
        tablename = resource.tablename
        record_id = record[str(resource._id)]

        # Determine URLs for Update/Open actions
        open_url = update_url = None

        if tablename == "deploy_alert":
            open_url = URL(f="alert", args=[record_id])

        elif tablename == "deploy_response":
            update_url = URL(f = "response_message",
                             args = [record_id, "update.popup"],
                             vars = {"refresh": list_id,
                                     "record": record_id,
                                     "profile": self.profile,
                                     },
                             )

        elif tablename == "deploy_assignment":
            update_url = URL(c = "deploy",
                             f = "assignment",
                             args = [record_id, "update.popup"],
                             vars = {"refresh": list_id,
                                     "record": record_id,
                                     "profile": self.profile,
                                     },
                             )

        has_permission = current.auth.s3_has_permission
        crud_string = S3Method.crud_string

        toolbox = DIV(_class="edit-bar fright")

        # Update- or Open-button
        if update_url and \
           has_permission("update", table, record_id=record_id):
            btn = A(ICON("edit"),
                    _href = update_url,
                    _class = "s3_modal",
                    _title = crud_string(tablename, "title_update"),
                    )
            toolbox.append(btn)
        elif open_url:
            btn = A(ICON("file-alt"),
                    _href = open_url,
                    _title = crud_string(tablename, "title_display"),
                    )
            toolbox.append(btn)

        # Delete-button
        if has_permission("delete", table, record_id=record_id):
            btn = A(ICON("delete"),
                    _class = "dl-item-delete",
                    _title = crud_string(tablename, "label_delete_button"),
                    )
            toolbox.append(btn)

        return toolbox

    # -------------------------------------------------------------------------
    def render_column(self, item_id, rfield, record):
        """
            Render a data column.

            @param item_id: the HTML element ID of the item
            @param rfield: the S3ResourceField for the column
            @param record: the record (from S3Resource.select)
        """

        colname = rfield.colname
        if colname not in record:
            return None

        value = record[colname]
        value_id = "%s-%s" % (item_id, colname.replace(".", "_"))

        label = LABEL("%s:" % rfield.label,
                      _for = value_id,
                      _class = "profile-data-label",
                      )

        value = SPAN(value,
                     _id = value_id,
                     _class = "profile-data-value",
                     )

        return TAG[""](label, value)

# END =========================================================================
