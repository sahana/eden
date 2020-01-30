# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Malaysia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/MY")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("MY")
    # Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["ms"] = "Malay"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ms"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Kuala_Lumpur"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 60

    settings.fin.currencies["MYR"] = "Ringgit"
    settings.fin.currency_default = "MYR"

# END =========================================================================
