# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Kyrgyzstan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/KG")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("KG")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["ky"] = "Kyrgyz"
    settings.L10n.languages["ru"] = "Russian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ky"
    #settings.L10n.default_language = "ru"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Bishkek"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 996

    settings.fin.currencies["KGS"] = "Som"
    settings.fin.currency_default = "KGS"

# END =========================================================================
