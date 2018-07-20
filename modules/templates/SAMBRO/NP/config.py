# -*- coding: utf-8 -*-

from gluon import current, URL

from collections import OrderedDict

def config(settings):
    """
        DHM Nepal specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("DHM Nepal Warning and Situational-Awareness System")
    settings.base.system_name_short = T("DHM Nepal")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SAMBRO.NP"
    settings.base.theme_base = "default"

    # Default Language
    settings.L10n.default_language = "ne"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("en-US", "English"),
        ("ne", "Nepali"),
    ])
    settings.cap.languages = languages
    settings.L10n.languages = languages

    # Alert Hub Title
    settings.cap.alert_hub_title = T("Nepal Alert Hub Common Alerting Picture")

    # UI Settings
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["SAMBRO", "NP", "img", "dhm.png"],
                                )

# END =========================================================================
