# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

def config(settings):
    """
        Settings for Urgences-Sante's extensions to the core SaFiRe template.
    """

    #settings.L10n.default_language = "fr"

    # Users should not be allowed to register themselves
    settings.security.self_registration = False

    settings.ui.menu_logo = "/%s/static/themes/Urgences-Sante/img/logo.png" % current.request.application

# END =========================================================================
