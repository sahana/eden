# -*- coding: utf-8 -*-

""" Simple Generic Location Tracking System

    @copyright: 2011-12 (c) Sahana Software Foundation
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
from gluon.dal import Table, Rows, Row
from datetime import datetime, timedelta

__all__ = ["S3Tracker"]

UID = "uuid"                # field name for UIDs

TRACK_ID = "track_id"       # field name for track ID
LOCATION_ID = "location_id" # field name for base location

LOCATION = "gis_location"   # location tablename
PRESENCE = "sit_presence"   # presence tablename

# =============================================================================
class S3Trackable(object):
    """
        Trackable types instance(s)
    """

    def __init__(self, table=None, tablename=None, record=None, query=None,
                 record_id=None, record_ids=None, rtable=None):
        """
            Constructor:

            @param table: a Table object
            @param tablename: a Str tablename
            @param record: a Row object
            @param query: a Query object
            @param record_id: a record ID (if object is a Table)
            @param record_ids: a list of record IDs (if object is a Table)
                               - these should be in ascending order
            @param rtable: the resource table (for the recursive calls)
        """

        db = current.db
        s3db = current.s3db

        self.records = []

        self.table = s3db.sit_trackable
        self.rtable = rtable

        # if isinstance(trackable, (Table, str)):
            # if hasattr(trackable, "_tablename"):
                # table = trackable
                # tablename = table._tablename
            # else:
                # table = s3db[trackable]
                # tablename = trackable
            # fields = self.__get_fields(table)
            # if not fields:
                # raise SyntaxError("Not a trackable type: %s" % tablename)
            # query = (table._id > 0)
            # if uid is None:
                # if record_id is not None:
                    # if isinstance(record_id, (list, tuple)):
                        # query = (table._id.belongs(record_id))
                    # else:
                        # query = (table._id == record_id)
            # elif UID in table.fields:
                # if not isinstance(uid, (list, tuple)):
                    # query = (table[UID].belongs(uid))
                # else:
                    # query = (table[UID] == uid)
            # fields = [table[f] for f in fields]
            # rows = db(query).select(*fields)
        if table or tablename:
            if table:
                tablename = table._tablename
            else:
                table = s3db[tablename]
            fields = self.__get_fields(table)
            if not fields:
                raise SyntaxError("Not a trackable type: %s" % tablename)
            if record_ids:
                query = (table._id.belongs(record_ids))
                limitby = (0, len(record_ids))
                orderby = table._id
            elif record_id:
                query = (table._id == record_id)
                limitby = (0, 1)
                orderby = None
            else:
                query = (table._id > 0)
                limitby = None
                orderby = table._id
            fields = [table[f] for f in fields]
            rows = db(query).select(limitby=limitby, orderby=orderby, *fields)

        # elif isinstance(trackable, Row):
            # fields = self.__get_fields(trackable)
            # if not fields:
                # raise SyntaxError("Required fields not present in the row")
            # rows = Rows(records=[trackable], compact=False)
        elif record:
            fields = self.__get_fields(record)
            if not fields:
                raise SyntaxError("Required fields not present in the row")
            rows = Rows(records=[record], compact=False)

        # elif isinstance(trackable, Rows):
            # rows = [r for r in trackable if self.__get_fields(r)]
            # fail = len(trackable) - len(rows)
            # if fail:
                # raise SyntaxError("Required fields not present in %d of the rows" % fail)
            # rows = Rows(records=rows, compact=False)

        # elif isinstance(trackable, (Query, Expression)):
            # tablename = db._adapter.get_table(trackable)
            # self.rtable = s3db[tablename]
            # fields = self.__get_fields(self.rtable)
            # if not fields:
                # raise SyntaxError("Not a trackable type: %s" % tablename)
            # query = trackable
            # fields = [self.rtable[f] for f in fields]
            # rows = db(query).select(*fields)
        elif query:
            tablename = db._adapter.get_table(query)
            self.rtable = s3db[tablename]
            fields = self.__get_fields(self.rtable)
            if not fields:
                raise SyntaxError("Not a trackable type: %s" % tablename)
            fields = [self.rtable[f] for f in fields]
            rows = db(query).select(*fields)

        # elif isinstance(trackable, Set):
            # query = trackable.query
            # tablename = db._adapter.get_table(query)
            # table = s3db[tablename]
            # fields = self.__get_fields(table)
            # if not fields:
                # raise SyntaxError("Not a trackable type: %s" % tablename)
            # fields = [table[f] for f in fields]
            # rows = trackable.select(*fields)

        else:
            raise SyntaxError("Invalid parameters")

        records = []
        for r in rows:
            if self.__super_entity(r):
                table = s3db[r.instance_type]
                fields = self.__get_fields(table, super_entity=False)
                if not fields:
                    raise SyntaxError("No trackable type: %s" % table._tablename)
                fields = [table[f] for f in fields]
                query = table[UID] == r[UID]
                row = db(query).select(limitby=(0, 1), *fields).first()
                if row:
                    records.append(row)
            else:
                records.append(r)

        self.records = Rows(records=records, compact=False)

    # -------------------------------------------------------------------------
    @staticmethod
    def __super_entity(trackable):
        """
            Check whether a trackable is a super-entity

            @param trackable: the trackable object
        """

        if hasattr(trackable, "fields"):
            keys = trackable.fields
        else:
            keys = trackable

        return "instance_type" in keys

    # -------------------------------------------------------------------------
    def __get_fields(self, trackable, super_entity=True):
        """
            Check a trackable for presence of required fields

            @param: the trackable object
        """

        fields = []

        if hasattr(trackable, "fields"):
            keys = trackable.fields
        else:
            keys = trackable

        try:
            if super_entity and \
               self.__super_entity(trackable) and UID in keys:
                return ("instance_type", UID)
            if LOCATION_ID in keys:
                fields.append(LOCATION_ID)
            if TRACK_ID in keys:
                fields.append(TRACK_ID)
                return fields
            elif hasattr(trackable, "update_record") or \
                 isinstance(trackable, Table) or \
                 isinstance(trackable, Row):
                return fields
        except:
            pass
        return None

    # -------------------------------------------------------------------------
    def get_location(self,
                     timestmp=None,
                     _fields=None,
                     _filter=None,
                     as_rows=False,
                     exclude=[]):
        """
            Get the current location of the instance(s) (at the given time)

            @param timestmp: last datetime for presence (defaults to current time)
            @param _fields: fields to retrieve from the location records (None for ALL)
            @param _filter: filter for the locations
            @param as_rows: return the result as Rows object
            @param exclude: interlocks to break at (avoids circular check-ins)

            @returns: a location record, or a list of location records (if multiple)
        """

        db = current.db
        s3db = current.s3db

        ptable = s3db[PRESENCE]
        ltable = s3db[LOCATION]

        if timestmp is None:
            timestmp = datetime.utcnow()

        locations = []
        for r in self.records:
            location = None
            if TRACK_ID in r:
                query = ((ptable.deleted == False) & \
                         (ptable[TRACK_ID] == r[TRACK_ID]) & \
                         (ptable.timestmp <= timestmp))
                presence = db(query).select(orderby=~ptable.timestmp,
                                            limitby=(0, 1)).first()
                if presence:
                    if presence.interlock:
                        exclude = [r[TRACK_ID]] + exclude
                        tablename, record_id = presence.interlock.split(",", 1)
                        trackable = S3Trackable(tablename=tablename, record_id=record_id)
                        record = trackable.records.first()
                        if TRACK_ID not in record or \
                           record[TRACK_ID] not in exclude:
                            location = trackable.get_location(timestmp=timestmp,
                                                              exclude=exclude,
                                                              _fields=_fields).first()
                    elif presence.location_id:
                        query = (ltable.id == presence.location_id)
                        if _filter is not None:
                            query = query & _filter
                        if _fields is None:
                            location = db(query).select(ltable.ALL,
                                                        limitby=(0, 1)).first()
                        else:
                            location = db(query).select(limitby=(0, 1),
                                                        *_fields).first()

            if not location:
                if len(self.records) > 1:
                    trackable = S3Trackable(record=r, rtable=self.rtable)
                else:
                    trackable = self
                location = trackable.get_base_location(_fields=_fields)

            if location:
                locations.append(location)
            else:
                # Ensure we return an entry so that indexes match
                locations.append(Row({"lat": None, "lon": None}))

        if as_rows:
            return Rows(records=locations, compact=False)

        if not locations:
            return None
        else:
            return locations

    # -------------------------------------------------------------------------
    def set_location(self, location, timestmp=None):
        """
            Set the current location of instance(s) (at the given time)

            @param location: the location (as Row or record ID)
            @param timestmp: the datetime of the presence (defaults to current time)

            @returns: nothing
        """

        ptable = current.s3db[PRESENCE]

        if timestmp is None:
            timestmp = datetime.utcnow()

        if isinstance(location, S3Trackable):
            location = location.get_base_location()
        if isinstance(location, Rows):
            location = location.first()
        if isinstance(location, Row):
            if "location_id" in location:
                location = location.location_id
            else:
                location = location.id

        if not location:
            return
        else:
            data = dict(location_id=location, timestmp=timestmp)

        for r in self.records:
            if TRACK_ID not in r:
                # No track ID => set base location
                if len(self.records) > 1:
                    trackable = S3Trackable(record=r)
                else:
                    trackable = self
                trackable.set_base_location(location)
            elif r[TRACK_ID]:
                data.update({TRACK_ID:r[TRACK_ID]})
                ptable.insert(**data)
                self.__update_timestamp(r[TRACK_ID], timestmp)

    # -------------------------------------------------------------------------
    def check_in(self, table, record, timestmp=None):
        """
            Bind the presence of the instance(s) to another instance

            @param table: table name of the other resource
            @param record: record in the other resource (as Row or record ID)
            @param timestmp: datetime of the check-in

            @returns: nothing
        """

        db = current.db
        s3db = current.s3db

        ptable = s3db[PRESENCE]

        if isinstance(table, str):
            table = s3db[table]
        fields = self.__get_fields(table)
        if not fields:
            raise SyntaxError("No location data in %s" % table._tablename)

        interlock = None
        if isinstance(record, Rows):
            record = record.first()
        if not isinstance(record, Row):
            record = table[record]
        if self.__super_entity(record):
            table = s3db[record.instance_type]
            fields = self.__get_fields(table, super_entity=False)
            if not fields:
                raise SyntaxError("No trackable type: %s" % table._tablename)
            query = table[UID] == record[UID]
            record = db(query).select(limitby=(0, 1)).first()
        if record and table._id.name in record:
            record = record[table._id.name]
            if record:
                interlock = "%s,%s" % (table, record)
        else:
            raise SyntaxError("No record specified for %s" % table._tablename)

        if interlock:
            if timestmp is None:
                timestmp = datetime.utcnow()
            data = dict(location_id=None,
                        timestmp=timestmp,
                        interlock=interlock)
            q = ((ptable.deleted == False) & (ptable.timestmp <= timestmp))
            for r in self.records:
                if TRACK_ID not in r:
                    # Cannot check-in a non-trackable
                    continue
                query = q & (ptable[TRACK_ID] == r[TRACK_ID])
                presence = db(query).select(orderby=~ptable.timestmp,
                                            limitby=(0, 1)).first()
                if presence and presence.interlock == interlock:
                    # already checked-in to the same instance
                    continue
                data.update({TRACK_ID:r[TRACK_ID]})
                ptable.insert(**data)
                self.__update_timestamp(r[TRACK_ID], timestmp)

    # -------------------------------------------------------------------------
    def check_out(self, table=None, record=None, timestmp=None):
        """
            Make the last log entry before timestmp independent from
            the referenced entity (if any)

            @param timestmp: the date/time of the check-out, defaults
                             to current time
        """

        db = current.db
        s3db = current.s3db

        ptable = s3db[PRESENCE]

        if timestmp is None:
            timestmp = datetime.utcnow()

        interlock = None
        if table is not None:
            if isinstance(table, str):
                table = s3db[table]
            if isinstance(record, Rows):
                record = record.first()
            if self.__super_entity(table):
                if not isinstance(record, Row):
                    record = table[record]
                table = s3db[record.instance_type]
                fields = self.__get_fields(table, super_entity=False)
                if not fields:
                    raise SyntaxError("No trackable type: %s" % table._tablename)
                query = table[UID] == record[UID]
                record = db(query).select(limitby=(0, 1)).first()
            if isinstance(record, Row) and table._id.name in record:
                record = record[table._id.name]
            if record:
                interlock = "%s,%s" % (table, record)
            else:
                return

        q = ((ptable.deleted == False) & (ptable.timestmp <= timestmp))

        for r in self.records:
            if TRACK_ID not in r:
                # Cannot check-out a non-trackable
                continue
            query = q & (ptable[TRACK_ID] == r[TRACK_ID])
            presence = db(query).select(orderby=~ptable.timestmp,
                                        limitby=(0, 1)).first()
            if presence and presence.interlock:
                if interlock and presence.interlock != interlock:
                    continue
                elif not interlock and table and \
                     not presence.interlock.startswith("%s" % table):
                    continue
                tablename, record_id = presence.interlock.split(",", 1)
                trackable = S3Trackable(tablename=tablename, record_id=record_id)
                location = trackable.get_location(timestmp=timestmp).first()
                if timestmp - presence.timestmp < timedelta(seconds=1):
                    timestmp = timestmp + timedelta(seconds=1)
                data = dict(location_id=location,
                            timestmp=timestmp,
                            interlock=None)
                data.update({TRACK_ID:r[TRACK_ID]})
                ptable.insert(**data)
                self.__update_timestamp(r[TRACK_ID], timestmp)

    # -------------------------------------------------------------------------
    def remove_location(self, location=None):
        """
            Remove a location from the presence log of the instance(s)

            @todo: implement
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def get_base_location(self,
                          _fields=None,
                          _filter=None,
                          as_rows=False):
        """
            Get the base location of the instance(s)

            @param _fields: fields to retrieve from the location records (None for ALL)
            @param _filter: filter for the locations
            @param as_rows: return the result as Rows object

            @returns: the base location(s) of the current instance
        """

        db = current.db
        s3db = current.s3db

        ltable = s3db[LOCATION]
        rtable = self.rtable

        locations = []
        for r in self.records:
            location = None
            query = None
            if LOCATION_ID in r:
                query = (ltable.id == r[LOCATION_ID])
                if rtable:
                    query = query & (rtable[LOCATION_ID] == ltable.id)
                    if TRACK_ID in r:
                        query = query & (rtable[TRACK_ID] == r[TRACK_ID])
            elif TRACK_ID in r:
                q = (self.table[TRACK_ID] == r[TRACK_ID])
                trackable = db(q).select(limitby=(0, 1)).first()
                table = s3db[trackable.instance_type]
                if LOCATION_ID in table.fields:
                    query = ((table[TRACK_ID] == r[TRACK_ID]) &
                             (table[LOCATION_ID] == ltable.id))
            if query:
                if _filter is not None:
                    query = query & _filter
                if not _fields:
                    location = db(query).select(ltable.ALL,
                                                limitby=(0, 1)).first()
                else:
                    location = db(query).select(limitby=(0, 1),
                                                *_fields).first()
            if location:
                locations.append(location)
            else:
                # Ensure we return an entry so that indexes match
                locations.append(Row({"lat": None, "lon": None}))

        if as_rows:
            return Rows(records=locations, compact=False)

        if not locations:
            return None
        elif len(locations) == 1:
            return locations[0]
        else:
            return locations

    # -------------------------------------------------------------------------
    def set_base_location(self, location=None):
        """
            Set the base location of the instance(s)

            @param location: the location for the base location as Row or record ID

            @returns: nothing

            @note: instance tables without a location_id field will be ignored
        """

        if isinstance(location, S3Trackable):
            location = location.get_base_location()
        if isinstance(location, Rows):
            location = location.first()
        if isinstance(location, Row):
            location.get("id", None)

        if not location or not str(location).isdigit():
            # Location not found
            return
        else:
            data = {LOCATION_ID:location}

        # Update records without track ID
        for r in self.records:
            if TRACK_ID in r:
                continue
            elif LOCATION_ID in r:
                if hasattr(r, "update_record"):
                    r.update_record(**data)
                else:
                    raise SyntaxError("Cannot relate record to a table.")

        db = current.db
        s3db = current.s3db

        # Update records with track ID
        # => this can happen table-wise = less queries
        track_ids = [r[TRACK_ID] for r in self.records
                                      if TRACK_ID in r]
        rows = db(self.table[TRACK_ID].belongs(track_ids)).select()
        tables = []
        for r in rows:
            instance_type = r.instance_type
            table = s3db[instance_type]
            if instance_type not in tables and \
               LOCATION_ID in table.fields:
                   tables.append(table)
            else:
                # No location ID in this type => ignore gracefully
                continue

        # Location specified => update all base locations
        for table in tables:
            db(table[TRACK_ID].belongs(track_ids)).update(**data)

        # Refresh records
        for r in self.records:
            if LOCATION_ID in r:
                r[LOCATION_ID] = location

    # -------------------------------------------------------------------------
    def __update_timestamp(self, track_id, timestamp):
        """
            Update the timestamp of a trackable

            @param track_id: the trackable ID (super-entity key)
            @param timestamp: the timestamp
        """

        if timestamp is None:
            timestamp = datetime.utcnow()
        if track_id:
            trackable = self.table[track_id]
        if trackable:
            trackable.update_record(track_timestmp=timestamp)

# =============================================================================
class S3Tracker(object):
    """
        S3 Tracking system, can be instantiated once as global "s3tracker" object
    """

    def __init__(self):
        """
            Constructor
        """

    # -------------------------------------------------------------------------
    def __call__(self, table=None, record_id=None, record_ids=None,
                 tablename=None, record=None, query=None):
        """
            Get a tracking interface for a record or set of records

            @param table: a Table object
            @param record_id: a record ID (together with Table or tablename)
            @param record_ids: a list/tuple of record IDs (together with Table or tablename)
            @param tablename: a Str object
            @param record: a Row object
            @param query: a Query object

            @returns: a S3Trackable instance for the specified record(s)
        """

        return S3Trackable(table=table,
                           tablename=tablename,
                           record_id=record_id,
                           record_ids=record_ids,
                           record=record,
                           query=query,
                           )

    # -------------------------------------------------------------------------
    def get_all(self, entity,
                location=None,
                bbox=None,
                timestmp=None):
        """
            Get all instances of the given entity at the given location and time
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def get_checked_in(self, table, record,
                       instance_type=None,
                       timestmp=None):
        """
            Get all trackables of the given type that are checked-in
            to the given instance at the given time
        """
        raise NotImplementedError

# END =========================================================================
