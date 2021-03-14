# -*- coding: utf-8 -*-

"""
    Request management customisations for RLPPTM template

    @license: MIT
"""

from gluon import current, redirect, URL

from s3 import S3Method

# =============================================================================
class RegisterShipment(S3Method):
    """
        RESTful method to register a shipment for a request
        - side-step the mandatory commit stage implemented in req
        - side-step any stock checks and manipulations
    """

    def apply_method(self, r, **attr):
        """
            Entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}

        if r.tablename != "req_req":
            r.error(400, current.ERROR.BAD_RESOURCE)

        # HTTP method must be POST
        if r.http == "POST" and r.method == "ship":
            if not r.interactive:
                r.error(415, current.ERROR.BAD_FORMAT)
            if not r.record:
                r.error(404, current.ERROR.BAD_RECORD)
            # TODO must have a form key
            output = self.register_shipment(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def register_shipment(self, r, **attr):

        req = r.record

        db = current.db
        s3db = current.s3db
        auth = current.auth

        stable = s3db.inv_send
        ritable = s3db.req_req_item
        titable = s3db.inv_track_item

        # Check permission
        # - user is permitted to read the request (checked by REST)
        # - user must also be permitted to create inv_send
        if not auth.s3_has_permission("create", stable):
            r.unauthorised()
        user_person_id = auth.s3_logged_in_person

        # Create the shipment
        shipment = {"sender_id": user_person_id,
                    "site_id": None,    # TODO need a default site
                    "recipient_id": req.requester_id,
                    "to_site_id": req.site_id,
                    "req_ref": req.req_ref,
                    "status": 0,        # In Process
                    }
        shipment["id"] = shipment_id = stable.insert(**shipment)

        # Get the requested items
        ritable = s3db.req_req_item
        query = (ritable.req_id == req.id) & \
                (ritable.quantity > 0) & \
                (ritable.deleted == False)
        ritems = db(query).select(ritable.id,
                                  ritable.item_id,
                                  ritable.item_pack_id,
                                  ritable.quantity,
                                  ritable.quantity_transit,
                                  ritable.quantity_fulfil,
                                  )

        # Create corresponding track items
        # - directly from catalog items, not linked to any stock items,
        #   so no stock level checks or updates will happen
        for ritem in ritems:
            titem = {"req_item_id": ritem.id,
                     "track_org_id": None, # TODO default site org
                     "send_id": shipment_id,
                     "status": 1, # Preparing
                     "item_id": ritem.item_id,
                     "item_pack_id": ritem.item_pack_id,
                     "quantity": ritem.quantity,
                     "recv_quantity": ritem.quantity, # is this correct?
                     }
            titem["id"] = titable.insert(**titem)

        # Postprocess the shipment
        s3db.onaccept(stable, shipment, method="create")

        # Redirect to the shipment
        # TODO hint to verify the shipment before actually sending it
        redirect(URL(c="inv", f="send", args = [shipment_id]))

        return None

# END =========================================================================
