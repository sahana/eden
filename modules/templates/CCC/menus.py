# -*- coding: utf-8 -*-

from gluon import current, URL
from s3 import IS_ISO639_2_LANGUAGE_CODE
from s3layouts import MM
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """ Custom Application Main Menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):
        """ Compose Menu """

        # Modules menus
        main_menu = MM()(
            cls.menu_modules(),
        )

        # Additional menus
        current.menu.personal = cls.menu_personal()
        current.menu.lang = cls.menu_lang()
        current.menu.about = cls.menu_about()
        current.menu.org = cls.menu_org()

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        menu = [MM("Volunteer Your Time", c="default", f="index", args="volunteer",
                   ),
                MM("Donate Items", c="default", f="index", args="donate",
                   ),
                ]

        auth = current.auth
        if auth.is_logged_in():
            menu.append(MM("General Information and Advice", c="cms", f="post", m="datalist"))

        if auth.s3_has_role("ADMIN"):
            menu += [MM("Events", c="req", f="req",
                        ),
                     MM("All Documents", c="doc", f="document", m="datalist",
                        ),
                     ]
        elif auth.s3_has_role("VOLUNTEER"):
            menu += [MM("Organisation Documents", c="doc", f="document", m="datalist",
                        ),
                     MM("Events", c="hrm", f="training_event",
                        ),
                     MM("Volunteer Opportunities", c="req", f="req",
                        ),
                     MM("Contact Organisation Admins", c="project", f="task", m="create",
                        ),
                     ]
        elif auth.s3_has_role("ORG_ADMIN"):
            menu += [MM("Organisation Documents", c="doc", f="document", m="datalist",
                        ),
                     MM("Volunteers", c="hrm", f="human_resource",
                        ),
                     MM("Events", c="hrm", f="training_event",
                        ),
                     MM("Volunteer Opportunities", c="req", f="req",
                        ),
                     MM("Messages", c="project", f="task",
                        ),
                     ]

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Organisation Logo and Name """

        OM = S3OrgMenuLayout
        return OM()

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls):
        """ Language Selector """

        languages = current.deployment_settings.get_L10n_languages()
        represent_local = IS_ISO639_2_LANGUAGE_CODE.represent_local

        menu_lang = ML("Language", right=True)

        for code in languages:
            # Show each language name in its own language
            lang_name = represent_local(code)
            menu_lang(ML(lang_name,
                         translate = False,
                         lang_code = code,
                         lang_name = lang_name,
                         )
                      )

        return menu_lang

    # -------------------------------------------------------------------------
    @classmethod
    def menu_personal(cls):
        """ Personal Menu """

        auth = current.auth
        #s3 = current.response.s3
        #settings = current.deployment_settings

        if not auth.is_logged_in():
            request = current.request
            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            #self_registration = settings.get_security_self_registration()
            menu_personal = MP()(
                        #MP("Register", c="default", f="user",
                        #   m = "register",
                        #   check = self_registration,
                        #   ),
                        MP("Login", c="default", f="user",
                           m = "login",
                           vars = {"_next": login_next},
                           ),
                        )
            #if settings.get_auth_password_retrieval():
            #    menu_personal(MP("Lost Password", c="default", f="user",
            #                     m = "retrieve_password",
            #                     ),
            #                  )
        else:
            ADMIN = current.auth.get_system_roles().ADMIN
            s3_has_role = auth.s3_has_role
            is_org_admin = lambda i: not s3_has_role(ADMIN) and \
                                     s3_has_role("ORG_ADMIN")
            menu_personal = MP()(
                        MP("Administration", c="admin", f="index",
                           restrict = ADMIN,
                           ),
                        MP("Administration", c="admin", f="user",
                           check = is_org_admin,
                           ),
                        MP("Profile", c="default", f="person"),
                        MP("Change Password", c="default", f="user",
                           m = "change_password",
                           ),
                        MP("Logout", c="default", f="user",
                           m = "logout",
                           ),
            )
        return menu_personal

    # -------------------------------------------------------------------------
    @classmethod
    def menu_about(cls):

        #ADMIN = current.auth.get_system_roles().ADMIN

        menu_about = MA(c="default")(
            MA("Help", f="help"),
            MA("Contact Us", f="contact"),
            #MA("Version", f="about", restrict = ADMIN),
        )
        return menu_about

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def cms():
        """ No Side Menu """

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def doc():
        """ No Side Menu """

        return None

# END =========================================================================
