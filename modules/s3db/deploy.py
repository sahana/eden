# -*- coding: utf-8 -*-

""" Sahana Eden Deployments Model

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

__all__ = ["S3DeploymentModel",
           "S3DeploymentAlertModel",
           "deploy_rheader",
           "deploy_apply",
           "deploy_alert_select_recipients",
           "deploy_response_select_mission",
           ]

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

from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3DeploymentModel(S3Model):

    names = ["deploy_event_type",
             "deploy_mission",
             "deploy_mission_id",
             "deploy_mission_document",
             "deploy_application",
             "deploy_assignment",
             "deploy_assignment_appraisal",
             "deploy_assignment_experience",
             ]

    def model(self):

        T = current.T
        db = current.db

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        human_resource_id = self.hrm_human_resource_id

        # ---------------------------------------------------------------------
        # Mission
        #
        mission_status_opts = {1 : T("Closed"),
                               2 : T("Open")
                               }
        tablename = "deploy_mission"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             Field("name",
                                   label = T("Name"),
                                   requires = IS_NOT_EMPTY(),
                                   ),
                             # @ToDo: Link to location via link table
                             # link table could be event_event_location for IFRC (would still allow 1 multi-country event to have multiple missions)
                             self.gis_location_id(),
                             # @ToDo: Link to event_type via event_id link table instead of duplicating
                             self.event_type_id(),
                             self.org_organisation_id(),
                             Field("code", length = 24,
                                   represent = lambda v: s3_unicode(v) \
                                                         if v else NONE,
                                   ),
                             Field("status", "integer",
                                   requires = IS_IN_SET(mission_status_opts),
                                   represent = lambda opt: \
                                    mission_status_opts.get(opt,
                                                            UNKNOWN_OPT),
                                   default = 2,
                                   label = T("Status"),
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # Virtual field
        # @todo: change into real fields written onaccept?
        table.hrquantity = Field.Lazy(deploy_mission_hrquantity)
        table.response_count = Field.Lazy(deploy_mission_response_count)

        # CRUD Form
        crud_form = S3SQLCustomForm("name",
                                    "event_type_id",
                                    "location_id",
                                    "code",
                                    "status",
                                    # Files
                                    S3SQLInlineComponent(
                                        "document",
                                        name = "file",
                                        label = T("Files"),
                                        fields = ["file", "comments"],
                                        filterby = dict(field = "file",
                                                        options = "",
                                                        invert = True,
                                                        )
                                    ),
                                    # Links
                                    S3SQLInlineComponent(
                                        "document",
                                        name = "url",
                                        label = T("Links"),
                                        fields = ["url", "comments"],
                                        filterby = dict(field = "url",
                                                        options = None,
                                                        invert = True,
                                                        )
                                    ),
                                    #S3SQLInlineComponent("document",
                                                         #name = "file",
                                                         #label = T("Attachments"),
                                                         #fields = ["file",
                                                                   #"comments",
                                                                  #],
                                                         #),
                                    "comments",
                                    "created_on",
                                    )

        # Profile
        alert_widget = dict(label="Alerts",
                            insert=lambda r, listid, title, url: \
                                   A(title,
                                     _href=r.url(component="alert",
                                                 method="create"),
                                     _class="action-btn profile-add-btn"),
                            title_create="New Alert",
                            type="datalist",
                            list_fields = ["modified_on",
                                           "mission_id",
                                           "message_id",
                                           "subject",
                                           "body",
                                           ],
                            tablename = "deploy_alert",
                            context = "mission",
                            list_layout = deploy_render_alert,
                            pagesize = 10,
                            )

        list_fields = ["created_on",
                       "mission_id",
                       "comments",
                       "human_resource_id$id",
                       "human_resource_id$person_id",
                       "human_resource_id$organisation_id",
                       "message_id$body",
                       "message_id$from_address",
                       "message_id$attachment.document_id$file",
                       ]
        response_widget = dict(label = "Responses",
                               insert = False,
                               type = "datalist",
                               tablename = "deploy_response",
                               list_fields = list_fields,
                               context = "mission",
                               list_layout = deploy_render_response,
                               pagesize = 10,
                               )

        hr_label = current.deployment_settings.get_deploy_hr_label()
        if hr_label == "Member":
            label = "Members Deployed"
            title_create = "Deploy New Member"
        elif hr_label == "Staff":
            label = "Staff Deployed"
            title_create = "Deploy New Staff"
        elif hr_label == "Volunteer":
            label = "Volunteers Deployed"
            title_create = "Deploy New Volunteer"

        assignment_widget = dict(label = label,
                                 insert=lambda r, listid, title, url: \
                                        A(title,
                                          _href=r.url(component="assignment",
                                                      method="create"),
                                          _class="action-btn profile-add-btn"),
                                 title_create = title_create,
                                 tablename = "deploy_assignment",
                                 type="datalist",
                                 #type="datatable",
                                 #actions=dt_row_actions,
                                 list_fields = [
                                     "human_resource_id$id",
                                     "human_resource_id$person_id",
                                     "human_resource_id$organisation_id",
                                     "start_date",
                                     "end_date",
                                     "job_title_id",
                                     "appraisal.rating",
                                     "mission_id",
                                 ],
                                 context = "mission",
                                 list_layout = deploy_render_assignment,
                                 pagesize = None, # all records
                                 )

        docs_widget = dict(label = "Documents & Links",
                           title_create = "Add New Document / Link",
                           type = "datalist",
                           tablename = "doc_document",
                           context = ("~.doc_id", "doc_id"),
                           icon = "icon-paperclip",
                           # Default renderer:
                           #list_layout = s3db.doc_render_documents,
                           )

        # Table configuration
        profile = URL(c="deploy", f="mission", args=["[id]", "profile"])
        configure(tablename,
                  create_next = profile,
                  crud_form = crud_form,
                  delete_next = URL(c="deploy", f="mission", args="summary"),
                  filter_widgets = [
                    S3TextFilter(["name",
                                  "code",
                                  "event_type_id$name",
                                  ],
                                 label=T("Search")
                                 ),
                    S3LocationFilter("location_id",
                                     label=messages.COUNTRY,
                                     widget="multiselect",
                                     levels=["L0"],
                                     hidden=True
                                     ),
                    S3OptionsFilter("event_type_id",
                                    widget="multiselect",
                                    hidden=True
                                    ),
                    S3OptionsFilter("status",
                                    options=mission_status_opts,
                                    hidden=True
                                    ),
                    S3DateFilter("created_on",
                                 hide_time=True,
                                 hidden=True
                                ),
                    ],
                  list_fields = ["name",
                                 (T("Date"), "created_on"),
                                 "event_type_id",
                                 (T("Country"), "location_id"),
                                 "code",
                                 (T("Responses"), "response_count"),
                                 (T(label), "hrquantity"),
                                 "status",
                                 ],
                  orderby = "deploy_mission.created_on desc",
                  profile_cols = 1,
                  profile_header = lambda r: \
                                   deploy_rheader(r, profile=True),
                  profile_widgets = [alert_widget,
                                     response_widget,
                                     assignment_widget,
                                     docs_widget,
                                     ],
                  summary = [{"name": "rheader",
                              "common": True,
                              "widgets": [{"method": self.add_button}]
                              },
                             {"name": "table",
                              "label": "Table",
                              "widgets": [{"method": "datatable"}]
                              },
                             {"name": "report",
                              "label": "Report",
                              "widgets": [{"method": "report2",
                                           "ajax_init": True}],
                              },
                             {"name": "map",
                              "label": "Map",
                              "widgets": [{"method": "map",
                                           "ajax_init": True}],
                              },
                             ],
                  super_entity = "doc_entity",
                  update_next = profile,
                  )

        # Components
        add_component("deploy_assignment",
                      deploy_mission="mission_id")

        add_component("deploy_alert",
                      deploy_mission="mission_id")

        add_component("deploy_response",
                      deploy_mission="mission_id")

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Mission"),
            title_display = T("Mission"),
            title_list = T("Missions"),
            title_update = T("Edit Mission Details"),
            title_search = T("Search Missions"),
            title_upload = T("Import Missions"),
            subtitle_create = T("Add New Mission"),
            label_list_button = T("List Missions"),
            label_create_button = T("New Mission"),
            label_delete_button = T("Delete Mission"),
            msg_record_created = T("Mission added"),
            msg_record_modified = T("Mission Details updated"),
            msg_record_deleted = T("Mission deleted"),
            msg_list_empty = T("No Missions currently registered"))

        # Reusable field
        represent = S3Represent(lookup = tablename,
                                linkto = URL(f="mission",
                                             args=["[id]", "profile"]),
                                show_link = True)
                                
        mission_id = S3ReusableField("mission_id", table,
                                     requires = IS_ONE_OF(db,
                                                          "deploy_mission.id",
                                                          represent),
                                     represent = represent,
                                     label = T("Mission"),
                                     ondelete = "CASCADE",
                                     )

        # ---------------------------------------------------------------------
        # Link table to link documents to missions, responses or assignments
        #
        tablename = "deploy_mission_document"
        table = define_table(tablename,
                             mission_id(),
                             self.msg_message_id(),
                             self.doc_document_id(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Application of human resources
        # - agreement that an HR is generally available for assignments
        # - can come with certain restrictions
        #
        tablename = "deploy_application"
        table = define_table(tablename,
                             human_resource_id(empty = False,
                                               label = T(hr_label)),
                             Field("active", "boolean",
                                   default = True,
                                   ),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Assignment of human resources
        # - actual assignment of an HR to a mission
        #
        tablename = "deploy_assignment"
        table = define_table(tablename,
                             mission_id(),
                             human_resource_id(empty = False,
                                               label = T(hr_label)),
                             self.hrm_job_title_id(),
                             # These get copied to hrm_experience
                             # rest of fields may not be filled-out, but are in attachments
                             s3_date("start_date", # Only field visible when deploying from Mission profile
                                     label = T("Start Date"),
                                     ),
                             s3_date("end_date",
                                     label = T("End Date"),
                                     ),
                             *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  context = {"mission": "mission_id",
                             },
                  create_onaccept = self.deploy_assignment_create_onaccept,
                  update_onaccept = self.deploy_assignment_update_onaccept,
                  filter_widgets = [
                    S3TextFilter(["human_resource_id$person_id$first_name",
                                  "human_resource_id$person_id$middle_name",
                                  "human_resource_id$person_id$last_name",
                                  "mission_id$code",
                                 ],
                                 label=T("Search")
                                ),
                    S3OptionsFilter("mission_id$event_type_id",
                                    widget="multiselect",
                                    hidden=True
                                   ),
                    S3LocationFilter("mission_id$location_id",
                                     label=messages.COUNTRY,
                                     widget="multiselect",
                                     levels=["L0"],
                                     hidden=True
                                    ),
                    S3OptionsFilter("job_title_id",
                                    widget="multiselect",
                                    hidden=True,
                                   ),
                    S3DateFilter("start_date",
                                 hide_time=True,
                                 hidden=True,
                                ),
                  ],
                  summary = [
                      {"name": "table",
                       "label": "Table",
                       "widgets": [{"method": "datatable"}]
                      },
                      {"name": "report",
                       "label": "Report",
                       "widgets": [{"method": "report2",
                                    "ajax_init": True}]
                      },
                  ],
                  )

        # Components
        add_component("hrm_appraisal",
                      deploy_assignment=dict(name="appraisal",
                                             link="deploy_assignment_appraisal",
                                             joinby="assignment_id",
                                             key="appraisal_id",
                                             autodelete=False))

        assignment_id = S3ReusableField("assignment_id", table,
                                        ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Link Assignments to Appraisals
        #
        tablename = "deploy_assignment_appraisal"
        table = define_table(tablename,
                             assignment_id(empty=False),
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
        table = define_table(tablename,
                             assignment_id(empty=False),
                             Field("experience_id", self.hrm_experience),
                             *s3_meta_fields())

        configure(tablename,
                  ondelete_cascade = \
                    self.deploy_assignment_experience_ondelete_cascade,
                  )

        # ---------------------------------------------------------------------
        # Assignment of assets
        #
        # @todo: deploy_asset_assignment
        
        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(deploy_mission_id = mission_id,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """
        mission_id = S3ReusableField("mission_id", "integer",
                                     readable=False, writable=False)
        return dict(deploy_mission_id = mission_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def add_button(r, widget_id=None, visible=True, **attr):

        return A(S3Method.crud_string(r.tablename,
                                      "label_create_button"),
                 _href=r.url(method="create", id=0, vars={}),
                 _class="action-btn",
                 )
                
    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_assignment_create_onaccept(form):
        """
            Create linked hrm_experience record
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars
        assignment_id = form_vars.id

        # Extract required data
        human_resource_id = form_vars.human_resource_id
        mission_id = form_vars.mission_id
        job_title_id = form_vars.mission_id
        
        if not mission_id or not human_resource_id:
            # Need to reload the record
            atable = db.deploy_assignment
            query = (atable.id == assignment_id)
            assignment = db(query).select(atable.mission_id,
                                          atable.human_resource_id,
                                          atable.job_title_id,
                                          limitby=(0, 1)).first()
            if assignment:
                mission_id = assignment.mission_id
                human_resource_id = assignment.human_resource_id
                job_title_id = assignment.job_title_id

        # Lookup the person ID
        hrtable = s3db.hrm_human_resource
        hr = db(hrtable.id == human_resource_id).select(hrtable.person_id,
                                                        limitby=(0, 1)
                                                        ).first()

        # Lookup mission details
        mtable = db.deploy_mission
        mission = db(mtable.id == mission_id).select(mtable.code,
                                                     mtable.location_id,
                                                     mtable.organisation_id,
                                                     limitby=(0, 1)
                                                     ).first()
        if mission:
            code = mission.code
            location_id = mission.location_id
            organisation_id = mission.organisation_id
        else:
            code = None
            location_id = None
            organisation_id = None

        # Create hrm_experience
        etable = s3db.hrm_experience
        id = etable.insert(person_id = hr.person_id,
                           code = code,
                           location_id = location_id,
                           job_title_id = job_title_id,
                           organisation_id = organisation_id,
                           start_date = form_vars.start_date,
                           # In case coming from update
                           end_date = form_vars.get("end_date", None),
                           )

        # Create link
        ltable = db.deploy_assignment_experience
        ltable.insert(assignment_id = assignment_id,
                      experience_id = id,
                      )

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
                                                     limitby=(0, 1)).first()
        if not link:
            return
        else:
            # Prevent infinite cascade
            link.update_record(experience_id=None)
            
        s3db.resource("hrm_experience", id=link.experience_id).delete()
        return

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
                                                     limitby=(0, 1)).first()
        if not link:
            return
        else:
            # Prevent infinite cascade
            link.update_record(appraisal_id=None)

        s3db.resource("hrm_appraisal", id=link.appraisal_id).delete()
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_assignment_update_onaccept(form):
        """
            Update linked hrm_experience record
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars

        # Lookup Experience
        ltable = s3db.deploy_assignment_experience
        link = db(ltable.assignment_id == form_vars.id).select(ltable.experience_id,
                                                               limitby=(0, 1)
                                                               ).first()
        if link:
            # Update Experience
            # - likely to be just end_date
            etable = s3db.hrm_experience
            db(etable.id == link.experience_id).update(start_date = form_vars.start_date,
                                                       end_date = form_vars.end_date,
                                                       )
        else:
            # Create Experience
            S3DeploymentModel.deploy_assignment_create_onaccept(form)

# =============================================================================
class S3DeploymentAlertModel(S3Model):

    names = ["deploy_alert",
             "deploy_alert_recipient",
             "deploy_response",
             ]

    def model(self):

        T = current.T

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        human_resource_id = self.hrm_human_resource_id
        message_id = self.msg_message_id
        mission_id = self.deploy_mission_id

        hr_label = current.deployment_settings.get_deploy_hr_label()

        # ---------------------------------------------------------------------
        # Alert
        # - also the PE representing its Recipients
        #
        tablename = "deploy_alert"
        table = define_table(tablename,
                             self.super_link("pe_id", "pr_pentity"),
                             mission_id(
                                requires = IS_ONE_OF(current.db,
                                    "deploy_mission.id",
                                    S3Represent(lookup="deploy_mission"),
                                    filterby="status",
                                    filter_opts=(2,),
                                    )),
                             Field("subject", length=78,    # RFC 2822
                                   label = T("Subject"),
                                   requires = IS_NOT_EMPTY(),
                                   ),
                             Field("body", "text",
                                   label = T("Message"),
                                   represent = lambda v: \
                                    v or current.messages["NONE"],
                                   ),
                             # Link to the Message once sent
                             message_id(readable=False),
                             *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Alert"),
            title_display = T("Alert Details"),
            title_list = T("Alerts"),
            title_update = T("Edit Alert Details"),
            title_search = T("Search Alerts"),
            title_upload = T("Import Alerts"),
            subtitle_create = T("Add New Alert"),
            label_list_button = T("List Alerts"),
            label_create_button = T("Add Alert"),
            label_delete_button = T("Delete Alert"),
            msg_record_created = T("Alert added"),
            msg_record_modified = T("Alert Details updated"),
            msg_record_deleted = T("Alert deleted"),
            msg_list_empty = T("No Alerts currently registered"))

        # CRUD Form
        crud_form = S3SQLCustomForm("mission_id",
                                    "subject",
                                    "body",
                                    "modified_on",
                                    )

        # Table Configuration
        configure(tablename,
                  super_entity = "pr_pentity",
                  context = {"mission": "mission_id"},
                  crud_form = crud_form,
                  list_fields = ["mission_id",
                                 "subject",
                                 "body",
                                 "alert_recipient.human_resource_id",
                                 ],
                  )

        # Components
        add_component("deploy_alert_recipient",
                      deploy_alert=dict(name="recipient",
                                        joinby="alert_id"))

        # Used to link to custom tab deploy_alert_select_recipients
        add_component("hrm_human_resource",
                      deploy_alert=dict(name="select",
                                        link="deploy_alert_recipient",
                                        joinby="alert_id",
                                        key="human_resource_id",
                                        autodelete=False))

        # Custom method to send alerts
        self.set_method("deploy", "alert",
                        method = "send",
                        action = self.deploy_alert_send)

        # Reusable field
        represent = S3Represent(lookup=tablename)
        alert_id = S3ReusableField("alert_id", table,
                                   requires = IS_ONE_OF(db, "deploy_alert.id",
                                                        represent),
                                   represent = represent,
                                   label = T("Alert"),
                                   ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Recipients of the Alert
        #
        tablename = "deploy_alert_recipient"
        table = define_table(tablename,
                             alert_id(),
                             human_resource_id(empty=False,
                                               label = T(hr_label)),
                             *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Recipient"),
            title_display = T("Recipient Details"),
            title_list = T("Recipients"),
            title_update = T("Edit Recipient Details"),
            title_search = T("Search Recipients"),
            title_upload = T("Import Recipients"),
            subtitle_create = T("Add New Recipient"),
            label_list_button = T("List Recipients"),
            label_create_button = T("Add Recipient"),
            label_delete_button = T("Delete Recipient"),
            msg_record_created = T("Recipient added"),
            msg_record_modified = T("Recipient Details updated"),
            msg_record_deleted = T("Recipient deleted"),
            msg_list_empty = T("No Recipients currently defined"))

        # ---------------------------------------------------------------------
        # Responses to Alerts
        #
        tablename = "deploy_response"
        table = define_table(tablename,
                             mission_id(),
                             human_resource_id(label = T(hr_label)),
                             message_id(label=T("Message"),
                                        writable=False),
                             s3_comments(),
                             *s3_meta_fields())

        crud_form = S3SQLCustomForm(
                        "mission_id",
                        "human_resource_id",
                        "message_id",
                        "comments",
                        # @todo:
                        #S3SQLInlineComponent("document"),
                    )

        # Table Configuration
        configure(tablename,
                  context = {"mission": "mission_id"},
                  crud_form = crud_form,
                  #editable = False,
                  insertable = False,
                  update_onaccept = self.deploy_response_update_onaccept,
                  )

        # CRUD Strings
        NO_MESSAGES = T("No Messages found")
        crud_strings[tablename] = Storage(
            title_display = T("Response Message"),
            title_list = T("Response Messages"),
            title_update = T("Edit Response Details"),
            title_search = T("Search Response Messages"),
            label_list_button = T("All Response Messages"),
            label_delete_button = T("Delete Message"),
            msg_record_deleted = T("Message deleted"),
            msg_no_match = NO_MESSAGES,
            msg_list_empty = NO_MESSAGES)

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_alert_send(r, **attr):
        """
            Custom Method to send an Alert
        """

        alert_id = r.id
        if r.representation != "html" or not alert_id or r.component:
            raise HTTP(501, BADMETHOD)

        T = current.T
        record = r.record
        # Always redirect to the Mission Profile
        mission_id = record.mission_id
        next_url = URL(f="mission", args=[mission_id, "profile"])

        # Check whether the alert has already been sent
        # - alerts should be read-only after creation
        if record.message_id:
            current.session.error = T("This Alert has already been sent!")
            redirect(next_url)

        db = current.db
        s3db = current.s3db
        table = s3db.deploy_alert

        # Check whether there are recipients
        ltable = db.deploy_alert_recipient
        query = (ltable.alert_id == alert_id) & \
                (ltable.deleted == False)
        recipients = db(query).select(ltable.id,
                                      limitby=(0, 1)).first()
        if not recipients:
            current.session.error = T("This Alert has no Recipients yet!")
            redirect(next_url)

        # Send Message

        # Embed the mission_id to parse replies
        # = @ToDo: Use a Message Template to add Footer (very simple one for RDRT)
        message = "%s\n:mission_id:%s:" % (record.body, mission_id)

        # Lookup from_address
        # @ToDo: Allow multiple channels to be defined &
        #        select the appropriate one for this mission
        ctable = s3db.msg_email_channel
        channel = db(ctable.deleted == False).select(ctable.username,
                                                     ctable.server,
                                                     limitby = (0, 1)
                                                     ).first()
        if not channel:
            current.session.error = T("Need to configure an Email Address!")
            redirect(URL(f="email_channel"))

        from_address = "%s@%s" % (channel.username, channel.server)

        # @ToDo: Support alternate channels, like SMS
        # if not body: body = subject
        message_id = current.msg.send_by_pe_id(record.pe_id,
                                               subject=record.subject,
                                               message=message,
                                               from_address=from_address
                                               )

        # Update the Alert to show it's been Sent
        db(table.id == alert_id).update(message_id=message_id)

        # Return to the Mission Profile
        current.session.confirmation = T("Alert Sent")
        redirect(next_url)

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy_response_update_onaccept(form):
        """
            Update the doc_id in all attachments (doc_document) to the
            hrm_human_resource the response is linked to.

            @param form: the form
        """

        db = current.db
        s3db = current.s3db

        data = form.vars
        if not data or "id" not in data:
            return

        # Get message ID and human resource ID
        if "human_resource_id" not in data or "message_id" not in data:
            rtable = s3db.deploy_response
            response = db(rtable.id == data.id).select(rtable.human_resource_id,
                                                       rtable.message_id,
                                                       limitby=(0, 1)
                                                       ).first()
            if not response:
                return
            human_resource_id = response.human_resource_id
            message_id = response.message_id
        else:
            human_resource_id = data.human_resource_id
            message_id = data.message_id

        # Update doc_id in all attachments (if any)
        dtable = s3db.doc_document
        ltable = s3db.deploy_mission_document
        query = (ltable.message_id == response.message_id) & \
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
                                                               limitby=(0, 1)
                                                               ).first()
                if hr:
                    doc_id = hr.doc_id
            db(dtable.id.belongs(attachments)).update(doc_id=doc_id)
        return
            
# =============================================================================
def deploy_rheader(r, tabs=[], profile=False):
    """ Deployment Resource Headers """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    record = r.record
    if not record:
        # List or Create form: rheader makes no sense here
        return None

    T = current.T
    table = r.table
    resourcename = r.name

    rheader = None
    if resourcename == "alert":

        alert_id = r.id
        db = current.db
        ltable = db.deploy_alert_recipient
        query = (ltable.alert_id == alert_id) & \
                (ltable.deleted == False)
        recipients = db(query).count()

        unsent = not r.record.message_id
        if unsent:
            send_button = BUTTON(T("Send Alert"), _class="alert-send-btn")
            if recipients:
                send_button.update(_onclick="window.location.href='%s'" %
                                            URL(c="deploy",
                                                f="alert",
                                                args=[alert_id, "send"]))
            else:
                send_button.update(_disabled="disabled")
        else:
            send_button = ""

        # Tabs
        tabs = [(T("Message"), None),
                (T("Recipients (%(number)s Total)") %
                   dict(number=recipients),
                 "recipient"),
                ]
        if unsent:
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
                            ), rheader_tabs, _class="alert-rheader")

    elif resourcename == "mission":

        if not profile and not r.component:
            rheader = ""
        else:
            crud_string = S3Method.crud_string
            record = r.record
            title = crud_string(r.tablename, "title_display")
            if record:
                render = lambda *columns: \
                         deploy_render_profile_data(record,
                                                    table=r.table,
                                                    prefix="header",
                                                    columns=columns)
                title = "%s: %s" % (title, record.name)
                data = render("event_type_id",
                              "location_id",
                              "code",
                              "created_on",
                              "status")
                if profile:
                    crud_button = S3CRUD.crud_button
                    edit_btn = crud_button(T("Edit"),
                                           _href=r.url(method="update"))
                    data.append(edit_btn)
                rheader = DIV(H2(title),
                              data,
                              _class="profile-header")
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

    db = current.db
    table = db.deploy_response
    count = table.id.count()
    row = db(table.mission_id == mission_id).select(count).first()
    if row:
        return row[count]
    else:
        return 0

