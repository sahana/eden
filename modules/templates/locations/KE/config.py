# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Kenya
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/KE")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("KE")
    # Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["sw"] = "Swahili"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "sw"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Nairobi"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 254

    settings.fin.currencies["KES"] = "Kenyan Shillings"
    settings.fin.currency_default = "KES"

# END =========================================================================
