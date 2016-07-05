# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Philippines specific template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Philippines Warning and Situational-Awareness System")

    # Default Language
    settings.L10n.default_language = "tl"

    # for creating location from SAME geocodes
    settings.cap.same_code = "PSGC"

# END =========================================================================
