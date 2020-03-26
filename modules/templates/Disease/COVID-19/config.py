# -*- coding: utf-8 -*-

#from collections import OrderedDict

#from gluon import current, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for COVID-19 data for the Disease template.

        Normally configured as:
        settings.base.template = ("locations.XX", "Disease", "Disease.COVID-19")
    """

    #T = current.T

    # PrePopulate data
    settings.base.prepopulate.append("Disease/COVID-19")
    
# END =========================================================================
