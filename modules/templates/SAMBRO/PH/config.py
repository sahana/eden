# -*- coding: utf-8 -*-

from gluon import current, URL

from collections import OrderedDict

def config(settings):
    """
        Philippines specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Philippines Warning and Situational-Awareness System")
    settings.base.system_name_short = T("PAGASA")

    # Default Language
    settings.L10n.default_language = "tl"

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SAMBRO.PH"
    settings.base.theme_base = "default"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("en-US", "English"),
        ("tl", "Tagalog"), # Filipino
    ])
    settings.cap.languages = languages
    settings.L10n.languages = languages

    # for creating location from SAME geocodes
    settings.cap.same_code = "PSGC"

    # Alert Hub Title
    # NB Alert Hub is home page for Philippines
    settings.cap.alert_hub_title = T("PAGASA Alert Hub Common Alerting Picture")

    # Default location from geocode
    settings.cap.area_default = ["geocode"]

    # UI Settings
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["SAMBRO", "PH", "img", "pagasa.png"],
                                )

# END =========================================================================
