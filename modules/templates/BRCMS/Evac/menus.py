# -*- coding: utf-8 -*-

from gluon import current, URL
from s3 import IS_ISO639_2_LANGUAGE_CODE
from s3layouts import MM, M
try:
    from ..layouts import *
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

        from s3db.br import br_terminology
        labels = br_terminology()

        if current.auth.s3_has_roles(("CASE_MANAGER",
                                      "CASE_SUPER",
                                      "ORG_ADMIN",
                                      )):
            #case_vars["mine"] = "1"
            CASES = MM(labels.CASES, c="br", f="person", vars={"closed": "0"})
        else:
            CASES = MM(labels.CASES, c="br", f="case_activity")

        return [CASES,
                MM("ToDo", c="project", f="task"),
                MM("Map", c="gis", f="index"),
                MM("Working Groups", link=False)(
                    MM("Flights", c="transport", f="flight"),
                    MM("Logistics", c="fin", f="index"),
                    MM("Medical", c="med", f="index"),
                    MM("Security", c="security", f="index"),
                    MM("Organizations", c="org", f="organisation"),
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

        auth = current.auth

        if not auth.s3_has_roles(("CASE_MANAGER",
                                  "CASE_SUPER",
                                  "ORG_ADMIN",
                                  )):
            # Can only see Activities
            return M(c="br")(
                    M("My Activities", f="case_activity")(),
                    M("Emergencies", f="case_activity",
                      vars = {"~.priority": "0"},
                      )
                    )

        from s3db.br import br_crud_strings, br_terminology
        crud_strings = br_crud_strings("pr_person")
        labels = br_terminology()

        system_roles = auth.get_system_roles()
        ADMIN = system_roles.ADMIN
        ORG_ADMIN = system_roles.ORG_ADMIN

        return M(c="br")(
                M(labels.CURRENT_MINE, f="person",
                  vars = {"closed": "0", "mine": "1"},
                  )(
                    M(crud_strings.label_create, m="create", restrict=ORG_ADMIN),
                    M("Activities", f="case_activity",
                      vars = {"my_cases": "1"},
                      ),
                    M("Emergencies", f="person",
                      vars = {"closed": "0", "mine": "1", "case.priority": "0"},
                      ),
                    ),
                M("Compilations", link=False)(
                    M("Urgent Cases", f="person",
                      vars = {"closed": "0",
                              "case.priority": "0",
                              }
                      ),
                    M("Current Cases", f="person",
                      vars = {"closed": "0"},
                      ),
                    M("All Cases", f="person"),
                    M("All Activities", f="case_activity",),
                    ),
                M("Statistics", link=False)(
                    M("Cases", f="person", m="report"),
                    M("Activities", f="case_activity", m="report"),
                    ),
                M("Archive", link=False)(
                    M(labels.CLOSED, f="person",
                      vars = {"closed": "1"},
                      ),
                    M("Invalid Cases", f="person",
                      vars = {"invalid": "1"},
                      restrict = ADMIN,
                      ),
                    ),
                M("Administration", link=False, restrict=ADMIN)(
                    M("Case Statuses", f="case_status"),
                    M("Case Activity Statuses", f="case_activity_status"),
                    M("Needs", f="need"),
                    M("Occupations", c="pr", f="occupation_type"),
                    ),
                )

    # -------------------------------------------------------------------------
    def cr(self):
        """ Events """

        return self.fin()

    # -------------------------------------------------------------------------
    def event(self):
        """ Events """

        return self.security()

    # -------------------------------------------------------------------------
    @staticmethod
    def fin():
        """ Logistics """

        ADMIN = current.auth.get_system_roles().ADMIN

        return M()(
                    M("Accommodation", c="cr", f="shelter")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                    M("Banks", c="fin", f="bank")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                    M("Brokers", c="fin", f="broker")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                    M("Stock", c="inv", f="inv_item")(
                        M("Create", m="create"),
                        M("Warehouses", f="warehouse"),
                        ),
                    M("Administration", link=False, restrict=ADMIN)(
                        M("Accomodation Types", c="cr", f="shelter_type"),
                        M("Bank Services", c="fin", f="bank_service"),
                        M("Item Catalog", c="supply", f="item"),
                        ),
                    )

    # -------------------------------------------------------------------------
    def gis(self):
        """ Maps """

        if current.request.function == "route":
            # @ToDo: Should be managed from within Case Activity?
            return self.security()
        else:
            return super(S3OptionsMenu, self).gis()

    # -------------------------------------------------------------------------
    def hrm(self):
        """ HRM / Human Resources Management """

        if current.request.function == "skill":
            return self.med()
        else:
            return self.org()

    # -------------------------------------------------------------------------
    def inv(self):
        """ Stock """

        return self.fin()

    # -------------------------------------------------------------------------
    @staticmethod
    def med():
        """ Medical """

        ADMIN = current.auth.get_system_roles().ADMIN

        return M(c="med")(
                    M("Medical Facilities", f="hospital", m="summary")(
                        M("Create", m="create"),
                        ),
                    M("Medical Personnel", f="contact")(
                        M("Create", m="create"),
                        ),
                    M("Pharmacies", f="pharmacy")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                    M("Administration", link=False, restrict=ADMIN)(
                        M("Qualifications", c="hrm", f="skill"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        ADMIN = current.auth.get_system_roles().ADMIN

        return M()(
                    M("Organizations", c="org", f="organisation")(
                        #M("Hierarchy", m="hierarchy"),
                        M("Create", m="create", restrict=ADMIN),
                        ),
                    M("Staff", c="hrm", f="staff")(
                        # Always create via User
                        #M("Create", m="create"),
                        ),
                    M("Administration", restrict=ADMIN)(
                        M("Organization Types", c="org", f="organisation_type"),
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
    def security():
        """ Security """

        ADMIN = current.auth.get_system_roles().ADMIN

        return M()(M("Checkpoints", c="security", f="checkpoint")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                   # View from inside Activity?
                   M("Evacuation Routes", c="gis", f="route")(
                        M("Create", m="create"),
                        ),
                   M("Incident Reports", c="event", f="incident_report")(
                       M("Create", m="create"),
                       M("Map", m="map"),
                       ),
                   M("Security Zones", c="security", f="zone")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                   M("Administration", link=False, restrict=ADMIN)(
                        M("Incident Types", c="event", f="incident_type"),
                        M("Zone Types", c="security", f="zone_type"),
                        ),
                   )

    # -------------------------------------------------------------------------
    @staticmethod
    def transport():
        """ Transport """

        return M(c="transport")(
                    M("Airports", f="airport")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                    M("Airplane Types", f="airplane")(
                        M("Create", m="create"),
                        ),
                    M("Flights", f="flight")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                    )

# END =========================================================================
