# -*- coding: utf-8 -*-

from gluon import current, URL

from collections import OrderedDict

def config(settings):
    """
        Global Alerthub specific template settings for Common Alerting Protocol (CAP) and other feeds
    """

    T = current.T

    settings.base.system_name = T("Sahana Research and Action Aggregated Globally Relayed Alerts and Bulletins")
    settings.base.system_name_short = T("SaRA-GRAB")

    # Default Language
    settings.L10n.default_language = "en-US"

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SAMBRO.AlertHub"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("en-US", "English"),
    ])
    settings.L10n.languages = languages

    # for creating location from SAME geocodes
    settings.cap.same_code = "PSGC"

    # Alert Hub Title
    # NB Alert Hub is home page for Philippines
    settings.cap.alert_hub_title = T("Sahana Research and Action Aggregated Globally Relayed Alerts and Bulletins")

    # UI Settings
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["SAMBRO", "AlertHub", "img", "alerthub.png"],
                                )

    # Name of Method used to create bulletin
    # This may vary according to organisation implementing it
    settings.cap.form_bulletin = "form_ocd"


# END =========================================================================
