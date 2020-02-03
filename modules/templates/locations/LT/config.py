# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Lithuania
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/LT")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("LT")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["lt"] = "Lithuanian"
    settings.L10n.languages["pl"] = "Polish"
    settings.L10n.languages["ru"] = "Russian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "lt"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Vilnius"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 370

    settings.fin.currencies["EUR"] = "Euros"
    settings.fin.currency_default = "EUR"

# END =========================================================================
