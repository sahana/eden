# -*- coding: utf-8 -*-

"""
    Deployments
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Customisable module homepage """

    return settings.customise_home(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Fallback for module homepage when not customised and
        no CMS content found (ADMINs will see CMS edit unless
        disabled globally via settings.cms.hide_index)
    """

    # Just redirect to the Mission Summary View
    s3_redirect_default(URL(f="mission", args="summary"))

# -----------------------------------------------------------------------------
def mission():
    """ RESTful CRUD Controller """

    def prep(r):
        # Configure created_on field in deploy_mission
        #created_on = r.table.created_on
        #created_on.readable = True
        #created_on.label = T("Date Created")
        #created_on.represent = lambda d: \
        #                       s3base.S3DateTime.date_represent(d, utc=True)
        if r.id:
            # Mission-specific workflows return to the profile page
            tablename = r.tablename if not r.component else r.component.tablename
            next_url = r.url(component="", method="profile", vars={})
            if r.component_name == "alert":
                alert_create_script()
                if settings.get_deploy_manual_recipients():
                    create_next = URL(f="alert", args=["[id]", "select"])
                else:
                    create_next = next_url
                s3db.configure(tablename,
                               create_next = create_next,
                               delete_next = next_url,
                               update_next = next_url,
                               )
            else:
                s3db.configure(tablename,
                               create_next = next_url,
                               delete_next = next_url,
                               update_next = next_url,
                               )
            s3.cancel = next_url
            if r.component_name == "assignment":
                member_id = r.get_vars.get("member_id", None)
                if member_id and str(member_id).isdigit():
                    # Deploy-this-member action
                    htable = s3db.hrm_human_resource
                    query = (htable.id == member_id) & \
                            (htable.deleted != True)
                    row = db(query).select(htable.id,
                                           limitby = (0, 1)
                                           ).first()
                    if row:
                        field = s3db.deploy_assignment.human_resource_id
                        field.default = row.id
                        field.writable = False
                        field.comment = None
                elif r.method == "create":
                    atable = s3db.deploy_assignment
                    atable.end_date.writable = atable.end_date.readable = False
            if not r.component and r.method == "profile":
                represent = lambda d: \
                            s3base.S3DateTime.datetime_represent(d, utc=True)
                s3db.deploy_alert.modified_on.represent = represent
                s3db.deploy_response.created_on.represent = represent
                s3base.s3_trunk8(lines=1)
        else:
            # All other workflows return to the summary page
            s3.cancel = r.url(method="summary", component=None, id=0)
            if not r.component:
                status = r.get_vars.get("~.status__belongs")
                if status == "2":
                    s3.crud_strings[r.tablename]["title_list"] = T("Active Missions")
                elif status == "1":
                    s3.crud_strings[r.tablename]["title_list"] = T("Closed Missions")

        return True
    s3.prep = prep

    def postp(r, output):
        if not r.component:
            # Override mission open actions to go to the profile page
            s3_action_buttons(r,
                              deletable = True,
                              editable = True,
                              read_url = r.url(method="profile", id="[id]"),
                              update_url = r.url(method="profile", id="[id]"),
                              delete_url = r.url(method="delete", id="[id]"),
                              )
            # Override the missions list-button go to the summary page
            if isinstance(output, dict) and "buttons" in output:
                # Override standard "List" button
                buttons = output["buttons"]
                if "list_btn" in buttons and "summary_btn" in buttons:
                    buttons["list_btn"] = buttons["summary_btn"]

        elif "subtitle" in output and "rheader" in output:
            # In component CRUD views, have a subtitle after the rheader
            output["rheader"] = TAG[""](output["rheader"],
                                        H3(output["subtitle"]))

        return output
    s3.postp = postp

    return s3_rest_controller(# Remove the title if we have a component
                              # (rheader includes the title)
                              notitle = lambda r: {"title": ""} \
                                               if r.component else None,
                              rheader = s3db.deploy_rheader,
                              )

# -----------------------------------------------------------------------------
def response_message():
    """
        RESTful CRUD Controller
        - can't be called 'response' as this clobbbers web2py global!
    """

    return s3_rest_controller("deploy", "response",
                              custom_crud_buttons = {"list_btn": None},
                              )

# -----------------------------------------------------------------------------
def human_resource():
    """
        RESTful CRUD Controller
    """

    # Tweak settings for RDRT
    # @ToDo: These should really be in customise_ in IFRC template
    settings.hrm.staff_experience = True
    settings.hrm.use_skills = True
    settings.search.filter_manager = True

    # Add deploy_alert_recipient as component so that we can filter by it
    s3db.add_components("hrm_human_resource",
                        deploy_alert_recipient = "human_resource_id",
                        )

    # Filter to just Deployables
    q = FS("application.active") != None
    output = s3db.hrm_human_resource_controller(extra_filter = q)
    return output

# -----------------------------------------------------------------------------
def person():
    """
        'Members' RESTful CRUD Controller
            - used as "member profile"
            - used for Imports
    """

    # Tweak settings for RDRT
    settings.hrm.staff_experience = "experience"
    settings.hrm.vol_experience = "experience"
    settings.hrm.use_skills = True
    settings.search.filter_manager = True

    # Use Legacy table for unavailability
    s3db.add_components("pr_person",
                        deploy_unavailability = "person_id",
                        )

    return s3db.hrm_person_controller(replace_option = None,
                                      csv_extra_fields = [
                                            # CSV column headers, so no T()
                                            dict(label="Deployable",
                                                 value="true"),
                                            # Assume volunteer if not
                                            # specified in CSV
                                            dict(label="Type",
                                                 value="volunteer"),
                                            ],
                                      csv_stylesheet = ("hrm", "person.xsl"),
                                      csv_template = ("deploy", "person"),
                                      )

# -----------------------------------------------------------------------------
def group():
    """
        Groups RESTful CRUD Controller
            - used to control membership of a group cc'd on Alerts
    """

    def prep(r):

        tablename = "pr_group"
        s3db.configure(tablename,
                       deletable = False,
                       )

        if r.component:

            if r.component_name == "group_membership":

                ctable = r.component.table

                # Hide group_head field
                field = ctable.group_head
                field.readable = field.writable = False

                # Configure person_id widget
                settings.pr.request_dob = False
                settings.pr.request_gender = False

                field = ctable.person_id
                field.widget = s3base.S3AddPersonWidget(controller="deploy")

                # Configure list_fields for this context
                list_fields = ["person_id",
                               "comments",
                               ]
                s3db.configure("pr_group_membership",
                               list_fields = list_fields,
                               )
        elif not r.id:

            table = r.table

            # Have we got a group defined?
            ltable = s3db.org_organisation_team
            query = (table.deleted == False) & \
                    (table.system == False) & \
                    (table.group_type == 5)
            organisation_id = auth.user.organisation_id
            if organisation_id:
                left = ltable.on((ltable.group_id == table.id) & \
                                 ((ltable.organisation_id == organisation_id) | \
                                  (ltable.organisation_id == None)))
            else:
                left = None
            groups = db(query).select(table.id,
                                      ltable.organisation_id,
                                      left = left,
                                      )
            if organisation_id and len(groups) > 1:
                _channels = groups.find(lambda row: row["org_organisation_team.organisation_id"] == organisation_id)
                if not _channels:
                    _channels = groups.find(lambda row: row["org_organisation_team.organisation_id"] == None)
                record = _channels.first()
            else:
                record = groups.first()

            if record:
                record_id = record.pr_group.id
                r.id = record_id
                r.resource.add_filter(table.id == record_id)
                r.method = "update"
            else:
                r.method = "create"

        return True
    s3.prep = prep

    return s3_rest_controller("pr", "group")

# -----------------------------------------------------------------------------
def application():
    """
        Custom workflow to manually create standing applications
        for deployments (for staff/volunteers)
    """

    # Tweak settings for RDRT
    settings.hrm.staff_experience = True
    settings.hrm.use_skills = True
    settings.search.filter_manager = True

    def prep(r):
        method = r.method
        if not method and r.representation != "s3json":
            r.method = method = "select"
        if method == "select":
            r.custom_action = s3db.deploy_apply
        return True
    s3.prep = prep

    if "delete" in request.args or \
       request.env.request_method == "POST" and auth.permission.format=="s3json":
        return s3_rest_controller()
    else:
        #return s3db.hrm_human_resource_controller()
        return s3_rest_controller("hrm", "human_resource")

# -----------------------------------------------------------------------------
def assignment():
    """ RESTful CRUD Controller """

    def prep(r):
        mission_date = s3db.deploy_mission.created_on
        mission_date.represent = lambda d: \
                                 s3base.S3DateTime.date_represent(d, utc=True)
        if r.record:
            table = r.resource.table
            table.mission_id.writable = False
            table.human_resource_id.writable = False

        if r.representation == "popup":
            r.resource.configure(insertable=False)

        return True
    s3.prep = prep

    def postp(r, output):
        if r.id and isinstance(output, dict):
            # Add button to Upload Appraisal
            popup = r.representation == "popup"
            record_id = r.id
            atable = s3db.hrm_appraisal
            ltable = s3db.deploy_assignment_appraisal
            query = (ltable.assignment_id == record_id) & \
                    (atable.id == ltable.appraisal_id) & \
                    (atable.deleted != True)
            appraisal = db(query).select(atable.id,
                                         limitby=(0, 1)).first()
            permit = auth.s3_has_permission
            url = None
            if appraisal and permit("update", atable, record_id=appraisal.id):
                hrtable = db.hrm_human_resource
                hr = db(hrtable.id == r.record.human_resource_id).select(hrtable.person_id,
                                                                         limitby=(0, 1)
                                                                         ).first()
                if hr:
                    get_vars = {}
                    if popup:
                        method = "update.popup"
                        refresh = get_vars.get("refresh", None)
                        if refresh:
                            get_vars["refresh"] = refresh
                        record = get_vars.get("record", None)
                        if record:
                            get_vars["record"] = record
                    else:
                        method = "update"
                    url = URL(c="deploy", f="person",
                              args=[hr.person_id, "appraisal",
                                    appraisal.id, method],
                              vars=get_vars,
                              )
            elif permit("update", r.table, record_id=record_id):
                # Currently we assume that anyone who can edit the assignment can upload the appraisal
                hrtable = db.hrm_human_resource
                hr = db(hrtable.id == r.record.human_resource_id).select(hrtable.person_id,
                                                                         limitby=(0, 1)
                                                                         ).first()
                if hr:
                    get_vars = {"mission_id": r.record.mission_id,
                                }

                    if popup:
                        method = "create.popup"
                        refresh = get_vars.get("refresh", None)
                        if refresh:
                            get_vars["refresh"] = refresh
                        record = get_vars.get("record", None)
                        if record:
                            get_vars["record"] = record
                    else:
                        method = "create"
                    url = URL(c="deploy", f="person",
                              args=[hr.person_id, "appraisal", method],
                              vars=get_vars,
                              )
            if url:
                button = s3base.S3CRUD.crud_button(T("Upload Appraisal"),
                                                   _href=url,
                                                   _class="action-btn",
                                                   )
                if popup:
                    output["items"] = button
                else:
                    s3.rfooter = button
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def competency():
    """ RESTful CRUD controller - unfiltered version """

    return s3db.hrm_competency_controller()

# -----------------------------------------------------------------------------
def credential():
    """ RESTful CRUD controller - unfiltered version """

    return s3db.hrm_credential_controller()

# -----------------------------------------------------------------------------
def experience():
    """ Experience Controller - unfiltered version """

    return s3db.hrm_experience_controller()

# -----------------------------------------------------------------------------
def event_type():
    """ RESTful CRUD Controller """

    return s3_rest_controller("event", "event_type")

# -----------------------------------------------------------------------------
def job_title():
    """ RESTful CRUD Controller """

    return s3_rest_controller("hrm", "job_title")

# -----------------------------------------------------------------------------
def training():
    """ Training Controller - unfiltered version """

    return s3db.hrm_training_controller()

# -----------------------------------------------------------------------------
def hr_search():
    """
        Human Resource REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    # Filter to just deployables (RDRT Members)
    s3.filter = FS("application.active") == True

    s3.prep = lambda r: r.method == "search_ac"

    return s3_rest_controller("hrm", "human_resource")

# -----------------------------------------------------------------------------
def person_search():
    """
        Person REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    # Filter to just deployables (RDRT Members)
    s3.filter = FS("application.active") == True

    s3.prep = lambda r: r.method == "search_ac"

    return s3_rest_controller("pr", "person")

# -----------------------------------------------------------------------------
def alert_create_script():
    """
        Inject JS to help the Alert creation form
    """

    # @ToDo: Generalise for alternate gateways
    # @ToDo: Port to _compose_form
    table = s3db.msg_sms_webapi_channel
    gateway = db(table.enabled == True).select(table.max_length,
                                               limitby=(0, 1)
                                               ).first()
    if gateway:
        max_length = gateway.max_length
        if max_length is None:
            # Single SMS
            max_length = 160
    else:
        # Single SMS
        max_length = 160

    script = \
'''$('#deploy_alert_contact_method').change(function(){
 var v=$(this).val()
 if(v==1){$('#deploy_alert_subject__row,#deploy_alert_subject__row1').show()
  $('#deploy_alert_subject__row1 label').html(i18n.subject+':')
  S3.maxLength.init('deploy_alert_body',0)
 }else if(v==2){$('#deploy_alert_subject__row,#deploy_alert_subject__row1').hide()
  S3.maxLength.init('deploy_alert_body',%(max_length)s)
 }else if(v==9){$('#deploy_alert_subject__row,#deploy_alert_subject__row1').show()
  $('#deploy_alert_subject__row1 label').html(i18n.subject+': <span class="red">'+i18n.only_visible+'</span>')
  S3.maxLength.init('deploy_alert_body',%(max_length)s)
}})''' % dict(max_length = max_length)
    s3.jquery_ready.append(script)
    i18n = \
'''i18n.characters_left="%s"
i18n.subject="%s"
i18n.only_visible="%s"''' % (T("characters left"),
                             T("Subject"),
                             T("Only visible to Email recipients"))
    s3.js_global.append(i18n)

# -----------------------------------------------------------------------------
def alert():
    """ RESTful CRUD Controller """

    # Tweak settings for RDRT
    settings.hrm.staff_experience = True
    settings.hrm.use_skills = True
    settings.search.filter_manager = True

    def prep(r):
        if r.component:
            if r.component.alias == "select":
                if not r.method:
                    r.method = "select"
                if r.method == "select":
                    r.custom_action = s3db.deploy_alert_select_recipients

            elif r.component_name == "response":
                s3db.configure(r.component.tablename,
                               deletable = False,
                               editable = False,
                               insertable = False,
                               )

            elif r.component_name == "recipient":
                settings.search.filter_manager = False
                from s3 import S3TextFilter, S3OptionsFilter
                recipient_filters = [
                    S3TextFilter([
                            "human_resource_id$person_id$first_name",
                            "human_resource_id$person_id$middle_name",
                            "human_resource_id$person_id$last_name",
                        ],
                        label=current.T("Name"),
                    ),
                    S3OptionsFilter(
                        "human_resource_id$organisation_id",
                        widget="multiselect",
                        search=True,
                        header="",
                        hidden=True,
                    ),
                ]
                if settings.get_org_regions():
                    recipient_filters.insert(1,
                        s3base.S3HierarchyFilter(
                            "human_resource_id$organisation_id$region_id",
                            lookup="org_region",
                            hidden=True,
                        )
                    )
                s3db.configure(r.component.tablename,
                               filter_widgets = recipient_filters,
                               )

                if r.record.message_id:
                    s3db.configure(r.component.tablename,
                                   deletable = False,
                                   insertable = False,
                                   )
        else:
            # No component
            if r.record:
                if r.record.message_id:
                    # Already sent - so lock
                    s3db.configure(r.tablename,
                                   deletable = False,
                                   editable = False,
                                   )
            else:
                alert_create_script()
                if settings.get_deploy_manual_recipients():
                    create_next = URL(f="alert", args=["[id]", "select"])
                else:
                    create_next = URL(f="alert", args=["[id]", "recipient"])
                s3db.configure(r.tablename,
                               create_next = create_next,
                               deletable = False,
                               # @ToDo: restrict in postp to change this action button
                               #editable = False,
                               )

        return True
    s3.prep = prep

    def postp(r, output):
        if r.component:
            if r.component_name == "select":
                s3.actions = [{"label": str(READ),
                               "url": URL(f="human_resource",
                                          args=["[id]", "profile"],
                                          ),
                               "_class": "action-btn read",
                               }
                              ]

            if r.component_name == "recipient":
                # Open should open the HR profile, not the link
                open_url = URL(f="human_resource",
                               args=["profile"],
                               vars={"alert_recipient.id": "[id]"},
                               )
                # Delete should delete the link, not the HR profile
                delete_url = URL(f="alert",
                                 args=[r.id, "recipient", "[id]", "delete"],
                                 )
                s3_action_buttons(r,
                                  read_url = open_url,
                                  update_url = open_url,
                                  delete_url = delete_url,
                                  # Can't delete recipients after the alert
                                  # has been sent:
                                  deletable = not r.record.message_id
                                  )
        else:
            # Delete should only be possible if the Alert hasn't yet been sent
            table = r.table
            query = auth.s3_accessible_query("delete", "deploy_alert") & \
                    (table.message_id == None)
            rows = db(query).select(table.id)
            restrict = [str(row.id) for row in rows]
            s3.actions = [{"label": str(READ),
                           "url": URL(f="alert", args="[id]"),
                           "_class": "action-btn read",
                           },
                          {"label": str(DELETE),
                           "url": URL(f="alert", args=["[id]", "delete"]),
                           "restrict": restrict,
                           "_class": "delete-btn",
                           },
                          ]

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.deploy_rheader,
                              # Show filter only on recipient tab
                              hide_filter = {"recipient": False,
                                             "_default": True,
                                             }
                              )

# -----------------------------------------------------------------------------
def alert_response():
    """
        RESTful CRUD Controller
        - used to allow RIT Memebers to apply for Positions

        @ToDo: Block all methods but CREATE => what next_url?
    """

    alert_id = get_vars.get("alert_id")
    if alert_id:
        table = s3db.deploy_response
        f = table.alert_id
        f.readable = f.writable = False
        f.default = alert_id
        atable = s3db.deploy_alert
        alert = db(atable.id == alert_id).select(atable.mission_id,
                                                 limitby=(0, 1),
                                                 ).first()
        if alert:
            f = table.mission_id
            f.readable = f.writable = False
            f.default = alert.mission_id
        human_resource_id = auth.s3_logged_in_human_resource()
        if human_resource_id:
            f = table.human_resource_id_id
            f.readable = f.writable = False
            f.default = alert_id
        table.message_id.readable = False
    #else:
    #    # Block
    #    pass

    return s3_rest_controller("deploy", "response")

# -----------------------------------------------------------------------------
def email_inbox():
    """
        RESTful CRUD controller for the Email Inbox
        - all Inbound Email Messages are visible here

        @ToDo: Filter to those which have been unable to be automatically
               processed as being responses to Alerts
        @ToDo: Filter to those coming into the specific account used for
               Deployments
        @ToDo: Provide a mechanism (Action button?) to link a mail manually to
               an Alert
    """

    if not auth.s3_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(c="default", f="user", args="login"))

    tablename = "msg_email"
    table = s3db.msg_email
    table.inbound.readable = False
    table.channel_id.readable = False
    table.to_address.readable = False

    from s3.s3query import FS
    s3.filter = (FS("response.id") == None) & \
                (FS("inbound") == True)

    from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
    crud_form = S3SQLCustomForm("date",
                                "subject",
                                "from_address",
                                "body",
                                S3SQLInlineComponent(
                                    "attachment",
                                    name = "document_id",
                                    label = T("Attachments"),
                                    fields = ["document_id"],
                                    ),
                                )

    s3db.configure(tablename,
                   crud_form = crud_form,
                   editable = False,
                   insertable = False,
                   list_fields = ["id",
                                  "date",
                                  "from_address",
                                  "subject",
                                  "body",
                                  (T("Attachments"), "attachment.document_id"),
                                  ],
                   )

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_list = T("View InBox"),
        title_update = T("Edit Message"),
        label_list_button = T("View InBox"),
        label_delete_button = T("Delete Message"),
        msg_record_modified = T("Message updated"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No Messages currently in InBox")
    )

    def prep(r):
        # Decode subject and sender fields
        decode = current.msg.decode_email
        if r.id:
            s3db.msg_attachment.document_id.label = ""
            if r.component and r.component.alias == "select":
                if not r.method:
                    r.method = "select"
                if r.method == "select":
                    r.custom_action = s3db.deploy_response_select_mission
            represent = lambda string: decode(string)
        elif not r.method and r.representation in ("html", "aadata"):
            # Use custom data table method to allow bulk deletion
            r.method = "inbox"
            r.custom_action = s3db.deploy_Inbox()
            represent = lambda string: s3base.s3_datatable_truncate(decode(string))
        table = r.resource.table
        table.subject.represent = represent
        table.from_address.represent = represent
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and r.record and not r.component:
            # Custom CRUD button for linking the message to mission
            authorised = auth.s3_has_permission("create", "deploy_response")
            if authorised:
                s3.rfooter = s3base.S3CRUD.crud_button(
                                        T("Link to Mission"),
                                        _href=URL(f="email_inbox",
                                                  args=[r.id, "select"],
                                                  ),
                                        _class="action-btn link",
                                        )
        return output
    s3.postp = postp

    return s3_rest_controller("msg", "email")

# -----------------------------------------------------------------------------
def email_channel():
    """
        RESTful CRUD controller for Inbound Email channels

        @ToDo: Allow selection of a specific Channel for Alerts
    """

    def prep(r):
        table = r.table
        tablename = "msg_email_channel"
        s3db.configure(tablename,
                       deletable = False,
                       )

        if not r.id:
            # Have we got a channel defined?
            query = (table.deleted == False) & \
                    (table.enabled == True)
            organisation_id = auth.user.organisation_id
            if organisation_id:
                query &= ((table.organisation_id == organisation_id) | \
                          (table.organisation_id == None))
            channels = db(query).select(table.id,
                                        table.organisation_id,
                                        )
            if organisation_id and len(channels) > 1:
                _channels = channels.find(lambda row: row.organisation_id == organisation_id)
                if not _channels:
                    _channels = channels.find(lambda row: row.organisation_id == None)
                record = _channels.first()
            else:
                record = channels.first()

            if record:
                record_id = record.id
                r.id = record_id
                r.resource.add_filter(table.id == record_id)
                r.method = "update"
            else:
                r.method = "create"

        if r.interactive:
            table.server.label = T("Server")
            table.protocol.label = T("Protocol")
            table.use_ssl.label = "SSL"
            table.port.label = T("Port")
            table.username.label = T("Username")
            table.password.label = T("Password")
            table.delete_from_server.label = T("Delete from Server?")
            table.port.comment = DIV(_class="tooltip",
                                     _title="%s|%s" % (T("Port"),
                                                       T("For POP-3 this is usually 110 (995 for SSL), for IMAP this is usually 143 (993 for IMAP).")))
            table.delete_from_server.comment = DIV(_class="tooltip",
                                                   _title="%s|%s" % (T("Delete"),
                                                                     T("If this is set to True then mails will be deleted from the server after downloading.")))

            # CRUD Strings
            s3.crud_strings[tablename] = Storage(
                title_display = T("Email Settings"),
                title_list = T("Email Accounts"),
                label_create = T("Create Email Account"),
                title_update = T("Edit Email Settings"),
                label_list_button = T("View Email Accounts"),
                msg_record_created = T("Account added"),
                msg_record_deleted = T("Email Account deleted"),
                msg_list_empty = T("No Accounts currently defined"),
                msg_record_modified = T("Email Settings updated")
                )

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and isinstance(output, dict) and \
           not s3task._is_alive():
            poll_btn = A(T("Poll"),
                         _class="action-btn",
                         _href=URL(args=[r.id, "poll"])
                         )
            output["rheader"] = poll_btn
        return output
    s3.postp = postp

    return s3_rest_controller("msg")

# -----------------------------------------------------------------------------
def twitter_channel():
    """
        RESTful CRUD controller for Twitter channels
        - appears in the administration menu
        Only 1 of these normally in existence
            @ToDo: Don't enforce
    """

    def prep(r):
        table = r.table
        tablename = "msg_twitter_channel"
        s3db.configure(tablename,
                       deletable = False,
                       )

        if not r.id:
            # Have we got a channel defined?
            query = (table.deleted == False) & \
                    (table.enabled == True)
            #organisation_id = auth.user.organisation_id
            #if organisation_id:
            #    query &= ((table.organisation_id == organisation_id) | \
            #              (table.organisation_id == None))
            #channels = db(query).select(table.id,
            #                            table.organisation_id,
            #                            )
            #if organisation_id and len(channels) > 1:
            #    _channels = channels.find(lambda row: row.organisation_id == organisation_id)
            #    if not _channels:
            #        _channels = channels.find(lambda row: row.organisation_id == None)
            #    record = _channels.first()
            #else:
            #    record = channels.first()

            record = db(query).select(table.id,
                                      limitby = (0, 1)
                                      )

            if record:
                record_id = record.id
                r.id = record_id
                r.resource.add_filter(table.id == record_id)
                r.method = "update"
            else:
                r.method = "create"

        if r.interactive:
            table.twitter_account.label = T("Current Twitter account")

            # CRUD Strings
            s3.crud_strings[tablename] = Storage(
                title_display = T("Twitter Settings"),
                title_list = T("Twitter Accounts"),
                label_create = T("Create Twitter Account"),
                title_update = T("Edit Twitter account"),
                label_list_button = T("View Twitter Accounts"),
                msg_record_created = T("Account added"),
                msg_record_deleted = T("Twitter Account deleted"),
                msg_list_empty = T("No Accounts currently defined"),
                msg_record_modified = T("Twitter Settings updated")
                )

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [{"label": s3_str(T("Enable")),
                            "_class": "action-btn",
                            "url": URL(args=["[id]", "enable"]),
                            "restrict": restrict_e,
                            },
                           {"label": s3_str(T("Disable")),
                            "_class": "action-btn",
                            "url": URL(args = ["[id]", "disable"]),
                            "restrict": restrict_d,
                            },
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [{"label": s3_str(T("Poll")),
                                "_class": "action-btn",
                                "url": URL(args = ["[id]", "poll"]),
                                "restrict": restrict_d,
                                },
                               ]
        return output
    s3.postp = postp

    return s3_rest_controller("msg",
                              deduplicate = "",
                              list_btn = "",
                              )

# -----------------------------------------------------------------------------
def alert_recipient():
    """
        RESTful CRUD controller for options.s3json lookups
        - needed for adding recipients
    """

    s3.prep = lambda r: r.method == "options" and r.representation == "s3json"

    return s3_rest_controller()

# -----------------------------------------------------------------------------
# Messaging
#
def compose():
    """ Send message to people/teams """

    return s3db.hrm_compose()

# END =========================================================================
