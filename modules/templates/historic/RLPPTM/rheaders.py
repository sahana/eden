# -*- coding: utf-8 -*-

"""
    Custom rheaders for RLPPTM template

    @license: MIT
"""

from gluon import current, A, URL

from s3 import S3ResourceHeader, s3_rheader_resource

# =============================================================================
def rlpptm_fin_rheader(r, tabs=None):
    """ FIN custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []
    rheader_title = None
    img = None

    if record:
        T = current.T

        if tablename == "fin_voucher":

            if not tabs:
                tabs = [(T("Voucher"), None),
                        ]

            rheader_title = None
            rheader_fields = [["program_id",
                               ],
                              ["signature",
                               ],
                              ["date",
                               ],
                              ["valid_until",
                               ],
                              ]

            signature = record.signature
            if signature:
                try:
                    import qrcode
                except ImportError:
                    pass
                else:
                    from s3 import s3_qrcode_represent
                    img = s3_qrcode_represent(signature, show_value=False)
                    img.add_class("rheader-qrcode")

        elif tablename == "fin_voucher_debit":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

                # If user can cancel the debit and the debit can be
                # cancelled, add the cancel-action as tab
                from .helpers import can_cancel_debit
                if can_cancel_debit(record):
                    p = current.s3db.fin_VoucherProgram(record.program_id)
                    error = p.cancellable(record.id)[1]
                    if not error:
                        tabs.append((T("Cancel##debit"), "cancel"))

            rheader_title = "signature"
            rheader_fields = [[(T("Status"), "status"),],
                              ]

        elif tablename == "fin_voucher_invoice":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

            from .helpers import InvoicePDF, check_invoice_integrity

            # Lookup the invoice header data
            data = InvoicePDF.lookup_header_data(record)
            addr_street = lambda row: data.get("addr_street", "-")
            addr_place = lambda row: "%s %s" % (data.get("addr_postcode", ""),
                                                data.get("addr_place", "?"),
                                                )
            email = lambda row: data.get("email") or "-"

            rheader_title = "pe_id"
            rheader_fields = [[(T("Address"), addr_street),
                               "invoice_no",
                               (T("Integrity Check"), check_invoice_integrity),
                               ],
                              [(T("Place"), addr_place), "date"],
                              [(T("Email"), email), "status"],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

        if img:
            rheader.insert(0, img)

    return rheader

# =============================================================================
def rlpptm_org_rheader(r, tabs=None):
    """ ORG custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "org_organisation":

            auth = current.auth
            is_org_group_admin = auth.s3_has_role("ORG_GROUP_ADMIN")

            db = current.db
            s3db = current.s3db

            if not tabs:

                invite_tab = None
                sites_tab = None
                doc_tab = None

                gtable = s3db.org_group
                mtable = s3db.org_group_membership
                query = (mtable.organisation_id == record.id) & \
                        (mtable.group_id == gtable.id)
                group = db(query).select(gtable.name,
                                         limitby = (0, 1)
                                         ).first()
                if group:
                    from .config import TESTSTATIONS, SCHOOLS, GOVERNMENT
                    if group.name == TESTSTATIONS:
                        sites_tab = (T("Test Stations"), "facility")
                        doc_tab = (T("Documents"), "document")
                    elif group.name == SCHOOLS:
                        sites_tab = (T("Administrative Offices"), "office")
                        if is_org_group_admin:
                            invite_tab = (T("Invite"), "invite")
                    elif group.name == GOVERNMENT:
                        sites_tab = (T("Warehouses"), "warehouse")

                tabs = [(T("Organisation"), None),
                        invite_tab,
                        sites_tab,
                        (T("Staff"), "human_resource"),
                        doc_tab,
                        ]

            # Look up the OrgID
            def org_id(row):
                ttable = s3db.org_organisation_tag
                query = (ttable.organisation_id == row.id) & \
                        (ttable.tag == "OrgID") & \
                        (ttable.deleted == False)
                tag = db(query).select(ttable.value, limitby=(0, 1)).first()
                return tag.value if tag else "-"

            # Check for active user accounts:
            rheader_fields = [[(T("Organization ID"), org_id)]]
            if is_org_group_admin:

                from .helpers import get_org_accounts
                active = get_org_accounts(record.id)[0]

                active_accounts = lambda row: len(active)
                rheader_fields.append([(T("Active Accounts"), active_accounts)])

            rheader_title = "name"

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

    return rheader

