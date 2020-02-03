# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Uzbekistan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/TJ")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("TJ")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["tg"] = "Tajik"
    settings.L10n.languages["ru"] = "Russian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "tg"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Dushanbe"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 992

    settings.fin.currencies["TJS"] = "Somoni"
    settings.fin.currency_default = "TJS"

# END =========================================================================
