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

        case_vars = {"closed": "0"}
        if auth.s3_logged_in_human_resource() and \
           auth.s3_has_role("CASE_MANAGEMENT"):
            case_vars["mine"] = "1"

        labels = current.s3db.br_terminology()

        return [MM(labels.CASES, c=("br", "pr"), f="person", vars=case_vars),
                MM("Case Management", c="br", f="index",
                   check = lambda this: not this.preceding()[-1].check_permission(),
                   ),
                MM("ToDo", c="project", f="task"),
                MM("Shelters", c="cr", f="shelter"),
                MM("More", link=False)(
                    MM("Organizations", c="org", f="organisation"),
                    MM("Facilities", c="org", f="facility"),
                    MM("Staff", c="hrm", f="staff"),
                    MM("Volunteers", c="vol", f="volunteer"),
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
    def cr():
        """ CR / Shelter Registry """

        ADMIN = current.auth.get_system_roles().ADMIN

        return M(c="cr")(
                    M("Shelters", f="shelter")(
                        M("Create", m="create"),
                        M("Map", m="map"),
                        ),
                    M("Administration", link=False, restrict=(ADMIN,))(
                        M("Shelter Types", f="shelter_type"),
                        ),
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
                        M("Hierarchy", m="hierarchy"),
                        M("Create", m="create", restrict=(ADMIN, ORG_GROUP_ADMIN)),
                        ),
                    M("Facilities", f="facility")(
                        M("Create", m="create"),
                        ),
                    M("Administration", restrict=(ADMIN, ORG_GROUP_ADMIN))(
                        M("Facility Types", f="facility_type"),
                        M("Organization Types", f="organisation_type"),
                        M("Sectors", f="sector"),
                        )
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM / Human Resources Management """

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

        settings = current.deployment_settings

        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams

        return M(c="vol")(
                    M("Volunteers", f="volunteer")(
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
    def project():
        """ PROJECT / Project/Task Management """

        return M(c="project", f="task")(
                    M("Tasks", f="task")(
                        M("Create", m="create"),
                        M("My Open Tasks", vars={"mine":1}),
                        ),
                    )

# END =========================================================================
