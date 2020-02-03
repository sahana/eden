# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Tuvalu
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/TV")

    # Restrict to specific country/countries
    settings.gis.countries.append("TV")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["tvl"] = "Tuvaluan"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "tvl"
    # Default timezone for users
    settings.L10n.timezone = "Pacific/Funafuti"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 688

    settings.fin.currencies["AUD"] = "Australian Dollars"
    #settings.fin.currencies["TVD"] = "Tuvaluan Dollars" # pegged to AUD
    settings.fin.currency_default = "AUD"

# END =========================================================================
