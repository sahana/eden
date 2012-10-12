import os
import sys
import copy
import subprocess

WEB2PY_PATH = sys.argv[1]
APP = sys.argv[2]
changed_table = "org_organisation"
new_field = "type_id"
new_table = "org_organisation_type"
old_field = "type"
new_table_field = "name"

os.chdir(WEB2PY_PATH)
sys.path.append(WEB2PY_PATH)

from gluon.custom_import import custom_import_install
custom_import_install(WEB2PY_PATH)
from gluon.shell import env
from gluon import DAL, Field

old_env = env(APP, c=None, import_models=True)
old_str ='''
try:
    s3db.load_all_models()
except NameError:
    print "s3db not defined"
'''
globals().update(**old_env)
exec old_str in globals(), locals()

database_string = "sqlite://storage.db"
old_database_folder = "%s/applications/%s/databases" % (WEB2PY_PATH, APP)
temp_db = DAL(database_string,
              folder=old_database_folder,
              migrate_enabled=True,
              migrate=True)

# Migration Script
list_of_fields = []
list_of_fields.append(Field(new_field, "integer"))

list_of_new_table_fields = []
list_of_new_table_fields.append(Field(new_table_field, "integer"))

try:
	db[changed_table]._primarykey
except KeyError:
	db[changed_table]._primarykey = None

temp_db.define_table(changed_table,
                     db[changed_table],
                     *list_of_fields,
                     primarykey = db[changed_table]._primarykey
                     )
temp_db.define_table(new_table,
                     *list_of_new_table_fields
                     )

temp_db.commit()

# Add a new field of int type in a class
for old_row in temp_db().select(temp_db[changed_table][old_field]):
    if (len(temp_db(temp_db[new_table][new_table_field] == old_row[old_field]).select()) == 0):
        row = temp_db[new_table].insert(name = old_row[old_field])
        new_id = int(row["id"])
        temp_db(temp_db[changed_table][old_field] == old_row[old_field]).update(type_id = new_id)
    
temp_db.commit()

# END =========================================================================
