# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Chad
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/TD")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("TD")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["ar"] = "Arabic"
    settings.L10n.languages["fr"] = "French"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ar"
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Ndjamena"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 235

    settings.fin.currencies["XAF"] = "Central African CFA Francs"
    settings.fin.currency_default = "XAF"

# END =========================================================================