# =============================================================================
def deploy_render_profile_data(record,
                               table=None,
                               record_id=None,
                               prefix="data",
                               fields=None,
                               columns=None):
    """
        DRY Helper method to render record data with labels, used
        in deploy_mission profile header and cards.

        @param record: the record, either a Row (raw values, also specify
                       table) or a Storage {colname: value} (represented
                       data, also specify fields)
        @param record_id: the record ID (to be added to the element ID)
        @param prefix: the element ID prefix
        @param fields: the S3ResourceFields as dict {colname: rfield}
                       to lookup labels
        @param table: the Table to lookup labels and represent function
        @param columns: the columns (field names with table, column
                        names with fields)
                        to render

        @return: a DIV with LABEL,SPAN pairs for each column
    """

    items = DIV()
    append = items.append

    for column in columns:
        if fields:
            rfield = fields[column]
            fname = rfield.fname
            label = "%s:" % rfield.label
            value = record[column]
        else:
            field = table[column]
            fname = column
            label = "%s:" % field.label
            represent = field.represent or s3_unicode
            value = represent(record[fname])
        if record_id:
            item_id = "profile-%s-%s-%s" % (prefix, fname, record_id)
        else:
            item_id = "profile-%s-%s" % (prefix, fname)
        append(LABEL(label,
                     _for=item_id,
                     _class="profile-%s-label" % prefix))
        append(SPAN(value,
                    _id=item_id,
                    _class="profile-%s-value" % prefix))

    return items

