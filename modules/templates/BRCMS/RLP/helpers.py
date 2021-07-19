# -*- coding: utf-8 -*-

"""
    Helper functions and classes for RLPCM template

    @license: MIT
"""

from gluon import current

# =============================================================================
def get_current_events(record):
    """
        Look up all current events

        @param record: include the event_id of this record even
                       if the event is closed

        @returns: list of event_ids, most recent first
    """

    db = current.db
    s3db = current.s3db

    table = s3db.event_event
    query = (table.closed == False)
    if record:
        query |= (table.id == record.event_id)
    query &= (table.deleted == False)
    rows = db(query).select(table.id,
                            orderby = ~table.start_date,
                            )
    return [row.id for row in rows]

# =============================================================================
def get_current_location(person_id=None):
    """
        Look up the current tracking location of a person

        @param person_id: the person ID (defaults to logged-in person)

        @returns: the ID of the lowest-level Lx of the current
                  tracking location of the person
    """

    if not person_id:
        person_id = current.auth.s3_logged_in_person()

    from s3 import S3Trackable
    trackable = S3Trackable(tablename="pr_person", record_id=person_id)

    # Look up the location
    location = trackable.get_location()
    if not location:
        return None
    if isinstance(location, list):
        location = location[0]

    # Return only Lx
    if location.level:
        return location.id
    else:
        return location.parent

# END =========================================================================
