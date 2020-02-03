# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Turkmenistan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/TM")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("TM")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["tk"] = "Turkmen"
    settings.L10n.languages["ru"] = "Russian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "tk"
    #settings.L10n.default_language = "ru"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Ashgabat"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 993

    settings.fin.currencies["TMT"] = "Turkmen New Manat"
    settings.fin.currency_default = "TMT"

# END =========================================================================
