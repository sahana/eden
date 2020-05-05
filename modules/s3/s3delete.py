# -*- coding: utf-8 -*-

""" S3 Record Deletion

    @copyright: 2018-2020 (c) Sahana Software Foundation
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

import json
import sys

from gluon import current
from gluon.tools import callback

from s3dal import original_tablename, Row
from .s3utils import s3_get_last_record_id, s3_has_foreign_key, s3_remove_last_record_id

__all__ = ("S3Delete",
           )

DELETED = "deleted"

# =============================================================================
class S3Delete(object):
    """
        Process to delete/archive records in a S3Resource
    """

    def __init__(self, resource, archive=None, representation=None):
        """
            Constructor

            @param resource: the S3Resource to delete records from
            @param archive: True|False to override global
                            security.archive_not_delete setting
            @param representation: the request format (for audit, optional)
        """

        self.resource = resource
        self.representation = representation

        # Get unaliased table
        tablename = self.tablename = original_tablename(resource.table)
        table = self.table = current.db[tablename]

        # Archive or hard-delete?
        if archive is None:
            if current.deployment_settings.get_security_archive_not_delete() and \
               DELETED in table:
                archive = True
            else:
                archive = False
        self.archive = archive

        # Callbacks
        get_config = resource.get_config
        self.prepare = get_config("ondelete_cascade")
        self.ondelete = get_config("ondelete")

        # Initialize properties
        self._super_keys = None
        self._foreign_keys = None
        self._references = None
        self._restrictions = None

        self._done = False

        # Initialize instance variables
        self.errors = {}
        self.permission_error = False

    # -------------------------------------------------------------------------
    def __call__(self, cascade=False, replaced_by=None, skip_undeletable=False):
        """
            Main deletion process, deletes/archives all records
            in the resource

            @param cascade: this is called as a cascade-action from another
                            process (e.g. another delete)
            @param skip_undeletable: delete whatever is possible, skip
                                     undeletable rows
            @param replaced_by: dict of {replaced_id: replacement_id},
                                used by record merger to log which record
                                has replaced which
        """

        # Must not re-use instance
        if self._done:
            raise RuntimeError("deletion already processed")
        self._done = True

        tablename = self.tablename

        # Check the entire cascade, rather than breaking out after the
        # first error - debug-only, this can be many errors
        # (NB ?debug=1 alone won't help if logging is off in 000_config.py)
        check_all = current.response.s3.debug

        # Look up all rows that are to be deleted
        rows = self.extract()
        if not rows:
            # No rows to delete
            # => not an error, but log anyway to assist caller debugging
            if not cascade:
                current.log.debug("Delete %s: no rows found" % tablename)
            return 0
        else:
            first = rows[0]
            if hasattr(first, tablename) and isinstance(first[tablename], Row):
                # Rows are the result of a join (due to extra_fields)
                joined = True
            else:
                joined = False

        table = self.table
        pkey = table._id.name

        add_error = self.add_error

        # Check permissions and prepare records
        has_permission = current.auth.s3_has_permission
        prepare = self.prepare

        records = []
        for row in rows:

            record = getattr(row, tablename) if joined else row
            record_id = record[pkey]

            # Check permissions
            if not has_permission("delete", table, record_id=record_id):
                self.permission_error = True
                add_error(record_id, "not permitted")
                continue

            # Run table-specific ondelete-cascade
            if prepare:
                try:
                    callback(prepare, record, tablename=tablename)
                except Exception:
                    # Exception indicates record is undeletable
                    add_error(record_id, sys.exc_info()[1])
                    continue

            records.append(record)

        # Identify deletable records
        deletable = self.check_deletable(records, check_all=check_all)

        # If on cascade or not skipping undeletable rows: exit immediately
        if self.errors and (cascade or not skip_undeletable):
            self.set_resource_error()
            if not cascade:
                self.log_errors()
            return 0

        # Delete the records
        db = current.db

        audit = current.audit
        resource = self.resource
        prefix, name = resource.prefix, resource.name

        ondelete = self.ondelete
        delete_super = current.s3db.delete_super

        num_deleted = 0
        for row in deletable:

            record_id = row[pkey]
            success = True

            if self.archive:
                # Run automatic deletion cascade
                success = self.cascade(row, check_all=check_all)

            if success:
                # Unlink all super-records
                success = delete_super(table, row)
                if not success:
                    add_error(record_id, "super-entity deletion failed")

            if success:
                # Auto-delete linked record if appropriate
                self.auto_delete_linked(row)

                # Archive/delete the row itself
                if self.archive:
                    success = self.archive_record(row, replaced_by=replaced_by)
                else:
                    success = self.delete_record(row)

            if success:
                # Postprocess delete

                # Clear session
                if s3_get_last_record_id(tablename) == record_id:
                    s3_remove_last_record_id(tablename)

                # Audit
                audit("delete", prefix, name,
                      record = record_id,
                      representation = self.representation,
                      )

                # On-delete hook
                if ondelete:
                    callback(ondelete, row)

                # Subsequent cascade errors would roll back successful
                # deletions too => we want to prevent that when skipping
                # undeletable rows, so commit here if this is the master
                # process
                if not cascade and skip_undeletable:
                    db.commit()

                num_deleted += 1

            elif not cascade:
                # Master process failure
                db.rollback()
                self.log_errors()

                if skip_undeletable:
                    # Try next row
                    continue
                else:
                    # Exit immediately
                    break
            else:
                # Cascade failure, no point to try any other row
                # - will be rolled back by master process
                break

        self.set_resource_error()
        return num_deleted

    # -------------------------------------------------------------------------
    def extract(self):
        """
             Extract the rows to be deleted

             @returns: a Rows instance
        """

        table = self.table

        # Determine which fields to extract
        fields = [table._id.name]
        if "uuid" in table.fields:
            fields.append("uuid")
        fields.extend(list(set(self.super_keys) | set(self.foreign_keys)))

        # Extract the records (as Rows)
        rows = self.resource.select(fields,
                                    limit = None,
                                    as_rows = True,
                                    )

        return rows

    # -------------------------------------------------------------------------
    def check_deletable(self, rows, check_all=False):
        """
            Check which rows in the set are deletable, collect all errors

            @param rows: the Rows to be deleted
            @param check_all: find all restrictions for each record
                              rather than from just one table (not
                              standard because of performance cost)

            @returns: array of Rows found to be deletable
                      NB those can still fail further down the cascade
        """

        db = current.db

        tablename = self.tablename
        table = self.table
        pkey = table._id.name

        deletable = set()
        for row in rows:
            record_id = row[pkey]
            deletable.add(record_id)

        if self.archive:

            add_error = self.add_error
            errors = {}

            record_ids = set(deletable) if check_all else deletable
            for restriction in self.restrictions:

                tn = restriction.tablename
                rtable = db[tn]
                rtable_id = rtable._id

                query = (restriction.belongs(record_ids))
                if tn == tablename:
                    query &= (restriction != rtable_id)
                if DELETED in rtable:
                    query &= (rtable[DELETED] == False)

                count = rtable_id.count()
                rrows = db(query).select(count,
                                         restriction,
                                         groupby = restriction,
                                         )

                fname = str(restriction)
                for rrow in rrows:
                    # Collect errors per restricted record
                    restricted = rrow[restriction]
                    if restricted in errors:
                        restrictions = errors[restricted]
                    else:
                        restrictions = errors[restricted] = {}
                    restrictions[fname] = rrow[count]

                    # Remove restricted record from deletables
                    deletable.discard(restricted)

            # Aggregate all errors
            if errors:
                for record_id, restrictions in errors.items():
                    msg = ", ".join("%s (%s records)" % (k, v)
                                    for k, v in restrictions.items()
                                    )
                    add_error(record_id, "restricted by %s" % msg)


        return [row for row in rows if row[pkey] in deletable]

    # -------------------------------------------------------------------------
    def cascade(self, row, check_all=False):
        """
            Run the automatic deletion cascade: remove or update records
            referencing this row with ondelete!="RESTRICT"

            @param row: the Row to delete
            @param check_all: process the entire cascade to reveal all
                              errors (rather than breaking out of it after
                              the first error)
        """

        tablename = self.tablename
        table = self.table
        pkey = table._id.name
        record_id = row[pkey]

        success = True

        db = current.db
        define_resource = current.s3db.resource
        add_error = self.add_error

        references = self.references
        for reference in references:

            fn = reference.name
            tn = reference.tablename
            rtable = db[tn]

            query = (reference == record_id)
            if tn == tablename:
                query &= (reference != rtable._id)

            ondelete = reference.ondelete
            if ondelete == "CASCADE":
                # NB permission check on target included, i.e. the right
                #    to delete a record does not imply the right to remove
                #    records referencing it
                rresource = define_resource(tn,
                                            filter = query,
                                            unapproved = True,
                                            )
                delete = S3Delete(rresource,
                                  archive = self.archive,
                                  representation = self.representation,
                                  )
                delete(cascade=True)
                if delete.errors:
                    success = False
                    add_error(record_id, delete.errors)
                    if check_all:
                        continue
                    else:
                        break
            else:
                # NB no permission check on target here, i.e. the right
                #    to delete a record overrides the right to keep an
                #    annullable reference to it
                if ondelete == "SET NULL":
                    default = None
                elif ondelete == "SET DEFAULT":
                    default = reference.default
                else:
                    continue

                if DELETED in rtable.fields:
                    query &= rtable[DELETED] == False
                try:
                    db(query).update(**{fn: default})
                except Exception:
                    success = False
                    add_error(record_id, sys.exc_info()[1])
                    if check_all:
                        continue
                    else:
                        break

        return success

    # -------------------------------------------------------------------------
    def auto_delete_linked(self, row):
        """
            Auto-delete linked records if row was the last link

            @param row: the Row about to get deleted
        """

        resource = self.resource
        linked = resource.linked

        if linked and resource.autodelete and linked.autodelete:

            table = self.table
            rkey = linked.rkey
            if rkey in row:
                this_rkey = row[rkey]

                # Check for other links to the same linked record
                query = (table._id != row[table._id.name]) & \
                        (table[rkey] == this_rkey)
                if DELETED in table:
                    query &= (table[DELETED] != True)
                remaining = current.db(query).select(table._id,
                                                     limitby = (0, 1),
                                                     ).first()
                if not remaining:
                    # Try to delete the linked record
                    s3db = current.s3db
                    fkey = linked.fkey
                    linked_table = s3db.table(linked.tablename)
                    query = (linked_table[fkey] == this_rkey)
                    linked = s3db.resource(linked_table,
                                           filter = query,
                                           unapproved = True,
                                           )
                    delete = S3Delete(linked,
                                      archive = self.archive,
                                      representation = self.representation,
                                      )
                    delete(cascade=True)
                    if delete.errors:
                        delete.log_errors()

    # -------------------------------------------------------------------------
    # Record Archiving/Deletion
    # -------------------------------------------------------------------------
    def archive_record(self, row, replaced_by=None):
        """
            Archive ("soft-delete") a record

            @param row: the Row to delete
            @param replaced_by: dict of {replaced_id: replacement_id},
                                used by record merger to log which record
                                has replaced which

            @returns: True for success, False on error
        """

        table = self.table
        table_fields = table.fields

        record_id = row[table._id.name]
        data = {"deleted": True}

        # Reset foreign keys to resolve constraints
        fk = {}
        for fname in self.foreign_keys:
            value = row[fname]
            if value:
                fk[fname] = value
            if not table[fname].notnull:
                data[fname] = None
        if fk and "deleted_fk" in table_fields:
            # Remember any deleted foreign keys
            data["deleted_fk"] = json.dumps(fk)

        # Remember the replacement record (used by record merger)
        if "deleted_rb" in table_fields and replaced_by:
            rb = replaced_by.get(str(record_id))
            if rb:
                data["deleted_rb"] = rb

        try:
            result = current.db(table._id == record_id).update(**data)
        except Exception:
            # Integrity Error
            self.add_error(record_id, sys.exc_info()[1])
            return False

        if not result:
            # Unknown Error
            self.add_error(record_id, "archiving failed")
            return False
        else:
            return True

    # -------------------------------------------------------------------------
    def delete_record(self, row):
        """
            Delete a record

            @param row: the Row to delete

            @returns: True for success, False on error
        """

        table = self.table
        record_id = row[table._id.name]

        try:
            result = current.db(table._id == record_id).delete()
        except Exception:
            # Integrity Error
            self.add_error(record_id, sys.exc_info()[1])
            return False

        if not result:
            # Unknown Error
            self.add_error(record_id, "deletion failed")
            return False
        else:
            return True

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def super_keys(self):
        """
            List of super-keys (instance links) in this resource

            @returns: a list of field names
        """

        super_keys = self._super_keys

        if super_keys is None:

            table_fields = self.table.fields

            super_keys = []
            append = super_keys.append

            s3db = current.s3db
            supertables = s3db.get_config(self.tablename, "super_entity")
            if supertables:
                if not isinstance(supertables, (list, tuple)):
                    supertables = [supertables]
                for sname in supertables:
                    stable = s3db.table(sname) \
                             if isinstance(sname, str) else sname
                    if stable is None:
                        continue
                    key = stable._id.name
                    if key in table_fields:
                        append(key)

            self._super_keys = super_keys

        return super_keys

    # -------------------------------------------------------------------------
    @property
    def foreign_keys(self):
        """
            List of foreign key fields in this resource

            @returns: a list of field names
        """

        # Produce a list of foreign key Fields in self.table
        foreign_keys = self._foreign_keys

        if foreign_keys is None:
            table = self.table
            foreign_keys = [f for f in table.fields
                              if s3_has_foreign_key(table[f])]
            self._foreign_keys = foreign_keys

        return foreign_keys

    # -------------------------------------------------------------------------
    @property
    def references(self):
        """
             A list of foreign keys referencing this resource,
             lazy property

             @returns: a list of Fields
        """

        references = self._references

        if references is None:
            self.introspect()
            references = self._references

        return references

    # -------------------------------------------------------------------------
    @property
    def restrictions(self):
        """
            A list of foreign keys referencing this resource with
            ondelete="RESTRICT", lazy property

            @returns: a list of Fields
        """

        restrictions = self._restrictions

        if restrictions is None:
            self.introspect()
            restrictions = self._restrictions

        return restrictions

    # -------------------------------------------------------------------------
    def introspect(self):
        """
            Introspect the resource to set process properties
        """

        # Must load all models to detect dependencies
        current.s3db.load_all_models()

        db = current.db
        if db._lazy_tables:
            # Must roll out all lazy tables to detect dependencies
            for tn in list(db._LAZY_TABLES.keys()):
                db[tn]

        references = self.table._referenced_by
        try:
            restrictions = [f for f in references if f.ondelete == "RESTRICT"]
        except AttributeError:
            # Older web2py
            references = [db[tn][fn] for tn, fn in references]
            restrictions = [f for f in references if f.ondelete == "RESTRICT"]

        self._references = references
        self._restrictions = restrictions

    # -------------------------------------------------------------------------
    # Error Handling
    # -------------------------------------------------------------------------
    def add_error(self, record_id, msg):
        """
            Add an error

            @param record_id: the record ID
            @param msg: the error message
        """

        key = (self.tablename, record_id)

        error = self.errors.get(key)
        if type(error) is list:
            error.append(msg)
        elif error:
            self.errors[key] = [error, msg]
        else:
            self.errors[key] = msg

    # -------------------------------------------------------------------------
    def set_resource_error(self):
        """
            Set the resource.error
        """

        if not self.errors:
            return

        resource = self.resource
        if self.permission_error:
            resource.error = current.ERROR.NOT_PERMITTED
        else:
            resource.error = current.ERROR.INTEGRITY_ERROR

    # -------------------------------------------------------------------------
    def log_errors(self):
        """
            Log all errors of this process instance
        """

        if not self.errors:
            return

        # Log errors
        for key, errors in self.errors.items():
            self._log("Could not delete %s.%s" % key, None, errors)

    # -------------------------------------------------------------------------
    @classmethod
    def _log(cls, master, reference, errors):
        """
            Log all errors for a failed master record

            @param master: the master log message
            @param reference: the prefix for the sub-message
            @param errors: the errors
        """

        log = current.log.error

        if isinstance(errors, list):
            # Multiple errors for the same record
            for e in errors:
                cls._log(master, reference, e)

        elif isinstance(errors, dict):
            # Cascade error (tree of blocking references)
            if not reference:
                prefix = "undeletable reference:"
            else:
                prefix = "%s <=" % reference
            for k, e in errors.items():
                reference_ = "%s %s.%s" % (prefix, k[0], k[1])
                cls._log(master, reference_, e)

        else:
            # Single error
            if reference:
                msg = "%s (%s)" % (reference, errors)
            else:
                msg = errors
            log("%s: %s" % (master, msg))

# END =========================================================================
