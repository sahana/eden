# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Armenia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/AM")

    # Restrict to specific country/countries
    settings.gis.countries.append("AM")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["hy"] = "Armenian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "hy"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Yerevan"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 374

    settings.fin.currencies["AMD"] = "Dram"
    settings.fin.currency_default = "AMD"

# END =========================================================================
