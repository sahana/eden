# -*- coding: utf-8 -*-
#
# Helper Script to split a pool retaining POOLREADER assignments
#
# RLP Template Version 1.5.0
#
# - Adjust POOLNAME and ADDPOOL below, then
# - Execute in web2py folder like:
#   python web2py.py -S eden -M -R applications/eden/modules/templates/RLP/tools/poolsplit.py
#

# The name of the pool to split
POOLNAME = "Weitere Freiwillige"

# The name of the new pool containing a subset of the former
ADDPOOL = "Impf-ÄrztInnen"

import sys

# Override auth (disables all permission checks)
auth.override = True

# Failed-flag
failed = False

# Info
def info(msg):
    sys.stderr.write("%s" % msg)
def infoln(msg):
    sys.stderr.write("%s\n" % msg)

# Load models for tables
gtable = s3db.pr_group
rtable = auth.settings.table_group
mtable = auth.settings.table_membership

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLP")

# -----------------------------------------------------------------------------
# Upgrade user role assignments
#
if not failed:
    info("Identify pools")

    # Look up the PE-ID of either pool
    query = (gtable.name.belongs([POOLNAME, ADDPOOL])) & \
            (gtable.deleted == False)
    pools = db(query).select(gtable.pe_id,
                             gtable.name,
                             )
    pool_ids = {pool.name: pool.pe_id for pool in pools}
    for name in (POOLNAME, ADDPOOL):
        if name not in pool_ids:
            infoln("...failed (%s pool not found)" % name)
            failed = True
            break
    if not failed:
        infoln("...found")

if not failed:
    info("Assign POOLREADER role for %s pool" % ADDPOOL)

    join = rtable.on(rtable.id == mtable.group_id)
    query = (rtable.uuid == "POOLREADER") & \
            (mtable.pe_id == pool_ids[POOLNAME]) & \
            (mtable.deleted == False)
    rows = db(query).select(mtable.group_id,
                            mtable.user_id,
                            join=join,
                            )
    updated = 0
    for row in rows:
        auth.s3_assign_role(row.user_id, row.group_id, for_pe=pool_ids[ADDPOOL])
        info(".")
        updated += 1
    infoln("...done (%s users updated)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
