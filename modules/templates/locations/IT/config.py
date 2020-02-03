# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Italy
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/IT")

    # Restrict to specific country/countries
    settings.gis.countries.append("IT")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["it"] = "Italian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "it"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Rome"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 39

    settings.fin.currencies["EUR"] = "Euros"
    settings.fin.currency_default = "EUR"

# END =========================================================================
