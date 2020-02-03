# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for North Macedonia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/MK")

    # Restrict to specific country/countries
    settings.gis.countries.append("MK")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["mk"] = "Macedonian"
    settings.L10n.languages["sq"] = "Albanian"
    settings.L10n.languages["rup"] = "Aromanian"
    settings.L10n.languages["bs"] = "Bosnian"
    settings.L10n.languages["rom"] = "Romani"
    settings.L10n.languages["sr"] = "Serbian"
    settings.L10n.languages["tr"] = "Turkish"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "mk"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Skopje"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 389

    settings.fin.currencies["MKD"] = "Macedonian Denars"
    settings.fin.currency_default = "MKD"

# END =========================================================================
