# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Greece
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/GR")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("GR")
    # Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["el"] = "Greek"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "el"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Athens"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 30

    settings.fin.currencies["EUR"] = "Euros"
    settings.fin.currency_default = "EUR"

# END =========================================================================
