
# All the functions that does the migration have been added to migration_scripts file . migration_scripts file 
# internally calls the functions of migration_helping_methods file too perform the migration . Thus in order to
#  do the migration one just needs to import migration_scripts and call the method corresponding to the migration 
# he wants .  Also the user who wishes to do the migration in the db doesn't have to know the internal functioning
# of migration_script ,  thus the functions or the methods declared in migration_helping_methods file doesn't concern him.
#
#
# Tests 
# Tests for each function has been made in order to call the tests just
# run the tests script using the following command as eden app being your parent directory
# python tests/dbmigration/test_migrations.py 
# 
# Choose from the menu whatever migration methos you want to test,

from migration_helping_methods import *

def list_field_to_reference(web2py_path, app , new_table_name , new_list_field , list_field_name , old_table_id_field , old_table):
    """
    This method handles the migration in which a new table with a column for the 
    values they'll get from the list field is made and maybe some empty columns to be filled in later. 
    That new table has a foreign key reference back to the original table.
    Then for each value in the list field for each record in the original table, 
    they create one record in the new table that points back to the original record.
  
    Method of Calling

    import migration_scripts
    migration_scripts.list_field_to_reference(web2py_path,app,new_table_name , new_list_field , list_field_name , old_table_id_field , old_table)
    
    @param     web2py_path        :    The path to the web2py congaing the Eden app (i.e "/home/web2py")
    @param     app                :    The name of the eden application of whose database needs to be migrated (i.e "eden")
    @param     new_table_name     :    The name of the new table to which the list field needs to migrated
    @param     new_list_field     :    The name of the field in the new table which will hold the content of the list field
    @param     list_field_name    :    The name of the list field in the original table
    @param     old_table_id_field :    The name of the id field in the original table
    @param     old_table          :    The name of the original table
    """
    set_globals(web2py_path,app)
    creating_new_table(new_table_name , new_list_field , list_field_name , old_table_id_field , old_table)
    fill_the_new_table(new_table_name , new_list_field , list_field_name , old_table_id_field , old_table )

def migrating_to_unique_field(web2py_path, app ,field_to_update,changed_table , mapping_function , list_of_tables = None):
    """
    Adding values to a new field and adding values according to the mappings given through the mapping_funation
    
    - Method of Calling

    import migration_scripts
    import mapping_function
    migration_scripts.migrating_to_unique_field( web2py_path, app ,field_to_update , changed_table ,mapping_function, list_of_tables)
    

    @param    web2py_path     :    The path to the web2py congaing the Eden app (i.e "/home/web2py")
    @param    app             :    The name of the eden application of whose database needs to be migrated (i.e "eden")
    @param    field_to_update :    The name of the field to be updated according to the mapping
    @param    changed_table   :    The name of the original table in which the new unique field id added
    @param    list_of_tables  :    These contains the list of tables which the changed_tables references

    """
    set_globals(web2py_path,app)
    temp_db = adding_new_fields(field_to_update,changed_table)
    set_db(adding_tables_temp_db(temp_db,list_of_tables))
    update_with_mappings(changed_table,field_to_update,mapping_function)


def update_field_by_mapping(web2py_path, app ,field_to_update,changed_table , mapping_function ):
    """
    Update the the values of an existing field according to the mappings given through the mapping_function
    
    - Method of Calling

    import migration_scripts
    import mapping_function
    migration_scripts.update_field_by_mapping( web2py_path, app ,field_to_update , changed_table ,mapping_function, list_of_tables)
    
    @param    web2py_path     :    The path to the web2py congaing the Eden app (i.e "/home/web2py")
    @param    app             :    The name of the eden application of whose database needs to be migrated (i.e "eden")
    @param    field_to_update :    The name of the field to be updated according to the mapping
    @param    changed_table   :    The name of the original table in which the new unique field id added
    @param    list_of_tables  :    These contains the list of tables which the changed_tables references

    """
    set_globals(web2py_path,app)
    update_with_mappings(changed_table,field_to_update,mapping_function)

def migration_renaming_table(web2py_path, app ,old_table_name,new_table_name):
    """
    Renaming a particular table , Thus if any fields references to that table it will be handled too.
    
    - Method of Calling

    import migration_scripts
    migration_scripts.migration_renaming_table(web2py_path, app ,old_table_name,new_table_name)
    Description of arguments

    @param    web2py_path    :    The path to the web2py congaing the Eden app (i.e "/home/web2py")
    @param    app            :    The name of the eden application of whose database needs to be migrated (i.e "eden")
    @param    old_table_name :    The name of the original table before renaming
    @param    new_table_name :    The name of the table after renaming
     """
    set_globals(web2py_path,app)
    renaming_table(old_table_name,new_table_name)

def migration_renaming_field(web2py_path, app ,table_name,old_field_name,new_field_name,attributes_to_copy = None):
    """
    Renaming a particular field , while keeping the other properties of the field same. 
    Also if there are some index on that table that will be recreated and other constraints will remain unchanged too.
    
    Method of Calling

    import migration_scripts
    migration_scripts.migration_renaming_field(web2py_path, app, old_table, old_field_name , new_field_name ,attributes_to_copy)
    
    @param  web2py_path        :    The path to the web2py congaing the Eden app (i.e "/home/web2py")
    @param  app                :    The name of the eden application of whose database needs to be migrated (i.e "eden")
    @param  old_table          :    The name of the table in which the field is renamed
    @param  old_field_name     :    The name of the original field before renaming
    @param  new_field_name     :    The name of the field after renaming
    @param  attributes_to_copy :    The list of attributes which needs to be copied from the old_field to the new_field (needed only in sqlite)

    """
    set_globals(web2py_path,app)
    renaming_field(table_name,old_field_name,new_field_name,attributes_to_copy)