# =============================================================================
def rlpptm_project_rheader(r, tabs=None):
    """ PROJECT custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "project_project":

            if not tabs:

                tabs = [(T("Basic Details"), None),
                        (T("Organizations"), "organisation"),
                        ]

            rheader_title = "name"

            rheader_fields = [[(T("Code"), "code")],
                              ["organisation_id"],
                              ]
        else:
            return None

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

    return rheader

# =============================================================================
def rlpptm_req_rheader(r, tabs=None):
    """ REQ custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "req_req":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Items"), "req_item"),
                        ]

            rheader_title = "site_id"

            rheader_fields = [["req_ref", "transit_status"],
                              ["date", "fulfil_status"],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

    return rheader

# =============================================================================
def rlpptm_supply_rheader(r, tabs=None):
    """ SUPPLY custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "supply_item":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Packs"), "item_pack"),
                        (T("In Requests"), "req_item"),
                        (T("In Shipments"), "track_item"),
                        ]

            rheader_title = "name"

            rheader_fields = [["code"],
                              ["um"],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
        rheader = rheader(r, table = resource.table, record = record)

    return rheader

# =============================================================================
def rlpptm_inv_rheader(r, tabs=None):
    """ INV custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        db = current.db
        s3 = current.response.s3

        auth = current.auth
        s3db = current.s3db

        from s3db.inv import SHIP_STATUS_IN_PROCESS, SHIP_STATUS_SENT

        if tablename == "inv_send":
            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Items"), "track_item"),
                        ]

            rheader_fields = [["req_ref"], # , "send_ref"],
                              ["status"],
                              ["date"]
                              ]
            rheader_title = "to_site_id"

            rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)

            actions = []

            # If the record status is SHIP_STATUS_IN_PROCESS, both sites are active
            # and there is at least one track item linked to it, add the send-button
            from .requests import is_active
            reason = None
            if record.status == SHIP_STATUS_IN_PROCESS:
                if not is_active(record.site_id):
                    reason = T("Distribution center no longer active")
                elif not is_active(record.to_site_id):
                    reason = T("Requesting site no longer active")
                elif auth.s3_has_permission("update", resource.table, record_id=record.id):
                    titable = s3db.inv_track_item
                    query = (titable.send_id == record.id) & \
                            (titable.deleted == False)
                    row = db(query).select(titable.id, limitby=(0, 1)).first()
                    if row:
                        actions.append(A(T("Send Shipment"),
                                         _href = URL(c = "inv",
                                                     f = "send_process",
                                                     args = [record.id]
                                                     ),
                                         _id = "send_process",
                                         _class = "action-btn",
                                         ))
                        s3.jquery_ready.append('''S3.confirmClick("#send_process","%s")''' \
                                                % T("Do you want to send this shipment?"))
                    else:
                        reason = T("Shipment is empty")
            else:
                reason = T("Shipment already in process")

            if reason:
                actions.append(A(T("Send Shipment"),
                                 _id = "send_process",
                                 _disabled = "disabled",
                                 _class = "action-btn",
                                 _title = reason,
                                 ))

            rheader = rheader(r, table=resource.table, record=record, actions=actions)

        elif tablename == "inv_recv":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Items"), "track_item"),
                        ]

            # Get the number of items linked to this delivery
            titable = s3db.inv_track_item
            query = (titable.recv_id == record.id) & \
                    (titable.deleted == False)
            cnt = titable.id.count()
            row = db(query).select(cnt).first()
            num_items = row[cnt] if row else 0

            # Representation of the number of items
            def content(row):
                if num_items == 1:
                    msg = T("This shipment contains one line item")
                elif num_items > 1:
                    msg = T("This shipment contains %s items") % num_items
                else:
                    msg = "-"
                return msg

            rheader_fields = [#["send_ref", "site_id"],
                              ["status", "site_id"],
                              ["date", (T("Content"), content)],
                              ]
            rheader_title = "req_ref"

            rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)

            actions = []

            # If the record is SHIP_STATUS_IN_PROCESS or SHIP_STATUS_SENT
            # and there is at least one track item linked to it, add the receive-button
            if record.status in (SHIP_STATUS_IN_PROCESS, SHIP_STATUS_SENT) and \
               auth.s3_has_permission("update", resource.table, record_id = record.id) and \
               num_items:

                actions.append(A(T("Receive Shipment"),
                                   _href = URL(c = "inv",
                                               f = "recv_process",
                                               args = [record.id]
                                               ),
                                   _id = "recv_process",
                                   _class = "action-btn"
                                   ))
                s3.jquery_ready.append('''S3.confirmClick("#recv_process","%s")''' \
                                        % T("Did you receive this shipment?"))

            rheader = rheader(r, table=resource.table, record=record, actions=actions)

        elif tablename == "inv_warehouse":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]

            rheader_fields = [["code", "email"],
                              ["organisation_id", "phone1"],
                              ["location_id", "phone2"],
                              ]
            rheader_title = "name"

            rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)
            rheader = rheader(r, table=resource.table, record=record)

    return rheader

# =============================================================================
def rlpptm_profile_rheader(r, tabs=None):
    """ Custom rheader for default/person """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:

        T = current.T

        if tablename == "pr_person":

            tabs = [(T("Person Details"), None),
                    (T("User Account"), "user_profile"),
                    (T("Contact Information"), "contacts"),
                    ]
            rheader_fields = []

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )
    return rheader

# END =========================================================================
