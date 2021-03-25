# -*- coding: utf-8 -*-

"""
    Helper functions and classes for RLPPTM template

    @license: MIT
"""

from gluon import current, Field, CRYPT, IS_EMAIL, IS_LOWER, IS_NOT_IN_DB, \
                  SQLFORM, DIV, H4, H5, I, INPUT, P, SPAN, TABLE, TD, TH, TR

from s3 import IS_FLOAT_AMOUNT, S3DateTime, S3Method, \
               s3_fullname, s3_mark_required

# =============================================================================
def get_role_realms(role):
    """
        Get all realms for which a role has been assigned

        @param role: the role ID or role UUID

        @returns: list of pe_ids the current user has the role for,
                  None if the role is assigned site-wide, or an
                  empty list if the user does not have the role, or
                  no realm for the role
    """

    db = current.db
    auth = current.auth
    s3db = current.s3db

    if isinstance(role, str):
        gtable = auth.settings.table_group
        query = (gtable.uuid == role) & \
                (gtable.deleted == False)
        row = db(query).select(gtable.id,
                               cache = s3db.cache,
                               limitby = (0, 1),
                               ).first()
        role_id = row.id if row else None
    else:
        role_id = role

    role_realms = []
    user = auth.user
    if user:
        role_realms = user.realms.get(role_id, role_realms)

    return role_realms

# =============================================================================
def get_org_accounts(organisation_id):
    """
        Get all user accounts linked to an organisation

        @param organisation_id: the organisation ID

        @returns: tuple (active, disabled, invited), each being
                  a list of user accounts (auth_user Rows)
    """

    auth = current.auth
    s3db = current.s3db

    utable = auth.settings.table_user
    oltable = s3db.org_organisation_user
    pltable = s3db.pr_person_user

    join = oltable.on((oltable.user_id == utable.id) & \
                      (oltable.deleted == False))
    left = pltable.on((pltable.user_id == utable.id) & \
                      (pltable.deleted == False))
    query = (oltable.organisation_id == organisation_id)
    rows = current.db(query).select(utable.id,
                                    utable.first_name,
                                    utable.last_name,
                                    utable.email,
                                    utable.registration_key,
                                    pltable.pe_id,
                                    join = join,
                                    left = left,
                                    )

    active, disabled, invited = [], [], []
    for row in rows:
        user = row[utable]
        person_link = row.pr_person_user
        if person_link.pe_id:
            if user.registration_key:
                disabled.append(user)
            else:
                active.append(user)
        else:
            invited.append(user)

    return active, disabled, invited

# -----------------------------------------------------------------------------
def get_role_users(role_uid, pe_id=None, organisation_id=None):
    """
        Look up users with a certain user role for a certain organisation

        @param role_uid: the role UUID
        @param pe_id: the pe_id of the organisation, or
        @param organisation_id: the organisation_id

        @returns: a dict {user_id: pe_id} of all active users with this
                  role for the organisation
    """

    db = current.db

    auth = current.auth
    s3db = current.s3db

    if not pe_id and organisation_id:
        # Look up the realm pe_id from the organisation
        otable = s3db.org_organisation
        query = (otable.id == organisation_id) & \
                (otable.deleted == False)
        organisation = db(query).select(otable.pe_id,
                                        limitby = (0, 1),
                                        ).first()
        pe_id = organisation.pe_id if organisation else None

    # Get all users with this realm as direct OU ancestor
    users = s3db.pr_realm_users(pe_id) if pe_id else None
    if users:
        # Look up those among the realm users who have
        # the role for either pe_id or for their default realm
        gtable = auth.settings.table_group
        mtable = auth.settings.table_membership
        ltable = s3db.pr_person_user
        utable = auth.settings.table_user
        join = [mtable.on((mtable.user_id == ltable.user_id) & \
                          ((mtable.pe_id == None) | (mtable.pe_id == pe_id)) & \
                          (mtable.deleted == False)),
                gtable.on((gtable.id == mtable.group_id) & \
                          (gtable.uuid == role_uid)),
                # Only verified+active accounts:
                utable.on((utable.id == mtable.user_id) & \
                          ((utable.registration_key == None) | \
                           (utable.registration_key == "")))
                ]
        query = (ltable.user_id.belongs(set(users.keys()))) & \
                (ltable.deleted == False)
        rows = db(query).select(ltable.user_id,
                                ltable.pe_id,
                                join = join,
                                )
        users = {row.user_id: row.pe_id for row in rows}

    return users if users else None

