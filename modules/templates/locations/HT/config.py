# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Haiti
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/HT")

    # Restrict to specific country/countries
    settings.gis.countries.append("HT")
    # Dosable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["ht"] = "Haitian Creole"
    settings.L10n.languages["fr"] = "French"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ht"
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.timezone = "America/Port-au-Prince"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 509

    settings.fin.currencies["HTG"] = "Haitian Gourdes"
    settings.fin.currency_default = "HTG"

# END =========================================================================
