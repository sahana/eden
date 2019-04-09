# -*- coding: utf-8 -*-

#from collections import OrderedDict

from gluon import current
#from gluon.storage import Storage

def config(settings):
    """
        Settings for the Caritas variant of BRCMS
    """

    T = current.T

    settings.base.system_name = T("Case Management")
    settings.base.system_name_short = "BRCMS"

    # Pre-populate data
    settings.base.prepopulate += ("BRCMS/Caritas",)
    settings.base.prepopulate_demo = ["default/users", "BRCMS/Caritas/Demo"]

    # -------------------------------------------------------------------------
    # Branding
    logo = "/%s/static/themes/BRCMS/img/caritas.png" % current.request.application
    settings.ui.menu_logo = settings.frontpage.logo = logo

    # -------------------------------------------------------------------------
    # Localisation
    settings.L10n.default_language = "de"

    # -------------------------------------------------------------------------
    # PR Module settings
    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

# END =========================================================================
