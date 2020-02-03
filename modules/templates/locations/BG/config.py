# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Bulgaria
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/BG")

    # Restrict to specific country/countries
    settings.gis.countries.append("BG")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["bg"] = "Bulgarian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "bg"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Sofia"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 359

    settings.fin.currencies["BGN"] = "Lev"
    settings.fin.currency_default = "BGN"

# END =========================================================================
