# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Finland
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/FI")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("FI")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["fi"] = "Finnish"
    settings.L10n.languages["sv"] = "Swedish"
    settings.L10n.languages["smi"] = "Sámi"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fi"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Helsinki"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 358

    settings.fin.currencies["EUR"] = "Euro"
    settings.fin.currency_default = "EUR"

# END =========================================================================
