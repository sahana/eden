# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Madagascar
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/MG")

    # Restrict to specific country/countries
    settings.gis.countries.append("MG")
    # Dosable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["mg"] = "Malagasy"
    settings.L10n.languages["fr"] = "French"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "mg"
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.timezone = "Indian/Antananarivo"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 261

    settings.fin.currencies["MGA"] = "Malagasy Ariary"
    settings.fin.currency_default = "MGA"

# END =========================================================================
