# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Syria
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/SY")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("SY")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["ar"] = "Arabic"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ar"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Damascus"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 963

    settings.fin.currencies["SYP"] = "Syrian Pound"
    settings.fin.currency_default = "SYP"

# END =========================================================================
