# -*- coding: utf-8 -*-

import datetime
import json

from gluon import current, Field, IS_NOT_EMPTY, INPUT, A, SQLFORM, URL

from s3 import s3_str, s3_encode_iso_datetime, s3_fullname, S3DateTime
from s3db.dvr import DVRRegisterCaseEvent

# =============================================================================
class DRKRegisterFoodEvent(DVRRegisterCaseEvent):
    """
        Special variant of DVRRegisterCaseEvent for DRK food distribution,
        handles all family members in one step
    """

    # -------------------------------------------------------------------------
    def registration_ajax(self, r, **attr):
        """
            Ajax response method, expects a JSON input like:

                {l: the PE label (from the input field),
                 c: boolean to indicate whether to just check
                    the PE label or to register payments
                 t: the event type code
                 x: [array of PE labels,
                     only when registering for multiple persons
                     ]
                 }

            @param r: the S3Request instance
            @param attr: controller parameters
            @return: JSON response, structure:

                    {l: the actual PE label (to update the input field),
                     p: the person details,
                     d: the family details,
                     f: [{n: the flag name
                          i: the flag instructions
                          },
                         ...],
                     b: profile picture URL,
                     i: {<event_code>: [<msg>, <blocked_until_datetime>]},

                     x: [{l: the family member PE label,
                          n: the family member full name,
                          d: the family member date of birth,
                          p: the family member profile picture URL,
                          r: {<event_code>: [<msg>, <blocked_until_datetime>]},
                          },
                         ],

                     s: whether the action is permitted or not

                     e: form error (for label field)

                     a: error message
                     w: warning message
                     m: success message
                     }
        """

        T = current.T
        s3db = current.s3db

        # Load JSON data from request body
        s = r.body
        s.seek(0)
        try:
            data = json.load(s)
        except (ValueError, TypeError):
            r.error(400, current.ERROR.BAD_REQUEST)


        # Initialize processing variables
        output = {}

        error = None

        alert = None
        message = None
        warning = None

        permitted = False
        flags = []

        # Identify the person
        pe_label = data.get("l")
        person = self.get_person(pe_label)

        if person is None:
            error = s3_str(T("No person found with this ID number"))

        else:
            # Get flag info
            flag_info = s3db.dvr_get_flag_instructions(person.id,
                                                       action = "id-check",
                                                       )
            permitted = flag_info["permitted"]

            check = data.get("c")
            if check:

                output["l"] = person.pe_label

                # Person details
                person_details = self.person_details(person)
                output["p"] = s3_str(person_details)

                # Profile picture
                profile_picture = self.profile_picture(person)
                output["b"] = profile_picture

                # Household Size
                details = s3db.dvr_get_household_size(person.id,
                                                      dob = person.date_of_birth,
                                                      )
                if details:
                    output["d"] = {"d": details}

                # Family Members
                family_members = self.get_family_members(person)
                if family_members:
                    output["x"] = family_members

                # Flag Info
                info = flag_info["info"]
                for flagname, instructions in info:
                    flags.append({"n": s3_str(T(flagname)),
                                  "i": s3_str(T(instructions)),
                                  })

                # Blocking periods for events
                event_types = self.get_event_types()
                blocked = self.get_blocked_events(person.id)
                intervals = {}
                for type_id, info in blocked.items():
                    event_type = event_types.get(type_id)
                    if not event_type:
                        continue
                    code = event_type.code
                    msg, dt = info
                    intervals[code] = (s3_str(msg),
                                       "%sZ" % s3_encode_iso_datetime(dt),
                                       )
                output["i"] = intervals
            else:
                # Check event code and permission
                type_id = None
                event_code = data.get("t")
                if not event_code:
                    alert = T("No event type specified")
                elif not permitted:
                    alert = T("Event registration not permitted")
                else:
                    event_type = self.get_event_type(event_code)
                    if not event_type:
                        alert = T("Invalid event type: %s") % event_code
                    else:
                        type_id = event_type.id

                if type_id:

                    family_labels = data.get("x")
                    if family_labels:
                        # Register event for multiple family members

                        # Get family members and interval rules
                        family_members = self.get_family_members(person,
                                                                 include_ids = True,
                                                                 )
                        family_members = dict((m["l"], m) for m in family_members)

                        registered = 0
                        alerts = []
                        for label in family_labels:

                            # Get the family member person_id
                            member = family_members.get(label)
                            if not member:
                                continue
                            member_id = member.get("id")

                            # Check interval rules
                            rules = member.get("r")
                            if rules and event_code in rules:
                                # Event type is currently blocked for this
                                # family member
                                alerts.append(": ".join((s3_str(member["n"]),
                                                         s3_str(rules[event_code][0]),
                                                         )))
                            else:
                                # Ok - register the event
                                self.register_event(member_id, type_id)
                                registered += 1

                        if alerts:
                            alert = ", ".join(alerts)
                        if registered:
                            message = T("%(number)s registrations successful") % \
                                       {"number": registered}
                        elif not alerts:
                            alert = T("Could not register event")

                    else:

                        # Check whether event type is blocked for this person
                        person_id = person.id
                        blocked = self.get_blocked_events(person_id,
                                                          type_id = type_id,
                                                          )
                        if type_id in blocked:
                            # Event type is currently blocked for this person
                            alert = blocked[type_id][0]
                        else:
                            # Ok - register the event
                            success = self.register_event(person.id, type_id)
                            if success:
                                message = T("Event registered")
                            else:
                                alert = T("Could not register event")

        # Add messages to output
        if alert:
            output["a"] = s3_str(alert)
        if error:
            output["e"] = s3_str(error)
        if message:
            output["m"] = s3_str(message)
        if warning:
            output["w"] = s3_str(warning)

        # Add flag info to output
        output["s"] = permitted
        output["f"] = flags

        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(output)

    # -------------------------------------------------------------------------
    def get_form_data(self, person, formfields, data, hidden, permitted=False):
        """
            Helper function to extend the form

            @param person: the person (Row)
            @param formfields: list of form fields (Field)
            @param data: the form data (dict)
            @param hidden: hidden form fields (dict)
            @param permitted: whether the action is permitted

            @return: tuple (widget_id, submit_label)
        """

        T = current.T

        # Extend form with household size info
        if person:
            family_members = self.get_family_members(person)
            details = current.s3db.dvr_get_household_size(person.id,
                                             dob = person.date_of_birth,
                                             )
        else:
            family_members = []
            details = ""

        formfields.extend([Field("details",
                                 label = T("Family"),
                                 writable = False,
                                 ),
                           Field("family",
                                 label = "",
                                 writable = False,
                                 ),
                           ])

        data["details"] = details
        data["family"] = ""

        hidden["family"] = json.dumps(family_members)

        widget_id = "case-event-form"
        submit = current.T("Register")

        return widget_id, submit

    # -------------------------------------------------------------------------
    def get_family_members(self, person, include_ids=False):
        """
            Get infos for all family members of person

            @param person: the person (Row)
            @param include_ids: include the person record IDs

            @returns: array with family member infos, format:
                            [{i: the person record ID (if requested)
                              l: pe_label,
                              n: fullname,
                              d: dob_formatted,
                              p: picture_URL,
                              r: {
                                event_code: {
                                    m: message,
                                    e: earliest_date_ISO
                                }
                              }, ...
                             ]
        """

        db = current.db
        s3db = current.s3db

        ptable = s3db.pr_person
        itable = s3db.pr_image
        gtable = s3db.pr_group
        mtable = s3db.pr_group_membership
        ctable = s3db.dvr_case
        stable = s3db.dvr_case_status

        # Get all case groups this person belongs to
        person_id = person.id
        query = ((mtable.person_id == person_id) & \
                 (mtable.deleted != True) & \
                 (gtable.id == mtable.group_id) & \
                 (gtable.group_type == 7))
        rows = db(query).select(gtable.id)
        group_ids = set(row.id for row in rows)

        members = {}

        if group_ids:
            join = [ptable.on(ptable.id == mtable.person_id),
                    ctable.on((ctable.person_id == ptable.id) & \
                              (ctable.archived == False) & \
                              (ctable.deleted == False)),
                    ]

            left = [stable.on(stable.id == ctable.status_id),
                    itable.on((itable.pe_id == ptable.pe_id) & \
                              (itable.profile == True) & \
                              (itable.deleted == False)),
                    ]

            query = (mtable.group_id.belongs(group_ids)) & \
                    (mtable.deleted != True) & \
                    (stable.is_closed != True)
            rows = db(query).select(ptable.id,
                                    ptable.pe_label,
                                    ptable.first_name,
                                    ptable.last_name,
                                    ptable.date_of_birth,
                                    itable.image,
                                    join = join,
                                    left = left,
                                    )

            for row in rows:
                member_id = row.pr_person.id
                if member_id not in members:
                    members[member_id] = row

        output = []

        if members:

            # All event types and blocking rules
            event_types = self.get_event_types()
            intervals = self.get_interval_rules(set(members.keys()))

            for member_id, data in members.items():

                member = data.pr_person
                picture = data.pr_image

                # Person data
                data = {"l": member.pe_label,
                        "n": s3_fullname(member),
                        "d": S3DateTime.date_represent(member.date_of_birth),
                        }

                # Record ID?
                if include_ids:
                    data["id"] = member_id

                # Profile picture URL
                if picture.image:
                    data["p"] = URL(c = "default",
                                    f = "download",
                                    args = picture.image,
                                    )

                # Blocking rules
                event_rules = intervals.get(member_id)
                if event_rules:
                    rules = {}
                    for event_type_id, rule in event_rules.items():
                        code = event_types.get(event_type_id).code
                        rules[code] = (s3_str(rule[0]),
                                       "%sZ" % s3_encode_iso_datetime(rule[1]),
                                       )
                    data["r"] = rules

                # Add info to output
                output.append(data)

        return output

    # -------------------------------------------------------------------------
    def get_interval_rules(self, person_ids):
        """
            Get interval (blocking) rules for persons

            @param person_ids: list|tuple|set of person record IDs
            @return: rules dict, format:
                        {person_id:
                            {event_type_id: (message, earliest_datetime),
                             ...
                             },
                         ...
                         }
        """

        T = current.T

        db = current.db
        s3db = current.s3db

        now = current.request.utcnow
        day_start = now.replace(hour=0,
                                minute=0,
                                second=0,
                                microsecond=0,
                                )
        next_day = day_start + datetime.timedelta(days=1)

        output = {}

        table = s3db.dvr_case_event
        event_type_id = table.type_id
        person_id = table.person_id

        # Get event types to check
        event_types = self.get_event_types()

        # Check impermissible combinations
        etable = s3db.dvr_case_event_exclusion
        query = (table.person_id.belongs(person_ids)) & \
                (table.date >= day_start) & \
                (table.deleted == False) & \
                (etable.excluded_by_id == table.type_id) & \
                (etable.deleted == False)

        rows = db(query).select(table.person_id,
                                etable.type_id,
                                etable.excluded_by_id,
                                )
        collisions = {}
        for row in rows:
            event = row.dvr_case_event
            exclusion = row.dvr_case_event_exclusion

            pid = event.person_id
            if pid in collisions:
                excluded = collisions[pid]
            else:
                excluded = collisions[pid] = {}

            tid = exclusion.type_id
            if tid in excluded:
                excluded[tid].append(exclusion.excluded_by_id)
            else:
                excluded[tid] = [exclusion.excluded_by_id]

        for pid, excluded in collisions.items():

            if pid not in output:
                rules = output[pid] = {}
            else:
                rules = output[pid]

            for tid, excluded_by_ids in excluded.items():

                event_type = event_types.get(tid)
                if not event_type:
                    continue

                excluded_by_names = []
                seen = set()
                for excluded_by_id in excluded_by_ids:
                    if excluded_by_id in seen:
                        continue
                    else:
                        seen.add(excluded_by_id)
                    excluded_by_type = event_types.get(excluded_by_id)
                    if not excluded_by_type:
                        continue
                    excluded_by_names.append(s3_str(T(excluded_by_type.name)))

                if excluded_by_names:
                    msg = T("%(event)s already registered today, not combinable") % \
                            {"event": ", ".join(excluded_by_names)
                             }
                    rules[tid] = (msg, next_day)

        # Helper function to build event type sub-query
        def type_query(items):
            if len(items) == 1:
                return (event_type_id == items[0])
            elif items:
                return (event_type_id.belongs(set(items)))
            else:
                return None

        # Check maximum occurences per day
        check = [tid for tid, row in event_types.items()
                 if row.max_per_day and tid != "_default"
                 ]
        q = type_query(check)
        if q is not None:

            # Get number of events per type and person today
            cnt = table.id.count()
            query = (table.person_id.belongs(person_ids)) & q & \
                    (table.date >= day_start) & \
                    (table.deleted != True)
            rows = db(query).select(person_id,
                                    event_type_id,
                                    cnt,
                                    groupby = (person_id, event_type_id),
                                    )

            # Check limit
            for row in rows:

                number = row[cnt]

                pid = row[person_id]
                if pid not in output:
                    rules = output[pid] = {}
                else:
                    rules = output[pid]

                tid = row[event_type_id]
                if tid in rules:
                    continue

                event_type = event_types[tid]
                limit = event_type.max_per_day

                if number >= limit:
                    if number > 1:
                        msg = T("%(event)s already registered %(number)s times today") % \
                                {"event": T(event_type.name),
                                 "number": number,
                                 }
                    else:
                        msg = T("%(event)s already registered today") % \
                                {"event": T(event_type.name),
                                 }
                    rules[tid] = (msg, next_day)

        # Check minimum intervals
        check = [tid for tid, row in event_types.items()
                 if row.min_interval and tid != "_default"
                 ]
        q = type_query(check)
        if q is not None:

            # Get the last events for these types per person
            query = (table.person_id.belongs(person_ids)) & q & \
                    (table.deleted != True)
            timestamp = table.date.max()
            rows = db(query).select(person_id,
                                    event_type_id,
                                    timestamp,
                                    groupby = (person_id, event_type_id),
                                    )

            # Check intervals
            represent = table.date.represent
            for row in rows:

                latest = row[timestamp]

                pid = row[person_id]
                if pid not in output:
                    rules = output[pid] = {}
                else:
                    rules = output[pid]

                tid = row[event_type_id]
                if tid in rules:
                    continue

                event_type = event_types[tid]
                interval = event_type.min_interval

                if latest:
                    earliest = latest + datetime.timedelta(hours=interval)
                    if earliest > now:
                        msg = T("%(event)s already registered on %(timestamp)s") % \
                                    {"event": T(event_type.name),
                                     "timestamp": represent(latest),
                                     }
                        rules[tid] = (msg, earliest)

        return output

    # -------------------------------------------------------------------------
    def get_event_types(self):
        """
            Lazy getter for case event types

            @return: a dict {id: Row} for dvr_case_event_type, with an
                     additional key "_default" for the default event type
        """

        if not hasattr(self, "event_types"):

            event_types = {}
            table = current.s3db.dvr_case_event_type

            # Active event types
            query = (table.is_inactive == False) & \
                    (table.code.like("FOOD%")) & \
                    (table.deleted == False)

            # Roles required
            sr = current.auth.get_system_roles()
            roles = current.session.s3.roles
            if sr.ADMIN not in roles:
                query &= (table.role_required == None) | \
                         (table.role_required.belongs(roles))

            rows = current.db(query).select(table.id,
                                            table.code,
                                            table.name,
                                            table.is_default,
                                            table.min_interval,
                                            table.max_per_day,
                                            table.comments,
                                            )
            for row in rows:
                event_types[row.id] = row
                if row.is_default:
                    event_types["_default"] = row
            self.event_types = event_types

        return self.event_types

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_js(widget_id, options):
        """
            Helper function to inject static JS and instantiate
            the foodRegistration widget

            @param widget_id: the node ID where to instantiate the widget
            @param options: dict of widget options (JSON-serializable)
        """

        T = current.T

        s3 = current.response.s3
        appname = current.request.application

        # Custom Ajax-URL
        options["ajaxURL"] = URL(c = "dvr",
                                 f = "case_event",
                                 args = ["register_food.json"],
                                 )
        options["selectAllText"] = s3_str(T("Select All"))

        # Custom JS
        scripts = s3.scripts
        # @Todo: minify?
        #if s3.debug:
        #    script = "/%s/static/themes/DRK/js/food.js" % appname
        #else:
        #    script = "/%s/static/themes/DRK/js/food.min.js" % appname
        script = "/%s/static/themes/DRK/js/food.js" % appname
        scripts.append(script)

        # Instantiate widget
        scripts = s3.jquery_ready
        script = '''$('#%(id)s').foodRegistration(%(options)s)''' % \
                 {"id": widget_id, "options": json.dumps(options)}
        if script not in scripts:
            scripts.append(script)

# END =========================================================================
