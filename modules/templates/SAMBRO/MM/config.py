# -*- coding: utf-8 -*-

from gluon import current, URL

from collections import OrderedDict

def config(settings):
    """
        Myanmar specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Myanmar Warning and Situational-Awareness System")
    settings.base.system_name_short = T("DMH")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SAMBRO.MM"

    # Default Language
    settings.L10n.default_language = "my"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("en-US", "English"),
        ("my", "Burmese"),
    ])
    settings.cap.languages = languages
    settings.L10n.languages = languages

    # Alert Hub Title
    settings.cap.alert_hub_title = T("Myanmar Alert Hub Common Alerting Picture")

    # UI Settings
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["SAMBRO", "MM", "img", "dmh.png"],
                                )

# END =========================================================================
