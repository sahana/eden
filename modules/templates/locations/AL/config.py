# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Albania
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/AL")

    # Restrict to specific country/countries
    settings.gis.countries.append("AL")

    # L10n (Localization) settings
    settings.L10n.languages["sq"] = "Albanian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "sq"
    # Uncomment this to Translate Location Names
    settings.L10n.translate_gis_location = True
    # Default timezone for users
    settings.L10n.timezone = "Europe/Tirane"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 355

    settings.fin.currencies["ALL"] = "Lek"
    settings.fin.currency_default = "ALL"

# END =========================================================================
