# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Afghanistan
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/AF")

    # Restrict to specific country/countries
    settings.gis.countries.append("AF")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["prs"] = "Dari"
    settings.L10n.languages["ps"] = "Pashto"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "prs"
    #settings.L10n.default_language = "ps"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Kabul"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 93

    settings.fin.currencies["AFN"] = "Afghani"
    settings.fin.currency_default = "AFN"

# END =========================================================================
