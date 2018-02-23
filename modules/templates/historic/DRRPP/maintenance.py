# -*- coding: utf-8 -*-

from datetime import timedelta

from gluon import *
#from s3 import *

# =============================================================================
class Daily():
    """ Daily Maintenance Tasks """

    def __call__(self):

        db = current.db
        request = current.request
        settings = current.deployment_settings

        appname = request.application
        base_url = settings.get_base_public_url()
        now = request.utcnow
        reply_to = settings.get_mail_sender()
        send_email = current.msg.send_email

        # Check Projects
        table = current.s3db.project_project

        # Email creator of the project when:
        # * the end date of the project is passed
        subject = "DRR Project Portal: '%s' has passed it's end date"
        message = "Please login to the DRR Project Portal & update the project to either show that it has been extended or that it is now completed:\n%s/%s/project/project/" \
            % (base_url, appname)

        query = (table.end_date == now.date())
        rows = db(query).select(table.id,
                                table.name,
                                table.created_by)
        for row in rows:
            send_email(to = row.created_by,
                       subject = subject % row.name,
                       message = message + row.id,
                       reply_to = reply_to
                       )

        # Email creator of the project when:
        # * a record hasn�t been updated in over 6 months when the status is not completed
        subject = "DRR Project Portal: '%s' hasn't been updated for 6 months"
        message = "Please login to the DRR Project Portal & update it. e.g. To show that it has been completed:\n%s/%s/project/project/" \
            % (base_url, appname)

        stale = now - timedelta(weeks = 26)
        query = (table.status != 2) & \
                (table.modified_on.year() == now.year) & \
                (table.modified_on.month() == now.month) & \
                (table.modified_on.day() == now.day)
        rows = db(query).select(table.id,
                                table.name,
                                table.created_by)
        for row in rows:
            send_email(to = row.created_by,
                       subject = subject % row.name,
                       message = message + row.id,
                       reply_to = reply_to
                       )

        # Do we want to provide a summary result for the Scheduler logs?
        result = ""

        return result

# END =========================================================================
