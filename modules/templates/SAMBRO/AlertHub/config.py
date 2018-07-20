# -*- coding: utf-8 -*-

from gluon import current, URL

from collections import OrderedDict

def config(settings):
    """
        Global Alerthub specific template settings for Common Alerting Protocol (CAP) and other feeds
    """

    T = current.T

    settings.base.system_name = T("Sahana Research and Action Aggregated Globally Relayed Alerts and Bulletins")
    settings.base.system_name_short = T("SaRA-GRAB")

    # Default Language
    settings.L10n.default_language = "en-US"

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "SAMBRO.AlertHub"
    settings.base.theme_base = "default"

    # L10n (Localization) settings
    languages = OrderedDict([
        ("ar-KW", "Arabic (Kuwait)"),
        ("ar-MA", "Arabic (Morocco)"),
        ("az-AZ", "Azeri (Azerbaijan)"),
        ("be-BY", "Belarusian (Belarus)"),
        ("bg-BG", "Bulgarian (Bulgaria)"),
        ("bi-VU", "Bislama (Vanuatu)"),
        ("bs-BA", "Bosnian (Bosnia and Herzegovina)"),
        ("ca-ES", "Catalan (Spain)"),
        ("cs-CZ", "Czech (Czech Republic)"),
        ("cy-GB", "Welsh (United Kingdom)"),
        ("da-DK", "Danish (Denmark)"),
        ("de-AT", "German (Austria)"),
        ("de-CH", "German (Switzerland)"),
        ("de-DE", "German (Germany)"),
        ("de-LI", "German (Liechtenstein)"),
        ("de-LU", "German (Luxembourg)"),
        ("dv-MV", "Divehi (Maldives)"),
        ("el-GR", "Greek (Greece)"),
        ("en-AU", "English (Australia)"),
        ("en-CA", "English (Canada)"),
        ("en-GB", "English (United Kingdom)"),
        ("en-NZ", "English (New Zealand)"),
        ("en-PH", "English (Republic of the Philippines)"),
        ("en-US", "English (United States)"),
        ("en-VU", "English (Vanuatu)"),
        ("es-419", "Spanish (Latin America and Caribbean region)"),
        ("es-AR", "Spanish (Argentina)"),
        ("es-EC", "Spanish (Ecuador)"),
        ("es-ES", "Spanish (Spain)"),
        ("es-GT", "Spanish (Guatemala)"),
        ("es-MX", "Spanish (Mexico)"),
        ("et-EE", "Estonian (Estonia)"),
        ("eu-ES", "Basque (Spain)"),
        ("fi-FI", "Finnish (Finland)"),
        ("fr-BE", "French (Belgium)"),
        ("fr-CA", "French (Canada)"),
        ("fr-CH", "French (Switzerland"),
        ("fr-FR", "French (France)"),
        ("fr-LU", "French (Luxembourg)"),
        ("fr-MC", "French (Principality of Monaco)"),
        ("he-IL", "Hebrew (Israel)"),
        ("hr-BA", "Croatian (Bosnia and Herzegovina)"),
        ("hr-HR", "Croatian (Croatia)"),
        ("hu-HU", "Hungarian (Hungary)"),
        ("hy-AM", "Armenian (Armenia)"),
        ("id-ID", "Indonesian (Indonesia)"),
        ("is-IS", "Icelandic (Iceland)"),
        ("it-CH", "Italian (Switzerland)"),
        ("it-IT", "Italian (Italy)"),
        ("ja-JP", "Japanese (Japan)"),
        ("ka-GE", "Georgian (Georgia)"),
        ("kk-KZ", "Kazakh (Kazakhstan)"),
        ("ky-KG", "Kyrgyz (Kyrgyzstan"),
        ("lt-LT", "Lithuanian (Lithuania)"),
        ("lv-LV", "Latvian (Latvia)"),
        ("mi-NZ", "Maori (New Zealand)"),
        ("mt-MT", "Maltese (Malta)"),
        ("nb-NO", "Norwegian (Bokm?l) (Norway)"),
        ("nl-BE", "Dutch (Belgium)"),
        ("nl-NL", "Dutch (Netherlands)"),
        ("nn-NO", "Norwegian (Nynorsk) (Norway)"),
        ("pl-PL", "Polish (Poland)"),
        ("pt-BR", "Portuguese (Brazil)"),
        ("pt-PT", "Portuguese (Portugal)"),
        ("ro-RO", "Romanian (Romania)"),
        ("se-FI", "Sami (Finland)"),
        ("se-NO", "Sami (Norway)"),
        ("se-SE", "Sami (Sweden)"),
        ("sk-SK", "Slovak (Slovakia)"),
        ("sl-SI", "Slovenian (Slovenia)"),
        ("sq-AL", "Albanian (Albania)"),
        ("sr-BA", "Serbian (Bosnia and Herzegovina)"),
        ("sr-ME", "Serbian (Montenegro)"),
        ("sr-SP", "Serbian (Serbia and Montenegro)"),
        ("sv-FI", "Swedish (Finland"),
        ("sv-SE", "Swedish (Sweden)"),
        ("th-TH", "Thai (Thailand)"),
        ("tl-PH", "Tagalog (Philippines)"),
        ("uk-UA", "Ukrainian (Ukraine)"),
        ("uz-UZ", "Uzbek (Uzbekistan)"),
        ("zh-tw", "Chinese (Taiwan)"),
    ])
    settings.L10n.languages = languages

    # for creating location from SAME geocodes
    settings.cap.same_code = "PSGC"

    # Alert Hub Title
    # NB Alert Hub is home page for Philippines
    settings.cap.alert_hub_title = T("Sahana Research and Action Aggregated Globally Relayed Alerts and Bulletins")

    # UI Settings
    settings.ui.menu_logo = URL(c = "static",
                                f = "themes",
                                args = ["SAMBRO", "AlertHub", "img", "alerthub.png"],
                                )

    # Name of Method used to create bulletin
    # This may vary according to organisation implementing it
    settings.cap.form_bulletin = "form_ocd"

# END =========================================================================
