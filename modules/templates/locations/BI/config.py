# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Burundi
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/BI")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("BI")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["fr"] = "French"
    settings.L10n.languages["rn"] = "Kirundi"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fr"
    #settings.L10n.default_language = "rn"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Bujumbura"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 257

    settings.fin.currencies["BIF"] = "Burundian Francs"
    settings.fin.currency_default = "BIF"

# END =========================================================================
