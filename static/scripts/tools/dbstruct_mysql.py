#
# Recommended usage: fabfile.py
#
# - or manually:
#
# 0. Configure /root/.my.cnf to allow the root user to access MySQL as root without password
#
# 1. Create a new, empty MySQL database 'sahana' as-normal
#     mysqladmin create sahana
#     mysql
#      GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,INDEX,ALTER,DROP ON sahana.* TO 'sahana'@'localhost' IDENTIFIED BY 'password';
#
# 2. set deployment_settings.base.prepopulate = False in models/000_config.py
#
# 3. Allow web2py to run the Eden model to configure the Database structure
#     web2py -N -S eden -M
#
# 4. Export the Live database from the Live server (including structure)
#     mysqldump sahana > backup.sql
#
# 5. Use this to populate a new table 'old'
#     mysqladmin create old
#     mysql old < backup.sql
#
# 6. Change database names/passwords in the script &/or access rights in the table, if not using root & .my.cnf
#     mysql
#      GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,INDEX,ALTER,DROP ON old.* TO 'sahana'@'localhost' IDENTIFIED BY 'password';
#
# 7. Run the script
#     python dbstruct.py
#
# 8. Fixup manually anything which couldn't be done automatically, e.g.:
#     "ALTER TABLE `gis_location` DROP `marker_id` ;
#      The table -> gis_location has a field -> marker_id that could not be automatically removed"
#     =>
#     mysql
#      \r old
#      show innodb status;
#      ALTER TABLE gis_location DROP FOREIGN KEY gis_location_ibfk_2;
#      ALTER TABLE gis_location DROP marker_id ;
#      ALTER TABLE gis_location DROP osm_id ;
#
# 9. Take a dump of the fixed data (no structure, full inserts)
#     mysqldump -tc old > old.sql
#
# 10. Import it into the empty database
#      mysql sahana < old.sql
#
# 11. Dump the final database with good structure/data ready to import on the server (including structure)
#      mysqldump sahana > new.sql
#
# 12. Import it on the Server
#      mysqladmin drop sahana
#      mysqladmin create sahana
#      mysql sahana < new.sql
#
# 13. Restore indexes
#      w2p
#       tablename = "pr_person"
#       field = "first_name"
#       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
#       field = "middle_name"
#       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
#       field = "last_name"
#       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
#       tablename = "gis_location"
#       field = "name"
#       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
#

user = "root"
# Password can be added to script, if it can't be read from /root/.my.cnf
passwd = "password"

# An empty database with the new db schema
new_db = "sahana"

# The old database (structure & data)
old_db = "old"

# ----------------------------------------------------------------------------------

import os
import sys
import subprocess
import MySQLdb

# If possible, read the password for root from /root/.my.cnf
config = "/root/.my.cnf"
if os.access(config, os.R_OK):
    f = open(config, "r")
    lines = f.readlines()
    f.close()
    for line in lines:
        findstring = "password="
        if findstring in line:
            passwd = line.replace(findstring, "").strip()

# DB1 is the db to sync to (Test or new Live)
db1 = MySQLdb.connection(host="localhost", user=user, passwd=passwd, db=new_db)

# DB2 is the db to sync from (backup of Live)
db2 = MySQLdb.connection(host="localhost", user=user, passwd=passwd, db=old_db)

def tablelist(db):
    db.query("SHOW TABLES;")
    r = db.store_result()
    tables = []
    for row in r.fetch_row(300):
        tables.append(row[0])
    return tables

# Dict to load up the database Structure
def tablestruct(db):
    tablestruct = {}
    tables = tablelist(db)
    for table in tables:
        db.query("describe %s;" % table)
        r = db.store_result()
        structure = []
        for row in r.fetch_row(100):
            structure.append(row[0])
        tablestruct[table] = structure
    return tablestruct

struct1 = tablestruct(db1)
struct2 = tablestruct(db2)
tables_to_delete = []
fields_to_delete = {}
for key in struct2:
    fields_to_delete[key] = []
    try:
        fields1 = struct1[key]
        fields2 = struct2[key]
        for field in fields2:
            try:
                fields1.index(field)
            except:
                fields_to_delete[key].append(field)

    except:
        tables_to_delete.append(key)

for table in fields_to_delete.keys():
    if fields_to_delete[table] == []:
        del fields_to_delete[table]

print tables_to_delete
print fields_to_delete

for table in tables_to_delete:
    db2.query("SET FOREIGN_KEY_CHECKS = 0;")
    db2.query("DROP TABLE %s;" % table)
    db2.query("SET FOREIGN_KEY_CHECKS = 1;")

problems = ""
filename = "/root/mysql.status"
for table in fields_to_delete:
    for field in fields_to_delete[table]:
        print "ALTER TABLE `" + table + "` DROP `" + field + "` ;"
        db2.query("SET FOREIGN_KEY_CHECKS = 0;")
        try:
            db2.query("ALTER TABLE `" + table + "` DROP  `" + field + "` ;")
        except:
            print "Table %s has a field %s with a FK constraint" % (table, field)
            # Try to resolve any FK constraint issues automatically
            cmd = "mysql -e 'show innodb status;' > %s" % filename
            subprocess.call(cmd, shell=True)
            if os.access(filename, os.R_OK):
                f = open(filename, "r")
                lines = f.readlines()
                f.close()
                fk = lines[1].split("CONSTRAINT")[1].split("FOREIGN")[0].strip()
                print "ALTER TABLE `" + table + "` DROP FOREIGN KEY `" + fk + "`;"
                try:
                    db2.query("ALTER TABLE `" + table + "` DROP FOREIGN KEY `" + fk + "`;")
                except (MySQLdb.OperationalError,):
                    e = sys.exc_info()[1]
                    print "Failed to remove FK %s from table %s" % (fk, table) + e.message
            # Try again now that FK constraint has been removed
            print "ALTER TABLE `" + table + "` DROP `" + field + "` ;"
            try:
                db2.query("ALTER TABLE `" + table + "` DROP  `" + field + "` ;")
            except (MySQLdb.OperationalError,):
                e = sys.exc_info()[1]
                message = "Failed to drop field %s from table %s" % (field, table) + e.message
                print message
                problems += message
        db2.query("SET FOREIGN_KEY_CHECKS = 1;")

# List any remaining issues as clearly/concisely as possible for us to resolve manually
print problems
