# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# Below is an example which you can base your own template's menus.py on
# - there are also other examples in the other templates folders

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """
        Custom Application Main Menu:

        The main menu consists of several sub-menus, each of which can
        be customised separately as a method of this class. The overall
        composition of the menu is defined in the menu() method, which can
        be customised as well:

        Function        Sub-Menu                Access to (standard)

        menu_modules()  the modules menu        the Eden modules
        menu_gis()      the GIS menu            GIS configurations
        menu_admin()    the Admin menu          System/User Administration
        menu_lang()     the Language menu       Selection of the GUI locale
        menu_auth()     the User menu           Login, Logout, User Profile
        menu_help()     the Help menu           Contact page, About page

        The standard uses the MM layout class for main menu items - but you
        can of course use a custom layout class which you define in layouts.py.

        Additional sub-menus can simply be defined as additional functions in
        this class, and then be included in the menu() method.

        Each sub-menu function returns a list of menu items, only the menu()
        function must return a layout class instance.
    """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):
        """ Compose Menu """

        main_menu = MMO()(

            # Modules-menu, align-left
            MM()(
                HM(),
                cls.menu_modules(),
            ),

            # Service menus, align-right
            MM(right=True)(
                cls.menu_auth(),
                cls.menu_lang(),
            ),
        )
        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        T = current.T

        project_filter = {"sector.name" : "None,Project"}
        deployment_filter = {"sector.name" : "None,Deployment"}

        return [
            MM("Contributors", c="pr", f="person",
                icon="icon-news"),
            MM("Deployments", c="project", f="project",
                icon="icon-check",
                vars=deployment_filter),
            MM("Projects", c="project", f="project",
                icon="icon-project",
                vars=project_filter),
            MM("Tasks", c="project", f="task",
                icon="icon-pencil"),
            MM("Disaster Organisations", c="org", f="organisation",
                icon="icon-globe"),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """ Auth Menu """

        auth = current.auth
        logged_in = auth.is_logged_in()
        menu_auth = None

        if not logged_in:
            request = current.request
            
            if request.controller == "default" and request.function == "user" \
                or "login" in request.args:
                pass
            else:
                # Dropdown Login Form
                menu_auth = ML() 
        else:
            # Logged-in
            user = auth.user
            options =[MM("Edit Profile", c="pr", f="person",
                         args=[user.id],
                         icon="icon-edit"),
                      MM(user.email, c="default", f="user", m="profile",
                         icon="icon-user"),
                      MM("Notification Settings", c="default", f="index", 
                         m="subscriptions",
                         icon="icon-envelope"),
                      MM("Change Password", c="default", f="user", 
                         m="change_password",
                         icon="icon-lock"),
                      MM("Logout", c="default", f="user", m="logout",
                         icon="icon-off"),
                      ]
            if auth.s3_has_role("ADMIN"):
                options.insert(0, MM("Admin", c="admin", f="user",
                                     icon="icon-cogs"))
                options.insert(1, SEP())
            menu_auth = MM("",icon="icon-cog")(*options)
        
        return menu_auth

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls, **attr):
        """ Language Menu """

        settings = current.deployment_settings
        if not settings.get_L10n_display_toolbar():
            return None

        s3 = current.response.s3
        languages = s3.l10n_languages
        lang = s3.language
        request = current.request

        menu_lang = MM("",icon="icon-comment-alt", **attr)
        for language in languages:
            menu_lang.append(MM(languages[language], r=request,
                                translate=False,
                                vars={"_language": language},
                                ltr=True,
                                icon="icon-check" if language == lang else "icon-check-empty"
                                ))
        return menu_lang

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """
        Custom Controller Menus

        The options menu (left-hand options menu) is individual for each
        controller, so each controller has its own options menu function
        in this class.

        Each of these option menu functions can be customised separately,
        by simply overriding (re-defining) the default function. The
        options menu function must return an instance of the item layout.

        The standard menu uses the M item layout class, but you can of
        course also use any other layout class which you define in
        layouts.py (can also be mixed).

        Make sure additional helper functions in this class don't match
        any current or future controller prefix (e.g. by using an
        underscore prefix).
    """

    def project(self):
        """ Project module """

        # Hide the options menu
        return None

    def org(self):
        """ Org module """

        # Hide the options menu
        return None

    def pr(self):
        """ Person Registry module """

        # Hide the options menu
        return None

# END =========================================================================
