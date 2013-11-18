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
           "deploy_application",
           "deploy_alert_select_recipients",
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

# =============================================================================
class S3DeploymentModel(S3Model):

    names = ["deploy_event_type",
             "deploy_mission",
             "deploy_mission_id",
             "deploy_role_type",
             "deploy_human_resource_application",
             "deploy_human_resource_assignment",
             ]

    def model(self):

        T = current.T
        db = current.db
        define_table = self.define_table
        configure = self.configure
        super_link = self.super_link
        add_component = self.add_component

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        NONE = current.messages["NONE"]
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT
        
        # ---------------------------------------------------------------------
        # Mission
        #
        mission_status_opts = {
            1 : T("Closed"),
            2 : T("Open")
        }
        tablename = "deploy_mission"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             Field("name",
                                   label = T("Name"),
                                   requires=IS_NOT_EMPTY(),
                                   ),
                             # @ToDo: Link to location via link table
                             # - country is very IFRC-specific
                             # link table could be event_event_location for IFRC (would still allow 1 multi-country event to have multiple missions)
                             self.gis_country_id(),
                             # @ToDo: Link to event_type via event_id link table instead of duplicating
                             self.event_type_id(label=T("Disaster Type")),
                             # Is this an Event code or a Mission code?
                             Field("code",
                                   length = 24,
                                   represent = lambda v: s3_unicode(v) \
                                                         if v else NONE,
                                   readable = False,
                                   writable = False),
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
        # @todo: move to real field written onaccept?
        table.hrquantity = Field.Lazy(deploy_mission_hrquantity)

        # CRUD Form
        crud_form = S3SQLCustomForm("name",
                                    "event_type_id",
                                    "location_id",
                                    "code",
                                    "status",
                                    S3SQLInlineComponent("document",
                                                         name = "file",
                                                         label = T("Attachments"),
                                                         fields = ["file",
                                                                   "comments",
                                                                  ],
                                                         ),
                                    "comments",
                                    "created_on",
                                    )

        # Profile
        alert_widget = dict(label="Alerts",
                            insert=lambda r, add_title, add_url: \
                                   A(add_title,
                                     _href=r.url(component="alert",
                                                 method="create"),
                                     _class="action-btn profile-add-btn"),
                            title_create="New Alert",
                            type="datalist",
                            list_fields = ["created_on",
                                           "subject",
                                           "body",
                                           ],
                            tablename = "deploy_alert",
                            context = "mission",
                            colspan = 2,
                            list_layout = deploy_render_alert,
                            pagesize = 10,
                            )

        response_widget = dict(label="Responses",
                               insert=False,
                               type="datalist",
                               list_fields = [
                                    "created_on",
                                    "mission_id",
                                    "human_resource_id$id",
                                    "human_resource_id$person_id",
                                    "human_resource_id$organisation_id",
                                    "message_id$body",
                               ],
                               tablename = "deploy_response",
                               context = "mission",
                               colspan = 2,
                               list_layout = deploy_render_response,
                               pagesize = 10,
                               )

        # @todo: generalize terminology (currently RDRT specific)
        assignment_widget = dict(label="Members Deployed",
                                 insert=lambda r, add_title, add_url: \
                                        A(add_title,
                                          _href=r.url(component="human_resource_assignment",
                                                      method="create"),
                                          _class="action-btn profile-add-btn"),
                                 title_create="Deploy New Member",
                                 type="datalist",
                                 list_fields = [
                                     "human_resource_id$id",
                                     "human_resource_id$person_id",
                                     "human_resource_id$organisation_id",
                                     "start_date",
                                     "end_date",
                                     "role_type_id",
                                 ],
                                 tablename = "deploy_human_resource_assignment",
                                 context = "mission",
                                 colspan = 2,
                                 list_layout = deploy_render_human_resource_assignment,
                                 pagesize = None, # all records
                                 )

        # Table configuration
        profile = URL(c="deploy", f="mission", args=["[id]", "profile"])
        configure(tablename,
                  super_entity = "doc_entity",
                  crud_form = crud_form,
                  create_next = profile,
                  update_next = profile,
                  list_fields = ["name",
                                 (T("Date"), "created_on"),
                                 "event_type_id",
                                 (T("Country"), "location_id"),
                                 "code",
                                 (T("Members"), "hrquantity"),
                                 "status",
                                 ],
                  profile_header = lambda r: \
                                   deploy_rheader(r, profile=True),
                  profile_widgets = [alert_widget,
                                     response_widget,
                                     assignment_widget,
                                    ],
                  summary=[{"name": "rheader",
                            "common": True,
                            "widgets": [
                                {"method": self.add_button}
                            ]
                           },
                           {"name": "table",
                            "label": "Table",
                            "widgets": [{"method": "datatable"}]
                            },
                            {"name": "map",
                             "label": "Map",
                             "widgets": [{"method": "map",
                                          "ajax_init": True}],
                            },
                  ],
                  filter_widgets = [
                      S3TextFilter(["name", "code", "event_type"],
                                   label=T("Search")),
                      S3LocationFilter("location_id",
                                       label=T("Country"),
                                       widget="multiselect",
                                       levels=["L0"],
                                       hidden=True),
                      S3OptionsFilter("event_type_id",
                                      widget="multiselect",
                                      hidden=True),
                      S3OptionsFilter("status",
                                      options=mission_status_opts,
                                      hidden=True),
                  ],
                  orderby="deploy_mission.created_on desc",
                  delete_next=URL(c="deploy", f="mission", args="summary"),
                  )

        # Components
        add_component("deploy_human_resource_assignment",
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
        represent = S3Represent(lookup=tablename)
        mission_id = S3ReusableField("mission_id", table,
                                     requires = IS_ONE_OF(db,
                                                          "deploy_mission.id",
                                                          represent),
                                     represent = represent,
                                     label = T("Mission"),
                                     ondelete = "CASCADE",
                                     )

        # ---------------------------------------------------------------------
        # Role Type ('Sector' in RDRT)
        # - used to classify Assignments & Trainings
        #
        # @ToDo: Replace with real Sectors
        #
        tablename = "deploy_role_type"
        table = define_table(tablename,
                             Field("name", notnull=True,
                                   length=64,
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Sector"),
            title_display = T("Sector Details"),
            title_list = T("Sectors"),
            title_update = T("Edit Sector"),
            title_search = T("Search Sectors"),
            title_upload = T("Import Sectors"),
            subtitle_create = T("Add New Sector"),
            label_list_button = T("List Sectors"),
            label_create_button = T("Add Sector"),
            label_delete_button = T("Remove Sector from this event"),
            msg_record_created = T("Sector added"),
            msg_record_modified = T("Sector updated"),
            msg_record_deleted = T("Sector removed"),
            msg_list_empty = T("No Sectors currently registered")
            )

        represent = S3Represent(lookup=tablename)
        role_type_id = S3ReusableField("role_type_id", table,
                                       sortby="name",
                                       requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "deploy_role_type.id",
                                                              represent,
                                                              orderby="deploy_role_type.name",
                                                              sort=True)),
                                       represent = represent,
                                       label = T("Sector"),
                                       ondelete = "RESTRICT",
                                       )
        configure(tablename,
                  deduplicate=self.deploy_role_type_duplicate
                  )

        # ---------------------------------------------------------------------
        # Application of human resources (= agreement that an HR is
        # generally available for assignments, can come with certain
        # restrictions)
        #
        # @ToDo: Better Name. human_resource_member perhaps.
        #
        tablename = "deploy_human_resource_application"
        table = define_table(tablename,
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
                             Field("active", "boolean",
                                   default=True,
                                   ),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Assignment of human resources (= actual assignment of an HR to
        # a mission)
        #
        tablename = "deploy_human_resource_assignment"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             mission_id(),
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
                             role_type_id(),
                             s3_date("start_date",
                                     label = T("Start Date")),
                             s3_date("end_date",
                                     label = T("End Date")),
                             Field("rating", "double",
                                   label=T("Rating"),
                                   default=0.0),
                             *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  super_entity="doc_entity",
                  context = {"mission": "mission_id"},
                  )

        # CRUD Strings
        # @todo: this is RDRT-specific, move into IFRC config
        crud_strings[tablename] = Storage(
            title_create = T("New Deployment"),
            title_display = T("Deployment Details"),
            title_list = T("Deployments"),
            title_update = T("Edit Deployment Details"),
            title_search = T("Search Deployments"),
            title_upload = T("Import Deployments"),
            subtitle_create = T("Add New Deployment"),
            label_list_button = T("List Deployments"),
            label_create_button = T("Add Deployment"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment Details updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"))

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
    def deploy_role_type_duplicate(item):
        """
            Deduplication of Role Types
        """

        if item.tablename != "deploy_role_type":
            return

        data = item.data
        name = data.get("name", None)

        if not name:
            return

        table = item.table
        query = (table.name == name)
        _duplicate = current.db(query).select(table.id,
                                              limitby=(0, 1)).first()
        if _duplicate:
            item.id = _duplicate.id
            item.data.id = _duplicate.id
            item.method = item.METHOD.UPDATE

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
        set_method = self.set_method
        super_link = self.super_link

        message_id = self.msg_message_id

        # ---------------------------------------------------------------------
        # Alert (also the PE representing its Recipients)
        #
        tablename = "deploy_alert"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             self.deploy_mission_id(
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
                                    "created_on",
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
        set_method("deploy", "alert",
                   method="send",
                   action=self.deploy_alert_send)

        # Reusable field
        represent = S3Represent(lookup=tablename)
        alert_id = S3ReusableField("alert_id", table,
                                   requires = IS_ONE_OF(db,
                                                        "deploy_alert.id",
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
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
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
                             self.deploy_mission_id(),
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
                             message_id(),
                             *s3_meta_fields())

        # Table Configuration
        configure(tablename,
                  context = {"mission": "mission_id"},
                  )
                  
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
        if recipients and unsent:
            send_button = S3CRUD.crud_button(T("Send Alert"),
                                             _href=URL(c="deploy", f="alert",
                                                       args=[alert_id, "send"]),
                                             #_id="send-alert-btn",
                                             )
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
            tabs.insert(1, (T("Select"), "select"))
        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(TR(TH("%s: " % table.mission_id.label),
                               A(table.mission_id.represent(record.mission_id),
                                 _href=URL(f="mission",
                                           args=[record.mission_id, "profile"])
                               ),
                               send_button,
                               ),
                            TR(TH("%s: " % table.subject.label),
                               record.subject
                               ),
                            ), rheader_tabs)

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
                    edit_btn = crud_button(current.T("Edit"),
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
    table = db.deploy_human_resource_assignment
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
def deploy_render_profile_toolbox(resource, record_id, update_url):
    """
        DRY Helper method to render a toolbox with Edit/Delete action
        buttons in datalist cards.

        @param resource: the S3Resource
        @param record_id: the record ID
        @param update_url: the update URL
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

    if has_permission("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                       _title=crud_string(tablename, "label_delete_button"))
        toolbox.append(delete_btn)

    return toolbox

# =============================================================================
def deploy_render_alert(listid,
                        resource,
                        rfields,
                        record,
                        **attr):
    """
        Item renderer for data list of alerts

        @param listid: the list ID
        @param resource: the S3Resource
        @param rfields: the list fields resolved as S3ResourceFields
        @param record: the record
        @param attr: additional attributes
    """
    
    T = current.T
    MEMBER = T("Member")
    MEMBERS = T("Members")
    RECIPIENTS = "%s: " % T("Recipients")

    pkey = "deploy_alert.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        record_id = None
        item_id = "%s-[id]" % listid

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

    if rows:
        represent = otable.region_id.represent
        regions = represent.bulk([row[region] for row in rows])
        none=None
        recipients = []
        for row in rows:
            region_id = row[region]
            num = row[rcount]
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
                                          MEMBER if num == 1 else MEMBERS),
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
        recipients = current.messages["NONE"]

    item_class = "thumbnail"

    created_on = record["deploy_alert.created_on"]
    subject = record["deploy_alert.subject"]
    body = record["deploy_alert.body"]

    # Toolbox
    toolbox = deploy_render_profile_toolbox(resource, record_id, None)
    no_recipients = True
    if no_recipients:
        send_btn = A(I(" ", _class="icon icon-search"),
                     #_class="dl-item-custom",
                     _title=current.T("Select Recipients"))
        toolbox.append(send_btn)

    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static",
                                  f="themes",
                                  args=["IFRC", "img", "alert.png"]),
                         ),
                         _class="pull-left",
                   ),
                   toolbox,
                   DIV(DIV(DIV(subject,
                               _class="card-title"),
                           DIV(#RECIPIENTS,
                               recipients,
                               _class="card-category"),
                           _class="media-heading"),
                       DIV(created_on, _class="card-subtitle"),
                       DIV(body, _class="alert-message-body s3-truncate"),
                       _class="media-body",
                   ),
                   _class="media",
               ),
               _class=item_class,
               _id=item_id,
           )

    return item

# =============================================================================
def deploy_render_response(listid,
                           resource,
                           rfields,
                           record,
                           **attr):
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

    row = record["_row"]
    human_resource_id = row["hrm_human_resource.id"]
    mission_id = row["deploy_response.mission_id"]

    # Member deployed?
    # @todo: bulk lookup instead of per-card
    table = current.s3db.deploy_human_resource_assignment
    query = (table.mission_id == mission_id) & \
            (table.human_resource_id == human_resource_id) & \
            (table.deleted != True)
    row = current.db(query).select(table.id, limitby=(0, 1)).first()
    if row:
        deploy_action = A(I(" ", _class="icon icon-deployed"),
                          SPAN(T("Member Deployed"), _class="card-action"),
                          _class="action-lnk")
    else:
        deploy_action = A(I(" ", _class="icon icon-deploy"),
                          SPAN(T("Deploy this Member"), _class="card-action"),
                          _href=URL(f="mission",
                                    args=[mission_id,
                                          "human_resource_assignment",
                                          "create"
                                         ],
                                    vars={"member_id": human_resource_id}),
                          _class="action-lnk")

    profile_url = URL(f="human_resource", args=[human_resource_id])
    profile_title = current.T("Open Member Profile (in a new tab)")

    person = A(record["hrm_human_resource.person_id"],
               _href=profile_url,
               _target="_blank",
               _title=profile_title)
    organisation = record["hrm_human_resource.organisation_id"]

    created_on = record["deploy_response.created_on"]
    message = record["msg_message.body"]
    
    #fields = dict((rfield.colname, rfield) for rfield in rfields)
    #render = lambda *columns: deploy_render_profile_data(record,
                                                         #fields=fields,
                                                         #columns=columns)

    # Toolbox
    toolbox = deploy_render_profile_toolbox(resource, record_id, None)

    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static",
                                  f="themes",
                                  args=["IFRC", "img", "email.png"]),
                         ),
                         _class="pull-left",
                   ),
                   toolbox,
                   DIV(DIV(DIV(person,
                               _class="card-title"),
                           DIV(organisation,
                               _class="card-category"),
                           _class="media-heading"),
                       DIV(created_on, _class="card-subtitle"),
                       DIV(message, _class="response-message-body s3-truncate"),
                       DIV(deploy_action,
                           _class="card-actions",
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
def deploy_render_human_resource_assignment(listid,
                                            resource,
                                            rfields,
                                            record,
                                            **attr):
    """
        Item renderer for data list of deployed human resources

        @param listid: the list ID
        @param resource: the S3Resource
        @param rfields: the list fields resolved as S3ResourceFields
        @param record: the record
        @param attr: additional attributes
    """

    pkey = "deploy_human_resource_assignment.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        record_id = None
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    row = record["_row"]
    human_resource_id = row["hrm_human_resource.id"]

    profile_url = URL(f="human_resource", args=[human_resource_id])
    profile_title = current.T("Open Member Profile (in a new tab)")
    
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
    update_url = URL(c="deploy", f="human_resource_assignment",
                     args=[record_id, "update.popup"],
                     vars={"refresh": listid, "record": record_id})
    toolbox = deploy_render_profile_toolbox(resource, record_id, update_url)

    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static",
                                  f="themes",
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
                       render("deploy_human_resource_assignment.start_date",
                              "deploy_human_resource_assignment.end_date",
                              "deploy_human_resource_assignment.role_type_id",
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
        custom methods for member selection, e.g. deploy_application
        or deploy_alert_select_recipients
    """

    widgets = [S3TextFilter(["person_id$first_name",
                             "person_id$middle_name",
                             "person_id$last_name",
                             ],
                            label=current.T("Name"),
                            ),
               S3OptionsFilter("organisation_id",
                               widget="multiselect",
                               filter=True,
                               header="",
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
def deploy_application(r, **attr):
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
            atable = s3db.deploy_human_resource_application
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
    member_query = S3FieldSelector("human_resource_application.active") == True

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
                                human_resource_id=human_resource_id)
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

        dt.defaultActionButtons(resource)
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

            #from s3filter import S3FilterForm
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

# END =========================================================================
