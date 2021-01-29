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

        is_org_group_admin = lambda i: not has_role("ADMIN") and \
                                       has_role("ORG_GROUP_ADMIN")
        menu = [MM("Organizations",
                   c = "org", f = "organisation",
                   vars = {"mine": 1} if not has_role("ORG_GROUP_ADMIN") else None,
                   restrict = ("ORG_GROUP_ADMIN", "ORG_ADMIN"),
                   ),
                MM("Test Results",
                   c = "disease", f="case_diagnostics",
                   restrict = ("VOUCHER_PROVIDER", "DISEASE_TEST_READER"),
                   ),
                MM("Projects",
                   c = "project", f="project",
                   restrict = "ADMIN",
                   ),
                MM("Find Test Station",
                   c = "org", f = "facility", m = "summary",
                   ),
                MM("Pending Approvals", c="default", f="index", args=["approve"],
                   check = is_org_group_admin,
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
    def disease():

        return M(c="disease")(
                    M("Test Results", f="case_diagnostics")(
                        M("Registrieren", m="create"),
                        M("Statistics", m="report"),
                        ),
                    M("Administration", restrict="ADMIN")(
                        M("Diseases", f="disease"),
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
                        M("Statistics", m="report", restrict=("PROGRAM_MANAGER")),
                        ),
                    M("Accepted Vouchers", f="voucher_debit")(
                        M("Accept Voucher", m="create", restrict=("VOUCHER_PROVIDER")),
                        M("Statistics", m="report"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @classmethod
    def hrm(cls):
        """ HRM / Human Resources Management """

        return cls.org()

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        org_menu = M("Organizations", f="organisation", link=False)

        auth = current.auth

        ORG_GROUP_ADMIN = auth.get_system_roles().ORG_GROUP_ADMIN
        has_role = auth.s3_has_role

        if has_role(ORG_GROUP_ADMIN):
            gtable = current.s3db.org_group
            query = (gtable.deleted == False)
            realms = auth.user.realms[ORG_GROUP_ADMIN] \
                     if not has_role("ADMIN") else None
            if realms is not None:
                query = (gtable.pe_id.belongs(realms)) & query
            groups = current.db(query).select(gtable.id,
                                              gtable.name,
                                              orderby = gtable.name,
                                              )
            for group in groups:
                org_menu(M(group.name, f="organisation",
                           vars = {"g": group.id}, translate = False,
                           ))

        org_menu(
            M("My Organizations", vars={"mine": 1}, restrict="ORG_ADMIN"),
            M("Create Organization", m="create", restrict="ORG_GROUP_ADMIN"),
            )

        return M(c="org")(
                    org_menu,
                    M("Administration", restrict=("ADMIN"))(
                        M("Facility Types", f="facility_type"),
                        M("Organization Types", f="organisation_type"),
                    #    M("Sectors", f="sector"),
                        )
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Management """

        return M(c="project") (
                    M("Projects", f="project")(
                        M("Create", m="create")
                        )
                    )

# END =========================================================================
