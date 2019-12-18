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
    """ Customisable module homepage """

    return settings.customise_home(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Requests
    s3_redirect_default(URL(f="req"))

# -----------------------------------------------------------------------------
def is_affiliated():
    """
        Check if User is affiliated to an Organisation
        @ToDo: Move this elsewhere, like s3aaa or s3db/org
    """

    if not auth.is_logged_in():
        return False
    elif auth.s3_has_role("ADMIN"):
        return True
    else:
        table = auth.settings.table_user
        auth_user = db(table.id == auth.user.id).select(table.organisation_id,
                                                        limitby=(0, 1),
                                                        ).first()
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
        #marker = "%s_orange" % marker
        marker = "%s_yellow" % marker
    #elif priority == 1:
    #    # Low
    #    marker = "%s_yellow" % marker

    mtable = db.gis_marker
    marker = db(mtable.name == marker).select(mtable.image,
                                              mtable.height,
                                              mtable.width,
                                              cache=s3db.cache,
                                              limitby=(0, 1),
                                              ).first()
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

    settings.req.prompt_match = False

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
                       list_fields = list_fields,
                       )

    elif "req_skill" in request.args:
        # List fields for req_skill
        table = s3db.req_req_skill
        list_fields = ["id",
                       "skill_id",
                       "quantity",
                       "comments",
                       ]
        s3db.configure("req_req_skill",
                       list_fields = list_fields,
                       )

    else:
        # Main Req
        fields = ["req_ref",
                  "date",
                  "date_required",
                  "date_required_until",
                  "date_recv",
                  "recv_by_id",
                  "cancel",
                  "commit_status",
                  "transit_status",
                  "fulfil_status",
                  ]
        for fieldname in fields:
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
                       list_fields = list_fields,
                       )

        # CRUD strings
        s3.crud_strings["req_req"] = Storage(
            label_create = T("Create Request Template"),
            title_display = T("Request Template Details"),
            title_list = T("Request Templates"),
            title_update = T("Edit Request Template"),
            label_list_button = T("List Request Templates"),
            label_delete_button = T("Delete Request Template"),
            msg_record_created = T("Request Template Added"),
            msg_record_modified = T("Request Template Updated"),
            msg_record_deleted = T("Request Template Deleted"),
            msg_list_empty = T("No Request Templates"))

    output = req_controller(template = True)
    return output

