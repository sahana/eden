# -*- coding: utf-8 -*-

from gluon import current
from s3 import IS_ISO639_2_LANGUAGE_CODE
from s3layouts import MM, M
try:
    from ..RLP.layouts import *
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
        has_role = auth.s3_has_role

        menu = [MM("Organizations",
                   c = "org", f = "organisation",
                   restrict = ("ORG_GROUP_ADMIN", "ORG_ADMIN"),
                   ),
                MM("Find Test Station",
                   c = "org", f = "facility", m = "summary",
                   ),
                MM("Register Test Station",
                   c = "default", f = "index", args = ["register"],
                   check = lambda i: not current.auth.s3_logged_in(),
                   ),
                ]

        # Link to voucher management
        if auth.s3_logged_in():
            f = None
            if has_role("PROGRAM_MANAGER"):
                label, f = "Voucher Programs", "voucher_program"
            elif has_role("VOUCHER_PROVIDER"):
                label, f = "Voucher Acceptance", "voucher_debit"
            elif has_role("VOUCHER_ISSUER"):
                label, f = "Voucher Issuance", "voucher"
            if f:
                menu.insert(0, MM(label, c="fin", f=f))

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Organisation Logo and Name """

        OM = S3OrgMenuLayout
        return OM()

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls, **attr):
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

        menu_about = MA(c="default")(
            MA("Help", f="help"),
            MA("Contact", f="contact"),
            MA("Privacy", f="index", args=["privacy"]),
            MA("Legal Notice", f="index", args=["legal"]),
            MA("Version", f="about", restrict = ("ORG_GROUP_ADMIN")),
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

        settings = current.deployment_settings
        consent_tracking = lambda i: settings.get_auth_consent_tracking()

        # NB: Do not specify a controller for the main menu to allow
        #     re-use of this menu by other controllers
        return M()(
                    M("User Management", c="admin", f="user")(
                        M("Create User", m="create"),
                        M("List All Users"),
                        M("Import Users", m="import"),
                        M("List All Roles", f="role"),
                    ),
                    M("Consent Tracking", c="admin", link=False, check=consent_tracking)(
                        M("Processing Types", f="processing_type"),
                        M("Consent Options", f="consent_option"),
                        ),
                    M("CMS", c="cms", f="post"),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Scheduler", c="admin", f="task"),
                    M("Error Tickets", c="admin", f="errors"),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("Create", m="create", restrict=("ORG_GROUP_ADMIN")),
                        ),
                    M("Administration", restrict=("ORG_GROUP_ADMIN"))(
                        M("Facility Types", f="facility_type"),
                    #    M("Organization Types", f="organisation_type"),
                    #    M("Sectors", f="sector"),
                        )
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def fin():
        """ FIN / Finance """

        return M(c="fin")(
                    M("Voucher Programs", f="voucher_program")(
                        M("Create", m="create", restrict=("PROGRAM_MANAGER")),
                        ),
                    M("Vouchers", f="voucher")(
                        M("Create Voucher", m="create", restrict=("VOUCHER_ISSUER")),
                        ),
                    M("Accepted Vouchers", f="voucher_debit")(
                        M("Accept Voucher", m="create", restrict=("VOUCHER_PROVIDER")),
                        ),
                    )

# END =========================================================================
