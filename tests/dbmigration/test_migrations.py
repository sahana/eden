# Tests for each migrations made in the migration_scripts file
# has been made in order to call the tests just run the this script 
# using
# cd web2py
# python web2py.py -S eden -R applications/eden/tests/dbmigration/test_migrations.py 
# 
# Choose from the menu whatever migration methods you want to test,

s3migration = local_import("s3migration")
s3migrate = s3migration.S3Migration()
db = s3migrate.db

class mapping_function():

    # -------------------------------------------------------------------------
    @staticmethod
    def fields(db):    
        """
            This function specify the fields that are needed for the select query
        """

        fields = []
        fields.append(db["org_organisation"].ALL)
        return fields

    # -------------------------------------------------------------------------
    @staticmethod
    def query(db):    
        """
            This function specify the query for the select query
        """

        query = (db.org_organisation.organisation_type_id == db.org_organisation_type.id)
        return query

    # -------------------------------------------------------------------------
    @staticmethod
    def mapping(row):
        """
            @param row : The row which is generated as a result of the select query done

            The new values are returned which are are generarated for each row .
        """

        return row["id"]

# -----------------------------------------------------------------------------
def rename_field():
    """
        Test for S3Migrate().rename_field function
    """

    tablename = "pr_person"
    print "Testing table: %s" % tablename
    table = db[tablename]
    for row in db(table.id > 0).select():
        print "id: %s, first_name: %s" % (row["id"], row["first_name"])
    attributes_to_copy = ["type", "length", "default", "required", "requires", "ondelete", "notnull", "unique",
        "uploadfield", "widget", "label", "comment", "writable", "readable", "update", "authorize",
        "autodelete", "represent", "uploadfolder", "uploadseparate", "uploadfs", "compute", "custom_store",
        "custom_retrieve", "custom_retrieve_file_properties", "custom_delete", "filter_in", "filter_out"]        
    s3migrate.rename_field(tablename, "first_name", "first_name_test", attributes_to_copy)
    print "Migrated data:"
    for row in db(table.id > 0).select():
        print "id: %s, first_name_test: %s" % (row["id"], row["first_name_test"])

# -----------------------------------------------------------------------------
def rename_table():
    """
        Test for S3Migrate().rename_table function
    """

    s3migrate.rename_table("vehicle_vehicle", "rename_vehicle")
    print "renamed vehicle_vehicle to rename_vehicle"

# -----------------------------------------------------------------------------
def add_new_field():
    """
        Test for S3Migrate().migrate_to_unique_field function
    """

    field_to_update = "new_field2"
    tablename = "org_organisation"
    s3migrate.migrate_to_unique_field(tablename, field_to_update, mapping_function(),
                                      ["org_organisation_type", "org_sector"])
    table = db[tablename]
    for row in db(table.id > 0).select(["id"], table[field_to_update]):
        print "id = ", row["id"], field_to_update, " = ", row[field_to_update]

# -----------------------------------------------------------------------------
def list_field_to_reference():
    """
        Test for S3Migrate().list_field_to_reference function
    """

    tablename_new = "sector_id_reference"
    new_list_field = list_field_name = "multi_sector_id"
    tablename_old_id_field = "id"
    tablename_old = "org_organisation"
    table_old = db[tablename_old]
    for a in range(2,10):
        db[tablename_old].insert(name = "test_%s" % str(a),
                                 organisation_type_id = a%5,
                                 uuid = "%s%s" % (table_old["uuid"].default, str(a)),
                                 multi_sector_id = [a-2, a-1, a]
                                 )
    db.commit()
    s3migrate.list_field_to_reference(tablename_new,
                                      new_list_field,
                                      list_field_name,
                                      tablename_old_id_field,
                                      tablename_old)
    print tablename_old
    for row in db(table_old).select():
        print "id: ", row[tablename_old_id_field], "sector_id: ", row[list_field_name]
    print tablename_new
    for row in db(db[tablename_new]).select():
        print "id: ", row["%s_%s" % (tablename_old, tablename_old_id_field)], "sector_id: ", row[new_list_field]

# -----------------------------------------------------------------------------
# The menu with all the options of migration for test
prt_str = '''
Select the migration that you want to test:
1. Renaming a field
2. Renaming a table
3. Addding a unique field
4. List field to table
'''
print prt_str
option_chosen = int(raw_input())
if option_chosen == 1:
    rename_field()

elif option_chosen == 2:
    rename_table()

elif option_chosen == 3:
    add_new_field()

elif option_chosen == 4:
    list_field_to_reference()

# END =========================================================================