# -----------------------------------------------------------------------------
def req_controller(template = False):
    """ REST Controller """

    REQ_STATUS_PARTIAL  = 1
    REQ_STATUS_COMPLETE = 2

    def prep(r):

        table = r.table
        s3.req_prep(r)

        #if len(settings.get_req_req_type()) == 1:
        #    # Remove type from list_fields
        #    list_fields = s3db.get_config("req_req", "list_fields")
        #    try:
        #        list_fields.remove("type")
        #    except:
        #         # It has already been removed.
        #         # This can happen if the req controller is called
        #         # for a second time, such as when printing reports
        #        pass
        #    s3db.configure("req_req", list_fields=list_fields)

        req_type = (r.record and r.record.type) or \
                   (get_vars.type and int(get_vars.type))

        if r.interactive:
            # Set the req_item site_id (Requested From), called from action buttons on req/req_item_inv_item/x page
            if "req_item_id" in get_vars and "inv_item_id" in get_vars:
                iitable = s3db.inv_inv_item
                inv_item = db(iitable.id == get_vars.inv_item_id).select(iitable.site_id,
                                                                         iitable.item_id,
                                                                         limitby=(0, 1),
                                                                         ).first()
                site_id = inv_item.site_id
                # @ToDo: Check Permissions & Avoid DB updates in GETs
                db(s3db.req_req_item.id == get_vars.req_item_id).update(site_id = site_id)
                response.confirmation = T("%(item)s requested from %(site)s") % \
                    {"item": s3db.supply_ItemRepresent()(inv_item.item_id),
                     "site": s3db.org_SiteRepresent()(site_id)
                     }
            elif "req.site_id" in get_vars:
                # Called from 'Make new request' button on [siteinstance]/req page
                table.site_id.default = get_vars.get("req.site_id")
                table.site_id.writable = False
                if r.http == "POST":
                    del r.get_vars["req.site_id"]

            # Set Fields and Labels depending on type
            if req_type:
                table.type.default = req_type

                # This prevents the type from being edited AFTER it is set
                table.type.readable = table.type.writable = False

                crud_strings = settings.get_req_req_crud_strings(req_type)
                if crud_strings:
                    s3.crud_strings["req_req"] = crud_strings
                elif req_type == 1:
                    s3.crud_strings["req_req"].label_create = T("Make Supplies Request")
                elif req_type == 3:
                    s3.crud_strings["req_req"].label_create = T("Make People Request")

                # Filter the query based on type
                r.resource.add_filter(table.type == req_type)

            # These changes are applied via JS in create forms where type is editable
            if req_type == 1: # Item
                table.date_recv.readable = table.date_recv.writable = True

                if settings.get_req_items_ask_purpose():
                    table.purpose.label = T("What the Items will be used for")
                table.site_id.label = T("Deliver To")
                table.request_for_id.label = T("Deliver To")
                # Keep consistency, don't change
                #table.requester_id.label = T("Site Contact")
                table.recv_by_id.label = T("Delivered To")

            elif req_type == 3: # Person
                table.date_required_until.readable = table.date_required_until.writable = True

                table.purpose.label = T("Task Details")
                table.purpose.comment = DIV(_class="tooltip",
                                            _title="%s|%s" % (T("Task Details"),
                                                              T("Include any special requirements such as equipment which they need to bring.")))
                table.site_id.label =  T("Report To")
                table.requester_id.label = T("Volunteer Contact")
                table.request_for_id.label = T("Report To")
                table.recv_by_id.label = T("Reported To")

            if r.component:
                if r.component_name == "document":
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

                elif r.component_name == "req_item":
                    ctable = r.component.table
                    ctable.site_id.writable = ctable.site_id.readable = False
                    s3.req_hide_quantities(ctable)

                elif r.component_name == "req_skill":
                    s3.req_hide_quantities(r.component.table)

                elif r.component.alias == "job":
                    s3task.configure_tasktable_crud(
                        function="req_add_from_template",
                        args = [r.id],
                        vars = {"user_id": 0 if auth.user is None else auth.user.id},
                        period = 86400, # seconds, so 1 day
                        )
                    db.scheduler_task.timeout.writable = False
            else:
                if r.id:
                    table.is_template.readable = table.is_template.writable = False

                keyvalue = settings.get_ui_auto_keyvalue()
                if keyvalue:
                    # What Keys do we have?
                    kvtable = s3db.req_req_tag
                    keys = db(kvtable.deleted == False).select(kvtable.tag,
                                                               distinct=True)
                    if keys:
                        tablename = "req_req"
                        crud_fields = [f for f in table.fields if table[f].readable]
                        cappend = crud_fields.append
                        add_component = s3db.add_components
                        list_fields = s3db.get_config(tablename,
                                                      "list_fields")
                        lappend = list_fields.append
                        for key in keys:
                            tag = key.tag
                            label = T(tag.title())
                            cappend(S3SQLInlineComponent("tag",
                                                         label = label,
                                                         name = tag,
                                                         multiple = False,
                                                         fields = [("", "value")],
                                                         filterby = {"field": "tag",
                                                                     "options": tag,
                                                                     },
                                                         ))
                            add_component(tablename,
                                          org_organisation_tag = {"name": tag,
                                                                  "joinby": "req_id",
                                                                  "filterby": "tag",
                                                                  "filterfor": (tag,),
                                                                  },
                                          )
                            lappend((label, "%s.value" % tag))
                        crud_form = S3SQLCustomForm(*crud_fields)
                        s3db.configure(tablename,
                                       crud_form = crud_form,
                                       )

                method = r.method
                if method in (None, "create"):
                    # Hide fields which don't make sense in a Create form
                    # - includes one embedded in list_create
                    # - list_fields over-rides, so still visible within list itself
                    s3db.req_create_form_mods()

                    if req_type and settings.get_req_inline_forms():
                        # Inline Forms
                        s3db.req_inline_form(req_type, method)

                    # Get the default Facility for this user
                    #if settings.has_module("hrm"):
                    #    hrtable = s3db.hrm_human_resource
                    #    query = (hrtable.person_id == auth.s3_logged_in_person())
                    #    site = db(query).select(hrtable.site_id,
                    #                            limitby=(0, 1)).first()
                    #    if site:
                    #        r.table.site_id.default = site.site_id
                    # Use site_id in User Profile
                    if auth.is_logged_in() and not table.site_id.default:
                        table.site_id.default = auth.user.site_id

                elif method == "update":
                    if settings.get_req_inline_forms():
                        # Inline Forms
                        s3db.req_inline_form(req_type, method)
                    s3.scripts.append("/%s/static/scripts/S3/s3.req_update.js" % appname)

                elif method == "map":
                    # Tell the client to request per-feature markers
                    s3db.configure("req_req",
                                   marker_fn = marker_fn,
                                   )

        elif r.representation == "plain":
            # Map Popups
            pass

        elif r.representation == "geojson":
            req_ref_represent = table.req_ref.represent
            table.req_ref.represent = lambda v, show_link=False, pdf=False: \
                req_ref_represent(v, show_link)
            # Load these models now as they'll be needed when we encode
            mtable = s3db.gis_marker
            s3db.configure("req_req",
                           marker_fn = marker_fn,
                           )

        if r.component:
            if r.component.name == "req_item":
                record = r.record
                if record: # Check as options.s3json checks the component without a record
                    # Prevent Adding/Deleting Items from Requests which are complete, closed or cancelled
                    # @ToDo: deployment_setting to determine which exact rule to apply?
                    if record.fulfil_status == REQ_STATUS_COMPLETE or \
                       record.transit_status == REQ_STATUS_COMPLETE or \
                       record.req_status == REQ_STATUS_COMPLETE or \
                       record.fulfil_status == REQ_STATUS_PARTIAL or \
                       record.transit_status == REQ_STATUS_PARTIAL or \
                       record.req_status == REQ_STATUS_PARTIAL or \
                       record.closed or \
                       record.cancel:
                        s3db.configure("req_req_item",
                                       deletable = False,
                                       insertable = False,
                                       )

            elif r.component.name == "commit":

                table = r.component.table
                record = r.record
                record_id = record.id

                stable = s3db.org_site
                rtype = record.type

                if (rtype == 3) and settings.get_req_commit_people():
                    # Don't allow people commits to happen in this view
                    insertable = False
                else:
                    commit_status = record.commit_status
                    if (commit_status == 2) and settings.get_req_restrict_on_complete():
                        # Restrict from committing to completed requests
                        insertable = False
                    else:
                        # Allow commitments to be added when doing so as a component
                        insertable = True

                # Limit site_id to permitted sites which have not
                # yet committed to this request
                current_site = None
                if r.component_id:
                    query = (table.id == r.component_id) & \
                            (table.deleted == False)
                    commit = db(query).select(table.site_id,
                                              limitby = (0, 1),
                                              ).first()
                    if commit:
                        current_site = commit.site_id

                allowed_sites = auth.permitted_facilities(redirect_on_error=False)
                if current_site and current_site not in allowed_sites:
                    table.site_id.writable = False
                else:
                    # Committing sites
                    query = (table.req_id == record_id) & \
                            (table.deleted == False)
                    commits = db(query).select(table.site_id)
                    committing_sites = set(c.site_id for c in commits)

                    # Acceptable sites
                    acceptable = set(allowed_sites) - committing_sites
                    if current_site:
                        acceptable.add(current_site)
                    if acceptable:
                        query = (stable.site_id.belongs(acceptable)) & \
                                (stable.deleted == False)
                        sites = db(query).select(stable.id,
                                                 stable.code,
                                                 orderby = stable.code,
                                                 )
                        site_opts = OrderedDict((s.id, s.code) for s in sites)
                        table.site_id.requires = IS_IN_SET(site_opts)
                    else:
                        if r.method == "create":
                            # Can't commit if we have no acceptable sites
                            # TODO do not redirect if site is not required,
                            #      e.g. org-only commits of skills
                            error_msg=T("You do not have permission for any facility to make a commitment.")
                            current.session.error = error_msg
                            redirect(r.url(component="", method=""))
                        else:
                            insertable = False

                s3db.configure(table,
                               # Don't want filter_widgets in the component view
                               filter_widgets = None,
                               insertable = insertable,
                               )

                if req_type == 1: # Items
                    if r.interactive:
                        # Dropdown not Autocomplete
                        itable = s3db.req_commit_item
                        itable.req_item_id.widget = None
                        itable.req_item_id.requires = \
                                        IS_ONE_OF(db, "req_req_item.id",
                                                  s3db.req_item_represent,
                                                  filterby = "req_id",
                                                  filter_opts = [r.id],
                                                  orderby = "req_req_item.id",
                                                  sort = True,
                                                  )
                        s3.jquery_ready.append('''
$.filterOptionsS3({
 'trigger':{'alias':'commit_item','name':'req_item_id'},
 'target':{'alias':'commit_item','name':'item_pack_id'},
 'scope':'row',
 'lookupPrefix':'req',
 'lookupResource':'req_item_packs',
 'lookupKey':'req_item_id',
 'lookupField':'id',
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
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
                        s3db.configure("req_commit",
                                       crud_form = crud_form,
                                       )
                        # Redirect to the Items tab after creation
                        #s3db.configure(table,
                        #               create_next = URL(c="req", f="commit",
                        #                                 args=["[id]", "commit_item"]),
                        #               update_next = URL(c="req", f="commit",
                        #                                 args=["[id]", "commit_item"]))

                elif req_type == 3: # People
                    # Limit site_id to orgs the user has permissions for
                    # @ToDo: Make this customisable between Site/Org
                    # @ToDo: is_affiliated() once Org is possible
                    auth.permitted_facilities(table=r.table,
                                              error_msg=T("You do not have permission for any facility to make a commitment."))
                    # Limit organisation_id to organisations the user has permissions for
                    #auth.permitted_organisations(table=r.table, redirect_on_error=False)
                    if r.interactive:
                        #table.organisation_id.readable = True
                        #table.organisation_id.writable = True
                        # Limit commit skills to skills from the request
                        skills_filter(record_id)

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
                        s3db.configure("req_commit",
                                       crud_form = crud_form,
                                       )
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
                        field = r.component.table.committer_id
                        field.writable = False
                        field.comment = None

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
            # Not r.component
            # Limit site_id to facilities the user has permissions for
            # @ToDo: Non-Item requests shouldn't be bound to a Facility?
            auth.permitted_facilities(table=r.table,
                                      error_msg=T("You do not have permission for any facility to make a request."))
            if r.id:
                # Prevent Deleting Requests which are complete or closed
                record = r.record
                if record.fulfil_status == REQ_STATUS_COMPLETE or \
                   record.transit_status == REQ_STATUS_COMPLETE or \
                   record.req_status == REQ_STATUS_COMPLETE or \
                   record.fulfil_status == REQ_STATUS_PARTIAL or \
                   record.transit_status == REQ_STATUS_PARTIAL or \
                   record.req_status == REQ_STATUS_PARTIAL or \
                   record.closed:
                    s3db.configure("req_req",
                                   deletable = False,
                                   )

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):

        if r.interactive:
            if r.method is None:
                # Customise Action Buttons
                if r.component:
                    s3_action_buttons(r, deletable=s3db.get_config(r.component.tablename, "deletable"))
                    if r.component.name == "req_item" and \
                       settings.get_req_prompt_match():
                        s3.actions.append(
                            {"label": s3_str(T("Request from Facility")),
                             "url": URL(c = "req",
                                        f = "req_item_inv_item",
                                        args = ["[id]"],
                                        ),
                             "_class": "action-btn",
                             })

                    elif r.component.name == "commit":
                        if "form" in output:
                            # User has Write access
                            req_id = r.record.id
                            ctable = s3db.req_commit
                            query = (ctable.deleted == False) & \
                                    (ctable.req_id == req_id)
                            exists = current.db(query).select(ctable.id,
                                                              limitby=(0, 1))
                            if not exists:
                                s3.rfooter = A(T("Commit All"),
                                               _href=URL(args=[req_id,
                                                               "commit_all"]),
                                               _class="action-btn",
                                               _id="commit-btn",
                                               )
                                s3.jquery_ready.append(
'''S3.confirmClick('#commit-btn','%s')''' % T("Do you want to commit to this request?"))
                            elif r.record.type == 1:
                                # Items
                                s3.actions.append(
                                      {"label": s3_str(T("Prepare Shipment")),
                                       "url": URL(c = "req",
                                                  f = "send_commit",
                                                  args = ["[id]"],
                                                  ),
                                       "_class": "action-btn send-btn",
                                       })
                                s3.jquery_ready.append(
'''S3.confirmClick('.send-btn','%s')''' % T("Are you sure you want to send this shipment?"))

                    elif r.component.alias == "job":
                        record_id = r.id
                        s3.actions = [
                            {"label": s3_str(T("Open")),
                             "url": URL(c="req",
                                        f="req_template",
                                        args=[record_id, "job", "[id]"],
                                        ),
                             "_class": "action-btn",
                             },
                            {"label": s3_str(T("Reset")),
                             "url": URL(c="req",
                                        f="req_template",
                                        args=[record_id, "job", "[id]", "reset"],
                                        ),
                             "_class": "action-btn",
                             },
                            {"label": s3_str(T("Run Now")),
                             "url": URL(c="req",
                                        f="req_template",
                                        args=[record_id, "job", "[id]", "run"],
                                        ),
                             "_class": "action-btn",
                             },
                            ]

                else:
                    # No Component
                    if r.http == "POST":
                        # Create form
                        # @ToDo: DRY
                        if not settings.get_req_inline_forms():
                            form_vars = output["form"].vars
                            type = form_vars.type
                            if type == "1":
                                # Stock: Open Tab for Items
                                r.next = URL(args=[form_vars.id, "req_item"])
                            elif type == "3":
                                # People: Open tab for Skills
                                r.next = URL(args=[form_vars.id, "req_skill"])
                    else:
                        s3_action_buttons(r, deletable =False)
                        # Add delete button for those records which are not completed
                        # @ToDo: Handle icons
                        table = r.table
                        query = (table.fulfil_status != REQ_STATUS_COMPLETE) & \
                                (table.transit_status != REQ_STATUS_COMPLETE) & \
                                (table.req_status != REQ_STATUS_COMPLETE) & \
                                (table.fulfil_status != REQ_STATUS_PARTIAL) & \
                                (table.transit_status != REQ_STATUS_PARTIAL) & \
                                (table.req_status != REQ_STATUS_PARTIAL)
                        rows = db(query).select(table.id)
                        restrict = [str(row.id) for row in rows]
                        s3.actions.append(
                            {"label": s3_str(s3.crud_labels.DELETE),
                             "url": URL(c = "req",
                                        f = "req",
                                        args = ["[id]", "delete"],
                                        ),
                             "_class": "delete-btn",
                             "restrict": restrict,
                             })
                        if not template and settings.get_req_use_commit():
                            # This is appropriate to both Items and People
                            s3.actions.append(
                                {"label": s3_str(T("Commit")),
                                 "url": URL(c = "req",
                                            f = "req",
                                            args = ["[id]", "commit_all"],
                                            ),
                                 "_class": "action-btn commit-btn",
                                 })
                            s3.jquery_ready.append(
'''S3.confirmClick('.commit-btn','%s')''' % T("Do you want to commit to this request?"))
                        # This is only appropriate for item requests
                        #query = (table.type == 1)
                        #rows = db(query).select(table.id)
                        #restrict = [str(row.id) for row in rows]
                        #s3.actions.append(
                        ##    {"label": s3_str(T("View Items")),
                        #     "url": URL(c = "req",
                        #                f = "req",
                        #                args = ["[id]", "req_item"],
                        #                ),
                        #     "_class": "action-btn",
                        #     "restrict": restrict,
                        #     })
                        # This is only appropriate for people requests
                        #query = (table.type == 3)
                        #rows = db(query).select(table.id)
                        #restrict = [str(row.id) for row in rows]
                        #s3.actions.append(
                        #    {"label": s3_str(T("View Skills")),
                        #     "url": URL(c = "req",
                        #                f = "req",
                        #                args = ["[id]", "req_skill"],
                        #                ),
                        #     "_class": "action-btn",
                        #     "restrict": restrict,
                        #     })
                        if settings.get_req_copyable():
                            s3.actions.append(
                                {"label": s3_str(T("Copy")),
                                 "url": URL(c = "req",
                                            f = "req",
                                            args = ["[id]", "copy_all"],
                                            ),
                                 "_class": "action-btn copy_all",
                                 })
                            confirm = T("Are you sure you want to create a new request as a copy of this one?")
                            s3.jquery_ready.append('''S3.confirmClick('.copy_all','%s')''' % confirm)
                        req_types = settings.get_req_req_type()
                        if not template:
                            if "Stock" in req_types:
                                if len(req_types) != 1 and (get_vars.type != "1"):
                                    # Restrict these Action Buttons to just those which are Items Requests
                                    table = r.table
                                    query = (table.deleted == False) & \
                                            (table.type == 1)
                                    rows = db(query).select(table.id)
                                    restrict = [str(row.id) for row in rows]
                                else:
                                    # All Requests are Items requests so no need to restrict
                                    restrict = None
                                if settings.get_req_use_commit():
                                    action = {"label": s3_str(T("Send")),
                                              "url": URL(c = "req",
                                                         f = "req",
                                                         args = ["[id]", "commit_all", "send"],
                                                         ),
                                              "_class": "action-btn send-btn dispatch",
                                              }
                                    if restrict is not None:
                                        action["restrict"] = restrict
                                    s3.actions.append(action)
                                    confirm = T("Are you sure you want to commit to this request and send a shipment?")
                                    s3.jquery_ready.append('''S3.confirmClick('.send-btn','%s')''' % confirm)
                                elif auth.user and auth.user.site_id:
                                    action = {# Better to force users to go through the Check process
                                              #"label": s3_str(T("Send")),
                                              #"url": URL(c = "req",
                                              #           f = "send_req",
                                              #           args = ["[id]"],
                                              #           vars = {"site_id": auth.user.site_id},
                                              #           ),
                                              "label": s3_str(T("Check")),
                                              "url": URL(c = "req",
                                                         f = "req",
                                                         args = ["[id]", "check"],
                                                         ),
                                              "_class": "action-btn send-btn dispatch",
                                              }
                                    if restrict is not None:
                                        action["restrict"] = restrict
                                    s3.actions.append(action)
                                    confirm = T("Are you sure you want to send a shipment for this request?")
                                    s3.jquery_ready.append('''S3.confirmClick('.send-btn','%s')''' % confirm)
                            if "People" in req_types and settings.get_req_commit_people():
                                if len(req_types) != 1 and (get_vars.type != "3"):
                                    # Restrict these Action Buttons to just those which are Skills Requests
                                    table = r.table
                                    query = (table.deleted == False) & \
                                            (table.type == 3)
                                    rows = db(query).select(table.id)
                                    restrict = [str(row.id) for row in rows]
                                else:
                                    # All Requests are Skills requests so no need to restrict
                                    restrict = None
                                if auth.user and auth.user.organisation_id:
                                    action = {"label": s3_str(T("Check")),
                                              "url": URL(c = "req",
                                                         f = "req",
                                                         args = ["[id]", "check"],
                                                         ),
                                              "_class": "action-btn",
                                              }
                                    if restrict is not None:
                                        action["restrict"] = restrict
                                    s3.actions.append(action)

            elif r.method == "create" and r.http == "POST":
                # Create form
                # @ToDo: DRY
                if not settings.get_req_inline_forms():
                    form_vars = output["form"].vars
                    req_type = form_vars.type
                    if req_type == "1":
                        # Stock: Open Tab for Items
                        r.next = URL(args=[form_vars.id, "req_item"])
                    elif req_type == "3":
                        # People: Open tab for Skills
                        r.next = URL(args=[form_vars.id, "req_skill"])

        return output
    s3.postp = postp

    return s3_rest_controller("req", "req",
                              rheader = s3db.req_rheader,
                              )

# =============================================================================
def req_item():
    """
        REST Controller
        @ToDo: Filter out fulfilled Items?
    """

    # Filter out Template Items
    if request.function != "fema":
        s3.filter = (FS("req_id$is_template") == False)

    def prep(r):

        if r.interactive or r.representation == "aadata":

            list_fields = s3db.get_config("req_req_item", "list_fields")
            list_fields.insert(1, "req_id$site_id")
            levels = gis.get_relevant_hierarchy_levels()
            levels.reverse()
            for level in levels:
                lfield = "req_id$site_id$location_id$%s" % level
                list_fields.insert(1, lfield)
            s3db.configure("req_req_item",
                           insertable = False,
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

    output = s3_rest_controller("req", "req_item")

    if settings.get_req_prompt_match():
        req_item_inv_item_btn = {"label": s3_str(T("Request from Facility")),
                                 "url": URL(c = "req",
                                            f = "req_item_inv_item",
                                            args = ["[id]"],
                                            ),
                                 "_class": "action-btn",
                                 }
        if s3.actions:
            s3.actions.append(req_item_inv_item_btn)
        else:
            s3.actions = [req_item_inv_item_btn]

    return output

# -----------------------------------------------------------------------------
def req_item_packs():
    """
        Called by S3OptionsFilter to provide the pack options for an Item

        Access via the .json representation to avoid work rendering menus, etc
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
                            table.quantity,
                            ).json()

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

    output["req_item"] = TABLE(TR(TH( "%s: " % T("Requested By") ),
                                  rtable.site_id.represent(req.site_id),
                                  TH( "%s: " % T("Item")),
                                  ritable.item_id.represent(req_item.item_id),
                                  ),
                               TR(TH( "%s: " % T("Requester") ),
                                  rtable.requester_id.represent(req.requester_id),
                                  TH( "%s: " % T("Quantity")),
                                  req_item.quantity,
                                  ),
                               TR(TH( "%s: " % T("Date Requested") ),
                                  rtable.date.represent(req.date),
                                  TH( T("Quantity Committed")),
                                  req_item.quantity_commit,
                                  ),
                               TR(TH( "%s: " % T("Date Required") ),
                                  rtable.date_required.represent(req.date_required),
                                  TH( "%s: " % T("Quantity in Transit")),
                                  req_item.quantity_transit,
                                  ),
                               TR(TH( "%s: " % T("Priority") ),
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

    if settings.get_supply_use_alt_name():
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
    s3.actions = [{"label": s3_str(T("Request From")),
                   "url": URL(c = request.controller,
                              f = "req",
                              args = [req_item.req_id, "req_item"],
                              vars = {"req_item_id": req_item_id,
                                      "inv_item_id": "[id]",
                                      },
                              ),
                   "_class": "action-btn",
                   }
                  ]

    return output

# =============================================================================
def req_skill():
    """
        REST Controller
        @ToDo: Filter out fulfilled Skills?
    """

    # Filter out Template Items
    s3.filter = (FS("req_id$is_template") == False)

    def prep(r):
        if r.interactive or r.representation == "aadata":
            list_fields = s3db.get_config("req_req_skill", "list_fields")
            list_fields.insert(1, "req_id$site_id")
            # @ToDo: Do this based on active gis_config/gis_hierarchy
            list_fields.insert(1, "req_id$site_id$location_id$L4")
            list_fields.insert(1, "req_id$site_id$location_id$L3")

            s3db.configure("req_req_skill",
                           insertable = False,
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
            s3.actions = [{"label": s3_str(READ),
                           "url": URL(c = "req",
                                      f = "req",
                                      args=["req_skill", "[id]"],
                                      ),
                           "_class": "action-btn",
                           },
                          ]
        return output
    s3.postp = postp

    return s3_rest_controller("req", "req_skill")

# =============================================================================
def skills_filter(req_id):
    """
        Limit commit skills to skills from the request
        - DRY helper function
    """

    rstable = s3db.req_req_skill
    rows = db(rstable.req_id == req_id).select(rstable.skill_id)
    filter_opts = []
    for r in rows:
        multi_skill_id = r.skill_id
        for skill_id in multi_skill_id:
            filter_opts.append(skill_id)
    if len(filter_opts) == 1:
        field = s3db.req_commit_skill.skill_id
        field.default = skill_id
        field.writable = False
        return
    s3db.req_commit_skill.skill_id.requires = IS_ONE_OF(db, "hrm_skill.id",
                                                        s3db.hrm_multi_skill_represent,
                                                        filterby = "id",
                                                        filter_opts = filter_opts,
                                                        sort=True,
                                                        multiple=True
                                                        )

# =============================================================================
def commit():
    """ REST Controller """

    # Check if user is affiliated to an Organisation
    if not is_affiliated():
        tablename = "req_commit_person"
        table = s3db[tablename]
        # Unaffiliated people can't commit on behalf of others
        #table.person_id.writable = False
        table.human_resource_id.writable = False
        # & can only make single-person commitments
        # (This should have happened in the main commitment)
        s3db.configure(tablename,
                       insertable = False,
                       )

    if "assign" in request.args:
        def skill_default_filter(selector, tablename=None):
            # Lookup Skills in the Request
            commit_id = request.args[0]
            ctable = s3db.req_commit
            rstable = s3db.req_req_skill
            query = (ctable.id == commit_id) & \
                    (ctable.req_id == rstable.req_id)
            multi_skills = db(query).select(rstable.skill_id,
                                            )
            skills = []
            for row in multi_skills:
                m = row.skill_id
                for s in m:
                    skills.append(s)
            return skills
        s3base.s3_set_default_filter("competency.skill_id",
                                     skill_default_filter,
                                     tablename = "hrm_human_resource")

    def prep(r):
        if r.interactive and r.record:
            # Commitments created through UI should be done via components
            if r.component:
                if r.component_name == "commit_item":
                    # Dropdown not Autocomplete
                    s3db.req_commit_item.req_item_id.widget = None

                    # Limit commit items to items from the request
                    s3db.req_commit_item.req_item_id.requires = \
                        IS_ONE_OF(db, "req_req_item.id",
                                  s3db.req_item_represent,
                                  filterby = "req_id",
                                  filter_opts = [r.record.req_id],
                                  orderby = "req_req_item.id",
                                  sort = True,
                                  )

                elif r.component_name == "commit_skill":
                    # Limit commit skills to skills from the request
                    skills_filter(r.record.req_id)

            else:
                # No Component
                table = r.table
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
                    s3db.req_commit_item.req_item_id.widget = None

                    # Options updater for inline items
                    jappend('''
$.filterOptionsS3({
 'trigger':{'alias':'commit_item','name':'req_item_id'},
 'target':{'alias':'commit_item','name':'item_pack_id'},
 'scope':'row',
'lookupPrefix':'req',
'lookupResource':'req_item_packs',
'lookupKey':'req_item_id',
'lookupField':'id',
'msgNoRecords':i18n.no_packs,
'fncPrep':S3.supply.fncPrepItem,
'fncRepresent':S3.supply.fncRepresentItem
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
                    s3db.configure("req_commit",
                                   crud_form = crud_form,
                                   )

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

                    # Limit commit skills to skills from the request
                    skills_filter(r.record.req_id)

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
                    s3db.configure("req_commit",
                                   crud_form = crud_form,
                                   )

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

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and r.method != "import":
            if not r.component:
                req_types = settings.get_req_req_type()
                if "Stock" in req_types:
                    # Items
                    s3_action_buttons(r)
                    if len(req_types) != 1 and (get_vars.type != "1"):
                        # Restrict these Action Buttons to just those which are Items Requests
                        table = r.table
                        query = (table.deleted == False) & \
                                (table.type == 1)
                        rows = db(query).select(table.id)
                        restrict = [str(row.id) for row in rows]
                    else:
                        # All Requests are Items requests so no need to restrict
                        restrict = None
                    action = {"label": s3_str(T("Prepare Shipment")),
                              "url": URL(f = "send_commit",
                                         args = ["[id]"],
                                         ),
                              "_class": "action-btn send-btn dispatch",
                              }
                    if restrict is not None:
                        action["restrict"] = restrict
                    s3.actions.append(action)
                    confirm = T("Are you sure you want to send this shipment?")
                    s3.jquery_ready.append('''S3.confirmClick('.send-btn','%s')''' % confirm)

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = commit_rheader)

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
                prepare_btn = A(T("Prepare Shipment"),
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
#                send_btn_confirm = SCRIPT("S3.confirmClick('#send_commit', '%s')" %
#                                          T("Do you want to send these Committed items?") )
#                s3.rfooter = TAG[""](send_btn,send_btn_confirm)
                #rheader.append(send_btn)
                #rheader.append(send_btn_confirm)

            elif type == 3:
                if settings.get_req_commit_people():
                    tabs.append((T("People"), "commit_person"))
                    if auth.s3_has_permission("create", "req_commit_person") and \
                       auth.s3_has_permission("update", "req_commit", r.id):
                        tabs.append((T("Assign"), "assign"))
                else:
                    tabs.append((T("Skills"), "commit_skill"))

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
                rheader = DIV(TABLE(TR(TH("%s: " % table.req_id.label),
                                       table.req_id.represent(record.req_id),
                                       ),
                                    TR(TH("%s: " % T("Committing Person")),
                                       table.committer_id.represent(record.committer_id),
                                       TH("%s: " % T("Commit Date")),
                                       s3_date_represent(record.date),
                                       ),
                                    TR(TH("%s: " % table.comments.label),
                                       TD(record.comments or "", _colspan=3)
                                       ),
                                    ),
                              )

            rheader_tabs = s3_rheader_tabs(r, tabs)
            rheader.append(rheader_tabs)

            return rheader
    return None

# =============================================================================
def send():
    """ RESTful CRUD controller """

    s3db.configure("inv_send",
                   listadd = False,
                   )

    return s3db.inv_send_controller()

# ==============================================================================
def send_commit():
    """
        Send a Shipment containing all items in a Commitment

        @ToDo: Rewrite as S3Method
                - means that permissions are better-controlled
    """

    return s3db.req_send_commit()

# -----------------------------------------------------------------------------
def send_process():
    """ Process a Shipment """

    return s3db.inv_send_process()

# =============================================================================
def commit_item():
    """ REST Controller """

    def prep(r):

        table = r.table

        # Filter to item commits
        field = table.commit_id
        field.requires = IS_EMPTY_OR(IS_ONE_OF(db, "req_commit.id",
                                               field.represent,
                                               filterby = "type",
                                               filter_opts = (1,),
                                               orderby="req_commit.date",
                                               sort=True,
                                               ))
        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def commit_req():
    """
        Function to commit items for a Request
        - i.e. copy data from a req into a commitment
        arg: req_id
        vars: site_id
    """

    req_id = request.args[0]
    site_id = request.vars.get("site_id")

    table = s3db.req_req
    r_req = db(table.id == req_id).select(table.type,
                                          limitby=(0, 1)).first()

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
        req_pack_quantity = req_item.req_req_item.pack_quantity()
        req_item_quantity = req_item.req_req_item.quantity * req_pack_quantity

        inv_item_quantity = req_item.inv_inv_item.quantity * \
                            req_item.inv_inv_item.pack_quantity()

        if inv_item_quantity > req_item_quantity:
            commit_item_quantity = req_item_quantity
        else:
            commit_item_quantity = inv_item_quantity
        commit_item_quantity = commit_item_quantity / req_pack_quantity

        if commit_item_quantity:
            req_item_id = req_item.req_req_item.id

            commit_item = {"commit_id": commit_id,
                           "req_item_id": req_item_id,
                           "item_pack_id": req_item.req_req_item.item_pack_id,
                           "quantity": commit_item_quantity,
                           }

            commit_item_id = citable.insert(**commit_item)
            commit_item["id"] = commit_item_id

            s3db.onaccept("req_commit_item", commit_item)

    # Redirect to commit
    redirect(URL(c="req", f="commit", args=[commit_id, "commit_item"]))

# =============================================================================
def send_req():
    """
        Function to send items for a Request.
        - i.e. copy data from a req into a send
        arg: req_id
        vars: site_id

        @ToDo: Rewrite as S3Method
                - means that permissions are better-controlled
    """

    req_id = request.args[0]
    site_id = request.vars.get("site_id", None)
    table = s3db.req_req
    r_req = db(table.id == req_id).select(table.req_ref,
                                          table.requester_id,
                                          table.site_id,
                                          limitby=(0, 1)).first()

    # User must have permissions over facility which is sending
    (prefix, resourcename, id) = s3db.get_instance(db.org_site, site_id)
    if not site_id or not auth.s3_has_permission("update",
                                                 "%s_%s" % (prefix,
                                                            resourcename),
                                                 record_id=id):
        session.error = T("You do not have permission to send this shipment.")
        redirect(URL(c="req", f="req",
                     args = [req_id]))

    ritable = s3db.req_req_item
    iitable = s3db.inv_inv_item
    sendtable = s3db.inv_send
    tracktable = s3db.inv_track_item
    siptable = s3db.supply_item_pack

    # Get the items for this request that have not been fulfilled or in transit
    sip_id_field = siptable.id
    sip_quantity_field = siptable.quantity
    query = (ritable.req_id == req_id) & \
            (ritable.quantity_transit < ritable.quantity) & \
            (ritable.deleted == False) & \
            (ritable.item_pack_id == sip_id_field)
    req_items = db(query).select(ritable.id,
                                 ritable.quantity,
                                 ritable.quantity_transit,
                                 ritable.quantity_fulfil,
                                 ritable.item_id,
                                 sip_quantity_field
                                 )

    if not req_items:
        # Can't use site_name as gluon/languages.py def translate has a str() which can give a Unicode error
        #site_name = s3db.org_site_represent(site_id, show_link=False)
        session.warning = \
            T("This request has no items outstanding!")

        # Redirect to view the list of items in the Request
        redirect(URL(c="req", f="req",
                     args=[req_id, "req_item"])
                 )

    # Create a new send record
    code = s3db.supply_get_shipping_code("WB",
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

    # Loop through each request item and find matches in the site inventory
    # - don't match items which are expired or in bad condition
    IN_PROCESS = s3db.inv_tracking_status["IN_PROCESS"]
    insert = tracktable.insert
    inv_remove = s3db.inv_remove
    ii_item_id_field = iitable.item_id
    ii_quantity_field = iitable.quantity
    ii_expiry_field = iitable.expiry_date
    ii_purchase_field = iitable.purchase_date
    iifields = [iitable.id,
                ii_item_id_field,
                ii_quantity_field,
                iitable.item_pack_id,
                iitable.pack_value,
                iitable.currency,
                ii_expiry_field,
                ii_purchase_field,
                iitable.bin,
                iitable.owner_org_id,
                iitable.supply_org_id,
                sip_quantity_field,
                iitable.item_source_no,
                ]
    bquery = (ii_quantity_field > 0) & \
             (iitable.site_id == site_id) & \
             (iitable.deleted == False) & \
             (iitable.item_pack_id == sip_id_field) & \
             ((iitable.expiry_date >= request.now) | ((iitable.expiry_date == None))) & \
             (iitable.status == 0)
    orderby = ii_expiry_field | ii_purchase_field

    no_match = True

    for ritem in req_items:
        rim = ritem.req_req_item
        rim_id = rim.id
        query = bquery & \
                (ii_item_id_field == rim.item_id)
        inv_items = db(query).select(*iifields,
                                     orderby=orderby)

        if len(inv_items) == 0:
            continue
        no_match = False
        one_match = len(inv_items) == 1
        # Get the Quantity Needed
        quantity_shipped = max(rim.quantity_transit, rim.quantity_fulfil)
        quantity_needed = (rim.quantity - quantity_shipped) * ritem.supply_item_pack.quantity
        # Insert the track item records
        # If there is more than one item match then we select the stock with the oldest expiry date first
        # then the oldest purchase date first
        # then a complete batch, if-possible
        iids = []
        append = iids.append
        for item in inv_items:
            if not quantity_needed:
                break
            iitem = item.inv_inv_item
            if one_match:
                # Remove this total from the warehouse stock
                send_item_quantity = inv_remove(iitem, quantity_needed)
                quantity_needed -= send_item_quantity
                append(iitem.id)
            else:
                quantity_available = iitem.quantity * item.supply_item_pack.quantity
                if iitem.expiry_date:
                    # We take first from the oldest expiry date
                    send_item_quantity = min(quantity_needed, quantity_available)
                    # Remove this total from the warehouse stock
                    send_item_quantity = inv_remove(iitem, send_item_quantity)
                    quantity_needed -= send_item_quantity
                    append(iitem.id)
                elif iitem.purchase_date:
                    # We take first from the oldest purchase date for non-expiring stock
                    send_item_quantity = min(quantity_needed, quantity_available)
                    # Remove this total from the warehouse stock
                    send_item_quantity = inv_remove(iitem, send_item_quantity)
                    quantity_needed -= send_item_quantity
                    append(iitem.id)
                elif quantity_needed <= quantity_available:
                    # Assign a complete batch together if possible
                    # Remove this total from the warehouse stock
                    send_item_quantity = inv_remove(iitem, quantity_needed)
                    quantity_needed = 0
                    append(iitem.id)
                else:
                    # Try again on the second loop, if-necessary
                    continue

            insert(send_id = send_id,
                   send_inv_item_id = iitem.id,
                   item_id = iitem.item_id,
                   req_item_id = rim_id,
                   item_pack_id = iitem.item_pack_id,
                   quantity = send_item_quantity,
                   recv_quantity = send_item_quantity,
                   status = IN_PROCESS,
                   pack_value = iitem.pack_value,
                   currency = iitem.currency,
                   bin = iitem.bin,
                   expiry_date = iitem.expiry_date,
                   owner_org_id = iitem.owner_org_id,
                   supply_org_id = iitem.supply_org_id,
                   item_source_no = iitem.item_source_no,
                   #comments = comment,
                   )
        # 2nd pass
        for item in inv_items:
            if not quantity_needed:
                break
            iitem = item.inv_inv_item
            if iitem.id in iids:
                continue
            # We have no way to know which stock we should take 1st so show all with quantity 0 & let the user decide
            send_item_quantity = 0
            insert(send_id = send_id,
                   send_inv_item_id = iitem.id,
                   item_id = iitem.item_id,
                   req_item_id = rim_id,
                   item_pack_id = iitem.item_pack_id,
                   quantity = send_item_quantity,
                   status = IN_PROCESS,
                   pack_value = iitem.pack_value,
                   currency = iitem.currency,
                   bin = iitem.bin,
                   expiry_date = iitem.expiry_date,
                   owner_org_id = iitem.owner_org_id,
                   supply_org_id = iitem.supply_org_id,
                   item_source_no = iitem.item_source_no,
                   #comments = comment,
                   )

    if no_match:
        # Can't use %(site_name)s as gluon/languages.py def translate has a str() which can give a Unicode error
        #site_name = s3db.org_site_represent(site_id, show_link=False)
        session.warning = \
            T("This site has no items exactly matching this request. There may still be other items in stock which can fulfill this request!")

    # Redirect to view the list of items in the Send
    redirect(URL(c="inv", f="send",
                 args=[send_id, "track_item"])
             )

# =============================================================================
def commit_item_json():
    """
        Used by s3.supply.js

        Access via the .json representation to avoid work rendering menus, etc
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
                               orderby = db.req_commit.date,
                               )

    json_str = '''[%s,%s''' % (json.dumps({"id": s3_str(T("Committed")),
                                           "quantity": "#"
                                           }),
                               records.json()[1:],
                               )

    response.headers["Content-Type"] = "application/json"
    return json_str

# =============================================================================
def fema():
    """
        Custom Report to list all open requests for items that FEMA can supply

        @ToDo: Filter to just Sites that FEMA support
    """

    ritable = s3db.req_req_item
    rtable = db.req_req
    itable = db.supply_item
    ictable = db.supply_item_category
    citable = db.supply_catalog_item
    query = (ictable.name == "FEMA") & \
            (citable.item_category_id == ictable.id) & \
            (citable.item_id == itable.id) & \
            (itable.deleted != True)
    fema_items = db(query).select(itable.id)
    fema_item_ids = [item.id for item in fema_items]

    REQ_STATUS_COMPLETE = 2
    s3.filter = (rtable.deleted != True) & \
                (rtable.is_template == False) & \
                (rtable.commit_status != REQ_STATUS_COMPLETE) & \
                (rtable.transit_status != REQ_STATUS_COMPLETE) & \
                (rtable.fulfil_status != REQ_STATUS_COMPLETE) & \
                (ritable.req_id == rtable.id) & \
                (ritable.quantity > ritable.quantity_commit) & \
                (ritable.quantity > ritable.quantity_transit) & \
                (ritable.quantity > ritable.quantity_fulfil) & \
                (ritable.deleted != True) & \
                (ritable.item_id.belongs(fema_item_ids))

    # Filter Widgets
    filter_widgets = [
        s3base.S3OptionsFilter("req_id$site_id",
                               label = T("Facility"),
                               #cols = 3,
                               ),
    ]
    s3db.configure("req_req_item", filter_widgets = filter_widgets)

    return req_item()

# -----------------------------------------------------------------------------
def need():
    """
        RESTful CRUD Controller for Needs
    """

    def prep(r):
        if r.component_name == "impact":
            s3db.stats_impact.location_id.default = r.record.location_id
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.req_rheader)

# -----------------------------------------------------------------------------
def need_line():
    """
        RESTful CRUD Controller for Need Lines
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def need_response():
    """
        RESTful CRUD Controller for Need Responses (i.e. Activity Groups)
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def need_response_line():
    """
        RESTful CRUD Controller for Need Response Lines (i.e. Activities)
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def facility():
    # Open record in this controller after creation
    s3db.configure("org_facility",
                   create_next = URL(c="req", f="facility",
                                     args = ["[id]", "read"]),
                   )

    return s3db.org_facility_controller()

# END =========================================================================
