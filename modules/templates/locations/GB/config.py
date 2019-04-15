# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for United Kingdom
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/GB")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("GB")

    # L10n (Localization) settings
    # Default timezone for users
    settings.L10n.timezone = "Europe/London"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 44

    settings.fin.currencies["GBP"] = "British Pounds"
    settings.fin.currency_default = "GBP"

# END =========================================================================
