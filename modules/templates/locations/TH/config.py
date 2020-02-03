# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Thailand
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/TH")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("TH")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["th"] = "Thai"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "th"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Bangkok"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 66

    settings.fin.currencies["THB"] = "Baht"
    settings.fin.currency_default = "THB"

# END =========================================================================
