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
    settings.L10n.languages["nso"] = "Sepedi"
    settings.L10n.languages["st"] = "Sesotho"
    settings.L10n.languages["tn"] = "Setswana"
    settings.L10n.languages["ss"] = "siSwati"
    settings.L10n.languages["ve"] = "Tshivenda"
    settings.L10n.languages["ts"] = "Xitsonga"
    settings.L10n.languages["af"] = "Afrikaans"
    settings.L10n.languages["nr"] = "isiNdebele"
    settings.L10n.languages["xh"] = "isiXhosa"
    settings.L10n.languages["zu"] = "isiZulu"
    # Default timezone for users
    settings.L10n.timezone = "Africa/Johannesburg"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 27

    settings.fin.currencies["ZAR"] = "Rand"
    settings.fin.currency_default = "ZAR"

# END =========================================================================
