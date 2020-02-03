# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Costa Rica
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/CR")

    # Restrict to specific country/countries
    settings.gis.countries.append("CR")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    #settings.L10n.languages[""] = "Mekatelyu"# Limonese Creole
    settings.L10n.languages["bzd"] = "Bribri"
    settings.L10n.languages["jam"] = "Patois"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/Costa_Rica"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 506

    settings.fin.currencies["CRC"] = "Costa Rican Colón"
    settings.fin.currency_default = "CRC"

# END =========================================================================
