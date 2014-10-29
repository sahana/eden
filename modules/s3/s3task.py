# -*- coding: utf-8 -*-

""" Asynchronous Task Execution
    - falls back to Synchronous if no workers are alive

    Worker nodes won't run on Win32 yet.

    To run a worker node: python web2py.py -K eden
    or use UWSGI's 'Mule'

    NB
        Need WEB2PY_PATH environment variable to be defined (e.g. /etc/profile)
        Tasks need to be defined outside conditional model loads (e.g. models/tasks.py)
        Avoid passing state into the async call as state may change before the message is executed (race condition)

    Old screencast: http://www.vimeo.com/27478796

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2011-14 (c) Sahana Software Foundation
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

__all__ = ("S3Task",)

import datetime

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current, HTTP, IS_EMPTY_OR
from gluon.storage import Storage

from s3utils import S3DateTime, RepeatedTimer
from s3validators import IS_TIME_INTERVAL_WIDGET, IS_UTC_DATETIME
from s3widgets import S3DateTimeWidget, S3TimeIntervalWidget

# -----------------------------------------------------------------------------
class S3Task(object):
    """ Asynchronous Task Execution """

    TASK_TABLENAME = "scheduler_task"

    # -------------------------------------------------------------------------
    def __init__(self):

        migrate = current.deployment_settings.get_base_migrate()
        tasks = current.response.s3.tasks

        # Instantiate Scheduler
        try:
            from gluon.scheduler import Scheduler
        except:
            # Warning should already have been given by eden_update_check.py
            self.scheduler = None
        else:
            self.scheduler = Scheduler(current.db,
                                       tasks,
                                       migrate=migrate)

    # -------------------------------------------------------------------------
    def configure_tasktable_crud(self,
                                 task=None,
                                 function=None,
                                 args=None,
                                 vars=None,
                                 period = 3600, # seconds, so 1 hour
                                 ):
        """
            Configure the task table for interactive CRUD,
            setting defaults, widgets and hiding unnecessary fields

            @param task: the task name (will use a UUID if omitted)
            @param function: the function name (won't hide if omitted)
            @param args: the function position arguments
            @param vars: the function named arguments
        """

        if args is None:
            args = []
        if vars is None:
            vars = {}

        T = current.T
        NONE = current.messages["NONE"]
        UNLIMITED = T("unlimited")

        tablename = self.TASK_TABLENAME
        table = current.db[tablename]

        table.uuid.readable = table.uuid.writable = False

        table.prevent_drift.readable = table.prevent_drift.writable = False

        table.sync_output.readable = table.sync_output.writable = False

        table.times_failed.readable = False

        field = table.start_time
        field.represent = lambda dt: \
            S3DateTime.datetime_represent(dt, utc=True)
        field.widget = S3DateTimeWidget(past=0)
        field.requires = IS_UTC_DATETIME(
                format=current.deployment_settings.get_L10n_datetime_format()
                )

        field = table.stop_time
        field.represent = lambda dt: \
            S3DateTime.datetime_represent(dt, utc=True)
        field.widget = S3DateTimeWidget(past=0)
        field.requires = IS_EMPTY_OR(
                            IS_UTC_DATETIME(
                format=current.deployment_settings.get_L10n_datetime_format()
                ))

        if not task:
            import uuid
            task = str(uuid.uuid4())
        field = table.task_name
        field.default = task
        field.readable = False
        field.writable = False

        if function:
            field = table.function_name
            field.default = function
            field.readable = False
            field.writable = False

        field = table.args
        field.default = json.dumps(args)
        field.readable = False
        field.writable = False

        field = table.repeats
        field.label = T("Repeat")
        field.comment = T("times (0 = unlimited)")
        field.default = 0
        field.represent = lambda opt: \
            opt and "%s %s" % (opt, T("times")) or \
            opt == 0 and UNLIMITED or \
            NONE

        field = table.period
        field.label = T("Run every")
        field.default = period
        field.widget = S3TimeIntervalWidget.widget
        field.requires = IS_TIME_INTERVAL_WIDGET(table.period)
        field.represent = S3TimeIntervalWidget.represent
        field.comment = None

        table.timeout.default = 600
        table.timeout.represent = lambda opt: \
            opt and "%s %s" % (opt, T("seconds")) or \
            opt == 0 and UNLIMITED or \
            NONE

        field = table.vars
        field.default = json.dumps(vars)
        field.readable = field.writable = False

        # Always use "default" controller (web2py uses current controller),
        # otherwise the anonymous worker does not pass the controller
        # permission check and gets redirected to login before it reaches
        # the task function which does the s3_impersonate
        field = table.application_name
        field.default = "%s/default" % current.request.application
        field.readable = field.writable = False
        table.group_name.readable = table.group_name.writable = False
        table.status.readable = table.status.writable = False
        table.next_run_time.readable = table.next_run_time.writable = False
        table.times_run.readable = table.times_run.writable = False
        table.assigned_worker_name.readable = \
            table.assigned_worker_name.writable = False

        current.s3db.configure(tablename,
                               list_fields = ["id",
                                              "enabled",
                                              "start_time",
                                              "repeats",
                                              "period",
                                              (T("Last run"), "last_run_time"),
                                              (T("Last status"), "status"),
                                              (T("Next run"), "next_run_time"),
                                              "stop_time"
                                              ],
                               )

        response = current.response
        if response:
            response.s3.crud_strings[tablename] = Storage(
                label_create = T("Create Job"),
                title_display = T("Scheduled Jobs"),
                title_list = T("Job Schedule"),
                title_update = T("Edit Job"),
                label_list_button = T("List Jobs"),
                msg_record_created = T("Job added"),
                msg_record_modified = T("Job updated"),
                msg_record_deleted = T("Job deleted"),
                msg_list_empty = T("No jobs configured yet"),
                msg_no_match = T("No jobs configured"))

        return

    # -------------------------------------------------------------------------
    # API Function run within the main flow of the application
    # -------------------------------------------------------------------------
    def async(self, task, args=None, vars=None, timeout=300):
        """
            Wrapper to call an asynchronous task.
            - run from the main request

            @param task: The function which should be run
                         - async if a worker is alive
            @param args: The list of unnamed args to send to the function
            @param vars: The list of named vars to send to the function
            @param timeout: The length of time available for the task to complete
                            - default 300s (5 mins)
        """
        
        if args is None:
            args = []
        if vars is None:
            vars = {}

        # Check that task is defined
        tasks = current.response.s3.tasks
        if not tasks:
            return False
        if task not in tasks:
            return False

        # Check that worker is alive
        if not self._is_alive():
            # Run the task synchronously
            _args = []
            for arg in args:
                if isinstance(arg, (int, long, float)):
                    _args.append(str(arg))
                elif isinstance(arg, basestring):
                    _args.append("%s" % str(json.dumps(arg)))
                else:
                    error = "Unhandled arg type: %s" % arg
                    current.log.error(error)
                    raise HTTP(501, error)
            args = ",".join(_args)
            _vars = ",".join(["%s=%s" % (str(var),
                                         str(vars[var])) for var in vars])
            if args:
                statement = "tasks['%s'](%s,%s)" % (task, args, _vars)
            else:
                statement = "tasks['%s'](%s)" % (task, _vars)
            # Handle JSON
            null = None
            exec(statement)
            return None

        auth = current.auth
        if auth.is_logged_in():
            # Add the current user to the vars
            vars["user_id"] = auth.user.id

        # Run the task asynchronously
        record = current.db.scheduler_task.insert(application_name="%s/default" % current.request.application,
                                                  task_name=task,
                                                  function_name=task,
                                                  args=json.dumps(args),
                                                  vars=json.dumps(vars),
                                                  timeout=timeout)

        # Return record so that status can be polled
        return record

    # -------------------------------------------------------------------------
    def schedule_task(self,
                      task,
                      args=None, # args to pass to the task
                      vars=None, # vars to pass to the task
                      function_name=None,
                      start_time=None,
                      next_run_time=None,
                      stop_time=None,
                      repeats=None,
                      period=None,
                      timeout=None,
                      enabled=None, # None = Enabled
                      group_name=None,
                      ignore_duplicate=False,
                      sync_output=0,
                      report_progress=False):
        """
            Schedule a task in web2py Scheduler

            @param task: name of the function/task to be scheduled
            @param args: args to be passed to the scheduled task
            @param vars: vars to be passed to the scheduled task
            @param function_name: function name (if different from task name)
            @param start_time: start_time for the scheduled task
            @param next_run_time: next_run_time for the the scheduled task
            @param stop_time: stop_time for the the scheduled task
            @param repeats: number of times the task to be repeated
            @param period: time period between two consecutive runs
            @param timeout: set timeout for a running task
            @param enabled: enabled flag for the scheduled task
            @param group_name: group_name for the scheduled task
            @param ignore_duplicate: disable or enable duplicate checking
            @param sync_output: sync output every n seconds (0 = disable sync)
        """

        if args is None:
            args = []
        if vars is None:
            vars = {}

        kwargs = {}

        if function_name is None:
            function_name = task

        # storing valid keyword arguments only if they are provided
        if start_time:
            kwargs["start_time"] = start_time

        if next_run_time:
            kwargs["next_run_time"] = next_run_time
        elif start_time:
            # default it to start_time
            kwargs["next_run_time"] = start_time

        if stop_time:
            kwargs["stop_time"] = stop_time
        elif start_time:
            # default it to one day ahead of given start_time
            if not isinstance(start_time, datetime.datetime):
                start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            stop_time = start_time + datetime.timedelta(days=1)

        if repeats is not None:
            kwargs["repeats"] = repeats

        if period:
            kwargs["period"] = period

        if timeout:
            kwargs["timeout"] = timeout

        if enabled != None:
            # NB None => enabled
            kwargs["enabled"] = enabled

        if group_name:
            kwargs["group_name"] = group_name

        if not ignore_duplicate and self._duplicate_task_exists(task, args, vars):
            # if duplicate task exists, do not insert a new one
            current.log.warning("Duplicate Task, Not Inserted", value=task)
            return False

        if sync_output != 0:
            kwargs["sync_output"] = sync_output

        auth = current.auth
        if auth.is_logged_in():
            # Add the current user to the vars
            vars["user_id"] = auth.user.id

        # Add to DB for pickup by Scheduler task
        record = self.scheduler.queue_task(task,
                                           args,
                                           vars,
                                           sync_output=sync_output)
        if report_progress:
            log_name = datetime.datetime.now() \
                .strftime("%y-%m-%d-%H-%M") + "_" + task + ".txt"
            from time import sleep
            rt = RepeatedTimer(1, self.check_status,
                               log_name, record.id,
                               self.scheduler, task,
                               current.request.folder)
            try:
                '''
                While the task is running..? What if it
                never gets out of a QUEUED state?
                Every second for 10 seconds, check
                the task's status
                '''
                sleep(15)
            finally:
                rt.stop()
        return record

    #--------------------------------------------------------------------------
    def check_status(user_id, log_name, task_id, scheduler, task_name, folder):
        import os
        log_path = os.path.join(folder, "logs", "tasks")
        from gluon import DAL, Field
        '''
        If we use current.db here instead of getting a
        new handle to the db, the task that we
        previously queued won't get inserted into the db
        so every call we make in this method to check
        on the task's status will always result in the task being in
        the 'QUEUED' state.
        '''
        db = DAL('sqlite://storage.db',
                 folder='applications/eden/databases',
                 auto_import=True)
        table = db.scheduler_task
        query = (table.id == task_id)
        task_status = None
        try:
            task_status = db(query).select(table.status).first().status
        except AttributeError:
            task_status = 'Unknown (task not yet in db)'
            
        '''
        This is the preferred way to check a task's status since
        it's using the web2py API, but we can't use this
        because the scheduler is pointing to
        current.db (see above comment):
        task_status = scheduler.task_status(task_id, output=True)
        print task_status.scheduler_task.status
        print task_status.result
        print task_status.scheduler_run.run_output
        '''

        if not os.path.exists(log_path):
            os.makedirs(log_path)

        with open(os.path.join(log_path, log_name), "a+") as log:
            log.write('<%s>: %s is currently in the %s state\n'
                      % (datetime.datetime.now(), task_name, task_status))

    # -------------------------------------------------------------------------
    def _duplicate_task_exists(self, task, args, vars):
        """
            Checks if given task already exists in the Scheduler and both coincide
            with their execution time

            @param task: name of the task function
            @param args: the job position arguments (list)
            @param vars: the job named arguments (dict)
        """

        db = current.db
        ttable = db.scheduler_task

        _args = json.dumps(args)

        query = ((ttable.function_name == task) & \
                 (ttable.args == _args) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        jobs = db(query).select(ttable.vars)
        for job in jobs:
            job_vars = json.loads(job.vars)
            if job_vars == vars:
                return True
        return False

    # -------------------------------------------------------------------------
    def _is_alive(self):
        """
            Returns True if there is at least 1 active worker to run scheduled tasks
            - run from the main request

            NB Can't run this 1/request at the beginning since the tables
               only get defined in zz_last
        """

        #if self.scheduler:
        #    return self.scheduler.is_alive()
        #else:
        #    return False

        db = current.db
        cache = current.response.s3.cache
        now = datetime.datetime.now()

        offset = datetime.timedelta(minutes=1)
        table = db.scheduler_worker
        query = (table.last_heartbeat > (now - offset))
        worker_alive = db(query).select(table.id,
                                        limitby=(0, 1),
                                        cache=cache).first()
        if worker_alive:
            return True
        else:
            return False

    # -------------------------------------------------------------------------
    @staticmethod
    def reset(task_id):
        """
            Reset the status of a task to QUEUED after FAILED

            @param task_id: the task record ID
        """

        db = current.db
        ttable = db.scheduler_task

        query = (ttable.id == task_id) & (ttable.status == "FAILED")
        task = db(query).select(ttable.id,
                                limitby=(0, 1)).first()
        if task:
            task.update_record(status="QUEUED")

    # =========================================================================
    # Functions run within the Task itself
    # =========================================================================
    def authenticate(self, user_id):
        """
            Activate the authentication passed from the caller to this new request
            - run from within the task

            NB This is so simple that we don't normally run via this API
               - this is just kept as an example of what needs to happen within the task
        """

        current.auth.s3_impersonate(user_id)

# END =========================================================================
