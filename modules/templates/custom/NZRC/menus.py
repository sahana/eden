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

        # @todo: restore?
        #current.menu.dashboard = cls.menu_dashboard()

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        return [
            homepage("gis")(
            ),
            #homepage("hrm", "org", name="Staff",
            #         vars=dict(group="staff"), check=hrm)(
            #    MM("Staff", c="hrm", f="staff", m="summary"),
            #    MM("Teams", c="hrm", f="group"),
            #    MM("Organizations", c="org", f="organisation"),
            #    MM("Offices", c="org", f="office"),
            #    MM("Job Titles", c="hrm", f="job_title"),
            #    #MM("Skill List", c="hrm", f="skill"),
            #    MM("Training Events", c="hrm", f="training_event"),
            #    MM("Training Courses", c="hrm", f="course"),
            #    MM("Certificate List", c="hrm", f="certificate", check=use_certs),
            #),
            homepage("vol", name="Volunteers")(
                MM("Volunteers", c="vol", f="volunteer", m="summary"),
                MM("Teams", c="vol", f="group"),
                MM("Volunteer Roles", c="vol", f="job_title"),
                MM("Programs", c="vol", f="programme"),
                #MM("Skill List", c="vol", f="skill"),
                MM("Training Events", c="vol", f="training_event"),
                MM("Training Courses", c="vol", f="course"),
                MM("Certificate List", c="vol", f="certificate"),
            ),
            homepage("member")(
                MM("Members", c="member", f="membership", m="summary"),
            ),
            #homepage("dvr")(
            #    MM("Cases", c="dvr", f="case", m="summary"),
            #),
            homepage("po")(
                MM("Households", c="po", f="household", m="summary"),
            ),
            homepage("req")(
                MM("Opportunities", c="req", f="req", m="summary"),
            ),
            homepage("project")(
                MM("Tasks", c="project", f="task"),
            ),
            homepage("deploy", name="Delegates", f="mission", m="summary",
                     vars={"~.status__belongs": "2"})(
                MM("Missions", c="deploy", f="mission", m="summary"),
                MM("Members", c="deploy", f="human_resource", m="summary"),
            ),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Custom Organisation Menu """

        OM = S3OrgMenuLayout
        return OM()

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls):

        s3 = current.response.s3

        # Language selector
        menu_lang = ML("Language", right=True)
        for language in s3.l10n_languages.items():
            code, name = language
            menu_lang(
                ML(name, translate=False, lang_code=code, lang_name=name)
            )
        return menu_lang

    # -------------------------------------------------------------------------
    @classmethod
    def menu_personal(cls):
        """ Custom Personal Menu """

        auth = current.auth
        s3 = current.response.s3
        settings = current.deployment_settings

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
                           m="register", check=self_registration),
                        MP("Login", c="default", f="user",
                           m="login", vars=dict(_next=login_next)),
                        MP("Lost Password", c="default", f="user",
                           m="retrieve_password"),
            )

        else:
            s3_has_role = auth.s3_has_role
            is_org_admin = lambda i: s3_has_role("ORG_ADMIN") and \
                                     not s3_has_role("ADMIN")
            menu_personal = MP()(
                        MP("Administration", c="admin", f="index",
                           check=s3_has_role("ADMIN")),
                        MP("Administration", c="admin", f="user",
                           check=is_org_admin),
                        MP("Profile", c="default", f="person"),
                        MP("Change Password", c="default", f="user",
                           m="change_password"),
                        MP("Logout", c="default", f="user",
                           m="logout"),
            )

        return menu_personal

    # -------------------------------------------------------------------------
    @classmethod
    def menu_about(cls):

        menu_about = MA(c="default")(
            MA("About Us", f="about"),
            MA("Contact", f="contact"),
            MA("Help", f="help"),
            MA("Privacy", f="privacy"),
        )
        return menu_about

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    def admin(self):
        """ ADMIN menu """

        # Standard Admin Menu
        menu = super(S3OptionsMenu, self).admin()

        # Additional Items
        menu(M("Map Settings", c="gis", f="config"),
             M("Content Management", c="cms", f="index"),
             )

        return menu

    # -------------------------------------------------------------------------
    def gis(self):
        """ GIS / GIS Controllers """

        if current.request.function == "index":
            # Empty so as to leave maximum space for the Map
            # - functionality accessible via the Admin menu instead
            return None
        else:
            return super(S3OptionsMenu, self).gis()

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM Human Resource Management """

        has_role = current.auth.s3_has_role
        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN
        settings = current.deployment_settings

        if "hrm" not in s3:
            current.s3db.hrm_vars()
        hrm_vars = s3.hrm

        SECTORS = "Clusters" if settings.get_ui_label_cluster() \
                             else "Sectors"

        manager_mode = lambda i: hrm_vars.mode is None
        personal_mode = lambda i: hrm_vars.mode is not None
        is_org_admin = lambda i: hrm_vars.orgs and True or \
                                 has_role(ADMIN)
        is_super_editor = lambda i: has_role("staff_super") or \
                                    has_role("vol_super")

        staff = {"group": "staff"}

        use_certs = lambda i: settings.get_hrm_use_certificates()

        return M()(
                    M("Staff", c="hrm", f=("staff", "person"), m="summary",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("Import", f="person", m="import",
                          vars=staff, p="create"),
                    ),
                    M("Staff & Volunteers (Combined)",
                      c="hrm", f="human_resource", m="summary",
                      check=[manager_mode, is_super_editor]),
                    M("Teams", c="hrm", f="group",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("Search Members", f="group_membership"),
                        M("Import", f="group_membership", m="import"),
                    ),
                    M("Organizations", c="org",
                                       f="organisation",
                      check=manager_mode)(
                        M("Create", m="create",
                          ),
                        M("Import", m="import", p="create", check=is_org_admin)
                    ),
                    M("Offices", c="org", f="office",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Department Catalog", c="hrm", f="department",
                      check=manager_mode)(
                        M("Create", m="create"),
                    ),
                    M("Job Title Catalog", c="hrm", f="job_title",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("Import", m="import", p="create", check=is_org_admin),
                    ),
                    #M("Skill Catalog", f="skill",
                    #  check=manager_mode)(
                    #    M("Create", m="create"),
                    #    #M("Skill Provisions", f="skill_provision"),
                    #),
                    M("Training Events", c="hrm", f="training_event",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("Search Training Participants", f="training"),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Reports", c="hrm", f="staff", m="report",
                      check=manager_mode)(
                        M("Staff Report", m="report"),
                        M("Expiring Staff Contracts Report",
                          vars=dict(expiring="1")),
                        M("Training Report", f="training", m="report"),
                    ),
                    M("Training Course Catalog", c="hrm", f="course",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("Import", m="import", p="create", check=is_org_admin),
                        M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", c="hrm", f="certificate",
                      check=[manager_mode, use_certs])(
                        M("Create", m="create"),
                        M("Import", m="import", p="create", check=is_org_admin),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("Organization Types", c="org", f="organisation_type",
                      restrict=[ADMIN],
                      check=manager_mode)(
                        M("Create", m="create"),
                    ),
                    M("Office Types", c="org", f="office_type",
                      restrict=[ADMIN],
                      check=manager_mode)(
                        M("Create", m="create"),
                    ),
                    #M("Facility Types", c="org", f="facility_type",
                    #  restrict=[ADMIN],
                    #  check=manager_mode)(
                    #    M("Create", m="create"),
                    #),
                    #M("My Profile", c="hrm", f="person",
                    #  check=personal_mode, vars=dict(access="personal")),
                    # This provides the link to switch to the manager mode:
                    M("Human Resources", c="hrm", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    #M("Personal Profile", c="hrm", f="person",
                    #  check=manager_mode, vars=dict(access="personal"))
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ Organisation Management """

        # Same as HRM
        return self.hrm()

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ Tasks """

        return M(c="project")(
                M("Projects", f="project")(
                    M("Create", m="create"),
                    M("Open Tasks for Project", vars={"tasks":1}),
                ),
                M("Tasks", f="task")(
                    M("Create", m="create"),
                ),
                M("Daily Work", f="time")(
                   M("My Logged Hours", vars={"mine":1}),
                   M("My Open Tasks", f="task", vars={"mine":1}),
                ),
                M("Reports", f="report")(
                    M("Activity Report", f="activity", m="report"),
                    M("Last Week's Work", f="time", m="report",
                      vars=Storage(rows="person_id",
                                   cols="day",
                                   fact="sum(hours)",
                                   week=1)),
                    M("Last Month's Work", f="time", m="report",
                      vars=Storage(rows="person_id",
                                   cols="week",
                                   fact="sum(hours)",
                                   month=1)),
                    M("Project Time Report", f="time", m="report"),
                ),
            )
                    
    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ Volunteer Opportunities """

        #recurring = lambda i: settings.get_req_recurring()

        return M(c="req")(
                    M("Requests", f="req")(
                        M("Create", m="create", vars={"type": 3}),
                        M("List Recurring Requests", f="req_template", #check=recurring
                          ),
                        M("Map", m="map"),
                        M("Report", m="report"),
                        M("Search All Requested Skills", f="req_skill"),
                    ),
                    M("Commitments", f="commit", #check=use_commit
                      )(),
                    M("Facilities", c="req", f="facility")(
                        M("Create", m="create", t="org_facility"),
                    ),
                )
                    
    # -------------------------------------------------------------------------
    @staticmethod
    def vol():
        """ Volunteer Management """

        auth = current.auth
        has_role = auth.s3_has_role
        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN
        root_org = auth.root_org_name()

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        manager_mode = lambda i: s3.hrm.mode is None
        personal_mode = lambda i: s3.hrm.mode is not None
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 has_role(ADMIN)
        is_super_editor = lambda i: has_role("vol_super") or \
                                    has_role("staff_super")

        settings = current.deployment_settings
        use_certs = lambda i: settings.get_hrm_use_certificates()
        show_programmes = lambda i: settings.get_hrm_vol_experience() == "programme"
        show_tasks = lambda i: settings.has_module("project") and \
                               settings.get_project_mode_task()
        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams

        return M(c="vol")(
                    M("Volunteers", f="volunteer", m="summary",
                      check=[manager_mode])(
                        M("Create", m="create"),
                        M("Import", f="person", m="import",
                          vars={"group":"volunteer"}, p="create"),
                    ),
                    M("Staff & Volunteers (Combined)",
                      c="vol", f="human_resource", m="summary",
                      check=[manager_mode, is_super_editor]),
                    M(teams, f="group",
                      check=[manager_mode, use_teams])(
                        M("Create", m="create"),
                        M("Search Members", f="group_membership"),
                        M("Import", f="group_membership", m="import"),
                    ),
                    #M("Department Catalog", f="department",
                    #  check=manager_mode)(
                    #    M("Create", m="create"),
                    #),
                    M("Volunteer Role Catalog", f="job_title",
                      check=[manager_mode])(
                        M("Create", m="create"),
                        M("Import", m="import", p="create", check=is_org_admin),
                    ),
                    #M("Skill Catalog", f="skill",
                    #  check=[manager_mode])(
                    #    M("Create", m="create"),
                    #    #M("Skill Provisions", f="skill_provision"),
                    #),
                    M("Training Events", f="training_event",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("Search Training Participants", f="training"),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Training Course Catalog", f="course",
                      check=manager_mode)(
                        M("Create", m="create"),
                        #M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", f="certificate",
                      check=[manager_mode, use_certs])(
                        M("Create", m="create"),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("Programs", f="programme",
                      check=[manager_mode, show_programmes])(
                        M("Create", m="create"),
                        M("Import Hours", f="programme_hours", m="import"),
                    ),
                    M("Awards", f="award",
                      check=[manager_mode, is_org_admin])(
                        M("Create", m="create"),
                    ),
                    M("Reports", f="volunteer", m="report",
                      check=manager_mode)(
                        M("Volunteer Report", m="report"),
                        M("Hours by Role Report", f="programme_hours", m="report",
                          vars=Storage(rows="job_title_id",
                                       cols="month",
                                       fact="sum(hours)"),
                          check=show_programmes),
                        M("Hours by Program Report", f="programme_hours", m="report",
                          vars=Storage(rows="programme_id",
                                       cols="month",
                                       fact="sum(hours)"),
                          check=show_programmes),
                        M("Training Report", f="training", m="report"),
                    ),
                    #M("My Profile", f="person",
                    #  check=personal_mode, vars=dict(access="personal")),
                    M("My Tasks", f="task",
                      check=[personal_mode, show_tasks],
                      vars=dict(access="personal",
                                mine=1)),
                    # This provides the link to switch to the manager mode:
                    M("Volunteer Management", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    #M("Personal Profile", f="person",
                    #  check=manager_mode, vars=dict(access="personal"))
                )

# END =========================================================================
