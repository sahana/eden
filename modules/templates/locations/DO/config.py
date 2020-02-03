# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Dominican Republic
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/DO")

    # Restrict to specific country/countries
    settings.gis.countries.append("DO")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/Santo_Domingo"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 1

    settings.fin.currencies["DOP"] = "Pesos"
    settings.fin.currency_default = "DOP"

# END =========================================================================
