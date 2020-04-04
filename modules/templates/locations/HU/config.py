# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Hungary
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/HU")

    # Restrict to specific country/countries
    settings.gis.countries.append("HU")

    # L10n (Localization) settings
    settings.L10n.languages["hu"] = "Hungarian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "hu"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Budapest"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 36

    settings.fin.currencies["HUF"] = "Forint"
    settings.fin.currency_default = "HUF"

# END =========================================================================
