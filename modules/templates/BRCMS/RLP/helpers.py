# -*- coding: utf-8 -*-

"""
    Helper functions and classes for RLPCM template

    @license: MIT
"""

import datetime
import json
import os

from gluon import current, A, DIV, SPAN

from s3 import FS, ICON, S3DateFilter, s3_str, s3_yes_no_represent
from s3db.pr import pr_PersonEntityRepresent

# =============================================================================
def get_role_realms(role):
    """
        Get all realms for which a role has been assigned

        @param role: the role ID or role UUID

        @returns: list of pe_ids the current user has the role for,
                  None if the role is assigned site-wide, or an
                  empty list if the user does not have the role, or
                  no realm for the role
    """

    db = current.db
    auth = current.auth
    s3db = current.s3db

    if isinstance(role, str):
        gtable = auth.settings.table_group
        query = (gtable.uuid == role) & \
                (gtable.deleted == False)
        row = db(query).select(gtable.id,
                               cache = s3db.cache,
                               limitby = (0, 1),
                               ).first()
        role_id = row.id if row else None
    else:
        role_id = role

    role_realms = []
    user = auth.user
    if user:
        role_realms = user.realms.get(role_id, role_realms)

    return role_realms

# =============================================================================
def get_managed_orgs(role):
    """
        Get the organisations for which the current user has a role

        @param role: the role id or UUID

        @returns: list of organisation pe_ids
    """

    db = current.db
    s3db = current.s3db

    role_realms = get_role_realms(role)

    etable = s3db.pr_pentity
    query = (etable.instance_type == "org_organisation")
    if role_realms is not None:
        query = (etable.pe_id.belongs(role_realms)) & query

    rows = db(query).select(etable.pe_id)

    return [row.pe_id for row in rows]

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

        # TODO move client-side
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
                row = db(q).select(ltable.level, limitby=(0, 1)).first()
                if row:
                    level = row.level

        if location_ids and level and level < "L4":
            # Include all child Lx of the match locations below level
            # TODO make this recursive to include grandchildren etc. too
            q = (ltable.parent.belongs(location_ids)) & \
                (ltable.level != None) & \
                (ltable.level > level) & \
                (ltable.deleted == False)
            children = db(q).select(ltable.id)
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

# =============================================================================
class ProviderRepresent(pr_PersonEntityRepresent):

    def __init__(self, as_string=False):
        """
            Constructor

            @param show_label: show the ID tag label for persons
            @param default_label: the default for the ID tag label
            @param show_type: show the instance_type
            @param multiple: assume a value list by default
        """

        self.as_string = as_string

        super(ProviderRepresent, self).__init__(show_label = False,
                                                show_type = False,
                                                )

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        pentity = row.pr_pentity
        instance_type = pentity.instance_type

        item = object.__getattribute__(row, instance_type)
        if instance_type == "pr_person":
            if self.as_string:
                pe_str = current.T("private")
            else:
                pe_str = SPAN(current.T("private"), _class="free-hint")
        elif "name" in item:
            pe_str = s3_str(item["name"])
        else:
            pe_str = "?"

        return pe_str

