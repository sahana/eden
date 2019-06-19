# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Demographic Republic of Congo
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/CD")

    # Restrict to specific country/countries
    settings.gis.countries.append("CD")
    # Dosable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["fr"] = "French"
    #settings.L10n.languages["kg"] = "Kongo"
    #settings.L10n.languages["ln"] = "Lingala"
    #settings.L10n.languages["sw"] = "Swahili"
    #settings.L10n.languages["lu"] = "Luba-Katanga"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Kinshasa"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 243

    settings.fin.currencies["CDF"] = "Congolese Franc"
    settings.fin.currency_default = "CDF"

# END =========================================================================
