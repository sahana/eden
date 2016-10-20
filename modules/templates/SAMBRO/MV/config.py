# -*- coding: utf-8 -*-

from gluon import current

from collections import OrderedDict

def config(settings):
    """
        Maldives specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Dhandhaana - Maldives Disaster Alerting and Situational Awareness Service")

    # Default Language
    settings.L10n.default_language = "dv"

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SAMBRO.MV"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("dv", "ދިވެހި"), # Divehi (Maldives)
        ("en-US", "English"),
    ])
    settings.L10n.languages = languages

    # Alert Hub Title
    settings.cap.alert_hub_title = T("Maldives Alert Hub Common Operating Picture")

    # Maldives don't support ack workflow
    settings.cap.use_ack = False

# END =========================================================================
