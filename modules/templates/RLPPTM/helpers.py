# -*- coding: utf-8 -*-

"""
    Helper functions and classes for RLPPTM template

    @license: MIT
"""

import json

from gluon import current, Field, URL, \
                  CRYPT, IS_EMAIL, IS_IN_SET, IS_LOWER, IS_NOT_IN_DB, \
                  SQLFORM, A, DIV, H4, H5, I, INPUT, LI, P, SPAN, TABLE, TD, TH, TR, UL

from s3 import ICON, IS_FLOAT_AMOUNT, JSONERRORS, S3DateTime, \
               S3Method, S3Represent, s3_fullname, s3_mark_required, s3_str

from s3db.pr import pr_PersonRepresentContact
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
def get_managed_facilities(role="ORG_ADMIN", public_only=True):
    """
        Get test stations managed by the current user

        @param role: the user role to consider
        @param public_only: only include sites with PUBLIC=Y tag

        @returns: list of site_ids
    """


    s3db = current.s3db

    ftable = s3db.org_facility
    query = (ftable.obsolete == False) & \
            (ftable.deleted == False)

    realms = get_role_realms(role)
    if realms:
        query = (ftable.realm_entity.belongs(realms)) & query
    elif realms is not None:
        # User does not have the required role, or at least not for any realms
        return realms

    if public_only:
        ttable = s3db.org_site_tag
        join = ttable.on((ttable.site_id == ftable.site_id) & \
                         (ttable.tag == "PUBLIC") & \
                         (ttable.deleted == False))
        query &= (ttable.value == "Y")
    else:
        join = None

    sites = current.db(query).select(ftable.site_id,
                                     cache = s3db.cache,
                                     join = join,
                                     )
    return [s.site_id for s in sites]

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
    from s3db.pr import pr_realm_users
    users = pr_realm_users(pe_id) if pe_id else None
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

        @status: obsolete, test results shall be reported for all projects
    """

    permitted_realms = current.auth.permission.permitted_realms
    realms = permitted_realms("disease_case_diagnostics",
                              method = "create",
                              c = "disease",
                              f = "case_diagnostics",
                              )

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

    user = auth.user
    if user:
        # Look up the role ID
        gtable = auth.settings.table_group
        query = (gtable.uuid == "VOUCHER_PROVIDER")
        role = current.db(query).select(gtable.id,
                                        cache = current.s3db.cache,
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
            from s3db.pr import pr_default_realms
            role_realms = pr_default_realms(user["pe_id"])

        return debit.pe_id in role_realms

    else:
        # No user
        return False

# -----------------------------------------------------------------------------
def configure_binary_tags(resource, tag_components):
    """
        Configure representation of binary tags

        @param resource: the S3Resource
        @param tag_components: tuple|list of filtered tag component aliases
    """

    T = current.T

    binary_tag_opts = {"Y": T("Yes"), "N": T("No")}

    for cname in tag_components:
        component = resource.components.get(cname)
        if component:
            ctable = component.table
            field = ctable.value
            field.default = "N"
            field.requires = IS_IN_SET(binary_tag_opts, zero=None)
            field.represent = lambda v, row=None: binary_tag_opts.get(v, "-")

# -----------------------------------------------------------------------------
def workflow_tag_represent(options):
    """
        Color-coded and icon-supported representation of
        facility approval workflow tags

        @param options: the tag options as dict {value: label}
    """

    icons = {"REVISE": "fa fa-exclamation-triangle",
             "REVIEW": "fa fa-hourglass",
             "APPROVED": "fa fa-check",
             "N": "fa fa-minus-circle",
             "Y": "fa fa-check",
             }
    css_classes = {"REVISE": "workflow-red",
                   "REVIEW": "workflow-amber",
                   "APPROVED": "workflow-green",
                   "N": "workflow-red",
                   "Y": "workflow-green",
                   }

    def represent(value, row=None):

        label = DIV(_class="approve-workflow")
        color = css_classes.get(value)
        if color:
            label.add_class(color)
        icon = icons.get(value)
        if icon:
            label.append(I(_class=icon))
        label.append(options.get(value, "-"))

        return label

    return represent

# -----------------------------------------------------------------------------
def configure_workflow_tags(resource, role="applicant", record_id=None):
    """
        Configure facility approval workflow tags

        @param resource: the org_facility resource
        @param role: the user's role in the workflow (applicant|approver)
        @param record_id: the facility record ID

        @returns: the list of visible workflow tags [(label, selector)]
    """

    T = current.T
    components = resource.components

    visible_tags = []

    # Configure STATUS tag
    status_tag_opts = {"REVISE": T("Completion/Adjustment Required"),
                       "READY": T("Ready for Review"),
                       "REVIEW": T("Review Pending"),
                       "APPROVED": T("Approved##actionable"),
                       }
    selectable = None
    status_visible = False
    review_tags_visible = False

    if role == "applicant" and record_id:
        # Check current status
        db = current.db
        s3db = current.s3db
        ftable = s3db.org_facility
        ttable = s3db.org_site_tag
        join = ftable.on((ftable.site_id == ttable.site_id) & \
                         (ftable.id == record_id))
        query = (ttable.tag == "STATUS") & (ttable.deleted == False)
        row = db(query).select(ttable.value, join=join, limitby=(0, 1)).first()
        if row:
            if row.value == "REVISE":
                review_tags_visible = True
                selectable = (row.value, "READY")
            elif row.value == "REVIEW":
                review_tags_visible = True
        status_visible = True

    component = components.get("status")
    if component:
        ctable = component.table
        field = ctable.value
        field.default = "REVISE"
        field.readable = status_visible
        if status_visible:
            if selectable:
                selectable_statuses = [(status, status_tag_opts[status])
                                       for status in selectable]
                field.requires = IS_IN_SET(selectable_statuses, zero=None)
                field.writable = True
            else:
                field.writable = False
            visible_tags.append((T("Processing Status"), "status.value"))
        field.represent = workflow_tag_represent(status_tag_opts)

    # Configure review tags
    review_tag_opts = (("REVISE", T("Completion/Adjustment Required")),
                       ("REVIEW", T("Review Pending")),
                       ("APPROVED", T("Approved##actionable")),
                       )
    selectable = review_tag_opts if role == "approver" else None

    review_tags = (("mpav", T("MPAV Qualification")),
                   ("hygiene", T("Hygiene Plan")),
                   ("layout", T("Facility Layout Plan")),
                   )
    for cname, label in review_tags:
        component = components.get(cname)
        if component:
            ctable = component.table
            field = ctable.value
            field.default = "REVISE"
            if selectable:
                field.requires = IS_IN_SET(selectable, zero=None, sort=False)
                field.readable = field.writable = True
            else:
                field.readable = review_tags_visible
                field.writable = False
            if field.readable:
                visible_tags.append((label, "%s.value" % cname))
            field.represent = workflow_tag_represent(dict(review_tag_opts))

    # Configure PUBLIC tag
    binary_tag_opts = {"Y": T("Yes"),
                       "N": T("No"),
                       }
    selectable = binary_tag_opts if role == "approver" else None

    component = resource.components.get("public")
    if component:
        ctable = component.table
        field = ctable.value
        field.default = "N"
        if selectable:
            field.requires = IS_IN_SET(selectable, zero=None)
            field.writable = True
        else:
            field.requires = IS_IN_SET(binary_tag_opts, zero=None)
            field.writable = False
        field.represent = workflow_tag_represent(binary_tag_opts)
    visible_tags.append((T("In Public Registry"), "public.value"))
    visible_tags.append("site_details.authorisation_advice")

    return visible_tags

# -----------------------------------------------------------------------------
def facility_approval_workflow(site_id):
    """
        Update facility approval workflow tags

        @param site_id: the site ID
    """

    db = current.db
    s3db = current.s3db

    workflow = ("STATUS", "MPAV", "HYGIENE", "LAYOUT", "PUBLIC")
    review = ("MPAV", "HYGIENE", "LAYOUT")

    # Get all tags for site
    ttable = s3db.org_site_tag
    query = (ttable.site_id == site_id) & \
            (ttable.tag.belongs(workflow)) & \
            (ttable.deleted == False)
    rows = db(query).select(ttable.id,
                            ttable.tag,
                            ttable.value,
                            )
    tags = {row.tag: row.value for row in rows}

    if any(k not in tags for k in workflow):
        ftable = s3db.org_facility
        facility = db(ftable.site_id == site_id).select(ftable.id,
                                                        limitby = (0, 1),
                                                        ).first()
        if facility:
            add_facility_default_tags(facility)
            facility_approval_workflow(site_id)

    update = {}
    notify = False

    status = tags.get("STATUS")
    if status == "REVISE":
        if all(tags[k] == "APPROVED" for k in review):
            update["PUBLIC"] = "Y"
            update["STATUS"] = "APPROVED"
            notify = True
        elif any(tags[k] == "REVIEW" for k in review):
            update["PUBLIC"] = "N"
            update["STATUS"] = "REVIEW"
        else:
            update["PUBLIC"] = "N"
            # Keep status REVISE

    elif status == "READY":
        update["PUBLIC"] = "N"
        if all(tags[k] == "APPROVED" for k in review):
            for k in review:
                update[k] = "REVIEW"
        else:
            for k in review:
                if tags[k] == "REVISE":
                    update[k] = "REVIEW"
        update["STATUS"] = "REVIEW"

    elif status == "REVIEW":
        if all(tags[k] == "APPROVED" for k in review):
            update["PUBLIC"] = "Y"
            update["STATUS"] = "APPROVED"
            notify = True
        elif any(tags[k] == "REVIEW" for k in review):
            update["PUBLIC"] = "N"
            # Keep status REVIEW
        elif any(tags[k] == "REVISE" for k in review):
            update["PUBLIC"] = "N"
            update["STATUS"] = "REVISE"
            notify = True

    elif status == "APPROVED":
        if any(tags[k] == "REVIEW" for k in review):
            update["PUBLIC"] = "N"
            update["STATUS"] = "REVIEW"
        elif any(tags[k] == "REVISE" for k in review):
            update["PUBLIC"] = "N"
            update["STATUS"] = "REVISE"
            notify = True

    for row in rows:
        key = row.tag
        if key in update:
            row.update_record(value=update[key])

    T = current.T

    public = update.get("PUBLIC")
    if public and public != tags["PUBLIC"]:
        if public == "Y":
            msg = T("Facility added to public registry")
        else:
            msg = T("Facility removed from public registry pending review")
        current.response.information = msg

    # Send Notifications
    if notify:
        tags.update(update)
        msg = facility_review_notification(site_id, tags)
        if msg:
            current.response.warning = \
                T("Test station could not be notified: %(error)s") % {"error": msg}
        else:
            current.response.flash = \
                T("Test station notified")

# -----------------------------------------------------------------------------
def facility_review_notification(site_id, tags):
    """
        Notify the OrgAdmin of a test station about the status of the review

        @param site_id: the test facility site ID
        @param tags: the current workflow tags

        @returns: error message on error, else None
    """

    db = current.db
    s3db = current.s3db

    # Lookup the facility
    ftable = s3db.org_facility
    query = (ftable.site_id == site_id) & \
            (ftable.deleted == False)
    facility = db(query).select(ftable.id,
                                ftable.name,
                                ftable.organisation_id,
                                limitby = (0, 1),
                                ).first()
    if not facility:
        return "Facility not found"

    organisation_id = facility.organisation_id
    if not organisation_id:
        return "Organisation not found"

    # Find the OrgAdmin email addresses
    email = get_role_emails("ORG_ADMIN",
                            organisation_id = organisation_id,
                            )
    if not email:
        return "No Organisation Administrator found"

    # Data for the notification email
    data = {"name": facility.name,
            "url": URL(c = "org",
                       f = "organisation",
                       args = [organisation_id, "facility", facility.id],
                       host = True,
                       ),
            }

    status = tags.get("STATUS")

    if status == "REVISE":
        template = "FacilityReview"

        # Add advice
        dtable = s3db.org_site_details
        query = (dtable.site_id == site_id) & \
                (dtable.deleted == False)
        details = db(query).select(dtable.authorisation_advice,
                                   limitby = (0, 1),
                                   ).first()
        if details and details.authorisation_advice:
            data["advice"] = details.authorisation_advice

        # Add explanations for relevant requirements
        review = (("MPAV", "FacilityMPAVRequirements"),
                  ("HYGIENE", "FacilityHygienePlanRequirements"),
                  ("LAYOUT", "FacilityLayoutRequirements"),
                  )
        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "org") & \
                         (ltable.resource == "facility") & \
                         (ltable.deleted == False))
        explanations = []
        for tag, requirements in review:
            if tags.get(tag) == "REVISE":
                query = (ctable.name == requirements) & \
                        (ctable.deleted == False)
                row = db(query).select(ctable.body,
                                       join = join,
                                       limitby = (0, 1),
                                       ).first()
                if row:
                    explanations.append(row.body)
        data["explanations"] = "\n\n".join(explanations) if explanations else "-"

    elif status == "APPROVED":
        template = "FacilityApproved"

    else:
        # No notifications for this status
        return "invalid status"

    # Lookup email address of current user
    from .notifications import CMSNotifications
    auth = current.auth
    if auth.user:
        cc = CMSNotifications.lookup_contact(auth.user.pe_id)
    else:
        cc = None

    # Send CMS Notification FacilityReview
    return CMSNotifications.send(email,
                                 template,
                                 data,
                                 module = "org",
                                 resource = "facility",
                                 cc = cc,
                                 )

# -----------------------------------------------------------------------------
def add_organisation_default_tags(organisation_id):
    """
        Add default tags to a new organisation

        @param organisation_id: the organisation record ID
    """

    db = current.db
    s3db = current.s3db

    # Add default tags
    otable = s3db.org_organisation
    ttable = s3db.org_organisation_tag
    dttable = ttable.with_alias("delivery")
    ittable = ttable.with_alias("orgid")

    left = [dttable.on((dttable.organisation_id == otable.id) & \
                       (dttable.tag == "DELIVERY") & \
                       (dttable.deleted == False)),
            ittable.on((ittable.organisation_id == otable.id) & \
                       (ittable.tag == "OrgID") & \
                       (ittable.deleted == False)),
            ]
    query = (otable.id == organisation_id)
    row = db(query).select(otable.id,
                           otable.uuid,
                           dttable.id,
                           ittable.id,
                           left = left,
                           limitby = (0, 1),
                           ).first()
    if row:
        org = row.org_organisation

        # Add DELIVERY-tag
        dtag = row.delivery
        if not dtag.id:
            ttable.insert(organisation_id = org.id,
                          tag = "DELIVERY",
                          value = "DIRECT",
                          )

        # Add OrgID-tag
        itag = row.orgid
        if not itag.id:
            try:
                uid = int(org.uuid[9:14], 16)
            except (TypeError, ValueError):
                import uuid
                uid = int(uuid.uuid4().urn[9:14], 16)
            value = "%06d%04d" % (uid, org.id)
            ttable.insert(organisation_id = org.id,
                          tag = "OrgID",
                          value = value,
                          )

# -----------------------------------------------------------------------------
def add_facility_default_tags(facility_id, approve=False):
    """
        Add default tags to a new facility

        @param facility_id: the facility record ID
        @param approve: whether called from approval-workflow
    """

    db = current.db
    s3db = current.s3db

    ftable = s3db.org_facility
    ttable = s3db.org_site_tag

    workflow = ("PUBLIC", "MPAV", "HYGIENE", "LAYOUT", "STATUS")

    left = ttable.on((ttable.site_id == ftable.site_id) & \
                     (ttable.tag.belongs(workflow)) & \
                     (ttable.deleted == False))
    query = (ftable.id == facility_id)
    rows = db(query).select(ftable.site_id,
                            ttable.id,
                            ttable.tag,
                            ttable.value,
                            left = left,
                            )
    if not rows:
        return
    else:
        site_id = rows.first().org_facility.site_id

    existing = {row.org_site_tag.tag: row.org_site_tag.value
                    for row in rows if row.org_site_tag.id}
    public = existing.get("PUBLIC") == "Y" or approve

    review = ("MPAV", "HYGIENE", "LAYOUT")
    for tag in workflow:
        if tag in existing:
            continue
        elif tag == "PUBLIC":
            default = "Y" if public else "N"
        elif tag == "STATUS":
            if any(existing[t] == "REVISE" for t in review):
                default = "REVISE"
            elif any(existing[t] == "REVIEW" for t in review):
                default = "REVIEW"
            else:
                default = "APPROVED" if public else "REVIEW"
        else:
            default = "APPROVED" if public else "REVISE"
        ttable.insert(site_id = site_id,
                      tag = tag,
                      value = default,
                      )
        existing[tag] = default

# -----------------------------------------------------------------------------
def set_facility_code(facility_id):
    """
        Generate and set a unique facility code

        @param facility_id: the facility ID

        @returns: the facility code
    """

    db = current.db
    s3db = current.s3db

    table = s3db.org_facility
    query = (table.id == facility_id)

    facility = db(query).select(table.id,
                                table.uuid,
                                table.code,
                                limitby = (0, 1),
                                ).first()

    if not facility or facility.code:
        return None

    try:
        uid = int(facility.uuid[9:14], 16) % 1000000
    except (TypeError, ValueError):
        import uuid
        uid = int(uuid.uuid4().urn[9:14], 16) % 1000000

    # Generate code
    import random
    suffix = "".join(random.choice("ABCFGHKLNPRSTWX12456789") for _ in range(3))
    code = "%06d-%s" % (uid, suffix)

    facility.update_record(code=code)

    return code

# -----------------------------------------------------------------------------
def applicable_org_types(organisation_id, group=None, represent=False):
    """
        Look up organisation types by OrgGroup-tag

        @param organisation_id: the record ID of an existing organisation
        @param group: alternatively, the organisation group name
        @param represent: include type labels in the result

        @returns: a list of organisation type IDs, for filtering,
                  or a dict {type_id: label}, for selecting
    """

    db = current.db
    s3db = current.s3db

    ttable = s3db.org_organisation_type_tag

    if organisation_id:
        # Look up the org groups of this record
        gtable = s3db.org_group
        mtable = s3db.org_group_membership
        join = gtable.on(gtable.id == mtable.group_id)
        query = (mtable.organisation_id == organisation_id) & \
                (mtable.deleted == False)
        rows = db(query).select(gtable.name, join=join)
        groups = {row.name for row in rows}
        q = (ttable.value.belongs(groups))

        # Look up the org types the record is currently linked to
        ltable = s3db.org_organisation_organisation_type
        query = (ltable.organisation_id == organisation_id) & \
                (ltable.deleted == False)
        rows = db(query).select(ltable.organisation_type_id)
        current_types = {row.organisation_type_id for row in rows}

    elif group:
        # Use group name as-is
        q = (ttable.value == group)

    # Look up all types tagged for this group
    query = (ttable.tag == "OrgGroup") & q & \
            (ttable.deleted == False)
    rows = db(query).select(ttable.organisation_type_id,
                            cache = s3db.cache,
                            )
    type_ids = {row.organisation_type_id for row in rows}

    if organisation_id:
        # Add the org types the record is currently linked to
        type_ids |= current_types

    if represent:
        labels = ttable.organisation_type_id.represent
        if hasattr(labels, "bulk"):
            labels.bulk(list(type_ids))
        output = {str(t): labels(t) for t in type_ids}
    else:
        output = list(type_ids)

    return output

# =============================================================================
def facility_map_popup(record):
    """
        Custom map popup for facilities

        @param record: the facility record (Row)

        @returns: the map popup contents as DIV
    """

    db = current.db
    s3db = current.s3db

    T = current.T

    table = s3db.org_facility

    # Custom Map Popup
    title = H4(record.name, _class="map-popup-title")

    details = TABLE(_class="map-popup-details")
    append = details.append

    def formrow(label, value, represent=None):
        return TR(TD("%s:" % label, _class="map-popup-label"),
                  TD(represent(value) if represent else value),
                  )

    # Address
    gtable = s3db.gis_location
    query = (gtable.id == record.location_id)
    location = db(query).select(gtable.addr_street,
                                gtable.addr_postcode,
                                gtable.L4,
                                gtable.L3,
                                limitby = (0, 1),
                                ).first()

    if location.addr_street:
        append(formrow(gtable.addr_street.label, location.addr_street))
    place = location.L4 or location.L3 or "?"
    if location.addr_postcode:
        place = "%s %s" % (location.addr_postcode, place)
    append(formrow(T("Place"), place))

    # Phone number
    phone = record.phone1
    if phone:
        append(formrow(T("Phone"), phone))

    # Email address (as hyperlink)
    email = record.email
    if email:
        append(formrow(table.email.label, A(email, _href="mailto:%s" % email)))

    # Opening Times
    opening_times = record.opening_times
    if opening_times:
        append(formrow(table.opening_times.label, opening_times))

    # Site services
    stable = s3db.org_service
    ltable = s3db.org_service_site
    join = stable.on(stable.id == ltable.service_id)
    query = (ltable.site_id == record.site_id) & \
            (ltable.deleted == False)
    rows = db(query).select(stable.name, join=join)
    services = [row.name for row in rows]
    if services:
        append(formrow(T("Services"), ", ".join(services)))

    # Comments
    if record.comments:
        append(formrow(table.comments.label,
                        record.comments,
                        represent = table.comments.represent,
                        ))

    return DIV(title, details, _class="map-popup")

# =============================================================================
class ServiceListRepresent(S3Represent):

    always_list = True

    def render_list(self, value, labels, show_link=True):
        """
            Helper method to render list-type representations from
            bulk()-results.

            @param value: the list
            @param labels: the labels as returned from bulk()
            @param show_link: render references as links, should
                              be the same as used with bulk()
        """

        show_link = show_link and self.show_link

        values = [v for v in value if v is not None]
        if not len(values):
            return ""

        if show_link:
            labels_ = (labels[v] if v in labels else self.default for v in values)
        else:
            labels_ = sorted(s3_str(labels[v]) if v in labels else self.default for v in values)

        html = UL(_class="service-list")
        for label in labels_:
            html.append(LI(label))

        return html

# =============================================================================
class OrganisationRepresent(S3Represent):
    """
        Custom representation of organisations showing the organisation type
        - relevant for facility approval
    """

    def __init__(self, show_type=True, show_link=True):

        super(OrganisationRepresent, self).__init__(lookup = "org_organisation",
                                                    fields = ["name",],
                                                    show_link = show_link,
                                                    )
        self.show_type = show_type
        self.org_types = {}
        self.type_names = {}

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for organisation rows, does a
            left join with the parent organisation. Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the organisation IDs
        """

        db = current.db
        s3db = current.s3db

        otable = s3db.org_organisation

        count = len(values)
        if count == 1:
            query = (otable.id == values[0])
        else:
            query = (otable.id.belongs(values))

        rows = db(query).select(otable.id,
                                otable.name,
                                limitby = (0, count),
                                )

        if self.show_type:
            ltable = s3db.org_organisation_organisation_type
            if count == 1:
                query = (ltable.organisation_id == values[0])
            else:
                query = (ltable.organisation_id.belongs(values))
            query &= (ltable.deleted == False)
            types = db(query).select(ltable.organisation_id,
                                     ltable.organisation_type_id,
                                     )

            all_types = set()
            org_types = self.org_types = {}

            for t in types:

                type_id = t.organisation_type_id
                all_types.add(type_id)

                organisation_id = t.organisation_id
                if organisation_id not in org_types:
                    org_types[organisation_id] = {type_id}
                else:
                    org_types[organisation_id].add(type_id)

            if all_types:
                ttable = s3db.org_organisation_type
                query = ttable.id.belongs(all_types)
                types = db(query).select(ttable.id,
                                         ttable.name,
                                         limitby = (0, len(all_types)),
                                         )
                self.type_names = {t.id: t.name for t in types}

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row, prefix=None):
        """
            Represent a single Row

            @param row: the org_organisation Row
            @param prefix: the hierarchy prefix (unused here)
        """

        name = s3_str(row.name)

        if self.show_type:

            T = current.T

            type_ids = self.org_types.get(row.id)
            if type_ids:
                type_names = self.type_names
                types = [s3_str(T(type_names[t]))
                         for t in type_ids if t in type_names
                         ]
                name = "%s (%s)" % (name, ", ".join(types))

        return name

