# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Jordan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/YE")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("YE")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["ar"] = "Arabic"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ar"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Aden"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 967

    settings.fin.currencies["YER"] = "Yemeni Rials"
    settings.fin.currency_default = "YER"

# END =========================================================================
