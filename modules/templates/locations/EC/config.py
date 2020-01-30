# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Ecuador
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/EC")

    # Restrict to specific country/countries
    settings.gis.countries.append("EC")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    settings.L10n.languages["qug"] = "Kichwa" # Chimborazo Highland
    settings.L10n.languages["jiv"] = "Shuar"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/Guayaquil"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 593

    settings.fin.currencies["USD"] = "United States Dollar"
    settings.fin.currency_default = "USD"

# END =========================================================================
