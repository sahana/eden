# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Maldives
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/MV")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("MV")
    # Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["dv"] = "Divehi"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "dv"
    # Default timezone for users
    settings.L10n.timezone = "Indian/Maldives"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 960

    settings.fin.currencies["MVR"] = "Maldivian Rufiyaa"
    settings.fin.currency_default = "MVR"

# END =========================================================================
