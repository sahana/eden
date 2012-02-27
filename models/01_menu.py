# -*- coding: utf-8 -*-

"""
    Global menus
"""

if auth.permission.format in ("html"):

    # =========================================================================
    # Application main menu
    # -> To customize, replace the standard components by the desired items
    # -> Put right-hand menu options in reverse order!
    #
    current.menu.main(

        # Standard modules-menu
        S3MainMenu.menu_modules(),

        # Custom menu (example)
        #homepage(),
        #homepage("gis"),
        #homepage("pr", restrict=[ADMIN])(
            #MM("Persons", f="person"),
            #MM("Groups", f="group")
        #),
        #MM("more", link=False)(
            #homepage("dvi"),
            #homepage("irs")
        #),

        # Standard service menus
        S3MainMenu.menu_help(right=True),
        S3MainMenu.menu_auth(right=True),
        S3MainMenu.menu_lang(right=True),
        S3MainMenu.menu_admin(right=True),
        S3MainMenu.menu_gis(right=True)
    )

    # =========================================================================
    # Custom controller menus
    #
    s3_menu_dict = {

        # Define custom controller menus here like:
        #"prefix": menu structure

    }

# END =========================================================================
