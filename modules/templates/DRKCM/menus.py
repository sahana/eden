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

        case_vars = {"closed": "0"}
        if auth.s3_logged_in_human_resource() and \
           auth.s3_has_role("CASE_MANAGEMENT"):
            case_vars["mine"] = "1"

        return [MM("Cases", c=("dvr", "pr"), f="person", vars=case_vars),
                MM("Case Consulting", c="dvr", f="index",
                   check = lambda this: not this.preceding()[-1].check_permission(),
                   ),
                MM("ToDo", c="project", f="task"),
                #MM("Map", c="gis", f="index"),
                MM("Shelters", c="cr", f="shelter"),
                MM("More", link=False)(
                    MM("Organizations", c="org", f="organisation"),
                    MM("Facilities", c="org", f="facility"),
                    MM("Staff", c="hrm", f="staff"),
                    MM("Volunteers", c="vol", f="volunteer"),
                    SEP(link=False),
                    MM("User Statistics", c="default", f="index",
                       args = ["userstats"],
                       restrict = ("ORG_GROUP_ADMIN",),
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
    def dvr():
        """ DVR / Disaster Victim Registry """

        auth = current.auth

        sysroles = auth.get_system_roles()

        ADMIN = sysroles.ADMIN
        ORG_ADMIN = sysroles.ORG_ADMIN
        ORG_GROUP_ADMIN = sysroles.ORG_GROUP_ADMIN

        due_followups = current.s3db.dvr_due_followups

        human_resource_id = auth.s3_logged_in_human_resource()
        if human_resource_id and auth.s3_has_role("CASE_MANAGEMENT"):

            due_followups = due_followups(human_resource_id = human_resource_id) or "0"
            follow_ups_label = "%s (%s)" % (current.T("Due Follow-ups"),
                                            due_followups,
                                            )

            my_cases = M("My Cases", c=("dvr", "pr"), f="person",
                         vars = {"closed": "0", "mine": "1"})(
                            M("Create Case", m="create", t="pr_person", p="create"),
                            # FIXME crashing (incorrect join order in S3GIS):
                            #M("Map", f="person", m="map",
                            #  vars = {"closed": "0", "mine": "1"},
                            #  ),
                            M("Activities", f="case_activity",
                              vars = {"mine": "1"},
                              ),
                            M(follow_ups_label, f="due_followups",
                              vars = {"mine": "1"},
                              ),
                            )

            my_actions = M("Actions", c="dvr", f="response_action")(
                            M("Assigned to me", vars = {"mine": "a"}),
                            M("Managed by me", vars = {"mine": "r"}),
                            )

            all_cases = M("Current Cases", c=("dvr", "pr"), f="person",
                          vars = {"closed": "0"})(
                            #M("Create Case", m="create", t="pr_person", p="create"),
                            M("All Cases", vars = {}),
                            #M("Actions", f="response_action"),
                            )

            all_activities = M("Activities", f="case_activity")(
                                M("Emergencies", vars = {"~.priority": "0"}),
                                M("All Activities"),
                                M("Report", m="report"),
                                )

        else:
            due_followups = due_followups() or "0"
            follow_ups_label = "%s (%s)" % (current.T("Due Follow-ups"),
                                            due_followups,
                                            )

            my_cases = None
            my_actions = None
            all_cases = M("Current Cases", c=("dvr", "pr"), f="person",
                          vars = {"closed": "0"})(
                            M("Create Case", m="create", t="pr_person", p="create"),
                            # FIXME crashing (incorrect join order in S3GIS):
                            #M("Map", f="person", m="map", vars = {"closed": "0"}),
                            M("All Cases", vars = {}),
                            M("Actions", f="response_action"),
                            )

            all_activities = M("Activities", f="case_activity")(
                                M("Emergencies", vars = {"~.priority": "0"}),
                                M(follow_ups_label, f="due_followups"),
                                M("All Activities"),
                                M("Report", m="report"),
                                )

        return M(c="dvr")(
                    my_cases,
                    my_actions,
                    all_cases,
                    all_activities,
                    M("Appointments", f="case_appointment")(
                        M("Overview"),
                        ),
                    M("Archive", link=False)(
                        M("Closed Cases", f="person",
                          vars={"closed": "1"},
                          ),
                        M("Invalid Cases", f="person",
                          restrict = (ADMIN, ORG_ADMIN),
                          vars={"archived": "1"},
                          ),
                        ),
                    M("Administration", restrict=(ADMIN, ORG_GROUP_ADMIN))(
                        M("Flags", f="case_flag"),
                        M("Case Status", f="case_status"),
                        M("Need Types", f="need"),
                        M("Intervention Types", f="response_type", m="hierarchy"),
                        M("Appointment Types", f="case_appointment_type"),
                        M("Residence Status Types", f="residence_status_type"),
                        M("Residence Permit Types", f="residence_permit_type"),
                        M("Service Contact Types", f="service_contact_type"),
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