# -----------------------------------------------------------------------------
def get_role_emails(role_uid, pe_id=None, organisation_id=None):
    """
        Look up the emails addresses of users with a certain user role
        for a certain organisation

        @param role_uid: the role UUID
        @param pe_id: the pe_id of the organisation, or
        @param organisation_id: the organisation_id

        @returns: a list of email addresses
    """

    contacts = None

    users = get_role_users(role_uid,
                           pe_id = pe_id,
                           organisation_id = organisation_id,
                           )

    if users:
        # Look up their email addresses
        ctable = current.s3db.pr_contact
        query = (ctable.pe_id.belongs(set(users.values()))) & \
                (ctable.contact_method == "EMAIL") & \
                (ctable.deleted == False)
        rows = current.db(query).select(ctable.value,
                                        orderby = ~ctable.priority,
                                        )
        contacts = list(set(row.value for row in rows))

    return contacts if contacts else None

# -----------------------------------------------------------------------------
def get_role_hrs(role_uid, pe_id=None, organisation_id=None):
    """
        Look up the HR records of users with a certain user role
        for a certain organisation

        @param role_uid: the role UUID
        @param pe_id: the pe_id of the organisation, or
        @param organisation_id: the organisation_id

        @returns: a list of hrm_human_resource IDs
    """

    hr_ids = None

    users = get_role_users(role_uid,
                           pe_id = pe_id,
                           organisation_id = organisation_id,
                           )

    if users:
        # Look up their HR records
        s3db = current.s3db
        ptable = s3db.pr_person
        htable = s3db.hrm_human_resource
        join = htable.on((htable.person_id == ptable.id) & \
                         (htable.deleted == False))
        query = (ptable.pe_id.belongs(set(users.values()))) & \
                (ptable.deleted == False)
        rows = current.db(query).select(htable.id,
                                        join = join,
                                        )
        hr_ids = list(set(row.id for row in rows))

    return hr_ids if hr_ids else None

# -----------------------------------------------------------------------------
def assign_pending_invoices(billing_id, organisation_id=None, invoice_id=None):
    """
        Auto-assign pending invoices in a billing to accountants,
        taking into account their current workload

        @param billing_id: the billing ID
        @param organisation_id: the ID of the accountant organisation
        @param invoice_id: assign only this invoice
    """

    db = current.db
    s3db = current.s3db

    if not organisation_id:
        # Look up the accounting organisation for the billing
        btable = s3db.fin_voucher_billing
        query = (btable.id == billing_id)
        billing = db(query).select(btable.organisation_id,
                                   limitby = (0, 1),
                                   ).first()
        if not billing:
            return
        organisation_id = billing.organisation_id

    if organisation_id:
        # Look up the active accountants of the accountant org
        accountants = get_role_hrs("PROGRAM_ACCOUNTANT",
                                   organisation_id = organisation_id,
                                   )
    else:
        accountants = None

    # Query for any pending invoices of this billing cycle
    itable = s3db.fin_voucher_invoice
    if invoice_id:
        query = (itable.id == invoice_id)
    else:
        query = (itable.billing_id == billing_id)
    query &= (itable.status != "PAID") & (itable.deleted == False)

    if accountants:
        # Limit to invoices that have not yet been assigned to any
        # of the accountants in charge:
        query &= ((itable.human_resource_id == None) | \
                  (~(itable.human_resource_id.belongs(accountants))))

        # Get the invoices
        invoices = db(query).select(itable.id,
                                    itable.human_resource_id,
                                    )
        if not invoices:
            return

        # Look up the number of pending invoices assigned to each
        # accountant, to get a measure for their current workload
        workload = {hr_id: 0 for hr_id in accountants}
        query = (itable.status != "PAID") & \
                (itable.human_resource_id.belongs(accountants)) & \
                (itable.deleted == False)
        num_assigned = itable.id.count()
        rows = db(query).select(itable.human_resource_id,
                                num_assigned,
                                groupby = itable.human_resource_id,
                                )
        for row in rows:
            workload[row[itable.human_resource_id]] = row[num_assigned]

        # Re-assign invoices
        # - try to distribute workload evenly among the accountants
        for invoice in invoices:
            hr_id, num = min(workload.items(), key=lambda item: item[1])
            invoice.update_record(human_resource_id = hr_id)
            workload[hr_id] = num + 1

    elif not invoice_id:
        # Unassign all pending invoices
        db(query).update(human_resource_id = None)

