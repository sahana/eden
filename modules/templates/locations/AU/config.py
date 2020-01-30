# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Australia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/AU")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("AU")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["en-gb"] = "English (United Kingdom)"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "en-gb"
    # Default timezone for users
    settings.L10n.timezone = "Australia/Melbourne"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 61

    settings.fin.currencies["AUD"] = "Australian Dollars"
    settings.fin.currency_default = "AUD"

# END =========================================================================
