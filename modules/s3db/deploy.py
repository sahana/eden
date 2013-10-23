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
           "deploy_deployment_rheader",
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

    names = ["deploy_deployment",
             "deploy_deployment_id",
             "deploy_human_resource_assignment"]

    def model(self):

        T = current.T
        db = current.db
        define_table = self.define_table
        configure = self.configure
        super_link = self.super_link
        add_component = self.add_component

        s3 = current.response.s3
        crud_strings = s3.crud_strings

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT
        
        # ---------------------------------------------------------------------
        # Deployment
        #
        deployment_status_opts = {
            1 : T("Closed"),
            2 : T("Open")
        }
        tablename = "deploy_deployment"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             Field("name",
                                   label = T("Name"),
                                   requires=IS_NOT_EMPTY(),
                                   ),
                             self.gis_location_id(
                                label = T("Country"),
                                widget = S3LocationAutocompleteWidget(level="L0"),
                                requires = IS_EMPTY_OR(IS_LOCATION(level="L0")),
                                represent = self.gis_LocationRepresent(sep=", "),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Country"),
                                                                T("Enter some characters to bring up a list of possible matches"))),
                             ),
                             Field("event_type", # @todo: replace by link
                                   label = T("Event Type"),
                                   ),        
                             Field("status", "integer",
                                   requires = IS_IN_SET(deployment_status_opts),
                                   represent = lambda opt: \
                                    deployment_status_opts.get(opt,
                                                               UNKNOWN_OPT),
                                   default = 2,
                                   label = T("Status"),
                             ),
                             s3_comments(),
                             *s3_meta_fields())

        # Virtual field
        # @todo: move to real field written onaccept?
        table.hrquantity = Field.Lazy(deploy_deployment_hrquantity)

        # CRUD Form
        crud_form = S3SQLCustomForm("name",
                                    "location_id",
                                    "status",
                                    "event_type",
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
                            context = "deployment",
                            colspan = 2,
                            list_layout = deploy_render_alert,
                            pagesize = 10,
                           )

        assignment_widget = dict(label="Members Assigned",
                                 insert=lambda r, add_title, add_url: \
                                        A(add_title,
                                          _href=r.url(component="human_resource_assignment",
                                                      method="create"),
                                          _class="action-btn profile-add-btn"),
                                 title_create="Add Member",
                                 type="datalist",
                                 list_fields = [
                                     "human_resource_id$id",
                                     "human_resource_id$person_id",
                                     "human_resource_id$organisation_id",
                                     "start_date",
                                     "end_date",
                                     "rating",
                                 ],
                                 tablename = "deploy_human_resource_assignment",
                                 context = "deployment",
                                 colspan = 2,
                                 list_layout = deploy_render_human_resource_assignment,
                                 pagesize = None, # all records
                                )

        # Table configuration
        profile = URL(c="deploy", f="deployment", args=["[id]", "profile"])
        configure(tablename,
                  super_entity = "doc_entity",
                  crud_form = crud_form,
                  create_next = profile,
                  update_next = profile,
                  list_fields = ["name",
                                 (T("Date"), "created_on"),
                                 (T("Country"), "location_id"),
                                 (T("Members"), "hrquantity"),
                                 "status",
                                 ],
                  profile_header = lambda r: \
                                   deploy_deployment_rheader(r, profile=True),
                  profile_widgets = [alert_widget,
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
                      S3TextFilter("name",
                                   label=T("Search"),
                                  ),
                      S3LocationFilter("location_id",
                                       label=T("Location"),
                                       widget="multiselect",
                                       levels=["L0"],
                                       hidden=True,
                                      ),
                  ],
                  orderby="deploy_deployment.created_on desc",
                  delete_next=URL(c="deploy", f="deployment", args="summary"),
                  )

        # Components
        add_component("deploy_human_resource_assignment",
                      deploy_deployment="deployment_id")

        add_component("deploy_alert",
                      deploy_deployment="deployment_id")

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Deployment"),
            title_display = T("Deployment"),
            title_list = T("Deployments"),
            title_update = T("Edit Deployment Details"),
            title_search = T("Search Deployments"),
            title_upload = T("Import Deployments"),
            subtitle_create = T("Add New Deployment"),
            label_list_button = T("List Deployments"),
            label_create_button = T("New Deployment"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment Details updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"))
                
        # Reusable field
        represent = S3Represent(lookup=tablename)
        deployment_id = S3ReusableField("deployment_id", table,
                                        requires = IS_ONE_OF(db,
                                                             "deploy_deployment.id",
                                                             represent),
                                        represent = represent,
                                        label = T("Deployment"),
                                        ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Deployment of human resources
        #
        tablename = "deploy_human_resource_assignment"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             deployment_id(),
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
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
                  context = {"deployment": "deployment_id"},
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("New Assignment"),
            title_display = T("Assignment Details"),
            title_list = T("Assignments"),
            title_update = T("Edit Assignment Details"),
            title_search = T("Search Assignments"),
            title_upload = T("Import Assignments"),
            subtitle_create = T("Add New Assignment"),
            label_list_button = T("List Assignments"),
            label_create_button = T("Add Assignment"),
            label_delete_button = T("Delete Assignment"),
            msg_record_created = T("Assignment added"),
            msg_record_modified = T("Assignment Details updated"),
            msg_record_deleted = T("Assignment deleted"),
            msg_list_empty = T("No Assignments currently registered"))

        # ---------------------------------------------------------------------
        # Deployment of assets
        #
        # @todo: deploy_asset_assignment
        
        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(deploy_deployment_id = deployment_id,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """
        deployment_id = S3ReusableField("deployment_id", "integer",
                                        readable=False, writable=False)
        return dict(deploy_deployment_id = deployment_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def add_button(r, widget_id=None, visible=True, **attr):

        return A(S3Method.crud_string(r.tablename,
                                      "label_create_button"),
                 _href=r.url(method="create", id=0, vars={}),
                 _class="action-btn",
                )
                
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
                             self.deploy_deployment_id(
                                requires = IS_ONE_OF(current.db,
                                    "deploy_deployment.id",
                                    S3Represent(lookup="deploy_deployment"),
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
        crud_form = S3SQLCustomForm("deployment_id",
                                    "subject",
                                    "body",
                                    "created_on",
                                    )

        # Table Configuration
        configure(tablename,
                  super_entity = "pr_pentity",
                  context = {"deployment": "deployment_id"},
                  crud_form = crud_form,
                  list_fields = ["deployment_id",
                                 "subject",
                                 "body",
                                 "alert_recipient.human_resource_id",
                                 ],
                  )

        # Components
        add_component("deploy_alert_recipient",
                      deploy_alert=dict(name="recipient",
                                        joinby="alert_id"))

        add_component("deploy_response", deploy_alert="alert_id")

        # Custom Methods
        set_method("deploy", "alert",
                   method="select",
                   action=self.deploy_alert_select_recipients)

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
                             self.deploy_deployment_id(),
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
                             message_id(),
                             *s3_meta_fields())

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
    def deploy_alert_select_recipients(r, **attr):
        """
            Custom Method to select recipients for an Alert
        """

        alert_id = r.id
        if r.representation not in ("html", "aadata") or not alert_id or r.component:
            raise HTTP(501, BADMETHOD)

        T = current.T
        s3db = current.s3db

        if r.http == "POST":
            # Why not in r.post_vars?
            selected = current.request._post_vars.get("selected", None)
            if selected:
                selected = selected.split(",")
                table = s3db.deploy_alert_recipient
                for s in selected:
                    table.insert(alert_id = alert_id,
                                 human_resource_id = s)
                current.response.confirmation = T("Recipients added to Alert")
            else:
                current.response.warning = T("No Recipients Selected!")

        get_vars = r.get_vars or {}
        response = current.response
        settings = current.deployment_settings

        resource = s3db.resource("hrm_human_resource")
        list_fields = ["id",
                       "person_id",
                       "job_title_id",
                       "organisation_id",
                       "department_id",
                       "site_id",
                       (T("Email"), "email.value"),
                       (settings.get_ui_label_mobile_phone(), "phone.value"),
                       ]
        totalrows = resource.count()
        if "iDisplayLength" in get_vars:
            display_length = int(get_vars["iDisplayLength"])
        else:
            display_length = 10
        limit = 4 * display_length

        filter, orderby, left = resource.datatable_filter(list_fields,
                                                          get_vars)
        resource.add_filter(filter)

        data = resource.select(list_fields,
                               start=0,
                               limit=limit,
                               orderby=orderby,
                               left=left,
                               count=True,
                               represent=True)
        filteredrows = data["numrows"]
        rfields = data["rfields"]
        rows = data["rows"]

        dt = S3DataTable(rfields, rows)
        dt_id = "hr_dt"

        if r.extension == "html":
            s3db.configure("hrm_human_resource",
                           deletable = False,
                           )
            dt.defaultActionButtons(resource)
            response.s3.no_formats = True

            items = dt.html(totalrows,
                            filteredrows,
                            dt_id,
                            dt_displayLength=display_length,
                            dt_ajax_url=URL(c="deploy",
                                            f="alert",
                                            args=[alert_id, "select"],
                                            extension="aadata",
                                            vars={"id": dt_id},
                                            ),
                            dt_pagination="true",
                            dt_bulk_actions = [(T("Select"), "select")],
                            )
            output = dict(items=items,
                          title = T("Select Recipients"),
                          )

            # Maintain RHeader for consistency
            if attr.get("rheader"):
                rheader = attr["rheader"](r)
                if rheader:
                    output["rheader"] = rheader

            response.view = "deploy/select.html"
            return output

        elif r.extension == "aadata":
            if "sEcho" in get_vars:
                echo = int(get_vars.sEcho)
            else:
                echo = None
            items = dt.json(totalrows,
                            filteredrows,
                            dt_id,
                            echo,
                            dt_bulk_actions = [(T("Select"), "select")],
                            )

            response.headers["Content-Type"] = "application/json"
            return items

        else:
            from gluon.http import HTTP
            raise HTTP(501, resource.ERROR.BAD_FORMAT)

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
        # Always redirect to the Deployment Profile
        next_url = URL(f="deployment", args=[record.deployment_id, "profile"])

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

        # Embed the alert_id to parse replies
        # = @ToDo: Use a Message Template to add Footer (very simple one for RDRT)
        message = "%s\nalert_id:%s:" % (record.body, alert_id)

        # Lookup from_address
        # @ToDo: Allow multiple channels to be defined &
        #        select the appropriate one for this deployment
        table = s3db.msg_email_channel
        channel = db(table.deleted == False).select(table.username,
                                                    table.server,
                                                    limitby = (0, 1)
                                                    ).first()
        if not channel:
            current.session.error = T("Need to configure an Email Address!")
            redirect(URL(f="email_channel"))

        from_address = "%s@%s" % (username, server)

        # @ToDo: Support alternate channels, like SMS
        # if not body: body = subject
        message_id = current.msg.send_by_pe_id(record.pe_id,
                                               subject=record.subject,
                                               message=message,
                                               from_address=from_address
                                               )

        # Update the Alert to show it's been Sent
        db(table.id == alert_id).update(message_id=message_id)

        # Return to the Deployment Profile
        current.session.confirmation = T("Alert Sent")
        redirect(next_url)

# =============================================================================
def deploy_rheader(r, tabs=[]):
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
        # Tabs
        tabs = [(T("Basic Details"), None),
                (T("Select"), "select"),
                (T("Recipients"), "recipient"),
                (T("Responses"), "response"),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)

        alert_id = r.id
        db = current.db
        ltable = db.deploy_alert_recipient
        query = (ltable.alert_id == alert_id) & \
                (ltable.deleted == False)
        recipients = db(query).select(ltable.id,
                                      limitby=(0, 1)).first()
        if recipients:
            send_button = S3CRUD.crud_button(T("Send Alert"),
                                             _href=URL(c="deploy", f="alert",
                                                       args=[alert_id, "send"]),
                                             #_id="send-alert-btn",
                                             )
        else:
            send_button = ""

        rheader = DIV(TABLE(TR(TH("%s: " % table.deployment_id.label),
                               table.deployment_id.represent(record.deployment_id),
                               send_button,
                               ),
                            TR(TH("%s: " % table.subject.label),
                               record.subject
                               ),
                            ), rheader_tabs)

    elif resourcename == "deployment":
        # Unused
        # Tabs
        tabs = [(T("Basic Details"), None),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name
                               ),
                            ), rheader_tabs)

    return rheader

# =============================================================================
def deploy_deployment_hrquantity(row):
    """ Number of human resources deployed """

    if hasattr(row, "deploy_deployment"):
        row = row.deploy_deployment
    try:
        deployment_id = row.id
    except AttributeError:
        return 0

    db = current.db
    table = db.deploy_human_resource_assignment
    count = table.id.count()
    row = db(table.deployment_id == deployment_id).select(count).first()
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
        in deploy_deployment profile header and cards.

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
            value = field.represent(record[fname])
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
def deploy_deployment_rheader(r, profile=False):
    """
        Header for deployment pages

        @param r: the S3Request
        @param profile: render an S3Profile header (with edit button)
                        rather than an rheader
    """

    if not profile and not r.component:
        return ""

    crud_string = S3Method.crud_string

    record = r.record
    title = crud_string(r.tablename, "title_display")
    if record:
        render = lambda *columns: deploy_render_profile_data(record,
                                                             table=r.table,
                                                             prefix="header",
                                                             columns=columns)

        title = "%s: %s" % (title, record.name)
        data = render("location_id", "created_on", "status")
        if profile:
            crud_button = r.resource.crud.crud_button
            edit_btn = crud_button(current.T("Edit"), _href=r.url(method="update"))
            data.append(edit_btn)
        header = DIV(H2(title),
                     data,
                     _class="profile-header")

        return header
    else:
        return H2(title)
        
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

    pkey = "deploy_alert.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        record_id = None
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    created_on = record["deploy_alert.created_on"]
    subject = record["deploy_alert.subject"]
    body = record["deploy_alert.body"]

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
                                  args=["IFRC", "img", "alert.png"]),
                         ),
                         _class="pull-left",
                         _href="#",
                   ),
                   toolbox,
                   DIV(DIV(DIV(subject,
                               _class="card-title"),
                           DIV(created_on,
                               _class="card-subtitle"),
                           _class="media-heading"),
                       DIV(body, _class="alert-message-body s3-truncate"),
                       #render("deploy_human_resource_assignment.start_date",
                              #"deploy_human_resource_assignment.end_date",
                              #"deploy_human_resource_assignment.rating",
                       #),
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
        Item renderer for data list of assigned human resources

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
                         _href=profile_url,
                         _title=profile_title,
                   ),
                   toolbox,
                   DIV(DIV(DIV(person,
                               _class="card-title"),
                           DIV(organisation,
                               _class="card-category"),
                           _class="media-heading"),
                       render("deploy_human_resource_assignment.start_date",
                              "deploy_human_resource_assignment.end_date",
                              "deploy_human_resource_assignment.rating",
                       ),
                       _class="media-body",
                   ),
                   _class="media",
               ),
               _class=item_class,
               _id=item_id,
           )

    return item

# END =========================================================================
