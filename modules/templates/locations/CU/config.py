# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Cuba
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/CU")

    # Restrict to specific country/countries
    settings.gis.countries.append("CU")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/Havana"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 53

    settings.fin.currencies["CUP"] = "Pesos"
    #settings.fin.currencies["CUC"] = "Convertible Pesos" # Pegged to USD
    settings.fin.currency_default = "CUP"

# END =========================================================================
