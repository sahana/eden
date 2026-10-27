"""
    Custom menus for MRCMS

    License: MIT
"""

from gluon import current, URL, TAG, SPAN
from core import IS_ISO639_2_LANGUAGE_CODE
from core.ui.layouts import MM, M, ML, MP, MA
try:
    from .layouts import OM
except ImportError:
    pass
import core.ui.menus as default

from .helpers import get_default_organisation, get_default_shelter

# =============================================================================
class MainMenu(default.MainMenu):
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
        """ Custom Modules Menu """

        auth = current.auth

        has_role = auth.s3_has_role
        has_permission = auth.s3_has_permission

        is_admin = has_role("ADMIN")

        # Single or multiple organisations?
        if has_permission("create", "org_organisation", c="org", f="organisation"):
            organisation_id = None
        else:
            organisation_id = get_default_organisation()

        # Organisation menu
        c = ("org", "hrm", "act") if is_admin else ("org", "hrm", "act", "cms")
        f = ("organisation", "*")
        if organisation_id:
            org_menu = MM("Organization", c=c, f=f, args=[organisation_id], ignore_args=True)
        else:
            org_menu = MM("Organizations", c=c, f=f)

        # Single or multiple shelters?
        if has_permission("create", "cr_shelter", c="cr", f="shelter"):
            shelter_id = None
        else:
            shelter_id = get_default_shelter()

        # Shelter menu
        if shelter_id:
            shelter_menu = MM("Shelter", c="cr", f="shelter", args=[shelter_id], ignore_args=True)
        else:
            shelter_menu = MM("Shelters", c="cr", f="shelter")

        # Med-menu
        if has_permission("read", "pr_person", c="dvr", f="person") and \
           has_permission("read", "pr_person", c="med", f="person"):
            # Primary perspective for case assistants
            med_menu = MM("Medical", c="med", f=("person", "*"))
        elif has_permission("read", "med_patient", c="med", f="patient"):
            # Primary perspective for other medical personnel
            med_menu = MM("Medical", c="med", f=("patient", "*"))
        else:
            # Fallback
            # - will self-disable if user not permitted, hence no
            #   MED-link at all without at least this permission
            med_menu = MM("Medical", c="med", f=("unit", "*"))

        menu = [
            MM("Clients", c=("dvr", "pr"), f=("person", "*")),
            MM("Food Distribution", c="dvr", f="case_event", m="register_food", p="create",
               restrict = "CATERING",
               check = not is_admin,
               ),
            MM("Counseling", c=("counsel", "pr"), f=("person", "*")),
            MM("Supply", c=("supply", "pr"), f=("person", "*")),
            med_menu,
            shelter_menu,
            org_menu,
            MM("Security", c="security", f="seized_item"),
            # MM("To Do", c="act", f=("my_open_tasks", "task", "issue")),
            ]

        # Optional entries
        if current.deployment_settings.get_custom("manage_work_orders", True):
            menu.append(MM("To Do", c="act", f=("my_open_tasks", "task", "issue")))

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Custom Organisation Menu """

        return OM()

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls, **attr):

        languages = current.deployment_settings.get_L10n_languages()
        represent_local = IS_ISO639_2_LANGUAGE_CODE.represent_local

        # Language selector
        menu_lang = ML("Language", right=True)
        for code in languages:
            # Show Language in it's own Language
            lang_name = represent_local(code)
            menu_lang(
                ML(lang_name, translate=False, lang_code=code, lang_name=lang_name)
                )
        return menu_lang

    # -------------------------------------------------------------------------
    @classmethod
    def menu_personal(cls):
        """ Custom Personal Menu """

        auth = current.auth
        settings = current.deployment_settings

        sr = current.auth.get_system_roles()
        ADMIN = sr.ADMIN

        if not auth.is_logged_in():
            request = current.request
            login_next = URL(args=request.args, vars=request.get_vars)
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
            if settings.get_auth_password_retrieval():
                menu_personal(MP("Lost Password", c="default", f="user",
                                 m = "retrieve_password",
                                 ),
                              )
        else:
            has_role = auth.s3_has_role
            is_user_admin = lambda i: not has_role(ADMIN) and (
                                        has_role(sr.ORG_ADMIN, include_admin=False) or \
                                        has_role(sr.ORG_GROUP_ADMIN, include_admin=False)
                                        )
            menu_personal = MP()(
                        MP("Administration", c="admin", f="index",
                           restrict = ADMIN,
                           ),
                        MP("Administration", c="admin", f="user",
                           check = is_user_admin,
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
                MA("Contact", f="index", args=["contact"]),
                MA("Privacy", f="index", args=["privacy"]),
                MA("Legal Notice", f="index", args=["legal"]),
                MA("Version", f="about", restrict = ADMIN),
                )

        return menu_about

# =============================================================================
class OptionsMenu(default.OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @classmethod
    def act(cls):

        if current.request.function == "activity":
            menu = cls.org()
        else:
            if current.s3db.act_task_is_manager():
                tasks = M("Work Orders", f="task")(
                            M("My Work Orders", f="my_open_tasks"),
                            M("All Work Orders", f="task"),
                            M("Create", m="create"),
                            )
            else:
                tasks = M("My Work Orders", f="my_open_tasks")

            menu = M(c="act")(
                        tasks,
                        M("Issue Reports", f="issue")(
                            M("Create", m="create"),
                            ),
                        )

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def counsel(cls):

        sr = current.auth.get_system_roles()
        ADMIN = sr.ADMIN
        ORG_GROUP_ADMIN = sr.ORG_GROUP_ADMIN

        return M(c="counsel")(
                    M("Current Cases", c=("counsel", "pr"), f="person")(
                        M("Tasks", c="counsel", f="task"),
                        ),
                    M("Actions", c="counsel", f="response_action")(
                        M("Overview"),
                        ),
                    M("Statistics", link=False)(
                        M("Actions", f="response_action", m="report"),
                        ),
                    M("Administration", link=False, restrict=(ADMIN, ORG_GROUP_ADMIN))(
                        # Global types
                        M("Need Types", f="need"),
                        M("Action Types", f="response_type"),
                        M("Response Themes", f="response_theme"),
                        M("Vulnerability Types", f="vulnerability_type"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @classmethod
    def cms(cls):

        if not current.auth.s3_has_role("ADMIN"):
            return cls.org()

        return super().cms()

    # -------------------------------------------------------------------------
    @staticmethod
    def cr():
        """ CR / Shelter Registry """

        # Single or multiple shelters?
        if current.auth.s3_has_permission("create", "cr_shelter", c="cr", f="shelter"):
            shelter_id = None
        else:
            shelter_id = get_default_shelter()

        if not shelter_id:
            menu = M(c="cr")(
                        M("Shelters", f="shelter")(
                            M("Create", m="create"),
                            ),
                        )
        else:
            menu = M(c="cr")(
                        M("Shelter", f="shelter", args=[shelter_id], ignore_args=True)(
                            M("Overview", m="overview", args=[shelter_id]),
                            M("Housing Units", t="cr_shelter_unit", args=[shelter_id, "shelter_unit"]),
                            ),
                        )

        ADMIN = current.auth.get_system_roles().ADMIN
        menu = menu(
                M("Administration", link=False, restrict=ADMIN)(
                    M("Target Demographics", f="shelter_commission_demographic"),
                    ))

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def hrm(cls):

        return cls.org()

    # -------------------------------------------------------------------------
    @staticmethod
    def dvr():
        """ DVR / Disaster Victim Registry """

        #due_followups = current.s3db.dvr_due_followups() or "0"
        #follow_up_label = "%s (%s)" % (current.T("Due Follow-ups"),
        #                               due_followups,
        #                               )

        sr = current.auth.get_system_roles()
        ADMIN = sr.ADMIN
        ORG_ADMIN = sr.ORG_ADMIN

        return M(c="dvr")(
                M("Current Cases", c=("dvr", "pr"), f="person")(
                    M("Create", m="create", t="pr_person", p="create"),
                    M("All Cases", vars = {"closed": "include"}),
                    M("Tasks", c="dvr", f="task"),
                    ),
                #M("Current Needs", f="case_activity")(
                #    M("Emergencies", vars={"~.emergency": "True"}),
                #    M(follow_up_label, f="due_followups"),
                #    M("Report", m="report"),
                #    ),
                M("Appointments", f="case_appointment")(
                    M("Overview"),
                    ),
                M("Registration", c="dvr", f="case_event", link=None)(
                    M("Checkpoint", c="dvr", f="case_event", m="register", p="create"),
                    M("Activity", c="dvr", f="case_event", m="register_activity", p="create"),
                    M("Food Distribution", c="dvr", f="case_event", m="register_food", p="create"),
                    ),
                M("Statistics", link=False)(
                    M("Cases", c="dvr", f="person", m="report",
                      restrict = (ADMIN, ORG_ADMIN, "CASE_ADMIN"),
                      ),
                    ),
                M("Reports", link=False)(
                    M("Arrivals and Departures##shelter", c="dvr", f="person", m="aandd",
                      t = "cr_shelter_registration_history", p="read",
                      restrict = ("ADMIN", "ORG_ADMIN", "CASE_ADMIN"),
                      ),
                    M("Presence", c="dvr", f="person", m="presence_report",
                      t = "org_site_presence_event", p="read",
                      restrict = (ADMIN, ORG_ADMIN, "CASE_ADMIN"),
                      ),
                    M("Food Distribution", c="dvr", f="case_event", m="meals_report",
                      restrict = (ADMIN, ORG_ADMIN, "CASE_ADMIN"),
                      ),
                    ),
                M("Archive", link=False)(
                    M("Closed Cases", f="person",
                        restrict = (ADMIN, ORG_ADMIN, "CASE_ADMIN"),
                        vars={"closed": "only"},
                        ),
                    M("Invalid Cases", f="person",
                        vars={"archived": "1", "closed": "1"},
                        restrict = (ADMIN, ORG_ADMIN),
                        ),
                    ),
                M("Administration", link=False, restrict=(ADMIN, ORG_ADMIN))(
                    # Org-specific types
                    M("Flags", f="case_flag"),
                    M("Appointment Types", f="case_appointment_type"),
                    M("Event Types", f="case_event_type"),

                    # Global types
                    M("Case Status", f="case_status", restrict=ADMIN),
                    M("Residence Status Types", f="residence_status_type", restrict=ADMIN),
                    M("Residence Permit Types", f="residence_permit_type", restrict=ADMIN),
                    M("Service Contact Types", f="service_contact_type", restrict=ADMIN),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def med():
        """ Medical Journal """

        ADMIN = current.session.s3.system_roles.ADMIN

        is_case_reader = current.auth.s3_has_permission("read", "pr_person", c="dvr", f="person")

        if is_case_reader:
            menu = M()(
                        M("Current Cases", c="med", f="person"),
                        M("Visits", c="med", f="patient")(
                            M("Create", m="create"),
                            M("Concluded Visits", vars={"closed": "only"}),
                            ),
                        )
        else:
            menu = M()(
                        M("Visits", c="med", f="patient")(
                            M("Create", m="create"),
                            M("Case Files", f="person"),
                            ),
                        )

        return menu(M("Administration", c="med", link=False)(
                        M("Care Units", f="unit", restrict=["ORG_ADMIN", "MED_ADMIN"]),
                        M("Active Substances", f="substance", restrict=ADMIN),
                        M("Vaccination Types", f="vaccination_type", restrict=ADMIN),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        T = current.T
        auth = current.auth

        ADMIN = current.session.s3.system_roles.ADMIN

        # Single or multiple organisations?
        if auth.s3_has_permission("create", "org_organisation", c="org", f="organisation"):
            organisation_id = None
        else:
            organisation_id = get_default_organisation()
        if organisation_id:
            org_menu = M("Organization", c="org", f="organisation", args=[organisation_id], ignore_args=True)
        else:
            org_menu = M("Organizations", c="org", f="organisation")(
                            M("Create", m="create"),
                            )

        # Newsletter menu
        author = auth.s3_has_permission("create", "cms_newsletter", c="cms", f="newsletter")
        inbox_label = T("Inbox") if author else T("Newsletters")
        unread = current.s3db.cms_unread_newsletters()
        if unread:
            inbox_label = TAG[""](inbox_label, SPAN(unread, _class="num-pending"))
        if author:
            cms_menu = M("Newsletters", c="cms", f="read_newsletter")(
                            M(inbox_label, f="read_newsletter", translate=False),
                            M("Compose and Send", f="newsletter", p="create"),
                            )
        else:
            cms_menu = M(inbox_label, c="cms", f="read_newsletter", translate=False)

        return M(c=("org", "hrm", "act"))(
                    org_menu,
                    M("Organization Groups", f="group")(
                        M("Create", m="create"),
                        ),
                    M("Activities", c="act", f="activity"),
                    M("Staff", c="hrm", f="staff"),
                    cms_menu,
                    M("Administration", link=False, restrict=[ADMIN])(
                        M("Organization Types", c="org", f="organisation_type"),
                        M("Activity Types", c="act", f="activity_type"),
                        M("Job Titles", c="hrm", f="job_title"),
                        ),
                    )

    ## -------------------------------------------------------------------------
    #@staticmethod
    #def project():
    #    """ PROJECT / Project/Task Management """
    #
    #    return M(c="project")(
    #             M("Tasks", f="task")(
    #                M("Create", m="create"),
    #                M("My Open Tasks", vars={"mine":1}),
    #             ),
    #            )
    #
    # -------------------------------------------------------------------------
    @staticmethod
    def security():
        """ SECURITY / Security Management """

        return M(c="security")(
                M("Confiscation", f="seized_item")(
                    M("Create", m="create"),
                    M("Item Types", f="seized_item_type"),
                    M("Depositories", f="seized_item_depository"),
                    ),
                )

    # -------------------------------------------------------------------------
    def supply(self):

        return M(c="supply")(
                M("Current Cases", c=("supply", "pr"), f="person"),
                M("Distributed Items", f="distribution_item")(
                    M("Overview"),
                    ),
                M("Registration", link=False)(
                    M("Distribution", f="distribution", m="register", p="create"),
                    ),
                #M("Statistics", link=False),
                M("Reports", link=False)(
                    M("Grants Total##supplies", f="distribution_item", m="grants_total"),
                    ),
                M("Administration", link=False, restrict=["ADMIN", "ORG_ADMIN"])(
                    M("Distribution Item Sets", f="distribution_set"),
                    M("Catalogs", f="catalog"),
                    M("Items", f="item"),
                    ),
                )

# END =========================================================================
