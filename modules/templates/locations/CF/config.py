# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Central African Republic
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/CF")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("CF")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["fr"] = "French"
    settings.L10n.languages["sg"] = "Sango"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fr"
    #settings.L10n.default_language = "sg"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Bangui"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 236

    settings.fin.currencies["BIF"] = "Burundian Francs"
    settings.fin.currency_default = "BIF"

# END =========================================================================
