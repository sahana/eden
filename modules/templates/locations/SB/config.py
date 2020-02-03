# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Solomon Islands
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/SB")

    # Restrict to specific country/countries
    settings.gis.countries.append("SB")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    # Default timezone for users
    settings.L10n.timezone = "	Pacific/Guadalcanal"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 677

    settings.fin.currencies["SBD"] = "Solomon Islands Dollar"
    settings.fin.currency_default = "SBD"

# END =========================================================================
