# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Lebanon
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/LB")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("LB")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["ar"] = "Arabic"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ar"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Beirut"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 961

    settings.fin.currencies["LBP"] = "Lebanese Pound"
    settings.fin.currency_default = "LBP"

# END =========================================================================
