# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Bangladesh
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/BD")

    # Restrict to specific country/countries
    settings.gis.countries.append("BD")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["bn"] = "Bengali"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "bn"
    # Default timezone for users
    settings.L10n.timezone = "Asia/Dhaka"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 880

    settings.fin.currencies["BDT"] = "Bangladeshi Taka"
    settings.fin.currency_default = "BDT"

# END =========================================================================
