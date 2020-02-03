# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Sierra Leone
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/SL")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("SL")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    # Default timezone for users
    settings.L10n.timezone = "Africa/Freetown"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 232

    settings.fin.currencies["SLL"] = "Leones"
    settings.fin.currency_default = "SLL"

# END =========================================================================
