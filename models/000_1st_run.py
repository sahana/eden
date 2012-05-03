# -*- coding: utf-8 -*-
"""
    1st RUN:

    - Run update check if needed.
    - Import the S3 Framework Extensions
    - If needed, copy deployment specific templates to the live installation.
      Developers: note that the templates are version-controlled, while their
                  site-specific copies are not (to avoid leaking of sensitive
                  or irrelevant information into the repository).
                  If you add something new to these files, you should also
                  make the change at deployment-templates and commit it.
"""

import os

# -----------------------------------------------------------------------------
# Perform update checks - will happen in 1st_run or on those upgrades when new
# dependencies have been added.

# Increment this when new dependencies are added
# This will be compared to the version in the 0000_update_check.py 'canary' file.
CURRENT_UPDATE_CHECK_ID = 2
update_check_needed = False
try:
    if CANARY_UPDATE_CHECK_ID != CURRENT_UPDATE_CHECK_ID:
        update_check_needed = True
except NameError:
    update_check_needed = True
if update_check_needed:
    # Run update checks -- these are the update_check() functions from each
    # Python file in private/update_check that has such a function.
    from gluon.fileutils import listdir
    update_check_path_parts = [
        "applications", request.application, "private", "update_check"]
    update_check_path = os.path.join(*update_check_path_parts)
    update_check_import_path = ".".join(update_check_path_parts)
    errors = []
    warnings = []
    # Supply the current (Web2py) environment. Pick out only the items that are
    # safe for the check functions to combine with their own environments, i.e.
    # not anything of the form __x__.
    environment = dict((k, v) for (k, v) in globals().iteritems() if not k.startswith("__"))
    for filename in listdir(update_check_path, expression = ".*\.py$"):
        try:
            exec "from %s.%s import update_check" % \
                 (update_check_import_path, filename[0:-3])
        except ImportError:
            continue
        messages = update_check(environment)
        errors.extend(messages.get("error_messages", []))
        warnings.extend(messages.get("warning_messages", []))

    # Catch-all check for dependency errors.
    # @ToDo: This does not satisfy the goal of calling out all the setup errors
    #        at once -- it will die on the first fatal error encountered.
    try:
        import s3 as s3base
    except Exception, e:
        errors.extend(e.message)

    # Report (non-fatal) warnings.
    if warnings:
        prefix = "\n%s: " % T("WARNING")
        msg = prefix + prefix.join(warnings)
        import sys
        print >> sys.stderr, msg
    # Report errors and stop.
    if errors:
        prefix = "\n%s: " % T("ACTION REQUIRED")
        msg = prefix + prefix.join(errors)
        import sys
        print >> sys.stderr, msg
        raise HTTP(500, body=msg)

    # Create or update the canary file.
    from gluon import portalocker
    canary = open(
        "applications/%s/models/0000_update_check.py" % request.application,
        "w")
    portalocker.lock(canary, portalocker.LOCK_EX)
    statement = "CANARY_UPDATE_CHECK_ID = %s" % CURRENT_UPDATE_CHECK_ID
    canary.write(statement)
    canary.close()

# -----------------------------------------------------------------------------
from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict

# Keep all S3 framework-level elements stored in response.s3, so as to avoid
# polluting global namespace & to make it clear which part of the framework is
# being interacted with.
# Avoid using this where a method parameter could be used:
# http://en.wikipedia.org/wiki/Anti_pattern#Programming_anti-patterns
response.s3 = Storage()
s3 = response.s3
response.s3.gis = Storage()  # Defined early for use by S3Config.

current.cache = cache

# Import S3Config
import s3cfg
deployment_settings = s3cfg.S3Config()
current.deployment_settings = deployment_settings

# END =========================================================================
