# -*- coding: utf-8 -*-

from gluon import current

from collections import OrderedDict

def config(settings):
    """
        Myanmar specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Myanmar Warning and Situational-Awareness System")

    # Default Language
    settings.L10n.default_language = "my"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("en-US", "English"),
        ("my", "မြန်မာစာ"),        # Burmese
    ])
    settings.L10n.languages = languages

# END =========================================================================
