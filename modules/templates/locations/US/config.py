# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Canada
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/US")

    # Restrict to specific country/countries
    settings.gis.countries.append("US")
    # Enable the Postcode selector in the LocationSelector
    settings.gis.postcode_selector = True

    # L10n (Localization) settings
    #settings.L10n.languages["es"] = "Spanish"
    # Default timezone for users
    settings.L10n.utc_offset = "-0500"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 1

    settings.fin.currencies["USD"] = "United States Dollars"
    settings.fin.currency_default = "USD"

# END =========================================================================
