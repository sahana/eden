# This script compares the db schema of 2 eden apps to tell the differences
#
# Just run the script with 3 necessary arguments in this order
# 1. WEB2PY_PATH
# 2. OLD_APP
# 3. NEW_APP
# python applications/eden/static/scripts/tools/apps_db_comparison.py /home/web2py eden_old eden_new
#
# This script also has a Test script that makes 2 new web2py apps to compare:
# python applications/eden/tests/dbmigration TestScript.py

import os
import sys
import copy
import subprocess

# Set Variables
WEB2PY_PATH = sys.argv[1]
if not "WEB2PY_PATH" in os.environ:
    os.environ["WEB2PY_PATH"] = WEB2PY_PATH

NEW_APP = sys.argv[3]
OLD_APP = sys.argv[2]
NEW_PATH = "%s/applications/%s" % (os.environ["WEB2PY_PATH"], NEW_APP)
OLD_PATH = "%s/applications/%s" % (os.environ["WEB2PY_PATH"], OLD_APP)

# Load the 2 environments with all their models
os.chdir(os.environ["WEB2PY_PATH"])
sys.path.append(os.environ["WEB2PY_PATH"])

from gluon.custom_import import custom_import_install
custom_import_install(os.environ["WEB2PY_PATH"])
from gluon.shell import env
from gluon import DAL, Field

new_env = env(NEW_APP, c=None, import_models=True)
d = globals().copy()
d.update(**new_env)
new_str ='''
try:
    s3db.load_all_models()
except NameError:
    print "s3db not defined"
new_db = db
'''
exec new_str in d, locals()

d.clear()

old_env = env(OLD_APP, c=None, import_models=True)
old_str ='''
try:
    s3db.load_all_models()
except NameError:
    print "s3db not defined"
old_db = db
'''
d = globals().copy()
d.update(**old_env)
exec old_str in d, locals()

# Get the Table and fields from the db
def get_tables_fields(db, database):
    tables = db.tables
    for table in tables:
        database[table] = {}
        database[table]["id"] = str(db[table]["_id"]).split(".")[-1]
        fields = db[table]["_fields"]
        for field in fields:
            database[table][field]= {}
        database[table]["referenced_by"] = db[table]["_referenced_by"]

old_database = {}
new_database = {}
get_tables_fields(old_db, old_database)
get_tables_fields(new_db, new_database)

# Get the union of the of the tables 2 databases
def intersect(a, b):
    return list(set(a) & set(b))

def union(a, b):
    return list(set(a) | set(b))

def all_tables(traversed):
    traversed.extend(union(old_database, new_database))

traversed = []
all_tables(traversed)

# Detect Changes
change = {}

tables_disappeared = list(set(old_database) - set(new_database))
tables_appeared = list(set(new_database) - set(old_database))

# Detect the changes in Tables: Renaming, Adding or Deleting fields
for table in intersect(old_database,new_database):
    change[table] = {}
    change[table]["appeared"] = list(set(new_database[table]) - set(old_database[table]))
    change[table]["disappeared"] = list(set(old_database[table]) - set(new_database[table]))

attributes = ["type", "length", "default", "required", "requires", "ondelete", "notnull", "unique",
        "uploadfield", "widget", "label", "comment", "writable", "readable", "update", "authorize",
        "autodelete", "represent", "uploadfolder", "uploadseparate", "uploadfs", "compute", "custom_store",
        "custom_retrieve", "custom_retrieve_file_properties", "custom_delete", "filter_in", "filter_out"]

change_attribute = {}

for table in intersect(old_database,new_database):
    for field in intersect(old_db[table]["_fields"], new_db[table]["_fields"]):
        if not hasattr(change_attribute,table):
            change_attribute[table] = {}
        change_attribute[table][field] = []
        for attribute in attributes:
            if not eval("old_db[table][field].%(attribute)s == new_db[table][field].%(attribute)s" % {"attribute":attribute}):
                change_attribute[table][field].append(attribute)
            
# Generate a Report of the Changes
print "\nTables Appeared = %s" % tables_appeared
print "\nTables Disappeared = %s" % tables_disappeared

for table in change.keys():
    if change[table]["appeared"]:
        print "table =", table, "changes appeared = ", change[table]["appeared"]
    if change[table]["disappeared"]:
        print "table =", table, "changes disappeared = ", change[table]["disappeared"]

for table in change_attribute.keys():
    for field in change_attribute[table].keys():
        if change_attribute[table][field] :
            print "table = ", table, " field = ", field, " changes = ", change_attribute[table][field]

# END =========================================================================
