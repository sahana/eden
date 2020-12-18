# -*- coding: utf-8 -*-
#
# Tool to adjust pool assignments of volunteers
#
# RLP Template Version 1.6.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLP/tools/pooladjust.py -A <rules-file>
#
import sys

from gluon import current

# -----------------------------------------------------------------------------
# Info
def info(msg):
    sys.stderr.write("%s" % msg)
def infoln(msg):
    sys.stderr.write("%s\n" % msg)

# -----------------------------------------------------------------------------
def update_pool(person_id, pool_id):

    db = current.db
    s3db = current.s3db

    gtable = s3db.pr_group
    mtable = s3db.pr_group_membership
    join = gtable.on((gtable.id == mtable.group_id) & \
                     (gtable.group_type.belongs((21, 22))))
    query = (mtable.person_id == person_id) & \
            (mtable.deleted == False)
    rows = db(query).select(mtable.id,
                            mtable.group_id,
                            join = join,
                            )
    existing = None
    for row in rows:
        if row.group_id == pool_id:
            existing = row
        else:
            row.delete_record()
    if existing:
        s3db.onaccept(mtable, existing)
        updated = False
    else:
        data = {"group_id": pool_id, "person_id": person_id}
        data["id"] = mtable.insert(**data)
        current.auth.s3_set_record_owner(mtable, data["id"])
        s3db.onaccept(mtable, data, method="create")
        updated = True

    return updated

# -----------------------------------------------------------------------------
def adjust_pools(rules):

    # Override auth (disables all permission checks)
    current.auth.override = True

    db = current.db
    s3db = current.s3db

    # Get all volunteer records
    htable = s3db.hrm_human_resource
    query = (htable.type == 2) & (htable.deleted == False)
    rows = db(query).select(htable.person_id)

    if rows:
        info("Checking %s volunteer records" % len(rows))

        updated = 0
        for row in rows:

            person_id = row.person_id
            if not person_id:
                continue

            new_pool_id = rules(person_id)
            if not new_pool_id:
                info(".")
                continue
            else:
                if update_pool(person_id, new_pool_id):
                    updated += 1
                    info("+")
                else:
                    info(".")
        infoln("...done (%s volunteers re-assigned)" % updated)
    else:
        infoln("No volunteer records to check")

    return True

# -----------------------------------------------------------------------------
def main(argv):

    from templates.RLP.poolrules import PoolRules

    if len(argv):
        rules = PoolRules(argv[0])
    else:
        rules = PoolRules()
    if rules.rules is None:
        return -1

    return 0 if adjust_pools(rules) else -1

# -----------------------------------------------------------------------------
if __name__ == "__main__":

    main(sys.argv[1:])

# END =========================================================================
