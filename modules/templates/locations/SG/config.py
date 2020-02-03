# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Singapore
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/SG")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("SG")
    # Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["ms"] = "Malay"
    settings.L10n.languages["zh"] = "Mandarin" # huyu Singaporean Mandarin
    settings.L10n.languages["ta"] = "Tamil"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ms"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Singapore"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 65

    settings.fin.currencies["SGD"] = "Singapore Dollars"
    settings.fin.currency_default = "SGD"

# END =========================================================================
