# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Liberia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/LR")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("LR")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    # Default timezone for users
    settings.L10n.timezone = "Africa/Monrovia"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 231

    settings.fin.currencies["LRD"] = "Liberian Dollars"
    settings.fin.currency_default = "LRD"

# END =========================================================================
