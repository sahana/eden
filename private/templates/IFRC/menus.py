# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from eden.layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import eden.menus as default

red_cross_filter = {"organisation.organisation_type_id$name" : "Red Cross / Red Crescent"}

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
        current.menu.dashboard = cls.menu_dashboard()

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        T = current.T

        return [
            homepage("gis")(
            ),
            homepage("hrm", "org", name=T("Staff"),
                    vars=dict(group="staff"))(
                MM("Staff", c="hrm", f="staff"),
                MM("Teams", c="hrm", f="group"),
                MM("National Societies", c="org", f="organisation",
                    vars = red_cross_filter),
                MM("Offices", c="org", f="office"),
                MM("Job Titles", c="hrm", f="job_title"),
                #MM("Skill List", c="hrm", f="skill"),
                MM("Training Events", c="hrm", f="training_event"),
                MM("Training Courses", c="hrm", f="course"),
                MM("Certificate List", c="hrm", f="certificate"),
            ),
            homepage("vol", name=T("Volunteers"))(
                MM("Volunteers", c="vol", f="volunteer"),
                MM("Teams", c="vol", f="group"),
                MM("Volunteer Roles", c="vol", f="job_title"),
                #MM("Skill List", c="vol", f="skill"),
                MM("Training Events", c="vol", f="training_event"),
                MM("Training Courses", c="vol", f="course"),
                MM("Certificate List", c="vol", f="certificate"),
            ),
            homepage("member")(
                MM("Members", c="member", f="membership"),
            ),
            homepage("inv", "supply", "req")(
                MM("Warehouses", c="inv", f="warehouse"),
                MM("Received Shipments", c="inv", f="recv"),
                MM("Sent Shipments", c="inv", f="send"),
                MM("Items", c="supply", f="item"),
                MM("Item Catalogues", c="supply", f="catalog"),
                MM("Item Categories", c="supply", f="item_category"),
                M("Requests", c="req", f="req")(),
                #M("Commitments", f="commit")(),
            ),
            homepage("asset")(
                MM("Assets", c="asset", f="asset"),
                MM("Items", c="asset", f="item"),
            ),
            homepage("survey")(
                MM("Assessment Templates", c="survey", f="template"),
                MM("Disaster Assessments", c="survey", f="series"),
            ),
            homepage("project")(
                MM("Projects", c="project", f="project"),
                MM("Communities", c="project", f="location"),
            ),
            homepage("vulnerability")(
                MM("Map", c="vulnerability", f="index"),
            ),
            #homepage("event", "irs")(
            #    MM("Events", c="event", f="event"),
            #    MM("Incident Reports", c="irs", f="ireport"),
            #)
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_dashboard(cls):
        """ Dashboard Menu (at bottom of page) """

        DB = S3DashBoardMenuLayout
        request = current.request

        if request.controller == "vol":
            dashboard = DB()(
                DB("VOLUNTEERS",
                    c="vol",
                    image = "graphic_staff_wide.png",
                    title = "Volunteers")(
                    DB("Manage Volunteer Data", f="volunteer"),
                    DB("Manage Teams Data", f="group"),
                ),
                DB("CATALOGS",
                    c="hrm",
                    image="graphic_catalogue.png",
                    title="Catalogs")(
                    DB("Certificates", f="certificate"),
                    DB("Training Courses", f="course"),
                    #DB("Skills", f="skill"),
                    DB("Job Titles", f="job_title")
                ))
        elif request.controller in ("hrm", "org"):
            dashboard = DB()(
                DB("STAFF",
                    c="hrm",
                    image = "graphic_staff_wide.png",
                    title = "Staff")(
                    DB("Manage Staff Data", f="staff"),
                    DB("Manage Teams Data", f="group"),
                ),
                DB("OFFICES",
                    c="org",
                    image = "graphic_office.png",
                    title = "Offices")(
                    DB("Manage Offices Data", f="office"),
                    DB("Manage National Society Data", f="organisation"),
                ),
                DB("CATALOGS",
                    c="hrm",
                    image="graphic_catalogue.png",
                    title="Catalogs")(
                    DB("Certificates", f="certificate"),
                    DB("Training Courses", f="course"),
                    #DB("Skills", f="skill"),
                    DB("Job Titles", f="job_title")
                ))

        elif request.controller == "default" and request.function == "index":

            dashboard = DB(_id="dashboard")(
                DB("Staff", c="hrm", f="staff", m="search",
                   image = "graphic_staff.png",
                   title = "Staff",
                   text = "Add new and manage existing staff."),
                DB("Volunteers", c="vol", f="volunteer", m="search",
                   image = "graphic_volunteers.png",
                   title = "Volunteers",
                   text = "Add new and manage existing volunteers."),
                DB("Members", c="member", f="index",
                   image = "graphic_members.png",
                   title = "Members",
                   text = "Add new and manage existing members."),
                DB("Warehouses", c="inv", f="index",
                   image = "graphic_warehouse.png",
                   title = "Warehouses",
                   text = "Stocks and relief items."),
                DB("Assets", c="asset", f="index",
                   image = "graphic_assets.png",
                   title = "Assests",
                   text = "Manage office inventories and assets."),
                DB("Assessments", c="survey", f="index",
                   image = "graphic_assessments.png",
                   title = "Assessments",
                   text = "Design, deploy & analyze surveys."),
                DB("Projects", c="project", f="index",
                   image = "graphic_tools.png",
                   title = "Projects",
                   text = "Tracking and analysis of Projects and Activities.")
            )

        else:
            dashboard = None

        return dashboard

    # -------------------------------------------------------------------------
    @classmethod
    def menu_personal(cls):
        """ Custom Personal Menu """

        auth = current.auth
        s3 = current.response.s3
        settings = current.deployment_settings

        # Language selector
        menu_lang = ML("Language", right=True)
        for language in s3.l10n_languages.items():
            code, name = language
            menu_lang(
                ML(name, translate=False, lang_code=code, lang_name=name)
            )

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
                        menu_lang
            )
        else:
            s3_has_role = auth.s3_has_role
            ADMIN = auth.get_system_roles().ADMIN
            menu_personal = MP()(
                        MP("Administration", c="admin", f="index",
                           check=s3_has_role(ADMIN)),
                        MP("Profile", c="default", f="person"),
                        MP("Change Password", c="default", f="user",
                           m="change_password"),
                        MP("Logout", c="default", f="user",
                           m="logout"),
                        menu_lang,
            )
        return menu_personal

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    def hrm(self):
        """ HRM Human Resource Management """

        session = current.session

        if "hrm" not in session.s3:
            current.s3db.hrm_vars()
        hrm_vars = session.s3.hrm

        ADMIN = current.auth.get_system_roles().ADMIN

        manager_mode = lambda i: hrm_vars.mode is None
        personal_mode = lambda i: hrm_vars.mode is not None
        is_org_admin = lambda i: hrm_vars.orgs and True or \
                                 ADMIN in session.s3.roles

        staff = {"group":"staff"}

        return M()(
                    M("Staff", c="hrm", f=("staff", "person"),
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", f="person", m="import",
                          vars=staff, p="create"),
                    ),
                    M("Teams", c="hrm", f="group",
                      check=manager_mode)(
                        M("New Team", m="create"),
                        M("List All"),
                    ),
                    M("National Societies", c="org", 
                                            f="organisation",
                                            vars = red_cross_filter,
                      check=manager_mode)(
                        M("New", m="create",vars = red_cross_filter,),
                        M("List All", vars = red_cross_filter,),
                        M("Search", m="search", vars = red_cross_filter,),
                        M("Import", m="import", p="create", check=is_org_admin)
                    ),
                    M("Offices", c="org", f="office",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Department Catalog", c="hrm", f="department",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Job Title Catalog", c="hrm", f="job_title",
                      check=manager_mode)(
                        M("New Job Title", m="create"),
                        M("List All"),
                        M("Import", m="import", p="create", check=is_org_admin),
                    ),
                    #M("Skill Catalog", f="skill",
                      #check=manager_mode)(
                        #M("New Skill", m="create"),
                        #M("List All"),
                        ##M("Skill Provisions", f="skill_provision"),
                    #),
                    M("Training Events", c="hrm", f="training_event",
                      check=manager_mode)(
                        M("New Training Event", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Search Training Participants", f="training",
                          m="search"),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Reports", c="hrm", f="staff", m="report",
                      check=manager_mode)(
                        M("Staff Report", m="report"),
                        M("Expiring Staff Contracts Report",
                          vars=dict(expiring=1)),
                        M("Training Report", f="training", m="report"),
                    ),
                    M("Training Course Catalog", c="hrm", f="course",
                      check=manager_mode)(
                        M("New Training Course", m="create"),
                        M("List All"),
                        M("Import", m="import", p="create", check=is_org_admin),
                        M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", c="hrm", f="certificate",
                      check=manager_mode)(
                        M("New Certificate", m="create"),
                        M("List All"),
                        M("Import", m="import", p="create", check=is_org_admin),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    #M("My Profile", c="hrm", f="person",
                    #  check=personal_mode, vars=dict(mode="personal")),
                    # This provides the link to switch to the manager mode:
                    M("Human Resources", c="hrm", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    #M("Personal Profile", c="hrm", f="person",
                    #  check=manager_mode, vars=dict(mode="personal"))
                )

    # -------------------------------------------------------------------------
    def vol(self):
        """ Volunteer Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        manager_mode = lambda i: s3.hrm.mode is None
        personal_mode = lambda i: s3.hrm.mode is not None
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 ADMIN in s3.roles

        settings = current.deployment_settings
        #job_roles = lambda i: settings.get_hrm_job_roles()
        show_programmes = lambda i: settings.get_hrm_vol_experience() == "programme"
        show_tasks = lambda i: settings.has_module("project") and \
                               settings.get_project_mode_task()
        use_teams = lambda i: settings.get_hrm_use_teams()

        check_org_dependent_field = lambda tablename, fieldname: \
            settings.set_org_dependent_field(tablename, fieldname,
                                             enable_field = False)

        #if job_roles(""):
        #    jt_catalog_label = "Job Title Catalog"
        #else:
        jt_catalog_label = "Volunteer Role Catalog"

        return M(c="vol")(
                    M("Volunteers", f="volunteer",
                      check=[manager_mode])(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", f="person", m="import",
                          vars={"group":"volunteer"}, p="create"),
                    ),
                    M("Teams", f="group",
                      check=[manager_mode, use_teams])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Department Catalog", f="department",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    #M("Job Role Catalog", f="job_role",
                    #  check=[manager_mode, job_roles])(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #),
                    M(jt_catalog_label, f="job_title",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    #M("Skill Catalog", f="skill",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    #M("Skill Provisions", f="skill_provision"),
                    #),
                    M("Training Events", f="training_event",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Search Training Participants", f="training",
                          m="search"),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Training Course Catalog", f="course",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        #M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", f="certificate",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("Programmes", f="programme",
                      check=[manager_mode, show_programmes])(
                        M("New", m="create"),
                        M("List All"),
                        M("Import Hours", f="programme_hours", m="import"),
                    ),
                    M("Volunteer Cluster Type", f="cluster_type",
                      check = check_org_dependent_field("vol_volunteer_cluster",
                                                        "vol_cluster_type_id"))(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Volunteer Cluster", f="cluster",
                      check = check_org_dependent_field("vol_volunteer_cluster",
                                                        "vol_cluster_id"))(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Volunteer Cluster Position", f="cluster_position",
                      check = check_org_dependent_field("vol_volunteer_cluster",
                                                        "vol_cluster_position_id"))(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Reports", f="volunteer", m="report",
                      check=manager_mode)(
                        M("Volunteer Report", m="report"),
                        M("Training Report", f="training", m="report"),
                    ),
                    #M("My Profile", f="person",
                    #  check=personal_mode, vars=dict(mode="personal")),
                    M("My Tasks", f="task",
                      check=[personal_mode, show_tasks],
                      vars=dict(mode="personal",
                                mine=1)),
                    # This provides the link to switch to the manager mode:
                    M("Volunteer Management", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    #M("Personal Profile", f="person",
                    #  check=manager_mode, vars=dict(mode="personal"))
                )

    # -------------------------------------------------------------------------
    def irs(self):
        """ IRS Incident Reporting """

        return M()(
                    M("Events", c="event", f="event")(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Incident Reports", c="irs", f="ireport")(
                        M("New", m="create"),
                        M("List All"),
                        M("Open Incidents", vars={"open":1}),
                        M("Timeline", args="timeline"),
                        M("Search", m="search"),
                    ),
                    M("Incident Categories", c="irs", f="icategory",
                      check=current.auth.s3_has_role(ADMIN))(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Reports", c="irs", f="ireport",  m="report")(
                        M("Incident Reports"),
                    ),
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ Organisation Management """

        # Same as HRM
        return self.hrm()
    
    # -------------------------------------------------------------------------
    def req(self):
        """ Organisation Management """

        # Same as Inventory
        return self.inv()
    # -------------------------------------------------------------------------
    def event(self):
        """ Event Management """

        # Same as IRS
        return self.irs()
    

# END =========================================================================

