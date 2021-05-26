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
                               "White: Any other White background": T("White: Any other White background, please describe"),
                               "Mixed/Multiple ethnic groups: White and Black Caribbean": T("Mixed/Multiple ethnic groups: White and Black Caribbean"),
                               "Mixed/Multiple ethnic groups: White and Black African": T("Mixed/Multiple ethnic groups: White and Black African"),
                               "Mixed/Multiple ethnic groups: White and Asian": T("Mixed/ Multiple ethnic groups: White and Asian"),
                               "Mixed/Multiple ethnic groups: Any other Mixed/Multiple ethnic background": T("Mixed/Multiple ethnic groups: Any other Mixed/Multiple ethnic background, please describe"),
                               "Asian/Asian British: Indian": T("Asian/Asian British: Indian"),
                               "Asian/Asian British: Pakistani": T("Asian/Asian British: Pakistani"),
                               "Asian/Asian British: Bangladeshi": T("Asian/Asian British: Bangladeshi"),
                               "Asian/Asian British: Chinese": T("Asian/Asian British: Chinese"),
                               "Asian/Asian British: Any other Asian background": T("Asian/Asian British: Any other Asian background, please describe"),
                               "Black/African/Caribbean/Black British: African": T("Black/African/Caribbean/Black British: African"),
                               "Black/African/Caribbean/Black British: Caribbean": T("Black/African/Caribbean/Black British: Caribbean"),
                               "Black/African/Caribbean/Black British: Any other Black/African/Caribbean background": T("Black/African/Caribbean/Black British: Any other Black/African/Caribbean background, please describe"),
                               "Other ethnic group: Arab": T("Other ethnic group: Arab"),
                               "Other ethnic group: Any other ethnic group": T("Other ethnic group: Any other ethnic group, please describe"),
                               }
    # Religion Options
    settings.L10n.religions = {"none": T("No religion"),
                               "christian": T("Christian (including Church of England, Catholic, Protestant and all other Christian denominations)"),
                               "buddhist": T("Buddhist"),
                               "hindu": T("Hindu"),
                               "jewish": T("Jewish"),
                               "muslim": T("Muslim"),
                               "sikh": T("Sikh"),
                               "other": T("Any other religion, please describe")
                               }

    settings.fin.currencies["GBP"] = "British Pounds"
    settings.fin.currency_default = "GBP"

# END =========================================================================
