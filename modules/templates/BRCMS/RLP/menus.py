# -*- coding: utf-8 -*-

from gluon import current, URL
from s3 import IS_ISO639_2_LANGUAGE_CODE
from s3layouts import MM, M
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

        has_role = auth.s3_has_role
        logged_in = auth.s3_logged_in()
        labels = current.s3db.br_terminology()

        if has_role("EVENT_MANAGER"):
            # Organisation managing events
            menu = [MM("Current Needs", c="br", f="case_activity"),
                    MM("Relief Offers", c="br", f="assistance_offer"),
                    MM(labels.CASES, c="br", f="person"),
                    ]
        elif has_role("CASE_MANAGER"):
            # Organisation managing cases
            menu = [MM(labels.CASES, c="br", f="person"),
                    MM("Relief Offers", c="br", f="assistance_offer"),
                    ]
        elif has_role("RELIEF_PROVIDER"):
            # Organisation offering relief services / supplies
            menu = [MM("Our Relief Offers", c="br", f="assistance_offer"),
                    MM("Current Needs", c="br", f="case_activity"),
                    ]
        else:
            # Private Citizen
            menu = [MM("Get Help", c="br", f="case_activity"),
                    MM("Offer Assistance / Supplies", c="br", f="assistance_offer"),
                    ]

        return [menu,

                # TODO adapt label if managing only one org
                MM("Organizations", c="org", f="organisation",
                   restrict=["ORG_ADMIN", "ORG_GROUP_ADMIN"],
                   ),
                MM("Events", c="event", f="event", restrict="EVENT_MANAGER"),
                MM("Register", c="default", f="index", link=False,
                   check = not logged_in)(
                    MM("Private Citizen", args=["register"]),
                    MM("Organisation / Company", args=["register_org"]),
                    ),
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
    def br():
        """ Beneficiary Registry """

        # TODO split into case | needs | offers

        auth = current.auth
        has_role = auth.s3_has_role

        sysroles = auth.get_system_roles()
        ADMIN = sysroles.ADMIN
        ORG_GROUP_ADMIN = sysroles.ORG_GROUP_ADMIN

        s3db = current.s3db
        labels = s3db.br_terminology()
        crud_strings = s3db.br_crud_strings("pr_person")

        settings = current.deployment_settings
        use_activities = settings.get_br_case_activities()
        urgent_activities = use_activities and settings.get_br_case_activity_urgent_option()

        manage_assistance = settings.get_br_manage_assistance()

        menu = M(c="br")

        # Statistics sub-memnu (common for all roles)
        statistics = M("Statistics", link=False)(
                        M("Cases", f="person", m="report"),
                        M("Activities", f="case_activity", m="report", check=use_activities),
                        M("Measures", f="assistance_measure", m="report", check=manage_assistance),
                        )

        # Registry sub-menu
        human_resource_id = auth.s3_logged_in_human_resource()
        if human_resource_id and has_role("CASE_MANAGEMENT"):

            # Side menu for case managers (including "my"-sections)
            menu(M(labels.CURRENT_MINE, f="person", vars={"closed": "0", "mine": "1"})(
                    M(crud_strings.label_create, m="create"),
                    M("My Activities", f="case_activity",
                      vars={"mine": "1"}, check=use_activities,
                      ),
                    M("Emergencies", f="case_activity",
                      vars={"mine": "1", "~.priority": "0"}, check=urgent_activities
                      ),
                    ),
                 M("My Measures", f="assistance_measure",
                   vars={"mine": "1"}, check=manage_assistance)(
                    M("Calendar", m="organize", vars={"mine": "1"}),
                    ),
                 #M("Appointments"),
                 statistics,
                 M("Compilations", link=False)(
                    M("Current Cases", f="person", vars={"closed": "0"}),
                    M("All Cases", f="person"),
                    M("All Activities", f="case_activity", check=use_activities),
                    M("All Measures", f="assistance_measure", check=manage_assistance),
                    ),
                 )
        else:

            # Default side menu (without "my"-sections)
            menu(M(labels.CURRENT, f="person", vars={"closed": "0"})(
                    M(crud_strings.label_create, m="create"),
                    M("Activities", f="case_activity", check=use_activities,
                      ),
                    M("Emergencies", f="case_activity",
                      vars={"~.priority": "0"}, check=urgent_activities,
                      ),
                    ),
                 M("Measures", f="assistance_measure", check=manage_assistance)(
                    #M("Overview"),
                    ),
                 #M("Appointments"),
                 statistics,
                 M("Compilations", link=False)(
                    M("All Cases", f="person"),
                    ),
                 )

        # Archive- and Administration sub-menus (common for all roles)
        menu(M("Archive", link=False)(
                M(labels.CLOSED, f="person", vars={"closed": "1"}),
                M("Invalid Cases", f="person", vars={"invalid": "1"}, restrict=[ADMIN]),
                ),
             M("Administration", link=False, restrict=[ADMIN, ORG_GROUP_ADMIN])(
                M("Case Statuses", f="case_status"),
                M("Case Activity Statuses", f="case_activity_status",
                  check = lambda i: use_activities and settings.get_br_case_activity_status(),
                  ),
                M("Need Types", f="need",
                  check = lambda i: not settings.get_br_needs_org_specific(),
                  ),
                M("Assistance Statuses", f="assistance_status",
                  check = manage_assistance,
                  ),
                M("Assistance Types", f="assistance_type",
                  check = lambda i: manage_assistance and \
                                    settings.get_br_assistance_types(),
                  ),
                M(labels.THEMES, f="assistance_theme",
                  check = lambda i: manage_assistance and \
                                    settings.get_br_assistance_themes() and \
                                    not settings.get_br_assistance_themes_org_specific(),
                  ),
                ),
             )

        return menu

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        # TODO implement

        pass

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        sysroles = current.auth.get_system_roles()

        ADMIN = sysroles.ADMIN
        ORG_GROUP_ADMIN = sysroles.ORG_GROUP_ADMIN

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("Create", m="create", restrict=(ADMIN, ORG_GROUP_ADMIN)),
                        ),
                    M("Administration", restrict=(ADMIN, ORG_GROUP_ADMIN))(
                        M("Organization Types", f="organisation_type"),
                        M("Sectors", f="sector"),
                        )
                    )

# END =========================================================================
