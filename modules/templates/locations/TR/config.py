# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Turkey
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/TR")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("TR")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["tr"] = "Turkish"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "tr"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Istanbul"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 90

    settings.fin.currencies["TRY"] = "Turkish Lira"
    settings.fin.currency_default = "TRY"

# END =========================================================================
