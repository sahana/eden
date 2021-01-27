# -*- coding: utf-8 -*-

import datetime
import os
import time

from gluon import current
from gluon.settings import global_settings

# =============================================================================
class Daily():
    """ Daily Maintenance Tasks """

    def __call__(self):

        db = current.db
        s3db = current.s3db
        request = current.request

        current.log.info("Daily Maintenance RLPPTM")

        now = datetime.datetime.utcnow()
        week_past = now - datetime.timedelta(weeks=1)

        # Cleanup Scheduler logs
        table = s3db.scheduler_run
        db(table.start_time < week_past).delete()

        # Cleanup Sync logs
        table = s3db.sync_log
        db(table.timestmp < week_past).delete()

        # Cleanup Sessions
        osjoin = os.path.join
        osstat = os.stat
        osremove = os.remove
        folder = osjoin(global_settings.applications_parent,
                        request.folder,
                        "sessions",
                        )

        # Convert to UNIX time
        week_past_u = time.mktime(week_past.timetuple())
        for file in os.listdir(folder):
            filepath = osjoin(folder, file)
            status = osstat(filepath)
            if status.st_mtime < week_past_u:
                try:
                    osremove(filepath)
                except:
                    pass

        # Cleanup unverified accounts
        self.cleanup_unverified_accounts()

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
            except:
                success = False
            if not success:
                current.log.warning("Could not delete temp data for user %s" % email)
                continue

            try:
                success = row.delete_record()
            except:
                success = False
            if not success:
                current.log.warning("Could not delete unverified user %s" % email)

            current.log.info("Deleted unverified user account %s" % email)

# END =========================================================================
