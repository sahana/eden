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
        #current.menu.about = cls.menu_about()
        current.menu.org = cls.menu_org()

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        menu= [MM("", c="default", f="index", icon="home"),
               MM("Needs", c="req", f="need_line", m="summary")(
                #MM("Statistics",  m="report"),
                #MM("Map", m="map"),
                MM("View", c="req", f="need_line", m="summary"),
                MM("Create", c="req", f="need", m="create", p="read"),
                MM("Dashboard", c="req", f="need_line", m="map"),
                ),
               MM("4W", c="req", f="need_response_line", m="summary")(
                #MM("Statistics",  m="report"),
                #MM("Map", m="map"),
                MM("View", c="req", f="need_response_line", m="summary"),
                MM("Create", c="req", f="need_response", m="create", p="read"),
                MM("Dashboard", c="req", f="need_response_line", m="map"),
                ),
               MM("Situational Updates", c="event", f="sitrep", m="summary"),
               MM("Organizations", c="org", f="organisation", m="summary")(
                #MM("Offices", c="org", f="office"),
                MM("Facilities", c="org", f="facility", m="summary"),
               ),
               MM("About", c="default", f="about"),
               MM("Help", c="default", f="help"),
               MM("More", link=False,
                  check = current.auth.s3_logged_in())(
                MM("HCT Coordination Folders", c="pr", f="forum", args=[1, "post", "datalist"]),
                MM("Documents", c="doc", f="document"),
                MM("Disasters", c="event", f="event"),
                MM("Items", c="supply", f="item"),
                MM("Sectors", c="org", f="sector"), #,check = current.auth.s3_logged_in()
                #MM("Services", c="org", f="service"),
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
        s3 = current.response.s3
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
    def event():
        """ Events Module """

        if current.request.function == "sitrep":
            #return M()(
            #            M("Situational Updates", c="event", f="sitrep")(
            #                M("Create", m="create"),
            #            ),
            #        )
            return None
        else:
            ADMIN = current.session.s3.system_roles.ADMIN
            if ADMIN:
                return M()(M("Disasters", c="event", f="event")(
                            M("Create", m="create"),
                            ),
                           M("Disaster Types", c="event", f="event_type")(
                            #restrict=[ADMIN])(
                            M("Create", m="create"),
                            ),
                           )
            else:
                return None

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ Organisation Registry """

        #ADMIN = current.session.s3.system_roles.ADMIN

        #return M(c="org")(
        #            M("Organizations", f="organisation")(
        #                M("Create", m="create"),
        #                #M("Import", m="import")
        #            ),
        #            M("Offices", f="office")(
        #                M("Create", m="create"),
        #                M("Map", m="map"),
        #                #M("Import", m="import")
        #            ),
        #            M("Facilities", f="facility")(
        #                M("Create", m="create"),
        #                #M("Import", m="import"),
        #            ),
        #            M("Organization Types", f="organisation_type",
        #              restrict=[ADMIN])(
        #                M("Create", m="create"),
        #            ),
        #            M("Office Types", f="office_type",
        #              restrict=[ADMIN])(
        #                M("Create", m="create"),
        #            ),
        #            M("Facility Types", f="facility_type",
        #              restrict=[ADMIN])(
        #                M("Create", m="create"),
        #            ),
        #            M("Sectors", f="sector", restrict=[ADMIN])(
        #                M("Create", m="create"),
        #            ),
        #            #M("Services", f="service", restrict=[ADMIN])(
        #            #    M("Create", m="create"),
        #            #),
        #        )

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def pr():
        """ Person Registry """

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ Project Module """

        #ADMIN = current.session.s3.system_roles.ADMIN

        #return M()(
        #            M("Activities", c="project", f="activity", m="summary")(
        #                M("Create", m="create"),
        #                #M("Statistics", m="report"),
        #                #M("Map", m="map"),
        #                #M("Import", m="import", p="create"),
        #            ),
        #        )

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ Requests Management """

        #ADMIN = current.session.s3.system_roles.ADMIN

        #return M(c="req")(
        #            M("Needs", f="need", m="summary")(
        #                M("Create", m="create"),
        #                #M("Statistics", m="report"),
        #                #M("Map", m="map"),
        #                #M("Import", m="import", p="create"),
        #            ),
        #        )

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def supply():
        """ Supply Management """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="supply")(
                    M("Items", c="supply", f="item")(
                        M("Create", m="create"),
                        M("Report", m="report"),
                        M("Import", m="import", p="create"),
                    ),
                    # Catalog Items moved to be next to the Item Categories
                    #M("Catalog Items", c="supply", f="catalog_item")(
                       #M("Create", m="create"),
                    #),
                    #M("Catalogs", c="supply", f="catalog")(
                    #    M("Create", m="create"),
                    #),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                )

# END =========================================================================
