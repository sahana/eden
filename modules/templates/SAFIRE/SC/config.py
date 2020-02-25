# -*- coding: utf-8 -*-

#from collections import OrderedDict

#from gluon import current, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for Seychelles's extensions to the core SaFiRe template.
    """

    #T = current.T

    #settings.security.policy = 6 # Controller, Function, Table ACLs and Entity Realm

    # Send Task Notifications by SMS, not Email
    settings.event.task_notification = "SMS"

# END =========================================================================
