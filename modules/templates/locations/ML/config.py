# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Mali
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/ML")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("ML")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["fr"] = "French"
    settings.L10n.languages["bm"] = "Bambara"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Bamako"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 223

    settings.fin.currencies["XOF"] = "West African CFA Francs"
    settings.fin.currency_default = "XOF"

# END =========================================================================
