# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Brazil
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/BR")

    # Restrict to specific country/countries
    settings.gis.countries.append("BR")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["pt-br"] = "Portuguese"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "pt-br"
    # Default timezone for users
    settings.L10n.timezone = "America/Sao_Paulo"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 55

    settings.fin.currencies["BRL"] = "Real"
    settings.fin.currency_default = "BRL"

# END =========================================================================
