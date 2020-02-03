# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Ukraine
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/UA")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("UA")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["uk"] = "Ukrainian"
    settings.L10n.languages["ru"] = "Russian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "uk"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Kiev"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 380

    settings.fin.currencies["UAH"] = "Ukrainian Hryvnia"
    settings.fin.currency_default = "UAH"

# END =========================================================================
