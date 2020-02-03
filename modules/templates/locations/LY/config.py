# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Libya
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/LY")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("LY")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["ar"] = "Arabic"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ar"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Tripoli"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 218

    settings.fin.currencies["LYD"] = "Libyan Dinars"
    settings.fin.currency_default = "LYD"

# END =========================================================================
