# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Peru
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/PE")

    # Restrict to specific country/countries
    settings.gis.countries.append("PE")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    settings.L10n.languages["ay"] = "Aymara"
    settings.L10n.languages["qu"] = "Quechua"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/Lima"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 51

    settings.fin.currencies["PEN"] = "Sol"
    settings.fin.currency_default = "PEN"

# END =========================================================================
