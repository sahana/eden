# -*- coding: utf-8 -*-

from gluon import current, URL

from collections import OrderedDict

def config(settings):
    """
        Bhutan specific template settings for SAMBRO and the Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Bhutan Warning and Situational-Awareness System")
    settings.base.system_name_short = T("DDM Bhutan")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SAMBRO.BT"
    settings.base.theme_base = "default"

    # Default Language
    settings.L10n.default_language = "en-US"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("en-US", "English"),
        ("bt", "Bhutan"),
    ])
    settings.cap.languages = languages
    settings.L10n.languages = languages

    # Alert Hub Title
    settings.cap.alert_hub_title = T("Bhutan Alert Hub Common Alerting Picture")

    # UI Settings
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["SAMBRO", "BT", "img", "ddm.png"],
                                )

# END =========================================================================
