# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for South Africa
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/ZA")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("ZA")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    languages = settings.L10n.languages
    languages["nso"] = "Sepedi"     # Northern Sotho
    languages["st"] = "Sesotho"     # Southern Sotho
    languages["tn"] = "Setswana"
    languages["ss"] = "siSwati"
    languages["ve"] = "Tshivenda"
    languages["ts"] = "Xitsonga"
    languages["af"] = "Afrikaans"
    languages["nr"] = "isiNdebele"  # Southern Ndebele
    languages["xh"] = "isiXhosa"
    languages["zu"] = "isiZulu"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Johannesburg"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 27

    settings.fin.currencies["ZAR"] = "Rand"
    settings.fin.currency_default = "ZAR"

# END =========================================================================
