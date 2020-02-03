# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Kazakhstan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/KZ")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("KZ")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["kk"] = "Kazakh"
    settings.L10n.languages["ru"] = "Russian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "kk"
    #settings.L10n.default_language = "ru"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Qyzylorda"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 7

    settings.fin.currencies["KZT"] = "Tenge"
    settings.fin.currency_default = "KZT"

# END =========================================================================