# =============================================================================
class OverviewData(object):
    """
        Data extraction for overview page
    """

    # Color palette for categories
    # - same category should use the same color in all contexts
    palette = [
        "ffff00", "ff5500", "55aaff", "aaaa00", "939393", "8b2e8b",
        "1f6c6d", "b31c1c", "ff995e", "457624", "550000", "005500",
        "00007f", "006898", "7777b3", "e1cb74", "100000", "001000",
        "000010", "5500ff", "ffaaff", "00aa7f", "ffaa7f", "3f3f3f",
        "00aaff", "74aa1d", "b30000", "7e547e", "274214", "55007f",
        "0c9cd0", "e03158", "fba629", "8abc3f", "afb8bf",
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def get_color(cls, category):
        """
            Get a color from the palette

            @param category: an integer representing the category

            @returns: CSS hex color (string)
        """

        palette = cls.palette
        return "#%s" % (palette[category % len(palette)])

    # -------------------------------------------------------------------------
    @classmethod
    def needs_by_category(cls):
        """
            Count current case activities by need type
        """

        db = current.db
        s3db = current.s3db

        atable = s3db.br_case_activity
        stable = s3db.br_case_activity_status

        join = stable.on((stable.id == atable.status_id) & \
                         (stable.is_closed == False))

        today = current.request.utcnow.date()
        query = ((atable.date == None) | (atable.date <= today)) & \
                ((atable.end_date == None) | (atable.end_date >= today)) & \
                (atable.person_id != None) & \
                (atable.need_id != None) & \
                (atable.deleted == False)

        number = atable.id.count()
        rows = db(query).select(atable.need_id,
                                number,
                                join = join,
                                groupby = atable.need_id,
                                orderby = ~number,
                                limitby = (0, 5),
                                )

        represent = atable.need_id.represent
        labels = represent.bulk([row.br_case_activity.need_id for row in rows])

        values = []
        for row in rows:
            value = row[number]
            need_id = row.br_case_activity.need_id
            need = labels.get(need_id)
            values.append({"label": str(need),
                           "color": cls.get_color(need_id),
                           "value": value if value else 0,
                           })

        return [{"key": s3_str(current.T("Current Need Reports")),
                 "values": values,
                 },
                ]

    # -------------------------------------------------------------------------
    @classmethod
    def offers_by_category(cls):
        """
            Count current assistance offers by need type
        """

        db = current.db
        s3db = current.s3db

        atable = s3db.br_assistance_offer

        today = current.request.utcnow.date()
        query = (atable.status == "APR") & \
                (atable.availability == "AVL") & \
                ((atable.date == None) | (atable.date <= today)) & \
                ((atable.end_date == None) | (atable.end_date >= today)) & \
                (atable.pe_id != None) & \
                (atable.need_id != None) & \
                (atable.deleted == False)

        number = atable.id.count()
        rows = db(query).select(atable.need_id,
                                number,
                                groupby = atable.need_id,
                                orderby = ~number,
                                limitby = (0, 5),
                                )

        represent = atable.need_id.represent
        labels = represent.bulk([row.br_assistance_offer.need_id for row in rows])

        values = []
        for row in rows:
            value = row[number]
            need_id = row.br_assistance_offer.need_id
            need = labels.get(need_id)
            values.append({"label": str(need),
                           "color": cls.get_color(need_id),
                           "value": value if value else 0,
                           })

        return [{"key": s3_str(current.T("Current Relief Offers")),
                 "values": values,
                 },
                ]

    # -------------------------------------------------------------------------
    @classmethod
    def usage_statistics(cls):
        """
            Establish site usage statistics

            @returns: the usage stats, a dict:

                     {"au": 0,   # Number of active users
                      "ao": 0,   # Number of active organisations
                      "nr": 0,   # Number of active need reports
                      "ro": 0,   # Number of active assistance offers
                      "pn": 0,   # Number of people with needs reported
                      "po": 0,  # Number of users offering help
                      }
        """

        db = current.db

        auth = current.auth
        s3db = current.s3db

        data = {}

        today = current.request.utcnow
        two_days_back = today - datetime.timedelta(days=2)

        utable = auth.settings.table_user
        gtable = auth.settings.table_group
        mtable = auth.settings.table_membership

        active_user = ((utable.registration_key == None) | (utable.registration_key == "")) & \
                      (utable.timestmp > two_days_back) & \
                      (utable.deleted == False)

        # Get the number of active users
        join = [mtable.on((mtable.user_id == utable.id) &
                          (mtable.deleted == False)),
                gtable.on((gtable.id == mtable.group_id) & \
                          (gtable.uuid.belongs(("CITIZEN", "RELIEF_PROVIDER"))))
                          ]
        query = active_user
        number = utable.id.count()
        row = db(query).select(number, join=join).first()
        if row:
            data["au"] = row[number]

        # Get the number of active organisations
        htable = s3db.hrm_human_resource
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user

        join = [ptable.on(ptable.id == htable.person_id),
                ltable.on((ltable.pe_id == ptable.pe_id) & \
                          (ltable.deleted == False)),
                utable.on((utable.id == ltable.user_id) & \
                          active_user),
                mtable.on((mtable.user_id == utable.id) &
                          (mtable.deleted == False)),
                gtable.on((gtable.id == mtable.group_id) & \
                          (gtable.uuid == "RELIEF_PROVIDER")),
                ]
        number = htable.organisation_id.count()
        row = db(query).select(number, join=join).first()
        if row:
            data["ao"] = row[number]

        # Count current need reports and distinct beneficiaries
        atable = s3db.br_case_activity
        stable = s3db.br_case_activity_status
        join = stable.on((stable.id == atable.status_id) & \
                         (stable.is_closed == False))
        query = ((atable.date == None) | (atable.date <= today)) & \
                ((atable.end_date == None) | (atable.end_date >= today)) & \
                (atable.deleted == False)
        number = atable.id.count()
        persons = atable.person_id.count(distinct=True)
        row = db(query).select(number, persons, join=join).first()
        if row:
            data["nr"] = row[number]
            data["pn"] = row[persons]

        # Count current assistance offers and distinct providers
        otable = s3db.br_assistance_offer
        query = (otable.status == "APR") & \
                (otable.availability != "RTD") & \
                ((otable.date == None) | (otable.date <= today)) & \
                ((otable.end_date == None) | (otable.end_date >= today)) & \
                (otable.deleted == False)
        number = otable.id.count()
        persons = otable.pe_id.count(distinct=True)
        row = db(query).select(number, persons).first()
        if row:
            data["ro"] = row[number]
            data["po"] = row[persons]

        return data

    # -------------------------------------------------------------------------
    @classmethod
    def update_data(cls):
        """
            Update data files for overview page

            NB requires write-permission for static/data/RLP folder+files
        """

        current.log.debug("Updating overview data")

        SEPARATORS = (",", ":")

        os_path_join = os.path.join
        json_dump = json.dump

        base = os_path_join(current.request.folder, "static", "data", "RLP")

        path = os_path_join(base, "rlpcm_needs.json")
        data = cls.needs_by_category()
        with open(path, "w") as outfile:
            json_dump(data, outfile, separators=SEPARATORS)

        path = os_path_join(base, "rlpcm_offers.json")
        data = cls.offers_by_category()
        with open(path, "w") as outfile:
            json_dump(data, outfile, separators=SEPARATORS)

        path = os_path_join(base, "rlpcm_usage.json")
        data = cls.usage_statistics()
        with open(path, "w") as outfile:
            json_dump(data, outfile, separators=SEPARATORS)

# =============================================================================
class OfferDetails(object):
    """
        Field methods for compact representation of place and
        contact information of offers
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def place(row):

        if hasattr(row, "gis_location"):
            location = row.gis_location
        else:
            location = row

        return tuple(location.get(level)
                     for level in ("L3", "L2", "L1"))

    # -------------------------------------------------------------------------
    @staticmethod
    def place_represent(value, row=None):

        if isinstance(value, tuple) and len(value) == 3:
            l3 = value[0]
            lx = tuple(n if n else "-" for n in value[1:])
            output = DIV(_class = "place-repr",
                         )
            if l3:
                output.append(DIV(l3,
                                  _class = "place-name",
                                  ))
            if lx:
                output.append(DIV("%s / %s" % lx,
                                  _class = "place-info",
                                  ))
            return output
        else:
            return value if value else "-"

    # -------------------------------------------------------------------------
    @staticmethod
    def contact(row):

        if hasattr(row, "br_assistance_offer"):
            offer = row.br_assistance_offer
        else:
            offer = row

        return tuple(offer.get(detail)
                     for detail in ("contact_name",
                                    "contact_phone",
                                    "contact_email",
                                    ))

    # -------------------------------------------------------------------------
    @staticmethod
    def contact_represent(value, row=None):

        if isinstance(value, tuple) and len(value) == 3:
            name, phone, email = value

            output = DIV(_class = "contact-repr",
                         )
            if name:
                output.append(SPAN(name,
                                   _class = "contact-name",
                                   ))

            if email or phone:
                details = DIV(_class="contact-details")
                if phone:
                    details.append(DIV(ICON("phone"),
                                       SPAN(phone,
                                            _class = "contact-phone"),
                                       _class = "contact-info",
                                       ))
                if email:
                    details.append(DIV(ICON("mail"),
                                       SPAN(A(email,
                                              _href="mailto:%s" % email,
                                              ),
                                            _class = "contact-email"),
                                       _class = "contact-info",
                                       ))
                output.append(details)

            return output
        else:
            return value if value else "-"

# =============================================================================
class OfferAvailabilityFilter(S3DateFilter):
    """
        Date-Range filter with custom variable
        - without this then we parse as a vfilter which clutters error console
          & is inefficient (including preventing a bigtable optimisation)
    """

    @classmethod
    def _variable(cls, selector, operator):

        return super()._variable("$$available", operator)

    # -------------------------------------------------------------------------
    @staticmethod
    def apply_filter(resource, get_vars):
        """
            Filter out offers that
            - become available only after a start date, or
            - become unavailable before an end date

            (reversed logic compared to a normal range filter)
        """

        parse_dt = current.calendar.parse_date

        from_date = parse_dt(get_vars.get("$$available__ge"))
        to_date = parse_dt(get_vars.get("$$available__le"))

        if from_date:
            query = (FS("date") == None) | (FS("date") <= from_date)
            resource.add_filter(query)

        if to_date:
            query = (FS("end_date") == None) | (FS("end_date") >= to_date)
            resource.add_filter(query)

# =============================================================================
def notify_direct_offer(record_id):
    # TODO docstring

    T = current.T

    db = current.db
    s3db = current.s3db

    table = s3db.br_direct_offer

    today = current.request.utcnow.date()
    atable = s3db.br_case_activity
    stable = s3db.br_case_activity_status
    aotable = s3db.br_assistance_offer
    join = [atable.on((atable.id == table.case_activity_id) & \
                      (atable.deleted == False)),
            stable.on((stable.id == atable.status_id) & \
                      (stable.is_closed == False)),
            aotable.on((aotable.id == table.offer_id) & \
                       (aotable.status != "BLC") & \
                       ((aotable.end_date == None) | (aotable.end_date >= today)) & \
                       (aotable.deleted == False)),
            ]
    query = (table.id == record_id) & \
            (table.notify == True) & \
            (table.notified_on == None) & \
            (table.deleted == False)
    row = db(query).select(table.id,
                           table.case_activity_id,
                           table.offer_id,
                           atable.person_id,
                           join = join,
                           limitby = (0, 1),
                           ).first()
    if not row:
        return None

    direct_offer = row.br_direct_offer
    case_activity = row.br_case_activity

    # Determine recipient
    recipient = None
    user_id = current.auth.s3_get_user_id(case_activity.person_id)
    if user_id:
        # Look up the user's email address
        ltable = s3db.pr_person_user
        ctable = s3db.pr_contact
        join = ctable.on((ctable.pe_id == ltable.pe_id) & \
                         (ctable.contact_method == "EMAIL") & \
                         (ctable.deleted == False))
        query = (ltable.user_id == user_id) & \
                (ltable.deleted == False)
        row = db(query).select(ctable.value,
                               join = join,
                               orderby = ctable.priority,
                               limitby = (0, 1),
                               ).first()
        if row:
            recipient = row.value
    else:
        # Look up the case org
        ctable = s3db.br_case
        query = (ctable.person_id == case_activity.person_id) & \
                (ctable.deleted == False)
        row = db(query).select(ctable.organisation_id,
                               limitby = (0, 1),
                               ).first()
        if row:
            organisation_id = row.organisation_id
        else:
            return T("Case Organisation not found")

        # Look up the email addresses of CASE_MANAGERs
        from templates.RLPPTM.helpers import get_role_emails
        recipient = get_role_emails("CASE_MANAGER",
                                    organisation_id = organisation_id,
                                    )
        if not recipient:
            # Fall back
            recipient = get_role_emails("RELIEF_PROVIDER",
                                        organisation_id = organisation_id,
                                        )

    if not recipient:
        return T("No suitable recipient for notification found")

    if isinstance(recipient, list) and len(recipient) == 1:
        recipient = recipient[0]

    # Lookup data for notification
    ltable = s3db.gis_location
    left = ltable.on(ltable.id == aotable.location_id)
    query = (aotable.id == direct_offer.offer_id)
    row = db(query).select(aotable.id,
                           aotable.pe_id,
                           aotable.refno,
                           aotable.name,
                           aotable.description,
                           aotable.chargeable,
                           aotable.contact_name,
                           aotable.contact_phone,
                           aotable.contact_email,
                           aotable.date,
                           aotable.end_date,
                           aotable.availability,
                           ltable.id,
                           ltable.L3,
                           ltable.L1,
                           left = left,
                           limitby = (0, 1),
                           ).first()

    offer = row.br_assistance_offer
    location = row.gis_location

    provider = ProviderRepresent(as_string=True)(offer.pe_id)
    availability_opts = dict(s3db.br_assistance_offer_availability)
    availability = availability_opts.get(offer.availability, "-")

    public_url = current.deployment_settings.get_base_public_url()
    appname = current.request.application
    base_url = "%s/%s" % (public_url, appname)
    data = {"provider": s3_str(provider),
            "title": offer.name or "-",
            "details": offer.description or "-",
            "refno": offer.refno or "-",
            "name": offer.contact_name or "-",
            "phone": offer.contact_phone or "-",
            "email": offer.contact_email or "-",
            "chargeable": s3_yes_no_represent(offer.chargeable),
            "available_from": aotable.date.represent(offer.date),
            "available_until": aotable.end_date.represent(offer.end_date),
            "availability": s3_str(availability),
            "offer_url": "%s/br/offers/%s" % (base_url, direct_offer.offer_id),
            "need_url":  "%s/br/case_activity/%s" % (base_url, direct_offer.case_activity_id),
            }
    if location.id:
        data["place"] = "%s (%s)" % (location.L3 or "-",
                                     location.L1 or "-",
                                     )

    # Send notification
    from templates.RLPPTM.notifications import CMSNotifications
    error = CMSNotifications.send(recipient,
                                  "DirectOfferNotification",
                                  data,
                                  #cc = None,
                                  module = "br",
                                  resource = "direct_offer",
                                  )
    if not error:
        # Set notified_on
        direct_offer.update_record(notified_on = datetime.datetime.utcnow,
                                   modified_on = table.modified_on,
                                   modified_by = table.modified_by,
                                   )
    return error

# END =========================================================================
