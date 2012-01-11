# -*- coding: utf-8 -*-

"""
    Request Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @author: Fran Boon
    @date-created: 2010-08-16

    A module to record requests & commitments for:
     - inventory items
     - people (actually request skills, but commit people)
     - assets
     - other

     @ToDo: Link to Tasks via link table (optional way of working)
"""

module = "req"

if deployment_settings.has_module(module): # or deployment_settings.has_module("inv"):

    # -------------------------------------------------------------------------
    REQ_STATUS_NONE       = 0
    REQ_STATUS_PARTIAL    = 1
    REQ_STATUS_COMPLETE   = 2

    req_status_opts = { REQ_STATUS_NONE:     SPAN(T("None"),
                                                  _class = "req_status_none"),
                        REQ_STATUS_PARTIAL:  SPAN(T("Partial"),
                                                  _class = "req_status_partial"),
                        REQ_STATUS_COMPLETE: SPAN(T("Complete"),
                                                  _class = "req_status_complete")
                       }

    # Component definitions should be outside conditional model loads
    s3mgr.model.add_component("req_req",
                              org_site=super_key(db.org_site))
                              #org_organisation = "donated_by_id")

    if deployment_settings.has_module("event"):
        s3mgr.model.add_component("req_req", event_event="event_id")

    if deployment_settings.has_module("doc"):
        s3mgr.model.add_component("req_document", req_req="req_id")

    # Should we have multiple Items/Skills per Request?
    multiple_req_items = deployment_settings.get_req_multiple_req_items()

    if deployment_settings.has_module("inv"):
        # Request Items as component of Request & Items
        s3mgr.model.add_component("req_req_item",
                                  req_req=dict(joinby="req_id",
                                               multiple=multiple_req_items),
                                  supply_item="item_id")

    # Request Skills as component of Request & Skills
    s3mgr.model.add_component("req_req_skill",
                              req_req=dict(joinby="req_id",
                                           multiple=multiple_req_items),
                              hrm_skill="skill_id")

    # Commitment as a component of Requests & Sites
    s3mgr.model.add_component("req_commit",
                              req_req="req_id",
                              org_site=super_key(db.org_site))

    if deployment_settings.has_module("inv"):
        # Commitment Items as component of Commitment
        s3mgr.model.add_component("req_commit_item",
                                  req_commit="commit_id")

    if deployment_settings.has_module("hrm"):
        # Commitment Persons as component of Commitment
        s3mgr.model.add_component("req_commit_person",
                                  req_commit="commit_id")

    def req_tables():
        """ Load the Request Tables when needed """

        module = "req"

        organisation_id = s3db.org_organisation_id
        organisation_represent = s3db.org_organisation_represent
        site_id = s3db.org_site_id
        org_site_represent = s3db.org_site_represent
        human_resource_id = s3db.hrm_human_resource_id

        if deployment_settings.has_module("inv"):
            s3mgr.load("supply_item")
            item_id = response.s3.item_id
            supply_item_id = response.s3.supply_item_id
            item_pack_id = response.s3.item_pack_id
            item_pack_virtualfields = response.s3.item_pack_virtualfields

        if deployment_settings.has_module("hrm"):
            multi_skill_id = s3db.hrm_multi_skill_id

        if deployment_settings.has_module("event"):
            s3mgr.load("event_event")
        event_id = response.s3.event_id

        req_status = S3ReusableField("req_status", "integer",
                                 label = T("Request Status"),
                                 requires = IS_NULL_OR(IS_IN_SET(req_status_opts,
                                                                 zero = None)),
                                 represent = lambda opt: \
                                    req_status_opts.get(opt, UNKNOWN_OPT),
                                 default = REQ_STATUS_NONE,
                                 writable = deployment_settings.get_req_status_writable(),
                                )

        req_priority_opts = {
            3:T("High"),
            2:T("Medium"),
            1:T("Low")
        }

        req_type_opts = {
            9:T("Other")
        }

        if deployment_settings.has_module("inv"):
             # Number hardcoded in controller
            req_type_opts[1] = deployment_settings.get_req_type_inv_label()
        #if deployment_settings.has_module("asset"):
        #    req_type_opts[2] = T("Assets")
        if deployment_settings.has_module("hrm"):
            req_type_opts[3] = deployment_settings.get_req_type_hrm_label()
        #if deployment_settings.has_module("cr"):
        #    req_type_opts[4] = T("Shelter")

        def req_priority_represent(id):
            src = "/%s/static/img/priority/priority_%d.gif" % \
                      (request.application, (id or 4))
            return DIV(IMG(_src= src))

        # ---------------------------------------------------------------------
        def req_hide_quantities(table):
            """
                Hide the Update Quantity Status Fields from Request create forms
            """
            if not deployment_settings.get_req_quantities_writable():
                table.quantity_commit.writable = table.quantity_commit.readable = False
                table.quantity_transit.writable = table.quantity_transit.readable= False
                table.quantity_fulfil.writable = table.quantity_fulfil.readable = False

        # ---------------------------------------------------------------------
        # Requests
        resourcename = "req"
        tablename = "req_req"
        table = db.define_table(tablename,
                                event_id(default=session.s3.event,
                                         ondelete="SET NULL"),
                                Field("type", "integer",
                                      requires = IS_IN_SET(req_type_opts, zero=None),
                                      represent = lambda opt: \
                                        req_type_opts.get(opt, UNKNOWN_OPT),
                                      label = T("Request Type")),
                                Field("request_number",
                                      unique = True,
                                      label = T("Request Number")),
                                Field("date", # DO NOT CHANGE THIS
                                      "datetime",
                                      label = T("Date Requested"),
                                      requires = [IS_EMPTY_OR(
                                                  IS_UTC_DATETIME_IN_RANGE(
                                                    maximum=request.utcnow,
                                                    error_message="%s %%(max)s!" %
                                                        T("Enter a valid past date")))],
                                      widget = S3DateTimeWidget(past=8760, # Hours, so 1 year
                                                                future=0),
                                      default = request.utcnow,
                                      represent = s3_utc_represent),
                                Field("priority",
                                      "integer",
                                      default = 2,
                                      label = T("Priority"),
                                      represent = req_priority_represent,
                                      requires = IS_NULL_OR(
                                                    IS_IN_SET(req_priority_opts))
                                      ),
                                Field("purpose",
                                      "text",
                                      label=T("Purpose")), # Donations: What will the Items be used for?; People: Task Details
                                Field("date_required",
                                      "datetime",
                                      label = T("Date Required"),
                                      requires = [IS_EMPTY_OR(
                                                  IS_UTC_DATETIME_IN_RANGE(
                                                    minimum=request.utcnow - datetime.timedelta(days=1),
                                                    error_message="%s %%(min)s!" %
                                                        T("Enter a valid future date")))],
                                      widget = S3DateTimeWidget(past=0,
                                                                future=8760),  # Hours, so 1 year
                                      represent = s3_utc_represent),
                                Field("date_required_until",
                                      "datetime",
                                      label = T("Date Required Until"),
                                      requires = [IS_EMPTY_OR(
                                                  IS_UTC_DATETIME_IN_RANGE(
                                                    minimum=request.utcnow - datetime.timedelta(days=1),
                                                    error_message="%s %%(min)s!" %
                                                        T("Enter a valid future date")))],
                                      widget = S3DateTimeWidget(past=0,
                                                                future=8760), # Hours, so 1 year
                                      represent = s3_utc_represent,
                                      readable = False,
                                      writable = False
                                      ),
                                human_resource_id("requester_id",
                                                  label = T("Requester"),
                                                  empty = False,
                                                  default = s3_logged_in_human_resource()),
                                human_resource_id("assigned_to_id", # This field should be in req_commit, but that complicates the UI
                                                  readable = False,
                                                  writable = False,
                                                  label = T("Assigned To")),
                                human_resource_id("approved_by_id",
                                                  label = T("Approved By")),
                                human_resource_id("request_for_id",
                                                  label = T("Requested For"),
                                                  #default = s3_logged_in_human_resource()
                                                  ),
                                super_link("site_id", "org_site",
                                           label = T("Requested For Facility"),
                                           default = auth.user.site_id if auth.is_logged_in() else None,
                                           readable = True,
                                           writable = True,
                                           empty = False,
                                           # Comment these to use a Dropdown & not an Autocomplete
                                           #widget = S3SiteAutocompleteWidget(),
                                           #comment = DIV(_class="tooltip",
                                           #              _title="%s|%s" % (T("Requested By Facility"),
                                           #                                T("Enter some characters to bring up a list of possible matches"))),
                                           represent = org_site_represent),
                                #Field("location",
                                #      label = T("Neighborhood")),
                                Field("transport_req",
                                       "boolean",
                                      label = T("Transportation Required")),
                                Field("security_req",
                                      "boolean",
                                      label = T("Security Required")),
                                Field("date_recv",
                                      "datetime",
                                      label = T("Date Received"), # Could be T("Date Delivered") - make deployment_setting
                                      requires = [IS_EMPTY_OR(
                                                  IS_UTC_DATETIME_IN_RANGE(
                                                    maximum=request.utcnow,
                                                    error_message="%s %%(max)s!" %
                                                        T("Enter a valid past date")))],
                                      widget = S3DateTimeWidget(past=8760, # Hours, so 1 year
                                                                future=0),
                                      represent = s3_utc_represent,
                                      readable = False,
                                      writable = False
                                      ),
                                human_resource_id("recv_by_id",
                                                  label = T("Received By"),
                                                  # @ToDo: Set this in Update forms? Dedicated 'Receive' button?
                                                  # (Definitely not in Create forms)
                                                  #default = s3_logged_in_human_resource()
                                                  ),
                                req_status("commit_status",
                                           label = T("Commit. Status")),
                                req_status("transit_status",
                                           label = T("Transit Status")),
                                req_status("fulfil_status",
                                           label = T("Fulfil. Status")),
                                Field("cancel",
                                      "boolean",
                                      label = T("Cancel"),
                                      default = False),
                                s3_comments(comment=""),
                                *s3_meta_fields())

        if deployment_settings.has_module("inv"):
            table.type.default = 1
        #elif deployment_settings.has_module("asset"):
        #    table.type.default = 2
        elif deployment_settings.has_module("hrm"):
            table.type.default = 3
        #elif deployment_settings.has_module("cr"):
        #    table.type.default = 4


        # CRUD strings
        ADD_REQUEST = T("Make Request")
        LIST_REQUEST = T("List Requests")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_REQUEST,
            title_display = T("Request Details"),
            title_list = LIST_REQUEST,
            title_update = T("Edit Request"),
            title_search = T("Search Requests"),
            subtitle_create = ADD_REQUEST,
            subtitle_list = T("Requests"),
            label_list_button = LIST_REQUEST,
            label_create_button = ADD_REQUEST,
            label_delete_button = T("Delete Request"),
            msg_record_created = T("Request Added"),
            msg_record_modified = T("Request Updated"),
            msg_record_deleted = T("Request Canceled"),
            msg_list_empty = T("No Requests"))

        # Represent
        def req_represent(id, link = True):
            id = int(id)
            table = db.req_req
            if id:
                query = (table.id == id)
                req = db(query).select(table.date,
                                       table.type,
                                       table.site_id,
                                       limitby=(0, 1)).first()
                if not req:
                    return NONE
                req = "%s - %s" % (org_site_represent(req.site_id,
                                                      link = False),
                                   req.date)
                if link:
                    return A(req,
                             _href = URL(c = "req",
                                         f = "req",
                                         args = [id]),
                             _title = T("Go to Request"))
                else:
                    return req
            else:
                return NONE

        # Reusable Field
        req_id = S3ReusableField("req_id", db.req_req, sortby="date",
                                 requires = IS_ONE_OF(db,
                                                      "req_req.id",
                                                      lambda id:
                                                        req_represent(id,
                                                                      False),
                                                      orderby="req_req.date",
                                                      sort=True),
                                 represent = req_represent,
                                 label = T("Request"),
                                 ondelete = "CASCADE")

        #----------------------------------------------------------------------
        def req_onaccept(form):

            table = db.req_req

            # Configure the next page to go to based on the request type
            tablename = "req_req"
            if "default_type" in request.get_vars:
                type = request.get_vars.default_type
            else:
                type = form.vars.type

            if type == "1" and deployment_settings.has_module("inv"):
                s3mgr.configure(tablename,
                                create_next = URL(c="req",
                                                  f="req",
                                                  args=["[id]", "req_item"]),
                                update_next = URL(c="req",
                                                  f="req",
                                                  args=["[id]", "req_item"]))
            elif type == "2" and deployment_settings.has_module("asset"):
                s3mgr.configure(tablename,
                                create_next = URL(c="req",
                                                  f="req",
                                                  args=["[id]", "req_asset"]),
                                update_next = URL(c="req",
                                                  f="req",
                                                  args=["[id]", "req_asset"]))
            elif type == "3" and deployment_settings.has_module("hrm"):
                s3mgr.configure(tablename,
                                create_next = URL(c="req",
                                                  f="req",
                                                  args=["[id]", "req_skill"]),
                                update_next = URL(c="req",
                                                  f="req",
                                                  args=["[id]", "req_skill"]))
            #elif type == "4" and deployment_settings.has_module("cr"):
            #    s3mgr.configure(tablename,
            #                    create_next = URL(c="req",
            #                                      f="req",
            #                                      args=["[id]", "req_shelter"]),
            #                    update_next = URL(c="req",
            #                                      f="req",
            #                                      args=["[id]", "req_shelter"]))

        s3mgr.configure(tablename,
                        onaccept = req_onaccept,
                        list_fields = ["id",
                                       "type",
                                       "event_id",
                                       "request_number",
                                       "priority",
                                       "commit_status",
                                       "transit_status",
                                       "fulfil_status",
                                       #"date",
                                       "date_required",
                                       #"requester_id",
                                       #"comments",
                                    ])

        #----------------------------------------------------------------------
        def req_create_form_mods():
            """
                Function to be called from REST prep functions
                 - main module & components (sites & events)
            """
            # Hide fields which don't make sense in a Create form
            table = db.req_req
            table.commit_status.readable = table.commit_status.writable = False
            table.transit_status.readable = table.transit_status.writable = False
            table.fulfil_status.readable = table.fulfil_status.writable = False
            table.cancel.readable = table.cancel.writable = False

            return

        # Script to inject into Pages which include Request create forms
        req_help_msg = ""
        req_help_msg_template = T("If the request is for %s, please enter the details on the next screen.")
        types = []
        if deployment_settings.has_module("inv"):
            types.append(T("Inventory Items"))
        #if deployment_settings.has_module("asset"):
        #    types.append(T("Assets"))
        if deployment_settings.has_module("hrm"):
            types.append(T("Staff"))
        #if deployment_settings.has_module("cr"):
        #    types.append(T("Shelter"))
        if types:
            message = types.pop(0)
            for type in types:
                message = "%s or %s" % (message, type)
            req_help_msg = req_help_msg_template % message

        req_helptext_script = SCRIPT("""
            $(function() {
                var req_help_msg = '%s\\n%s';
                // Provide some default help text in the Details box if empty
                if (!$('#req_req_comments').val()) {
                    $('#req_req_comments').addClass('default-text').attr({ value: req_help_msg }).focus(function(){
                        if($(this).val() == req_help_msg){
                            // Clear on click if still default
                            $(this).val('').removeClass('default-text');
                        }
                    });
                    $('form').submit( function() {
                        // Do the normal form-submission tasks
                        // @ToDo: Look to have this happen automatically
                        // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
                        // http://api.jquery.com/bind/
                        S3ClearNavigateAwayConfirm();

                        if ($('#req_req_comments').val() == req_help_msg) {
                            // Default help still showing
                            if ($('#req_req_type').val() == 9) {
                                // Requests of type 'Other' need this field to be mandatory
                                $('#req_req_comments').after('<div id="type__error" class="error" style="display: block;">%s</div>');
                                // Reset the Navigation protection
                                S3SetNavigateAwayConfirm();
                                // Move focus to this field
                                $('#req_req_comments').focus();
                                // Prevent the Form's save from continuing
                                return false;
                            } else {
                                // Clear the default help
                                $('#req_req_comments').val('');
                                // Allow the Form's save to continue
                                return true;
                            }
                        } else {
                            // Allow the Form's save to continue
                            return true;
                        }
                    });
                }
            });""" % (T('If the request type is "Other", please enter request details here.'),
                      req_help_msg,
                      T("Details field is required!"))
            )

        # ---------------------------------------------------------------------
        def req_match():
            """
                Function to be called from controller functions to display all
                requests as a tab for a site.
                @ToDo: Filter out requests from this site
            """

            output = dict()

            if deployment_settings.has_module("inv"):
                # Load Models (for tabs at least)
                s3mgr.load("inv_inv_item")
            #if deployment_settings.has_module("hrm"):
            #    # Load Models (for tabs at least)
            #    s3mgr.load("hrm_skill")

            if "viewing" not in request.vars:
                return output
            else:
                viewing = request.vars.viewing
            if "." in viewing:
                tablename, id = viewing.split(".", 1)
            else:
                return output
            site_id = db[tablename][id].site_id
            response.s3.actions = [dict(url = URL(c = "req",
                                                  f = "req",
                                                  args = ["[id]","check"],
                                                  vars = {"site_id": site_id}
                                                 ),
                                        _class = "action-btn",
                                        label = str(T("Check")),
                                        ),
                                   dict(url = URL(c = "req",
                                                  f = "commit_req",
                                                  args = ["[id]"],
                                                  vars = {"site_id": site_id}
                                                 ),
                                        _class = "action-btn",
                                        label = str(T("Commit")),
                                        ),
                                   dict(url = URL(c = "req",
                                                  f = "send_req",
                                                  args = ["[id]"],
                                                  vars = {"site_id": site_id}
                                                 ),
                                        _class = "action-btn",
                                        label = str(T("Send")),
                                        )
                                   ]

            rheader_dict = dict(org_office = office_rheader)
            if deployment_settings.has_module("cr"):
                rheader_dict["cr_shelter"] = response.s3.shelter_rheader
            if deployment_settings.has_module("hms"):
                rheader_dict["hms_hospital"] = hms_hospital_rheader

            s3mgr.configure("req_req", insertable=False)
            output = s3_rest_controller("req", "req",
                                        method = "list",
                                        rheader = rheader_dict[tablename])
            if isinstance(output, dict):
                output["title"] = s3.crud_strings[tablename]["title_display"]

            return output

        # ---------------------------------------------------------------------
        def req_check(r, **attr):
            """
                Check to see if your Inventory can be used to match any open Requests
            """

            # Load Models (for tabs at least)
            s3mgr.load("inv_inv_item")

            site_id = r.vars.site_id
            site_name = org_site_represent(site_id, link = False)
            output = {}
            output["title"] = T("Check Request")
            output["rheader"] = req_rheader(r, check_page = True)

            stable = db.org_site
            ltable = s3db.gis_location
            query = (stable.id == site_id ) & \
                    (stable.location_id == ltable.id)
            location_r = db(query).select(ltable.lat,
                                          ltable.lon,
                                          limitby=(0, 1)).first()
            query = (stable.id == r.record.site_id ) & \
                    (stable.location_id == ltable.id)
            req_location_r = db(query).select(ltable.lat,
                                              ltable.lon,
                                              limitby=(0, 1)).first()
            try:
                distance = gis.greatCircleDistance(location_r.lat, location_r.lon,
                                                   req_location_r.lat, req_location_r.lon,)
                output["rheader"][0].append(TR(TH( T("Distance from %s:") % site_name),
                                               TD( T("%.1f km") % distance)
                                               ))
            except:
                pass

            output["subtitle"] = T("Request Items")

            # Get req_items & inv_items from this site
            table = db.req_req_item
            query = (table.req_id == r.id ) & \
                    (table.deleted == False )
            req_items = db(query).select(table.id,
                                         table.item_id,
                                         table.quantity,
                                         table.item_pack_id,
                                         table.quantity_commit,
                                         table.quantity_transit,
                                         table.quantity_fulfil)
            itable = db.inv_inv_item
            query = (itable.site_id == site_id ) & \
                    (itable.deleted == False )
            inv_items = db(query).select(itable.item_id,
                                         itable.quantity,
                                         itable.item_pack_id)
            inv_items_dict = inv_items.as_dict(key = "item_id")

            if len(req_items):
                items = TABLE(THEAD(TR(#TH(""),
                                       TH(table.item_id.label),
                                       TH(table.quantity.label),
                                       TH(table.item_pack_id.label),
                                       TH(table.quantity_commit.label),
                                       TH(table.quantity_transit.label),
                                       TH(table.quantity_fulfil.label),
                                       TH(T("Quantity in %s's Inventory") % site_name),
                                       TH(T("Match?"))
                                      )
                                    ),
                              _id = "list",
                              _class = "dataTable display")

                for req_item in req_items:
                    # Convert inv item quantity to req item quantity
                    try:
                        inv_item = Storage(inv_items_dict[req_item.item_id])
                        inv_quantity = inv_item.quantity * \
                                       inv_item.pack_quantity / \
                                       req_item.pack_quantity

                    except:
                        inv_quantity = NONE

                    if inv_quantity and inv_quantity != NONE:
                        if inv_quantity < req_item.quantity:
                            status = SPAN(T("Partial"), _class = "req_status_partial")
                        else:
                            status = SPAN(T("YES"), _class = "req_status_complete")
                    else:
                        status = SPAN(T("NO"), _class = "req_status_none"),

                    items.append(TR( #A(req_item.id),
                                     response.s3.item_represent(req_item.item_id),
                                     req_item.quantity,
                                     response.s3.item_pack_represent(req_item.item_pack_id),
                                     # This requires an action btn to get the req_id
                                     req_item.quantity_commit,
                                     req_item.quantity_fulfil,
                                     req_item.quantity_transit,
                                     #req_quantity_represent(req_item.quantity_commit, "commit"),
                                     #req_quantity_represent(req_item.quantity_fulfil, "fulfil"),
                                     #req_quantity_represent(req_item.quantity_transit, "transit"),
                                     inv_quantity,
                                     status,
                                    )
                                )
                    output["items"] = items
                    #response.s3.actions = [req_item_inv_item_btn]
                    response.s3.no_sspag = True # pag won't work
            else:
                output["items"] = s3.crud_strings.req_req_item.msg_list_empty

            response.view = "list.html"
            response.s3.no_formats = True

            return output

        s3mgr.model.set_method(module, resourcename,
                               method = "check", action=req_check)

        # ---------------------------------------------------------------------
        def req_quantity_represent(quantity, type):
                # @ToDo: There should be better control of this feature - currently this only works
                #        with req_items which are being matched by commit / send / recv
                if quantity and not deployment_settings.get_req_quantities_writable():
                    return TAG[""]( quantity,
                                    A(DIV(_class = "quantity %s ajax_more collapsed" % type
                                          ),
                                        _href = "#",
                                      )
                                    )
                else:
                    return quantity

        # ---------------------------------------------------------------------
        def req_rheader(r, check_page = False):
            """ Resource Header for Requests """

            if r.representation == "html":
                if r.name == "req":
                    record = r.record
                    if record:
                        tabs = [(T("Edit Details"), None)]
                        if record.type == 1 and deployment_settings.has_module("inv"):
                            if deployment_settings.get_req_multiple_req_items():
                                req_item_tab_label = T("Items")
                            else:
                                req_item_tab_label = T("Item")
                            tabs.append((req_item_tab_label, "req_item"))
                        elif record.type == 3 and deployment_settings.has_module("hrm"):
                            tabs.append((T("People"), "req_skill"))
                        if deployment_settings.has_module("doc"):
                            tabs.append((T("Documents"), "document"))
                        if deployment_settings.get_req_use_commit():
                            tabs.append((T("Commitments"), "commit"))

                        rheader_tabs = s3_rheader_tabs(r, tabs)

                        site_id = request.vars.site_id
                        if site_id:
                            site_name = org_site_represent(site_id, link = False)
                            commit_btn = TAG[""](
                                        A( T("Commit from %s") % site_name,
                                            _href = URL(c = "req",
                                                        f = "commit_req",
                                                        args = [r.id],
                                                        vars = dict(site_id = site_id)
                                                        ),
                                            _class = "action-btn"
                                           ),
                                        A( T("Send from %s") % site_name,
                                            _href = URL(c = "req",
                                                        f = "send_req",
                                                        args = [r.id],
                                                        vars = dict(site_id = site_id)
                                                        ),
                                            _class = "action-btn"
                                           )
                                        )
                        #else:
                        #    commit_btn = A( T("Commit"),
                        #                    _href = URL(c = "req",
                        #                                f = "commit",
                        #                                args = ["create"],
                        #                                vars = dict(req_id = r.id)
                        #                                ),
                        #                    _class = "action-btn"
                        #                   )
                            response.s3.rfooter = commit_btn

                        if deployment_settings.get_req_show_quantity_transit():
                            transit_status = req_status_opts.get(record.transit_status, "")
                            try:
                                if record.transit_status in [REQ_STATUS_PARTIAL,REQ_STATUS_COMPLETE] and \
                                   record.fulfil_status in [None, REQ_STATUS_NONE, REQ_STATUS_PARTIAL]:
                                    site_record = db.org_site[record.site_id]
                                    query = (db[site_record.instance_type].uuid == site_record.uuid)
                                    id = db(query).select(db[site_record.instance_type].id,
                                                          limitby=(0, 1)).first().id
                                    transit_status = SPAN( transit_status,
                                                           "           ",
                                                           A(T("Incoming Shipments"),
                                                             _href = URL(c = site_record.instance_type.split("_")[0],
                                                                         f = "incoming",
                                                                         vars = {"viewing" : "%s.%s" % (site_record.instance_type, id)}
                                                                         )
                                                             )
                                                           )
                            except:
                                pass
                            transit_status_cells = (TH( "%s: " % T("Transit Status")),
                                                    transit_status)
                        else:
                            transit_status_cells = ("","")

                        rheader = DIV( TABLE(
                                           TR(
                                            TH("%s: " % T("Date Required")),
                                            s3_date_represent(record.date_required),
                                            TH( "%s: " % T("Commitment Status")),
                                            req_status_opts.get(record.commit_status, ""),
                                            ),
                                           TR(
                                            TH( "%s: " % T("Date Requested")),
                                            s3_date_represent(record.date),
                                            *transit_status_cells
                                            ),
                                           TR(
                                            TH( "%s: " % T("Requested By")),
                                            org_site_represent(record.site_id),
                                            TH( "%s: " % T("Fulfillment Status")),
                                            req_status_opts.get(record.fulfil_status, "")
                                            ),
                                           TR(
                                            TH( "%s: " % T("Details")),
                                            TD(record.comments or "", _colspan=3)
                                            ),
                                        ),
                                        #commit_btn,
                                        )
                        if not check_page:
                            rheader.append(rheader_tabs)

                        return rheader
                    #else:
                        # No Record means that we are either a Create or List Create
                        # Inject the helptext script
                        # Removed because causes an error if validation fails twice
                        # return response.s3.req_helptext_script
            return None

        # ---------------------------------------------------------------------
        def req_controller():
            """
                Request Controller
            """

            req_table = db.req_req

            # Set the req_item site_id (Requested From)
            # @ToDo: What does this do? Where does it get called from?
            if "req_item_id" in request.vars and "inv_item_id" in request.vars:
                s3mgr.load("inv_inv_item")
                site_id = db.inv_inv_item[request.vars.inv_item_id].site_id
                db.req_req_item[request.vars.req_item_id] = dict(site_id = site_id)

            if "document" in request.args:
                s3mgr.load("doc_document")

            default_type = request.vars.default_type
            if default_type:
                type_field = req_table.type
                type_field.default = int(default_type)
                type_field.writable = False

            def prep(r):

                # Remove type from list_fields
                list_fields = s3mgr.model.get_config("req_req",
                                                     "list_fields")
                try:
                    list_fields.remove("type")
                except:
                     # It has already been removed.
                     # This can happen if the req controller is called
                     # for a second time, such as when printing reports
                    pass
                s3mgr.configure(tablename, list_fields=list_fields)

                if r.interactive:
                    # Set Fields and Labels depending on type
                    type = ( r.record and r.record.type ) or \
                           ( request.vars and request.vars.default_type )
                    if type:
                        type = int(type)
                        req_table.type.default = int(type)

                        # This prevents the type from being edited AFTER it is set
                        req_table.type.readable = False
                        req_table.type.writable = False

                        crud_strings = deployment_settings.get_req_req_crud_strings(type)
                        if crud_strings:
                            s3.crud_strings["req_req"] = crud_strings

                        # Filter the query based on type
                        if response.s3.filter:
                            response.s3.filter = response.s3.filter & \
                                                 (db.req_req.type == type)
                        else:
                            response.s3.filter = (db.req_req.type == type)

                    # @ToDo: apply these changes via JS for the create form where type is edittable
                    if type == 1: # Item
                        req_table.date_recv.readable = True
                        req_table.date_recv.writable = True
                        req_table.date_recv.readable = True
                        req_table.date_recv.writable = True

                        req_table.purpose.label = T("What the Items will be used for")
                        req_table.site_id.label =T("Deliver To")
                        req_table.request_for_id.label = T("Deliver To")
                        req_table.recv_by_id.label = T("Delivered To")

                    if type == 3: # Person
                        req_table.date_required_until.readable = True
                        req_table.date_required_until.writable = True

                        req_table.purpose.label = T("Task Details")
                        req_table.site_id.label =  T("Report To")
                        req_table.request_for_id.label = T("Report To")
                        req_table.recv_by_id.label = T("Reported To")

                    if r.method != "update" and r.method != "read":
                        if not r.component:
                            # Hide fields which don't make sense in a Create form
                            # - includes one embedded in list_create
                            # - list_fields over-rides, so still visible within list itself
                            req_create_form_mods()

                            # Get the default Facility for this user
                            # @ToDo: Use site_id in User Profile (like current organisation_id)
                            if deployment_settings.has_module("hrm"):
                                query = (db.hrm_human_resource.person_id == s3_logged_in_person())
                                site = db(query).select(db.org_site.id,
                                                        limitby=(0, 1)).first()
                                if site:
                                    r.table.site_id.default = site.id

                        elif r.component.name == "document":
                            s3.crud.submit_button = T("Add")
                            table = r.component.table
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
                            req_hide_quantities(table)

                        elif r.component.name == "req_skill":
                            req_hide_quantities(r.component.table)

                if r.component and r.component.name == "commit":
                    table = r.component.table
                    # Allow commitments to be added when doing so as a component
                    s3mgr.configure(table,
                                    listadd = True)

                    type = r.record.type
                    if type == 1: # Items
                        # Limit site_id to facilities the user has permissions for
                        auth.permission.permitted_facilities(table=r.table,
                                                             error_msg=T("You do not have permission for any facility to make a commitment."))
                        if r.interactive:
                            # Redirect to the Items tab after creation
                            s3mgr.configure(table,
                                            create_next = URL(c="req", f="commit",
                                                              args=["[id]", "commit_item"]),
                                            update_next = URL(c="req", f="commit",
                                                              args=["[id]", "commit_item"]))
                    else:
                        # Non-Item commits can have an Organisation
                        # Check if user is affiliated to an Organisation
                        if is_affiliated():
                            # Limit organisation_id to organisations the user has permissions for
                            auth.permission.permitted_organisations(table=r.table,
                                                                    redirect_on_error=False)
                            table.organisation_id.readable = True
                            table.organisation_id.writable = True
                        else:
                            # Unaffiliated people can't commit on behalf of others
                            r.component.table.committer_id.writable = False
                            r.component.table.committer_id.comment = None

                        # Non-Item commits shouldn't have a From Inventory
                        # @ToDo: Assets do?
                        table.site_id.readable = False
                        table.site_id.writable = False
                        if r.interactive and r.record.type == 3: # People
                            # Redirect to the Persons tab after creation
                            s3mgr.configure(table,
                                            create_next = URL(c="req", f="commit",
                                                              args=["[id]", "commit_person"]),
                                            update_next = URL(c="req", f="commit",
                                                              args=["[id]", "commit_person"]))
                else:
                    # Limit site_id to facilities the user has permissions for
                    # @ToDo: Non-Item requests shouldn't be bound to a Facility?
                    auth.permission.permitted_facilities(table=r.table,
                                                         error_msg=T("You do not have permission for any facility to make a request."))

                return True
            response.s3.prep = prep

            # Post-process
            def postp(r, output):

                if r.interactive:
                    s3_action_buttons(r)
                    if not r.component:
                        if deployment_settings.get_req_use_commit():
                            # This is appropriate to all
                            response.s3.actions.append(
                                dict(url = URL(c = "req",
                                               f = "req",
                                               args = ["[id]", "commit", "create"]),
                                     _class = "action-btn",
                                     label = str(T("Commit"))
                                    )
                                )
                        # This is only appropriate for item requests
                        query = (r.table.type == 1)
                        rows = db(query).select(r.table.id)
                        restrict = [str(row.id) for row in rows]
                        response.s3.actions.append(
                            dict(url = URL(c = "req",
                                           f = "req",
                                           args = ["[id]", "req_item"]),
                                 _class = "action-btn",
                                 label = str(T("View Items")),
                                 restrict = restrict
                                )
                            )
                    elif r.component.name == "req_item":
                        response.s3.actions.append(req_item_inv_item_btn)
                    elif r.component.name == "req_skill":
                        pass
                    else:
                        # We don't yet have other components
                        pass

                return output
            response.s3.postp = postp

            output = s3_rest_controller("req", "req", rheader=req_rheader)

            return output

        # =====================================================================
        if deployment_settings.has_module("inv"):

            # -----------------------------------------------------------------
            # Request Items

            resourcename = "req_item"
            tablename = "req_req_item"
            quantities_writable = deployment_settings.get_req_quantities_writable()
            table = db.define_table(tablename,
                                    req_id(),
                                    item_id,
                                    supply_item_id(),
                                    item_pack_id(),
                                    Field( "quantity",
                                           "double",
                                           notnull = True,
                                           requires = IS_FLOAT_IN_RANGE(minimum=0)),
                                    Field("pack_value",
                                           "double",
                                           label = T("Value per Pack")),
                                    # @ToDo: Move this into a Currency Widget for the pack_value field
                                    currency_type("currency"),
                                    site_id,
                                    Field( "quantity_commit",
                                           "double",
                                           label = T("Quantity Committed"),
                                           represent = lambda quantity_commit: \
                                            req_quantity_represent(quantity_commit,
                                                                   "commit"),
                                           default = 0,
                                           requires = IS_FLOAT_IN_RANGE(minimum=0),
                                           writable = quantities_writable),
                                    Field( "quantity_transit",
                                           "double",
                                           label = T("Quantity in Transit"),
                                           represent = lambda quantity_transit: \
                                            req_quantity_represent(quantity_transit,
                                                                   "transit"),
                                           default = 0,
                                           requires = IS_FLOAT_IN_RANGE(minimum=0),
                                           writable = quantities_writable),
                                    Field( "quantity_fulfil",
                                           "double",
                                           label = T("Quantity Fulfilled"),
                                           represent = lambda quantity_fulfil: \
                                            req_quantity_represent(quantity_fulfil,
                                                                   "fulfil"),
                                           default = 0,
                                           requires = IS_FLOAT_IN_RANGE(minimum=0),
                                           writable = quantities_writable),
                                    s3_comments(),
                                    *s3_meta_fields())

            table.site_id.label = T("Requested From")

            if not deployment_settings.get_req_show_quantity_transit():
                table.quantity_transit.writable = table.quantity_transit.readable= False

            # pack_quantity virtual field
            table.virtualfields.append(item_pack_virtualfields(tablename = tablename))

            # CRUD strings
            ADD_REQUEST_ITEM = T("Add Item to Request")
            LIST_REQUEST_ITEM = T("List Request Items")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_REQUEST_ITEM,
                title_display = T("Request Item Details"),
                title_list = LIST_REQUEST_ITEM,
                title_update = T("Edit Request Item"),
                title_search = T("Search Request Items"),
                subtitle_create = T("Add New Request Item"),
                subtitle_list = T("Requested Items"),
                label_list_button = LIST_REQUEST_ITEM,
                label_create_button = ADD_REQUEST_ITEM,
                label_delete_button = T("Delete Request Item"),
                msg_record_created = T("Request Item added"),
                msg_record_modified = T("Request Item updated"),
                msg_record_deleted = T("Request Item deleted"),
                msg_list_empty = T("No Request Items currently registered"))

            # -----------------------------------------------------------------
            def req_item_represent (id):
                query = (db.req_req_item.id == id) & \
                        (db.req_req_item.item_id == db.supply_item.id)
                record = db(query).select( db.supply_item.name,
                                           limitby = (0, 1)).first()
                if record:
                    return record.name
                else:
                    return None

            # Reusable Field
            req_item_id = S3ReusableField( "req_item_id",
                                           db.req_req_item,
                                           requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                           "req_req_item.id",
                                                                           req_item_represent,
                                                                           orderby="req_req_item.id",
                                                                           sort=True)),
                                           represent = req_item_represent,
                                           label = T("Request Item"),
                                           comment = DIV( _class="tooltip",
                                                          _title="%s|%s" % (T("Request Item"),
                                                                            T("Select Items from the Request"))),
                                           ondelete = "CASCADE",
