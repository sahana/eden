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

        now = request.utcnow
        month_past = now - datetime.timedelta(weeks = 4)

        # Cleanup Scheduler logs
        table = s3db.scheduler_run
        db(table.start_time < month_past).delete()

        # Cleanup Sync logs
        table = s3db.sync_log
        db(table.timestmp < month_past).delete()

        # Cleanup Sessions
        osjoin = os.path.join
        osstat = os.stat
        osremove = os.remove
        folder = osjoin(global_settings.applications_parent,
                        request.folder,
                        "sessions")
        # Convert to UNIX time
        month_past_u = time.mktime(month_past.timetuple())
        for file in os.listdir(folder):
            filepath = osjoin(folder, file)
            status = osstat(filepath)
            if status.st_mtime < month_past_u:
                try:
                    osremove(filepath)
                except:
                    pass

        # Cleanup Uploaded Import Spreadsheets
        week_past = now - datetime.timedelta(weeks = 1)

        from s3.s3import import S3Importer
        S3Importer.define_upload_table()

        table = s3db.s3_import_upload
        db(table.created_on < week_past).delete()

        return

        # Check for Expiring Stock
        # @ToDo: Complete
        ninety_days = now + datetime.timedelta(days = 90)
        table = s3db.inv_inv_item
        rows = db(table.expiry_date < ninety_days).select(table.id,
                                                          table.site_id,
                                                          table.item_id,
                                                          table.expiry_date,
                                                          table.quantity,
                                                          table.bin,
                                                          )
        if len(rows):
            # Bulk Represent Sites
            # Bulk Represent Items
            for row in rows:
                # Dashboard Alerts
                # Which User(s) should we Alert?
                # Check if we already have an Alert
                ntable = s3db.auth_user_notification
                record_id = row.id
                # Add Alert
                ntable.insert(user_id = user_id,
                              # @ToDo: i18n
                              name = "%(quantity)s %(item)s in %(bin)s from %(site)s will expire on %(date)s",
                              url = URL(c="inv", f="inv_item", args=record_id),
                              type = "expiry",
                              tablename = "inv_inv_item",
                              record_id = record_id,
                              )
                # Send i18n emails

# END =========================================================================
