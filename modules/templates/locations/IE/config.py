# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Ireland
        - designed to be used in a Cascade with an application template
    """

    T = current.T

    # Pre-Populate
    #settings.base.prepopulate.append("locations/IE")

    # Restrict to specific country/countries
    settings.gis.countries.append("IE")
    # Enable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = True

    # L10n (Localization) settings
    #settings.L10n.languages["ga"] = "Irish"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Dublin"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 353
    # Enable this to change the label for 'Postcode'
    settings.ui.label_postcode = "Eircode"

    settings.fin.currencies["EUR"] = "Euros"
    settings.fin.currency_default = "EUR"

# END =========================================================================
