# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Monitoring

    Template-specific Monitoring Tasks are defined here.

    @copyright: 2014-2021 (c) Sahana Software Foundation
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
import os
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

INSTANCE_TYPES = {"prod": 1,
                  "setup": 2,
                  "test": 3,
                  "demo": 4,
                  }

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

        db = current.db
        s3db = current.s3db

        # Read the Task Options
        ttable = s3db.setup_monitor_task
        task = db(ttable.id == task_id).select(ttable.options,
                                               ttable.server_id,
                                               limitby = (0, 1)
                                               ).first()
        options = task.options or {}
        options_get = options.get

        partition = options_get("partition", "/") # Root Partition by default
        space_min = options_get("space_min", 1000000000) # 1 Gb

        stable = s3db.setup_server
        server = db(stable.id == task.server_id).select(stable.host_ip,
                                                        stable.remote_user,
                                                        stable.private_key,
                                                        limitby = (0, 1)
                                                        ).first()

        if server.host_ip == "127.0.0.1":
            result = os.statvfs(partition)
            space = result.f_bavail * result.f_frsize
            percent = float(result.f_bavail) / float(result.f_blocks) * 100
            if space < space_min:
                return {"result": "Warning: %s free (%d%%)" % \
                                    (_bytes_to_size_string(space), percent),
                        "status": 2,
                        }

            return {"result": "OK. %s free (%d%%)" % \
                                (_bytes_to_size_string(space), percent),
                    "status": 1,
                    }

        ssh = _ssh(server)
        if isinstance(ssh, dict):
            # We failed to login
            return ssh

        command = "import os;result=os.statvfs('%s');print(result.f_bavail);print(result.f_frsize);print(result.f_blocks)" % partition
        stdin, stdout, stderr = ssh.exec_command('python -c "%s"' % command)
        outlines = stdout.readlines()
        ssh.close()

        f_bavail = int(outlines[0])
        f_frsize = int(outlines[1])
        f_blocks = int(outlines[2])

        space = f_bavail * f_frsize
        percent = float(f_bavail) / float(f_blocks) * 100
        if space < space_min:
            return {"result": "Warning: %s free (%d%%)" % \
                                (_bytes_to_size_string(space), percent),
                    "status": 2,
                    }

        return {"result": "OK. %s free (%d%%)" % \
                            (_bytes_to_size_string(space), percent),
                "status": 1,
                }

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
        task = db(ttable.id == task_id).select(ttable.options,
                                               ttable.deployment_id,
                                               ttable.server_id,
                                               limitby = (0, 1)
                                               ).first()
        options = task.options or {}
        options_get = options.get

        appname = options_get("appname", "eden")
        public_url = options_get("public_url")
        timeout = options_get("timeout", 60) # 60s (default is no timeout!)

        if not public_url:
            deployment_id = task.deployment_id
            if deployment_id:
                # Read from the instance
                itable = s3db.setup_instance
                query = (itable.deployment_id == deployment_id) & \
                        (itable.type == 1)
                instance = db(query).select(itable.url,
                                            limitby = (0, 1)
                                            ).first()
                if instance:
                    public_url = instance.url
            if not public_url:
                # Use the server name
                stable = s3db.setup_server
                server = db(stable.id == task.server_id).select(stable.name,
                                                                limitby = (0, 1)
                                                                ).first()
                public_url = "https://%s" % server.name

        url = "%(public_url)s/%(appname)s/default/public_url" % {"appname": appname,
                                                                 "public_url": public_url,
                                                                 }

        try:
            r = requests.get(url, timeout = timeout) # verify=True
        except requests.exceptions.SSLError:
            # e.g. Expired Certificate
            import traceback
            tb_parts = sys.exc_info()
            tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                         tb_parts[1],
                                                         tb_parts[2]))
            return {"result": "Critical: SSL Error\n\n%s" % tb_text,
                    "status": 3,
                    }
        except requests.exceptions.Timeout:
            import traceback
            tb_parts = sys.exc_info()
            tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                         tb_parts[1],
                                                         tb_parts[2]))
            return {"result": "Critical: Timeout Error\n\n%s" % tb_text,
                    "status": 3,
                    }
        except requests.exceptions.TooManyRedirects:
            import traceback
            tb_parts = sys.exc_info()
            tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                         tb_parts[1],
                                                         tb_parts[2]))
            return {"result": "Critical: TooManyRedirects Error\n\n%s" % tb_text,
                    "status": 3,
                    }
        except requests.exceptions.ConnectionError:
            # e.g. DNS Error
            import traceback
            tb_parts = sys.exc_info()
            tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                         tb_parts[1],
                                                         tb_parts[2]))
            return {"result": "Critical: Connection Error\n\n%s" % tb_text,
                    "status": 3,
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

        latency = int(r.elapsed.microseconds / 1000)
        latency_max = options_get("latency_max", 2000) # 2 seconds
        if latency > latency_max:
            return {"result": "Warning: Latency of %s exceeded threshold of %s." % \
                                (latency, latency_max),
                    "status": 2,
                    }

        return {"result": "OK. Latency: %s" % latency,
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
            # Schedule a task to see if the reply has arrived
            wait = options_get("wait", 60) # Default = 60 minutes
            start_time = datetime.datetime.utcnow() + \
                         datetime.timedelta(minutes = wait)
            current.s3task.schedule_task("setup_monitor_check_email_reply",
                                         args = [run_id],
                                         start_time = start_time,
                                         timeout = 300, # seconds
                                         repeats = 1    # one-time
                                         )
            return {"result": "OK so far: Waiting for Reply",
                    "status": 1,
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

        db = current.db
        s3db = current.s3db

        # Read the Task Options
        ttable = s3db.setup_monitor_task
        task = db(ttable.id == task_id).select(ttable.options,
                                               ttable.server_id,
                                               limitby = (0, 1)
                                               ).first()
        options = task.options or {}
        options_get = options.get

        which = options_get("which", 2) # 15 min average
        load_max = options_get("load_max", 2)

        stable = s3db.setup_server
        server = db(stable.id == task.server_id).select(stable.host_ip,
                                                        stable.remote_user,
                                                        stable.private_key,
                                                        limitby = (0, 1)
                                                        ).first()

        if server.host_ip == "127.0.0.1":
            loadavg = os.getloadavg()
            if loadavg[which] > load_max:
                return {"result": "Warning: load average: %0.2f, %0.2f, %0.2f" % \
                                (loadavg[0], loadavg[1], loadavg[2]),
                        "status": 2,
                        }

            return {"result": "OK. load average: %0.2f, %0.2f, %0.2f" % \
                                (loadavg[0], loadavg[1], loadavg[2]),
                    "status": 1,
                    }

        ssh = _ssh(server)
        if isinstance(ssh, dict):
            # We failed to login
            return ssh

        command = "import os;loadavg=os.getloadavg();print(loadavg[0]);print(loadavg[1]);print(loadavg[2])"
        stdin, stdout, stderr = ssh.exec_command('python -c "%s"' % command)
        outlines = stdout.readlines()
        ssh.close()

        loadavg = {0: float(outlines[0]),
                   1: float(outlines[1]),
                   2: float(outlines[2]),
                   }

        if loadavg[which] > load_max:
            return {"result": "Warning: load average: %0.2f, %0.2f, %0.2f" % \
                            (loadavg[0], loadavg[1], loadavg[2]),
                    "status": 2,
                    }

        return {"result": "OK. load average: %0.2f, %0.2f, %0.2f" % \
                            (loadavg[0], loadavg[1], loadavg[2]),
                "status": 1,
                }

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
            return {"result": "Critical: Ping failed\n\n%s" % tb_text,
                    "status": 3,
                    }

        return {"result": "OK",
                "status": 1,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def scheduler(task_id, run_id):
        """
            Test whether the scheduler is running
        """

        db = current.db
        s3db = current.s3db

        # Read the Task Options
        ttable = s3db.setup_monitor_task
        task = db(ttable.id == task_id).select(ttable.options,
                                               ttable.server_id,
                                               limitby = (0, 1)
                                               ).first()
        options = task.options or {}
        options_get = options.get

        stable = s3db.setup_server
        server = db(stable.id == task.server_id).select(stable.host_ip,
                                                        stable.remote_user,
                                                        stable.private_key,
                                                        limitby = (0, 1)
                                                        ).first()

        earliest = current.request.utcnow - datetime.timedelta(seconds = 900) # 15 minutes

        if server.host_ip == "127.0.0.1":
            # This shouldn't make much sense as a check, since this won't run if the scheduler has died
            # - however in practise, it can actually provide useful warning!

            wtable = s3db.scheduler_worker
            worker = db(wtable.status == "ACTIVE").select(wtable.last_heartbeat,
                                                          limitby = (0, 1)
                                                          ).first()

            error = None
            if worker is None:
                error = "Warning: Scheduler not ACTIVE"

            elif worker.last_heartbeat < earliest:
                error = "Warning: Scheduler stalled since %s" % worker.last_heartbeat.strftime("%H:%M %a %d %b")

            if error:
                appname = options_get("appname", "eden")
                instance = options_get("instance", "prod")

                # Restart uwsgi
                error += "\n\nAttempting to restart:\n"
                # Note this needs to actually run after last task as it kills us ;)
                # NB Need to ensure the web2py user has permission to run sudo
                command = 'echo "sudo service uwsgi-%s restart" | at now + 1 minutes' % instance
                output = subprocess.check_output(command,
                                                 stderr = subprocess.STDOUT,
                                                 shell = True)
                error += output.decode("utf-8")
                # Restart Monitoring Scripts
                command = 'echo "cd /home/%s;python web2py.py --no-banner -S %s -M -R applications/%s/static/scripts/tools/restart_monitor_tasks.py" | at now + 5 minutes' % \
                    (instance, appname, appname)
                output = subprocess.check_output(command,
                                                 stderr = subprocess.STDOUT,
                                                 shell = True)
                error += output.decode("utf-8")
                return {"result": error,
                        "status": 3,
                        }

            return {"result": "OK",
                    "status": 1,
                    }


        ssh = _ssh(server)
        if isinstance(ssh, dict):
            # We failed to login
            return ssh

        appname = options_get("appname", "eden")
        instance = options_get("instance", "prod")

        command = "cd /home/%s;python web2py.py --no-banner -S %s -M -R applications/%s/static/scripts/tools/check_scheduler.py -A '%s'" % \
            (instance, appname, appname, earliest)
        stdin, stdout, stderr = ssh.exec_command(command)
        outlines = stdout.readlines()

        if outlines:
            error = outlines[0]
            # Restart uwsgi
            error += "\n\nAttempting to restart:\n"
            command = "sudo service uwsgi-%s restart" % instance
            stdin, stdout, stderr = ssh.exec_command(command)
            outlines = stdout.readlines()
            if outlines:
                error += "\n".join(outlines)
            else:
                # Doesn't usually give any output
                error += "OK"
            ssh.close()
            return {"result": error,
                    "status": 3,
                    }
        ssh.close()

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

    # -------------------------------------------------------------------------
    @staticmethod
    def tickets(task_id, run_id):
        """
            Test whether there are new tickets today
            - designed to be run daily (period 86400s)
        """

        db = current.db
        s3db = current.s3db

        # Read the Task Options
        ttable = s3db.setup_monitor_task
        task = db(ttable.id == task_id).select(ttable.options,
                                               #ttable.period,
                                               ttable.server_id,
                                               limitby = (0, 1)
                                               ).first()
        options = task.options or {}
        options_get = options.get

        stable = s3db.setup_server
        server = db(stable.id == task.server_id).select(stable.host_ip,
                                                        stable.remote_user,
                                                        stable.private_key,
                                                        stable.deployment_id,
                                                        limitby = (0, 1)
                                                        ).first()

        request = current.request
        today = request.utcnow.date().isoformat()

        if server.host_ip == "127.0.0.1":
            appname = request.application
            public_url = current.deployment_settings.get_base_public_url()
            tickets = os.listdir("applications/%s/errors" % appname)
            new = []
            for ticket in tickets:
                #if os.stat(ticket).st_mtime < now - task.period:
                if today in ticket:
                    url = "%s/%s/admin/ticket/%s/%s" % (public_url,
                                                        appname,
                                                        appname,
                                                        ticket,
                                                        )
                    new.append(url)

            if new:
                return {"result": "Warning: New tickets:\n\n%s" % "\n".join(new),
                        "status": 2,
                        }

            return {"result": "OK",
                    "status": 1,
                    }

        ssh = _ssh(server)
        if isinstance(ssh, dict):
            # We failed to login
            return ssh

        appname = options_get("appname", "eden")
        instance = options_get("instance", "prod")

        command = "import os;ts=os.listdir('/home/%s/applications/%s/errors');for t in ts:print(t) if '%s' in t" % \
            (instance, appname, today)
        stdin, stdout, stderr = ssh.exec_command('python -c "%s"' % command)
        outlines = stdout.readlines()
        ssh.close()

        if outlines:
            itable = s3db.setup_instance
            query = (itable.deployment_id == server.deployment_id) & \
                    (itable.type == INSTANCE_TYPES[instance])
            instance = db(query).select(itable.url,
                                        limitby = (0, 1)
                                        ).first()
            public_url = instance.url
            new = []
            for ticket in outlines:
                 url = "%s/%s/admin/ticket/%s/%s" % (public_url,
                                                     appname,
                                                     appname,
                                                     ticket,
                                                     )
                 new.append(url)
            return {"result": "Warning: New tickets:\n\n%s" % "\n".join(new),
                    "status": 2,
                    }

        return {"result": "OK",
                "status": 1,
                }

# =============================================================================
def _bytes_to_size_string(b):
#def _bytes_to_size_string(b: int) -> str:
    """
        Convert a number in bytes to a sensible unit.

        From https://github.com/jamesoff/simplemonitor/blob/develop/simplemonitor/Monitors/host.py#L35
    """

    kb = 1024
    mb = kb * 1024
    gb = mb * 1024
    tb = gb * 1024

    if b > tb:
        return "%0.2fTiB" % (b / float(tb))
    elif b > gb:
        return "%0.2fGiB" % (b / float(gb))
    elif b > mb:
        return "%0.2fMiB" % (b / float(mb))
    elif b > kb:
        return "%0.2fKiB" % (b / float(kb))
    else:
        return str(b)

# =============================================================================
def _ssh(server):
    """
        SSH into a Server
    """

    remote_user = server.remote_user
    private_key = server.private_key
    if not private_key or not remote_user:
        if remote_user:
            return {"result": "Critical. Missing Private Key",
                    "status": 3,
                    }
        elif private_key:
            return {"result": "Critical. Missing Remote User",
                    "status": 3,
                    }
        else:
            return {"result": "Critical. Missing Remote User & Private Key",
                    "status": 3,
                    }

    # SSH in & run check
    try:
        import paramiko
    except ImportError:
        return {"result": "Critical. Paramiko required.",
                "status": 3,
                }

    keyfile = open(os.path.join(current.request.folder, "uploads", private_key), "r")
    mykey = paramiko.RSAKey.from_private_key(keyfile)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname = server.host_ip,
                    username = remote_user,
                    pkey = mykey)
    except paramiko.ssh_exception.AuthenticationException:
        import traceback
        tb_parts = sys.exc_info()
        tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                     tb_parts[1],
                                                     tb_parts[2]))
        return {"result": "Critical. Authentication Error\n\n%s" % tb_text,
                "status": 3,
                }
    except paramiko.ssh_exception.SSHException:
        import traceback
        tb_parts = sys.exc_info()
        tb_text = "".join(traceback.format_exception(tb_parts[0],
                                                     tb_parts[1],
                                                     tb_parts[2]))
        return {"result": "Critical. SSH Error\n\n%s" % tb_text,
                "status": 3,
                }

    return ssh

# END =========================================================================
