# -*- coding: utf-8 -*-

def config(settings):
    """
        Template settings for New Zealand
        - designed to be used in a Cascade with an application template
    """

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

    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False

# END =========================================================================
