# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Iraq
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/IQ")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("IQ")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["ar"] = "Arabic"
    settings.L10n.languages["ku"] = "Kurdish"
    settings.L10n.languages["mid"] = "Mandaic"
    settings.L10n.languages["sdb"] = "Shabaki"
    settings.L10n.languages["fa"] = "Farsi"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ar"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Baghdad"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 964

    settings.fin.currencies["IQD"] = "Iraqi Dinar"
    settings.fin.currency_default = "IQD"

# END =========================================================================
