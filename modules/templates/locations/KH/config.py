# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Cambodia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/KH")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("KH")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["km"] = "Khmer"
    settings.L10n.languages["fr"] = "French"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "km"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Phnom_Penh"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 855

    settings.fin.currencies["KHR"] = "Riel"
    settings.fin.currency_default = "KHR"

# END =========================================================================
