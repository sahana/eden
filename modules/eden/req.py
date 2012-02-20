# -*- coding: utf-8 -*-

""" Sahana Eden Request Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3RequestModel",
           "S3RequestItemModel",
           "S3RequestSkillModel",
           "S3CommitModel",
           "S3CommitItemModel",
           "S3CommitPersonModel",
           "req_item_onaccept",
           "req_rheader",
           ]

import datetime

from gluon import *
from gluon.storage import Storage
from ..s3 import *

REQ_STATUS_NONE       = 0
REQ_STATUS_PARTIAL    = 1
REQ_STATUS_COMPLETE   = 2

T = current.T
req_status_opts = { REQ_STATUS_NONE:     SPAN(T("None"),
                                              _class = "req_status_none"),
                    REQ_STATUS_PARTIAL:  SPAN(T("Partial"),
                                              _class = "req_status_partial"),
                    REQ_STATUS_COMPLETE: SPAN(T("Complete"),
                                              _class = "req_status_complete")
                   }

# =============================================================================
class S3RequestModel(S3Model):
    """
    """

    names = ["req_req",
             "req_req_id",
             "req_hide_quantities",
             "req_create_form_mods",
            ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        request = current.request
        session = current.session
        s3 = current.response.s3
        settings = current.deployment_settings

        org_site_represent = self.org_site_represent
        human_resource_id = self.hrm_human_resource_id
        event_id = self.event_event_id

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        #s3_date_format = settings.get_L10n_date_format()
        #s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)
        s3_datetime_represent = lambda dt: S3DateTime.datetime_represent(dt, utc=True)

        # Multiple Item/Skill Types per Request?
        multiple_req_items = settings.get_req_multiple_req_items()

        req_status = S3ReusableField("req_status", "integer",
                                     label = T("Request Status"),
                                     requires = IS_NULL_OR(IS_IN_SET(req_status_opts,
                                                                     zero = None)),
                                     represent = lambda opt: \
                                        req_status_opts.get(opt, UNKNOWN_OPT),
                                     default = REQ_STATUS_NONE,
                                     writable = settings.get_req_status_writable(),
                                    )

        req_priority_opts = {
            3:T("High"),
            2:T("Medium"),
            1:T("Low")
        }

        req_types_deployed = settings.get_req_req_type()
        if "Other" in req_types_deployed:
            req_type_opts = {9:T("Other")}
        else:
            req_type_opts = {}

        if settings.has_module("inv") and "Stock" in req_types_deployed:
            # Number hardcoded in controller
            req_type_opts[1] = settings.get_req_type_inv_label()
        #if settings.has_module("asset"):
        #    req_type_opts[2] = T("Assets")
        if settings.has_module("hrm") and "People" in req_types_deployed:
            req_type_opts[3] = settings.get_req_type_hrm_label()
        #if settings.has_module("cr"):
        #    req_type_opts[4] = T("Shelter")

        # ---------------------------------------------------------------------
        # Requests
        tablename = "req_req"
        table = self.define_table(tablename,
                                  self.super_link("doc_id", "doc_entity"),
                                  event_id(default=session.s3.event,
                                           readable = False,
                                           writable = False,
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
                                        represent = s3_datetime_represent),
                                  Field("priority",
                                        "integer",
                                        default = 2,
                                        label = T("Priority"),
                                        represent = self.req_priority_represent,
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
                                        represent = s3_datetime_represent),
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
                                        represent = s3_datetime_represent,
                                        readable = False,
                                        writable = False
                                        ),
                                  human_resource_id("requester_id",
                                                    label = T("Requester"),
                                                    empty = False,
                                                    default = auth.s3_logged_in_human_resource()),
                                  human_resource_id("assigned_to_id", # This field should be in req_commit, but that complicates the UI
                                                    readable = False,
                                                    writable = False,
                                                    label = T("Assigned To")),
                                  human_resource_id("approved_by_id",
                                                    label = T("Approved By")),
                                  human_resource_id("request_for_id",
                                                    label = T("Requested For"),
                                                    #default = auth.s3_logged_in_human_resource()
                                                    ),
                                  self.super_link("site_id", "org_site",
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
                                        represent = s3_datetime_represent,
                                        readable = False,
                                        writable = False
                                        ),
                                  human_resource_id("recv_by_id",
                                                    label = T("Received By"),
                                                    # @ToDo: Set this in Update forms? Dedicated 'Receive' button?
                                                    # (Definitely not in Create forms)
                                                    #default = auth.s3_logged_in_human_resource()
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
                                  s3.comments(comment=""),
                                  *s3.meta_fields())

        if settings.has_module("inv"):
            table.type.default = 1
        #elif settings.has_module("asset"):
        #    table.type.default = 2
        elif settings.has_module("hrm"):
            table.type.default = 3
        #elif settings.has_module("cr"):
        #    table.type.default = 4

        if not settings.get_req_use_req_number():
            table.request_number.readable = False
            table.request_number.writable = False

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

        # Reusable Field
        req_id = S3ReusableField("req_id", db.req_req, sortby="date",
                                 requires = IS_ONE_OF(db,
                                                      "req_req.id",
                                                      lambda id:
                                                        self.req_represent(id,
                                                                      False),
                                                      orderby="req_req.date",
                                                      sort=True),
                                 represent = self.req_represent,
                                 label = T("Request"),
                                 ondelete = "CASCADE")
        list_fields = ["id",
                       "type",
                       "event_id",]

        if settings.get_req_use_req_number():
            list_fields.append("request_number")
        list_fields.append("priority")
        list_fields.append("commit_status")
        list_fields.append("transit_status")
        list_fields.append("fulfil_status")
        list_fields.append("date_required")
        self.configure(tablename,
                       onaccept = self.req_onaccept,
                       deduplicate = self.req_req_duplicate,
                       list_fields = list_fields
                      )

        # Script to inject into Pages which include Request create forms
        req_help_msg = ""
        req_help_msg_template = T("If the request is for %s, please enter the details on the next screen.")
        types = []
        if settings.has_module("inv"):
            types.append(T("Warehouse Stock"))
        #if settings.has_module("asset"):
        #    types.append(T("Assets"))
        if settings.has_module("hrm"):
            types.append(T("Staff"))
        #if settings.has_module("cr"):
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

        # Custom Methos
        self.set_method(tablename,
                        method = "check",
                        action=self.req_check)

        # Components
        # Documents as a component of Requests
        self.add_component("req_document",
                           req_req="req_id")

        # Request Items as component of Requests
        self.add_component("req_req_item",
                           req_req=dict(joinby="req_id",
                                        multiple=multiple_req_items))

        # Request Skills as component of Requests
        self.add_component("req_req_skill",
                           req_req=dict(joinby="req_id",
                                        multiple=multiple_req_items))

        # Commitment as a component of Requests
        self.add_component("req_commit",
                           req_req="req_id")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                req_req_id = req_id,
                req_create_form_mods = self.req_create_form_mods,
                req_helptext_script = req_helptext_script,
                req_tabs = self.req_tabs,
                req_priority_represent = self.req_priority_represent,
                req_hide_quantities = self.req_hide_quantities,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def req_create_form_mods():
        """
            Function to be called from REST prep functions
             - main module & components (sites & events)
        """

        s3db = current.s3db

        # Hide fields which don't make sense in a Create form
        table = s3db.req_req
        table.commit_status.readable = table.commit_status.writable = False
        table.transit_status.readable = table.transit_status.writable = False
        table.fulfil_status.readable = table.fulfil_status.writable = False
        table.cancel.readable = table.cancel.writable = False

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def req_represent(id, link = True):
        """
        """

        db = current.db
        s3db = current.s3db
        NONE = current.messages.NONE

        id = int(id)
        if id:
            table = s3db.req_req
            query = (table.id == id)
            req = db(query).select(table.date,
                                   #table.type,
                                   table.site_id,
                                   limitby=(0, 1)).first()
            if not req:
                return NONE
            req = "%s - %s" % (table.site_id.represent(req.site_id,
                                                       link = False),
                               table.date.represent(req.date))
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

    # -------------------------------------------------------------------------
    @staticmethod
    def req_priority_represent(id):
        """
        """

        src = URL(c="static", f="img",
                  args=["priority", "priority_%d.gif" % (id or 4)]
                )
        return DIV(IMG(_src= src))

    # -------------------------------------------------------------------------
    @staticmethod
    def req_hide_quantities(table):
        """
            Hide the Update Quantity Status Fields from Request create forms
        """

        settings = current.deployment_settings

        if not settings.get_req_quantities_writable():
            table.quantity_commit.writable = table.quantity_commit.readable = False
            table.quantity_transit.writable = table.quantity_transit.readable= False
            table.quantity_fulfil.writable = table.quantity_fulfil.readable = False

    # -------------------------------------------------------------------------
    @staticmethod
    def req_tabs(r):
        """
            Add a set of Tabs for a Site's Request Tasks

            @ToDo: Roll these up like inv_tabs in inv.py
        """

        if current.deployment_settings.has_module("req") and \
            current.auth.s3_has_permission("read", "req_req"):
            return [
                    (T("Requests"), "req"),
                    (T("Match Requests"), "match/"),
                    (T("Commit"), "commit")
                    ]
        else:
            return []

    # -------------------------------------------------------------------------
    @staticmethod
    def req_check(r, **attr):
        """
            Check to see if your Inventory can be used to match any open Requests
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        response = current.response
        s3 = response.s3

        NONE = current.messages.NONE

        site_id = r.vars.site_id
        site_name = s3db.org_site_represent(site_id, link = False)

        output = {}
        output["title"] = T("Check Request")
        output["rheader"] = req_rheader(r, check_page = True)

        stable = s3db.org_site
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
            distance = current.gis.greatCircleDistance(location_r.lat,
                                                       location_r.lon,
                                                       req_location_r.lat,
                                                       req_location_r.lon,)
            output["rheader"][0].append(TR(TH( T("Distance from %s:") % site_name),
                                           TD( T("%.1f km") % distance)
                                           ))
        except:
            pass

        output["subtitle"] = T("Request Items")

        # Get req_items & inv_items from this site
        table = s3db.req_req_item
        query = (table.req_id == r.id ) & \
                (table.deleted == False )
        req_items = db(query).select(table.id,
                                     table.item_id,
                                     table.quantity,
                                     table.item_pack_id,
                                     table.quantity_commit,
                                     table.quantity_transit,
                                     table.quantity_fulfil)
        itable = s3db.inv_inv_item
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
                                   TH(T("Quantity in %s's Warehouse") % site_name),
                                   TH(T("Match?"))
                                  )
                                ),
                          _id = "list",
                          _class = "dataTable display")

            supply_item_represent = table.item_id.represent
            item_pack_represent = table.item_pack_id.represent
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
                                 supply_item_represent(req_item.item_id),
                                 req_item.quantity,
                                 item_pack_represent(req_item.item_pack_id),
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
                #s3.actions = [req_item_inv_item_btn]
                s3.no_sspag = True # pag won't work
        else:
            output["items"] = s3.crud_strings.req_req_item.msg_list_empty

        response.view = "list.html"
        s3.no_formats = True

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def req_onaccept(form):
        """
        """

        s3db = current.s3db
        request = current.request
        settings = current.deployment_settings

        # Configure the next page to go to based on the request type
        tablename = "req_req"
        if "default_type" in request.get_vars:
            type = request.get_vars.default_type
        else:
            type = form.vars.type

        if type == "1" and settings.has_module("inv"):
            s3db.configure(tablename,
                           create_next = URL(c="req",
                                             f="req",
                                             args=["[id]", "req_item"]),
                           update_next = URL(c="req",
                                             f="req",
                                             args=["[id]", "req_item"]))
        elif type == "2" and settings.has_module("asset"):
            s3db.configure(tablename,
                           create_next = URL(c="req",
                                             f="req",
                                             args=["[id]", "req_asset"]),
                           update_next = URL(c="req",
                                             f="req",
                                             args=["[id]", "req_asset"]))
        elif type == "3" and settings.has_module("hrm"):
            s3db.configure(tablename,
                           create_next = URL(c="req",
                                             f="req",
                                             args=["[id]", "req_skill"]),
                           update_next = URL(c="req",
                                             f="req",
                                             args=["[id]", "req_skill"]))
        #elif type == "4" and settings.has_module("cr"):
        #    s3db.configure(tablename,
        #                   create_next = URL(c="req",
        #                                     f="req",
        #                                     args=["[id]", "req_shelter"]),
        #                   update_next = URL(c="req",
        #                                     f="req",
        #                                     args=["[id]", "req_shelter"]))

    # -------------------------------------------------------------------------
    @staticmethod
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

        db = current.db

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


