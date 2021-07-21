# -*- coding: utf-8 -*-

"""
    Helper functions and classes for RLPCM template

    @license: MIT
"""

from gluon import current

from s3 import FS

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

# =============================================================================
def get_offer_filters(person_id=None):
    """
        Get filters for br_assistance_offer matching a person's
        current needs

        @param person_id: the person ID

        @returns: S3ResourceQuery to apply to an br_assistance_offer
                  resource, or None, if matching is not possible
    """

    db = current.db
    auth = current.auth
    s3db = current.s3db

    if not person_id:
        person_id = auth.s3_logged_in_person()
    if not person_id:
        return None

    # Lookup all current needs of the person
    atable = s3db.br_case_activity
    ltable = s3db.gis_location
    ptable = s3db.pr_person
    stable = s3db.br_case_activity_status

    today = current.request.utcnow.date()

    join = [ptable.on(ptable.id == atable.person_id),
            stable.on((stable.id == atable.status_id) & \
                      (stable.is_closed == False)),
            ]
    left = ltable.on(ltable.id == atable.location_id)
    query = (atable.person_id == person_id) & \
            (atable.need_id != None) & \
            (atable.location_id != None) & \
            ((atable.date == None) | (atable.date <= today)) & \
            ((atable.end_date == None) | (atable.end_date >= today)) & \
            (atable.deleted == False)
    rows = db(query).select(atable.need_id,
                            atable.location_id,
                            ltable.name,
                            #ltable.parent,
                            ltable.level,
                            ltable.path,
                            ptable.pe_id,
                            join = join,
                            left = left,
                            )

    gis = current.gis
    get_neighbours = gis.get_neighbours
    get_parents = gis.get_parents
    filters, exclude_provider = None, None
    for row in rows:

        # Provider to exclude
        person = row.pr_person
        exclude_provider = person.pe_id

        activity = row.br_case_activity

        # Match by need
        query = FS("~.need_id") == activity.need_id

        # Match by Location
        # - include exact match if Need is at an Lx
        # - include all higher level Lx
        # - include all adjacent lowest-level Lx
        location_id = activity.location_id

        location = row.gis_location
        level = location.level

        if level:
            # Lx location (the normal case)
            location_ids = [location_id]

            # Include all parent Lx
            parents = get_parents(location_id, feature=location, ids_only=True)
            if parents:
                location_ids += parents

            # Include all adjacent Lx of the same level
            neighbours = get_neighbours(location_id)
            if neighbours:
                location_ids += neighbours
        else:
            # Specific address
            location_ids = []

            # Include all parent Lx
            parents = get_parents(location_id, feature=location, ids_only=True)
            if parents:
                location_ids = parents
                # Include all adjacent Lx of the immediate ancestor Lx
                neighbours = get_neighbours(parents[0])
                if neighbours:
                    location_ids += neighbours

                # Lookup the immediate ancestor's level
                q = (ltable.id == parents[0]) & (ltable.deleted == False)
                row = db(query).select(ltable.level, limitby=(0, 1)).first()
                if row:
                    level = row.level

        if location_ids and level and level < "L4":
            # Include all child Lx of the match locations below level
            # TODO make this recursive to include grandchildren etc. too
            q = (ltable.parent.belongs(location_ids)) & \
                (ltable.level != None) & \
                (ltable.level > level) & \
                (ltable.deleted == False)
            children = db(query).select(ltable.id)
            location_ids += [c.id for c in children]

        if location_ids:
            if len(location_ids) == 1:
                q = FS("~.location_id") == list(location_ids)[0]
            else:
                q = FS("~.location_id").belongs(location_ids)
            query = (query & q) if query else q
        else:
            continue

        filters = (filters | query) if filters else query

    # Exclude the person's own offers
    if exclude_provider:
        filters &= FS("~.pe_id") != exclude_provider

    return filters

# END =========================================================================
