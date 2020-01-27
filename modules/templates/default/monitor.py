# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Monitoring

    Template-specific Monitoring Tasks are defined here.

    @copyright: 2014-2020 (c) Sahana Software Foundation
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
import json
import platform
import subprocess
import sys

from gluon import current

try:
    import requests
except ImportError:
    REQUESTS = None
else:
    REQUESTS = True

# =============================================================================
class S3Monitor(object):
    """
       Monitoring Check Scripts
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def diskspace(task_id, run_id):
        """
            Test the free diskspace
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    @staticmethod
    def eden(task_id, run_id):
        """
            Test that we can retrieve the public_url, which checks:
            - DNS must resolve to correct IP
            - Server must be up
            - Firewall cannot be blocking
            - Web server is running
            - UWSGI is running
            - Database is running
            - Eden can connect to Database
        """

        if REQUESTS is None:
            return {"result": "Critical: Requests library not installed",
                    "status": 3,
                    }

        db = current.db
        s3db = current.s3db

        # Read the Task Options
        ttable = s3db.setup_monitor_task
        task = db(ttable.id == task_id).select(ttable.deployment_id,
                                               ttable.options,
                                               limitby = (0, 1)
                                               ).first()
        options = task.options or {}
        options_get = options.get

        appname = options_get("appname", "eden")
        public_url = options_get("public_url")
        timeout = options_get("timeout", 60) # 60s (default is no timeout!)

        if not public_url:
            itable = s3db.setup_instance
            query = (itable.deployment_id == task.deployment_id) & \
                    (itable.type == 1)
            instance = db(query).select(itable.url,
                                        limitby = (0, 1)
                                        ).first()
            public_url = instance.url

        url = "%(public_url)s/%(appname)s/default/public_url" % {"appname": appname,
                                                                 "public_url": public_url,
                                                                 }

        try:
            r = requests.get(url, timeout = timeout) # verify=True
        except requests.exceptions.SSLError:
            import traceback
            tb_parts = sys.exc_info()
            tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                         tb_parts[1],
                                                         tb_parts[2]))
            return {"result": "Critical: SSL Error", # e.g. expired
                    "status": 3,
                    "traceback": tb_text,
                    }
        except requests.exceptions.Timeout:
            import traceback
            tb_parts = sys.exc_info()
            tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                         tb_parts[1],
                                                         tb_parts[2]))
            return {"result": "Critical: Timeout Error",
                    "status": 3,
                    "traceback": tb_text,
                    }
        except requests.exceptions.TooManyRedirects:
            import traceback
            tb_parts = sys.exc_info()
            tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                         tb_parts[1],
                                                         tb_parts[2]))
            return {"result": "Critical: TooManyRedirects Error",
                    "status": 3,
                    "traceback": tb_text,
                    }

        if r.status_code != 200:
            return {"result": "Critical: HTTP Error. Status = %s" % r.status_code,
                    "status": 3,
                    }

        if r.text != public_url:
            return {"result": "Critical: Page returned '%s' instead of  '%s'" % \
                                (r.text, public_url),
                    "status": 3,
                    }

        return {"latency": r.elapsed,
                "result": "OK",
                "status": 1,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def email_round_trip(task_id, run_id):
        """
            Check that a Mailbox is being Polled & Parsed OK and can send replies
        """

        # Read the Task Options
        ttable = current.s3db.setup_monitor_task
        task = current.db(ttable.id == task_id).select(ttable.options,
                                                       limitby = (0, 1)
                                                       ).first()
        options = task.options or {}
        options_get = options.get

        to = options_get("to", None)
        if not to:
            return {"result": "Critical: No recipient address specified",
                    "status": 3,
                    }

        subject = options_get("subject", "")
        message = options_get("message", "")
        reply_to = options_get("reply_to")
        if not reply_to:
            # Use the outbound email address
            reply_to = current.deployment_settings.get_mail_sender()
            if not reply_to:
                return {"result": "Critical: No reply_to specified",
                        "status": 3,
                        }

        # Append the run_id for the remote parser to identify as a monitoring message & return to us to be able to match the run
        message = "%s\n%s" % (message, ":run_id:%s:" % run_id)

        # Append the reply_to address for the remote parser
        message = "%s\n%s" % (message, ":reply_to:%s:" % reply_to)

        # Send the Email
        result = current.msg.send_email(to,
                                        subject,
                                        message,
                                        reply_to = reply_to)

        if result:
            # Schedule a task to see if the reply has arrived after 1 hour
            start_time = datetime.datetime.utcnow() + \
                         datetime.timedelta(hours = 1)
            current.s3task.schedule_task("setup_monitor_check_email_reply",
                                         args = [run_id],
                                         start_time = start_time,
                                         timeout = 300, # seconds
                                         repeats = 1    # one-time
                                         )
            return {"result": "Warning: No reply received yet",
                    "status": 2,
                    }

        return {"result": "Critical: Unable to send Email",
                "status": 3,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def http(task_id, run_id):
        """
            Test that HTTP is accessible
        """

        if REQUESTS is None:
            return {"result": "Critical: Requests library not installed",
                    "status": 3,
                    }

        raise NotImplementedError

    # -------------------------------------------------------------------------
    @staticmethod
    def https(task_id, run_id):
        """
            Test that HTTP is accessible
        """

        if REQUESTS is None:
            return {"result": "Critical: Requests library not installed",
                    "status": 3,
                    }

        raise NotImplementedError

    # -------------------------------------------------------------------------
    @staticmethod
    def load_average(task_id, run_id):
        """
            Test the Load Average
        """

        raise NotImplementedError

    # -------------------------------------------------------------------------
    @staticmethod
    def ping(task_id, run_id):
        """
            ICMP Ping a server
            - NB AWS instances don't respond to ICMP Ping by default, but this can be enabled in the Firewall
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
            # @ToDo: Replace with socket?
            # - we want to see the latency
            if platform.system().lower == "windows":
                _format = "n"
            else:
                _format = "c"
            output = subprocess.check_output("ping -{} 1 {}".format(_format,
                                                                    host_ip),
                                             shell = True)
        except Exception:
            import traceback
            tb_parts = sys.exc_info()
            tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                         tb_parts[1],
                                                         tb_parts[2]))
            return {"result": "Critical: Ping failed",
                    "status": 3,
                    "traceback": tb_text,
                    }

        return {"result": "OK",
                "status": 1,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def tcp(task_id, run_id):
        """
            Test that a TCP port is accessible
        """

        raise NotImplementedError

# END =========================================================================
