# -*- coding: utf-8 -*-

#from collections import OrderedDict

from gluon import current, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for Missouri Emergency Medical Services Association's extensions to the core SaFiRe template.
    """

    T = current.T

    settings.ui.menu_logo = "/%s/static/themes/MOEMTF/img/logo.jpg" % current.request.application

    # PrePopulate data
    settings.base.prepopulate += ("SAFIRE/MOEMTF",)

    # Users should not be allowed to register themselves
    #settings.security.self_registration = False

# END =========================================================================
