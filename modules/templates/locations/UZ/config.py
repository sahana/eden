# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Uzbekistan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/UZ")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("UZ")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["uz"] = "Uzbek"
    settings.L10n.languages["kaa"] = "Karakalpak"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "uz"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Tashkent"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 998

    settings.fin.currencies["UZS"] = "Uzbek Som"
    settings.fin.currency_default = "UZS"

# END =========================================================================
