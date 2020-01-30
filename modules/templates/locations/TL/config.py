# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Timor-Leste
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/TL")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("TL")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["tdt"] = "Tetum"
    settings.L10n.languages["pt"] = "Portuguese"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "tdt"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Dili"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 670

    settings.fin.currencies["USD"] = "United States Dollars"
    settings.fin.currency_default = "USD"

# END =========================================================================
