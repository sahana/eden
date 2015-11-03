# -*- coding: utf-8 -*-
"""
    1st RUN:
    - Run update_check if needed.
    - Import the S3 Framework Extensions
    - If needed, copy deployment templates to the live installation.
"""

# Debug why Eclipse breakpoints are ignored
# http://stackoverflow.com/questions/29852426/pydev-ignoring-breakpoints
#import sys
#def trace_func(frame, event, arg):
#    print 'Context: ', frame.f_code.co_name, '\tFile:', frame.f_code.co_filename, '\tLine:', frame.f_lineno, '\tEvent:', event
#    return trace_func
#sys.settrace(trace_func)

# -----------------------------------------------------------------------------
# Perform update checks - will happen in 1st_run or on those upgrades when new
# dependencies have been added.

# Increment this when new dependencies are added
# This will be compared to the version in the 0000_update_check.py 'canary' file.
CURRENT_UPDATE_CHECK_ID = 4
update_check_needed = False
try:
    if CANARY_UPDATE_CHECK_ID != CURRENT_UPDATE_CHECK_ID:
        update_check_needed = True
except NameError:
    update_check_needed = True

# shortcut
appname = request.application

if update_check_needed:
    # @ToDo: Load deployment_settings so that we can configure the update_check
    # - need to rework so that 000_config.py is parsed 1st
    import s3cfg
    settings = s3cfg.S3Config()
    # Run update checks
    from s3_update_check import update_check
    errors = []
    warnings = []
    messages = update_check(settings)
    errors.extend(messages.get("error_messages", []))
    warnings.extend(messages.get("warning_messages", []))

    # Catch-all check for dependency errors.
    # NB This does not satisfy the goal of calling out all the setup errors
    #    at once - it will die on the first fatal error encountered.
    try:
        import s3 as s3base
    except Exception, e:
        errors.append(e.message)

    import sys

    if warnings:
        # Report (non-fatal) warnings.
        prefix = "\n%s: " % T("WARNING")
        msg = prefix + prefix.join(warnings)
        print >> sys.stderr, msg
    if errors:
        # Report errors and stop.
        actionrequired = T("ACTION REQUIRED")
        prefix = "\n%s: " % actionrequired
        msg = prefix + prefix.join(errors)
        print >> sys.stderr, msg
        htmlprefix = "\n<br /><b>%s</b>: " % actionrequired
        html = "<errors>" + htmlprefix + htmlprefix.join(errors) + "\n</errors>"
        raise HTTP(500, body=html)

    # Create or update the canary file.
    from gluon import portalocker
    canary = open("applications/%s/models/0000_update_check.py" % appname, "w")
    portalocker.lock(canary, portalocker.LOCK_EX)

    statement = "CANARY_UPDATE_CHECK_ID = %s" % CURRENT_UPDATE_CHECK_ID
    canary.write(statement)
    canary.close()

# -----------------------------------------------------------------------------
import os
try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage

# Keep all S3 framework-level elements stored in response.s3, so as to avoid
# polluting global namespace & to make it clear which part of the framework is
# being interacted with.
# Avoid using this where a method parameter could be used:
# http://en.wikipedia.org/wiki/Anti_pattern#Programming_anti-patterns
response.s3 = Storage()
s3 = response.s3
s3.gis = Storage() # Defined early for use by S3Config.

current.cache = cache
# Limit for filenames on filesystem:
# https://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
# NB This takes effect during the file renaming algorithm - the length of uploaded filenames is unaffected
current.MAX_FILENAME_LENGTH = 255 # Defined early for use by S3Config.

# Import S3Config
import s3cfg
settings = s3cfg.S3Config()
current.deployment_settings = deployment_settings = settings

# END =========================================================================
