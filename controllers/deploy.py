# -*- coding: utf-8 -*-

"""
    Deployments
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

s3db.hrm_vars()

# =============================================================================
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)
    
# =============================================================================
def mission():
    """ RESTful CRUD Controller """

    def prep(r):
        # Configure created_on field in deploy_mission
        created_on = r.table.created_on
        created_on.readable = True
        created_on.label = T("Date Created")
        created_on.represent = lambda d: \
                               s3base.S3DateTime.date_represent(d, utc=True)
        if r.id:
            # Mission-specific workflows return to the profile page
            tablename = r.tablename if not r.component else r.component.tablename
            next_url = r.url(component="", method="profile", vars={})
            if r.component_name == "alert":
                s3db.configure(tablename,
                               create_next=URL(f="alert",
                                               args=["[id]", "select"]),
                               update_next=next_url,
                               delete_next=next_url,
                               )
            else:
                s3db.configure(tablename,
                               create_next=next_url,
                               update_next=next_url,
                               delete_next=next_url)
            s3.cancel = next_url
            if r.component_name == "human_resource_assignment":
                get_vars = r.get_vars
                if "member_id" in get_vars:
                    # Deploy-this-member action
                    member_id = get_vars["member_id"]
                    if str(member_id).isdigit():
                        # Check if this member exists, otherwise ignore
                        htable = s3db.hrm_human_resource
                        query = (htable.id == member_id) & \
                                (htable.deleted != True)
                        row = db(query).select(htable.id, limitby=(0, 1)).first()
                        if row:
                            field = s3db.deploy_human_resource_assignment \
                                        .human_resource_id
                            field.default = row.id
                            field.writable = False
                            field.comment = None
            if not r.component and r.method == "profile":
                represent = lambda d: \
                            s3base.S3DateTime.datetime_represent(d, utc=True)
                s3db.deploy_alert.created_on.represent = represent
                s3db.deploy_response.created_on.represent = represent
                s3base.s3_trunk8(lines=1)
        else:
            # All other workflows return to the summary page
            s3.cancel = r.url(method="summary", component=None, id=0)
        return True
    s3.prep = prep

    def postp(r, output):
        if not r.component:
            # Override mission open actions to go to the profile page
            s3_action_buttons(r,
                              editable=True,
                              deletable=True,
                              read_url=r.url(method="profile", id="[id]"),
                              update_url=r.url(method="profile", id="[id]"),
                              delete_url=r.url(method="delete", id="[id]"),
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

    return s3_rest_controller(hide_filter=False,
                              # Remove the title if we have a component
                              # (rheader includes the title)
                              notitle=lambda r: {"title": ""} \
                                             if r.component else None,
                              rheader=s3db.deploy_rheader)

# =============================================================================
def human_resource():
    """
        RESTful CRUD Controller
    """

    # Tweak settings for RDRT
    settings.hrm.staff_experience = True
    settings.hrm.use_skills = True
    settings.search.filter_manager = True

    # Add application component
    # @todo: move into HRM model
    s3db.add_component("deploy_human_resource_application",
                       hrm_human_resource="human_resource_id")

    q = s3base.S3FieldSelector("human_resource_application.active") == True
    output = s3db.hrm_human_resource_controller(extra_filter=q)
    if isinstance(output, dict) and "title" in output:
        output["title"] = T("RDRT Members")
    return output

# -----------------------------------------------------------------------------
def person():
    """
        'Members' RESTful CRUD Controller
            - currently used as "member profile"
            - used for Imports
    """

    # Tweak settings for RDRT
    settings.hrm.staff_experience = "experience"
    settings.hrm.vol_experience = "experience"
    settings.hrm.use_skills = True
    settings.search.filter_manager = True

    # @todo: move into HRM model
    s3db.add_component("deploy_human_resource_application",
                       hrm_human_resource="human_resource_id")

    # Replace default title in imports:
    retitle = lambda r: {"title": T("Import Members")} \
                        if r.method == "import" else None
    
    return s3db.hrm_person_controller(replace_option=None,
                                      csv_extra_fields=[
                                            dict(label="Deployable",
                                                 value="true"),
                                            # Assume volunteer if not
                                            # specified in CSV
                                            dict(label="Type",
                                                 value="volunteer"),
                                      ],
                                      retitle=retitle)

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
        if not r.method:
            r.method = "select"
        if r.method == "select":
            r.custom_action = s3db.deploy_application
        return True
    s3.prep = prep

    #return s3db.hrm_human_resource_controller()
    return s3_rest_controller("hrm", "human_resource")

# -----------------------------------------------------------------------------
def human_resource_assignment():
    """ RESTful CRUD Controller """

    def prep(r):
        if r.representation == "popup":
            r.resource.configure(insertable=False)
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def alert():
    """ RESTful CRUD Controller """

    # Tweak settings for RDRT
    settings.hrm.staff_experience = True
    settings.hrm.use_skills = True
    settings.search.filter_manager = True
    
    # Add application component
    # @todo: move into HRM model
    s3db.add_component("deploy_human_resource_application",
                       hrm_human_resource="human_resource_id")

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
                from s3.s3filter import S3TextFilter, S3OptionsFilter
                recipient_filters = [
                    s3base.S3TextFilter([
                            "human_resource_id$person_id$first_name",
                            "human_resource_id$person_id$middle_name",
                            "human_resource_id$person_id$last_name",
                        ],
                        label=current.T("Name"),
                    ),
                    s3base.S3OptionsFilter(
                        "human_resource_id$organisation_id",
                        widget="multiselect",
                        filter=True,
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
                               filter_widgets=recipient_filters)
                if r.record.message_id:
                    s3db.configure(r.component.tablename,
                                   insertable=False,
                                   deletable=False)
        else:
            if r.record:
                if r.record.message_id:
                    # Already sent - so lock
                    s3db.configure(r.tablename,
                                   deletable = False,
                                   editable = False,
                                   )
            else:
                s3db.configure(r.tablename,
                               deletable = False,
                               # @ToDo: restrict in postp to change this action button
                               #editable = False,
                               )

            # Hide label for single field in InlineComponent
            #s3db.deploy_alert_recipient.human_resource_id.label = ""
            created_on = r.table.created_on
            created_on.readable = True
            created_on.label = T("Date Created")
            created_on.represent = lambda d: \
                                   s3base.S3DateTime.date_represent(d, utc=True)
        return True
    s3.prep = prep

    def postp(r, output):
        if r.component:
            if r.component_name == "recipient":
                # Open should open the member profile, not the link
                s3.actions = [dict(label=str(READ),
                                   _class="action-btn read",
                                   url=URL(f="person",
                                           vars={"human_resource.id":"[id]"}))]
                if not r.record.message_id:
                    # Delete should remove the Link, not the Member
                    s3.actions.append(dict(label=str(DELETE),
                                           _class="delete-btn",
                                           url=URL(f="alert",


                                                   args=[r.id,
                                                         "recipient",
                                                         "[id]",
                                                         "delete"])))
        else:
            # Delete should only be possible if the Alert hasn't yet been sent
            table = r.table
            rows = db(table.message_id == None).select(table.id)
            restrict = [str(row.id) for row in rows]
            s3.actions = [dict(label=str(READ),
                               _class="action-btn read",
                               url=URL(f="alert",
                                       args="[id]")),
                          dict(label=str(DELETE),
                               _class="delete-btn",
                               restrict=restrict,
                               url=URL(f="alert",
                                       args=["[id]", "delete"])),
                          ]
        return output
    s3.postp = postp

    return s3_rest_controller(rheader=s3db.deploy_rheader,
                              hide_filter={"recipient": False,
                                           "_default": True})

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

    s3db.add_component("deploy_response",
                       msg_email="message_id")

    from s3.s3resource import S3FieldSelector
    s3.filter = (S3FieldSelector("response.id") == None) & \
                (S3FieldSelector("inbound") == True)

    s3db.configure(tablename,
                   insertable=False,
                   editable=False)

    s3db.set_method("msg", "email",
                    method="link",
                    action=link_response
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

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons
            s3.actions += [dict(label=str(T("Link to Mission")),
                                _class="action-btn link",
                                url=URL(f="email_inbox",
                                        args=["[id]", "link"])),
                           ]

        return output
    s3.postp = postp

    return s3_rest_controller("msg", "email")

# -----------------------------------------------------------------------------
def link_response(r, **attr):
    """
        Manually link an email to a Mission
    """

    if r.http == "POST":
        session.confirmation = T("Message Linked")
        redirect(URL(f="email_inbox"))

    formstyle = s3.crud.formstyle
    if not callable(formstyle):
        # Unsupported
        raise

    form = DIV()
    message_id = r.record.message_id
    htable = s3db.hrm_human_resource
    ptable = db.pr_person
    ctable = s3db.pr_contact
    query = (ctable.contact_method == "EMAIL") & \
            (ctable.value == r.record.from_address) & \
            (ctable.pe_id == ptable.pe_id) & \
            (ptable.id == htable.person_id)
    hr = db(query).select(htable.id,
                          limitby=(0, 1)).first()
    if hr:
        # Show read-only view
        pass
    else:
        # @ToDo: Search based on Name?
        if not hr:
            # Select HR
            pass

    comment = None
    # Show Dropdown for Missions
    id = "mission_id"
    label = T("Mission")
    widget = SELECT()
    row = formstyle(id, label, widget, comment, hidden=False)
    form.append(row)

    # Show Message
    id = "subject"
    label = T("Subject")
    widget = INPUT(_value=r.record.subject,
                   _readonly=True)
    row = formstyle(id, label, widget, comment, hidden=False)
    form.append(row)
    id = "body"
    label = T("Message")
    widget = TEXTAREA(_value=r.record.body,
                      _readonly=True)
    row = formstyle(id, label, widget, comment, hidden=False)
    form.append(row)

    output = dict(title=T("Link Response to Mission"),
                  form=form,
                  )
    response.view = "deploy/link_response.html"
    return output

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
                       deletable=False)

        if not r.id:
            # Have we got a channel defined?
            record = db(table.deleted == False).select(table.id,
                                                       limitby=(0, 1)
                                                       ).first()
            if record:
                r.id = record.id
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
            ADD_EMAIL_ACCOUNT = T("Add Email Account")
            s3.crud_strings[tablename] = Storage(
                title_display = T("Email Settings"),
                title_list = T("Email Accounts"),
                title_create = ADD_EMAIL_ACCOUNT,
                title_update = T("Edit Email Settings"),
                label_list_button = T("View Email Accounts"),
                label_create_button = ADD_EMAIL_ACCOUNT,
                subtitle_create = T("Add New Email Account"),
                msg_record_created = T("Account added"),
                msg_record_deleted = T("Email Account deleted"),
                msg_list_empty = T("No Accounts currently defined"),
                msg_record_modified = T("Email Settings updated")
                )

        return True
    s3.prep = prep

    return s3_rest_controller("msg")

# END =========================================================================
