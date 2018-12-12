# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Canada
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/CA")

    # Restrict to specific country/countries
    settings.gis.countries.append("CA")
    # Enable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = True

    # L10n (Localization) settings
    settings.L10n.languages["fr"] = "French"
    #settings.L10n.languages["ath"] = "Athabaskan"
    #settings.L10n.languages["ikt"] = "Inuinnaqtun"
    #settings.L10n.languages["iu"] = "Inuktitut"
    #settings.L10n.languages["moe"] = "Innu-aimun"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.utc_offset = "-0500"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 1

    settings.fin.currencies["CAD"] = "Canadian Dollars"
    settings.fin.currency_default = "CAD"

# END =========================================================================
