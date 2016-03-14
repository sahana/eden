# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Maldives specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Maldives Warning and Situational-Awareness System")

# END =========================================================================
