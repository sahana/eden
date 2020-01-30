# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Nicaragua
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/NI")

    # Restrict to specific country/countries
    settings.gis.countries.append("NI")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/Managua"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 505

    settings.fin.currencies["NIO"] = "Córdoba"
    settings.fin.currency_default = "NIO"

# END =========================================================================
