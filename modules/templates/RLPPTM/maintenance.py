"""
    Maintenance Tasks for RLPPTM

    License: MIT
"""

import datetime

from gluon import current

# =============================================================================
class Daily():
    """ Daily Maintenance Tasks """

    def __call__(self):

        db = current.db
        s3db = current.s3db

        current.log.info("Daily Maintenance RLPPTM")
        errors = None

        now = datetime.datetime.utcnow()
        week_past = now - datetime.timedelta(weeks=1)

        # Cleanup Scheduler logs
        table = s3db.scheduler_run
        db(table.start_time < week_past).delete()

        # Cleanup Sync logs
        table = s3db.sync_log
        db(table.timestmp < week_past).delete()

        # Cleanup old sessions
        from core.tools.utils import remove_old_sessions
        remove_old_sessions(ttl=1)

        # Cleanup unverified accounts
        self.cleanup_unverified_accounts()

        # Update the RAT device list
        from .rat import RATList
        RATList.sync()

        # Cleanup DCC data
        from .dcc import DCC
        DCC.cleanup()

        # Check for expired commissions
        self.expire_commissions()

        # Check/update verification status for changed org type requirements
        self.check_verification_status()

        # On Sundays, cleanup public test station registry
        settings = current.deployment_settings
        if settings.get_custom(key="test_station_cleanup") and \
           now.weekday() == 6:
            errors = self.cleanup_public_registry()

        return errors if errors else None

    # -------------------------------------------------------------------------
    @staticmethod
    def cleanup_unverified_accounts():
        """
            Remove unverified user accounts
        """

        db = current.db
        s3db = current.s3db
        auth = current.auth

        auth_settings = auth.settings

        now = datetime.datetime.utcnow()

        utable = auth_settings.table_user
        mtable = auth_settings.table_membership
        ttable = s3db.auth_user_temp
        ltable = s3db.pr_person_user

        left = [ltable.on(ltable.user_id == utable.id),
                mtable.on(mtable.user_id == utable.id),
                ]

        query = (utable.created_on < now - datetime.timedelta(hours=48)) & \
                (utable.registration_key != None) & \
                (~(utable.registration_key.belongs("", "disabled", "blocked", "pending"))) & \
                (utable.deleted == False) & \
                (ltable.id == None) & \
                (mtable.id == None)

        rows = db(query).select(utable.id,
                                utable.email,
                                left = left,
                                )
        for row in rows:

            email = row.email

            try:
                success = db(ttable.user_id == row.id).delete()
            except Exception:
                success = False
            if not success:
                current.log.warning("Could not delete temp data for user %s" % email)
                continue

            try:
                success = row.delete_record()
            except Exception:
                success = False
            if not success:
                current.log.warning("Could not delete unverified user %s" % email)

            current.log.info("Deleted unverified user account %s" % email)

    # -------------------------------------------------------------------------
    @staticmethod
    def cleanup_public_registry():
        """
            Automatically mark test stations as obsolete (and thus remove them
            from the public registry) when they have failed to submit daily
            activity reports for more than 4 four weeks; + notify OrgAdmins
            about deactivation

            Returns:
                error message, or None if successful
        """

        db = current.db
        s3db = current.s3db

        ftable = s3db.org_facility
        atable = s3db.org_site_approval
        otable = s3db.org_organisation
        gtable = s3db.org_group
        mtable = s3db.org_group_membership
        rtable = s3db.disease_testing_report
        ltable = s3db.gis_location

        today = datetime.datetime.utcnow().date()
        four_weeks_ago = today - datetime.timedelta(days=28)

        from .config import TESTSTATIONS
        join = [atable.on((atable.site_id == ftable.site_id) & \
                          (atable.public == "Y") & \
                          (atable.deleted == False)),
                otable.on((otable.id == ftable.organisation_id)),
                gtable.on((mtable.organisation_id == otable.id) & \
                          (mtable.deleted == False) & \
                          (gtable.id == mtable.group_id) & \
                          (gtable.name == TESTSTATIONS)),
                ]
        left = [rtable.on((rtable.site_id == ftable.site_id) & \
                          (rtable.date >= four_weeks_ago) & \
                          (rtable.deleted == False)),
                ltable.on((ltable.id == ftable.location_id)),
                ]
        query = (rtable.id == None) & \
                (ftable.created_on < four_weeks_ago) & \
                (ftable.obsolete == False) & \
                (ftable.deleted == False)

        rows = db(query).select(ftable.id,
                                ftable.name,
                                otable.id,
                                otable.pe_id,
                                otable.name,
                                ltable.L1,
                                #ltable.L2,
                                ltable.L3,
                                ltable.L4,
                                ltable.addr_street,
                                ltable.addr_postcode,
                                join = join,
                                left = left,
                                )
        if not rows:
            return None
        else:
            current.log.info("%s test facilities found obsolete" % len(rows))

        from .helpers import get_role_emails
        from .notifications import CMSNotifications
        from core import s3_str

        errors = []
        update_super = s3db.update_super
        for row in rows:

            organisation = row.org_organisation
            facility = row.org_facility
            location = row.gis_location

            # Mark facility as obsolete
            facility.update_record(obsolete = True)
            update_super(ftable, facility)

            # Prepare data for notification template
            place = location.L4 if location.L4 else location.L3
            if location.L1:
                place = "%s (%s)" % (place, location.L1)
            reprstr = lambda v: s3_str(v) if v else "-"

            data = {"organisation": reprstr(organisation.name),
                    "facility": reprstr(facility.name),
                    "address": reprstr(location.addr_street),
                    "postcode": reprstr(location.addr_postcode),
                    "place": place,
                    }

            # Notify all OrgAdmins
            contacts = get_role_emails("ORG_ADMIN", pe_id=organisation.pe_id)
            if contacts:
                error = CMSNotifications.send(contacts,
                                              "FacilityObsolete",
                                              data,
                                              module = "org",
                                              resource = "facility",
                                              )
            else:
                error = "No contacts found"

            if error:
                msg = "Cound not notify %s (%s)" % (organisation.name, error)
                current.log.error(msg)
                errors.append(msg)

        return "\n".join(errors) if errors else None

    # -------------------------------------------------------------------------
    @staticmethod
    def expire_commissions():
        """
            Check for expired test station commissions
        """

        from .config import TESTSTATIONS
        from .models.org import TestProvider

        db = current.db
        s3db = current.s3db

        today = datetime.datetime.utcnow().date()

        # Look up affected organisations in the TESTSTATIONS group
        ctable = s3db.org_commission
        gtable = s3db.org_group
        mtable = s3db.org_group_membership

        join = gtable.on((mtable.organisation_id == ctable.organisation_id) & \
                         (gtable.id == mtable.group_id) & \
                         (gtable.name == TESTSTATIONS) & \
                         (mtable.deleted == False)
                         )

        query = (ctable.status in ("CURRENT", "SUSPENDED")) & \
                (ctable.end_date != None) & \
                (ctable.end_date < today) & \
                (ctable.deleted == False)
        rows = db(query).select(ctable.id,
                                ctable.status,
                                ctable.organisation_id,
                                join = join,
                                )
        for row in rows:
            TestProvider(row.organisation_id).expire_commission()

    # -------------------------------------------------------------------------
    @staticmethod
    def check_verification_status():
        """
            Check verification status of all test stations for which
            organisation type requirements have changed
        """

        from .config import TESTSTATIONS
        from .models.org import TestProvider

        db = current.db
        s3db = current.s3db

        # New organisation type requirements will be enforced for
        # existing organisations after a grace period of 3 days
        delay = 3 # days
        now = datetime.datetime.utcnow()
        earliest = now - datetime.timedelta(days=delay + 1)
        latest   = now - datetime.timedelta(days=delay)

        ttable = s3db.org_organisation_type
        rtable = s3db.org_requirements

        join = rtable.on((rtable.organisation_type_id == ttable.id) & \
                         (rtable.modified_on >= earliest) & \
                         (rtable.modified_on < latest) & \
                         (rtable.deleted == False))
        query = (ttable.deleted == False)
        types = db(query)._select(ttable.id, join=join)

        # Look up affected organisations in the TESTSTATIONS group
        otable = s3db.org_organisation
        gtable = s3db.org_group
        mtable = s3db.org_group_membership
        ltable = s3db.org_organisation_organisation_type

        join = [gtable.on((mtable.organisation_id == otable.id) & \
                          (gtable.id == mtable.group_id) & \
                          (gtable.name == TESTSTATIONS) & \
                          (mtable.deleted == False)
                          ),
                ltable.on((ltable.organisation_id == otable.id) & \
                          (ltable.organisation_type_id.belongs(types)) & \
                          (ltable.deleted == False)
                          ),
                ]
        query = (otable.deleted == False)
        rows = db(query).select(otable.id, join=join)
        organisation_ids = {row.id for row in rows}

        # Update verification status for these organisations
        for organisation_id in organisation_ids:
            TestProvider(organisation_id).update_verification()

# END =========================================================================
