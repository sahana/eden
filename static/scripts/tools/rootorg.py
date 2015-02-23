#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Post-migration script to update root_organisation in all
# org_organisation records
#
# Execute like: python web2py.py -S eden -M -R applications/eden/static/scripts/tools/rootorg.py
#
# @todo: remove when obsolete
#
import sys
auth.override = True

# Get all root orgs
s3db = current.s3db
otable = s3db.org_organisation
ltable = s3db.org_organisation_branch
left = ltable.on(ltable.branch_id == otable.id)
db = current.db
query = (otable.id > 0) & (ltable.id == None)
rows = db(query).select(otable.id, otable.name, left = left)

# Update root organisation (will automatically propagate to branches)
from s3db.org import org_update_root_organisation
for row in rows:
    print >> sys.stderr, "Update all branches of %s" % row.name
    org_update_root_organisation(row.id)
    
db.commit()
auth.override = False
print >> sys.stderr, "Done."
