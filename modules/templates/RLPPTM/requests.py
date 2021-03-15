# -*- coding: utf-8 -*-

"""
    Request management customisations for RLPPTM template

    @license: MIT
"""

from collections import OrderedDict

from gluon import current, redirect, URL, A, B

from s3 import S3Method, S3Represent, s3_str

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
            self.register_shipment(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def register_shipment(r, **attr):

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

# =============================================================================
def req_filter_widgets():
    """
        Filter widgets for requests

        @returns: list of filter widgets
    """

    T = current.T

    from s3 import S3DateFilter, \
                   S3LocationFilter, \
                   S3OptionsFilter, \
                   S3TextFilter, \
                   s3_get_filter_opts

    s3db = current.s3db

    req_status_opts = OrderedDict(sorted(s3db.req_status_opts.items(),
                                         key = lambda i: i[0],
                                         ))

    filter_widgets = [
        S3TextFilter(["req_ref"],
                     label = T("Order No."),
                     ),
        S3DateFilter("date"),
        S3OptionsFilter("transit_status",
                        cols = 3,
                        options = req_status_opts,
                        sort = False,
                        ),
        S3OptionsFilter("fulfil_status",
                        cols = 3,
                        hidden = True,
                        options = req_status_opts,
                        sort = False,
                        ),
        S3OptionsFilter("req_item.item_id",
                        hidden = True,
                        options = lambda: s3_get_filter_opts("supply_item"),
                        ),
        ]

    if current.auth.s3_has_role("SUPPLY_COORDINATOR"):

        coordinator_filters = [
            S3LocationFilter("site_id$location_id",
                             levels = ["L3", "L4"],
                             ),
            S3TextFilter("site_id$location_id$addr_postcode",
                         label = T("Postcode"),
                         ),
            S3OptionsFilter("site_id",
                            hidden = True
                            ),
            ]
        filter_widgets[2:2] = coordinator_filters

    return filter_widgets

# =============================================================================
def send_filter_widgets():
    """
        Filter widgets for outgoing shipments

        @returns: list of filter widgets
    """

    T = current.T

    from s3 import S3DateFilter, \
                   S3LocationFilter, \
                   S3OptionsFilter, \
                   S3TextFilter, \
                   s3_get_filter_opts

    s3db = current.s3db

    send_status_opts = OrderedDict(sorted(s3db.inv_shipment_status_labels.items(),
                                          key = lambda i: i[0],
                                          ))
    # We don't currently use these statuses
    from s3db.inv import SHIP_STATUS_CANCEL, SHIP_STATUS_RETURNING
    del send_status_opts[SHIP_STATUS_CANCEL]
    del send_status_opts[SHIP_STATUS_RETURNING]

    filter_widgets = [
        S3TextFilter(["req_ref",
                      "send_ref",
                      ],
                     label = T("Search"),
                     ),
        S3DateFilter("date"),
        S3OptionsFilter("status",
                        cols = 3,
                        options = send_status_opts,
                        sort = False,
                        ),
        S3OptionsFilter("track_item.item_id",
                        hidden = True,
                        options = lambda: s3_get_filter_opts("supply_item"),
                        ),
        ]

    if current.auth.s3_has_role("SUPPLY_COORDINATOR"):

        coordinator_filters = [
            S3OptionsFilter("to_site_id",
                            ),
            S3LocationFilter("to_site_id$location_id",
                             levels = ["L3", "L4"],
                             hidden = True
                             ),
            S3TextFilter("to_site_id$location_id$addr_postcode",
                         label = T("Postcode"),
                         hidden = True
                         ),
            ]
        filter_widgets[3:3] = coordinator_filters

    return filter_widgets

# =============================================================================
def recv_filter_widgets():
    """
        Filter widgets for incoming shipments

        @returns: list of filter widgets
    """

    T = current.T

    from s3 import S3DateFilter, \
                   S3OptionsFilter, \
                   S3TextFilter, \
                   s3_get_filter_opts

    s3db = current.s3db

    recv_status_opts = OrderedDict(sorted(s3db.inv_shipment_status_labels.items(),
                                          key = lambda i: i[0],
                                          ))
    # We don't currently use these statuses
    from s3db.inv import SHIP_STATUS_CANCEL, SHIP_STATUS_RETURNING
    del recv_status_opts[SHIP_STATUS_CANCEL]
    del recv_status_opts[SHIP_STATUS_RETURNING]

    filter_widgets = [
        S3TextFilter(["req_ref",
                      "send_ref",
                      ],
                     label = T("Search"),
                     ),
        S3OptionsFilter("status",
                        cols = 3,
                        options = recv_status_opts,
                        sort = False,
                        ),
        S3DateFilter("date",
                     hidden = True,
                     ),
        S3OptionsFilter("track_item.item_id",
                        hidden = True,
                        options = lambda: s3_get_filter_opts("supply_item"),
                        ),
        ]

    return filter_widgets

# =============================================================================
class ShipmentCodeRepresent(S3Represent):
    """
        S3Represent variant of the shipment code representation (REQ, WB, GRN)

        - TODO generalize as supply_ShipmentCodeRepresent?
    """

    def __init__(self, tablename, fieldname, show_link=True, pdf=False):
        """
            Constructor

            @param show_link: show representation as clickable link
        """

        if not show_link:
            lookup = key = None
        else:
            lookup = tablename
            key = fieldname

        super(ShipmentCodeRepresent, self).__init__(lookup = lookup,
                                                    key = key,
                                                    show_link = show_link,
                                                    )
        if not show_link:
            # Make lookup-function a simple echo
            self._lookup = lambda values, rows=None: \
                           {v: B(v if v else self.none) for v in values}

        c, f = tablename.split("_", 1)
        args = ["[id]"]
        if pdf:
            args.append("form")
        self.linkto = URL(c=c, f=f, args=args, extension="")

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        table = self.table

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        rows = current.db(query).select(table.id,
                                        key,
                                        limitby = (0, count),
                                        )
        self.queries += 1

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """
        return str(row.id)

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.
            - same as default, except with k and v reversed ;)

            @param k: the key [here: the shipment code]
            @param v: the representation of the key [here: the record ID]

            @param row: the row with this key
        """

        if self.linkto:
            k = s3_str(k)
            return A(k, _href=self.linkto.replace("[id]", v) \
                                         .replace("%5Bid%5D", v))
        else:
            return k

# END =========================================================================
