#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Call Web2py scheduler in app models context and run a specified task using
# its scheduled arguments.  Two options for running this script:
#
# cd web2py
# python applications/<app>/static/scripts/tools/run_scheduler_tasks.py --app=<app> --task=<task>
# -- or --
# export WEB2PY_PATH=/path/to/web2py
# cd $WEB2PY_PATH/applications/<app>/static/scripts/tools
# python run_scheduler_tasks.py --app=<app> --task=<task>
#
# If task is omitted this will run all scheduled tasks sequentially.  If both
# args are omitted, the app will default to eden.
#
# Purpose of this is to allow executing tasks with the Eclipse debugger -- the
# usual ways of starting a scheduler worker launchs it in a separate thread or
# via exec, which the debugger doesn't step into.
#
# To set up an Eclipse run config, duplicate your Web2py run config, replace
# the file to run with this script, and add at least the --app argument.
# The WEB2PY_PATH is not needed in this case since the working directory will
# be set to the web2py directory.
#
# The statement that executes the task function is marked with a comment:
# SET BREAKPOINT HERE
# Find that, set a breakpoint on that line, then step into the function.

import os, sys, argparse

if not 'WEB2PY_PATH' in os.environ:
    os.environ['WEB2PY_PATH'] = os.getcwd()
else:
    os.chdir(os.environ['WEB2PY_PATH'])
sys.path.append(os.environ['WEB2PY_PATH'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = """
        Run Web2py scheduler tasks in Web2py application context, without the
        scheduler.  Useful for executing the task in a debugger.
        Tasks must be scheduled in order to provide their arguments -- they
        won't be run if not scheduled.  If task is specified, the first
        scheduled instance will be run.  If task is not specified, the first
        scheduled instance for each task will be run sequentially.
        """,
        usage = """
        export WEB2PY_PATH = /path/to/web2py; python run_scheduler_tasks.py --app=<app> [--task=<task>] [--allargs=<True|False>]
        """)
    parser.add_argument(
        "--app", dest="app", default="eden", help="Application directory name")
    parser.add_argument(
        "--task", dest="task", default=None, help="Task name")
    parser.add_argument(
        "--allargs", dest="allargs", default=True,
        help="If True (the default), run task with all scheduled arg sets. If False, run with first set encountered only.")
    args = vars(parser.parse_args())
    app = args["app"]
    task = args["task"]
    allargs = args["allargs"]

    adir = os.path.join('applications', app)
    if not os.path.exists(adir):
        print >> sys.stderr, "Application not found: %s" % adir
        sys.exit(1)

    from gluon.custom_import import custom_import_install
    custom_import_install(os.environ['WEB2PY_PATH'])
    from gluon.shell import env
    _env = env(app, c=None, import_models=True)
    globals().update(**_env)
    # This is present in case this is a first run of the models.
    db.commit()

    from gluon import current

    # Get tasks from the scheduler_task table.
    if task:
        query = (db.scheduler_task.task_name == task)
    else:
        query = (db.scheduler_task.id > 0)
    scheduled_tasks = db(query).select(orderby=db.scheduler_task.task_name)
    # Pick up the associated function objects from the scheduler's task list.
    # These are also stored in the S3Task instance -- both lists should be the
    # same.
    posted_tasks = current._scheduler.tasks
    #posted_tasks = current.response.s3.tasks

    task_name = None
    for task_row in scheduled_tasks:
        if not allargs and task_row.task_name == task_name:
            continue
        task_name = task_row.task_name
        task_function = posted_tasks.get(task_name, None)
        if not task_function:
            print >> sys.stderr, "Skipping task %s as no function in task list" % task_name
            continue
        # That args list and vars dict are stored as strings.
        if task_row.args:
            task_args = eval(task_row.args)
        else:
            task_args = []
        if task_row.vars:
            task_vars = eval(task_row.vars)
        else:
            task_vars = {}
        try:
            # To examine each task function in the debugger, set a breakpoint
            # here, then step into the function.
            task_function(*task_args, **task_vars)  # SET BREAKPOINT HERE
        except Exception:
            print >> sys.stderr, "Task %s threw:\n" % task_name
            import traceback
            exc_type, exc_value, exc_trace = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_trace, file=sys.stderr)
            try:
                # Python docs for sys.exc_info() warn that one must clean up the
                # extracted trace object.
                del exc_trace
            except:
                pass
