# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Myanmar specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Myanmar Warning and Situational-Awareness System")

    settings.L10n.languages = {"en-US": "English",
                               "my": "မြန်မာစာ"}

# END =========================================================================
