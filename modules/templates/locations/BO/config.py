# -*- coding: utf-8 -*-

from gluon import current

def config(settings):
    """
        Template settings for Bolivia
        - designed to be used in a Cascade with an application template
    """

    #T = current.T

    # Pre-Populate
    settings.base.prepopulate.append("locations/BO")

    # Restrict to specific country/countries
    settings.gis.countries.append("BO")
    # Dosable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # L10n (Localization) settings
    settings.L10n.languages["es"] = "Spanish"
    settings.L10n.languages["ay"] = "Aymara"
    settings.L10n.languages["aro"] = "Araona"
    settings.L10n.languages["brg"] = "Bauré"
    settings.L10n.languages["cax"] = "Bésiro"
    settings.L10n.languages["caz"] = "Canichana"
    settings.L10n.languages["cav"] = "Cavineña"
    settings.L10n.languages["cyb"] = "Cayuvava"
    settings.L10n.languages["cao"] = "Chácobo"
    settings.L10n.languages["cas"] = "Chimané / Mosetén"
    settings.L10n.languages["ese"] = "Ese Ejja"
    settings.L10n.languages["gn"] = "Guarani"
    settings.L10n.languages["psm"] = "Guarasuawe"
    settings.L10n.languages["gyr"] = "Guarayu"
    settings.L10n.languages["ito"] = "Itonama"
    settings.L10n.languages["lec"] = "Leco"
    settings.L10n.languages["caw"] = "Machajuyai-Kallawaya"
    settings.L10n.languages["mpd"] = "Machineri"
    settings.L10n.languages["rey"] = "Maropa"
    settings.L10n.languages["ign"] = "Mojeño-Ignaciano"
    settings.L10n.languages["trn"] = "Mojeño-Trinitario"
    settings.L10n.languages["ite"] = "Moré"
    settings.L10n.languages["mzp"] = "Movima"
    settings.L10n.languages["pcp"] = "Pacawara"
    settings.L10n.languages["puq"] = "Puquina"
    settings.L10n.languages["qu"] = "Quechua"
    settings.L10n.languages["srq"] = "Sirionó"
    settings.L10n.languages["tna"] = "Tacana"
    #settings.L10n.languages[""] = "Tapieté"
    settings.L10n.languages["tno"] = "Toromona"
    settings.L10n.languages["cap"] = "Uru-Chipaya"
    settings.L10n.languages["mtp"] = "Weenhayek"
    settings.L10n.languages["yaa"] = "Yaminawa"
    settings.L10n.languages["yuq"] = "Yúki"
    settings.L10n.languages["yuz"] = "Yuracaré"
    settings.L10n.languages["ayo"] = "Zamuco"
    # Default Language (put this in custom template if-required)
    #settings.L10n.default_language = "es"
    # Default timezone for users
    settings.L10n.timezone = "America/La_Paz"
    # Default Country Code for telephone numbers
    settings.L10n.default_country_code = 591

    settings.fin.currencies["BOB"] = "Boliviano"
    settings.fin.currency_default = "BOB"

# END =========================================================================
