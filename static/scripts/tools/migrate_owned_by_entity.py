# -*- coding: utf-8 -*-
# Script to migrate existing records from owned_by_entity to realm_entity.
# This script must be run after upgrading the site and *before* any further
# records get created or updated.
#
# Script does:
# 1. let web2py auto-migrate create the new field "realm_entity" in all tables
# 2. copy all values from owned_by_entity into realm_entity
#
# The "owned_by_entity" field will be dropped in a later revision of Eden.
#
# Run like:
#   python web2py.py -S eden -M -R applications/eden/static/scripts/tools/migrate_owned_by_entity.py
#
if __name__ == "__main__":

    s3db.load_all_models()

    error = False
    for table in db:
        if "realm_entity" in table.fields and \
           "owned_by_entity" in table.fields:
            print "Updating %s" % table
            query = (table._id > 0) & \
                    (table.realm_entity == None) & \
                    (table.owned_by_entity != None)
            try:
                num = db(query).update(realm_entity =
                                       table["owned_by_entity"])
            except Exception, e:
                print e
                error = True
            else:
                print "%s records updated" % num
        else:
            print "Not updating: %s" % table

    if error:
        db.rollback()
        print "Migration failed - rolled back"
    else:
        db.commit()
        print "Migration successful - committed"

