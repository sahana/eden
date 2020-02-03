# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Georgia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/GE")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("GE")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["ka"] = "Georgian"
    settings.L10n.languages["ab"] = "Abkhaz"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "ka"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Tbilisi"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 995

    settings.fin.currencies["GEL"] = "Georgian Lari"
    settings.fin.currency_default = "GEL"

# END =========================================================================
