# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Azerbaijan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/AZ")

    # Restrict to specific country/countries
    settings.gis.countries.append("AZ")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["az"] = "Azerbaijani"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "az"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Baku"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 994

    settings.fin.currencies["AZN"] = "Manat"
    settings.fin.currency_default = "AZN"

# END =========================================================================
