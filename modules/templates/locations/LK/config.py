# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Myanmar
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/LK")

    # Restrict to specific country/countries
    settings.gis.countries.append("LK")
    # Disable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["si"] = "Sinhala"
    settings.L10n.languages["ta"] = "Tamil"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "si"
    # Default timezone for users
    settings.L10n.utc_offset = "+0530"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 94

    settings.fin.currencies["LKR"] = "Sri Lanka Rupees"
    settings.fin.currency_default = "LKR"

# END =========================================================================