# =============================================================================
def deploy_render_profile_toolbox(resource,
                                  record_id,
                                  update_url=None,
                                  open_url=None):
    """
        DRY Helper method to render a toolbox with Edit/Delete action
        buttons in datalist cards.

        @param resource: the S3Resource
        @param record_id: the record ID
        @param update_url: the update URL (for edit in popup)
        @param open_url: alternatively, an open URL (for edit in new page)
    """

    has_permission = current.auth.s3_has_permission
    table = resource.table
    tablename = resource.tablename

    crud_string = S3Method.crud_string

    toolbox = DIV(_class="edit-bar fright")

    if update_url and \
       has_permission("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=update_url,
                     _class="s3_modal",
                     _title=crud_string(tablename, "title_update"))
        toolbox.append(edit_btn)
    elif open_url:
        open_btn = A(I(" ", _class="icon icon-file-alt"),
                     _href=open_url,
                     _title=crud_string(tablename, "title_display"))
        toolbox.append(open_btn)

    if has_permission("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       _title=crud_string(tablename, "label_delete_button"))
        toolbox.append(delete_btn)

    return toolbox

# =============================================================================
def deploy_render_alert(listid, resource, rfields, record, **attr):
    """
        Item renderer for data list of alerts

        @param listid: the list ID
        @param resource: the S3Resource
        @param rfields: the list fields resolved as S3ResourceFields
        @param record: the record
        @param attr: additional attributes
    """
    
    T = current.T
    hr_label = current.deployment_settings.get_deploy_hr_label()
    HR_LABEL = T(hr_label)
    if hr_label == "Member":
        HRS_LABEL = T("Members")
    elif hr_label == "Staff":
        HRS_LABEL = HR_LABEL
    elif hr_label == "Volunteer":
        HRS_LABEL = T("Volunteers")

    pkey = "deploy_alert.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        record_id = None
        item_id = "%s-[id]" % listid

    row = record["_row"]
    sent = True if row["deploy_alert.message_id"] else False

    # Recipients, aggregated by region
    s3db = current.s3db
    rtable = s3db.deploy_alert_recipient
    htable = s3db.hrm_human_resource
    otable = s3db.org_organisation
    left = [htable.on(htable.id==rtable.human_resource_id),
            otable.on(otable.id==htable.organisation_id)]
    query = (rtable.alert_id == record_id) & \
            (rtable.deleted != True)
    region = otable.region_id
    rcount = htable.id.count()
    rows = current.db(query).select(region, rcount, left=left, groupby=region)

    recips = 0
    if rows:
        represent = otable.region_id.represent
        regions = represent.bulk([row[region] for row in rows])
        none = None
        recipients = []
        for row in rows:
            region_id = row[region]
            num = row[rcount]
            recips += num
            if region_id:
                region_name = regions.get(region_id)
            else:
                region_name = T("No Region")
            region_filter = {
                "recipient.human_resource_id$" \
                "organisation_id$region_id__belongs": region_id
            }
            link = URL(f = "alert",
                       args = [record_id, "recipient"],
                       vars = region_filter)
            recipient = SPAN("%s (" % region_name,
                             A("%s %s" % (num,
                                          HR_LABEL if num == 1 else HRS_LABEL),
                               _href=URL(f = "alert",
                                         args = [record_id, "recipient"],
                                         vars = region_filter),
                             ), ")")
            if region_id:
                recipients.extend([recipient, ", "])
            else:
                none = [recipient, ", "]
        if none:
            recipients.extend(none)
        recipients = TAG[""](recipients[:-1])
    else:
        recipients = T("No Recipients Selected")

    item_class = "thumbnail"

    modified_on = record["deploy_alert.modified_on"]
    if sent:
        status = SPAN(I(_class="icon icon-sent"),
                      T("sent"), _class="alert-status")
    else:
        status = SPAN(I(_class="icon icon-unsent"),
                      T("not sent"), _class="red alert-status")
    subject = record["deploy_alert.subject"]
    body = record["deploy_alert.body"]

    # Toolbox
    open_url = URL(f="alert", args=[record_id])
    toolbox = deploy_render_profile_toolbox(resource, record_id,
                                            open_url=open_url)

    # Workflow actions
    if not sent and recips and \
       current.auth.s3_has_permission("update", resource.table,
                                      record_id=record_id):
        send_btn = A(I(" ", _class="icon icon-envelope-alt"),
                     SPAN(T("Send this Alert"), _class="card-action"),
                     _onclick="window.location.href='%s'" %
                        URL(c="deploy", f="alert", args=[record_id, "send"]),
                     _class="action-lnk")
        #toolbox.insert(0, send_btn)
    else:
        send_btn = ""
    toolbox.insert(0, DIV(send_btn, _class="card-actions"))
                                            
    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static", f="themes",
                                  args=["IFRC", "img", "alert.png"]),
                         ),
                         _class="pull-left",
                   ),
                   toolbox,
                   DIV(DIV(DIV(subject,
                               _class="card-title"),
                           DIV(recipients,
                               _class="card-category"),
                           _class="media-heading"),
                       DIV(modified_on, status, _class="card-subtitle"),
                       DIV(body, _class="message-body s3-truncate"),
                       _class="media-body",
                   ),
                   _class="media",
               ),
               _class=item_class,
               _id=item_id,
           )

    return item

