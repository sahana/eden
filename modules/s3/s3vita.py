# -*- coding: utf-8 -*-

""" Person Finder Toolkit (VITA)

    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2010-2011 (c) Sahana Software Foundation
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

    @status: to be deprecated

"""

__all__ = ["S3Vita"]

from gluon import current
from gluon.storage import Storage

# =============================================================================

class S3Vita(object):

    """ Toolkit for Person Identification, Tracking and Tracing """

    SEEN = 1
    TRANSIT = 2
    PROCEDURE = 3
    TRANSITIONAL_PRESENCE = (1, 2, 3)

    CHECK_IN = 11
    CONFIRMED = 12
    DECEASED = 13
    LOST = 14
    PERSISTANT_PRESENCE = (11, 12, 13, 14)

    TRANSFER = 21
    CHECK_OUT = 22
    ABSENCE = (21, 22)

    MISSING = 99

    # -------------------------------------------------------------------------
    def __init__(self):

        """ Constructor """

        # Trackable types
        self.trackable_types = {
            1:current.T("Person"),          # an individual
            2:current.T("Group"),           # a group
            3:current.T("Body"),            # a dead body or body part
            4:current.T("Object"),          # other objects belonging to persons
            5:current.T("Organization"),    # an organisation
            6:current.T("Office"),          # an office
        }
        self.DEFAULT_TRACKABLE = 1

        # Presence conditions
        self.presence_conditions = {
            # Transitional presence conditions:
            self.SEEN: current.T("Seen"),           # seen (formerly "found") at location
            self.TRANSIT: current.T("Transit"),     # seen at location, between two transfers
            self.PROCEDURE: current.T("Procedure"), # seen at location, undergoing procedure ("Checkpoint")

            # Persistant presence conditions:
            self.CHECK_IN: current.T("Check-In"),   # arrived at location for accomodation/storage
            self.CONFIRMED: current.T("Confirmed"), # confirmation of stay/storage at location
            self.DECEASED: current.T("Deceased"),   # deceased
            self.LOST: current.T("Lost"),           # destroyed/disposed at location

            # Absence conditions:
            self.TRANSFER: current.T("Transfer"),   # Send to another location
            self.CHECK_OUT: current.T("Check-Out"), # Left location for unknown destination

            # Missing condition:
            self.MISSING: current.T("Missing"),     # Missing (from a "last-seen"-location)
        }
        self.DEFAULT_PRESENCE = 1


    # -------------------------------------------------------------------------
    def presence_accept(self, presence):
        """
        Update the presence log of a person entity

            - mandatory to be called as onaccept routine at any modification
              of pr_presence records

        """

        db = current.db
        table = db.pr_presence

        if isinstance(presence, (int, long, str)):
            id = presence
        elif hasattr(presence, "vars"):
            id = presence.vars.id
        else:
            id = presence.id

        presence = db(table.id == id).select(table.ALL, limitby=(0,1)).first()
        if not presence:
            return
        else:
            condition = presence.presence_condition

        pe_id = presence.pe_id
        datetime = presence.datetime
        if not datetime or not pe_id:
            return

        this_entity = ((table.pe_id == pe_id) & (table.deleted == False))
        earlier = (table.datetime < datetime)
        later = (table.datetime > datetime)
        same_place = ((table.location_id == presence.location_id) |
                      (table.shelter_id == presence.shelter_id))
        is_present = (table.presence_condition.belongs(self.PERSISTANT_PRESENCE))
        is_absent = (table.presence_condition.belongs(self.ABSENCE))
        is_missing = (table.presence_condition == self.MISSING)

        if not presence.deleted:

            if condition in self.TRANSITIONAL_PRESENCE:
                if presence.closed:
                    db(table.id == id).update(closed=False)

            elif condition in self.PERSISTANT_PRESENCE:
                if not presence.closed:
                    query = this_entity & earlier & (is_present | is_missing) & \
                            (table.closed == False)
                    db(query).update(closed=True)

                    query = this_entity & later & \
                            (is_present | (is_absent & same_place))
                    if db(query).count():
                        db(table.id == id).update(closed=True)

            elif condition in self.ABSENCE:
                query = this_entity & earlier & is_present & same_place
                db(query).update(closed=True)

                if not presence.closed:
                    db(table.id == id).update(closed=True)

        if not presence.closed:

            # Re-open the last persistant presence if no closing event
            query = this_entity & is_present
            presence = db(query).select(table.ALL, orderby=~table.datetime, limitby=(0,1)).first()
            if presence and presence.closed:
                later = (table.datetime > presence.datetime)
                query = this_entity & later & is_absent & same_place
                if not db(query).count():
                    db(table.id == presence.id).update(closed=False)

            # Re-open the last missing if no later persistant presence
            query = this_entity & is_missing
            presence = db(query).select(table.ALL, orderby=~table.datetime, limitby=(0,1)).first()
            if presence and presence.closed:
                later = (table.datetime > presence.datetime)
                query = this_entity & later & is_present
                if not db(query).count():
                    db(table.id == presence.id).update(closed=False)

        pentity = db(db.pr_pentity.pe_id == pe_id).select(db.pr_pentity.instance_type,
                                                          limitby=(0,1)).first()
        if pentity and pentity.instance_type == "pr_person":
            query = this_entity & is_missing & (table.closed == False)
            if db(query).count():
                db(db.pr_person.pe_id == pe_id).update(missing = True)
            else:
                db(db.pr_person.pe_id == pe_id).update(missing = False)

        return

    # -------------------------------------------------------------------------
    def pentity(self, entity):

        """ Get the PersonEntity record for the given ID, ID Tag Number,
            sub-entity or related record

        """

        table = current.db.pr_pentity

        if entity:

            query = (table.deleted==False)

            if isinstance(entity, (int, long)) or \
               (isinstance(entity, str) and entity.strip().isdigit()):
                query = (table.id == entity) & query

            elif isinstance(entity, str):
                query = (table.label.strip().lower() == entity.strip().lower()) & query

            elif isinstance(entity, dict):
                if "pe_id" in entity:
                    query = (table.id == entity.pe_id) & query
                else:
                    return entity # entity already given?

            else:
                return None

            try:
                record = current.db(query).select(table.ALL, limitby=(0, 1)).first()
                return record
            except:
                return None

        else:
            return None

    # -------------------------------------------------------------------------
    def person(self, entity):

        """ Get the Person record for the given ID, PersonEntity record or
            Person-related record

        """

        table = current.db.pr_person

        if entity:

            query = (table.deleted==False)

            if isinstance(entity, (int, long)) or \
               (isinstance(entity, str) and entity.strip().isdigit()):
                query = (table.id == entity) & query

            elif isinstance(entity, dict):
                if "pe_id" in entity:
                    query = (table.pe_id == entity.pe_id) & query
                elif "person_id" in entity:
                    query = (table.id == entity.person_id) & query
                elif "id" in entity:
                    query = (table.pe_id == entity.id) & query
                else:
                    return None

            else:
                return None

            try:
                record = current.db(query).select(table.ALL, limitby=(0, 1)).first()
                return record
            except:
                return None

        else:
            return None

    # -------------------------------------------------------------------------
    def group(self, entity):

        """ Get the Group record for the given ID, PersonEntity record or
            Group-related record

        """

        table = current.db.pr_group

        if entity:

            query = (table.deleted == False)

            if isinstance(entity, (int, long)) or \
               (isinstance(entity, str) and entity.strip().isdigit()):
                query = (table.id == entity) & query

            elif isinstance(entity, dict):
                if "pe_id" in entity:
                    query = (table.pe_id == entity.pe_id) & query
                elif "group_id" in entity:
                    query = (table.id == entity.group_id) & query
                elif "id" in entity:
                    query = (table.pe_id == entity.id) & query
                else:
                    return None

            else:
                return None

            try:
                record = current.db(query).select(table.ALL, limitby=(0, 1)).first()
                return record
            except:
                return None

        else:
            return None

# END =========================================================================
