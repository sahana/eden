# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Fiji
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/FJ")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("FJ")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["fj"] = "Fijian"
    settings.L10n.languages["hif"] = "Fiji Hindi"
    settings.L10n.languages["rtm"] = "Rotuman"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "fj"
    # Default timezone for users
    settings.L10n.timezone = "Pacific/Fiji"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 679

    settings.fin.currencies["FJD"] = "Fijian Dollar"
    settings.fin.currency_default = "FJD"

# END =========================================================================
