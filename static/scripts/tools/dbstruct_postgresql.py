#
# Recommended usage: fabfile.py
#

# The script should be run as user postgres:
# sudo -H -u postgres python dbstruct_postgresql.py
#user = "postgres"

# An empty database with the new db schema
new_db = "sahana"

# The old database (structure & data)
old_db = "old"

# ----------------------------------------------------------------------------------

import os
import sys
import subprocess
import psycopg2
import psycopg2.errorcodes
import psycopg2.extras

# DB1 is the db to sync to (Test or new Live)
conn1 = psycopg2.connect("dbname=%s" % new_db)
cursor1 = conn1.cursor(cursor_factory=psycopg2.extras.DictCursor)

# DB2 is the db to sync from (backup of Live)
conn2 = psycopg2.connect("dbname=%s" % old_db)
cursor2 = conn2.cursor(cursor_factory=psycopg2.extras.DictCursor)

def tablelist(db, cursor):
    #filename = "/tmp/tables.txt"
    #os.system("psql -d %s -c '\d' > %s" % (new_db, filename))
    cursor.execute("SELECT table_name FROM information_schema.tables \
                    WHERE table_catalog=%s AND \
                          table_schema='public';", (db,))
    r = cursor.fetchall()
    tables = []
    for row in r:
        tables.append(row[0])
    return tables

# Dict to load up the database Structure
def tablestruct(db, cursor):
    tablestruct = {}
    tables = tablelist(db, cursor)
    for table in tables:
        cursor.execute("SELECT column_name, column_default, is_nullable, data_type FROM information_schema.columns \
                        WHERE table_name=%s AND \
                              table_schema='public';", (table,))
        r = cursor.fetchall()
        structure = []
        for row in r:
            structure.append(row[0])
        tablestruct[table] = structure
    return tablestruct

# Get the structure of the new Database
struct1 = tablestruct(new_db, cursor1)
cursor1.close()
conn1.close()

# Get the structure of the old Database
struct2 = tablestruct(old_db, cursor2)

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
    # http://stackoverflow.com/questions/139884/how-do-i-disable-referential-integrity-in-postgres-8-2
    cursor2.execute("ALTER TABLE %s DISABLE TRIGGER USER;" % table)
    cursor2.execute("DROP TABLE %s;" % table)
    cursor2.execute("ALTER TABLE %s ENABLE TRIGGER USER;" % table)

problems = ""
for table in fields_to_delete:
    cursor2.execute("ALTER TABLE %s DISABLE TRIGGER USER;" % table)
    for field in fields_to_delete[table]:
        print "ALTER TABLE `%s` DROP `%s`;" % (table, field)
        try:
            cursor2.execute("ALTER TABLE %s DROP %s;" % (table, field))
        except (psycopg2.IntegrityError,):
            e = sys.exc_info()[1]
            if psycopg2.errorcodes.lookup(e.pgcode) == "FOREIGN_KEY_VIOLATION":
                print "Table %s has a field %s with a FK constraint" % (table, field)
                # Try to resolve any FK constraint issues automatically
                fk = e[0].split("violates foreign key constraint \"")[1].split("\" on table")[0].strip()
                print "ALTER TABLE `%s` DROP CONSTRAINT `%s`;" % (table, fk)
                try:
                    cursor2.execute("ALTER TABLE %s DROP CONSTRAINT %s;" % (table, fk))
                except:
                    e = sys.exc_info()[1]
                    print "Failed to remove FK %s from table %s" % (fk, table)
                    problems = "%s\n%s" % (problems, e[0])
                # Try again now that FK constraint has been removed
                print "ALTER TABLE `%s` DROP `%s`;" % (table, field)
                try:
                    cursor2.execute("ALTER TABLE %s DROP %s;" % (table, field))
                except (psycopg2.IntegrityError,):
                    e = sys.exc_info()[1]
                    message = "Failed to drop field %s from table %s" % (field, table)
                    print message
                    problems = "%s\n%s" % (problems, message)
            else:
                # Some other problem than an FK constraint
                problems = "%s\n%s" % (problems, e[0])
                continue
                
    cursor2.execute("ALTER TABLE %s ENABLE TRIGGER USER;" % (table))

# Close the database
cursor2.close()
conn2.close()

# List any remaining issues as clearly/concisely as possible for us to resolve manually
print problems
