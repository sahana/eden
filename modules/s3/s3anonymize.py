# -*- coding: utf-8 -*-

""" S3 Person Record Anonymizing

    @copyright: 2018-2018 (c) Sahana Software Foundation
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

from gluon import current

from s3rest import S3Method
from s3query import FS, S3Joins

__all__ = ("S3Anonymize",
           )

# =============================================================================
class S3Anonymize(S3Method):
    """ REST Method to Anonymize Person Records """

    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request instance
            @param attr: controller parameters

            @return: output data (JSON)
        """

        output = {}

        table, record_id = self.get_target_id()
        if not table:
            r.error(405, "Anonymizing not configured for resource")
        if not record_id:
            r.error(400, "No target record specified")
        if not self.permitted(table, record_id):
            r.error(403, "Operation not permitted")

        if r.representation == "json":
            if r.http == "GET":
                output = self.options(table, record_id)
            elif r.http == "POST":
                output = self.anonymize(table, record_id)
            else:
                r.error(405, current.ERROR.BAD_METHOD)
        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        # Set Content Type
        current.response.headers["Content-Type"] = "application/json"

        return output

    # -------------------------------------------------------------------------
    @classmethod
    def anonymize(cls, table, record_id):
        """
            TODO implement
        """

        # return JSON message

        pass

    # -------------------------------------------------------------------------
    @classmethod
    def options(cls, table, record_id):
        """
            TODO implement
        """

        # return JSON options

        pass

    # -------------------------------------------------------------------------
    @classmethod
    def action_button(cls, table, record_id):
        """
            TODO implement
        """

        # Generate action-button, inject JS

        # Store button UID in session?

        pass

    # -------------------------------------------------------------------------
    def get_target_id(self):
        """
            Determine the target table and record ID

            @return: tuple (table, record_id)
        """

        resource = self.resource

        rules = resource.get_config("anonymize")
        if not rules:
            return None, None

        return resource.table, self.record_id

    # -------------------------------------------------------------------------
    def permitted(self, table, record_id):
        """
            Check permissions to anonymize the target record

            @param table: the target Table
            @param record_id: the target record ID

            @return: True|False
        """

        has_permission = current.auth.s3_has_permission

        return has_permission("update", table, record_id=record_id) and \
               has_permission("delete", table, record_id=record_id)

    # -------------------------------------------------------------------------
    @classmethod
    def cascade(cls, table, record_ids, rules):
        """
            Apply cascade of rules to anonymize records

            @param table: the Table
            @param record_ids: a set of record IDs
            @param rules: the rules for this Table

            @raises Exception: if the cascade failed due to DB constraints
                               or invalid rules; callers should roll back
                               the transaction if an exception is raised
        """

        s3db = current.s3db

        pkey = table._id.name

        cascade = rules.get("cascade")
        if cascade:

            fieldnames = set(rule.get("match", pkey) for _, rule in cascade)
            if pkey not in fieldnames:
                fieldnames.add(pkey)
            fields = [table[fn] for fn in fieldnames]

            db = current.db
            rows = db(table._id.belongs(record_ids)).select(*fields)

            for tablename, rule in cascade:

                lookup = rule.get("lookup")
                if lookup:
                    # Explicit look-up function, call with master table+rows,
                    # as well as the name of the related table; should return
                    # a set/tuple/list of record ids in the related table
                    ids = lookup(table, rows, tablename)
                else:
                    key = rule.get("key")
                    if not key:
                        continue

                    field = rule.get("match", pkey)
                    match = set(row[field] for row in rows)

                    # Resolve key and construct query
                    resource = s3db.resource(tablename, components=[])
                    rq = FS(key).belongs(match)
                    query = rq.query(resource)

                    # Construct necessary joins
                    joins = S3Joins(tablename)
                    joins.extend(rq._joins(resource)[0])
                    joins = joins.as_list()

                    # Extract the target table IDs
                    target_rows = db(query).select(resource._id,
                                                   join = joins,
                                                   )
                    ids = set(row[resource._id.name] for row in target_rows)

                # Recurse into related table
                if ids:
                    cls.cascade(resource.table, ids, rule)

        # Apply field rules
        field_rules = rules.get("cleanup")
        if field_rules:
            cls.apply_field_rules(table, record_ids, field_rules)

        # Apply deletion rules
        if rules.get("delete"):
            resource = s3db.resource(table, id=list(record_ids))
            resource.delete(cascade=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def apply_field_rules(table, record_ids, rules):
        """
            Apply field rules on a set of records in a table

            @param table: the Table
            @param record_ids: the record IDs
            @param rules: the rules

            @raises Exception: if the field rules could not be applied
                               due to DB constraints or invalid rules;
                               callers should roll back the transaction
                               if an exception is raised
        """

        fields = [table[fn] for fn in rules if fn in table.fields]
        if table._id.name not in rules:
            fields.insert(0, table._id)

        # Select the records
        query = table._id.belongs(record_ids)
        rows = current.db(query).select(*fields)

        pkey = table._id.name

        s3db = current.s3db
        update_super = s3db.update_super
        onaccept = s3db.onaccept

        for row in rows:
            data = {}
            for fieldname, rule in rules.items():

                if fieldname in table.fields:
                    field = table[fieldname]
                else:
                    continue

                if rule == "remove":
                    # Set to None
                    if field.notnull:
                        raise ValueError("Cannot remove %s - must not be NULL" % field)
                    else:
                        data[fieldname] = None

                elif rule == "reset":
                    # Reset to the field's default value
                    default = field.default
                    if default is None and field.notnull:
                        raise ValueError("Cannot reset %s - default value None violates notnull-constraint")
                    data[fieldname] = default

                elif callable(rule):
                    # Callable rule to procude a new value
                    data[fieldname] = rule(field, row[field])

                elif type(rule) is tuple:
                    method, value = rule
                    if method == "set":
                        # Set a fixed value
                        data[fieldname] = value

            if data:
                success = row.update_record(**data)
                if not success:
                    raise ValueError("Could not clean %s record" % table)

                update_super(table, row)

                data[pkey] = row[pkey]
                onaccept(table, data, method="update")

# END =========================================================================
