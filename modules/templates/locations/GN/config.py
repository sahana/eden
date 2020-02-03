# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Guinea
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/GN")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("GN")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["fr"] = "French"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Conakry"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 224

    settings.fin.currencies["GNF"] = "Guinean Francs"
    settings.fin.currency_default = "GNF"

# END =========================================================================