# -----------------------------------------------------------------------------
def check_invoice_integrity(row):
    """
        Rheader-helper to check and report invoice integrity

        @param row: the invoice record

        @returns: integrity check result
    """

    billing = current.s3db.fin_VoucherBilling(row.billing_id)
    try:
        checked = billing.check_invoice(row.id)
    except ValueError:
        checked = False

    T = current.T
    if checked:
        return SPAN(T("Ok"),
                    I(_class="fa fa-check"),
                    _class="record-integrity-ok",
                    )
    else:
        current.response.error = T("This invoice may be invalid - please contact the administrator")
        return SPAN(T("Failed"),
                    I(_class="fa fa-exclamation-triangle"),
                    _class="record-integrity-broken",
                    )

# -----------------------------------------------------------------------------
def get_stats_projects():
    """
        Find all projects the current user can report test results, i.e.
        - projects marked as STATS=Y where
        - the current user has the VOUCHER_PROVIDER role for a partner organisation
    """

    permitted_realms = current.auth.permission.permitted_realms
    realms = permitted_realms("disease_case_diagnostics", "create")

    if realms is not None and not realms:
        return []

    s3db = current.s3db

    otable = s3db.org_organisation
    ltable = s3db.project_organisation
    ttable = s3db.project_project_tag

    oquery = otable.deleted == False
    if realms:
        oquery = otable.pe_id.belongs(realms) & oquery

    join = [ltable.on((ltable.project_id == ttable.project_id) & \
                      (ltable.deleted == False)),
            otable.on((otable.id == ltable.organisation_id) & oquery),
            ]

    query = (ttable.tag == "STATS") & \
            (ttable.value == "Y") & \
            (ttable.deleted == False)
    rows = current.db(query).select(ttable.project_id,
                                    cache = s3db.cache,
                                    join = join,
                                    groupby = ttable.project_id,
                                    )
    return [row.project_id for row in rows]

# -----------------------------------------------------------------------------
def can_cancel_debit(debit):
    """
        Check whether the current user is entitled to cancel a certain
        voucher debit:
        * User must have the VOUCHER_PROVIDER role for the organisation
          that originally accepted the voucher (not even ADMIN-role can
          override this requirement)

        @param debit: the debit (Row, must contain the debit pe_id)

        @returns: True|False
    """

    auth = current.auth
    s3db = current.s3db

    user = auth.user
    if user:
        # Look up the role ID
        gtable = auth.settings.table_group
        query = (gtable.uuid == "VOUCHER_PROVIDER")
        role = current.db(query).select(gtable.id,
                                        cache = s3db.cache,
                                        limitby = (0, 1),
                                        ).first()
        if not role:
            return False

        # Get the realms they have this role for
        realms = user.realms
        if role.id in realms:
            role_realms = realms.get(role.id)
        else:
            # They don't have the role at all
            return False

        if not role_realms:
            # User has a site-wide VOUCHER_PROVIDER role, however
            # for cancellation of debits they must be affiliated
            # with the debit owner organisation
            role_realms = s3db.pr_realm(user["pe_id"])

        return debit.pe_id in role_realms

    else:
        # No user
        return False

