# -*- coding: utf-8 -*-

""" Simple Generic Location Tracking System

    @author: Dominic König <dominic[at]aidiq.com>

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
from gluon.dal import Table, Query, Set, Expression, Rows, Row
from datetime import datetime, timedelta

__all__ = ["S3Tracker"]

# =============================================================================
class S3Trackable(object):
    """
        Trackable types instance(s)
    """

    UID = "uuid"                # field name for UIDs

    TRACK_ID = "track_id"       # field name for track ID
    LOCATION_ID = "location_id" # field name for base location

    LOCATION = "gis_location"   # location tablename
    PRESENCE = "sit_presence"   # presence tablename

    def __init__(self, db, trackable, record_id=None, uid=None, rtable=None):
        """
            Constructor:

            @param db: the database (DAL)
            @param trackable: the trackable object
            @param record_id: the record ID(s) (if object is a table or tablename)
            @param uid: the record UID(s) (if object is a table or tablename)
            @param rtable: the resource table (for the recursive calls)
        """

        current.db = db
        self.records = []

        self.table = db.sit_trackable
        self.rtable = rtable

        if isinstance(trackable, (Table, str)):
            if hasattr(trackable, "_tablename"):
                table = trackable
                tablename = table._tablename
            else:
                table = db[trackable]
                tablename = trackable
            fields = self.__get_fields(table)
            if not fields:
                raise SyntaxError("No trackable type: %s" % tablename)
            query = (table._id > 0)
            if uid is None:
                if record_id is not None:
                    if isinstance(record_id, (list, tuple)):
                        query = (table._id.belongs(record_id))
                    else:
                        query = (table._id == record_id)
            elif UID in table.fields:
                if not isinstance(uid, (list, tuple)):
                    query = (table[UID].belongs(uid))
                else:
                    query = (table[UID] == uid)
            fields = [table[f] for f in fields]
            rows = current.db(query).select(*fields)

        elif isinstance(trackable, Row):
            fields = self.__get_fields(trackable)
            if not fields:
                raise SyntaxError("Required fields not present in the row")
            rows = Rows(records=[trackable], compact=False)

        elif isinstance(trackable, Rows):
            rows = [r for r in trackable if self.__get_fields(r)]
            fail = len(trackable) - len(rows)
            if fail:
                raise SyntaxError("Required fields not present in %d of the rows" % fail)
            rows = Rows(records=rows, compact=False)

        elif isinstance(trackable, (Query, Expression)):
            tablename = current.db._adapter.get_table(trackable)
            self.rtable = current.db[tablename]
            fields = self.__get_fields(self.rtable)
            if not fields:
                raise SyntaxError("No trackable type: %s" % tablename)
            query = trackable
            fields = [self.rtable[f] for f in fields]
            rows = current.db(query).select(*fields)

        elif isinstance(trackable, Set):
            query = trackable.query
            tablename = current.db._adapter.get_table(query)
            table = current.db[tablename]
            fields = self.__get_fields(table)
            if not fields:
                raise SyntaxError("No trackable type: %s" % tablename)
            fields = [table[f] for f in fields]
            rows = trackable.select(*fields)

        else:
            raise SyntaxError("Invalid parameter type %s" % type(trackable))

        records = []
        for r in rows:
            if self.__super_entity(r):
                table = current.db[r.instance_type]
                fields = self.__get_fields(table, super_entity=False)
                if not fields:
                    raise SyntaxError("No trackable type: %s" % table._tablename)
                fields = [table[f] for f in fields]
                query = table[self.UID] == r[self.UID]
                row = current.db(query).select(limitby=(0, 1), *fields).first()
                if row:
                    records.append(row)
            else:
                records.append(r)

        self.records = Rows(records=records, compact=False)


    # -------------------------------------------------------------------------
    @classmethod
    def __super_entity(cls, trackable):
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
    @classmethod
    def __get_fields(cls, trackable, super_entity=True):
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
               cls.__super_entity(trackable) and cls.UID in keys:
                return ("instance_type", cls.UID)
            if cls.LOCATION_ID in keys:
                fields.append(cls.LOCATION_ID)
            if cls.TRACK_ID in keys:
                fields.append(cls.TRACK_ID)
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

        ptable = current.db[self.PRESENCE]
        ltable = current.db[self.LOCATION]

        if timestmp is None:
            timestmp = datetime.utcnow()

        locations = []
        for r in self.records:
            location = None
            if self.TRACK_ID in r:
                query = ((ptable.deleted == False) &
                         (ptable[self.TRACK_ID] == r[self.TRACK_ID]) &
                         (ptable.timestmp <= timestmp))
                presence = current.db(query).select(orderby=~ptable.timestmp,
                                                 limitby=(0, 1)).first()
                if presence:
                    if presence.interlock:
                        exclude = [r[self.TRACK_ID]] + exclude
                        tablename, record = presence.interlock.split(",", 1)
                        trackable = S3Trackable(current.db, tablename, record)
                        record = trackable.records.first()
                        if self.TRACK_ID not in record or \
                           record[self.TRACK_ID] not in exclude:
                            location = trackable.get_location(timestmp=timestmp,
                                                              exclude=exclude)
                    elif presence.location_id:
                        query = (ltable.id == presence.location_id)
                        if _filter is not None:
                            query = query & _filter
                        if _fields is None:
                            location = current.db(query).select(ltable.ALL,
                                                             limitby=(0, 1)).first()
                        else:
                            location = current.db(query).select(limitby=(0, 1),
                                                             *_fields).first()

            if not location:
                if len(self.records) > 1:
                    trackable = S3Trackable(current.db, r, rtable=self.rtable)
                else:
                    trackable = self
                location = trackable.get_base_location(_fields=_fields)

            if location:
                locations.append(location)

        if as_rows:
            return Rows(records=locations, compact=False)

        if not locations:
            return None
        elif len(locations) == 1:
            return locations[0]
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

        ptable = current.db[self.PRESENCE]

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
            if self.TRACK_ID not in r:
                # No track ID => set base location
                if len(self.records) > 1:
                    trackable = S3Trackable(r)
                else:
                    trackable = self
                trackable.set_base_location(location)
            elif r[self.TRACK_ID]:
                data.update({self.TRACK_ID:r[self.TRACK_ID]})
                ptable.insert(**data)
                self.__update_timestamp(r[self.TRACK_ID], timestmp)


    # -------------------------------------------------------------------------
    def check_in(self, table, record, timestmp=None):
        """
            Bind the presence of the instance(s) to another instance

            @param table: table name of the other resource
            @param record: record in the other resource (as Row or record ID)
            @param timestmp: datetime of the check-in

            @returns: nothing
        """

        ptable = current.db[self.PRESENCE]

        if isinstance(table, str):
            table = current.db[table]
        fields = self.__get_fields(table)
        if not fields:
            raise SyntaxError("No location data in %s" % table._tablename)

        interlock = None
        if isinstance(record, Rows):
            record = record.first()
        if not isinstance(record, Row):
            record = table[record]
        if self.__super_entity(record):
            table = current.db[record.instance_type]
            fields = self.__get_fields(table, super_entity=False)
            if not fields:
                raise SyntaxError("No trackable type: %s" % table._tablename)
            query = table[self.UID] == record[self.UID]
            record = current.db(query).select(limitby=(0, 1)).first()
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
                if self.TRACK_ID not in r:
                    # Cannot check-in a non-trackable
                    continue
                query = q & (ptable[self.TRACK_ID] == r[self.TRACK_ID])
                presence = current.db(query).select(orderby=~ptable.timestmp,
                                                 limitby=(0, 1)).first()
                if presence and presence.interlock == interlock:
                    # already checked-in to the same instance
                    continue
                data.update({self.TRACK_ID:r[self.TRACK_ID]})
                ptable.insert(**data)
                self.__update_timestamp(r[self.TRACK_ID], timestmp)


    # -------------------------------------------------------------------------
    def check_out(self, table=None, record=None, timestmp=None):
        """
            Make the last log entry before timestmp independent from
            the referenced entity (if any)

            @param timestmp: the date/time of the check-out, defaults
                             to current time

        """

        ptable = current.db[self.PRESENCE]

        if timestmp is None:
            timestmp = datetime.utcnow()

        interlock = None
        if table is not None:
            if isinstance(table, str):
                table = current.db[table]
            if isinstance(record, Rows):
                record = record.first()
            if self.__super_entity(table):
                if not isinstance(record, Row):
                    record = table[record]
                table = current.db[record.instance_type]
                fields = self.__get_fields(table, super_entity=False)
                if not fields:
                    raise SyntaxError("No trackable type: %s" % table._tablename)
                query = table[self.UID] == record[self.UID]
                record = current.db(query).select(limitby=(0, 1)).first()
            if isinstance(record, Row) and table._id.name in record:
                record = record[table._id.name]
            if record:
                interlock = "%s,%s" % (table, record)
            else:
                return

        q = ((ptable.deleted == False) & (ptable.timestmp <= timestmp))

        for r in self.records:
            if self.TRACK_ID not in r:
                # Cannot check-out a non-trackable
                continue
            query = q & (ptable[self.TRACK_ID] == r[self.TRACK_ID])
            presence = current.db(query).select(orderby=~ptable.timestmp,
                                             limitby=(0, 1)).first()
            if presence and presence.interlock:
                if interlock and presence.interlock != interlock:
                    continue
                elif not interlock and table and \
                     not presence.interlock.startswith("%s" % table):
                    continue
                tablename, record = presence.interlock.split(",", 1)
                trackable = S3Trackable(current.db, tablename, record)
                location = trackable.get_location(timestmp=timestmp)
                if timestmp - presence.timestmp < timedelta(seconds=1):
                    timestmp = timestmp + timedelta(seconds=1)
                data = dict(location_id=location,
                            timestmp=timestmp,
                            interlock=None)
                data.update({self.TRACK_ID:r[self.TRACK_ID]})
                ptable.insert(**data)
                self.__update_timestamp(r[self.TRACK_ID], timestmp)


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
        ltable = db[self.LOCATION]
        rtable = self.rtable

        locations = []
        for r in self.records:
            location = None
            query = None
            if self.LOCATION_ID in r:
                query = (ltable.id == r[self.LOCATION_ID])
                if rtable:
                    query = query & (rtable[self.LOCATION_ID] == ltable.id)
                    if self.TRACK_ID in r:
                        query = query & (rtable[self.TRACK_ID] == r[self.TRACK_ID])
            elif self.TRACK_ID in r:
                q = (self.table[self.TRACK_ID] == r[self.TRACK_ID])
                trackable = db(q).select(limitby=(0, 1)).first()
                table = db[trackable.instance_type]
                if self.LOCATION_ID in table.fields:
                    query = ((table[self.TRACK_ID] == r[self.TRACK_ID]) &
                             (table[self.LOCATION_ID] == ltable.id))
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
            location = location.id

        if not location or not str(location).isdigit():
            # Location not found
            return
        else:
            data = {self.LOCATION_ID:location}

        # Update records without track ID
        for r in self.records:
            if self.TRACK_ID in r:
                continue
            elif self.LOCATION_ID in r:
                if hasattr(r, "update_record"):
                    r.update_record(**data)
                else:
                    raise SyntaxError("Cannot relate record to a table.")

        # Update records with track ID
        # => this can happen table-wise = less queries
        track_ids = [r[self.TRACK_ID] for r in self.records
                                      if self.TRACK_ID in r]
        rows = current.db(self.table[self.TRACK_ID].belongs(track_ids)).select()
        tables = []
        for r in rows:
            instance_type = r.instance_type
            table = current.db[instance_type]
            if instance_type not in tables and \
               self.LOCATION_ID in table.fields:
                   tables.append(table)
            else:
                # No location ID in this type => ignore gracefully
                continue

        # Location specified => update all base locations
        for table in tables:
            current.db(table[self.TRACK_ID].belongs(track_ids)).update(**data)

        # Refresh records
        for r in self.records:
            if self.LOCATION_ID in r:
                r[self.LOCATION_ID] = location


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
    S3 Tracking system, to be instantiated once as global "s3_trackable" object

    """

    def __init__(self):
        """
        Constructor

        """

    # -------------------------------------------------------------------------
    def __call__(self, trackable, record_id=None, uid=None):
        """
        Get a tracking interface for a record or set of records

        @param trackable: a Row, Rows, Query, Expression, Set object or
                          a Table or a tablename
        @param record_id: a record ID or a list/tuple of record IDs (together
                          with Table or tablename)
        @param uid: a record UID or a list/tuple of record UIDs (together with
                    Table or tablename)

        @returns: a S3Trackable instance for the specified record(s)

        """

        return S3Trackable(current.db, trackable,
                           record_id=record_id,
                           uid=uid)


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


# =============================================================================

