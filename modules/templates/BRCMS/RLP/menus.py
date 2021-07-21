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

        settings = current.deployment_settings

        org_registration = lambda i: settings.get_custom("org_registration")

        if has_role("EVENT_MANAGER"):
            # Organisation managing events
            menu = [MM("Affected Persons", c="br", f="person"),
                    MM("Current Needs", c="br", f="activities"),
                    MM("Relief Offers", c="br", f="offers", link=False)(
                        MM("Current Relief Offers"),
                        MM("Pending Approvals", vars={"pending": "1"}),
                        MM("Blocked Entries", vars={"blocked": 1}),
                        ),
                    ]
        elif has_role("CASE_MANAGER"):
            # Organisation managing cases
            menu = [MM("Affected Persons", c="br", f="person"),
                    MM("Relief Offers", c="br", f="offers"),
                    ]
        elif has_role("RELIEF_PROVIDER"):
            # Organisation offering relief services / supplies
            menu = [MM("Current Needs", c="br", f="activities"),
                    MM("Our Relief Offers", c="br", f="assistance_offer"),
                    ]
        else:
            # Private Citizen
            menu = [MM("Report Need", c="br", f="case_activity"),
                    MM("Find Relief Offers", c="br", f="offers"),
                    MM("Offer Assistance / Supplies", c="br", f="assistance_offer"),
                    ]

        return [menu,

                # TODO adapt label if managing only one org
                MM("Organizations", c="org", f="organisation",
                   restrict=["ORG_ADMIN", "ORG_GROUP_ADMIN"],
                   ),
                MM("Events", c="event", f="event", restrict="EVENT_MANAGER"),
                MM("Pending Approvals", c="default", f="index", args=["approve_org"],
                   restrict = "ORG_GROUP_ADMIN",
                   ),
                MM("Register", c="default", f="index", link=False,
                   check = not logged_in)(
                    MM("Private Citizen", args=["register"]),
                    MM("Organisation / Company", args=["register_org"],
                       check = org_registration,
                       ),
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
    @staticmethod
    def br():
        """ Beneficiary Registry """

        s3db = current.s3db

        labels = s3db.br_terminology()
        crud_strings = s3db.br_crud_strings("pr_person")

        f = current.request.function

        auth = current.auth
        is_event_manager = auth.s3_has_role("EVENT_MANAGER")
        org_role = is_event_manager or auth.s3_has_roles("CASE_MANAGER", "RELIEF_PROVIDER")

        if org_role:
            # Org Users: separate menus per function
            if f == "person":
                # Cases
                menu = [M(labels.CURRENT, f="person", vars={"closed": "0"},
                          restrict=("EVENT_MANAGER", "CASE_MANAGER"))(
                            M(crud_strings.label_create, m="create"),
                            )
                        ]
            elif f in ("assistance_offer", "offers", "assistance_type"):
                # Relief Offers
                menu = [M("Our Relief Offers", f="assistance_offer",
                          restrict="RELIEF_PROVIDER")(
                            M("Create", m="create"),
                            ),
                        M("Current Relief Offers", f="offers")(
                            M("Statistics", m="report"),
                            # TODO enable when implemented
                            #M("Map", m="map"),
                            ),
                        M("Approval", f="offers", link=False, restrict="EVENT_MANAGER")(
                            M("Pending Approvals", vars={"pending": "1"}),
                            M("Blocked Entries", vars={"blocked": 1}),
                            ),
                        M("Administration", link=False, restrict="ADMIN")(
                            M("Assistance Types", f="assistance_type"),
                            )
                        ]
            else:
                # Needs
                menu = [M("Current Needs", f="activities")(
                            M("Statistic", m="report"),
                            ),
                        M("Administration", link=False, restrict="ADMIN")(
                            M("Need Types", f="need"),
                            )
                        ]
        else:
            # Private Citizen: combined menu
            menu = [M("My Needs", f="case_activity")(
                        M("Report Need", m="create"),
                        M("Matching Offers", f="offers", vars={"match": "1"}),
                        M("All Relief Offers", f="offers"),
                        ),
                    M("My Relief Offers", f="assistance_offer")(
                        M("New Offer", m="create"),
                        ),
                    M("All Current Needs", f="activities")(
                        M("Statistic", m="report"),
                        ),
                    ]

        return M(c="br")(menu)

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ EVENT / Event Management """

        return M(c="event")(
                    M("Events", f="event")(
                        M("Create", m="create", restrict=("EVENT_MANAGER",)),
                        ),
                    M("Administration", restrict=("ADMIN",))(
                        M("Event Types", f="event_type"),
                        )
                    )

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
