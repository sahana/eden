# -*- coding: utf-8 -*-

from gluon import current, URL
#from s3 import IS_ISO639_2_LANGUAGE_CODE
from s3layouts import M, MM
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
        #current.menu.lang = cls.menu_lang()
        current.menu.about = cls.menu_about()

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        if not current.auth.is_logged_in():
            return None

        shelter_id = current.session.s3.shelter_id

        if shelter_id:
            menu = [MM("My Shelter", c="cr", f="shelter", args=[shelter_id])(
                       MM("All Shelters", c="cr", f="shelter", m="summary"),
                       ),
                    MM("My Staff", c="cr", f="shelter", args=[shelter_id, "human_resource_site"])(
                       MM("Check-In", c="cr", f="shelter", args=[shelter_id, "human_resource_site", "create"]),
                       MM("All Staff", c="hrm", f="human_resource"),
                       ),
                    MM("My Clients", c="cr", f="shelter", args=[shelter_id, "client"])(
                       MM("Check-In", c="cr", f="shelter", args=[shelter_id, "client", "create"]),
                       MM("All Clients", c="pr", f="person", m="summary"),
                       MM("Import", m="import"),
                       ),
                    ]
        else:
            menu = [MM("Shelters", c="cr", f="shelter", m="summary"),
                    MM("Staff", c="hrm", f="human_resource")(),
                    MM("Clients", c="pr", f="person", m="summary")(
                       MM("Import", m="import"),
                       ),
                    ]

        return menu

    # -------------------------------------------------------------------------
    #@classmethod
    #def menu_lang(cls):
    #    """ Language Selector """

    #    languages = current.deployment_settings.get_L10n_languages()
    #    represent_local = IS_ISO639_2_LANGUAGE_CODE.represent_local

    #    menu_lang = ML("Language", right=True)

    #    for code in languages:
    #        # Show each language name in its own language
    #        lang_name = represent_local(code)
    #        menu_lang(ML(lang_name,
    #                     translate = False,
    #                     lang_code = code,
    #                     lang_name = lang_name,
    #                     )
    #                  )

    #    return menu_lang

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
    def admin(self):
        """ ADMIN menu """

        if not current.auth.s3_has_role("ADMIN"):
            # OrgAdmin: No Side-menu
            return None

        #settings_messaging = self.settings_messaging()

        #settings = current.deployment_settings
        #consent_tracking = lambda i: settings.get_auth_consent_tracking()
        #is_data_repository = lambda i: settings.get_sync_data_repository()
        #translate = settings.has_module("translate")

        # NB: Do not specify a controller for the main menu to allow
        #     re-use of this menu by other controllers
        return M()(
                    #M("Setup", c="setup", f="deployment")(
                    #    #M("Create", m="create"),
                    #    #M("Servers", f="server")(
                    #    #),
                    #    #M("Instances", f="instance")(
                    #    #),
                    #),
                    #M("Settings", c="admin", f="setting")(
                    #    settings_messaging,
                    #),
                    M("User Management", c="admin", f="user")(
                        M("Create User", m="create"),
                        M("List All Users"),
                        M("Import Users", m="import"),
                        M("List All Roles", f="role"),
                        #M("List All Organization Approvers & Whitelists", f="organisation"),
                        #M("Roles", f="group"),
                        #M("Membership", f="membership"),
                    ),
                    #M("Consent Tracking", c="admin", link=False, check=consent_tracking)(
                    M("Consent Tracking", c="admin", link=False)(
                        M("Processing Types", f="processing_type"),
                        M("Consent Options", f="consent_option"),
                        ),
                    #M("Goods / Services", c="supply", f="item")(),
                    #M("Qualifications", c="hrm", f="certificate")(),
                    M("Organizations", c="org", f="organisation")(
                        #M("Types", f="organisation_type"),
                        #M("Job Titles", c="hrm", f="job_title"),
                        ),
                    #M("Time Slots", c="pr", f="slot")(),
                    #M("Volunteer Offers", c="hrm", f="skill")(),
                    #M("CMS", c="cms", f="post")(
                    #),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Error Tickets", c="admin", f="errors"),
                    #M("Monitoring", c="setup", f="server")(
                    #    M("Checks", f="monitor_check"),
                    #    M("Servers", f="server"),
                    #    M("Tasks", f="monitor_task"),
                    #    M("Logs", f="monitor_run"),
                    #),
                    M("Scheduler", c="admin", f="task"),
                    #M("Synchronization", c="sync", f="index")(
                    #    M("Settings", f="config", args=[1], m="update"),
                    #    M("Repositories", f="repository"),
                    #    M("Public Data Sets", f="dataset", check=is_data_repository),
                    #    M("Log", f="log"),
                    #),
                    #M("Edit Application", a="admin", c="default", f="design",
                      #args=[request.application]),
                    #M("Translation", c="admin", f="translate", check=translate)(
                    #   M("Select Modules for translation", c="admin", f="translate",
                    #     m="create", vars=dict(opt="1")),
                    #   M("Upload translated files", c="admin", f="translate",
                    #     m="create", vars=dict(opt="2")),
                    #   M("View Translation Percentage", c="admin", f="translate",
                    #     m="create", vars=dict(opt="3")),
                    #   M("Add strings manually", c="admin", f="translate",
                    #     m="create", vars=dict(opt="4"))
                    #),
                    #M("View Test Result Reports", c="admin", f="result"),
                    #M("Portable App", c="admin", f="portable")
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def br():
        """ No Side Menu """

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def cms():
        """ No Side Menu """

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def cr():
        """ No Side Menu """

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def doc():
        """ No Side Menu """

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ No Side Menu """

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ No Side Menu """

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def pr():
        """ No Side Menu """

        return None

# END =========================================================================
