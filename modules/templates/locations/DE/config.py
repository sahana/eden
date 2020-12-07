# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Germany
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/DE")

    # Restrict to specific country/countries
    settings.gis.countries.append("DE")

    # L10n (Localization) settings
    settings.L10n.languages["de"] = "German"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "de"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Berlin"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 49

    settings.fin.currencies["EUR"] = "Euros"
    settings.fin.currency_default = "EUR"

# END =========================================================================
