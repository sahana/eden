# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from s3layouts import *
try:
    # Nice to not have to copy this file, but currently imported in s3layouts.py
    #from templates.IFRC.layouts import *
    from .layouts import *
except ImportError:
    pass
import s3menus as default

#red_cross_filter = {"organisation_type.name" : "Red Cross / Red Crescent"}

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
        current.menu.org = cls.menu_org()

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        T = current.T

        return [
            homepage("gis")(
            ),
            homepage("cms", f="newsfeed", m="datalist", name=T("News"))(
            ),
            homepage("event", name= "Situational Awareness")(
                MM("Incidents", c="event", f="incident"),
                #MM("Incident Reports", c="event", f="incident_report"),
                MM("Deployments", c="deploy", f="mission"),
                MM("Assessments", c="survey", f="series"),
                MM("Situation Reports", c="doc", f="sitrep"),
                MM("Messages", c="msg", f="index"),
                # Have as a Tab on the Incident?
                #MM("Budgets", c="budget", f="budget"),
                # Have as a Tab on the Incident?
                #MM("Assignments", c="deploy", f="assignment"),
            ),
            #homepage("sit", "survey")(
            #    MM("Assessment Templates", c="survey", f="template"),
            #    MM("Assessments", c="survey", f="series"),
            #    MM("Situation Reports", c="sit", f="report"),
            #),
            #homepage("deploy", f="mission", m="summary",
            #         vars={"~.status__belongs": "2"})(
            #    MM("Missions", c="deploy", f="mission", m="summary"),
            #    MM("Human Resources", c="deploy", f="human_resource", m="summary"),
            #),
            homepage("cr", name="Operations Management")(
                MM("Budgets", c="budget", f="budget"),
                MM("Requests", c="req", f="req"),
                MM("Received Shipments", c="inv", f="recv"),
                MM("Sent Shipments", c="inv", f="send"),
                MM("Shelters", c="cr", f="shelter", m="summary"),
                MM("Warehouses", c="inv", f="warehouse"),
            ),
            homepage("project")(
                MM("Projects", c="project", f="project"),
                #MM("Communities", c="project", f="location"),
                MM("Tasks", c="project", f="task"),
            ),
            homepage("hrm", "org", "vol", "asset", name=T("Resources"),
                     vars=dict(group="staff"))(
                MM("Staff", c="hrm", f="staff", m="summary"),
                MM("Volunteers", c="vol", f="volunteer", m="summary"),
                MM("Teams", c="hrm", f="group"),
                MM("Organizations", c="org", f="organisation",
                   #vars = red_cross_filter
                   ),
                MM("Facilities", c="org", f="facility", m="summary"),
                MM("Offices", c="org", f="office", m="summary"),
                MM("Job Titles", c="hrm", f="job_title"),
                #MM("Skill List", c="hrm", f="skill"),
                MM("Training Events", c="hrm", f="training_event"),
                MM("Training Courses", c="hrm", f="course"),
                MM("Certificate List", c="hrm", f="certificate"),
                MM("Assets", c="asset", f="asset", m="summary"),
                MM("Items", c="supply", f="item"),
                MM("Vehicles", c="vehicle", f="vehicle", m="summary"),
            ),
            #homepage("vol", name=T("Volunteers"))(
            #    MM("Volunteers", c="vol", f="volunteer", m="summary"),
            #    MM("Teams", c="vol", f="group"),
            #    MM("Volunteer Roles", c="vol", f="job_title"),
            #    MM("Programs", c="vol", f="programme"),
            #    #MM("Skill List", c="vol", f="skill"),
            #    MM("Training Events", c="vol", f="training_event"),
            #    MM("Training Courses", c="vol", f="course"),
            #    MM("Certificate List", c="vol", f="certificate"),
            #),
            #homepage("member")(
            #    MM("Members", c="member", f="membership", m="summary"),
            #),
            #homepage("cr", "inv", "org", name="Facilities")(
            #    MM("Facilities", c="org", f="facility", m="summary"),
            #    MM("Offices", c="org", f="office", m="summary"),
            #    MM("Shelters", c="cr", f="shelter", m="summary"),
            #    MM("Warehouses", c="inv", f="warehouse", m="summary"),
            #),
            #homepage("asset")(
            #    MM("Assets", c="asset", f="asset", m="summary"),
            #    MM("Items", c="asset", f="item", m="summary"),
            #    MM("Vehicles", c="vehicle", f="vehicle", m="summary"),
            #),
            #homepage("inv", "supply", "req", name="Inventory")(
            #    MM("Warehouses", c="inv", f="warehouse"),
            #    MM("Received Shipments", c="inv", f="recv"),
            #    MM("Sent Shipments", c="inv", f="send"),
            #    MM("Items", c="supply", f="item"),
            #    MM("Item Catalogs", c="supply", f="catalog"),
            #    MM("Item Categories", c="supply", f="item_category"),
            #    MM("Requests", c="req", f="req"),
            #    #MM("Commitments", f="commit"),
            #),
            #homepage("vulnerability")(
            #    MM("Map", c="vulnerability", f="index"),
            #),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_dashboard(cls):
        """ Dashboard Menu (at bottom of page) """

        DB = S3DashBoardMenuLayout
        request = current.request
        controller = request.controller

        if controller == "vol":
            dashboard = DB()(
                DB("Volunteers",
                    c="vol",
                    image = "graphic_staff_wide.png",
                    title = "Volunteers")(
                    DB("Manage Volunteer Data", f="volunteer", m="summary"),
                    DB("Manage Teams Data", f="group"),
                ),
                DB("Catalogs",
                    c="hrm",
                    image="graphic_catalogue.png",
                    title="Catalogs")(
                    DB("Certificates", f="certificate"),
                    DB("Training Courses", f="course"),
                    #DB("Skills", f="skill"),
                    DB("Job Titles", f="job_title")
                ))
        elif controller in ("hrm", "org"):
            dashboard = DB()(
                DB("Staff",
                    c="hrm",
                    image = "graphic_staff_wide.png",
                    title = "Staff")(
                    DB("Manage Staff Data", f="staff", m="summary"),
                    DB("Manage Teams Data", f="group"),
                ),
                DB("Offices",
                    c="org",
                    image = "graphic_office.png",
                    title = "Offices")(
                    DB("Manage Offices Data", f="office"),
                    DB("Manage Organizations", f="organisation",
                       #vars=red_cross_filter
                       ),
                ),
                DB("Catalogs",
                    c="hrm",
                    image="graphic_catalogue.png",
                    title="Catalogs")(
                    DB("Certificates", f="certificate"),
                    DB("Training Courses", f="course"),
                    #DB("Skills", f="skill"),
                    DB("Job Titles", f="job_title")
                ))

        elif controller == "default" and request.function == "index":

            dashboard = DB(_id="dashboard")(
                DB("Assessments", c="survey", f="index",
                   image = "graphic_assessments.png",
                   title = "Assessments",
                   text = "Design, deploy & analyze surveys."),
                DB("Projects", c="project", f="index",
                   image = "graphic_tools.png",
                   title = "Projects",
                   text = "Tracking and analysis of Projects and Activities."),
                DB("Staff", c="hrm", f="staff", m="summary",
                   image = "graphic_staff.png",
                   title = "Staff",
                   text = "Add new and manage existing staff."),
                DB("Volunteers", c="vol", f="volunteer", m="summary",
                   image = "graphic_volunteers.png",
                   title = "Volunteers",
                   text = "Add new and manage existing volunteers."),
                #DB("Members", c="member", f="membership", m="summary",
                #   image = "graphic_members.png",
                #   title = "Members",
                #   text = "Add new and manage existing members."),
                DB("Assets", c="asset", f="index",
                   image = "graphic_assets.png",
                   title = "Assets",
                   text = "Manage office inventories and assets."),
                DB("Warehouses", c="inv", f="index",
                   image = "graphic_warehouse.png",
                   title = "Warehouses",
                   text = "Stocks and relief items."),
            )

        else:
            dashboard = None

        return dashboard

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Custom Organisation Menu """

        OM = S3OrgMenuLayout
        return OM()

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

            self_registration = settings.get_security_registration_visible()
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
            is_org_admin = lambda i: s3_has_role("ORG_ADMIN") and \
                                     not s3_has_role("ADMIN")
            menu_personal = MP()(
                        MP("Administration", c="admin", f="index",
                           check=s3_has_role("ADMIN")),
                        MP("Administration", c="admin", f="user",
                           check=is_org_admin),
                        MP("Profile", c="default", f="person"),
                        MP("Subscription", c="default", f="index", args=["subscriptions"]),
                        # Allow space for 'Subscription'
                        #MP("Change Password", c="default", f="user",
                        MP("Password", c="default", f="user",
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
    def admin(self):
        """ ADMIN menu """

        menu = super(S3OptionsMenu, self).admin()
        gis_item = M("Map Settings", c="gis", f="config")
        menu.append(gis_item)

        return menu

    # -------------------------------------------------------------------------
    @staticmethod
    def asset():
        """ ASSET Controller """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="asset")(
                    M("Assets", f="asset", m="summary")(
                        M("Create", m="create"),
                        #M("Map", m="map"),
                        M("Import", m="import", p="create"),
                    ),
                    #M("Brands", f="brand",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    M("Items", f="item", m="summary")(
                        M("Create", m="create"),
                        M("Import", f="catalog_item", m="import", p="create"),
                    ),
                    M("Item Categories", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Catalogs", f="catalog",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Suppliers", f="supplier")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Vehicles", c="vehicle" , f="vehicle")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                        M("Map", m="map"),
                    ),
                    M("Vehicle Types", c="vehicle", f="vehicle_type")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    def doc(self):
        """ Situation Reports """

        # Same as Events
        return self.event()

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ Incidents """

        return M()(
                    #M("Events", c="event", f="event")(
                    #    M("Create", m="create"),
                    #),
                    M("Incidents", c="event", f="incident", args="summary")(
                        M("Create", m="create"),
                    ),
                    #M("Incident Reports", c="event", f="incident_report")(
                    #    M("Create", m="create"),
                    #    #M("Open Incidents", vars={"open": 1}),
                    #    M("Map", m="map"),
                    #    #M("Timeline", args="timeline"),
                    #    M("Report", m="report")
                    #),
                    M("Assessments", c="survey", f="series")(
                        M("Create", m="create"),
                    ),
                    M("Situation Reports", c="doc", f="sitrep")(
                        M("Create", m="create"),
                    ),
                    M("Incident Types", c="event", f="incident_type",
                      check=current.auth.s3_has_role(current.session.s3.system_roles.ADMIN))(
                        M("Create", m="create"),
                    ),
                    #M("Reports", c="event", f="incident_report",  m="report")(
                    #    M("Incident Reports", m="report"),
                    #),
                )

    # -------------------------------------------------------------------------
    def gis(self):
        """ GIS / Mapping """

        if current.request.function == "index":
            # Empty so as to leave maximum space for the Map
            # - functionality accessible via the Admin menu instead
            return None
        else:
            return super(S3OptionsMenu, self).gis()

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM / Human Resource Management """

        session = current.session
        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        if "hrm" not in s3:
            current.s3db.hrm_vars()
        hrm_vars = s3.hrm

        SECTORS = "Clusters" if current.deployment_settings.get_ui_label_cluster() \
                             else "Sectors"

        manager_mode = lambda i: hrm_vars.mode is None
        personal_mode = lambda i: hrm_vars.mode is not None
        is_org_admin = lambda i: hrm_vars.orgs and True or \
                                 ADMIN in s3.roles
        is_super_editor = lambda i: current.auth.s3_has_role("staff_super") or \
                                    current.auth.s3_has_role("vol_super")

        staff = {"group": "staff"}

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
                                            #vars=red_cross_filter,
                      check=manager_mode)(
                        M("Create", m="create",
                          #vars=red_cross_filter
                          ),
                        M("Import", m="import", p="create", check=is_org_admin)
                    ),
                    M("Offices", c="org", f="office",
                      check=manager_mode)(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Facilities", c="org", f="facility")(
                        M("Create", m="create"),
                    ),
                    M("Facility Types", c="org", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
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
                      check=manager_mode)(
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
    @staticmethod
    def inv():
        """ INV / Inventory """

        ADMIN = current.session.s3.system_roles.ADMIN

        s3db = current.s3db
        s3db.inv_recv_crud_strings()
        inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        #settings = current.deployment_settings
        #use_adjust = lambda i: not settings.get_inv_direct_stock_edits()
        #def use_adjust(i):
        #    db = current.db
        #    otable = s3db.org_organisation
        #    try:
        #        ausrc = db(otable.name == "Australian Red Cross").select(otable.id,
        #                                                                 limitby=(0, 1)
        #                                                                 ).first().id
        #    except:
        #        # No IFRC prepop done - skip (e.g. testing impacts of CSS changes in this theme)
        #        return False
        #    if current.auth.root_org() == ausrc:
        #        # AusRC use proper Logistics workflow
        #        return True
        #    else:
        #        # Others use simplified version
        #        return False
        #use_commit = lambda i: settings.get_req_use_commit()

        return M()(
                    #M("Home", f="index"),
                    M("Warehouses", c="inv", f="warehouse")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Warehouse Stock", c="inv", f="inv_item")(
                        M("Search Shipped Items", f="track_item"),
                        #M("Adjust Stock Levels", f="adj", check=use_adjust),
                        #M("Kitting", f="kit"),
                        M("Import", f="inv_item", m="import", p="create"),
                    ),
                    M("Requests", c="req", f="req")(
                        M("Create", m="create"),
                        M("Requested Items", f="req_item"),
                        M("Recurring Requests", f="req_template"),
                    ),
                    #M("Commitments", c="req", f="commit", check=use_commit)(
                    #),
                    M("Reports", c="inv", f="inv_item")(
                        M("Warehouse Stock", f="inv_item",m="report"),
                        #M("Expiration Report", c="inv", f="track_item",
                        #  vars=dict(report="exp")),
                        #M("Monetization Report", c="inv", f="inv_item",
                        #  vars=dict(report="mon")),
                        #M("Utilization Report", c="inv", f="track_item",
                        #  vars=dict(report="util")),
                        #M("Summary of Incoming Supplies", c="inv", f="track_item",
                        #  vars=dict(report="inc")),
                        # M("Summary of Releases", c="inv", f="track_item",
                        #  vars=dict(report="rel")),
                    ),
                    M(inv_recv_list, c="inv", f="recv")(
                        M("Create", m="create"),
                    ),
                    M("Sent Shipments", c="inv", f="send")(
                        M("Create", m="create"),
                        M("Search Shipped Items", f="track_item"),
                    ),
                    M("Items", c="supply", f="item", m="summary")(
                        M("Create", m="create"),
                        M("Import", f="catalog_item", m="import", p="create"),
                    ),
                    # Catalog Items moved to be next to the Item Categories
                    #M("Catalog Items", c="supply", f="catalog_item")(
                    #   M("Create", m="create"),
                    #),
                    #M("Brands", c="supply", f="brand",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    M("Catalogs", c="supply", f="catalog")(
                        M("Create", m="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Suppliers", c="inv", f="supplier")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ Organisation Management """

        # Same as HRM
        return self.hrm()

    # -------------------------------------------------------------------------
    def req(self):
        """ Requests Management """

        # Same as Inventory
        return self.inv()

    # -------------------------------------------------------------------------
    def survey(self):
        """ Survey """

        # Same as Events
        return self.event()

        ADMIN = current.session.s3.system_roles.ADMIN

        # Do we have a series_id?
        series_id = False
        get_vars = Storage()
        try:
            series_id = int(current.request.args[0])
        except:
            try:
                (dummy, series_id) = current.request.get_vars["viewing"].split(".")
                series_id = int(series_id)
            except:
                pass
        if series_id:
            get_vars.viewing = "survey_complete.%s" % series_id

        return M(c="survey")(
                    M("Assessment Templates", f="template")(
                        M("Create", m="create"),
                    ),
                    #M("Section", f="section")(
                    #    M("Create", args="create"),
                    #),
                    M("Assessments", f="series")(
                        M("Create", m="create"),
                    ),
                    M("Situation Reports", c="sit", f="report")(
                        M("Create", m="create"),
                    ),
                    M("Administration", f="admin", restrict=[ADMIN])(
                        M("Import Templates", f="question_list",
                          m="import", p="create"),
                        M("Import Template Layout", f="formatter",
                          m="import", p="create"),
                        M("Import Completed Assessment Forms", f="complete",
                          m="import", p="create", vars=get_vars, check=series_id),
                    ),
                )

    # -------------------------------------------------------------------------
    def vehicle(self):
        return self.asset()

    # -------------------------------------------------------------------------
    @staticmethod
    def vol():
        """ Volunteer Management """

        auth = current.auth
        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        manager_mode = lambda i: s3.hrm.mode is None
        personal_mode = lambda i: s3.hrm.mode is not None
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 ADMIN in s3.roles
        is_super_editor = lambda i: auth.s3_has_role("vol_super") or \
                                    auth.s3_has_role("staff_super")

        settings = current.deployment_settings
        show_programmes = lambda i: settings.get_hrm_vol_experience() == "programme"
        show_tasks = lambda i: settings.has_module("project") and \
                               settings.get_project_mode_task()
        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams

        not_vnrc = lambda i: auth.root_org_name() != "Viet Nam Red Cross"
        skills_menu = lambda i: auth.root_org_name() in ("Afghan Red Crescent Society",
                                                         "Indonesian Red Cross Society (Pelang Merah Indonesia)",
                                                         "Viet Nam Red Cross",
                                                         )

        check_org_dependent_field = lambda tablename, fieldname: \
            settings.set_org_dependent_field(tablename, fieldname,
                                             enable_field = False)

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
                      check=[manager_mode, not_vnrc])(
                        M("Create", m="create"),
                        M("Import", m="import", p="create", check=is_org_admin),
                    ),
                    M("Skill Catalog", f="skill",
                      check=[manager_mode, skills_menu])(
                        M("Create", m="create"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
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
                      check=manager_mode)(
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
                    M("Volunteer Cluster Type", f="cluster_type",
                      check = check_org_dependent_field("vol_volunteer_cluster",
                                                        "vol_cluster_type_id"))(
                        M("Create", m="create"),
                    ),
                    M("Volunteer Cluster", f="cluster",
                      check = check_org_dependent_field("vol_volunteer_cluster",
                                                        "vol_cluster_id"))(
                        M("Create", m="create"),
                    ),
                    M("Volunteer Cluster Position", f="cluster_position",
                      check = check_org_dependent_field("vol_volunteer_cluster",
                                                        "vol_cluster_position_id"))(
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