# =============================================================================
def deploy_render_response(listid, resource, rfields, record, **attr):
    """
        Item renderer for data list of responses

        @param listid: the list ID
        @param resource: the S3Resource
        @param rfields: the list fields resolved as S3ResourceFields
        @param record: the record
        @param attr: additional attributes
    """

    T = current.T
    pkey = "deploy_response.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        record_id = None
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    human_resource_id = raw["hrm_human_resource.id"]
    mission_id = raw["deploy_response.mission_id"]

    db = current.db

    # Number of previous deployments and average rating
    # @todo: bulk lookups instead of per-card
    if human_resource_id:
        s3db = current.s3db
        table = s3db.deploy_assignment
        query = (table.human_resource_id == human_resource_id) & \
                (table.deleted != True)
        dcount = db(query).count()

        table = s3db.hrm_appraisal
        htable = s3db.hrm_human_resource
        query = (htable.id == human_resource_id) & \
                (htable.person_id == table.person_id) & \
                (table.deleted != True) & \
                (table.rating != None) & \
                (table.rating > 0)
        avgrat = table.rating.avg()
        row = db(query).select(avgrat).first()
        if row:
            avgrat = row[avgrat]
        else:
            avgrat = None
    else:
        dcount = avgrat = "?"

    dcount_id = "profile-data-dcount-%s" % record_id
    avgrat_id = "profile-data-avgrat-%s" % record_id
    dinfo = DIV(LABEL("%s:" % T("Previous Deployments"),
                      _for=dcount_id,
                      _class="profile-data-label"),
                SPAN(dcount,
                     _id=dcount_id,
                     _class="profile-data-value"),
                LABEL("%s:" % T("Average Rating"),
                      _for=avgrat_id,
                      _class="profile-data-label"),
                SPAN(avgrat,
                     _id=avgrat_id,
                     _class="profile-data-value"),
                _class="profile-data",
                )

    if human_resource_id:
        person_id = record["hrm_human_resource.person_id"]
        profile_url = URL(f="human_resource", args=[human_resource_id, "profile"])
        profile_title = T("Open Member Profile (in a new tab)")
        person = A(person_id,
                   _href=profile_url,
                   _target="_blank",
                   _title=profile_title)
    else:
        person_id = "%s (%s)" % \
                    (T("Unknown"), record["msg_message.from_address"])
        person = person_id

    organisation = record["hrm_human_resource.organisation_id"]

    created_on = record["deploy_response.created_on"]
    message = record["msg_message.body"]
    
    #fields = dict((rfield.colname, rfield) for rfield in rfields)
    #render = lambda *columns: deploy_render_profile_data(record,
                                                         #fields=fields,
                                                         #columns=columns)

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
            doc_url = URL(c="default", f="download",
                          args=[doc])
            if bootstrap:
                doc_item = LI(A(I(_class="icon-file"),
                                " ",
                                doc_name,
                                _href=doc_url,
                                ),
                              _role="menuitem",
                              )
            else:
                doc_item = A(I(_class="icon-file"),
                             " ",
                             doc_name,
                             _href=doc_url,
                             )
            docs.append(doc_item)
            docs.append(", ")
        if bootstrap:
            docs = DIV(A(I(_class="icon-paper-clip"),
                         SPAN(_class="caret"),
                         _class="btn dropdown-toggle",
                         _href="#",
                         **{"_data-toggle": "dropdown"}
                         ),
                       doc_list,
                       _class="btn-group attachments dropdown pull-right",
                       )
        else:
            # Remove final comma
            docs.components.pop()
            docs = DIV(LABEL("%s:" % T("Attachments"),
                             _class = "profile-data-label",
                             _for="attachments",
                             ),
                       docs,
                       _class = "profile-data",
                       )
    else:
        docs = ""

    # Comments
    comments_id = "profile-data-comments-%s" % record_id
    comments = DIV(LABEL("%s:" % T("Comments"),
                         _for=comments_id,
                         _class="profile-data-label"),
                   SPAN(record["deploy_response.comments"],
                        _id=comments_id,
                        _class="profile-data-value s3-truncate"),
                   _class="profile-data",
                  )

    # Toolbox
    update_url = URL(f="response_message",
                     args=[record_id, "update.popup"],
                     vars={"refresh": listid, "record": record_id})
    toolbox = deploy_render_profile_toolbox(resource, record_id,
                                            update_url=update_url)

    # Workflow actions
    # @todo: bulk lookup instead of per-card
    if human_resource_id:
        table = current.s3db.deploy_assignment
        query = (table.mission_id == mission_id) & \
                (table.human_resource_id == human_resource_id) & \
                (table.deleted != True)
        row = db(query).select(table.id, limitby=(0, 1)).first()
        if row:
            deploy_action = A(I(" ", _class="icon icon-deployed"),
                              SPAN(T("Member Deployed"),
                                   _class="card-action"),
                              _class="action-lnk"
                             )
        else:
            deploy_action = A(I(" ", _class="icon icon-deploy"),
                              SPAN(T("Deploy this Member"),
                                   _class="card-action"),
                              _href=URL(f="mission",
                                        args=[mission_id,
                                              "assignment",
                                              "create"
                                              ],
                                        vars={"member_id": human_resource_id}),
                              _class="action-lnk"
                              )
    else:
        deploy_action = ""
    toolbox.insert(0, DIV(deploy_action, _class="card-actions"))

    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static", f="themes",
                                  args=["IFRC", "img", "email.png"]),
                         ),
                         _class="pull-left",
                         ),
                   toolbox,
                   DIV(DIV(DIV(person,
                               _class="card-title"),
                           DIV(organisation,
                               _class="card-category"),
                           _class="media-heading",
                           ),
                       DIV(created_on, _class="card-subtitle"),
                       DIV(message, _class="message-body s3-truncate"),
                       docs,
                       dinfo,
                       comments,
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def deploy_render_assignment(listid, resource, rfields, record, 
                             **attr):
    """
        Item renderer for data list of deployed human resources

        @param listid: the list ID
        @param resource: the S3Resource
        @param rfields: the list fields resolved as S3ResourceFields
        @param record: the record
        @param attr: additional attributes
    """

    pkey = "deploy_assignment.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        record_id = None
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    T = current.T
    raw = record["_row"]
    human_resource_id = raw["hrm_human_resource.id"]

    profile_url = URL(f="human_resource", args=[human_resource_id, "profile"])
    profile_title = T("Open Member Profile (in a new tab)")

    person_id = raw["hrm_human_resource.person_id"]
    person = A(record["hrm_human_resource.person_id"],
               _href=profile_url,
               _target="_blank",
               _title=profile_title)
    organisation = record["hrm_human_resource.organisation_id"]

    fields = dict((rfield.colname, rfield) for rfield in rfields)
    render = lambda *columns: deploy_render_profile_data(record,
                                                         fields=fields,
                                                         columns=columns)

    # Toolbox
    update_url = URL(c="deploy", f="assignment",
                     args=[record_id, "update.popup"],
                     vars={"refresh": listid, "record": record_id})
    toolbox = deploy_render_profile_toolbox(resource, record_id,
                                            update_url=update_url)

    # Workflow actions
    s3db = current.s3db
    atable = s3db.hrm_appraisal
    ltable = s3db.deploy_assignment_appraisal
    query = (ltable.assignment_id == record_id) & \
            (atable.id == ltable.appraisal_id) & \
            (atable.deleted != True)
    appraisal = current.db(query).select(atable.id,
                                         limitby=(0, 1)).first()
    permit = current.auth.s3_has_permission
    if appraisal and permit("update", atable, record_id=appraisal.id):
        _class = "action-lnk"
        EDIT_APPRAISAL = T("Open Appraisal")
        upload_btn = A(I(" ", _class="icon icon-paperclip"),
                       SPAN(EDIT_APPRAISAL, _class="card-action"),
                       _href=URL(c="deploy", f="person",
                                 args=[person_id, "appraisal",
                                       appraisal.id, "update.popup"],
                                 vars={"refresh": listid,
                                       "record": record_id,
                                       },
                                 ),
                       _class="s3_modal %s" % _class,
                       _title=EDIT_APPRAISAL,
                       )
    elif permit("update", resource.table, record_id=record_id):
        # Currently we assume that anyone who can edit the assignment can upload the appraisal
        _class = "action-lnk"
        UPLOAD_APPRAISAL = T("Upload Appraisal")
        upload_btn = A(I(" ", _class="icon icon-paperclip"),
                       SPAN(UPLOAD_APPRAISAL, _class="card-action"),
                       _href=URL(c="deploy", f="person",
                                 args=[person_id, "appraisal", "create.popup"],
                                 vars={"mission_id": raw["deploy_assignment.mission_id"],
                                       "refresh": listid,
                                       "record": record_id,
                                       },
                                 ),
                       _class="s3_modal %s" % _class,
                       _title=UPLOAD_APPRAISAL,
                       )
    else:
        upload_btn = ""
    toolbox.insert(0, DIV(upload_btn, _class="card-actions"))

    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static", f="themes",
                                  args=["IFRC", "img", "member.png"]),
                         ),
                     _class="pull-left",
                     #_href=profile_url,
                     #_title=profile_title,
                     ),
                   toolbox,
                   DIV(DIV(DIV(person,
                               _class="card-title"),
                           DIV(organisation,
                               _class="card-category"),
                           _class="media-heading"),
                       render("deploy_assignment.start_date",
                              "deploy_assignment.end_date",
                              "deploy_assignment.job_title_id",
                              "hrm_appraisal.rating",
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
def deploy_member_filter():
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
                            label=T("Name"),
                            ),
               S3OptionsFilter("organisation_id",
                               widget="multiselect",
                               filter=True,
                               header="",
                               hidden=True,
                               ),
               S3OptionsFilter("credential.job_title_id",
                               # @ToDo: Label setting
                               label = T("Sector"),
                               widget="multiselect",
                               hidden=True,
                               ),
               ]
    if current.deployment_settings.get_org_regions():
        widgets.insert(1, S3HierarchyFilter("organisation_id$region_id",
                                            lookup="org_region",
                                            hidden=True,
                                            ))
    return widgets
    
