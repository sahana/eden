# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from s3layouts import *
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
        """ Modules Menu """

        auth = current.auth

        return [MM("Volunteers", c="vol", f="volunteer"),
                MM("Recruitment", c="hrm", f="delegation"),
                MM("More", link=None)(
                    MM("Organizations", c="org", f="organisation"),
                    )
                ]

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
            menu_lang(
                ML(lang_name,
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
        settings = current.deployment_settings

        ADMIN = current.auth.get_system_roles().ADMIN

        if not auth.is_logged_in():
            request = current.request
            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            self_registration = settings.get_security_self_registration()
            menu_personal = MP()(
                        MP("Register", c="default", f="user",
                           m = "register",
                           check = self_registration,
                           ),
                        MP("Login", c="default", f="user",
                           m = "login",
                           vars = {"_next": login_next},
                           ),
                        )
            if settings.get_auth_password_retrieval():
                menu_personal(MP("Lost Password", c="default", f="user",
                                 m = "retrieve_password",
                                 ),
                              )
        else:
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

        ADMIN = current.auth.get_system_roles().ADMIN

        menu_about = MA(c="default")(
            MA("Help", f="help"),
            #MA("Contact", f="contact"),
            MA("Version", f="about", restrict = ADMIN),
        )
        return menu_about

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        sysroles = current.auth.get_system_roles()

        ADMIN = sysroles.ADMIN
        ORG_GROUP_ADMIN = sysroles.ORG_GROUP_ADMIN

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        #M("Hierarchy", m="hierarchy"),
                        M("Create", m="create", restrict=(ADMIN, ORG_GROUP_ADMIN)),
                        ),
                    #M("Administration", restrict=(ADMIN, ORG_GROUP_ADMIN))(
                    #    M("Facility Types", f="facility_type"),
                    #    M("Organization Types", f="organisation_type"),
                    #    M("Sectors", f="sector"),
                    #    )
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM / Human Resources Management """

        # TODO remove

        settings = current.deployment_settings

        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams

        return M(c="hrm")(
                    M(settings.get_hrm_staff_label(), f="staff")(
                        M("Create", m="create"),
                        ),
                    M(teams, f="group", check=use_teams)(
                        M("Create", m="create"),
                        ),
                    M("Job Titles", f="job_title")(
                        M("Create", m="create"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def vol():
        """ VOL / Volunteer Management """

        return M(c="vol")(
                    M("Volunteers", f="person")(
                        M("Create", m="create"),
                        ),
                    M("Administration", link=False)(
                        M("Occupation Types", c="pr", f="occupation_type"),
                        M("Skill Types", c="hrm", f="skill"),
                        M("Competency Levels", c="hrm", f="competency_rating"),
                        )
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project/Task Management """

        return M(c="project", f="task")(
                    M("Tasks", f="task")(
                        M("Create", m="create"),
                        M("My Open Tasks", vars={"mine":1}),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def req():

        return M(c="req", f="need")(
                M("Recruitment", link=False)(
                    M("Open Requests", f="need"),
                    M("Assigned Staff", f="need"),
                    )
                )

# END =========================================================================
