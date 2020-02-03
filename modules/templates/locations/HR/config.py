# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Croatia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/HR")

    # Restrict to specific country/countries
    settings.gis.countries.append("HR")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["hr"] = "Croatian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "hr"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Zagreb"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 385

    settings.fin.currencies["HRK"] = "Kuna"
    settings.fin.currency_default = "HRK"

# END =========================================================================
