# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Vietnam
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/VN")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("VN")
    # Disable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["vi"] = "Vietnamese"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "vi"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Hanoi"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 84

    settings.fin.currencies["VND"] = "đồng"
    settings.fin.currency_default = "VND"

# END =========================================================================
