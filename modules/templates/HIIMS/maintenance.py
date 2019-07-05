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
        month_past = now - datetime.timedelta(weeks=4)

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

# END =========================================================================
