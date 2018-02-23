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

        main_menu = MM()(

            cls.menu_modules(),
            cls.menu_lang(right=True),
            cls.menu_auth(),
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
            MM("Home", c="default", f="index"),
            MM("Contributors", c="pr", f="person"),
            MM("Deployments", c="project", f="project",
               vars=deployment_filter,
               tags="deployment"),
            MM("Projects", c="project", f="project",
               vars=project_filter,
               tags="project"),
            MM("Tasks", c="project", f="task"),
            MM("Disaster Organisations", c="org", f="organisation"),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """ Auth Menu """

        auth = current.auth
        user_id = auth.s3_logged_in_person()
        menu_auth = None

        if not user_id:
            menu_auth = MM("Login", c="default", f="user", m="login", right=True)
        else:
            # Logged-in
            user = auth.user
            options =[MM("Edit Profile", c="pr", f="person", args=[user_id]),
                      MM("Details", c="default", f="user", m="profile"),
                      MM("Notification Settings", c="default", f="index",
                         m="subscriptions"),
                      MM("Change Password", c="default", f="user",
                         m="change_password"),
                      MM("Logout", c="default", f="user", m="logout"),
                      ]
            if auth.s3_has_role("ADMIN"):
                options.insert(0, MM("Admin", c="admin", f="user"))
                options.insert(1, SEP())
            menu_auth = MM(user.email, right=True)(*options)
        return menu_auth

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
        """ Project Options Menu """

        project_filter = {"sector.name" : "None,Project"}
        return M(c="project")(
                   M("Projects", c="project", f="project", vars=project_filter)(
                       M("Create", m="create"),
                       M("Map", m="map", vars=project_filter),
                       M("Import", m="import"),
                    ),
                )

    def task(self):
        """ Task Options Menu """

        return M(c="project")(
                   M("Tasks", f="task")(
                       M("Create", m="create"),
                       M("Import", m="import"),
                   ),
                )

    def deployment(self):
        """ Deployments Options Menu """

        deployment_filter = {"sector.name" : "None,Deployment"}
        return M(c="project")(
                   M("Deployments", c="project", f="project", vars=deployment_filter)(
                       M("Create", m="create", vars=deployment_filter),
                       M("Map", m="map", vars=deployment_filter),
                       M("Import", m="import"),
                   ),
                )

# END =========================================================================
