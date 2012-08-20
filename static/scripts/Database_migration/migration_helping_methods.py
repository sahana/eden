# This file does all the interaction with the database for migration 
# It is imported in from migration_scripts.py . 
# It handles all the database operations , like adding a new field , 
# changing values of a field , adding new table etc . 
# These operations are readily used in migration_scripts.py .
# 
# In order to use the function in this file fierstly set_gloabls() needs to be called
# with the appropiate arguments in order to set the environment variables.

import os
import sys
import copy
import subprocess

# Globals that are used to set the environment

WEB2PY_PATH = APP = dbengine = ""
db = {}

# Function that sets the environment
def set_globals(web2py_path,app):
    """
    This function sets the environment variables like database , dbengine etc .
        
    @param     web2py_path        :    The path to the web2py congaing the Eden app (i.e "/home/web2py")
    @param     app                :    The name of the eden application of whose database needs to be migrated (i.e "eden")
    
    It loads the models all the models to get the database and also sets the 
    other global variable which are required by all of the functions for database operations
    """
    global WEB2PY_PATH,APP,dbengine
    WEB2PY_PATH = web2py_path
    APP = app
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
    if settings.database.db_type:
        dbengine = settings.database.db_type
    else:
        dbengine = "sqlite"

def set_db(extern_db):
    """
    This function loads the extern db as the global database , so that 
    all the migration  operations are done on it 
    
    @param extern_db    :   External database
    """
    global db
    db = extern_db


def map_type_list_field(old_type):
    """
    This function maps the list type into individual field type which can contain 
    the individual values of the list.
    
    Mappings
    - list:reference <table> --> refererence <table>
    - list:integer           --> integer
    - list:string            --> string
    """
    if (old_type == "list:integer"):
        return "integer"
    elif old_type.startswith("list:reference"):
        return old_type.strip("list:")
    elif old_type == "list:string":
        return "string"

def creating_new_table(new_table_name , new_list_field , list_field_name , old_table_id_field , old_table): 
    """
    This function creates the new table which is used in the list_field_to_reference migration.
    That new table has a foreign key reference back to the original table.
    
    @param     new_table_name     :    The name of the new table to which the list field needs to migrated
    @param     new_list_field     :    The name of the field in the new table which will hold the content of the list field
    @param     list_field_name    :    The name of the list field in the original table
    @param     old_table_id_field :    The name of the id field in the original table
    @param     old_table          :    The name of the original table
    
    """
    new_field_type = map_type_list_field(db[old_table][list_field_name].type)
    new_field = Field(new_list_field,new_field_type)
    new_id_field = Field("%s_%s" %(old_table,old_table_id_field),"reference %s" % ( old_table))
    db.define_table(new_table_name ,new_id_field , new_field )
    db.commit()
    
def fill_the_new_table(new_table_name , new_list_field , list_field_name , old_table_id_field , old_table ):
    """
    This function is used in the list_field_to_reference migration.
    For each value in the list field for each record in the original table, 
    they create one record in the new table that points back to the original record.
    
    @param     new_table_name     :    The name of the new table to which the list field needs to migrated
    @param     new_list_field     :    The name of the field in the new table which will hold the content of the list field
    @param     list_field_name    :    The name of the list field in the original table
    @param     old_table_id_field :    The name of the id field in the original table
    @param     old_table          :    The name of the original table
    
    """
    update_dict = {}
    for row in db().select(db[old_table][old_table_id_field],db[old_table][list_field_name]):
        for element in row[list_field_name]:
            update_dict[new_list_field] = element
            update_dict["%s_%s" %(old_table,old_table_id_field)] = row[old_table_id_field]
            db[new_table_name].insert(**update_dict)
    db.commit()



def renaming_table(old_table_name,new_table_name):
    """
    Renaming a particular table , Thus if any fields references to that table, it will be handled too.
    
    @param    app            :    The name of the eden application of whose database needs to be migrated (i.e "eden")
    @param    old_table_name :    The name of the original table before renaming
    @param    new_table_name :    The name of the table after renaming
    """
    try:
        db.executesql("ALTER TABLE %s  RENAME TO %s;" % (old_table_name, new_table_name))
    except Exception:
        print "Exception given in renaming_table_function"     
    db.commit()


def adding_renamed_fields(table_name,old_field_name,new_field_name,attributes_to_copy):
    """
    This function is used add a field in table mentioned while 
    renaming a field . The renamed field is added separately to the table with the 
    same properties as the original field.     
    """
    database_string = "sqlite://storage.db"
    old_database_folder = "%s/applications/%s/databases" % (WEB2PY_PATH, APP)
    temp_db = DAL( database_string, folder = old_database_folder, migrate_enabled=True ,migrate = True)
    new_field = Field(new_field_name)
    try:
        table_primary_key = db[table_name]._primarykey
    except KeyError:
        table_primary_key = None
    for attribute in attributes_to_copy:
        exec_str = "new_field.%(attribute)s = db[table_name][old_field_name].%(attribute)s" % {"attribute":attribute}
        exec exec_str in globals() , locals()
    temp_db.define_table(table_name ,db[table_name],new_field,primarykey = table_primary_key)
    return temp_db

