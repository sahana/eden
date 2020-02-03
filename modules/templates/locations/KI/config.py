# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Kiribati
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/KI")

    # Restrict to specific country/countries
    settings.gis.countries.append("KI")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["gil"] = "Gilbertese"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "gil"
    # Default timezone for users
    settings.L10n.timezone = "Pacific/Tarawa"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 686

    settings.fin.currencies["AUD"] = "Australian Dollars" # Kiribati Dollar pegged
    settings.fin.currency_default = "AUD"

# END =========================================================================
