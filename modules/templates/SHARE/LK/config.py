# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

def config(settings):
    """
        SHARE settings for Sri Lanka

        @ToDo: Setting for single set of Sectors / Sector Leads Nationally
    """

    #T = current.T

    # PrePopulate data
    settings.base.prepopulate += ("SHARE/LK",)
    settings.base.prepopulate_demo += ("SHARE/Demo",)

    # Finance settings
    settings.fin.currencies = {
        #"EUR" : "Euros",
        #"GBP" : "Great British Pounds",
        "LKR" : "Sri Lanka Rupees",
        "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "USD"

# END =========================================================================
