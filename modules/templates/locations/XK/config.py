# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Kosovo
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/XK")

    # Restrict to specific country/countries
    settings.gis.countries.append("XK")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["sq"] = "Albanian"
    settings.L10n.languages["bs"] = "Bosnian"
    settings.L10n.languages["rom"] = "Romani"
    settings.L10n.languages["sr"] = "Serbian"
    settings.L10n.languages["tr"] = "Turkish"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "sq"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Belgrade"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 383

    settings.fin.currencies["EUR"] = "Euros"
    settings.fin.currency_default = "EUR"

# END =========================================================================
