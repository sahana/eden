# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Cameroon
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/CM")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("CM")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["fr"] = "French"
    settings.L10n.languages["wes"] = "Cameroonian Pidgin English"
    settings.L10n.languages["ff"] = "Fula"
    settings.L10n.languages["ewo"] = "Ewondo"
    #settings.L10n.languages[""] = "Camfranglais"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fr"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Douala"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 237

    settings.fin.currencies["XAF"] = "Central African CFA Francs"
    settings.fin.currency_default = "XAF"

# END =========================================================================
