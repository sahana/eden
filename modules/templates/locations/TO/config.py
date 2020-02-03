# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Tonga
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/TO")

    # Restrict to specific country/countries
    settings.gis.countries.append("TO")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["to"] = "Tongan"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "to"
    # Default timezone for users
    settings.L10n.timezone = "Pacific/Tongatapu"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 676

    settings.fin.currencies["TOP"] = "Pa'anga"
    settings.fin.currency_default = "TOP"

# END =========================================================================
