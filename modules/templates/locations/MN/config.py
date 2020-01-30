# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Mongolia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/MN")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("MN")
    # Disable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["mn"] = "Mongolian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "mn"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Ulan_Bator"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 976

    settings.fin.currencies["MNT"] = "Tögrög"
    settings.fin.currency_default = "MNT"

# END =========================================================================
