# -*- coding: utf-8 -*-

""" S3 Framework Tables

    @copyright: 2009-2019 (c) Sahana Software Foundation
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

__all__ = ("S3HierarchyModel",
           "S3DashboardModel",
           "S3DynamicTablesModel",
           "s3_table_rheader",
           )

import random

from gluon import *
from ..s3 import *

# =============================================================================
class S3HierarchyModel(S3Model):
    """ Model for stored object hierarchies """

    names = ("s3_hierarchy",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Stored Object Hierarchy
        #
        tablename = "s3_hierarchy"
        self.define_table(tablename,
                          Field("tablename", length=64),
                          Field("dirty", "boolean",
                                default = False,
                                ),
                          Field("hierarchy", "json"),
                          *S3MetaFields.timestamps())

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if module is disabled """

        return {}

# =============================================================================
class S3DashboardModel(S3Model):
    """ Model for stored dashboard configurations """

    names = ("s3_dashboard",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Stored Dashboard Configuration
        #
        tablename = "s3_dashboard"
        self.define_table(tablename,
                          Field("controller", length = 64,
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("function", length = 512,
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("version", length = 40,
                                readable = False,
                                writable = False,
                                ),
                          Field("next_id", "integer",
                                readable = False,
                                writable = False,
                                ),
                          Field("layout",
                                default = S3DashboardConfig.DEFAULT_LAYOUT,
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("title",
                                ),
                          Field("widgets", "json",
                                requires = IS_JSONS3(),
                                ),
                          Field("active", "boolean",
                                default = True,
                                ),
                          *s3_meta_fields())

        self.configure(tablename,
                       onaccept = self.dashboard_onaccept,
                       )

        # ---------------------------------------------------------------------
        # Link Dashboard Config <=> Person Entity
        #
        # @todo

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if module is disabled """

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def dashboard_onaccept(form):
        """
            On-accept routine for dashboard configurations
                - make sure there is at most one active config for the same
                  controller/function
        """

        db = current.db

        try:
            record_id = form.vars.id
        except AttributeError:
            return

        table = current.s3db.s3_dashboard
        query = table.id == record_id

        row = db(query).select(table.id,
                               table.controller,
                               table.function,
                               table.active,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return

        if row.active:
            # Deactivate all other configs for the same controller/function
            query = (table.controller == row.controller) & \
                    (table.function == row.function) & \
                    (table.id != row.id) & \
                    (table.active == True) & \
                    (table.deleted != True)
            db(query).update(active = False)

# =============================================================================
class S3DynamicTablesModel(S3Model):
    """ Model for dynamic tables """

    names = ("s3_table",
             "s3_table_id",
             "s3_field",
             "s3_field_id",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        define_table = self.define_table
        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Dynamic Table
        #
        tablename = "s3_table"
        define_table(tablename,
                     Field("title",
                           label = T("Title"),
                           ),
                     Field("name", length=128, unique=True, notnull=True,
                           # Set a random name as default, so this field
                           # can be hidden from the users (one-time default)
                           default = "%s_%s" % (DYNAMIC_PREFIX, self.random_name()),
                           label = T("Table Name"),
                           represent = self.s3_table_name_represent(),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LOWER(),
                                       IS_MATCH("^%s_[a-z0-9_]+$" % DYNAMIC_PREFIX,
                                                error_message = "Invalid table name",
                                                ),
                                       IS_LENGTH(128),
                                       IS_NOT_IN_DB(db, "s3_table.name"),
                                       ],
                           ),
                     Field("mobile_form", "boolean",
                           label = T("Expose mobile form"),
                           default = True,
                           ),
                     Field("mobile_data", "boolean",
                           label = T("Expose data for mobile clients"),
                           default = False,
                           ),
                     Field("settings", "json",
                           label = T("Settings"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Settings"),
                                                           T("Configuration settings for this table (JSON object)"),
                                                           ),
                                         ),
                           ),
                     # Link this table to a certain master key
                     self.auth_masterkey_id(),
                     #s3_comments(),
                     *s3_meta_fields(),
                     on_define = lambda table: \
                                 [self.s3_table_set_before_write(table)]
                     )

        # Components
        self.add_components(tablename,
                            s3_field = "table_id",
                            )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Table"),
            title_display = T("Table Details"),
            title_list = T("Tables"),
            title_update = T("Edit Table"),
            label_list_button = T("List Tables"),
            label_delete_button = T("Delete Table"),
            msg_record_created = T("Table created"),
            msg_record_modified = T("Table updated"),
            msg_record_deleted = T("Table deleted"),
            msg_list_empty = T("No Tables currently defined"),
        )

        # Reusable field
        represent = S3Represent(lookup=tablename, show_link=True)
        table_id = S3ReusableField("table_id", "reference %s" % tablename,
                                   label = T("Table"),
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          )),
                                   sortby = "name",
                                   )

        # ---------------------------------------------------------------------
        # Field in Dynamic Table
        #
        tablename = "s3_field"
        define_table(tablename,
                     table_id(empty = False,
                              ondelete = "CASCADE",
                              ),
                     Field("label",
                           label = T("Label"),
                           ),
                     Field("name", length=128, notnull=True,
                           label = T("Field Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_DYNAMIC_FIELDNAME(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     Field("field_type", notnull=True,
                           default = "string",
                           label = T("Field Type"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_DYNAMIC_FIELDTYPE(),
                                       ],
                           ),
                     Field("require_unique", "boolean",
                           default = False,
                           label = T("Must be unique"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Must be unique"),
                                                           T("Field value must be unique"),
                                                           ),
                                         ),
                           ),
                     Field("require_not_empty", "boolean",
                           default = False,
                           label = T("Is required"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Is required"),
                                                           T("Field value must not be empty"),
                                                           ),
                                         ),
                           ),
                     Field("options", "json",
                           label = T("Options"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Options"),
                                                           T("Fixed set of selectable values for this field (JSON object)"),
                                                           ),
                                         ),
                           ),
                     Field("default_value",
                           label = T("Default Value"),
                           ),
                     Field("component_key", "boolean",
                           label = T("Is Component Key"),
                           default = False,
                           represent = s3_yes_no_represent,
                           ),
                     Field("master",
                           # Hidden field, will be set onaccept
                           readable = False,
                           writable = False,
                           ),
                     Field("component_alias", length=128,
                           label = T("Component Alias"),
                           requires = IS_EMPTY_OR((IS_LENGTH(128), IS_LOWER())),
                           ),
                     Field("component_tab", "boolean",
                           label = T("Show on Tab"),
                           default = False,
                           represent = s3_yes_no_represent,
                           ),
                     Field("settings", "json",
                           label = T("Settings"),
                           requires = IS_EMPTY_OR(IS_JSONS3()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Settings"),
                                                           T("Configuration settings for this field (JSON object)"),
                                                           ),
                                         ),
                           ),
                     s3_comments(label = T("Tooltip"),
                                 represent = s3_text_represent,
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Tooltip"),
                                                                 T("Explanation of the field to be displayed in forms"),
                                                                 ),
                                               ),
                                 ),
                     *s3_meta_fields())

        # Table configuration
        self.configure(tablename,
                       deduplicate = S3Duplicate(primary=("table_id", "name")),
                       onvalidation = self.s3_field_onvalidation,
                       onaccept = self.s3_field_onaccept,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Field"),
            title_display = T("Field Details"),
            title_list = T("Fields"),
            title_update = T("Edit Field"),
            label_list_button = T("List Fields"),
            label_delete_button = T("Delete Field"),
            msg_record_created = T("Field created"),
            msg_record_modified = T("Field updated"),
            msg_record_deleted = T("Field deleted"),
            msg_list_empty = T("No Fields currently defined"),
        )

        # Reusable field
        represent = S3Represent(lookup=tablename, show_link=True)
        field_id = S3ReusableField("field_id", "reference %s" % tablename,
                                   label = T("Field"),
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                            IS_ONE_OF(db, "%s.id" % tablename,
                                                      represent,
                                                      )),
                                   sortby = "name",
                                   )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"s3_table_id": table_id,
                "s3_field_id": field_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def random_name():
        """
            Generate a random name

            @return: an 8-character random name
        """

        alpha = "abcdefghijklmnopqrstuvwxyz"
        return ''.join(random.choice(alpha) for _ in range(8))

    # -------------------------------------------------------------------------
    @classmethod
    def s3_table_set_before_write(cls, table):
        """
            Set functions to call before write

            @param table: the table (s3_table)
        """

        update_default = cls.s3_table_name_update_default

        table._before_insert.append(update_default)
        table._before_update.append(lambda s, data: update_default(data))

    # -------------------------------------------------------------------------
    @classmethod
    def s3_table_name_update_default(cls, data):
        """
            Set a new default table name when the current default
            is written (to prevent duplicates, i.e. single-use default)

            @param data: the data currently being written

            @returns: nothing (otherwise insert/update will not work)
        """

        table = current.s3db.s3_table
        field = table.name

        name = data.get("name")
        if not name or name == field.default:
            # The name currently being written is the default,
            # => set a new default for subsequent writes
            field.default = "%s_%s" % (DYNAMIC_PREFIX, cls.random_name())

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_table_name_represent(c="default", f="table"):
        """
            Return a representation function for dynamic table names,
            renders the table name as a link to the table controller

            @param c: the controller prefix
            @param f: the function name

            @returns: function
        """

        def represent(value):

            if value and "_" in value:
                suffix = value.split("_", 1)[1]
                return A(value, _href=URL(c=c, f=f, args=[suffix]))
            else:
                return value

        return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_field_onvalidation(form):
        """
            On-validation routine for s3_fields:
                - field name must be unique within the table
                - @ToDo: Check for Reserved Words
        """

        db = current.db
        table = db.s3_field

        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        record = form.record if hasattr(form, "record") else None

        # Get previous values if record exists
        if record_id:
            fields_required = ("table_id",
                               "name",
                               "field_type",
                               "component_key",
                               "component_alias",
                               )
            if not record:
                missing = fields_required
            else:
                missing = []
                for fieldname in fields_required:
                    if fieldname not in record:
                        missing.append(fieldname)
            if missing:
                query = (table.id == record_id)
                record = db(query).select(limitby=(0, 1), *missing).first()

        # Get the table ID
        table_id = None
        if "table_id" in form_vars:
            table_id = form_vars.table_id
        elif record and "table_id" in record:
            table_id = record.table_id
        else:
            table_id = table.table_id.default

        # Verify field name
        if "name" in form_vars:
            new_name = form_vars.name

            # Get the current field name
            if record:
                current_name = record.name
            else:
                current_name = None

            # Verify that new field name is unique within the table
            if new_name != current_name and table_id:
                query = (table.name == new_name) & \
                        (table.table_id == table_id) & \
                        (table.deleted != True)
                if record_id:
                    query &= (table.id != record_id)
                row = db(query).select(table.id,
                                       limitby = (0, 1),
                                       ).first()
                if row:
                    form.errors["name"] = "A field with this name already exists in this table"

        # Verify component settings
        if "component_key" in form_vars:
            component_key = form_vars.component_key
        elif record:
            component_key = record.component_key
        else:
            component_key = table.component_key.default
        if component_key:

            # Determine the master table name
            master = None
            if "field_type" in form_vars:
                field_type = form_vars.field_type
            elif record:
                field_type = record.field_type
            else:
                field_type = table.field_type.default
            field_type = str(field_type)
            if field_type[:10] == "reference ":
                ktablename = field_type.split(" ", 1)[1]
                if "." in ktablename:
                    ktablename = ktablename.split(".", 1)[0]
                master = ktablename

            # Make sure the alias is unique for the master table
            if "component_alias" in form_vars:
                component_alias = form_vars.component_alias
            elif record:
                component_alias = record.component_alias
            if not component_alias:
                ttable = current.s3db.s3_table
                query = ttable.id == table_id
                row = db(query).select(ttable.name,
                                       limitby = (0, 1),
                                       ).first()
                tablename = row.name
                component_alias = tablename.split("_", 1)[1]
                form_vars.component_alias = component_alias

            # Verify that no other dynamic component with
            # this alias exists for the same master table
            query = ((table.field_type == "reference %s" % master) | \
                     (table.field_type.like("reference %s.%%" % master))) & \
                    (table.component_key == True) & \
                    (table.component_alias == component_alias) & \
                    (table.deleted != True)
            if record_id:
                query &= (table.id != record_id)
            row = db(query).select(table.id, limitby=(0, 1)).first()
            if row:
                form.errors["component_alias"] = "A component with this alias already exists for this master table"

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_field_onaccept(form):
        """
            On-accept routine for s3_field:
                - set master table name for component keys (from field type)
        """

        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            return

        db = current.db
        table = db.s3_field
        row = db(table.id == record_id).select(table.id,
                                               table.component_key,
                                               table.field_type,
                                               limitby = (0, 1),
                                               ).first()

        master = None
        if row and row.component_key:
            field_type = str(row.field_type)
            if field_type[:10] == "reference ":
                ktablename = field_type.split(" ", 1)[1]
                if "." in ktablename:
                    ktablename = ktablename.split(".", 1)[0]
                master = ktablename

        row.update_record(master=master)

# =============================================================================
def s3_table_rheader(r, tabs=None):

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    rheader = None

    record = r.record
    if record:

        T = current.T
        rheader_fields = []

        if r.tablename == "s3_table":

            if not tabs:

                # Use default/tables as native controller for s3_table
                tab_vars = {"native": True}

                tabs = [(T("Table"), None, tab_vars),
                        (T("Fields"), "field", tab_vars),
                        ]

            rheader_fields = [["name"],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = r.resource.table,
                                                         record = record,
                                                         )

    return rheader

# END =========================================================================
