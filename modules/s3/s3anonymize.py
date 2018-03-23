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

        output = {}

        if r.representation == "json":
            if r.http == "GET":
                pass
            elif r.http == "POST":
                pass
            else:
                r.error(405, current.ERROR.BAD_METHOD)
        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    @classmethod
    def anonymize(cls, tablename, record_id, rules=None):
        """
            TODO implement
        """

        pass

    # -------------------------------------------------------------------------
    @classmethod
    def cascade(cls, table, record_ids, rules):
        """
            TODO docstring
            TODO complete implementation
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

                # TODO move ids from key/match into subfunction
                # TODO allow explicit lookup function

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
                cls.cascade(resource.table, ids, rule)

        # Apply field rules
        field_rules = rules.get("cleanup")
        if field_rules:
            cls.apply_field_rules(table, record_ids, field_rules)

        # Apply deletion rules
        # TODO override auth to enforce deletion?
        #      => not necessary for the purpose of anonymization
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

            TODO check success
        """

        fields = [table[fn] for fn in rules if fn in table.fields]
        if table._id.name not in rules:
            fields.insert(0, table._id)

        # Select the records
        query = table._id.belongs(record_ids)
        rows = current.db(query).select(*fields)

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
                row.update_record(**data)
                # TODO update_super, onaccept

# END =========================================================================
