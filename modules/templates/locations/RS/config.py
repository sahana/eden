# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Serbia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/RS")

    # Restrict to specific country/countries
    settings.gis.countries.append("RS")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["sq"] = "Albanian"
    settings.L10n.languages["bs"] = "Bosnian"
    settings.L10n.languages["bg"] = "Bulgarian"
    settings.L10n.languages["hr"] = "Croatian"
    settings.L10n.languages["hu"] = "Hungarian"
    settings.L10n.languages["ro"] = "Romanian"
    settings.L10n.languages["rue"] = "Rusyn"
    settings.L10n.languages["sr"] = "Serbian"
    settings.L10n.languages["sk"] = "Slovak"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "sr"
    # Default timezone for users
    settings.L10n.timezone = "Europe/Belgrade"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 381

    settings.fin.currencies["RSD"] = "Serbian Dinars"
    settings.fin.currency_default = "RSD"

# END =========================================================================
