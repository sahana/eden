# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Bhutan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/BT")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("BT")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["dz"] = "Dzongkha"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "dz"
    # Uncomment this to Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this to use Alternate Location Names
    settings.L10n.name_alt_gis_location = True
    # Default timezone for users
    settings.L10n.timezone = "Asia/Thimphu"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 975

    settings.fin.currencies["BTN"] = "Ngultrum"
    settings.fin.currency_default = "BTN"

# END =========================================================================