# =============================================================================
def deploy_apply(r, **attr):
    """
        Custom method to select new RDRT members

        @todo: make workflow re-usable for manual assignments
    """

    T = current.T
    s3db = current.s3db

    get_vars = r.get_vars
    response = current.response
    settings = current.deployment_settings

    resource = r.resource
    if r.http == "POST":
        added = 0
        post_vars = r.post_vars
        if all([n in post_vars for n in ("add", "selected", "mode")]):
            selected = post_vars.selected
            if selected:
                selected = selected.split(",")
            else:
                selected = []

            db = current.db
            atable = s3db.deploy_application
            if selected:
                # Handle exclusion filter
                if post_vars.mode == "Exclusive":
                    if "filterURL" in post_vars:
                        filters = S3URLQuery.parse_url(post_vars.ajaxURL)
                    else:
                        filters = None
                    query = ~(S3FieldSelector("id").belongs(selected))
                    hresource = s3db.resource("hrm_human_resource",
                                              filter=query, vars=filters)
                    rows = hresource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]
                    
                query = (atable.human_resource_id.belongs(selected)) & \
                        (atable.deleted != True)
                rows = db(query).select(atable.id,
                                        atable.active)
                rows = dict((row.id, row) for row in rows)
                for human_resource_id in selected:
                    try:
                        hr_id = int(human_resource_id.strip())
                    except ValueError:
                        continue
                    if hr_id in rows:
                        row = rows[hr_id]
                        if not row.active:
                            added += 1
                        row.update_record(active=True)
                    else:
                        atable.insert(human_resource_id=human_resource_id,
                                      active=True)
                        added += 1
        current.session.confirmation = T("%(number)s RDRT members added") % \
                                       dict(number=added)
        if added > 0:
            redirect(URL(f="human_resource", args=["summary"], vars={}))
        else:
            redirect(URL(f="application", vars={}))

    elif r.http == "GET":

        # Filter widgets
        filter_widgets = deploy_member_filter()

        # List fields
        list_fields = ["id",
                       "person_id",
                       "job_title_id",
                       "organisation_id",
                       ]
        
        # Data table
        totalrows = resource.count()
        if "iDisplayLength" in get_vars:
            display_length = int(get_vars["iDisplayLength"])
        else:
            display_length = 25
        limit = 4 * display_length
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
        # @todo: generalize label
        dt_bulk_actions = [(T("Add as RDRT Members"), "add")]

        if r.extension == "html":
            # Page load
            resource.configure(deletable = False)

            #dt.defaultActionButtons(resource)
            profile_url = URL(f = "human_resource",
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
                            dt_displayLength=display_length,
                            dt_ajax_url=URL(c="deploy",
                                            f="application",
                                            extension="aadata",
                                            vars={},
                                            ),
                            dt_bFilter="false",
                            dt_pagination="true",
                            dt_bulk_actions=dt_bulk_actions,
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
                alias = resource.alias if r.component else None
                ff = filter_form.html(fresource,
                                      r.get_vars,
                                      target="datatable",
                                      alias=alias)
            else:
                ff = ""
                
            output = dict(items = items,
                          # @todo: generalize
                          title = T("Add RDRT Members"),
                          list_filter_form = ff)

            response.view = "list_filter.html"
            return output

        elif r.extension == "aadata":
            # Ajax refresh
            if "sEcho" in get_vars:
                echo = int(get_vars.sEcho)
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
            r.error(501, resource.ERROR.BAD_FORMAT)
    else:
        r.error(405, r.ERROR.BAD_METHOD)

# =============================================================================
def deploy_alert_select_recipients(r, **attr):
    """
        Custom method to select Recipients for an Alert
    """

    alert_id = r.id
    if r.representation not in ("html", "aadata") or not alert_id or not r.component:
        r.error(405, r.ERROR.BAD_METHOD)

    T = current.T
    s3db = current.s3db

    response = current.response
    member_query = S3FieldSelector("application.active") == True

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
                        (~(S3FieldSelector("id").belongs(selected)))

                hresource = s3db.resource("hrm_human_resource",
                                          filter=query, vars=filters)
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
                rtable.insert(alert_id=alert_id,
                              human_resource_id=human_resource_id,
                              )
                added += 1
        if not selected:
            response.warning = T("No Recipients Selected!")
        else:
            response.confirmation = T("%(number)s Recipients added to Alert") % \
                                     dict(number=added)

    get_vars = r.get_vars or {}
    settings = current.deployment_settings
    resource = s3db.resource("hrm_human_resource",
                             filter=member_query, vars=r.get_vars)

    # Filter widgets
    filter_widgets = deploy_member_filter()

    # List fields
    list_fields = ["id",
                   "person_id",
                   "job_title_id",
                   "organisation_id",
                   ]

    # Data table
    totalrows = resource.count()
    if "iDisplayLength" in get_vars:
        display_length = int(get_vars["iDisplayLength"])
    else:
        display_length = 25
    limit = 4 * display_length
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
    dt_bulk_actions = [(T("Select as Recipients"), "select")]

    if r.representation == "html":
        # Page load
        resource.configure(deletable = False)

        #dt.defaultActionButtons(resource)
        response.s3.no_formats = True

        # Data table (items)
        items = dt.html(totalrows,
                        filteredrows,
                        dt_id,
                        dt_displayLength=display_length,
                        dt_ajax_url=r.url(representation="aadata"),
                        dt_bFilter="false",
                        dt_pagination="true",
                        dt_bulk_actions=dt_bulk_actions,
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
            alias = resource.alias if r.component else None
            ff = filter_form.html(fresource,
                                  r.get_vars,
                                  target="datatable",
                                  alias=alias)
        else:
            ff = ""

        output = dict(items=items,
                      title=T("Select Recipients"),
                      list_filter_form=ff)

        # Maintain RHeader for consistency
        if attr.get("rheader"):
            rheader = attr["rheader"](r)
            if rheader:
                output["rheader"] = rheader

        response.view = "list_filter.html"
        return output

    elif r.representation == "aadata":
        # Ajax refresh
        if "sEcho" in get_vars:
            echo = int(get_vars.sEcho)
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
        r.error(501, resource.ERROR.BAD_FORMAT)

# =============================================================================
def deploy_response_select_mission(r, **attr):
    """
        Custom method to Link a Response to a Mission &/or Human Resource
    """

    message_id = r.record.message_id if r.record else None
    if r.representation not in ("html", "aadata") or not message_id or not r.component:
        r.error(405, r.ERROR.BAD_METHOD)

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
    mission_query = S3FieldSelector("mission.status") == 2

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
        #                                    dict(mission=mission)
        current.session.confirmation = T("Response linked to Mission")
        redirect(URL(c="deploy", f="email_inbox"))

    settings = current.deployment_settings
    resource = s3db.resource("deploy_mission",
                             filter=mission_query, vars=r.get_vars)

    # Filter widgets
    filter_widgets = s3db.get_config("deploy_mission", "filter_widgets")

    # List fields
    list_fields = s3db.get_config("deploy_mission", "list_fields")
    list_fields.insert(0, "id")

    # Data table
    totalrows = resource.count()
    if "iDisplayLength" in get_vars:
        display_length = int(get_vars["iDisplayLength"])
    else:
        display_length = 25
    limit = 4 * display_length
    filter, orderby, left = resource.datatable_filter(list_fields, get_vars)
    if not orderby:
        # Most recent missions on top
        orderby = "created_on desc"
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

    if r.representation == "html":
        # Page load
        resource.configure(deletable = False)

        record = r.record
        action_vars = dict(mission_id="[id]")

        # Can we identify the Member?
        from ..s3.s3parser import S3Parsing
        from_address = record.from_address
        hr_id = S3Parsing().lookup_human_resource(from_address)
        if hr_id:
            action_vars["hr_id"] = hr_id

        s3 = response.s3
        s3.actions = [dict(label=str(T("Select Mission")),
                           _class="action-btn",
                           url=URL(f="email_inbox",
                                   args=[r.id, "select"],
                                   vars=action_vars,
                                   )),
                      ]
        s3.no_formats = True

        # Data table (items)
        items = dt.html(totalrows,
                        filteredrows,
                        dt_id,
                        dt_displayLength=display_length,
                        dt_ajax_url=r.url(representation="aadata"),
                        dt_bFilter="false",
                        dt_pagination="true",
                        )

        # Filter form
        if filter_widgets:

            # Where to retrieve filtered data from:
            _vars = resource.crud._remove_filters(r.get_vars)
            filter_submit_url = r.url(vars=_vars)

            # Where to retrieve updated filter options from:
            filter_ajax_url = URL(f="mission",
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
            alias = resource.alias if r.component else None
            ff = filter_form.html(fresource,
                                  r.get_vars,
                                  target="datatable",
                                  alias=alias)
        else:
            ff = ""

        output = dict(items=items,
                      title=T("Select Mission"),
                      list_filter_form=ff)

        # Add RHeader
        if hr_id:
            from_address = A(from_address,
                             _href=URL(c="deploy", f="human_resource",
                                       args=[hr_id, "profile"],
                                       )
                             )
            row = ""
        else:
            id = "deploy_response_human_resource_id__row"
            # @ToDo: deployment_setting for 'Member' label
            title = T("Select Member")
            label = "%s:" % title
            field = s3db.deploy_response.human_resource_id
            # @ToDo: Get fancier & auto-click if there is just a single Mission
            script = \
'''S3.update_links=function(){
 var value=$('#deploy_response_human_resource_id').val()
 if(value){
  $('.action-btn.link').each(function(){
   var url=this.href
   var posn=url.indexOf('&hr_id=')
   if(posn>0){
    url=url.split('&hr_id=')[0]+'&hr_id='+value
   }else{
    url+='&hr_id='+value
   }
   $(this).attr('href',url)
   })}}
'''
            s3.js_global.append(script)
            post_process = '''S3.update_links()'''
            widget = S3HumanResourceAutocompleteWidget(post_process=post_process)
            widget = widget(field, None)
            comment = DIV(_class="tooltip",
                          _title="%s|%s" % (title,
                                            T("Enter some characters to bring up "
                                              "a list of possible matches")))
            # @ToDo: Handle non-callable formstyles
            row = s3.crud.formstyle(id, label, widget, comment)
            if isinstance(row, tuple):
                row = TAG[""](row[0],
                              row[1],
                              )
        # Any attachments?
        if atts:
            attachments = TABLE(TR(TH("%s: " % T("Attachments"))))
            for a in atts:
                url = URL(c="default", f="download",
                          args=a.file)
                attachments.append(TR(TD(A(I(" ", _class="icon icon-paperclip"),
                                           a.name,
                                           _href=url))))
        else:
            attachments = ""
        # @ToDo: Add Reply button
        rheader = DIV(row,
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
                            DIV(record.body, _class="message-body s3-truncate"),
                            attachments,
                            )
        output["rheader"] = rheader
        s3_trunk8(lines=5)
        
        response.view = "list_filter.html"
        return output

    elif r.representation == "aadata":
        # Ajax refresh
        if "sEcho" in get_vars:
            echo = int(get_vars.sEcho)
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
        r.error(501, resource.ERROR.BAD_FORMAT)

# END =========================================================================
