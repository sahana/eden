# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Cook Islands
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/CK")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("CK")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["rar"] = "Cook Islands Māori"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "rar"
    # Default timezone for users
    settings.L10n.timezone = "Pacific/Rarotonga"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 682

    settings.fin.currencies["NZD"] = "New Zealand Dollars" # Cook Island Dollars are pegged
    settings.fin.currency_default = "NZD"

# END =========================================================================
