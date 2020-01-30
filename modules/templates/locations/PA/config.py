# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Panama
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/PA")

    # Restrict to specific country/countries
    settings.gis.countries.append("PA")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/Panama"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 507

    settings.fin.currencies["PAB"] = "Balboa"
    settings.fin.currencies["USD"] = "United States Dollars"
    settings.fin.currency_default = "PAB"

# END =========================================================================
