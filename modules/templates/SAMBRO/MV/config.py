# -*- coding: utf-8 -*-

from gluon import current

from collections import OrderedDict

def config(settings):
    """
        Maldives specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Maldives Warning and Situational-Awareness System")

    # Default Language
    settings.L10n.default_language = "dv"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("dv", "ދިވެހި"), # Divehi (Maldives)
        ("en-US", "English"),
    ])
    settings.L10n.languages = languages

# END =========================================================================
