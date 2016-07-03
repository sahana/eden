# -*- coding: utf-8 -*-

# This is an example for a Sahana plugin
#
# (NB any plugin with the name "skeleton" will be ignored)
#

# Can specify a version string:
# - this is visible in the session when running ?debug=1,
#   and it can be visible in the GUI (depends on template)
# - helps with support requests and debugging
#
__version__ = "1.0"

# Load current to access things like settings
from gluon import current

def setup():
    """
        Setup function that will be called by the plugin loader
        during the request cycle, immediately before entering
        the controller.

        This function *must* be present in any plugin, otherwise
        the plugin will be ignored after the initial attempt.

        NB: this function is called in every request cycle, so
            should not create bottlenecks, but keep all added
            functionality lazy/optional or small as possible.

        @return: nothing (return value will be ignored)
    """

    # Examples where functionality could be added:

    # Can access the settings:
    settings = current.deployment_settings

    # Can access scheduler tasks:
    tasks = s3.tasks
