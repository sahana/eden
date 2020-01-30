# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Pakistan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/PK")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("PK")
    # Disable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["ur"] = "Urdu"
    settings.L10n.languages["pa"] = "Punjabi"
    settings.L10n.languages["ps"] = "Pashto"
    settings.L10n.languages["sd"] = "Sindhi"
    settings.L10n.languages["bal"] = "Balochi"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ur"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Karachi"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 92

    settings.fin.currencies["PKR"] = "Pakistani Rupees"
    settings.fin.currency_default = "PKR"

# END =========================================================================
