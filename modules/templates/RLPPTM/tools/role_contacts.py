# -*- coding: utf-8 -*-
#
# Helper Script to get a list of organisation contacts (email addresses)
# with a certain user role
#
# RLPPTM Template Version 1.5
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/tools/role_contacts.py
#
import os
import sys

from s3 import s3_format_datetime

from templates.RLPPTM.config import SCHOOLS, TESTSTATIONS

org_group = TESTSTATIONS
project = "COVID-19 Tests für Alle"
include = "ORG_ADMIN"
exclude = "VOUCHER_ISSUER"

# Override auth (disables all permission checks)
auth.override = True

# Failed-flag
failed = False

# Info
def info(msg):
    sys.stderr.write("%s" % msg)
def infoln(msg):
    sys.stderr.write("%s\n" % msg)

# -----------------------------------------------------------------------------
def get_role_contacts(org_group, include=None, exclude=None, project=None):

    db = current.db

    auth = current.auth
    s3db = current.s3db

    contacts = None

    # Lookup the pe_ids of all organisations in the group
    otable = s3db.org_organisation
    ptable = s3db.project_project
    ltable = s3db.project_organisation
    ogtable = s3db.org_group
    gmtable = s3db.org_group_membership

    join = [gmtable.on((gmtable.organisation_id == otable.id) & \
                       (gmtable.deleted == False)),
            ogtable.on((ogtable.id == gmtable.group_id) & \
                       (ogtable.name == org_group)),
            ]
    if project:
        join.extend([ltable.on((ltable.organisation_id == otable.id) & \
                               (ltable.deleted == False)),
                    ptable.on((ptable.id == ltable.project_id) & \
                              (ptable.name == project)),
                    ])
    query = (otable.deleted == False)
    rows = db(query).select(otable.name,
                            otable.pe_id,
                            join = join,
                            )
    org_pe_ids = list(set(row.pe_id for row in rows))

    # Get all users with this realm as direct OU ancestor
    users = s3db.pr_realm_users(org_pe_ids) if org_pe_ids else None
    if users:

        # Look up those among the realm users who have
        # the include-role for either pe_id or for their default realm
        gtable = auth.settings.table_group
        mtable = auth.settings.table_membership
        ltable = s3db.pr_person_user
        join = [mtable.on((mtable.user_id == ltable.user_id) & \
                          ((mtable.pe_id == None) | (mtable.pe_id.belongs(org_pe_ids))) & \
                          (mtable.deleted == False)),
                gtable.on((gtable.id == mtable.group_id) & \
                          (gtable.uuid == include)),
                ]
        query = (ltable.user_id.belongs(set(users.keys()))) & \
                (ltable.deleted == False)
        rows = db(query).select(ltable.pe_id, join=join)
        include_pe_ids = set(row.pe_id for row in rows)

        if exclude:
            # Look up those among the realm users who have
            # the exclude-role for either pe_id or for their default realm
            join = [mtable.on((mtable.user_id == ltable.user_id) & \
                            ((mtable.pe_id == None) | (mtable.pe_id.belongs(org_pe_ids))) & \
                            (mtable.deleted == False)),
                    gtable.on((gtable.id == mtable.group_id) & \
                            (gtable.uuid == exclude)),
                    ]
            query = (ltable.user_id.belongs(set(users.keys()))) & \
                    (ltable.deleted == False)
            rows = db(query).select(ltable.pe_id, join=join)
            exclude_pe_ids = set(row.pe_id for row in rows)
        else:
            exclude_pe_ids = set()

        user_pe_ids = include_pe_ids - exclude_pe_ids

        # Look up their email addresses
        if user_pe_ids:
            ctable = s3db.pr_contact
            query = (ctable.pe_id.belongs(user_pe_ids)) & \
                    (ctable.contact_method == "EMAIL") & \
                    (ctable.deleted == False)
            rows = db(query).select(ctable.pe_id,
                                    ctable.value,
                                    orderby = ~ctable.priority,
                                    )
            contacts = {row.pe_id: row.value for row in rows}

    return list(set(contacts.values())) if contacts else None

# -----------------------------------------------------------------------------
if not failed:

    emails = get_role_contacts(org_group,
                               include = include,
                               exclude = exclude,
                               project = project,
                               )
    if emails:
        for email in emails:
            infoln(email)

# -----------------------------------------------------------------------------
