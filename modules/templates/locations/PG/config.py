# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Papua New Guinea
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/PG")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("PG")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["ho"] = "Hiri Motu"
    settings.L10n.languages["pgz"] = "Papua New Guinean Sign Language"
    settings.L10n.languages["tpi"] = "Tok Pisin"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "tpi"
    # Default timezone for users
    settings.L10n.timezone = "Pacific/Port_Moresby"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 675

    settings.fin.currencies["PGK"] = "Papua New Guinean Kina"
    settings.fin.currency_default = "PGK"

# END =========================================================================
