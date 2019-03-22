# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Nepal
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/NP")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("NP")
    # Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["ne"] = "Nepali"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ne"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Kathmandu"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 977

    settings.fin.currencies["NPR"] = "Nepalese Rupee"
    settings.fin.currency_default = "NPR"

# END =========================================================================
