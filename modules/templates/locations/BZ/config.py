# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Belize
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/BZ")

    # Restrict to specific country/countries
    settings.gis.countries.append("BZ")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    settings.L10n.languages["bzj"] = "Kriol"
    settings.L10n.languages["kek"] = "Q'eqchi'"
    settings.L10n.languages["mop"] = "Mopan"
    settings.L10n.languages["yua"] = "Yucatec Maya"
    settings.L10n.languages["de"] = "German"
    settings.L10n.languages["cab"] = "Garifuna"
    settings.L10n.languages["zh"] = "Chinese"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/Belize"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 501

    settings.fin.currencies["BZD"] = "Belize Dollars"
    settings.fin.currency_default = "BZD"

# END =========================================================================
