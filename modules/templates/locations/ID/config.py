# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Indonesia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/ID")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("ID")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["id"] = "Indonesian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "id"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Jakarta"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 62

    settings.fin.currencies["IDR"] = "Indonesian Rupiah"
    settings.fin.currency_default = "IDR"

# END =========================================================================
