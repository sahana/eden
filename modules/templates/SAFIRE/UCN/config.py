# -*- coding: utf-8 -*-

#from collections import OrderedDict

from gluon import current#, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for United Cajun Navy's extensions to the core SaFiRe template.
    """

    settings.base.system_name = "United Cajun Navy Emergency Management"
    settings.base.system_name_short = "UCN"

    settings.ui.menu_logo = "/%s/static/themes/UCN/img/logo.png" % current.request.application

    settings.L10n.display_toolbar = False

# END =========================================================================
