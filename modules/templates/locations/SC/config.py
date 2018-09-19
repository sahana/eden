# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Seychelles
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/SC")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("SC")
    # Disable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["fr"] = "French"
    settings.L10n.languages["crs"] = "Seychellois Creole"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "crs"
    # Default timezone for users
    settings.L10n.utc_offset = "+0400"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 248

    settings.fin.currencies["SCR"] = "Seychellois Rupee"
    settings.fin.currency_default = "SCR"

# END =========================================================================
