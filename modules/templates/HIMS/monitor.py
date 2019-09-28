# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Monitoring

    Template-specific Monitoring Tasks are defined here.

    @copyright: 2014-2019 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3Monitor",)

import datetime
import platform
import subprocess

from gluon import current
#from gluon.tools import fetch

# =============================================================================
class S3Monitor(object):
    """
       Monitoring Check Scripts
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def ping(task_id, run_id):
        """
            Ping a server
        """

        s3db = current.s3db

        # Read the IP to Ping
        ttable = s3db.setup_monitor_task
        stable = s3db.setup_server
        query = (ttable.id == task_id) & \
                (ttable.server_id == stable.id)
        row = current.db(query).select(stable.host_ip,
                                       limitby = (0, 1)
                                       ).first()

        host_ip = row.host_ip

        try:
            output = subprocess.check_output("ping -{} 1 {}".format("n" if platform.system().lower == "windows" else "c", host_ip), shell=True)
        except Exception as e:
            # Critical: Ping failed
            return 3
        else:
            # OK
            return 1

    # -------------------------------------------------------------------------
    #@staticmethod
    #def http(task_id, run_id):
    #    """
    #        Test that HTTP is accessible
    #    """

    # -------------------------------------------------------------------------
    #@staticmethod
    #def https(task_id, run_id):
    #    """
    #        Test that HTTPS is accessible
    #        @ToDo: Check that SSL certificate hasn't expired
    #    """

    # -------------------------------------------------------------------------
    @staticmethod
    def email_round_trip(task_id, run_id):
        """
            Check that a Mailbox is being Polled & Parsed OK and can send replies
        """

        # Read the Task Options
        otable = current.s3db.setup_monitor_task_option
        query = (otable.task_id == task_id) & \
                (otable.deleted == False)
        rows = current.db(query).select(otable.tag,
                                        otable.value,
                                        )
        options = dict((row.tag, row.value) for row in rows)

        to = options.get("to", None)
        if not to:
            return False

        subject = options.get("subject", "")
        message = options.get("message", "")
        reply_to = options.get("reply_to")
        if not reply_to:
            # Use the outbound email address
            reply_to = current.deployment_settings.get_mail_sender()
            if not reply_to:
                return False

        # Append the run_id for the remote parser to identify as a monitoring message & return to us to be able to match the run
        message = "%s\n%s" % (message, ":run_id:%s:" % run_id)

        # Append the reply_to address for the remote parser
        message = "%s\n%s" % (message, ":reply_to:%s:" % reply_to)

        # Send the Email
        result = current.msg.send_email(to,
                                        subject,
                                        message,
                                        reply_to=reply_to)

        if result:
            # Schedule a task to see if the reply has arrived after 1 hour
            start_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            current.s3task.schedule_task("setup_monitor_check_email_reply",
                                         args = [run_id],
                                         start_time = start_time,
                                         timeout = 300, # seconds
                                         repeats = 1    # one-time
                                         )
            # Warning: No reply received yet
            return 2
        else:
            # Critical: Unable to send Email
            return 3

# END =========================================================================
