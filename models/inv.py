# -*- coding: utf-8 -*-
"""
    Inventory Management

    A module to record inventories of items at a location (site)
"""

# Session dictionary to indicate if a site inv should be shown
if session.s3.show_inv == None:
    session.s3.show_inv = {}

# -----------------------------------------------------------------------------
# Defined in the Model for use from Multiple Controllers for unified menus
#
def inv_item_controller():
    """ RESTful CRUD controller """

    table = s3db.inv_inv_item

    # Limit site_id to sites the user has permissions for
    auth.permission.permitted_facilities(table=table,
                                         error_msg=T("You do not have permission for any site to add an inventory item."))

    return s3_rest_controller("inv", "inv_item",
                              csv_extra_fields = [
                                dict(label="Organisation",
                                     field=s3db.org_organisation_id(comment=None))],
                              interactive_report = True
                              )

# -----------------------------------------------------------------------------
def inv_recv_controller():
    """ RESTful CRUD controller """
    tablename = "inv_recv"
    table = s3db.inv_recv

    # Limit site_id to sites the user has permissions for
    if deployment_settings.get_inv_shipment_name() == "order":
        error_msg = T("You do not have permission for any facility to add an order.")
    else:
        error_msg = T("You do not have permission for any facility to receive a shipment.")
    auth.permission.permitted_facilities(table=table,
                                         error_msg=error_msg)

    def prep(r):
        if r.interactive:

            # Redirect to the Items tabs after creation
            recv_item_url = URL(f="recv", args=["[id]",
                                                "recv_item"])
            s3mgr.configure(tablename,
                            create_next = recv_item_url,
                            update_next = recv_item_url)

            # If component view
            if r.record:
                SHIP_STATUS_IN_PROCESS = s3db.inv_ship_status["IN_PROCESS"]
                if r.record.status == SHIP_STATUS_IN_PROCESS:
                    s3.crud_strings.inv_recv.title_update = \
                    s3.crud_strings.inv_recv.title_display = T("Process Received Shipment")
        return True

    response.s3.prep = prep

    output = s3_rest_controller("inv", "recv",
                                rheader=eden.inv.inv_recv_rheader,
                                componentname="inv_recv_item",
                                report_hide_comments=True,
                                )
    return output

# -----------------------------------------------------------------------------
def inv_send_controller():
    """ RESTful CRUD controller """
    tablename = "inv_send"
    table = s3db.inv_send

    # Limit site_id to sites the user has permissions for
    error_msg = T("You do not have permission for any facility to send a shipment.")
    auth.permission.permitted_facilities(table=table,
                                         error_msg=error_msg)

    # Set Validator for checking against the number of items in the warehouse
    vars = request.vars
    if (vars.inv_item_id):
        s3db.inv_send_item.quantity.requires = QUANTITY_INV_ITEM(db,
                                                                 vars.inv_item_id,
                                                                 vars.item_pack_id)

    def prep(r):
        if r.interactive:
            # Redirect to the Items tabs after creation
            send_item_url = URL(f="send", args=["[id]",
                                                "send_item"])
            s3mgr.configure(tablename,
                            create_next = send_item_url,
                            update_next = send_item_url)

            # Default to the Search tab in the location selector
            response.s3.gis.tab = "search"

            # If component view
            if r.record:
                if r.record.get("site_id"):
                    # Restrict to items from this warehouse only
                    sitable = s3db.inv_send_item
                    sitable.inv_item_id.requires = IS_ONE_OF(db,
                                                             "inv_inv_item.id",
                                                             s3db.inv_item_represent,
                                                             orderby="inv_inv_item.id",
                                                             sort=True,
                                                             filterby = "site_id",
                                                             filter_opts = [r.record.site_id]
                                                            )
                SHIP_STATUS_IN_PROCESS = s3db.inv_ship_status["IN_PROCESS"]
                SHIP_STATUS_SENT = s3db.inv_ship_status["SENT"]
                if r.record.status == SHIP_STATUS_IN_PROCESS:
                    s3.crud_strings.inv_send.title_update = \
                    s3.crud_strings.inv_send.title_display = T("Process Shipment to Send")
                elif "site_id" in request.vars and r.record.status == SHIP_STATUS_SENT:
                    s3.crud_strings.inv_send.title_update = \
                    s3.crud_strings.inv_send.title_display = T("Review Incoming Shipment to Receive")

        return True

    response.s3.prep = prep

    output = s3_rest_controller("inv", "send",
                                rheader=eden.inv.inv_send_rheader,
                                componentname="inv_send_item",
                                report_hide_comments=True
                               )
    return output


# -----------------------------------------------------------------------------
# Inv Send Incoming as a simulated "component" of Inventory Store
def inv_incoming():
    """
        Pipeline Report showing the inbound shipments which haven't yet been received
        Allows easy access to Receive these shipments into the Inventory

        @ToDo: Provide a function to allow adding new expected shipments which are coming ex-system
               - this would be adding a Sent Shipment with us as Destination, not Source
    """

    tablename, id = request.vars.viewing.split(".")
    record = s3db[tablename][id]
    to_site_id = record.site_id
    site_id = record.site_id

    rheader_dict = dict(org_office = s3db.org_rheader)
    if deployment_settings.has_module("cr"):
        rheader_dict["cr_shelter"] = response.s3.shelter_rheader
    if deployment_settings.has_module("hms"):
        rheader_dict["hms_hospital"] = s3db.hms_hospital_rheader

    stable = s3db.inv_send
    SHIP_STATUS_SENT = s3db.inv_ship_status["SENT"]
    response.s3.filter = (stable.status == SHIP_STATUS_SENT) & \
                         (stable.to_site_id == to_site_id)

    s3mgr.configure("inv_send", insertable=False)

    response.s3.actions = [dict(url = URL(c="inv", f="send",
                                          args = ["[id]", "send_item"],
                                          vars = dict(site_id = site_id)
                                          ),
                                _class = "action-btn",
                                label = str(T("Review"))),
                           dict(url = URL(c="inv", f="recv_sent",
                                          args = ["[id]"],
                                          vars = dict(site_id = site_id)
                                           ),
                                _class = "action-btn",
                                label = "%s    " % T("Process")),
                           ]

    # @ToDo: Probably need to adjust some more CRUD strings:
    s3.crud_strings["inv_send"].update(
        msg_record_modified = T("Incoming Shipment updated"),
        msg_record_deleted = T("Incoming Shipment canceled"),
        msg_list_empty = T("No Incoming Shipments"))

    output = s3_rest_controller("inv", "send",
                                method = "list",
                                rheader = rheader_dict[tablename],
                                title = s3.crud_strings[tablename]["title_display"])

    if tablename == "org_office" and isinstance(output, dict):
        output["title"] = T("Warehouse Details")

    return output

# END =========================================================================