# =============================================================================
class ContactRepresent(pr_PersonRepresentContact):
    """
        Visually enhanced version of pr_PersonRepresentContact
    """

    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        output = DIV(SPAN(s3_fullname(row),
                          _class = "contact-name",
                          ),
                     _class = "contact-repr",
                     )

        try:
            pe_id = row.pe_id
        except AttributeError:
            pass
        else:
            if self.show_email:
                email = self._email.get(pe_id)
            if self.show_phone:
                phone = self._phone.get(pe_id)
            if email or phone:
                details = DIV(_class="contact-details")
                if email:
                    details.append(DIV(ICON("mail"),
                                       SPAN(A(email,
                                              _href="mailto:%s" % email,
                                              ),
                                            _class = "contact-email"),
                                       _class = "contact-info",
                                       ))
                if phone:
                    details.append(DIV(ICON("phone"),
                                       SPAN(phone,
                                            _class = "contact-phone"),
                                       _class = "contact-info",
                                       ))
                output.append(details)

        return output

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

# =============================================================================
class ClaimPDF(S3Method):
    """
        REST Method to generate a claim PDF
        - for external accounting archives
    """

    def apply_method(self, r, **attr):
        """
            Generate a PDF of a Claim

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        if r.representation != "pdf":
            r.error(415, current.ERROR.BAD_FORMAT)
        if not r.record or r.http != "GET":
            r.error(400, current.ERROR.BAD_REQUEST)

        T = current.T

        # Filename to include invoice number if available
        invoice_no = self.invoice_number(r.record)

        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r.resource,
                        request = r,
                        method = "read",
                        pdf_title = T("Compensation Claim"),
                        pdf_filename = invoice_no if invoice_no else None,
                        pdf_header = self.claim_header,
                        pdf_callback = self.claim,
                        pdf_footer = self.claim_footer,
                        pdf_hide_comments = True,
                        pdf_header_padding = 12,
                        pdf_orientation = "Portrait",
                        pdf_table_autogrow = "B",
                        **attr
                        )

    # -------------------------------------------------------------------------
    @staticmethod
    def invoice_number(record):

        invoice_id = record.invoice_id
        if invoice_id:
            s3db = current.s3db
            itable = s3db.fin_voucher_invoice
            query = (itable.id == invoice_id)
            invoice = current.db(query).select(itable.invoice_no,
                                               cache = s3db.cache,
                                               limitby = (0, 1),
                                               ).first()
        else:
            invoice = None

        return invoice.invoice_no if invoice else None

    # -------------------------------------------------------------------------
    @classmethod
    def claim_header(cls, r):
        """
            Generate the claim header

            @param r: the S3Request
        """

        T = current.T

        table = r.resource.table
        itable = current.s3db.fin_voucher_invoice

        claim = r.record
        pdata = cls.lookup_header_data(claim)

        place = [pdata.get(k) for k in ("addr_postcode", "addr_place")]

        status = " " if claim.invoice_id else "(%s)" % T("not invoiced yet")

        header = TABLE(TR(TD(DIV(H4(T("Compensation Claim")), P(status)),
                             _colspan = 4,
                             ),
                          ),
                       TR(TH(T("Invoicing Party")),
                          TD(pdata.get("organisation", "-")),
                          TH(T("Invoice No.")),
                          TD(itable.invoice_no.represent(pdata.get("invoice_no"))),
                          ),
                       TR(TH(T("Address")),
                          TD(pdata.get("addr_street", "-")),
                          TH(itable.date.label),
                          TD(itable.date.represent(pdata.get("invoice_date"))),
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
    def claim(cls, r):
        """
            Generate the claim body

            @param r: the S3Request
        """

        T = current.T

        table = r.table

        claim = r.record
        pdata = cls.lookup_body_data(claim)

        # Lambda to format currency amounts
        amt = lambda v: IS_FLOAT_AMOUNT.represent(v, precision=2, fixed=True)
        currency = claim.currency

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
                         TD(str(claim.quantity_total)),
                         TD(pdata.get("unit", "-")),
                         TD(amt(claim.price_per_unit)),
                         TD(amt(claim.amount_receivable)),
                         TD(currency),
                         ),
                      TR(TD(H5(T("Total")), _colspan=5),
                         TD(H5(amt(claim.amount_receivable))),
                         TD(H5(currency)),
                         ),
                      )

        # Payment Details
        an_field = table.account_number
        an = an_field.represent(claim.account_number)
        payment_details = TABLE(TR(TH(table.account_holder.label),
                                   TD(claim.account_holder),
                                   ),
                                TR(TH(an_field.label),
                                   TD(an),
                                   ),
                                TR(TH(table.bank_name.label),
                                   TD(claim.bank_name),
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
    def claim_footer(r):
        """
            Generate the claim footer

            @param r: the S3Request
        """

        T = current.T

        claim = r.record

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
        vhash = claim.vhash
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
                          TD("%s [%s]" % (claim.uuid, verification)),
                          ),
                       )

        return DIV(P(note), source)

    # -------------------------------------------------------------------------
    @staticmethod
    def lookup_header_data(claim):
        """
            Look up data for the claim header

            @param claim: the claim record

            @returns: dict with header data
        """

        db = current.db
        s3db = current.s3db

        data = {}

        btable = s3db.fin_voucher_billing
        itable = s3db.fin_voucher_invoice
        ptable = s3db.fin_voucher_program
        otable = s3db.org_organisation
        ftable = s3db.org_facility
        ltable = s3db.gis_location
        ctable = s3db.pr_contact

        # Look up the billing date
        query = (btable.id == claim.billing_id)
        billing = db(query).select(btable.date,
                                   limitby = (0, 1),
                                   ).first()
        if billing:
            data["billing_date"] = billing.date

        # Look up invoice details
        if claim.invoice_id:
            query = (itable.id == claim.invoice_id)
            invoice = db(query).select(itable.date,
                                       itable.invoice_no,
                                       limitby = (0, 1),
                                       ).first()
            if invoice:
                data["invoice_no"] = invoice.invoice_no
                data["invoice_date"] = invoice.date

        # Use the program admin org as "payers"
        query = (ptable.id == claim.program_id)
        join = otable.on(otable.id == ptable.organisation_id)
        admin_org = db(query).select(otable.name,
                                     join = join,
                                     limitby = (0, 1),
                                     ).first()
        if admin_org:
            data["payers"] = admin_org.name

        # Look up details of the invoicing party
        query = (otable.pe_id == claim.pe_id) & \
                (otable.deleted == False)
        organisation = db(query).select(otable.id,
                                        otable.name,
                                        limitby = (0, 1),
                                        ).first()
        if organisation:

            data["organisation"] = organisation.name

            # Email address
            query = (ctable.pe_id == claim.pe_id) & \
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
    def lookup_body_data(claim):
        """
            Look up additional data for claim body

            @param claim: the claim record

            @returns: dict with claim data
        """

        db = current.db
        s3db = current.s3db

        ptable = s3db.fin_voucher_program

        query = (ptable.id == claim.program_id) & \
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

# =============================================================================
class TestFacilityInfo(S3Method):
    """
        REST Method to report details/activities of a test facility
    """

    def apply_method(self, r, **attr):
        """
            Report test facility information

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        if r.http == "POST":
            if r.representation == "json":
                output = self.facility_info(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def facility_info(r, **attr):
        """
            Respond to a POST .json request, request body format:

                {"client": "CLIENT",        - the client identity (ocert)
                 "appkey": "APPKEY",        - the client app key (ocert)
                 "code": "FACILITY-CODE",   - the facility code
                 "report": ["start","end"], - the date interval to report
                                              activities for (optional)
                                              (ISO-format dates YYYY-MM-DD)
                }

            Output format:
                {"code": "FACILITY-CODE",   - echoed from input
                 "name": "FACILITY-NAME",   - the facility name
                 "phone": "phone #",        - the facility phone number
                 "email": "email",          - the facility email address
                 "organisation":
                    {"name": "ORG-NAME",    - the organisation name
                     "type": "ORG-TYPE",    - the organisation type
                     "website": "URL"       - the organisation website URL
                     },
                 "location":
                    {"L1": "L1-NAME",       - the L1 name (state)
                     "L2": "L2-NAME",       - the L2 name (district)
                     "L3": "L3-NAME",       - the L3 name (commune/city)
                     "L4": "L4-NAME",       - the L4 name (village/town)
                     "address": "STREET",   - the street address
                     "postcode": "XXXXX"    - the postcode
                     },
                 "report": ["start","end"], - echoed from input, ISO-format dates YYYY-MM-DD
                 "activity":
                    {"tests":59             - the total number of tests reported for the period
                    }
                 }
        """

        settings = current.deployment_settings

        # Get the configured, permitted clients
        ocert = settings.get_custom("ocert")
        if not ocert:
            r.error(501, current.ERROR.METHOD_DISABLED)

        # Read the body JSON of the request
        body = r.body
        body.seek(0)
        try:
            s = body.read().decode("utf-8")
        except (ValueError, AttributeError, UnicodeDecodeError):
            r.error(400, current.ERROR.BAD_REQUEST)
        try:
            ref = json.loads(s)
        except JSONERRORS:
            r.error(400, current.ERROR.BAD_REQUEST)

        # Verify the client
        client = ref.get("client")
        if not client or client not in ocert:
            r.error(403, current.ERROR.NOT_PERMITTED)
        key, _ = ocert.get(client)
        if key:
            appkey = ref.get("appkey")
            if not appkey or appkey.upper() != key.upper():
                r.error(403, current.ERROR.NOT_PERMITTED)

        # Identify the facility
        db = current.db
        s3db = current.s3db

        table = s3db.org_facility
        record = r.record
        if record:
            query = (table.id == record.id)
        else:
            code = ref.get("code")
            if not code:
                r.error(400, current.ERROR.BAD_REQUEST)
            query = (table.code.upper() == code.upper())

        query &= (table.deleted == False)
        facility = db(query).select(table.code,
                                    table.name,
                                    table.phone1,
                                    table.email,
                                    table.website,
                                    table.organisation_id,
                                    table.location_id,
                                    table.site_id,
                                    limitby = (0, 1),
                                    ).first()

        if not facility:
            r.error(404, current.ERROR.BAD_RECORD)

        # Prepare facility info
        output = {"code": facility.code,
                  "name": facility.name,
                  "phone": facility.phone1,
                  "email": facility.email,
                  }

        # Look up organisation data
        otable = s3db.org_organisation
        ttable = s3db.org_organisation_type
        ltable = s3db.org_organisation_organisation_type
        left = [ttable.on((ltable.organisation_id == otable.id) & \
                          (ltable.deleted == False) & \
                          (ttable.id == ltable.organisation_type_id)),
                ]
        query = (otable.id == facility.organisation_id) & \
                (otable.deleted == False)
        row = db(query).select(otable.name,
                               otable.website,
                               ttable.name,
                               left = left,
                               limitby = (0, 1),
                               ).first()
        if row:
            organisation = row.org_organisation
            orgtype = row.org_organisation_type
            orgdata = {"name": organisation.name,
                       "type": orgtype.name,
                       "website": organisation.website,
                       }
            output["organisation"] = orgdata

        # Look up location data
        ltable = s3db.gis_location
        query = (ltable.id == facility.location_id) & \
                (ltable.deleted == False)
        row = db(query).select(ltable.L1,
                               ltable.L2,
                               ltable.L3,
                               ltable.L4,
                               ltable.addr_street,
                               ltable.addr_postcode,
                               limitby = (0, 1),
                               ).first()
        if row:
            locdata = {"L1": row.L1,
                       "L2": row.L2,
                       "L3": row.L3,
                       "L4": row.L4,
                       "address": row.addr_street,
                       "postcode": row.addr_postcode,
                       }
            output["location"] = locdata

        # Look up activity data
        report = ref.get("report")
        if isinstance(report, list) and len(report) == 2:
            parse_date = current.calendar.parse_date
            start, end = parse_date(s3_str(report[0])), \
                         parse_date(s3_str(report[1]))
            if start and end:
                if start > end:
                    start, end = end, start
                table = s3db.disease_testing_report
                query = (table.site_id == facility.site_id) & \
                        (table.date >= start) & \
                        (table.date <= end) & \
                        (table.deleted == False)
                total = table.tests_total.sum()
                row = db(query).select(total).first()
                tests_total = row[total]
                if not tests_total:
                    tests_total = 0
                output["report"] = [start.isoformat(), end.isoformat()]
                output["activity"] = {"tests": tests_total}
            else:
                r.error(400, "Invalid date format in report parameter")
        else:
            r.error(400, "Invalid report parameter format")

        # Return as JSON
        response = current.response
        if response:
            response.headers["Content-Type"] = "application/json; charset=utf-8"
        return json.dumps(output, separators=(",", ":"), ensure_ascii=False)

# END =========================================================================
