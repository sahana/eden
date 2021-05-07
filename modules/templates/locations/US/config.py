# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Canada
        - designed to be used in a Cascade with an application template
    """

    T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/US")

    # Restrict to specific country/countries
    settings.gis.countries.append("US")
    # Enable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = True

    # L10n (Localization) settings
    #settings.L10n.languages["es"] = "Spanish"
    # Default timezone for users
    settings.L10n.timezone = "US/Eastern"
    # Uncomment these to use US-style dates in English
    settings.L10n.date_format = "%m-%d-%Y"
    # Start week on Sunday
    settings.L10n.firstDOW = 0
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 1
    # Ethnicity Options
    settings.L10n.ethnicity = {"American Indian": T("American Indian"),
                               "Alaskan": T("Alaskan"),
                               "Asian": T("Asian"),
                               "African American": T("African American"),
                               "Hispanic or Latino": T("Hispanic or Latino"),
                               "Native Hawaiian": T("Native Hawaiian"),
                               "Pacific Islander": T("Pacific Islander"),
                               "Two or more": T("Two or more"),
                               "Unspecified": T("Unspecified"),
                               "White": T("White"),
                               }

    # Enable this to change the label for 'Mobile Phone'
    settings.ui.label_mobile_phone = "Cell Phone"
    # Enable this to change the label for 'Postcode'
    settings.ui.label_postcode = "ZIP Code"

    # PDF default size Letter
    settings.base.pdf_size = "Letter"

    settings.fin.currencies["USD"] = "United States Dollars"
    settings.fin.currency_default = "USD"

# END =========================================================================
