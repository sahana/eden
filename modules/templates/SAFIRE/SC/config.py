# -*- coding: utf-8 -*-

#from collections import OrderedDict

#from gluon import current, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for Seychelles's extensions to the core SaFiRe template.
    """

    #T = current.T

    # Send Task Notifications by SMS, not Email
    settings.event.task_notification = "SMS"

# END =========================================================================
