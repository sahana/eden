# -*- coding: utf-8 -*-

"""
    Request Management
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name

    item = None
    if settings.has_module("cms"):
        table = s3db.cms_post
        _item = db(table.module == module).select(table.id,
                                                  table.body,
                                                  limitby=(0, 1)).first()
        if _item:
            if s3_has_role(ADMIN):
                item = DIV(XML(_item.body),
                           BR(),
                           A(T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[_item.id, "update"],
                                       vars={"module": module}),
                             _class="action-btn"))
            else:
                item = XML(_item.body)
        elif s3_has_role(ADMIN):
            item = DIV(H2(module_name),
                       A(T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module":module}),
                         _class="action-btn"))

    if not item:
        #item = H2(module_name)
        # Just redirect to the list of Requests
        redirect(URL(f="req", args=["search"]))

    # tbc
    report = ""

    response.view = "index.html"
    return dict(item=item, report=report)

# -----------------------------------------------------------------------------
def is_affiliated():
    """
        Check if User is affiliated to an Organisation
        @ToDo: Move this elsewhere
    """

    if not auth.is_logged_in():
        return False
    elif s3_has_role(ADMIN):
        return True
    else:
        table = auth.settings.table_user
        query = (table.id == auth.user.id)
        auth_user = db(query).select(table.organisation_id,
                                     limitby=(0, 1)).first()
        if auth_user and auth_user.organisation_id:
            return True
        else:
            return False

# =============================================================================
def create():
    """ Redirect to req/create """

    redirect(URL(f="req", args="create"))

# -----------------------------------------------------------------------------
def marker_fn(record):
    """
        Function to decide which Marker to use for Requests Map
        @ToDo: Use Symbology
    """

    # Base Icon based on Type
    type = record.type
    if type in (1, 8):
        # Items
        marker = "asset"
    elif type == 3:
        # People
        marker = "staff"
    #elif type == 6:
    #    # Food
    #    marker = "food"
    else:
        marker = "request"

    # Colour code by priority
    priority = record.priority
    if priority == 3:
        # High
        marker = "%s_red" % marker
    elif priority == 2:
        # Medium
        marker = "%s_yellow" % marker
    #elif priority == 1:
    #    # Low
    #    marker = "%s_yellow" % marker

    mtable = db.gis_marker
    marker = db(mtable.name == marker).select(mtable.image,
                                              mtable.height,
                                              mtable.width,
                                              cache=s3db.cache,
                                              limitby=(0, 1)).first()
    return marker

# -----------------------------------------------------------------------------
def req():
    """
        REST Controller for Request Instances
    """

    s3.filter = (s3db.req_req.is_template == False)

    output = req_controller()
    return output

# -----------------------------------------------------------------------------
def req_template():
    """
        REST Controller for Request Templates
    """

    # Hide fields which aren't relevant to templates
    # @ToDo: Need to get this done later after being opened by Types?
    table = s3db.req_req
    field = table.is_template
    field.default = True
    field.readable = field.writable = False
    s3.filter = (field == True)

    if "req_item" in request.args:
        # List fields for req_item
        table = s3db.req_req_item
        list_fields = ["id",
                       "item_id",
                       "item_pack_id",
                       "quantity",
                       "comments",
                       ]
        s3db.configure("req_req_item",
                       list_fields=list_fields)

    elif "req_skill" in request.args:
        # List fields for req_skill
        table = s3db.req_req_skill
        list_fields = ["id",
                       "skill_id",
                       "quantity",
                       "comments",
                       ]
        s3db.configure("req_req_skill",
                       list_fields=list_fields)

    else:
        # Main Req
        for fieldname in ["req_ref",
                          "date",
                          "date_required",
                          "date_required_until",
                          "date_recv",
                          "recv_by_id",
                          "commit_status",
                          "transit_status",
                          "fulfil_status",
                          "cancel",
                          ]:
            field = table[fieldname]
            field.readable = field.writable = False
        table.purpose.label = T("Details")
        list_fields = ["id",
                       "site_id"
                       ]
        if len(settings.get_req_req_type()) > 1:
            list_fields.append("type")
        list_fields.append("priority")
        list_fields.append("purpose")
        list_fields.append("comments")
        s3db.configure("req_req",
                       list_fields=list_fields)

        # CRUD strings
        ADD_REQUEST = T("Add Request Template")
        s3.crud_strings["req_req"] = Storage(
            title_create = ADD_REQUEST,
            title_display = T("Request Template Details"),
            title_list = T("Request Templates"),
            title_update = T("Edit Request Template"),
            subtitle_create = ADD_REQUEST,
            label_list_button = T("List Request Templates"),
            label_create_button = ADD_REQUEST,
            label_delete_button = T("Delete Request Template"),
            msg_record_created = T("Request Template Added"),
            msg_record_modified = T("Request Template Updated"),
            msg_record_deleted = T("Request Template Deleted"),
            msg_list_empty = T("No Request Templates"))

    output = req_controller()
    return output

# -----------------------------------------------------------------------------
def req_controller():
    """ REST Controller """

    # Set the req_item site_id (Requested From), called from action buttons on req/req_item_inv_item/x page
    if "req_item_id" in request.vars and "inv_item_id" in request.vars:
        inv_item = s3db.inv_inv_item[request.vars.inv_item_id]
        site_id = inv_item.site_id
        item_id = inv_item.item_id
        s3db.req_req_item[request.vars.req_item_id] = dict(site_id = site_id)
        response.confirmation = T("%(item)s requested from %(site)s" % \
            {"item":s3db.supply_item_represent(item_id, show_link=False),
             "site":s3db.org_site_represent(site_id, show_link=False)
             })

    def prep(r):

        req_table = s3db.req_req
        s3.req_prep(r)

        if len(settings.get_req_req_type()) == 1:
            # Remove type from list_fields
            list_fields = s3db.get_config("req_req", "list_fields")
            try:
                list_fields.remove("type")
            except:
                 # It has already been removed.
                 # This can happen if the req controller is called
                 # for a second time, such as when printing reports
                pass
            s3db.configure("req_req", list_fields=list_fields)

        if r.interactive:
            # Set Fields and Labels depending on type
            type = (r.record and r.record.type) or \
                   (request.vars and request.vars.type)
            if type:
                type = int(type)
                req_table.type.default = int(type)

                # This prevents the type from being edited AFTER it is set
                req_table.type.readable = req_table.type.writable = False

                crud_strings = settings.get_req_req_crud_strings(type)
                if crud_strings:
                    s3.crud_strings["req_req"] = crud_strings

                # Filter the query based on type
                if s3.filter:
                    s3.filter = s3.filter & \
                                (s3db.req_req.type == type)
                else:
                    s3.filter = (s3db.req_req.type == type)

            # These changes are applied via JS in create forms where type is editable
            if type == 1: # Item
                req_table.date_recv.readable = req_table.date_recv.writable = True

                req_table.purpose.label = T("What the Items will be used for")
                req_table.site_id.label = T("Deliver To")
                req_table.request_for_id.label = T("Deliver To")
                req_table.requester_id.label = T("Site Contact")
                req_table.recv_by_id.label = T("Delivered To")
     
            elif type == 3: # Person
                req_table.date_required_until.readable = req_table.date_required_until.writable = True

                req_table.purpose.label = T("Task Details")
                req_table.purpose.comment = DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Task Details"),
                                                                  T("Include any special requirements such as equipment which they need to bring.")))
                req_table.site_id.label =  T("Report To")
                req_table.requester_id.label = T("Volunteer Contact")
                req_table.request_for_id.label = T("Report To")
                req_table.recv_by_id.label = T("Reported To")

            if r.component:
                if r.component.name == "document":
                    s3.crud.submit_button = T("Add")
                    #table = r.component.table
                    # @ToDo: Fix for Link Table
                    #table.date.default = r.record.date
                    #if r.record.site_id:
                    #    stable = db.org_site
                    #    query = (stable.id == r.record.site_id)
                    #    site = db(query).select(stable.location_id,
                    #                            stable.organisation_id,
                    #                            limitby=(0, 1)).first()
                    #    if site:
                    #        table.location_id.default = site.location_id
                    #        table.organisation_id.default = site.organisation_id

                elif r.component.name == "req_item":
                    table = r.component.table
                    table.site_id.writable = table.site_id.readable = False
                    s3db.req_hide_quantities(table)

                elif r.component.name == "req_skill":
                    s3db.req_hide_quantities(r.component.table)

                elif r.component.alias == "job":
                    s3task.configure_tasktable_crud(
                        function="req_add_from_template",
                        args = [r.id],
                        vars = dict(user_id = auth.user is not None and auth.user.id or 0),
                        period = 86400, # seconds, so 1 day
                        )
                    db.scheduler_task.timeout.writable = False
            else:
                if r.id:
                    req_table.is_template.readable = req_table.is_template.writable = False

                if type == 8:
                    req_table.purpose.label = T("Details")
                    stable = current.s3db.req_summary_option
                    options = db(stable.deleted == False).select(stable.name,
                                                                 orderby=~stable.name)
                    summary_items = [opt.name for opt in options]
                    s3.js_global.append('''req_summary_items=%s''' % json.dumps(summary_items))
                    s3.scripts.append("/%s/static/scripts/S3/s3.req_update.js" % appname)

                if r.method not in ("read", "update", "search"):
                    # Hide fields which don't make sense in a Create form
                    # - includes one embedded in list_create
                    # - list_fields over-rides, so still visible within list itself
                    s3db.req_create_form_mods()

                    if type == 1:
                        # Dropdown not Autocomplete
                        itable = s3db.req_req_item
                        itable.item_id.widget = None
                        s3.jquery_ready.append('''
S3OptionsFilter({
 'triggerName':'item_id',
 'targetName':'item_pack_id',
 'lookupPrefix':'supply',
 'lookupResource':'item_pack',
 'lookupKey':'item_id',
 'lookupField':'id',
 'msgNoRecords':i18n.no_packs,
 'fncPrep':fncPrepItem,
 'fncRepresent':fncRepresentItem
})''')
                        # We don't want to force people to enter quantities
                        #itable.quantity.default = 0
                        # Custom Form
                        s3forms = s3base.s3forms
                        crud_form = s3forms.S3SQLCustomForm(
                                # If not generated automatically
                                #"req_ref",
                                "site_id",
                                "is_template",
                                "requester_id",
                                "date",
                                "priority",
                                "date_required",
                                "purpose",
                                s3forms.S3SQLInlineComponent(
                                    "req_item",
                                    label = T("Items"),
                                    fields = ["item_id",
                                              "item_pack_id",
                                              "quantity",
                                              "comments"
                                              ]
                                ),
                                #"date_recv",
                                "comments",
                            )
                        s3db.configure("req_req", crud_form=crud_form)

                    elif type == 3:
                        # Custom Form
                        stable = s3db.req_req_skill
                        stable.skill_id.label = T("Required Skills (optional)")
                        stable.skill_id.widget = None
                        s3forms = s3base.s3forms
                        crud_form = s3forms.S3SQLCustomForm(
                                # If not generated automatically
                                #"req_ref",
                                "site_id",
                                "is_template",
                                "requester_id",
                                "date",
                                "priority",
                                "date_required",
                                "date_required_until",
                                "purpose",
                                s3forms.S3SQLInlineComponent(
                                    "req_skill",
                                    label = T("Skills"),
                                    fields = ["quantity",
                                              "skill_id",
                                              "comments"
                                              ]
                                ),
                                "comments",
                            )
                        s3db.configure("req_req", crud_form=crud_form)

                    # Get the default Facility for this user
                    # @ToDo: Use site_id in User Profile (like current organisation_id)
                    if settings.has_module("hrm"):
                        hrtable = s3db.hrm_human_resource
                        query = (hrtable.person_id == s3_logged_in_person())
                        site = db(query).select(hrtable.site_id,
                                                limitby=(0, 1)).first()
                        if site:
                            r.table.site_id.default = site.site_id

                    if r.method == "map":
                        # Tell the client to request per-feature markers
                        s3db.configure("req_req", marker_fn=marker_fn)

        elif r.representation == "plain":
            # Map Popups
            pass

        elif r.representation == "geojson":
            # Load these models now as they'll be needed when we encode
            mtable = s3db.gis_marker
            s3db.configure("req_req", marker_fn=marker_fn)

        if r.component and r.component.name == "commit":
            table = r.component.table
            record = r.record
            # If there are no commitments yet then run req_commit_all
            if record.commit_status == 0:
                redirect(URL(f="req", args=[record.id, "commit_all"]))
            # Allow commitments to be added when doing so as a component
            s3db.configure(table,
                           listadd = True)

            type = record.type
            if type == 1: # Items
                # Limit site_id to facilities the user has permissions for
                auth.permitted_facilities(table=r.table,
                                          error_msg=T("You do not have permission for any facility to make a commitment."))
                if r.interactive:
                    # Dropdown not Autocomplete
                    itable = s3db.req_commit_item
                    itable.req_item_id.widget = None
                    s3.jquery_ready.append('''
S3OptionsFilter({
 'triggerName':'req_item_id',
 'targetName':'item_pack_id',
 'lookupPrefix':'req',
 'lookupResource':'req_item_packs',
 'lookupKey':'req_item_id',
 'lookupField':'id',
 'msgNoRecords':i18n.no_packs,
 'fncPrep':fncPrepItem,
 'fncRepresent':fncRepresentItem
})''')
                    # Custom Form
                    s3forms = s3base.s3forms
                    crud_form = s3forms.S3SQLCustomForm(
                            "site_id",
                            "date",
                            "date_available",
                            "committer_id",
                            s3forms.S3SQLInlineComponent(
                                "commit_item",
                                label = T("Items"),
                                fields = ["req_item_id",
                                          "item_pack_id",
                                          "quantity",
                                          "comments"
                                          ]
                            ),
                            "comments",
                        )
                    s3db.configure("req_commit", crud_form=crud_form)
                    # Redirect to the Items tab after creation
                    #s3db.configure(table,
                    #               create_next = URL(c="req", f="commit",
                    #                                 args=["[id]", "commit_item"]),
                    #               update_next = URL(c="req", f="commit",
                    #                                 args=["[id]", "commit_item"]))

            elif type == 3: # People
                # Limit site_id to orgs the user has permissions for
                # @ToDo: Make this customisable between Site/Org
                # @ToDo: is_affiliated()
                auth.permitted_facilities(table=r.table,
                                          error_msg=T("You do not have permission for any facility to make a commitment."))
                # Limit organisation_id to organisations the user has permissions for
                #auth.permitted_organisations(table=r.table, redirect_on_error=False)
                if r.interactive:
                    #table.organisation_id.readable = True
                    #table.organisation_id.writable = True
                    # Dropdown not Autocomplete
                    itable = s3db.req_commit_skill
                    itable.skill_id.widget = None
                    # Custom Form
                    s3forms = s3base.s3forms
                    crud_form = s3forms.S3SQLCustomForm(
                            "site_id",
                            "date",
                            "date_available",
                            "committer_id",
                            s3forms.S3SQLInlineComponent(
                                "commit_skill",
                                label = T("Skills"),
                                fields = ["quantity",
                                          "skill_id",
                                          "comments"
                                          ]
                            ),
                            "comments",
                        )
                    s3db.configure("req_commit", crud_form=crud_form)
                    # Redirect to the Skills tab after creation
                    #s3db.configure(table,
                    #               create_next = URL(c="req", f="commit",
                    #                                 args=["[id]", "commit_skill"]),
                    #               update_next = URL(c="req", f="commit",
                    #                                 args=["[id]", "commit_skill"]))
            else:
                # Non-Item commits can have an Organisation
                # Check if user is affiliated to an Organisation
                if is_affiliated():
                    # Limit organisation_id to organisations the user has permissions for
                    auth.permitted_organisations(table=r.table,
                                                 redirect_on_error=False)
                    table.organisation_id.readable = table.organisation_id.writable = True
                else:
                    # Unaffiliated people can't commit on behalf of others
                    r.component.table.committer_id.writable = False
                    r.component.table.committer_id.comment = None

                # Non-Item commits shouldn't have a From Inventory
                # @ToDo: Assets do? (Well, a 'From Site')
                table.site_id.readable = table.site_id.writable = False
                #if r.interactive and r.record.type == 3: # People
                #    # Redirect to the Persons tab after creation
                #    s3db.configure(table,
                #                   create_next = URL(c="req", f="commit",
                #                                     args=["[id]", "commit_person"]),
                #                   update_next = URL(c="req", f="commit",
                #                                     args=["[id]", "commit_person"])
                #                   )
        else:
            # Limit site_id to facilities the user has permissions for
            # @ToDo: Non-Item requests shouldn't be bound to a Facility?
            auth.permitted_facilities(table=r.table,
                                      error_msg=T("You do not have permission for any facility to make a request."))
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            s3_action_buttons(r)
            if not r.component:
                if settings.get_req_use_commit():
                    # This is appropriate to all
                    s3.actions.append(
                        dict(url = URL(c="req", f="req",
                                       args=["[id]", "commit_all"]),
                             _class = "action-btn commit-btn",
                             label = str(T("Commit"))
                            )
                        )
                    s3.jquery_ready.append(
'''S3ConfirmClick('.commit-btn','%s')''' % T("Do you want to commit to this request?"))
                # This is only appropriate for item requests
                query = (r.table.type == 1)
                rows = db(query).select(r.table.id)
                restrict = [str(row.id) for row in rows]
                s3.actions.append(
                    dict(url = URL(c="req", f="req",
                                   args=["[id]", "req_item"]),
                         _class = "action-btn",
                         label = str(T("View Items")),
                         restrict = restrict
                        )
                    )
                # This is only appropriate for people requests
                query = (r.table.type == 3)
                rows = db(query).select(r.table.id)
                restrict = [str(row.id) for row in rows]
                s3.actions.append(
                    dict(url = URL(c="req", f="req",
                                   args=["[id]", "req_skill"]),
                         _class = "action-btn",
                         label = str(T("View Skills")),
                         restrict = restrict
                        )
                    )
            elif r.component.name == "req_item" and settings.get_req_prompt_match():
                req_item_inv_item_btn = dict(url = URL(c = "req",
                                                       f = "req_item_inv_item",
                                                       args = ["[id]"]
                                                      ),
                                             _class = "action-btn",
                                             label = str(T("Request from Facility")),
                                             )
                s3.actions.append(req_item_inv_item_btn)
            elif r.component.alias == "job":
                s3.actions = [
                    dict(label=str(T("Open")),
                         _class="action-btn",
                         url=URL(c="req", f="req_template",
                                 args=[str(r.id), "job", "[id]"])),
                    dict(label=str(T("Reset")),
                         _class="action-btn",
                         url=URL(c="req", f="req_template",
                                 args=[str(r.id), "job", "[id]", "reset"])),
                    dict(label=str(T("Run Now")),
                         _class="action-btn",
                         url=URL(c="req", f="req_template",
                                 args=[str(r.id), "job", "[id]", "run"])),
                    ]
            else:
                # We don't yet have other components
                pass

        return output
    s3.postp = postp

    output = s3_rest_controller("req", "req",
                                rheader=eden.req.req_rheader)

    return output

# =============================================================================
def req_item():
    """
        REST Controller
        @ToDo: Filter out fulfilled Items?
    """

    # Filter out Template Items
    table = s3db.req_req_item
    rtable = s3db.req_req
    s3.filter = (rtable.is_template == False) & \
                (rtable.id == table.req_id)

    # Search method
    S3SearchOptionsWidget = s3base.S3SearchOptionsWidget
    req_item_search = (
        S3SearchOptionsWidget(
            name="req_search_fulfil_status",
            label=T("Status"),
            field="req_id$fulfil_status",
            options = s3.req_status_opts,
            cols = 3,
        ),
        S3SearchOptionsWidget(
            name="req_search_priority",
            label=T("Priority"),
            field="req_id$priority",
            options = s3.req_priority_opts,
            cols = 3,
        ),
        #S3SearchOptionsWidget(
        #  name="req_search_L1",
        #  field="req_id$site_id$location_id$L1",
        #  location_level="L1",
        #  cols = 3,
        #),
        #S3SearchOptionsWidget(
        #  name="req_search_L2",
        #  field="req_id$site_id$location_id$L2",
        #  location_level="L2",
        #  cols = 3,
        #),
        S3SearchOptionsWidget(
            name="req_search_L3",
            field="req_id$site_id$location_id$L3",
            location_level="L3",
            cols = 3,
        ),
        S3SearchOptionsWidget(
            name="req_search_L4",
            field="req_id$site_id$location_id$L4",
            location_level="L4",
            cols = 3,
        ),
    )
    s3db.configure("req_req_item",
                   search_method = s3base.S3Search(advanced=req_item_search),
                   )

    def prep(r):
        if r.interactive:
            list_fields = s3db.get_config("req_req_item", "list_fields")
            list_fields.insert(1, "req_id$site_id")
            list_fields.insert(1, "req_id$site_id$location_id$L4")
            list_fields.insert(1, "req_id$site_id$location_id$L3")
            s3db.configure("req_req_item",
                           insertable=False,
                           list_fields = list_fields,
                           )

            s3.crud_strings["req_req_item"].title_list = T("Requested Items")
            if r.method != None and r.method != "update" and r.method != "read":
                # Hide fields which don't make sense in a Create form
                # - includes one embedded in list_create
                # - list_fields over-rides, so still visible within list itself
                s3db.req_hide_quantities(r.table)

        return True
    s3.prep = prep

    output = s3_rest_controller()

    if settings.get_req_prompt_match():
        req_item_inv_item_btn = dict(url = URL(c="req", f="req_item_inv_item",
                                               args=["[id]"]),
                                     _class = "action-btn",
                                     label = str(T("Request from Facility")),
                                     )
        if s3.actions:
            s3.actions += [req_item_inv_item_btn]
        else:
            s3.actions = [req_item_inv_item_btn]

    return output

# -----------------------------------------------------------------------------
def req_item_packs():
    """
        Called by S3FilterFieldChange to provide the pack options for a
            particular Item
    """

    req_item_id = None
    args = request.args
    if len(args) == 1 and args[0].isdigit():
        req_item_id = args[0]
    else:
        for v in request.vars:
            if "." in v and v.split(".", 1)[1] == "req_item_id":
                req_item_id = request.vars[v]
                break

    table = s3db.supply_item_pack
    ritable = s3db.req_req_item
    query = (ritable.id == req_item_id) & \
            (ritable.item_id == table.item_id)

    response.headers["Content-Type"] = "application/json"
    return db(query).select(table.id,
                            table.name,
                            table.quantity).json()

# -----------------------------------------------------------------------------
def req_item_inv_item():
    """
        Shows the inventory items which match a requested item
        @ToDo: Make this page a component of req_item
    """

    req_item_id  = request.args[0]
    request.args = [] #
    ritable = s3db.req_req_item
    req_item = ritable[req_item_id]
    rtable = s3db.req_req
    req = rtable[req_item.req_id]

    output = {}

    output["title"] = T("Request Stock from Available Warehouse")
    output["req_btn"] = A(T("Return to Request"),
                          _href = URL(c="req", f="req",
                                      args=[req_item.req_id, "req_item"]),
                          _class = "action-btn"
                          )

    output["req_item"] = TABLE( TR(
                                    TH( "%s: " % T("Requested By") ),
                                    rtable.site_id.represent(req.site_id),
                                    TH( "%s: " % T("Item")),
                                    ritable.item_id.represent(req_item.item_id),
                                   ),
                                TR(
                                    TH( "%s: " % T("Requester") ),
                                    rtable.requester_id.represent(req.requester_id),
                                    TH( "%s: " % T("Quantity")),
                                    req_item.quantity,
                                   ),
                                TR(
                                    TH( "%s: " % T("Date Requested") ),
                                    rtable.date.represent(req.date),
                                    TH( T("Quantity Committed")),
                                    req_item.quantity_commit,
                                   ),
                                TR(
                                    TH( "%s: " % T("Date Required") ),
                                    rtable.date_required.represent(req.date_required),
                                    TH( "%s: " % T("Quantity in Transit")),
                                    req_item.quantity_transit,
                                   ),
                                TR(
                                    TH( "%s: " % T("Priority") ),
                                    rtable.priority.represent(req.priority),
                                    TH( "%s: " % T("Quantity Fulfilled")),
                                    req_item.quantity_fulfil,
                                   )
                               )

    s3.no_sspag = True # pagination won't work with 2 datatables on one page @todo: test

    itable = s3db.inv_inv_item
    # Get list of matching inventory items
    s3.filter = (itable.item_id == req_item.item_id)
    # Tweak CRUD String for this context
    s3.crud_strings["inv_inv_item"].msg_list_empty = T("No Inventories currently have this item in stock")

    inv_items = s3_rest_controller("inv", "inv_item")
    output["items"] = inv_items["items"]

    if current.deployment_settings.get_supply_use_alt_name():
        # Get list of alternative inventory items
        atable = s3db.supply_item_alt
        query = (atable.item_id == req_item.item_id ) & \
                (atable.deleted == False )
        alt_item_rows = db(query).select(atable.alt_item_id)
        alt_item_ids = [alt_item_row.alt_item_id for alt_item_row in alt_item_rows]

        if alt_item_ids:
            s3.filter = (itable.item_id.belongs(alt_item_ids))
            inv_items_alt = s3_rest_controller("inv", "inv_item")
            output["items_alt"] = inv_items_alt["items"]
        else:
            output["items_alt"] = T("No Inventories currently have suitable alternative items in stock")

    response.view = "req/req_item_inv_item.html"
    s3.actions = [dict(url = URL(c = request.controller,
                                          f = "req",
                                          args = [req_item.req_id, "req_item"],
                                          vars = dict(req_item_id = req_item_id,
                                                      inv_item_id = "[id]")
                                         ),
                                _class = "action-btn",
                                label = str(T("Request From")),
                                )]

    return output

# =============================================================================
def req_skill():
    """
        REST Controller
        @ToDo: Filter out fulfilled Skills?
    """

    # Filter out Template Items
    table = s3db.req_req_skill
    rtable = s3db.req_req
    s3.filter = (rtable.is_template == False) & \
                (rtable.id == table.req_id)

    # Search method
    S3SearchOptionsWidget = s3base.S3SearchOptionsWidget
    req_skill_search = (
        S3SearchOptionsWidget(
            name="req_search_fulfil_status",
            label=T("Status"),
            field="req_id$fulfil_status",
            options = s3.req_status_opts,
            cols = 3,
        ),
        S3SearchOptionsWidget(
            name="req_search_priority",
            label=T("Priority"),
            field="req_id$priority",
            options = s3.req_priority_opts,
            cols = 3,
        ),
        #S3SearchOptionsWidget(
        #  name="req_search_L1",
        #  field="req_id$site_id$location_id$L1",
        #  location_level="L1",
        #  cols = 3,
        #),
        #S3SearchOptionsWidget(
        #  name="req_search_L2",
        #  field="req_id$site_id$location_id$L2",
        #  location_level="L2",
        #  cols = 3,
        #),
        S3SearchOptionsWidget(
            name="req_search_L3",
            field="req_id$site_id$location_id$L3",
            location_level="L3",
            cols = 3,
        ),
        S3SearchOptionsWidget(
            name="req_search_L4",
            field="req_id$site_id$location_id$L4",
            location_level="L4",
            cols = 3,
        ),
    )
    s3db.configure("req_req_skill",
                   search_method = s3base.S3Search(advanced=req_skill_search),
                   )

    def prep(r):
        if r.interactive:
            list_fields = s3db.get_config("req_req_skill", "list_fields")
            list_fields.insert(1, "req_id$site_id")
            list_fields.insert(1, "req_id$site_id$location_id$L4")
            list_fields.insert(1, "req_id$site_id$location_id$L3")

            s3db.configure("req_req_skill",
                           insertable=False,
                           list_fields = list_fields,
                           )

            if r.method != "update" and r.method != "read":
                # Hide fields which don't make sense in a Create form
                # - includes one embedded in list_create
                # - list_fields over-rides, so still visible within list itself
                s3db.req_hide_quantities(r.table)

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive:
            response.s3.actions = [
                dict(url = URL(c="req", f="req",
                               args=["req_skill", "[id]"]),
                     _class = "action-btn",
                     label = str(READ)
                    )
                ]
        return output
    s3.postp = postp

    output = s3_rest_controller("req", "req_skill")

    return output

# =============================================================================
def summary_option():
    """ REST Controller """

    return s3_rest_controller()

# =============================================================================
def commit():
    """ REST Controller """

    # Check if user is affiliated to an Organisation
    if not is_affiliated():
        tablename = "req_commit_person"
        table = s3db[tablename]
        # Unaffiliated people can't commit on behalf of others
        table.person_id.writable = False
        # & can only make single-person commitments
        # (This should have happened in the main commitment)
        s3db.configure(tablename,
                       insertable=False)

    def prep(r):

        if r.interactive:
            # Commitments created through UI should be done via components
            table = r.table

            if r.record:
                s3.crud.submit_button = T("Save Changes")
                if r.record.type == 1: # Items
                    # Limit site_id to facilities the user has permissions for
                    auth.permitted_facilities(table=table,
                                              error_msg=T("You do not have permission for any facility to make a commitment.") )

                    table.site_id.comment = A(T("Set as default Site"),
                                              _id="req_commit_site_id_link",
                                              _target="_blank",
                                              _href=URL(c="default",
                                                        f="user",
                                                        args=["profile"]))
                    
                    jappend = s3.jquery_ready.append
                    jappend('''
$('#req_commit_site_id_link').click(function(){
 var site_id=$('#req_commit_site_id').val()
 if(site_id){
  var url = $('#req_commit_site_id_link').attr('href')
  var exists=url.indexOf('?')
  if(exists=='-1'){
   $('#req_commit_site_id_link').attr('href',url+'?site_id='+site_id)
  }
 }
 return true
})''')
                    # Dropdown not Autocomplete
                    itable = s3db.req_commit_item
                    itable.req_item_id.widget = None
                    jappend('''
S3OptionsFilter({
'triggerName':'req_item_id',
'targetName':'item_pack_id',
'lookupPrefix':'req',
'lookupResource':'req_item_packs',
'lookupKey':'req_item_id',
'lookupField':'id',
'msgNoRecords':i18n.no_packs,
'fncPrep':fncPrepItem,
'fncRepresent':fncRepresentItem
})''')
                    # Custom Form
                    s3forms = s3base.s3forms
                    crud_form = s3forms.S3SQLCustomForm(
                            "site_id",
                            "date",
                            "date_available",
                            "committer_id",
                            s3forms.S3SQLInlineComponent(
                                "commit_item",
                                label = T("Items"),
                                fields = ["req_item_id",
                                          "item_pack_id",
                                          "quantity",
                                          "comments"
                                          ]
                            ),
                            "comments",
                        )
                    s3db.configure("req_commit", crud_form=crud_form)

                elif r.record.type == 3: # People
                    # Limit site_id to sites the user has permissions for
                    auth.permitted_facilities(table=r.table,
                          error_msg=T("You do not have permission for any facility to make a commitment."))
                    table.site_id.comment = A(T("Set as default Site"),
                                              _id="req_commit_site_id_link",
                                              _target="_blank",
                                              _href=URL(c="default",
                                                        f="user",
                                                        args=["profile"]))
                    # Limit organisation_id to organisations the user has permissions for
                    #auth.permitted_organisations(table=r.table, redirect_on_error=False)
                    #table.organisation_id.readable = True
                    #table.organisation_id.writable = True
                    # Dropdown not Autocomplete
                    stable = s3db.req_commit_skill
                    stable.skill_id.widget = None
                    # Custom Form
                    s3forms = s3base.s3forms
                    crud_form = s3forms.S3SQLCustomForm(
                            #"organisation_id",
                            "site_id",
                            "date",
                            "date_available",
                            "committer_id",
                            s3forms.S3SQLInlineComponent(
                                "commit_skill",
                                label = T("People"),
                                fields = ["quantity",
                                          "skill_id",
                                          "comments"
                                          ]
                            ),
                            "comments",
                        )
                    s3db.configure("req_commit", crud_form=crud_form)

                else:
                    # Commits to Other requests can have an Organisation
                    # Limit organisation_id to organisations the user has permissions for
                    auth.permitted_organisations(table=r.table, redirect_on_error=False)
                    table.organisation_id.readable = True
                    table.organisation_id.writable = True
                    # Non-Item commits shouldn't have a From Inventory
                    # @ToDo: Assets do?
                    table.site_id.readable = False
                    table.site_id.writable = False

        if r.component:
            req_id = r.record.req_id
            if r.component.name == "commit_item":
                # Limit commit items to items from the request
                s3db.req_commit_item.req_item_id.requires = \
                    IS_ONE_OF(db,
                              "req_req_item.id",
                              s3db.req_item_represent,
                              orderby = "req_req_item.id",
                              filterby = "req_id",
                              filter_opts = [req_id],
                              sort=True
                              )
            elif r.component.name == "person":
                pass
                # Limit commit skills to skills from the request
                #db.req_commit_skill.req_skill_id.requires = \
                #    IS_ONE_OF(db,
                #              "req_req_skill.id",
                #              s3db.req_skill_represent,
                #              orderby = "req_req_skill.id",
                #              filterby = "req_id",
                #              filter_opts = [req_id],
                #              sort=True
                #              )
        return True
    s3.prep = prep

    output = s3_rest_controller(rheader=commit_rheader)
    return output

# -----------------------------------------------------------------------------
def commit_rheader(r):
    """ Resource Header for Commitments """

    if r.representation == "html":
        record = r.record
        if record and r.name == "commit":

            s3_date_represent = s3base.S3DateTime.date_represent

            tabs = [(T("Edit Details"), None)]
            type = record.type and int(record.type)

            table = r.table
            if type == 1:
                tabs.append((T("Items"), "commit_item"))

                #req_record = db.req_req[record.req_id]
                #req_date = req_record.date
                rheader = DIV(TABLE(TR(TH("%s: " % table.req_id.label),
                                       table.req_id.represent(record.req_id),
                                       ),
                                    TR(TH("%s: " % T("Committing Warehouse")),
                                       s3db.org_site_represent(record.site_id),
                                       TH("%s: " % T("Commit Date")),
                                       s3_date_represent(record.date),
                                       ),
                                    TR(TH("%s: " % table.comments.label),
                                       TD(record.comments or "", _colspan=3)
                                       ),
                                    ),
                                )
                prepare_btn = A( T("Prepare Shipment"),
                              _href = URL(f = "send_commit",
                                          args = [record.id]
                                          ),
                              _id = "send_commit",
                              _class = "action-btn"
                              )

                s3.rfooter = TAG[""](prepare_btn)

#                send_btn = A( T("Send Commitment as Shipment"),
#                              _href = URL(f = "send_commit",
#                                          args = [record.id]
#                                          ),
#                              _id = "send_commit",
#                              _class = "action-btn"
#                              )
#
#                send_btn_confirm = SCRIPT("S3ConfirmClick('#send_commit', '%s')" %
#                                          T("Do you want to send these Committed items?") )
#                s3.rfooter = TAG[""](send_btn,send_btn_confirm)
                #rheader.append(send_btn)
                #rheader.append(send_btn_confirm)

            elif type == 3:
                #tabs.append((T("People"), "commit_person"))
                tabs.append((T("People"), "commit_skill"))

                #req_record = db.req_req[record.req_id]
                #req_date = req_record.date
                organisation_represent = s3db.org_organisation_represent
                rheader = DIV(TABLE(TR(TH("%s: " % table.req_id.label),
                                       table.req_id.represent(record.req_id),
                                       ),
                                    TR(TH("%s: " % T("Committing Organization")),
                                       organisation_represent(record.organisation_id),
                                       TH("%s: " % T("Commit Date")),
                                       s3_date_represent(record.date),
                                       ),
                                    TR(TH("%s: " % table.comments.label),
                                       TD(record.comments, _colspan=3)
                                       ),
                                    ),
                                )
            else:
                # Other (& Assets/Shelter)
                rheader = DIV( TABLE( TR( TH( "%s: " % table.req_id.label),
                                          table.req_id.represent(record.req_id),
                                         ),
                                      TR( TH( "%s: " % T("Committing Person")),
                                          s3db.pr_person_represent(record.committer_id),
                                          TH( "%s: " % T("Commit Date")),
                                          s3_date_represent(record.date),
                                          ),
                                      TR( TH( "%s: " % table.comments.label),
                                          TD(record.comments or "", _colspan=3)
                                          ),
                                         ),
                                        )

            rheader_tabs = s3_rheader_tabs(r,
                                           tabs)
            rheader.append(rheader_tabs)

            return rheader
    return None

# =============================================================================
def send():
    """ RESTful CRUD controller """

    s3db.configure("inv_send",
                   listadd=False)

    return s3db.inv_send_controller()

# ==============================================================================
def send_commit():
    """
        Send a Shipment containing all items in a Commitment
    """

    return s3db.req_send_commit()

# -----------------------------------------------------------------------------
def send_process():
    """ Process a Shipment """

    return s3db.inv_send_process()

# =============================================================================
def commit_item():
    """ REST Controller """

    return s3_rest_controller()

# =============================================================================
def commit_req():
    """
        function to commit items according to a request.
        copy data from a req into a commitment
        arg: req_id
        vars: site_id
    """

    req_id = request.args[0]
    r_req = s3db.req_req[req_id]
    site_id = request.vars.get("site_id")

    # User must have permissions over facility which is sending
    (prefix, resourcename, id) = s3db.get_instance(s3db.org_site, site_id)
    if not site_id or not auth.s3_has_permission("update",
                                                 "%s_%s" % (prefix,
                                                            resourcename),
                                                 record_id=id):
        session.error = T("You do not have permission to make this commitment.")
        redirect(URL(c="req", f="req",
                     args=[req_id]))

    # Create a new commit record
    commit_id = s3db.req_commit.insert(date = request.utcnow,
                                       req_id = req_id,
                                       site_id = site_id,
                                       type = r_req.type
                                       )

    # Only select items which are in the warehouse
    ritable = s3db.req_req_item
    iitable = s3db.inv_inv_item
    query = (ritable.req_id == req_id) & \
            (ritable.quantity_fulfil < ritable.quantity) & \
            (iitable.site_id == site_id) & \
            (ritable.item_id == iitable.item_id) & \
            (ritable.deleted == False)  & \
            (iitable.deleted == False)
    req_items = db(query).select(ritable.id,
                                 ritable.quantity,
                                 ritable.item_pack_id,
                                 iitable.item_id,
                                 iitable.quantity,
                                 iitable.item_pack_id)

    citable = s3db.req_commit_item
    for req_item in req_items:
        req_item_quantity = req_item.req_req_item.quantity * \
                            req_item.req_req_item.pack_quantity

        inv_item_quantity = req_item.inv_inv_item.quantity * \
                            req_item.inv_inv_item.pack_quantity

        if inv_item_quantity > req_item_quantity:
            commit_item_quantity = req_item_quantity
        else:
            commit_item_quantity = inv_item_quantity
        commit_item_quantity = commit_item_quantity / req_item.req_req_item.pack_quantity

        if commit_item_quantity:
            commit_item_id = citable.insert(commit_id = commit_id,
                                            req_item_id = req_item.req_req_item.id,
                                            item_pack_id = req_item.req_req_item.item_pack_id,
                                            quantity = commit_item_quantity
                                            )

            # Update the req_item.commit_quantity  & req.commit_status
            s3mgr.store_session("req", "commit_item", commit_item_id)
            s3db.req_commit_item_onaccept(None)

    # Redirect to commit
    redirect(URL(c="req", f="commit",
                 args=[commit_id, "commit_item"]))

# =============================================================================
def send_req():
    """
        function to send items according to a request.
        copy data from a req into a send
        arg: req_id
        vars: site_id
    """

    ritable = s3db.req_req_item
    iitable = s3db.inv_inv_item
    sendtable = s3db.inv_send
    tracktable = s3db.inv_track_item
    siptable = s3db.supply_item_pack

    req_id = request.args[0]
    r_req = s3db.req_req[req_id]
    site_id = request.vars.get("site_id")

    # User must have permissions over facility which is sending
    (prefix, resourcename, id) = s3db.get_instance(db.org_site, site_id)
    if not site_id or not auth.s3_has_permission("update",
                                                 "%s_%s" % (prefix,
                                                            resourcename),
                                                 record_id=id):
        session.error = T("You do not have permission to send this shipment.")
        redirect(URL(c="req", f="req",
                     args = [req_id]))

    # Create a new send record
    code = s3db.inv_get_shipping_code("WB",
                                      site_id,
                                      s3db.inv_send.send_ref
                                     )
    send_id = sendtable.insert(send_ref = code,
                               req_ref = r_req.req_ref,
                               sender_id = auth.s3_logged_in_person(),
                               site_id = site_id,
                               date = request.utcnow,
                               recipient_id = r_req.requester_id,
                               to_site_id = r_req.site_id,
                               status = s3db.inv_ship_status["IN_PROCESS"],
                              )

    # Get the items for this request that have not been fulfilled (in transit)
    query = (ritable.req_id == req_id) & \
            (ritable.quantity_transit < ritable.quantity) & \
            (ritable.deleted == False)
    req_items = db(query).select(ritable.id,
                                 ritable.quantity,
                                 ritable.quantity_transit,
                                 ritable.item_id,
                                 ritable.item_pack_id,
                                )

    # loop through each request item and find matched in the site inventory
    for req_i in req_items:
        query = (iitable.item_id == req_i.item_id) & \
                (iitable.quantity > 0) & \
                (iitable.site_id == site_id) & \
                (iitable.deleted == False)
        inv_items = db(query).select(iitable.id,
                                     iitable.item_id,
                                     iitable.quantity,
                                     iitable.item_pack_id,
                                     iitable.pack_value,
                                     iitable.currency,
                                     iitable.expiry_date,
                                     iitable.bin,
                                     iitable.owner_org_id,
                                     iitable.supply_org_id,
                                    )
        # if their is a single match then set up a tracktable record
        # get the request pack_quantity
        req_p_qnty = siptable[req_i.item_pack_id].quantity
        req_qnty = req_i.quantity
        req_qnty_in_t = req_i.quantity_transit
        req_qnty_wanted = (req_qnty - req_qnty_in_t) * req_p_qnty
        # insert the track item records
        # if their is more than one item match then set the quantity to 0
        # and add the quantity requested in the comments
        for inv_i in inv_items:
            # get inv_item.pack_quantity
            if len(inv_items) == 1:
                # Remove this total from the warehouse stock
                send_item_quantity = s3db.inv_remove(inv_i, req_qnty_wanted)
            else:
                send_item_quantity = 0
            comment = "%d items needed to match total request" % req_qnty_wanted
            tracktable.insert(send_id = send_id,
                              send_inv_item_id = inv_i.id,
                              item_id = inv_i.item_id,
                              req_item_id = req_i.id,
                              item_pack_id = inv_i.item_pack_id,
                              quantity = send_item_quantity,
                              status = s3db.inv_tracking_status["IN_PROCESS"],
                              pack_value = inv_i.pack_value,
                              currency = inv_i.currency,
                              bin = inv_i.bin,
                              expiry_date = inv_i.expiry_date,
                              owner_org_id = inv_i.owner_org_id,
                              supply_org_id = inv_i.supply_org_id,
                              comments = comment,
                             )
    # Redirect to commit
    redirect(URL(c = "inv",
                 f = "send",
                 args = [send_id, "track_item"]))

# =============================================================================
def commit_item_json():
    """
    """

    ctable = s3db.req_commit
    itable = s3db.req_commit_item
    stable = s3db.org_site
    #ctable.date.represent = lambda dt: dt[:10]
    query = (itable.req_item_id == request.args[0]) & \
            (ctable.id == itable.commit_id) & \
            (ctable.site_id == stable.id) & \
            (itable.deleted == False)
    records = db(query).select(ctable.id,
                               ctable.date,
                               stable.name,
                               itable.quantity,
                               orderby = db.req_commit.date)

    json_str = '''[%s,%s''' % (json.dumps(dict(id = str(T("Committed")),
                                               quantity = "#")),
                               records.json()[1:])

    response.headers["Content-Type"] = "application/json"
    return json_str

# END =========================================================================
