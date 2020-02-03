# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Brunei
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/BN")

    # Restrict to specific country/countries
    settings.gis.countries.append("BN")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["ms"] = "Malay"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ms"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Brunei"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 673

    settings.fin.currencies["BND"] = "Brunei Dollars"
    settings.fin.currency_default = "BND"

# END =========================================================================
