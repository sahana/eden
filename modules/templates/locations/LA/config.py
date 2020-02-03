# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Laos
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/LA")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("LA")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["lo"] = "Lao"
    settings.L10n.languages["fr"] = "French"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "lo"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Vientiane"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 856

    settings.fin.currencies["LAK"] = "Kip"
    settings.fin.currency_default = "LAK"

# END =========================================================================
