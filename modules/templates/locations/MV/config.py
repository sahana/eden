# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Maldives
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/MV")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("MV")

    # L10n (Localization) settings
    settings.L10n.languages["dv"] = "ދިވެހި"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "dv"
    # Default timezone for users
    settings.L10n.utc_offset = "+0500"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 960

    settings.fin.currencies["MVR"] = "Maldivian Rufiyaa"
    settings.fin.currency_default = "MVR"

# END =========================================================================
