# -*- coding: utf-8 -*-
#
# Helper Script for Mass-Invitation of Participant Organisations
#
# RLPPTM Template Version 1.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLPPTM/tools/mis.py
#
import os
import sys

from s3 import s3_format_datetime

from templates.RLPPTM.config import SCHOOLS
from templates.RLPPTM.helpers import rlpptm_InviteUserOrg

# Batch limit (set to False to disable)
BATCH_LIMIT = 250

# Override auth (disables all permission checks)
auth.override = True

# Failed-flag
failed = False

# Info
log = None
def info(msg):
    sys.stderr.write("%s" % msg)
    if log:
        log.write("%s" % msg)
def infoln(msg):
    sys.stderr.write("%s\n" % msg)
    if log:
        log.write("%s\n" % msg)

# Load models for tables
otable = s3db.org_organisation
gtable = s3db.org_group
mtable = s3db.org_group_membership
utable = s3db.auth_user
oltable = s3db.org_organisation_user
pltable = s3db.pr_person_user
ctable = s3db.pr_contact

timestmp = s3_format_datetime(dtfmt="%Y%m%d%H%M%S")
LOGFILE = os.path.join(request.folder, "private", "mis_%s.log" % timestmp)

# -----------------------------------------------------------------------------
# Invite organisations
#
if not failed:

    try:
        with open(LOGFILE, "w", encoding="utf-8") as logfile:
            log = logfile

            join = [mtable.on((mtable.organisation_id == otable.id) & \
                              (mtable.deleted == False)),
                    gtable.on((gtable.id == mtable.group_id) & \
                              (gtable.name == SCHOOLS) & \
                              (gtable.deleted == False)),
                    ]
            query = (otable.deleted == False)
            organisations = db(query).select(otable.id,
                                             otable.pe_id,
                                             otable.name,
                                             join = join,
                                             orderby = otable.id,
                                             )

            total = len(organisations)
            infoln("Total: %s Organisations" % total)
            infoln("")
            skipped = sent = failures = 0
            invite_org = rlpptm_InviteUserOrg.invite_account
            for organisation in organisations:

                info("%s..." % organisation.name)

                # Get all accounts that are linked to this org
                organisation_id = organisation.id
                join = oltable.on((oltable.user_id == utable.id) & \
                                (oltable.deleted == False))
                left = pltable.on((pltable.user_id == utable.id) & \
                                (pltable.deleted == False))
                query = (oltable.organisation_id == organisation_id)
                rows = db(query).select(utable.id,
                                        utable.email,
                                        utable.registration_key,
                                        pltable.pe_id,
                                        join = join,
                                        left = left,
                                        )

                if rows:
                    # There are already accounts linked to this organisation
                    invited, registered = [], []
                    for row in rows:
                        username = row.auth_user.email
                        if row.pr_person_user.pe_id:
                            registered.append(username)
                        else:
                            invited.append(username)
                    if registered:
                        infoln("already registered (%s)." % ", ".join(registered))
                    else:
                        infoln("already invited (%s)." % ", ".join(invited))
                    skipped += 1
                    continue

                # Find email address
                query = (ctable.pe_id == organisation.pe_id) & \
                        (ctable.contact_method == "EMAIL") & \
                        (ctable.deleted == False)
                contact = db(query).select(ctable.value,
                                           orderby = ctable.priority,
                                           limitby = (0, 1),
                                           ).first()
                if contact:
                    email = contact.value
                    info("(%s)..." % email)
                else:
                    infoln("no email address.")
                    skipped += 1
                    continue

                error = invite_org(organisation, email, account=None)
                if not error:
                    sent += 1
                    infoln("invited.")
                    db.commit()
                else:
                    failures += 1
                    infoln("invitation failed (%s)." % error)

                if BATCH_LIMIT and sent >= BATCH_LIMIT:
                    infoln("Batch limit (%s) reached" % BATCH_LIMIT)
                    skipped = total - (sent + failures)
                    break

            infoln("")
            infoln("%s invitations sent" % sent)
            infoln("%s invitations failed" % failures)
            infoln("%s organisations skipped" % skipped)
            log = None

    except IOError:
        infoln("...failed (could not create logfile)")
        failed = True

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("PROCESS FAILED - Action rolled back.")
else:
    db.commit()
    infoln("PROCESS SUCCESSFUL.")
