# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Nigeria
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/NG")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("NG")
    # Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["ha"] = "Hausa"
    settings.L10n.languages["ig"] = "Igbo"
    settings.L10n.languages["yo"] = "Yoruba"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ha"
    #settings.L10n.default_language = "ig"
    #settings.L10n.default_language = "yo"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Lagos"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 234

    settings.fin.currencies["NGN"] = "Naira"
    settings.fin.currency_default = "NGN"

# END =========================================================================
