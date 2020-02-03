# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Senegal
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/SN")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("SN")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["fr"] = "French"
    settings.L10n.languages["wo"] = "Wolof"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Dakar"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 221

    settings.fin.currencies["XOF"] = "West African CFA Francs"
    settings.fin.currency_default = "XOF"

# END =========================================================================
