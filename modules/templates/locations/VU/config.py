# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Vanuatu
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/VU")

    # Restrict to specific country/countries
    settings.gis.countries.append("VU")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["bi"] = "Bislama"
    settings.L10n.languages["fr"] = "French"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "bi"
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.timezone = "Pacific/Efate"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 678

    settings.fin.currencies["VUV"] = "Vanuatu Vatu"
    settings.fin.currency_default = "VUV"

# END =========================================================================
