# -*- coding: utf-8 -*-

#from collections import OrderedDict

#from gluon import current, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for South Africa's extensions to the core SaFiRe template.
    """

    T = current.T

    settings.base.system_name = T("Disaster Management Information System")
    settings.base.system_name_short = T("DMIS")

# END =========================================================================