script =
    SCRIPT("""
    $(document).ready(function() {
        S3FilterFieldChange({
            'FilterField':    'req_item_id',
            'Field':        'item_pack_id',
            'FieldResource':'item_pack',
            'FieldPrefix':    'supply',
            'url':             S3.Ap.concat('/req/req_item_packs/'),
            'msgNoRecords':    S3.i18n.no_packs,
            'fncPrep':        fncPrepItem,
            'fncRepresent':    fncRepresentItem
        });
    });"""),
                                        )

            # On Accept to update req_req
            def req_item_onaccept(form):
                """
                    Update req_req. commit_status, transit_status, fulfil_status
                    None = quantity = 0 for ALL items
                    Partial = some items have quantity > 0
                    Complete = quantity_x = quantity(requested) for ALL items
                """
                table = db.req_req_item

                if form and form.vars.req_id:
                    req_id = form.vars.req_id
                else:
                    req_id = s3mgr.get_session("req", "req")
                if not req_id:
                    # @todo: should raise a proper HTTP status here
                    raise Exception("can not get req_id")

                is_none = dict(commit = True,
                               transit = True,
                               fulfil = True)

                is_complete = dict(commit = True,
                                   transit = True,
                                   fulfil = True)

                # Must check all items in the req
                query = (table.req_id == req_id) & \
                        (table.deleted == False )
                req_items = db(query).select(table.quantity,
                                             table.quantity_commit,
                                             table.quantity_transit,
                                             table.quantity_fulfil)

                for req_item in req_items:
                    for status_type in ["commit", "transit", "fulfil"]:
                        if req_item["quantity_%s" % status_type] < req_item.quantity:
                            is_complete[status_type] = False
                        if req_item["quantity_%s" % status_type]:
                            is_none[status_type] = False

                status_update = {}
                for status_type in ["commit", "transit", "fulfil"]:
                    if is_complete[status_type]:
                        status_update["%s_status" % status_type] = REQ_STATUS_COMPLETE
                    elif is_none[status_type]:
                        status_update["%s_status" % status_type] = REQ_STATUS_NONE
                    else:
                        status_update["%s_status" % status_type] = REQ_STATUS_PARTIAL
                #db.req_req[req_id] = status_update <- works on web2py r3204
                db(db.req_req.id == req_id).update(**status_update)

            s3mgr.configure(tablename,
                            super_entity="supply_item_entity",
                            onaccept=req_item_onaccept,
                            create_next = URL(c="req",
                                              # Shows the inventory items which match a requested item
                                              # @ToDo: Make this page a component of req_item
                                              f="req_item_inv_item",
                                              args=["[id]"]),
                            deletable = multiple_req_items,
                            list_fields = ["id",
                                           "item_id",
                                           "item_pack_id",
                                           "site_id",
                                           "quantity",
                                           "quantity_commit",
                                           "quantity_transit",
                                           "quantity_fulfil",
                                           "comments",
                                        ])

        # =====================================================================
        if deployment_settings.has_module("doc"):
            # -----------------------------------------------------------------
            # Documents Link Table
            s3mgr.load("doc_document")
            document_id = response.s3.document_id

            tablename = "req_document"
            table = db.define_table(tablename,
                                    req_id(),
                                    document_id())

            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Document"),
                title_display = T("Document Details"),
                title_list = T("List Documents"),
                title_update = T("Edit Document"),
                title_search = T("Search Documents"),
                subtitle_create = T("Add New Document"),
                subtitle_list = T("Documents"),
                label_list_button = T("List Documents"),
                label_create_button = T("Add Document"),
                # @ToDo: option to delete document (would likely be usual case)
                label_delete_button = T("Remove Document from this request"),
                msg_record_created = T("Document added"),
                msg_record_modified = T("Document updated"),
                msg_record_deleted = T("Document removed"),
                msg_list_empty = T("No Documents currently attached to this request"))

        # =====================================================================
        if deployment_settings.has_module("hrm"):

            # -----------------------------------------------------------------
            # Request Skills

            resourcename = "req_skill"
            tablename = "req_req_skill"
            quantities_writable = deployment_settings.get_req_quantities_writable()
            table = db.define_table(tablename,
                                    req_id(),
                                    Field("task",
                                          readable=False,
                                          writable=False, # Populated from req_req 'Purpose'
                                          label = T("Task Details")),
                                    multi_skill_id(label=T("Required Skills"),
                                                   comment = T("Leave blank to request an unskilled person")
                                                  ),
                                    # @ToDo: Add a minimum competency rating?
                                    Field("quantity",
                                          "integer",
                                          default = 1,
                                          label = T("Number of People Required"),
                                          notnull = True),
                                    site_id,
                                    Field("quantity_commit",
                                          "integer",
                                          label = T("Quantity Committed"),
                                          #represent = lambda quantity_commit: \
                                           #req_quantity_represent(quantity_commit,
                                           #                       "commit"),
                                          default = 0,
                                          writable = quantities_writable),
                                    Field("quantity_transit",
                                          "integer",
                                          label = T("Quantity in Transit"),
                                          #represent = lambda quantity_transit: \
                                          # req_quantity_represent(quantity_transit,
                                          #                        "transit"),
                                          default = 0,
                                          writable = quantities_writable),
                                    Field("quantity_fulfil",
                                          "integer",
                                          label = T("Quantity Fulfilled"),
                                          #represent = lambda quantity_fulfil: \
                                          #  req_quantity_represent(quantity_fulfil,
                                          #                         "fulfil"),
                                          default = 0,
                                          writable = quantities_writable),
                                    s3_comments(label = T("Task Details"),
                                             comment = DIV(_class="tooltip",
                                                           _title="%s|%s" % (T("Task Details"),
                                                                             T("Include any special requirements such as equipment which they need to bring.")))),
                                    *s3_meta_fields())

            table.site_id.label = T("Requested From")

            if not deployment_settings.get_req_show_quantity_transit():
                table.quantity_transit.writable = table.quantity_transit.readable= False

            # CRUD strings
            ADD_REQUEST_SKILL = T("Add Skill to Request")
            LIST_REQUEST_SKILL = T("List Requested Skills")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_REQUEST_SKILL,
                title_display = T("Requested Skill Details"),
                title_list = LIST_REQUEST_SKILL,
                title_update = T("Edit Requested Skill"),
                title_search = T("Search Requested Skills"),
                subtitle_create = T("Request New People"),
                subtitle_list = T("Requested Skills"),
                label_list_button = LIST_REQUEST_SKILL,
                label_create_button = ADD_REQUEST_SKILL,
                label_delete_button = T("Remove Skill from Request"),
                msg_record_created = T("Skill added to Request"),
                msg_record_modified = T("Requested Skill updated"),
                msg_record_deleted = T("Skill removed from Request"),
                msg_list_empty = T("No Skills currently requested"))

            # -----------------------------------------------------------------
            def req_skill_represent (id):
                rstable = db.req_req_skill
                hstable = db.hrm_skill
                query = (rstable.id == id) & \
                        (rstable.skill_id == hstable.id)
                record = db(query).select(hstable.name,
                                          limitby = (0, 1)).first()
                if record:
                    return record.name
                else:
                    return None

            task_id = s3db.project_task_id
            tablename = "project_task_req"
            table = db.define_table(tablename,
                                    task_id(),
                                    req_id(),
                                    *s3_meta_fields())

            # On Accept to update req_req
            def req_skill_onaccept(form):
                """
                    Update req_req. commit_status, transit_status, fulfil_status
                    None = quantity = 0 for ALL skills
                    Partial = some skills have quantity > 0
                    Complete = quantity_x = quantity(requested) for ALL skills

                    Create a Task for People to be assigned to
                """

                if form and form.vars.req_id:
                    req_id = form.vars.req_id
                else:
                    req_id = s3mgr.get_session("req", "req")
                if not req_id:
                    # @ToDo: should raise a proper HTTP status here
                    raise Exception("can not get req_id")

                table = db.req_req
                query = (table.id == req_id)
                record = db(query).select(table.purpose,
                                          limitby=(0, 1)).first()

                table = db.req_req_skill
                query = (table.req_id == req_id)
                if record:
                    # Copy the Task description to the Skills component
                    db(query).update(task=record.purpose)

                is_none = dict(commit = True,
                               transit = True,
                               fulfil = True)

                is_complete = dict(commit = True,
                                   transit = True,
                                   fulfil = True)

                # Must check all skills in the req
                req_skills = db(query).select(table.quantity,
                                              table.quantity_commit,
                                              table.quantity_transit,
                                              table.quantity_fulfil)

                for req_skill in req_skills:
                    for status_type in ["commit", "transit", "fulfil"]:
                        if req_skill["quantity_%s" % status_type] < req_skill.quantity:
                            is_complete[status_type] = False
                        if req_skill["quantity_%s" % status_type]:
                            is_none[status_type] = False

                status_update = {}
                for status_type in ["commit", "transit", "fulfil"]:
                    if is_complete[status_type]:
                        status_update["%s_status" % status_type] = REQ_STATUS_COMPLETE
                    elif is_none[status_type]:
                        status_update["%s_status" % status_type] = REQ_STATUS_NONE
                    else:
                        status_update["%s_status" % status_type] = REQ_STATUS_PARTIAL
                table = db.req_req
                query = (table.id == req_id)
                db(query).update(**status_update)

                if deployment_settings.has_module("project"):
                    # Add a Task to which the People can be assigned

                    # Get the request record
                    record = db(query).select(table.request_number,
                                              table.purpose,
                                              table.priority,
                                              table.requester_id,
                                              table.site_id,
                                              limitby=(0, 1)).first()
                    if not record:
                        return
                    table = db.org_site
                    query = (table.id == record.site_id)
                    site = db(query).select(table.location_id,
                                            table.organisation_id,
                                            limitby=(0, 1)).first()
                    if site:
                        location = site.location_id
                        organisation = site.organisation_id
                    else:
                        location = None
                        organisation = None

                    s3mgr.load("project_task")
                    table = db.project_task
                    task = table.insert(name=record.request_number,
                                        description=record.purpose,
                                        priority=record.priority,
                                        location_id=location,
                                        site_id=record.site_id)
                    # Add the Request as a Component to the Task
                    table = db.project_task_req
                    table.insert(task_id = task,
                                 req_id = req_id)

            s3mgr.configure("req_req_skill",
                            onaccept=req_skill_onaccept,
                            # @ToDo: Produce a custom controller like req_item_inv_item?
                            #create_next = URL(c="req", f="req_skill_skill",
                            #                  args=["[id]"]),
                            deletable = multiple_req_items,
                            list_fields = ["id",
                                           "task",
                                           "skill_id",
                                           "quantity",
                                           "quantity_commit",
                                           "quantity_transit",
                                           "quantity_fulfil",
                                           "comments",
                                        ])
            # ---------------------------------------------------------------------
            def req_skill_controller():
                """
                    Request Controller
                """

                tablename = "req_req_skill"
                table = db[tablename]

                s3mgr.configure(tablename,
                                insertable=False)

                def prep(r):
                    if r.interactive:
                        if r.method != "update" and r.method != "read":
                            # Hide fields which don't make sense in a Create form
                            # - includes one embedded in list_create
                            # - list_fields over-rides, so still visible within list itself
                            response.s3.req_hide_quantities(r.table)

                    return True
                response.s3.prep = prep

                # Post-process
                def postp(r, output):
                    if r.interactive:
                        response.s3.actions = [
                            dict(url = URL(c = "req",
                                           f = "req",
                                           args = ["req_skill", "[id]"]),
                                 _class = "action-btn",
                                 label = str(READ)
                                )
                            ]

                    return output
                response.s3.postp = postp

                output = s3_rest_controller("req", "req_skill")

                return output

        # =====================================================================
        # Commitments (Pledges)
        resourcename = "commit"
        tablename = "req_commit"
        table = db.define_table(tablename,
                                super_link("site_id", "org_site",
                                           label = T("From Facility"),
                                           default = auth.user.site_id if auth.is_logged_in() else None,
                                           # Non-Item Requests make False in the prep
                                           writable = True,
                                           readable = True,
                                           # Comment these to use a Dropdown & not an Autocomplete
                                           #widget = S3SiteAutocompleteWidget(),
                                           #comment = DIV(_class="tooltip",
                                           #              _title="%s|%s" % (T("From Facility"),
                                           #                                T("Enter some characters to bring up a list of possible matches"))),
                                           represent = org_site_represent),
                                # Non-Item Requests make True in the prep
                                organisation_id(readable = False,
                                                writable = False),
                                req_id(),
                                Field("type",
                                      "integer",
                                      # These are copied automatically from the Req
                                      readable=False,
                                      writable=False),
                                Field("date",
                                      "date",
                                      requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                      widget = S3DateWidget(),
                                      default = request.utcnow,
                                      label = T("Date"),
                                      represent = s3_date_represent),
                                Field("date_available",
                                      "date",
                                      requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                      widget = S3DateWidget(),
                                      label = T("Date Available"),
                                      represent = s3_date_represent),
                                person_id("committer_id",
                                          default = s3_logged_in_person(),
                                          label = T("Committed By") ),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_COMMIT = T("Make Commitment")
        LIST_COMMIT = T("List Commitments")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_COMMIT,
            title_display = T("Commitment Details"),
            title_list = LIST_COMMIT,
            title_update = T("Edit Commitment"),
            title_search = T("Search Commitments"),
            subtitle_create = ADD_COMMIT,
            subtitle_list = T("Commitments"),
            label_list_button = LIST_COMMIT,
            label_create_button = ADD_COMMIT,
            label_delete_button = T("Delete Commitment"),
            msg_record_created = T("Commitment Added"),
            msg_record_modified = T("Commitment Updated"),
            msg_record_deleted = T("Commitment Canceled"),
            msg_list_empty = T("No Commitments"))

        # ---------------------------------------------------------------------
        def commit_represent(id):
            if id:
                table = db.req_commit
                r = db(table.id == id).select(table.type,
                                              table.date,
                                              table.organisation_id,
                                              table.site_id,
                                              limitby=(0, 1)).first()
                if r.type == 1: # Items
                    return "%s - %s" % (org_site_represent(r.site_id),
                                        r.date)
                else:
                    return "%s - %s" % (organisation_represent(r.organisation_id),
                                        r.date)
            else:
                return NONE

        # ---------------------------------------------------------------------
        # Reusable Field
        commit_id = S3ReusableField("commit_id", db.req_commit, sortby="date",
                                    requires = IS_NULL_OR( \
                                                    IS_ONE_OF(db,
                                                              "req_commit.id",
                                                              commit_represent,
                                                              orderby="req_commit.date",
                                                              sort=True)),
                                    represent = commit_represent,
                                    label = T("Commitment"),
                                    ondelete = "CASCADE")

        # -----------------------------------------------------------------
        def commit_onvalidation(form):
            # Copy the request_type to the commitment
            req_id = s3mgr.get_session("req", "req")
            if req_id:
                rtable = db.req_req
                query = (rtable.id == req_id)
                req_record = db(query).select(rtable.type,
                                              limitby=(0, 1)).first()
                if req_record:
                    form.vars.type = req_record.type

        # -----------------------------------------------------------------
        def commit_onaccept(form):
            table = db.req_commit

            # Update owned_by_role to the organisation's owned_by_role
            # @ToDo: Facility
            if form.vars.organisation_id:
                otable = db.org_organisation
                query = (otable.id == form.vars.organisation_id)
                org = db(query).select(otable.owned_by_organisation,
                                       limitby=(0, 1)).first()
                if org:
                    query = (table.id == form.vars.id)
                    db(query).update(owned_by_organisation=org.owned_by_organisation)

            rtable = db.req_req
            if form.vars.type == 3: # People
                # If no organisation_id, then this is a single person commitment, so create the commit_person record automatically
                table = db.req_commit_person
                table.insert(commit_id = form.vars.id,
                             #skill_id = ???,
                             person_id = auth.s3_logged_in_person())
                # @ToDo: Mark Person's allocation status as 'Committed'
            elif form.vars.type == 9:
                # Non-Item requests should have commitment status updated if a commitment is made
                query = (table.id == form.vars.id) & \
                        (rtable.id == table.req_id)
                req_record = db(query).select(rtable.id,
                                              rtable.commit_status,
                                              limitby=(0, 1)).first()
                if req_record and req_record.commit_status == REQ_STATUS_NONE:
                    # Assume Partial not Complete
                    # @ToDo: Provide a way for the committer to specify this
                    query = (rtable.id == req_record.id)
                    db(query).update(commit_status=REQ_STATUS_PARTIAL)

        # ---------------------------------------------------------------------
        s3mgr.configure(tablename,
                        # Commitments should only be made to a specific request
                        listadd = False,
                        onvalidation = commit_onvalidation,
                        onaccept = commit_onaccept)

        # =====================================================================
        if deployment_settings.has_module("inv"):

            # -----------------------------------------------------------------
            # Commitment Items
            # @ToDo: Update the req_item_id in the commit_item if the req_id of the commit is changed

            resourcename = "commit_item"
            tablename = "req_commit_item"
            table = db.define_table(tablename,
                                    commit_id(),
                                    #item_id,
                                    #supply_item_id(),
                                    req_item_id(),
                                    item_pack_id(),
                                    Field("quantity",
                                          "double",
                                          notnull = True),
                                    s3_comments(),
                                    *s3_meta_fields())

            # pack_quantity virtual field
            table.virtualfields.append(item_pack_virtualfields(tablename = tablename))

            # CRUD strings
            ADD_COMMIT_ITEM = T("Add Item to Commitment")
            LIST_COMMIT_ITEM = T("List Commitment Items")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_COMMIT_ITEM,
                title_display = T("Commitment Item Details"),
                title_list = LIST_COMMIT_ITEM,
                title_update = T("Edit Commitment Item"),
                title_search = T("Search Commitment Items"),
                subtitle_create = T("Add New Commitment Item"),
                subtitle_list = T("Commitment Items"),
                label_list_button = LIST_COMMIT_ITEM,
                label_create_button = ADD_COMMIT_ITEM,
                label_delete_button = T("Delete Commitment Item"),
                msg_record_created = T("Commitment Item added"),
                msg_record_modified = T("Commitment Item updated"),
                msg_record_deleted = T("Commitment Item deleted"),
                msg_list_empty = T("No Commitment Items currently registered"))

            # -----------------------------------------------------------------
            def commit_item_onaccept(form):
                table = db.req_commit_item

                # Try to get req_item_id from the form
                req_item_id = 0
                if form:
                    req_item_id = form.vars.get("req_item_id")
                if not req_item_id:
                    commit_item_id = s3mgr.get_session("req", "commit_item")
                    r_commit_item = table[commit_item_id]

                    req_item_id = r_commit_item.req_item_id

                query = (table.req_item_id == req_item_id) & \
                        (table.deleted == False)
                commit_items = db(query).select(table.quantity ,
                                                table.item_pack_id)
                quantity_commit = 0
                for commit_item in commit_items:
                    quantity_commit += commit_item.quantity * commit_item.pack_quantity

                r_req_item = db.req_req_item[req_item_id]
                quantity_commit = quantity_commit / r_req_item.pack_quantity
                db.req_req_item[req_item_id] = dict(quantity_commit = quantity_commit)

                # Update status_commit of the req record
                s3mgr.store_session("req", "req_item", r_req_item.id)
                req_item_onaccept(None)


            s3mgr.configure(tablename,
                            onaccept = commit_item_onaccept )

        # =====================================================================
        if deployment_settings.has_module("hrm"):

            # -----------------------------------------------------------------
            # Committed Persons

            resourcename = "commit_person"
            tablename = "req_commit_person"
            table = db.define_table(tablename,
                                    commit_id(),
                                    # For reference
                                    multi_skill_id(writable=False, comment=None),
                                    # This should be person as we want to mark them as allocated
                                    person_id(),
                                    s3_comments(),
                                    *s3_meta_fields())

            # CRUD strings
            ADD_COMMIT_PERSON = T("Add Person to Commitment")
            LIST_COMMIT_PERSON = T("List Committed People")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_COMMIT_PERSON,
                title_display = T("Committed Person Details"),
                title_list = LIST_COMMIT_PERSON,
                title_update = T("Edit Committed Person"),
                title_search = T("Search Committed People"),
                subtitle_create = T("Add New Person to Commitment"),
                subtitle_list = T("Committed People"),
                label_list_button = LIST_COMMIT_PERSON,
                label_create_button = ADD_COMMIT_PERSON,
                label_delete_button = T("Remove Person from Commitment"),
                msg_record_created = T("Person added to Commitment"),
                msg_record_modified = T("Committed Person updated"),
                msg_record_deleted = T("Person removed from Commitment"),
                msg_list_empty = T("No People currently committed"))

           # -----------------------------------------------------------------
            def commit_person_onaccept(form):
                table = db.req_commit_person

                # Try to get req_skill_id from the form
                req_skill_id = 0
                if form:
                    req_skill_id = form.vars.get("req_skill_id")
                if not req_skill_id:
                    commit_skill_id = s3mgr.get_session("req", "commit_skill")
                    r_commit_skill = table[commit_skill_id]
                    req_skill_id = r_commit_skill.req_skill_id

                query = (table.req_skill_id == req_skill_id) & \
                        (table.deleted == False)
                commit_skills = db(query).select(table.quantity)
                quantity_commit = 0
                for commit_skill in commit_skills:
                    quantity_commit += commit_skill.quantity

                r_req_skill = db.req_req_skill[req_skill_id]
                db.req_req_skill[req_skill_id] = dict(quantity_commit = quantity_commit)

                # Update status_commit of the req record
                s3mgr.store_session("req", "req_skill", r_req_skill.id)
                req_skill_onaccept(None)


            # @ToDo: Fix this before enabling
            #s3mgr.configure(tablename,
            #                onaccept = commit_person_onaccept )

        # =====================================================================
        def req_tabs(r):
            """
                Add a set of Tabs for a Site's Request Tasks

                @ToDo: Roll these up like inv_tabs in 08_inv.py
            """
            if deployment_settings.has_module("req") and \
                auth.s3_has_permission("read", db.req_req):
                return [
                        (T("Requests"), "req"),
                        (T("Match Requests"), "req_match/"),
                        (T("Commit"), "commit")
                        ]
            else:
                return []

        # Pass variables back to global scope (response.s3.*)
        return_dict = dict(
            req_id = req_id,
            req_item_id = req_item_id,
            req_item_onaccept = req_item_onaccept,
            req_represent = req_represent,
            req_item_represent = req_item_represent,
            req_create_form_mods = req_create_form_mods,
            req_helptext_script = req_helptext_script,
            req_tabs = req_tabs,
            req_match = req_match,
            req_priority_represent = req_priority_represent,
            req_hide_quantities = req_hide_quantities,
            req_controller = req_controller,
            req_skill_controller = req_skill_controller
            )

        if deployment_settings.get_req_use_commit():
            return_dict["commit_item_onaccept"] = commit_item_onaccept

        return return_dict

    # Provide a handle to this load function
    s3mgr.loader(req_tables,
                 "req_req",
                 "req_req_item",
                 "req_req_skill",
                 "req_commit",
                 "req_commit_item",
                 "req_commit_person",
                 "project_task_req")

    def req_req_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - If the Request Number exists then it's a duplicate
        """
        # ignore this processing if the id is set or there is no data
        if job.id or job.data == None:
            return
        if job.tablename == "req_req":
            table = job.table
            if "request_number" in job.data:
                request_number = job.data.request_number
            else:
                return

            query = (table.request_number == request_number)
            _duplicate = db(query).select(table.id,
                                          limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    s3mgr.configure("req_req", deduplicate=req_req_duplicate)

    def req_item_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - If the Request Number matches
           - The item is the same
        """
        # ignore this processing if the id is set or there is no data
        if job.id or job.data == None:
            return
        if job.tablename == "req_req_item":
            itable = job.table
            rtable = db.req_req
            stable = db.supply_item
            req_id = None
            item_id = None
            for ref in job.references:
                if ref.entry.tablename == "req_req":
                    if ref.entry.id != None:
                        req_id = ref.entry.id
                    else:
                        uuid = ref.entry.item_id
                        jobitem = job.job.items[uuid]
                        req_id = jobitem.id
                elif ref.entry.tablename == "supply_item":
                    if ref.entry.id != None:
                        item_id = ref.entry.id
                    else:
                        uuid = ref.entry.item_id
                        jobitem = job.job.items[uuid]
                        item_id = jobitem.id

            if req_id != None and item_id != None:
                query = (itable.req_id == req_id) & \
                        (itable.item_id == item_id)
            else:
                return

            _duplicate = db(query).select(itable.id,
                                          limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    s3mgr.configure("req_req_item", deduplicate=req_item_duplicate)

else:
    def req_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("req_id", "integer", readable=False, writable=False)
    response.s3.req_id = req_id
    def req_item_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("req_item_id", "integer", readable=False, writable=False)
    response.s3.req_item_id = req_item_id

# END =========================================================================