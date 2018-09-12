#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Script to restore an archived (="soft-deleted") record with all its
# dependencies
#
# Run as:
#   python web2py.py -S eden -M -R applications/eden/static/scripts/tools/restore.py -A <tablename> <recordID>
#
# CAUTION: Use with utter care!
#
# Restoring a record almost always re-instates related records, some of which
# may have become obsolete or downright invalid by that time, and must therefore
# be cleaned up afterwards.
#
# Due to later changes in the database, restored records may end up to be in
# a now-invalid state, and thus not be accessible as intended - especially in
# combination with complex hierarchies (organisations, realms etc.). Manual
# verification may be required.
#
# Restoring records can affect the realm hierarchy and therefore expose (or
# block access to) data in unintended ways. In doubt, block all untrusted user
# accounts until access permissions have been verified.
#
# Always consider the reasons that motivated the deletion in the first place!
# If there was a problem with the data, restoring them will also restore that
# problem.
#
try:
    template = settings.get_template()
except NameError:
    raise RuntimeError("Script needs to be run in the web2py environment")

import datetime
import sys
import json

from gluon import current
from s3 import s3_get_foreign_key

# =============================================================================
class S3Deleted(object):
    """
        Utility class to restore deleted records (DRAFT for command line use)
    """

    def __init__(self, tablename, record_id, level=-1, master=None):
        """
            Constructor

            @param tablename: the table name
            @param record_id: the record ID
            @param level: the current recursion level
        """

        self.tablename = tablename
        self.record_id = record_id

        self.level = level + 1
        self.master = master

        # A list of column names ("table.field") that shall be excluded
        # from implicitly re-instating referenced records
        # TODO parametrize
        self.exclude_references = []

        if level == -1:
            current.s3db.load_all_models()
            db = current.db
            if db._lazy_tables:
                for tn in db._LAZY_TABLES.keys():
                    db[tn]

    # -------------------------------------------------------------------------
    def startm(self, msg):
        """
            Helper function to start a new info message line

            @param msg: the message
        """

        sys.stderr.write("\n%s%s" % ("  " * self.level, msg))

    # -------------------------------------------------------------------------
    def info(self, msg):
        """
            Helper function to continue an info message line

            @param msg: the message
        """

        sys.stderr.write("%s" % msg)

    # -------------------------------------------------------------------------
    def restore(self, instance=None, master=None):
        """
            Restore a record

            @returns: the record ID
        """

        s3db = current.s3db

        tablename = self.tablename
        record_id = self.record_id

        self.startm("Restore %s #%s..." % (tablename, record_id))

        # Check whether the record can be restored
        table = s3db[tablename]
        if "deleted" not in table.fields:
            self.info("table does not archive records")
            return None

        # Get the deleted record
        record = current.db(table._id == record_id).select(table.ALL,
                                                           limitby = (0, 1),
                                                           ).first()
        if not record:
            self.info("record not found")
            return None
        else:
            record_id = record[table._id.name]

        # Check if it was deleted
        if not record.deleted:
            self.info("was not deleted.")
            return record_id

        # Check if it was replaced
        if "deleted_rb" in table and record.deleted_rb:
            self.info("was replaced by #%s." % record.deleted_rb)
            return self.cascade(tablename, record.deleted_rb)

        # If it is a super-entity, restore the instance first (unless passed-in)
        is_super = table._id.name != "id" and "instance_type" in table.fields
        if is_super and instance is None:
            self.restore_instance(table, record)

        # Get the time stamp of the deletion
        if instance and "modified_on" in instance:
            timestamp = instance.modified_on
        elif "modified_on" in table.fields:
            timestamp = record.modified_on
        else:
            timestamp = None

        data = {"deleted": False,
                }

        # Get deleted references
        references = {}
        if "deleted_fk" in table.fields:
            deleted_fk = record.deleted_fk
            if deleted_fk:
                try:
                    references = json.loads(deleted_fk)
                except:
                    pass
            data["deleted_fk"] = None

        # Restore deleted references
        for fieldname, value in references.items():
            if record[fieldname] is not None:
                continue
            fk = self.restore_reference(table[fieldname], value, timestamp)
            if fk:
                data[fieldname] = fk

        # Undelete the record itself, reset deleted_fk and update foreign keys
        record.update_record(**data)

        # Restore super-records
        if not is_super:
            self.restore_super(record)

        # Restoring a record is the same as updating it, so run onaccept
        s3db.onaccept(table, record, method="update")

        # Restore related records
        self.restore_linked(table, record, timestamp)

        # Done
        self.startm("%s #%s restored" % (tablename, record_id))
        return record_id

    # -------------------------------------------------------------------------
    def cascade(self, tablename, record_id, instance=None):
        """
            Cascade restore a related/dependent record

            @param tablename: the table name
            @param record_id: the ID of the related/dependent record
            @param instance: the instance record if the related record is a SE

            @returns: the record ID of the related record
        """

        deleted = self.__class__(tablename, record_id,
                                 level = self.level,
                                 master = self,
                                 )

        return deleted.restore(instance=instance)

    # -------------------------------------------------------------------------
    def is_master(self, tablename, record_id=None):
        """
            Check if any of the callers already restores a certain record
        """

        if self.tablename == tablename and \
           (record_id is None or self.record_id == record_id):
            return True
        elif self.master:
            return self.master.is_master(tablename, record_id=record_id)
        else:
            return False

    # -------------------------------------------------------------------------
    def is_master_table(self, tablename):
        """
            Check if a table is among the masters
        """


    # -------------------------------------------------------------------------
    def restore_reference(self, field, value, timestamp):
        """
            Restore references

            @param field: the foreign key Field
            @param value: the original value of the field (from deleted_fk)
            @param timestamp: the deletion time stamp of the record
        """

        db = current.db
        s3db = current.s3db

        if value is None:
            return None

        # Get the referenced table and key
        rtablename = s3_get_foreign_key(field, m2m=False)[0]
        if not rtablename:
            # Not a reference, so simply restore the value
            return value

        # Check whether the referenced record still exists
        rtable = s3db[rtablename]

        fields = [rtable._id]
        if "deleted" in rtable.fields:
            fields.append(rtable.deleted)
        if "modified_on" in rtable.fields:
            check_timestamp = True
            fields.append(rtable.modified_on)
        else:
            check_timestamp = False

        row = db(rtable._id == value).select(limitby=(0, 1), *fields).first()

        # Must restore the record
        self.startm("Restore reference %s=%s..." % (field, value))

        if not row:
            # Referenced record does no longer exist (hard-deleted)
            self.info("deleted")
            return None

        if not row.deleted:
            # Referenced record exists and is not archived
            self.info("ok")
            return row[rtable._id]

        if check_timestamp and timestamp:
            modified_on = row.modified_on
            if modified_on and modified_on > timestamp + datetime.timedelta(minutes=1):
                # Referenced record was deleted after the master record
                ondelete = field.ondelete
                if ondelete == "SET NULL":
                    self.info("setting %s=None" % field)
                    return None

                elif ondelete == "SET DEFAULT":
                    self.info("setting %s=%s (default)" % (field, field.default))
                    return field.default

        if str(field) not in self.exclude_references:
            # Restore the referenced record
            self.info("restore referenced record")
            restored = self.cascade(rtablename, value)
            if restored:
                self.startm("=> setting %s=%s" % (field, restored))
                return restored
            else:
                self.startm("=> failed to restore %s" % field)
                return None
        else:
            # We shall not restore this if deleted
            self.info("must not restore referenced record")
            return None

    # -------------------------------------------------------------------------
    def restore_super(self, instance):
        """
            Restore all super-entities of an instance record

            @param instance: the instance record
        """

        db = current.db
        s3db = current.s3db

        supertables = s3db.get_config(self.tablename, "super_entity")
        if not supertables:
            return

        self.startm("Restore super-entities...")

        data = {}
        uid = instance.uuid
        if not isinstance(supertables, (tuple, list)):
            supertables = [supertables]
        for stablename in supertables:

            # Find the super-entity record by its uuid
            stable = s3db[stablename]
            srecord = db(stable.uuid == uid).select(stable._id,
                                                    limitby = (0, 1),
                                                    ).first()

            # Restore the super-entity record
            if srecord:
                super_key = self.cascade(stablename,
                                         srecord[stable._id],
                                         instance=instance,
                                         )
                if super_key:
                    data[stable._id.name] = super_key

        # Update the super-keys
        if data:
            instance.update_record(**data)

        # Run update_super to restore all shared fields and
        # establish new super-entities where they could not be restored
        s3db.update_super(s3db[self.tablename], instance)

    # -------------------------------------------------------------------------
    def restore_instance(self, supertable, record):
        """
            Restore the instance record of a super-entity

            @param supertable - the super-entity table
            @param record - the super-entity record

            @returns - the super-entity record ID
        """

        # Get the instance table
        tablename = record.instance_type
        table = current.s3db[tablename]

        # Get the instance record by its uuid
        instance = current.db(table.uuid == record.uuid).select(table._id,
                                                                limitby = (0, 1),
                                                                ).first()

        # Restore the instance record
        if instance:
            instance_id = instance[table._id]
            if self.cascade(tablename, instance_id):
                return record[supertable._id]

        # Instance record could not be restored
        return None

    # -------------------------------------------------------------------------
    def restore_linked(self, table, record, timestamp):
        """
            Restore records linked to a master record

            @param table: the table
            @param record: the master record
            @param timestamp: the timestamp when the record was deleted
        """

        db = current.db
        s3db = current.s3db

        references = table._referenced_by
        try:
            fks = [f for f in references]
        except AttributeError:
            # older web2py
            fks = [f for f in [db[tn][fn] for tn, fn in references]]

        record_id = record[table._id]

        restore = []
        for fk in fks:

            fn, tn = fk.name, fk.tablename
            if self.is_master(tn) and not s3db.get(tn, "hierarchy"):
                # Do not restore related records in the same table
                continue

            rtable = db[tn]
            if not all(f in rtable.fields for f in ("deleted", "deleted_fk")):
                # Records in this table are not archived, so
                # they cannot be restored either
                continue

            fields = [rtable._id, rtable.deleted_fk]
            if "modified_on" in rtable.fields:
                check_timestamp = True
                fields.append(rtable.modified_on)
            else:
                check_timestamp = False

            rows = db(rtable.deleted == True).select(*fields)
            for row in rows:
                # Check if this record is related
                if row.deleted_fk:
                    deleted_fk = json.loads(row.deleted_fk)
                else:
                    continue
                if str(deleted_fk.get(fn)) != str(record_id):
                    continue

                # Check if this record was deleted as part of the cascade
                if check_timestamp and timestamp and \
                   timestamp > row.modified_on + datetime.timedelta(minutes=1):
                    # Was deleted before master, not as part of the cascade
                    continue

                # Mark for re-instating
                related_id = row[rtable._id]
                if not self.is_master(tn, related_id):
                    restore.append((tn, related_id))

        if restore:
            self.startm("Restore related records...")
        else:
            return

        for tn, record_id in restore:
            self.cascade(tn, record_id)

# =============================================================================
# Main script
#
def main(argv):

    tablename = argv[0]
    record_id = argv[1]

    auth = current.auth

    auth.override = True

    deleted = S3Deleted(tablename, record_id)
    deleted.restore()

    current.db.commit()
    auth.override = False

    sys.stderr.write("\n")

if __name__ == "__main__":

    sys.exit(main(sys.argv[1:]))

# END =========================================================================
