# -*- coding: utf-8 -*-

""" Database Migration Toolkit

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

"""

__all__ = ["S3Migration"]

import os

from gluon import current, DAL, Field
from gluon.cfs import getcfs
from gluon.compileapp import build_environment
from gluon.restricted import restricted
from gluon.storage import Storage

class S3Migration(object):
    """
        Database Migration Toolkit
        - will be useful to migrate both a production database on a server
          and also an offline client

        Normally run from a script in web2py context, but without models loaded:
        cd web2py
        python web2py.py -S eden -R <script.py>

        Where script looks like:
        m = local_import("s3migration")
        migrate = m.S3Migration()
        migrate.prep()
        migrate.migrate()
        migrate.post()
    """

    def __init__(self):

        request= current.request

        # Load s3cfg
        name = "applications.%s.modules.s3cfg" % request.application
        s3cfg = __import__(name)
        for item in name.split(".")[1:]:
            # Remove the dot
            s3cfg = getattr(s3cfg, item)
        settings = s3cfg.S3Config()
        # Pass into template
        current.deployment_settings = settings

        # Read settings
        model = "%s/models/000_config.py" % request.folder
        code = getcfs(model, model, None)
        environment = build_environment(request, current.response,
                                        current.session)
        environment["settings"] = settings
        def template_path():
            " Return the path of the Template config.py to load "
            path = os.path.join(request.folder,
                                "private", "templates",
                                settings.get_template(),
                                "config.py")
            return path
        environment["template_path"] = template_path
        environment["os"] = os
        environment["Storage"] = Storage
        restricted(code, environment, layer=model)

        self.db_engine = settings.get_database_type()
        (db_string, pool_size) = settings.get_database_string()

        # Get a handle to the database
        self.db = DAL(db_string,
                      #folder="%s/databases" % request.folder,
                      auto_import=True,
                      # @ToDo: Set to False until we migrate
                      migrate_enabled=True,
                      )

    # -------------------------------------------------------------------------
    def prep(self, foreigns=[], uniques=[]):
        """
            Preparation before migration

            @param foreigns : List of tuples (tablename, fieldname) to have the foreign keys removed
                              - if tablename == "all" then all tables are checked
            @param uniques  : List of tuples (tablename, fieldname) to have the unique indices removed
        """

        # Backup current database
        self.backup()

        # Remove Foreign Key constraints which need to go in next code
        for tablename, fieldname in foreigns:
            self.remove_foreign(tablename, fieldname)

        # Remove Unique indices which need to go in next code
        for tablename, fieldname in uniques:
            self.remove_unique(tablename, fieldname)

        self.db.commit()

    # -------------------------------------------------------------------------
    def post(self):
        """
            Cleanup after migration
            @ToDo
        """

        # Do prepops of new tables
        # Copy data
        pass

    # -------------------------------------------------------------------------
    def migrate(self):
        """
            Perform the migration
            @ToDo
        """

        # Update code: git pull
        # run_models_in(environment)
        # or
        # Set migrate=True in models/000_config.py
        # current.s3db.load_all_models() via applications/eden/static/scripts/tools/noop.py
        # Set migrate=False in models/000_config.py
        pass

    # -------------------------------------------------------------------------
    def backup(self):
        """
            Backup the database to a local SQLite database
        """

        import os

        db = self.db
        folder = "%s/databases/backup" % current.request.folder

        # Create clean folder for the backup
        if os.path.exists(folder):
            import shutil
            shutil.rmtree(folder)
            import time
            time.sleep(1)
        os.mkdir(folder)

        # Setup backup database
        db_bak = DAL("sqlite://backup.db", folder=folder)

        # Copy Table structure
        for tablename in db.tables:
            if tablename == "gis_location":
                table = db[tablename]
                fields = [table[field] for field in table.fields if field != "the_geom"]
                db_bak.define_table(tablename, *fields)
            else:
                db_bak.define_table(tablename, db[tablename])

        # Copy Data
        import csv
        csv.field_size_limit(2**20 * 100)  # 100 megs
        filename = "%s/data.csv" % folder
        file = open(filename, "w")
        db.export_to_csv_file(file)
        file.close()
        file = open(filename, "r")
        db_bak.import_from_csv_file(file, unique="uuid2") # designed to fail
        file.close()
        db_bak.commit()

        # Pass handle back to other functions
        self.db_bak = db_bak

    # -------------------------------------------------------------------------
    def remove_foreign(self, tablename, fieldname):
        """
            Remove a Foreign Key constraint from a table
        """

        db = self.db
        db_engine = self.db_engine
        executesql = db.executesql

        if tablename == "all":
            tables = db.tables
        else:
            tables = [tablename]

        for tablename in tables:
            if fieldname not in db[tablename].fields:
                continue

            # Modify the database
            if db_engine == "sqlite":
                # @ToDo:
                raise NotImplementedError

            elif db_engine == "mysql":
                # http://dev.mysql.com/doc/refman/5.1/en/alter-table.html
                create = executesql("SHOW CREATE TABLE `%s`;" % tablename)[0][1]
                fk = create.split("` FOREIGN KEY (`%s" % fieldname)[0].split("CONSTRAINT `").pop()
                if "`" in fk:
                    fk = fk.split("`")[0]
                sql = "ALTER TABLE `%(tablename)s` DROP FOREIGN KEY `%(fk)s`;" % \
                    dict(tablename=tablename, fk=fk)

            elif db_engine == "postgres":
                # @ToDo:
                raise NotImplementedError

            try:
                executesql(sql)
            except:
                print "Error: Table %s with FK %s" % (tablename, fk)
                import sys
                e = sys.exc_info()[1]
                print >> sys.stderr, e

    # -------------------------------------------------------------------------
    def remove_unique(self, tablename, fieldname):
        """
            Remove a Unique Index from a table
        """

        db = self.db
        db_engine = self.db_engine

        # Modify the database
        if db_engine == "sqlite":
            # @ToDo:
            raise NotImplementedError

        elif db_engine == "mysql":
            # http://dev.mysql.com/doc/refman/5.1/en/alter-table.html
            sql = "ALTER TABLE `%(tablename)s` DROP INDEX `%(fieldname)s`;" % \
                dict(tablename=tablename, fieldname=fieldname)

        elif db_engine == "postgres":
            sql = "ALTER TABLE %(tablename)s DROP CONSTRAINT %(tablename)s_%(fieldname)s_key;" % \
                dict(tablename=tablename, fieldname=fieldname)

        try:
            db.executesql(sql)
        except:
            import sys
            e = sys.exc_info()[1]
            print >> sys.stderr, e

        # Modify the .table file
        table = db[tablename]
        fields = []
        for fn in table.fields:
            field = table[fn]
            if fn == fieldname:
                field.unique = False
            fields.append(field)
        db.__delattr__(tablename)
        db.tables.remove(tablename)
        db.define_table(tablename, *fields,
                        # Rebuild the .table file from this definition
                        fake_migrate=True)

    # =========================================================================
    # OLD CODE below here
    # - There are tests for this in /tests/dbmigration
    # -------------------------------------------------------------------------
    def rename_field(self,
                     tablename,
                     fieldname_old,
                     fieldname_new,
                     attributes_to_copy=None):
        """
            Rename a field, while keeping the other properties of the field the same. 
            If there are some indexes on that table, these will be recreated and other constraints will remain unchanged too.
            
            @param tablename          : name of the table in which the field is renamed
            @param fieldname_old      : name of the original field before renaming
            @param fieldname_new      : name of the field after renaming
            @param attributes_to_copy : list of attributes which need to be copied from the old_field to the new_field (needed only in sqlite)
        """

        db = self.db
        db_engine = self.db_engine

        if db_engine == "sqlite":
            self._add_renamed_fields(db, tablename, fieldname_old, fieldname_new, attributes_to_copy)
            self._copy_field(db, tablename, fieldname_old, fieldname_new)     
            sql = "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='%s' ORDER BY name;" % \
                tablename
            list_index = db.executesql(sql)
            for element in list_index:
                search_str = "%s(%s)" % (tablename, fieldname_old)
                if element[0] is not None and search_str in element[0]:
                    sql = "CREATE INDEX %s__idx on %s(%s);" % \
                        (fieldname_new, tablename, fieldname_new)
                    try:
                        db.executesql(sql)
                    except:
                        pass

        elif db_engine == "mysql":
            field = db[tablename][fieldname_old]
            sql_type = map_type_web2py_to_sql(field.type)
            sql = "ALTER TABLE %s CHANGE %s %s %s(%s)" % (tablename,
                                                          fieldname_old,
                                                          fieldname_new,
                                                          sql_type,
                                                          field.length)
            db.executesql(sql)

        elif db_engine == "postgres":
            sql = "ALTER TABLE %s RENAME COLUMN %s TO %s" % \
                (tablename, fieldname_old, fieldname_new)
            db.executesql(sql)

    # -------------------------------------------------------------------------
    def rename_table(self,
                     tablename_old,
                     tablename_new):
        """
            Rename a table.
            If any fields reference that table, they will be handled too.
            
            @param tablename_old : name of the original table before renaming
            @param tablename_new : name of the table after renaming
        """

        try:
            sql = "ALTER TABLE %s RENAME TO %s;" % (tablename_old,
                                                    tablename_new)
            self.db.executesql(sql)
        except Exception, e:
            print e

    # -------------------------------------------------------------------------
    def list_field_to_reference(self,
                                tablename_new,
                                new_list_field,
                                list_field_name,
                                table_old_id_field,
                                tablename_old):
        """
            This method handles the migration in which a new table with a column for the 
            values they'll get from the list field is made and maybe some empty columns to be filled in later. 
            That new table has a foreign key reference back to the original table.
            Then for each value in the list field for each record in the original table, 
            they create one record in the new table that points back to the original record.

            @param tablename_new      : name of the new table to which the list field needs to migrated
            @param new_list_field     : name of the field in the new table which will hold the content of the list field
            @param list_field_name    : name of the list field in the original table
            @param table_old_id_field : name of the id field in the original table
            @param tablename_old      : name of the original table
        """

        self._create_new_table(tablename_new, new_list_field, list_field_name,
                               table_old_id_field, tablename_old)
        self._fill_the_new_table(tablename_new, new_list_field, list_field_name,
                                 table_old_id_field, tablename_old)

    # -------------------------------------------------------------------------
    def migrate_to_unique_field(self,
                                tablename,
                                field_to_update,
                                mapping_function,
                                list_of_tables=None):
        """
            Add values to a new field according to the mappings given through the mapping_function

            @param tablename        : name of the original table in which the new unique field id added
            @param field_to_update  : name of the field to be updated according to the mapping
            @param mapping_function : class instance containing the mapping functions
            @param list_of_tables   : list of tables which the table references
        """

        db = self.db
        self._add_new_fields(db, field_to_update, tablename)
        self._add_tables_temp_db(db, list_of_tables)
        self.update_field_by_mapping(db, tablename, field_to_update, mapping_function)

    # -------------------------------------------------------------------------
    def update_field_by_mapping(db,
                                tablename,
                                field_to_update,
                                mapping_function):
        """
            Update the values of an existing field according to the mappings given through the mapping_function
            - currently unused
            
            @param db               : database instance
            @param tablename        : name of the original table in which the new unique field id added
            @param field_to_update  : name of the field to be updated according to the mapping
            @param mapping_function : class instance containing the mapping functions
        """

        fields = mapping_function.fields(db)
        table = db[tablename]
        if table["id"] not in fields:
            fields.append(table["id"])
        rows = db(mapping_function.query(db)).select(*fields)
        if rows:
            try:
                rows[0][tablename]["id"]
                row_single_layer = False
            except KeyError:
                row_single_layer = True
        dict_update = {}
        for row in rows:
            if not row_single_layer:
                row_id = row[tablename]["id"]
            else:
                row_id = row["id"]
            changed_value = mapping_function.mapping(row)
            dict_update[field_to_update] = changed_value
            db(table["id"] == row_id).update(**dict_update)    

    # -------------------------------------------------------------------------
    @staticmethod
    def _map_type_list_field(old_type):
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

    # -------------------------------------------------------------------------
    def _create_new_table(self,
                          tablename_new,
                          new_list_field,
                          list_field_name,
                          table_old_id_field,
                          tablename_old):
        """
            This function creates the new table which is used in the list_field_to_reference migration.
            That new table has a foreign key reference back to the original table.
            
            @param tablename          : name of the new table to which the list field needs to migrated
            @param new_list_field     : name of the field in the new table which will hold the content of the list field
            @param list_field_name    : name of the list field in the original table
            @param table_old_id_field : name of the id field in the original table
            @param tablename_old      : name of the original table
        """

        db = self.db
        new_field_type = self._map_type_list_field(db[tablename_old][list_field_name].type)
        new_field = Field(new_list_field, new_field_type)
        new_id_field = Field("%s_%s" % (tablename_old, table_old_id_field),
                             "reference %s" % tablename_old)
        db.define_table(tablename,
                        new_id_field,
                        new_field)

    # -------------------------------------------------------------------------
    @staticmethod
    def _fill_the_new_table(tablename_new,
                            new_list_field,
                            list_field_name,
                            table_old_id_field,
                            tablename_old):
        """
            This function is used in the list_field_to_reference migration.
            For each value in the list field for each record in the original table, 
            they create one record in the new table that points back to the original record.
            
            @param tablename_new      : name of the new table to which the list field needs to migrated
            @param new_list_field     : name of the field in the new table which will hold the content of the list field
            @param list_field_name    : name of the list field in the original table
            @param table_old_id_field : name of the id field in the original table
            @param tablename_old      : name of the original table
        """

        update_dict = {}
        table_old = db[tablename_old]
        table_new = db[tablename_new]
        for row in db().select(table_old[table_old_id_field],
                               table_old[list_field_name]):
            for element in row[list_field_name]:
                update_dict[new_list_field] = element
                update_dict["%s_%s" % (tablename_old, table_old_id_field)] = row[table_old_id_field]
                table_new.insert(**update_dict)

    # -------------------------------------------------------------------------
    @staticmethod
    def _add_renamed_fields(db,
                            tablename,
                            fieldname_old,
                            fieldname_new,
                            attributes_to_copy):
        """
            Add a field in table mentioned while renaming a field.
            The renamed field is added separately to the table with the same properties as the original field.

            @param db : database instance
        """

        table = db[tablename]
        if hasattr(table, "_primarykey"):
            primarykey = table._primarykey
        else:
            primarykey = None
        field_new = Field(fieldname_new)
        for attribute in attributes_to_copy:
            exec_str = "field_new.%(attribute)s = table[fieldname_old].%(attribute)s" % \
                dict(attribute=attribute)
            exec exec_str in globals(), locals()
        db.define_table(tablename,
                        table, # Table to inherit from
                        field_new,
                        primarykey=primarykey)

    # -------------------------------------------------------------------------
    @staticmethod
    def _copy_field(db, tablename, fieldname_old, fieldname_new):
        """
            Copy all the values from old_field into new_field

            @param db : database instance
        """

        dict_update = {}
        field_old = db[tablename][fieldname_old]
        for row in db().select(field_old):
            dict_update[fieldname_new] = row[fieldname_old]
            query = (field_old == row[fieldname_old])
            db(query).update(**dict_update)

    # -------------------------------------------------------------------------
    @staticmethod
    def map_type_web2py_to_sql(dal_type):
        """
            Map the web2py type into SQL type
            Used when writing SQL queries to change the properties of a field
            
            Mappings:
            string   -->   Varchar
        """

        if dal_type == "string":
            return "varchar"
        else:
            return dal_type

    # -------------------------------------------------------------------------
    @staticmethod
    def _add_new_fields(db, new_unique_field, tablename):
        """
            This function adds a new _unique_ field into the table, while keeping all the rest of 
            the properties of the table unchanged

            @param db : database instance
        """

        new_field = Field(new_unique_field, "integer")
        table = db[tablename]
        if hasattr(table, "_primarykey"):
            primarykey = table._primarykey
        else:
            primarykey = None
        db.define_table(tablename,
                        table, # Table to inherit from
                        new_field,
                        primarykey=primarykey)

    # -------------------------------------------------------------------------
    def _add_tables_temp_db(self,
                            temp_db,
                            list_of_tables):
        """
            This field adds tables to the temp_db from the global db
            these might be used for the running queries or validating values. 
        """

        for tablename in list_of_tables:
            temp_db.define_table(tablename, self.db[tablename])

# END =========================================================================
