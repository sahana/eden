# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Austria
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/AT")

    # Restrict to specific country/countries
    settings.gis.countries.append("AT")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["de"] = "German"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "de"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Vienna"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 43

    settings.fin.currencies["EUR"] = "Euros"
    settings.fin.currency_default = "EUR"

# END =========================================================================
