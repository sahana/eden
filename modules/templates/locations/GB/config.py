# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for United Kingdom
        - designed to be used in a Cascade with an application template
    """

    T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/GB")

    # Uncomment to restrict to specific country/countries
    settings.gis.countries.append("GB")

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages["en-gb"] = "English (United Kingdom)"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "en-gb"
    # Default timezone for users
    settings.L10n.timezone = "Europe/London"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 44
    # Ethnicity Options
    # https://www.ethnicity-facts-figures.service.gov.uk/style-guide/ethnic-groups
    settings.L10n.ethnicity = {"White: English, Welsh, Scottish, Northern Irish or British": T("White: English, Welsh, Scottish, Northern Irish or British"),
                               "White: Irish": T("White: Irish"),
                               "White: Gypsy or Irish Traveller": T("White: Gypsy or Irish Traveller"),
                               "White: Any other White background": T("White: Any other White background"),
                               "Mixed or Multiple ethnic groups: White and Black Caribbean": T("Mixed or Multiple ethnic groups: White and Black Caribbean"),
                               "Mixed or Multiple ethnic groups: White and Black African": T("Mixed or Multiple ethnic groups: White and Black African"),
                               "Mixed or Multiple ethnic groups: White and Asian": T("Mixed or Multiple ethnic groups: White and Asian"),
                               "Mixed or Multiple ethnic groups: Any other Mixed or Multiple ethnic background": T("Mixed or Multiple ethnic groups: Any other Mixed or Multiple ethnic background"),
                               "Asian or Asian British: Indian": T("Asian or Asian British: Indian"),
                               "Asian or Asian British: Pakistani": T("Asian or Asian British: Pakistani"),
                               "Asian or Asian British: Bangladeshi": T("Asian or Asian British: Bangladeshi"),
                               "Asian or Asian British: Chinese": T("Asian or Asian British: Chinese"),
                               "Asian or Asian British: Any other Asian background": T("Asian or Asian British: Any other Asian background"),
                               "Black, African, Caribbean or Black British: African": T("Black, African, Caribbean or Black British: African"),
                               "Black, African, Caribbean or Black British: Caribbean": T("Black, African, Caribbean or Black British: Caribbean"),
                               "Black, African, Caribbean or Black British: Any other Black, African or Caribbean background": T("Black, African, Caribbean or Black British: Any other Black, African or Caribbean background"),
                               "Other ethnic group: Arab": T("Other ethnic group: Arab"),
                               "Other ethnic group: Any other ethnic group": T("Other ethnic group: Any other ethnic group"),
                               }

    settings.fin.currencies["GBP"] = "British Pounds"
    settings.fin.currency_default = "GBP"

# END =========================================================================