# =============================================================================
class S3RequestItemModel(S3Model):
    """
    """

    names = ["req_req_item",
             "req_item_id",
             "req_item_represent",
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        currency_type = s3.currency_type
        site_id = self.org_site_id
        item_id = self.supply_item_entity_id
        supply_item_id = self.supply_item_id
        item_pack_id = self.supply_item_pack_id
        item_pack_virtualfields = self.supply_item_pack_virtualfields
        req_id = self.req_req_id

        settings = current.deployment_settings

        quantities_writable = settings.get_req_quantities_writable()

        req_quantity_represent = self.req_quantity_represent

        # -----------------------------------------------------------------
        # Request Items
        #
        tablename = "req_req_item"
        table = self.define_table(tablename,
                                  req_id(),
                                  item_id,
                                  supply_item_id(),
                                  item_pack_id(),
                                  Field("quantity",
                                        "double",
                                        notnull = True,
                                        requires = IS_FLOAT_IN_RANGE(minimum=0)),
                                  Field("pack_value",
                                        "double",
                                        label = T("Est. Value per Pack")),
                                  # @ToDo: Move this into a Currency Widget for the pack_value field
                                  currency_type("currency"),
                                  site_id,
                                  Field("quantity_commit",
                                        "double",
                                        label = T("Quantity Committed"),
                                        represent = lambda quantity_commit: \
                                            req_quantity_represent(quantity_commit,
                                                                   "commit"),
                                        default = 0,
                                        requires = IS_FLOAT_IN_RANGE(minimum=0),
                                        writable = quantities_writable),
                                  Field("quantity_transit",
                                        "double",
                                        label = T("Quantity in Transit"),
                                        represent = lambda quantity_transit: \
                                            req_quantity_represent(quantity_transit,
                                                                   "transit"),
                                        default = 0,
                                        requires = IS_FLOAT_IN_RANGE(minimum=0),
                                        writable = quantities_writable),
                                  Field("quantity_fulfil",
                                        "double",
                                        label = T("Quantity Fulfilled"),
                                        represent = lambda quantity_fulfil: \
                                            req_quantity_represent(quantity_fulfil,
                                                                   "fulfil"),
                                        default = 0,
                                        requires = IS_FLOAT_IN_RANGE(minimum=0),
                                        writable = quantities_writable),
                                  s3.comments(),
                                  *s3.meta_fields())

        table.site_id.label = T("Requested From")

        if not settings.get_req_show_quantity_transit():
            table.quantity_transit.writable = table.quantity_transit.readable= False

        # pack_quantity virtual field
        table.virtualfields.append(item_pack_virtualfields(tablename=tablename))

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

        # Reusable Field
        req_item_id = S3ReusableField("req_item_id",
                                      db.req_req_item,
                                      requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                      "req_req_item.id",
                                                                      self.req_item_represent,
                                                                      orderby="req_req_item.id",
                                                                      sort=True)),
                                      represent = self.req_item_represent,
                                      label = T("Request Item"),
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Request Item"),
                                                                      T("Select Items from the Request"))),
                                      ondelete = "CASCADE",
                                      script = SCRIPT("""
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


        self.configure(tablename,
                       super_entity="supply_item_entity",
                       onaccept=req_item_onaccept,
                       create_next = URL(c="req",
                                         # Shows the inventory items which match a requested item
                                         # @ToDo: Make this page a component of req_item
                                         f="req_item_inv_item",
                                         args=["[id]"]),
                       deletable = settings.get_req_multiple_req_items(),
                       deduplicate=self.req_item_duplicate,
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

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                req_item_id = req_item_id,
                req_item_represent = self.req_item_represent,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def req_item_represent(id):
        """
        """

        db = current.db
        s3db = current.s3db

        ritable = s3db.req_req_item
        sitable = s3db.supply_item

        query = (ritable.id == id) & \
                (ritable.item_id == sitable.id)
        record = db(query).select(sitable.name,
                                  limitby = (0, 1)).first()
        if record:
            return record.name
        else:
            return None

    # ---------------------------------------------------------------------
    @staticmethod
    def req_quantity_represent(quantity, type):
        """
            @ToDo: There should be better control of this feature - currently this only works
                   with req_items which are being matched by commit / send / recv
        """

        settings = current.deployment_settings

        if quantity and not settings.get_req_quantities_writable():
            return TAG[""]( quantity,
                            A(DIV(_class = "quantity %s ajax_more collapsed" % type
                                  ),
                                _href = "#",
                              )
                            )
        else:
            return quantity

    # -------------------------------------------------------------------------
    @staticmethod
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

        db = current.db
        s3db = current.s3db

        # ignore this processing if the id is set or there is no data
        if job.id or job.data == None:
            return
        if job.tablename == "req_req_item":
            itable = job.table
            rtable = s3db.req_req
            stable = s3db.supply_item
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


# =============================================================================
class S3RequestSkillModel(S3Model):
    """
    """

    names = ["req_req_skill",
             #"project_task_req"
            ]

    def model(self):

        T = current.T
        s3 = current.response.s3
        settings = current.deployment_settings

        site_id = self.org_site_id
        multi_skill_id = self.hrm_multi_skill_id
        task_id = self.project_task_id
        req_id = self.req_req_id

        quantities_writable = settings.get_req_quantities_writable()

        # -----------------------------------------------------------------
        # Request Skills
        #
        tablename = "req_req_skill"
        table = self.define_table(tablename,
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
                                  s3.comments(label = T("Task Details"),
                                              comment = DIV(_class="tooltip",
                                                            _title="%s|%s" % (T("Task Details"),
                                                                             T("Include any special requirements such as equipment which they need to bring.")))),
                                  *s3.meta_fields())

        table.site_id.label = T("Requested From")

        if not settings.get_req_show_quantity_transit():
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
        # Link Skill Requests to Tasks
        # @ToDo: Break this into a separate model activated based on a
        #        deployment_setting
        #
        tablename = "project_task_req"
        table = self.define_table(tablename,
                                  task_id(),
                                  req_id(),
                                  *s3.meta_fields())

        self.configure("req_req_skill",
                       onaccept=req_skill_onaccept,
                       # @ToDo: Produce a custom controller like req_item_inv_item?
                       #create_next = URL(c="req", f="req_skill_skill",
                       #                  args=["[id]"]),
                       deletable = settings.get_req_multiple_req_items(),
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
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

    # -----------------------------------------------------------------
    @staticmethod
    def req_skill_represent (id):
        """
        """

        db = current.db
        s3db = current.s3db

        rstable = s3db.req_req_skill
        hstable = s3db.hrm_skill
        query = (rstable.id == id) & \
                (rstable.skill_id == hstable.id)
        record = db(query).select(hstable.name,
                                  limitby = (0, 1)).first()
        if record:
            return record.name
        else:
            return None

# =============================================================================
class S3CommitModel(S3Model):
    """
    """

    names = ["req_commit",
             "req_commit_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        request = current.request
        s3 = current.response.s3
        settings = current.deployment_settings

        person_id = self.pr_person_id
        organisation_id = self.org_organisation_id
        org_site_represent = self.org_site_represent
        req_id = self.req_req_id

        s3_date_format = settings.get_L10n_date_format()
        s3_date_represent = lambda dt: S3DateTime.date_represent(dt, utc=True)

        # ---------------------------------------------------------------------
        # Commitments (Pledges)
        tablename = "req_commit"
        table = self.define_table(tablename,
                                  self.super_link("site_id", "org_site",
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
                                            default = auth.s3_logged_in_person(),
                                            label = T("Committed By") ),
                                  s3.comments(),
                                  *s3.meta_fields())

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

        # Reusable Field
        commit_id = S3ReusableField("commit_id", db.req_commit, sortby="date",
                                    requires = IS_NULL_OR( \
                                                    IS_ONE_OF(db,
                                                              "req_commit.id",
                                                              self.commit_represent,
                                                              orderby="req_commit.date",
                                                              sort=True)),
                                    represent = self.commit_represent,
                                    label = T("Commitment"),
                                    ondelete = "CASCADE")

        self.configure(tablename,
                       # Commitments should only be made to a specific request
                       listadd = False,
                       onvalidation = self.commit_onvalidation,
                       onaccept = self.commit_onaccept)

        # Components
        # Commitment Items as component of Commitment
        self.add_component("req_commit_item",
                           req_commit="commit_id")

        # Commitment Persons as component of Commitment
        self.add_component("req_commit_person",
                           req_commit="commit_id")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                    req_commit_id = commit_id,
                )

    # -----------------------------------------------------------------
    @staticmethod
    def commit_represent(id):
        """
        """

        if id:
            db = current.db
            s3db = current.s3db

            table = s3db.req_commit

            r = db(table.id == id).select(table.type,
                                          table.date,
                                          table.organisation_id,
                                          table.site_id,
                                          limitby=(0, 1)).first()
            if r.type == 1:
                # Items
                return "%s - %s" % (table.site_id.represent(r.site_id),
                                    table.date.represent(r.date))
            else:
                return "%s - %s" % (table.organisation_id.represent(r.organisation_id),
                                    table.date.represent(r.date))
        else:
            return current.messages.NONE

    # -----------------------------------------------------------------
    @staticmethod
    def commit_onvalidation(form):
        """
            Copy the request_type to the commitment
        """

        db = current.db
        s3db = current.s3db
        s3mgr = current.manager

        req_id = s3mgr.get_session("req", "req")
        if req_id:
            rtable = s3db.req_req
            query = (rtable.id == req_id)
            req_record = db(query).select(rtable.type,
                                          limitby=(0, 1)).first()
            if req_record:
                form.vars.type = req_record.type

    # -----------------------------------------------------------------
    @staticmethod
    def commit_onaccept(form):
        """
        """

        db = current.db
        s3db = current.s3db

        table = s3db.req_commit

        vars = form.vars

        # Update owned_by_role to the organisation's owned_by_role
        # @ToDo: Facility
        if vars.organisation_id:
            otable = s3db.org_organisation
            query = (otable.id == vars.organisation_id)
            org = db(query).select(otable.owned_by_organisation,
                                   limitby=(0, 1)).first()
            if org:
                query = (table.id == vars.id)
                db(query).update(owned_by_organisation=org.owned_by_organisation)

        rtable = s3db.req_req
        if vars.type == 3: # People
            # If no organisation_id, then this is a single person commitment, so create the commit_person record automatically
            table = s3db.req_commit_person
            table.insert(commit_id = vars.id,
                         #skill_id = ???,
                         person_id = auth.s3_logged_in_person())
            # @ToDo: Mark Person's allocation status as 'Committed'
        elif vars.type == 9:
            # Non-Item requests should have commitment status updated if a commitment is made
            query = (table.id == vars.id) & \
                    (rtable.id == table.req_id)
            req_record = db(query).select(rtable.id,
                                          rtable.commit_status,
                                          limitby=(0, 1)).first()
            if req_record and req_record.commit_status == REQ_STATUS_NONE:
                # Assume Partial not Complete
                # @ToDo: Provide a way for the committer to specify this
                query = (rtable.id == req_record.id)
                db(query).update(commit_status=REQ_STATUS_PARTIAL)


# =============================================================================
class S3CommitItemModel(S3Model):
    """
    """

    names = ["req_commit_item"
            ]

    def model(self):

        T = current.T
        s3 = current.response.s3

        item_pack_id = self.supply_item_pack_id
        item_pack_virtualfields = self.supply_item_pack_virtualfields
        commit_id = self.req_commit_id
        req_item_id = self.req_item_id

        # -----------------------------------------------------------------
        # Commitment Items
        # @ToDo: Update the req_item_id in the commit_item if the req_id of the commit is changed

        tablename = "req_commit_item"
        table = self.define_table(tablename,
                                  commit_id(),
                                  #item_id,
                                  #supply_item_id(),
                                  req_item_id(),
                                  item_pack_id(),
                                  Field("quantity",
                                        "double",
                                        label = T("Quantity"),
                                        notnull = True),
                                  s3.comments(),
                                  *s3.meta_fields())

        # pack_quantity virtual field
        table.virtualfields.append(item_pack_virtualfields(tablename=tablename))

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

        self.configure(tablename,
                       onaccept = self.commit_item_onaccept )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                # Used by commit_req() controller
                req_commit_item_onaccept = self.commit_item_onaccept
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_item_onaccept(form):
        """
        """

        db = current.db
        s3db = current.s3db
        s3mgr = current.manager

        table = s3db.req_commit_item

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

        r_req_item = s3db.req_req_item[req_item_id]
        quantity_commit = quantity_commit / r_req_item.pack_quantity
        s3db.req_req_item[req_item_id] = dict(quantity_commit = quantity_commit)

        # Update status_commit of the req record
        s3mgr.store_session("req", "req_item", r_req_item.id)
        req_item_onaccept(None)


# =============================================================================
class S3CommitPersonModel(S3Model):
    """
    """

    names = ["req_commit_person"
            ]

    def model(self):

        T = current.T
        s3 = current.response.s3

        person_id = self.pr_person_id
        multi_skill_id = self.hrm_multi_skill_id
        commit_id = self.req_commit_id

        # -----------------------------------------------------------------
        # Committed Persons
        #
        tablename = "req_commit_person"
        table = self.define_table(tablename,
                                  commit_id(),
                                  # For reference
                                  multi_skill_id(writable=False, comment=None),
                                  # This should be person not hrm as we want to mark them as allocated
                                  person_id(),
                                  s3.comments(),
                                  *s3.meta_fields())

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

        # @ToDo: Fix this before enabling
        #self.configure(tablename,
        #                onaccept = self.commit_person_onaccept)

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_person_onaccept(form):
        """
            Not working
        """

        db = current.db
        s3db = current.s3db
        s3mgr = current.manager
        s3 = current.response.s3

        table = s3db.req_commit_person
        rstable = s3db.req_req_skill

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
        rstable[req_skill_id] = dict(quantity_commit = quantity_commit)

        # Update status_commit of the req record
        s3mgr.store_session("req", "req_skill", r_req_skill.id)
        req_skill_onaccept(None)

# =============================================================================
def req_item_onaccept(form):
    """
        Update req_req. commit_status, transit_status, fulfil_status
        None = quantity = 0 for ALL items
        Partial = some items have quantity > 0
        Complete = quantity_x = quantity(requested) for ALL items
    """

    db = current.db
    s3db = current.s3db
    s3mgr = current.manager

    table = s3db.req_req_item

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
        quantity = req_item.quantity
        for status_type in ["commit", "transit", "fulfil"]:
            if req_item["quantity_%s" % status_type] < quantity:
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

    rtable = s3db.req_req
    db(rtable.id == req_id).update(**status_update)

# =============================================================================
def req_skill_onaccept(form):
    """
        Update req_req. commit_status, transit_status, fulfil_status
        None = quantity = 0 for ALL skills
        Partial = some skills have quantity > 0
        Complete = quantity_x = quantity(requested) for ALL skills

        Create a Task for People to be assigned to
    """

    db = current.db
    s3db = current.s3db
    s3mgr = current.manager
    settings = current.deployment_settings

    if form and form.vars.req_id:
        req_id = form.vars.req_id
    else:
        req_id = s3mgr.get_session("req", "req")
    if not req_id:
        # @ToDo: should raise a proper HTTP status here
        raise Exception("can not get req_id")

    rtable = s3db.req_req
    query = (rtable.id == req_id)
    record = db(query).select(rtable.purpose,
                              limitby=(0, 1)).first()

    table = s3db.req_req_skill
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
        quantity = req_skill.quantity
        for status_type in ["commit", "transit", "fulfil"]:
            if req_skill["quantity_%s" % status_type] < quantity:
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
    query = (rtable.id == req_id)
    db(query).update(**status_update)

    if settings.has_module("project"):
        # Add a Task to which the People can be assigned

        # Get the request record
        record = db(query).select(rtable.request_number,
                                  rtable.purpose,
                                  rtable.priority,
                                  rtable.requester_id,
                                  rtable.site_id,
                                  limitby=(0, 1)).first()
        if not record:
            return
        otable = s3db.org_site
        query = (otable.id == record.site_id)
        site = db(query).select(otable.location_id,
                                otable.organisation_id,
                                limitby=(0, 1)).first()
        if site:
            location = site.location_id
            organisation = site.organisation_id
        else:
            location = None
            organisation = None

        table = s3db.project_task
        task = table.insert(name=record.request_number,
                            description=record.purpose,
                            priority=record.priority,
                            location_id=location,
                            site_id=record.site_id)

        # Add the Request as a Component to the Task
        table = s3db.project_task_req
        table.insert(task_id = task,
                     req_id = req_id)

# =============================================================================
def req_rheader(r, check_page = False):
    """ Resource Header for Requests """

    if r.representation == "html":
        if r.name == "req":
            record = r.record
            if record:

                T = current.T
                s3db = current.s3db
                request = current.request
                s3 = current.response.s3
                settings = current.deployment_settings

                tabs = [(T("Edit Details"), None)]
                if record.type == 1 and settings.has_module("inv"):
                    if settings.get_req_multiple_req_items():
                        req_item_tab_label = T("Items")
                    else:
                        req_item_tab_label = T("Item")
                    tabs.append((req_item_tab_label, "req_item"))
                elif record.type == 3 and settings.has_module("hrm"):
                    tabs.append((T("People"), "req_skill"))
                tabs.append((T("Documents"), "document"))
                if settings.get_req_use_commit():
                    tabs.append((T("Commitments"), "commit"))

                rheader_tabs = s3_rheader_tabs(r, tabs)

                site_id = request.vars.site_id
                if site_id:
                    site_name = s3db.org_site_represent(site_id, link = False)
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
                    s3.rfooter = commit_btn

                if settings.get_req_show_quantity_transit():
                    transit_status = req_status_opts.get(record.transit_status, "")
                    try:
                        if record.transit_status in [REQ_STATUS_PARTIAL,REQ_STATUS_COMPLETE] and \
                           record.fulfil_status in [None, REQ_STATUS_NONE, REQ_STATUS_PARTIAL]:
                            site_record = s3db.org_site[record.site_id]
                            table = s3db[site_record.instance_type]
                            query = (table.uuid == site_record.uuid)
                            id = db(query).select(table.id,
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

                table = r.table

                rheader = DIV( TABLE(
                                   TR(
                                    TH("%s: " % table.date_required.label),
                                    table.date_required.represent(record.date_required),
                                    TH( "%s: " % table.commit_status.label),
                                    table.commit_status.represent(record.commit_status),
                                    ),
                                   TR(
                                    TH( "%s: " % table.date.label),
                                    table.date.represent(record.date),
                                    *transit_status_cells
                                    ),
                                   TR(
                                    TH( "%s: " % table.site_id.label),
                                    table.site_id.represent(record.site_id),
                                    TH( "%s: " % table.fulfil_status.label),
                                    table.fulfil_status.represent(record.fulfil_status)
                                    ),
                                   TR(
                                    TH( "%s: " % table.comments.label),
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

# END =========================================================================
