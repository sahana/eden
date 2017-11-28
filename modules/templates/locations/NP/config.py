# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Nepal
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/NP")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("NP")

    # L10n (Localization) settings
    settings.L10n.languages["ne"] = "Nepali"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ne"
    # Default timezone for users
    settings.L10n.utc_offset = "+0545"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 977

    settings.fin.currencies["NPR"] = "Nepalese Rrupee"
    settings.fin.currency_default = "NPR"

# END =========================================================================
