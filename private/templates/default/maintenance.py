# -*- coding: utf-8 -*-

import datetime

from gluon import current

# =============================================================================
class Daily():
    """ Daily Maintenance Tasks """

    def __call__(self):

        db = current.db
        s3db = current.s3db

        now = current.request.utcnow
        month_past = now - datetime.timedelta(weeks=4)

        # Cleanup Scheduler logs
        table = s3db.scheduler_run
        db(table.start_time < month_past).delete()

        # Cleanup Sync logs
        table = s3db.sync_log
        db(table.timestmp < month_past).delete()

# END =========================================================================
