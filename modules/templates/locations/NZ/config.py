# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for New Zealand
        - designed to be used in a Cascade with an application template
    """

    T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations.NZ")

    # L10n (Localization) settings
    settings.L10n.languages = {"en-gb": "English",
                               }
    # Default Language
    settings.L10n.default_language = "en-gb"
    # Default timezone for users
    settings.L10n.utc_offset = "+1200"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 64

    settings.fin.currencies = {
        #"EUR" : T("Euros"),
        #"GBP" : T("Great British Pounds"),
        "NZD" : T("New Zealand Dollars"),
        #"USD" : T("United States Dollars"),
    }
    settings.fin.currency_default = "NZD"

    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False

# END =========================================================================
