# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Bosnia and Herzegovina
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/BA")

    # Restrict to specific country/countries
    settings.gis.countries.append("BA")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["bs"] = "Bosnian"
    settings.L10n.languages["hr"] = "Croatian"
    settings.L10n.languages["sr"] = "Serbian"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "bs"
    #settings.L10n.default_language = "hr"
    #settings.L10n.default_language = "sr"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Sarajevo"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 387

    settings.fin.currencies["BAM"] = "Convertible Marks"
    settings.fin.currency_default = "BAM"

# END =========================================================================
