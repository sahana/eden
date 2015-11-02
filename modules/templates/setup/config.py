# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for the Setup co-application

        http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Amazon/Setup
    """

    T = current.T

    settings.base.system_name = T("Sahana Eden Deployment")
    #settings.base.theme = "default"

    # -----------------------------------------------------------------------------
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Sahana Eden"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("setup", Storage(
            name_nice = T("Sahana Eden Deployment Tool"),
            restricted = False,
            access = None,
            module_type = None
        ))
    ])

# END =========================================================================