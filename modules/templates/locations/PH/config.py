# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Philippines
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/PH")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("PH")

    # L10n (Localization) settings
    settings.L10n.languages["tl"] = "Tagalog"
    # Default Language
    settings.L10n.default_language = "tl"
    # Default timezone for users
    settings.L10n.utc_offset = "+0800"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 63

    settings.fin.currencies["PHP"] = "Philippine Pesos"
    settings.fin.currency_default = "PHP"

# END =========================================================================
