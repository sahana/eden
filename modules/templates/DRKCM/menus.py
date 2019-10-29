# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

from .config import get_ui_options

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
        ui_options = get_ui_options()

        case_vars = {"closed": "0"}
        if not ui_options.get("case_collaboration") and \
           auth.s3_logged_in_human_resource() and \
           auth.s3_has_role("CASE_MANAGEMENT"):
            case_vars["mine"] = "1"

        return [MM("Cases", c=("dvr", "pr"), f=("person", "case_activity", "response_action"),
                   t = "dvr_case",
                   vars = case_vars,
                   ),
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

        T = current.T
        auth = current.auth

        sysroles = auth.get_system_roles()

        ADMIN = sysroles.ADMIN
        ORG_ADMIN = sysroles.ORG_ADMIN
        ORG_GROUP_ADMIN = sysroles.ORG_GROUP_ADMIN

        ui_options = get_ui_options()
        ui_options_get = ui_options.get

        due_followups_label = T("Due Follow-ups")
        followups = ui_options_get("activity_follow_up")
        if followups:
            due_followups = current.s3db.dvr_due_followups
            all_due_followups = due_followups() or "0"

        use_priority = ui_options_get("activity_priority")

        human_resource_id = auth.s3_logged_in_human_resource()
        if human_resource_id and auth.s3_has_role("CASE_MANAGEMENT"):

            # Follow-up labels
            if followups:
                my_due_followups = due_followups(human_resource_id = human_resource_id) or "0"
                my_due_followups_label = "%s (%s)" % (due_followups_label,
                                                      my_due_followups,
                                                      )
                all_due_followups_label = "%s (%s)" % (T("All Follow-ups"),
                                                       all_due_followups,
                                                       )
            else:
                my_due_followups_label = all_due_followups_label = due_followups_label

            # Cases sub-menu
            case_collaboration = ui_options_get("case_collaboration")
            if case_collaboration:
                # Current Cases as lead item
                case_menu = M("Current Cases", c=("dvr", "pr"), f="person", t="dvr_case",
                              vars = {"closed": "0"},
                              )
            else:
                # My Cases as lead item (Current Cases in Overviews)
                case_menu = M("My Cases", c=("dvr", "pr"), f="person", t="dvr_case",
                              vars = {"closed": "0", "mine": "1"},
                              )

            # Actions sub-menu
            if ui_options_get("response_use_organizer"):
                # In case collaboration, use HR filter widget with default
                # rather than mine-parameter, so that the user can choose
                # to see other team member's response actions
                get_vars = {"mine": "f"} if case_collaboration else {"mine": "a"}
                my_actions = M("My Actions", c="dvr", f="response_action",
                               t="dvr_response_action", vars = get_vars)(
                                M("Calendar", m="organize", vars = get_vars),
                                    )
            else:
                my_actions = M("Actions", c="dvr", f="response_action",
                               t="dvr_response_action", link=False)(
                                M("Assigned to me", vars = {"mine": "a"}),
                                M("Managed by me", vars = {"mine": "r"}),
                                )

            menu = M(c="dvr")(
                    case_menu(
                        M("Create Case", m="create", t="pr_person", p="create"),
                        M("My Cases", f="person", t="dvr_case",
                          vars = {"closed": "0", "mine": "1"},
                          check = case_collaboration,
                          ),
                        M("My Activities", c="dvr", f="case_activity", vars={"mine": "1"}),
                        M(my_due_followups_label, c="dvr", f="due_followups",
                          vars = {"mine": 1},
                          check = followups,
                          ),
                        ),
                    my_actions,
                    M("Overviews", c=("dvr", "pr"), link=False)(
                        M("Current Cases", f="person", t="dvr_case",
                          vars = {"closed": "0"},
                          check = case_collaboration,
                          ),
                        M("All Cases", f="person", t="dvr_case"),
                        M("All Activities", f="case_activity", t="dvr_case_activity"),
                        M(all_due_followups_label, f="due_followups",
                          check = followups,
                          ),
                        M("Emergencies", f="case_activity",
                          vars = {"~.priority": "0"},
                          check = use_priority,
                          ),
                        M("All Actions", f="response_action"),
                        ),
                    )
        else:
            # Reduced menu for other users
            if followups:
                all_due_followups_label = "%s (%s)" % (due_followups_label,
                                                       all_due_followups,
                                                       )

            menu = M(c="dvr")(
                    M("Current Cases", c=("dvr", "pr"), f="person", t="dvr_case",
                      vars = {"closed": "0"})(
                        M("Create Case", m="create", t="pr_person", p="create"),
                        M("All Cases", vars = {}),
                        M("Actions", f="response_action"),
                        ),
                    M("Activities", f="case_activity")(
                        M("Emergencies", f="case_activity",
                          vars = {"~.priority": "0"},
                          check = use_priority,
                          ),
                        M(due_followups_label, f="due_followups",
                          check = followups,
                          ),
                        M("All Activities"),
                        ),
                    )

        # Appointments sub-menu (optional)
        if ui_options_get("case_use_appointments"):
            appointments_menu = M("Appointments", f="case_appointment")(
                                    M("Overview"),
                                    )
            # Show personal calendar if using staff link and organizer
            if ui_options_get("appointments_staff_link") and \
               ui_options_get("appointments_use_organizer"):
                appointments_menu(M("My Appointments", m="organize", p="read",
                                    vars = {"mine": "1"},
                                    check = ui_options_get("appointments_staff_link"),
                                    )
                                  )

            menu(appointments_menu)

        return menu(M("Statistics", c="dvr", link=False)(
                        M("Actions", f="response_action", t="dvr_response_action", m="report"),
                        M("Activities", f="case_activity", t="dvr_case_activity", m="report"),
                        M("Cases", f="person", m="report", t="dvr_case", vars={"closed": "0"}),
                        ),
                    M("Archive", link=False)(
                        M("Closed Cases", f="person", t="dvr_case",
                          vars={"closed": "1"},
                          ),
                        M("Invalid Cases", f="person", t="dvr_case",
                          restrict = (ADMIN, ORG_ADMIN),
                          vars={"archived": "1"},
                          ),
                        ),
                    M("Administration", restrict=(ADMIN, ORG_GROUP_ADMIN))(
                        #M("Flags", f="case_flag"),
                        #M("Case Status", f="case_status"),
                        M("Action Types", f="response_type"),
                        #M("Appointment Types", f="case_appointment_type"),
                        #M("Residence Status Types", f="residence_status_type"),
                        M("Residence Permit Types", f="residence_permit_type"),
                        #M("Service Contact Types", f="service_contact_type"),
                        M("Diagnoses", f="vulnerability_type"),
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
