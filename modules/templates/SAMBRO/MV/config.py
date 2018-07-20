# -*- coding: utf-8 -*-

from gluon import current, URL

from collections import OrderedDict

def config(settings):
    """
        Maldives specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Dhandhaana - Maldives Disaster Alerting and Situational Awareness Service")
    settings.base.system_name_short = T("NDMC")

    # Default Language
    settings.L10n.default_language = "dv"

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SAMBRO.MV"
    settings.base.theme_base = "default"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("dv", "Divehi"), # Maldives
        ("en-US", "English"),
    ])
    settings.cap.languages = languages
    settings.L10n.languages = languages

    # Alert Hub Title
    settings.cap.alert_hub_title = T("Maldives Alert Hub Common Alerting Picture")

    # Maldives don't support ack workflow
    settings.cap.use_ack = False

    # UI Settings
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["SAMBRO", "MV", "img", "ndmc.png"],
                                )

# END =========================================================================