# =============================================================================
class InviteUserOrg(S3Method):
    """ Custom Method Handler to invite User Organisations """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}

        if r.http in ("GET", "POST"):
            if not r.record:
                r.error(400, current.ERROR.BAD_REQUEST)
            if r.interactive:
                output = self.invite(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def invite(self, r, **attr):
        """
            Prepare and process invitation form

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        T = current.T

        db = current.db
        s3db = current.s3db

        response = current.response
        request = current.request
        session = current.session

        settings = current.deployment_settings
        auth = current.auth
        auth_settings = auth.settings
        auth_messages = auth.messages

        output = {"title": T("Invite Organisation"),
                  }

        # Check for existing accounts
        active, disabled, invited = get_org_accounts(r.record.id)
        if active or disabled:
            response.error = T("There are already user accounts registered for this organization")

            from gluon import UL, LI
            from s3 import s3_format_fullname

            fullname = lambda user: s3_format_fullname(fname = user.first_name,
                                                    lname = user.last_name,
                                                    truncate = False,
                                                    )
            account_list = DIV(_class="org-account-list")
            if active:
                account_list.append(H4(T("Active Accounts")))
                accounts = UL()
                for user in active:
                    accounts.append(LI("%s <%s>" % (fullname(user), user.email)))
                account_list.append(accounts)
            if disabled:
                account_list.append(H4(T("Disabled Accounts")))
                accounts = UL()
                for user in disabled:
                    accounts.append(LI("%s <%s>" % (fullname(user), user.email)))
                account_list.append(accounts)

            output["item"] = account_list
            response.view = self._view(r, "display.html")
            return output

        account = invited[0] if invited else None

        # Look up email to use for invitation
        email = None
        if account:
            email = account.email
        else:
            ctable = s3db.pr_contact
            query = (ctable.pe_id == r.record.pe_id) & \
                    (ctable.contact_method == "EMAIL") & \
                    (ctable.deleted == False)
            contact = db(query).select(ctable.value,
                                       orderby = ctable.priority,
                                       limitby = (0, 1),
                                       ).first()
            if contact:
                email = contact.value

        # Form Fields
        utable = auth_settings.table_user
        dbset = db(utable.id != account.id) if account else db
        formfields = [Field("email",
                            default = email,
                            requires = [IS_EMAIL(error_message = auth_messages.invalid_email),
                                        IS_LOWER(),
                                        IS_NOT_IN_DB(dbset, "%s.email" % utable._tablename,
                                                     error_message = auth_messages.duplicate_email,
                                                     ),
                                        ]
                            ),
                      ]

        # Generate labels (and mark required fields in the process)
        labels, has_required = s3_mark_required(formfields)
        response.s3.has_required = has_required

        # Form buttons
        SEND_INVITATION = T("Send New Invitation") if account else T("Send Invitation")
        buttons = [INPUT(_type = "submit",
                         _value = SEND_INVITATION,
                         ),
                   # TODO cancel-button?
                   ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = "invite",
                               record = None,
                               hidden = {"_next": request.vars._next},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = SEND_INVITATION,
                               #delete_label = auth_messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Identify form for CSS & JS Validation
        form.add_class("send_invitation")

        if form.accepts(request.vars,
                        session,
                        formname = "invite",
                        #onvalidation = auth_settings.register_onvalidation,
                        ):

            error = self.invite_account(r.record, form.vars.email, account=account)
            if error:
                response.error = T("Could not send invitation (%(reason)s)") % {"reason": error}
            else:
                response.confirmation = T("Invitation sent")
        else:
            if account:
                response.warning = T("This organisation has been invited before!")

        output["form"] = form

        response.view = self._view(r, "update.html")

        return output

    # -------------------------------------------------------------------------
    @classmethod
    def invite_account(cls, organisation, email, account=None):

        request = current.request

        data = {"first_name": organisation.name,
                "email": email,
                # TODO language => use default language
                "link_user_to": ["staff"],
                "organisation_id": organisation.id,
                }

        # Generate registration key and activation code
        from uuid import uuid4
        key = str(uuid4())
        code = uuid4().hex[-6:].upper()

        # Add hash to data
        data["registration_key"] = cls.keyhash(key, code)

        if account:
            success = account.update_record(**data)
            if not success:
                return "could not update preliminary account"
        else:
            utable = current.auth.settings.table_user

            # Catch email addresses already used in existing accounts
            if current.db(utable.email == email).select(utable.id,
                                                        limitby = (0, 1),
                                                        ).first():
                return "email address %s already in use" % email

            user_id = utable.insert(**data)
            if user_id:
                ltable = current.s3db.org_organisation_user
                ltable.insert(organisation_id = organisation.id,
                              user_id = user_id,
                              )
            else:
                return "could not create preliminary account"

        # Compose and send invitation email
        # => must use public_url setting because URL() produces a
        #    localhost address when called from CLI or script
        base_url = current.deployment_settings.get_base_public_url()
        appname = request.application
        registration_url = "%s/%s/default/index/register_invited/%s"

        data = {"url": registration_url % (base_url, appname, key),
                "code": code,
                }

        from .notifications import CMSNotifications
        return CMSNotifications.send(email, "InviteOrg", data,
                                     module = "auth",
                                     resource = "user",
                                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def keyhash(key, code):
        """
            Generate a hash of the activation code using
            the registration key

            @param key: the registration key
            @param code: the activation code

            @returns: the hash as string
        """

        crypt = CRYPT(key=key, digest_alg="sha512", salt=None)
        return str(crypt(code.upper())[0])

# =============================================================================
class InvoicePDF(S3Method):
    """
        REST Method to generate an invoice PDF
        - for external accounting archives
    """

    def apply_method(self, r, **attr):
        """
            Generate a PDF of an Invoice

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        if r.representation != "pdf":
            r.error(415, current.ERROR.BAD_FORMAT)
        if not r.record or r.http != "GET":
            r.error(400, current.ERROR.BAD_REQUEST)

        T = current.T

        # Filename to include invoice number if available
        invoice_no = r.record.invoice_no

        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r.resource,
                        request = r,
                        method = "read",
                        pdf_title = T("Invoice"),
                        pdf_filename = invoice_no if invoice_no else None,
                        pdf_header = self.invoice_header,
                        pdf_callback = self.invoice,
                        pdf_footer = self.invoice_footer,
                        pdf_hide_comments = True,
                        pdf_header_padding = 12,
                        pdf_orientation = "Portrait",
                        pdf_table_autogrow = "B",
                        **attr
                        )

    # -------------------------------------------------------------------------
    @classmethod
    def invoice_header(cls, r):
        """
            Generate the invoice header

            @param r: the S3Request
        """

        T = current.T

        table = r.resource.table
        invoice = r.record
        pdata = cls.lookup_header_data(invoice)

        place = [pdata.get(k) for k in ("addr_postcode", "addr_place")]

        header = TABLE(TR(TD(DIV(H4(T("Invoice")), P(" ")),
                             _colspan = 4,
                             ),
                          ),
                       TR(TH(T("Invoicing Party")),
                          TD(pdata.get("organisation", "-")),
                          TH(T("Invoice No.")),
                          TD(table.invoice_no.represent(invoice.invoice_no)),
                          ),
                       TR(TH(T("Address")),
                          TD(pdata.get("addr_street", "-")),
                          TH(table.date.label),
                          TD(table.date.represent(invoice.date)),
                          ),
                       TR(TH(T("Place")),
                          TD(" ".join(v for v in place if v)),
                          TH(T("Payers")),
                          TD(pdata.get("payers")),
                          ),
                       TR(TH(T("Email")),
                          TD(pdata.get("email", "-")),
                          TH(T("Billing Date")),
                          TD(table.date.represent(pdata.get("billing_date"))),
                          ),
                       )

        return header

    # -------------------------------------------------------------------------
    @classmethod
    def invoice(cls, r):
        """
            Generate the invoice body

            @param r: the S3Request
        """

        T = current.T

        table = r.table

        invoice = r.record
        pdata = cls.lookup_body_data(invoice)

        # Lambda to format currency amounts
        amt = lambda v: IS_FLOAT_AMOUNT.represent(v, precision=2, fixed=True)
        currency = invoice.currency

        # Specification of costs
        costs = TABLE(TR(TH(T("No.")),
                         TH(T("Description")),
                         TH(T("Number##count")),
                         TH(T("Unit")),
                         TH(table.price_per_unit.label),
                         TH(T("Total")),
                         TH(table.currency.label),
                         ),
                      TR(TD("1"), # only one line item here
                         TD(pdata.get("title", "-")),
                         TD(str(invoice.quantity_total)),
                         TD(pdata.get("unit", "-")),
                         TD(amt(invoice.price_per_unit)),
                         TD(amt(invoice.amount_receivable)),
                         TD(currency),
                         ),
                      TR(TD(H5(T("Total")), _colspan=5),
                         TD(H5(amt(invoice.amount_receivable))),
                         TD(H5(currency)),
                         ),
                      )

        # Payment Details
        an_field = table.account_number
        an = an_field.represent(invoice.account_number)
        payment_details = TABLE(TR(TH(table.account_holder.label),
                                   TD(invoice.account_holder),
                                   ),
                                TR(TH(an_field.label),
                                   TD(an),
                                   ),
                                TR(TH(table.bank_name.label),
                                   TD(invoice.bank_name),
                                   ),
                                )

        return DIV(H4(" "),
                   H5(T("Specification of Costs")),
                   costs,
                   H4(" "),
                   H4(" "),
                   H5(T("Payable within %(num)s days to") % {"num": 30}),
                   payment_details,
                   )

    # -------------------------------------------------------------------------
    @staticmethod
    def invoice_footer(r):
        """
            Generate the invoice footer

            @param r: the S3Request
        """

        T = current.T

        invoice = r.record

        # Details about who generated the document and when
        user = current.auth.user
        if not user:
            username = T("anonymous user")
        else:
            username = s3_fullname(user)
        now = S3DateTime.datetime_represent(current.request.utcnow, utc=True)
        note = T("Document generated by %(user)s on %(date)s") % {"user": username,
                                                                  "date": now,
                                                                  }
        # Details about the data source
        vhash = invoice.vhash
        try:
            verification = vhash.split("$$")[1][:7]
        except (AttributeError, IndexError):
            verification = T("invalid")

        settings = current.deployment_settings
        source = TABLE(TR(TH(T("System Name")),
                          TD(settings.get_system_name()),
                          ),
                       TR(TH(T("Web Address")),
                          TD(settings.get_base_public_url()),
                          ),
                       TR(TH(T("Data Source")),
                          TD("%s [%s]" % (invoice.uuid, verification)),
                          ),
                       )

        return DIV(P(note), source)

    # -------------------------------------------------------------------------
    @staticmethod
    def lookup_header_data(invoice):
        """
            Look up data for the invoice header

            @param invoice: the invoice record

            @returns: dict with header data
        """

        db = current.db
        s3db = current.s3db

        data = {}

        btable = s3db.fin_voucher_billing
        ptable = s3db.fin_voucher_program
        otable = s3db.org_organisation
        ftable = s3db.org_facility
        ltable = s3db.gis_location
        ctable = s3db.pr_contact

        # Look up the billing date
        query = (btable.id == invoice.billing_id)
        billing = db(query).select(btable.date,
                                   limitby = (0, 1),
                                   ).first()
        if billing:
            data["billing_date"] = billing.date

        # Use the program admin org as "payers"
        query = (ptable.id == invoice.program_id)
        join = otable.on(otable.id == ptable.organisation_id)
        admin_org = db(query).select(otable.name,
                                     join = join,
                                     limitby = (0, 1),
                                     ).first()
        if admin_org:
            data["payers"] = admin_org.name

        # Look up details of the invoicing party
        query = (otable.pe_id == invoice.pe_id) & \
                (otable.deleted == False)
        organisation = db(query).select(otable.id,
                                        otable.name,
                                        limitby = (0, 1),
                                        ).first()
        if organisation:

            data["organisation"] = organisation.name

            # Email address
            query = (ctable.pe_id == invoice.pe_id) & \
                    (ctable.contact_method == "EMAIL") & \
                    (ctable.deleted == False)
            email = db(query).select(ctable.value,
                                     limitby = (0, 1),
                                     ).first()
            if email:
                data["email"] = email.value

            # Facility address
            query = (ftable.organisation_id == organisation.id) & \
                    (ftable.obsolete == False) & \
                    (ftable.deleted == False)
            left = ltable.on(ltable.id == ftable.location_id)
            facility = db(query).select(ftable.email,
                                        ltable.addr_street,
                                        ltable.addr_postcode,
                                        ltable.L3,
                                        ltable.L4,
                                        left = left,
                                        limitby = (0, 1),
                                        orderby = ftable.created_on,
                                        ).first()
            if facility:
                if data.get("email"):
                    # Fallback
                    data["email"] = facility.org_facility.email

                location = facility.gis_location
                data["addr_street"] = location.addr_street or "-"
                data["addr_postcode"] = location.addr_postcode or "-"
                data["addr_place"] = location.L4 or location.L3 or "-"

        return data

    # -------------------------------------------------------------------------
    @staticmethod
    def lookup_body_data(invoice):
        """
            Look up additional data for invoice body

            @param invoice: the invoice record

            @returns: dict with invoice data
        """

        db = current.db
        s3db = current.s3db

        ptable = s3db.fin_voucher_program

        query = (ptable.id == invoice.program_id) & \
                (ptable.deleted == False)
        program = db(query).select(ptable.id,
                                   ptable.name,
                                   ptable.unit,
                                   limitby = (0, 1),
                                   ).first()
        if program:
            data = {"title": program.name,
                    "unit": program.unit,
                    }
        else:
            data = {}

        return data

# END =========================================================================