def copy_field(table_name,old_field_name,new_field_name):
    """
    Copy all the values from a old_field into he new_field which are
    there in the table mentioned .
    """
    dict_update = {}
    for row in db().select(db[table_name][old_field_name]):
        dict_update[new_field_name] = row[old_field_name]
        db(db[table_name][old_field_name] == row[old_field_name]).update(**dict_update)
    return db


def map_type_web2py_to_sql(dal_type):
    """
    This function maps the web2py type into sql type , 
    It is usefull when writing sql queries to change the properties of a field
    
    Mappings
    string   -->   Varchar
    """
    if dal_type == "string":
        return "varchar"
    else:
        return dal_type

def renaming_field(table_name,old_field_name,new_field_name,attributes_to_copy = None):
    """
    Renaming a particular field , while keeping the other properties of the field same. 
    Also if there are some index on that table that will be recreated and other constraints will remain unchanged too.
    
    @param  old_table          :    The name of the table in which the field is renamed
    @param  old_field_name     :    The name of the original field before renaming
    @param  new_field_name     :    The name of the field after renaming
    @param  attributes_to_copy :    The list of attributes which needs to be copied from the old_field to the new_field (needed only in sqlite)
    """
    if dbengine == "sqlite":
        db = adding_renamed_fields(table_name,old_field_name,new_field_name,attributes_to_copy)
        db = copy_field(table_name,old_field_name,new_field_name)     
        list_index = db.executesql("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='%s' ORDER BY name;" %(table_name))
        for element in list_index:
            if element[0] is not None and "%s(%s)" % (table_name,old_field_name) in element[0]:
                db.executesql("CREATE INDEX %s__idx on %s(%s);" % (new_field_name, table_name,new_field_name))
    elif dbengine == "mysql":
        sql_type = map_type_web2py_to_sql(db[table_name][old_field_name].type)
        query = "ALTER TABLE %s CHANGE %s %s %s(%s)" % (table_name,old_field_name,new_field_name,sql_type,db[table_name][old_field_name].length)
        db.executesql(query)
    elif dbengine == "postgres" :
        query = "ALTER TABLE %s RENAME COLUMN %s TO %s" % (table_name,old_field_name,new_field_name)
        db.executesql(query)
    db.commit()

def adding_new_fields(new_unique_field,changed_table):
    """
    This function adds a new_uniwue_field into the changed_table , while keeping all the rest of 
    the properties of the table ubchanged
    """
    database_string = "sqlite://storage.db"
    old_database_folder = "%s/applications/%s/databases" % (WEB2PY_PATH, APP)
    temp_db = DAL( database_string, folder = old_database_folder, migrate_enabled=True ,migrate = True)
    new_field = Field(new_unique_field,"integer")
    try:
        changed_table_primary_key = db[changed_table]._primarykey
    except KeyError:
        changed_table_primary_key = None
    temp_db.define_table(changed_table ,db[changed_table],new_field,primarykey = changed_table_primary_key)
    return temp_db

def adding_tables_temp_db(temp_db , list_of_table):
    """
    This field adds table to the temp_db from the global db
    these might in the running queries or validating values. 
    """
    for table in list_of_table:
        temp_db.define_table(table ,db[table])
    return temp_db

def update_with_mappings(changed_table,field_to_update,mapping_function):
    """
   Update the the values of an existing field according to the mappings given through the mapping_function
    
    @param    field_to_update :    The name of the field to be updated according to the mapping
    @param    changed_table   :    The name of the original table in which the new unique field id added
    @param    list_of_tables  :    These contains the list of tables which the changed_tables references

    """
    fields = mapping_function.fields(db)
    if db[changed_table]["id"] not in fields:
        fields.append(db[changed_table]["id"])
    rows = db(mapping_function.query(db)).select(*fields)
    if rows:
        try:
                rows[0][changed_table]["id"]
                row_single_layer = False
        except KeyError:
                row_single_layer = True
    dict_update = {}
    for row in rows:
        if not row_single_layer:
            row_id = row[changed_table]["id"]
        else:
            row_id = row["id"]
        changed_value = mapping_function.mapping(row)
        dict_update[field_to_update] = changed_value
        db(db[changed_table]["id"] == row_id).update(**dict_update)    
    db.commit()
