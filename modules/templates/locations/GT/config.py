# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Guatemala
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/GT")

    # Restrict to specific country/countries
    settings.gis.countries.append("GT")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/Guatemala"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 502

    settings.fin.currencies["GTQ"] = "Quetzal"
    settings.fin.currency_default = "GTQ"

# END =========================================================================
