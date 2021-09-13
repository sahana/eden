# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

red_cross_filter = {"organisation_type.name" : "Red Cross / Red Crescent"}
ARCS = "Afghan Red Crescent Society"
CRMADA = "Malagasy Red Cross Society"
#HNRC = "Honduran Red Cross"
IRCS = "Iraqi Red Crescent Society"
NRCS = "Nepal Red Cross Society"
NZRC = "New Zealand Red Cross"

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

        system_roles = current.session.s3.system_roles
        ADMIN = system_roles.ADMIN

        T = current.T
        auth = current.auth
        has_role = auth.s3_has_role
        s3db = current.s3db

        if not has_role(ADMIN):
            if auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
                # Simplified menu for Bangkok CCST
                return [homepage("hrm", "org", name=T("Training Events"), f="training_event",
                                 #vars={"group": "staff"}, check=hrm)(
                                 vars={"group": "staff"})(
                            #MM("Training Events", c="hrm", f="training_event"),
                            #MM("Trainings", c="hrm", f="training"),
                            #MM("Training Courses", c="hrm", f="course"),
                            ),
                        ]
            elif not has_role("RDRT_ADMIN") and has_role("RDRT_MEMBER"):
                # Simplified menu for AP RDRT
                return []

        settings = current.deployment_settings

        root_org = auth.root_org_name()
        ORG_ADMIN = system_roles.ORG_ADMIN

        s3db.inv_recv_crud_strings()
        inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        vol_activities = lambda i: True if root_org == CRMADA else False

        use_certs = lambda i: settings.get_hrm_use_certificates()

        vol_programmes = lambda i: settings.get_hrm_vol_experience() in ("programme", "both")

        #def hrm(item):
        #    return root_org != HNRC or \
        #           has_role(ORG_ADMIN)

        #def inv(item):
        #    return root_org != HNRC or \
        #           has_role("hn_wh_manager") or \
        #           has_role("hn_national_wh_manager") or \
        #           has_role(ORG_ADMIN)

        #def basic_warehouse(i):
        #    if root_org == HNRC  and \
        #       not (has_role("hn_national_wh_manager") or \
        #            has_role(ORG_ADMIN)):
        #        # Hide menu entries which user shouldn't need access to
        #        return False
        #    else:
        #        return True

        #def multi_warehouse(i):
        #    if root_org == HNRC and \
        #       not (has_role("hn_national_wh_manager") or \
        #            has_role(ORG_ADMIN)):
        #        # Only responsible for 1 warehouse so hide menu entries which should be accessed via Tabs on their warehouse
        #        return False
        #    else:
        #        return True

        def outreach(item):
            return root_org == NZRC or \
                   root_org is None and has_role(ADMIN)

        #def rdrt_admin(item):
        #    return has_role("RDRT_ADMIN")

        #def vol(item):
        #    return root_org != HNRC or \
        #           has_role(ORG_ADMIN)

        def vol_roles(item):
            return root_org != IRCS

        def vol_teams(item):
            return root_org != IRCS

        return [
            homepage("gis")(
            ),
            homepage("hrm", "org", name=T("Staff"),
                     #vars={"group": "staff"}, check=hrm)(
                     vars={"group": "staff"})(
                MM("Staff", c="hrm", f="staff", m="summary"),
                MM("Teams", c="hrm", f="group"),
                MM("National Societies", c="org", f="organisation",
                   vars = red_cross_filter),
                MM("Offices", c="org", f="office"),
                MM("Job Titles", c="hrm", f="job_title"),
                #MM("Skill List", c="hrm", f="skill"),
                MM("Training Events", c="hrm", f="training_event"),
                MM("Training Courses", c="hrm", f="course"),
                MM("Certificate List", c="hrm", f="certificate", check=use_certs),
            ),
            #homepage("vol", name=T("Volunteers"), check=vol)(
            homepage("vol", name=T("Volunteers"))(
                MM("Volunteers", c="vol", f="volunteer", m="summary"),
                MM("Teams", c="vol", f="group", check=vol_teams),
                MM("Volunteer Roles", c="vol", f="job_title", check=vol_roles),
                MM("Activities", c="vol", f="activity", check=vol_activities),
                MM("Programs", c="vol", f="programme", check=vol_programmes),
                #MM("Skill List", c="vol", f="skill"),
                MM("Training Events", c="vol", f="training_event"),
                MM("Training Courses", c="vol", f="course"),
                MM("Certificate List", c="vol", f="certificate", check=use_certs),
            ),
            homepage("member")(
                MM("Members", c="member", f="membership", m="summary"),
            ),
            #homepage("inv", "supply", "req", check=inv)(
            homepage("inv", "supply", "req")(
                #MM("Warehouses", c="inv", f="warehouse", m="summary", check=multi_warehouse),
                MM("Warehouses", c="inv", f="warehouse", m="summary"),
                #MM(inv_recv_list, c="inv", f="recv", check=multi_warehouse),
                MM(inv_recv_list, c="inv", f="recv"),
                #MM("Sent Shipments", c="inv", f="send", check=multi_warehouse),
                MM("Sent Shipments", c="inv", f="send"),
                #MM("Items", c="supply", f="item", check=basic_warehouse),
                MM("Items", c="supply", f="item"),
                #MM("Catalogs", c="supply", f="catalog", check=basic_warehouse),
                MM("Catalogs", c="supply", f="catalog"),
                ##MM("Item Categories", c="supply", f="item_category"),
                #M("Suppliers", c="inv", f="supplier", check=basic_warehouse)(),
                M("Suppliers", c="inv", f="supplier")(),
                #M("Facilities", c="inv", f="facility", check=basic_warehouse)(),
                M("Facilities", c="inv", f="facility")(),
                M("Requests", c="req", f="req")(),
                ##M("Commitments", f="commit")(),
            ),
            homepage("asset")(
                MM("Assets", c="asset", f="asset", m="summary"),
                MM("Items", c="asset", f="item", m="summary"),
            ),
            homepage("survey")(
                MM("Assessment Templates", c="survey", f="template"),
                MM("Disaster Assessments", c="survey", f="series"),
            ),
            homepage("project")(
                MM("Projects", c="project", f="project", m="summary"),
                MM("Communities", c="project", f="location"),
                MM("Outreach", c="po", f="index", check=outreach),
            ),
            homepage("vulnerability")(
                MM("Map", c="vulnerability", f="index"),
            ),
            homepage("event")(
                MM("Events", c="event", f="event", m="summary"),
                MM("Incident Reports", c="event", f="incident_report", m="summary"),
            ),
            homepage("deploy", name="Surge", f="mission", m="summary",
                     vars={"~.status__belongs": "2"})(
                MM("InBox", c="deploy", f="email_inbox"),
                MM("Missions", c="deploy", f="mission", m="summary"),
                MM("Members", c="deploy", f="human_resource", m="summary"),
            ),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_dashboard(cls):
        """ Dashboard Menu (at bottom of page) """

        DB = S3DashBoardMenuLayout
        auth = current.auth
        request = current.request
        controller = request.controller

        has_role = auth.s3_has_role
        root_org = auth.root_org_name()
        system_roles = current.session.s3.system_roles
        #ADMIN = system_roles.ADMIN
        ORG_ADMIN = system_roles.ORG_ADMIN

        def hrm(item):
            # @ToDo: Bot sure why this isn't hidden automatically when user doesn't have access
            return root_org != CRMADA or \
                   has_role(ORG_ADMIN)

        #def inv(item):
        #    return root_org != HNRC or \
        #           has_role("hn_wh_manager") or \
        #           has_role("hn_national_wh_manager") or \
        #           has_role(ORG_ADMIN)

        #def vol(item):
        #    return root_org != HNRC or \
        #           has_role(ORG_ADMIN)

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
                   DB("Manage National Society Data", f="organisation",
                      vars=red_cross_filter
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
                DB("Staff", c="hrm", f="staff", m="summary",
                   check = hrm,
                   image = "graphic_staff.png",
                   title = "Staff",
                   text = "Add new and manage existing staff."),
                DB("Volunteers", c="vol", f="volunteer", m="summary",
                   #check = vol,
                   image = "graphic_volunteers.png",
                   title = "Volunteers",
                   text = "Add new and manage existing volunteers."),
                DB("Members", c="member", f="membership", m="summary",
                   image = "graphic_members.png",
                   title = "Members",
                   text = "Add new and manage existing members."),
                DB("Warehouses", c="inv", f="warehouse", m="summary",
                   #check = inv,
                   image = "graphic_warehouse.png",
                   title = "Warehouses",
                   text = "Stocks and relief items."),
                DB("Assets", c="asset", f="index",
                   image = "graphic_assets.png",
                   title = "Assets",
                   text = "Manage office inventories and assets."),
                DB("Assessments", c="survey", f="index",
                   image = "graphic_assessments.png",
                   title = "Assessments",
                   text = "Design, deploy & analyze surveys."),
                DB("Projects", c="project", f="project", m="summary",
                   image = "graphic_tools.png",
                   title = "Projects",
                   text = "Tracking and analysis of Projects and Activities.")
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
        settings = current.deployment_settings
        languages = settings.get_L10n_languages()
        represent_local = IS_ISO639_2_LANGUAGE_CODE.represent_local

        # Language selector
        menu_lang = ML("Language", right=True)
        for code in languages:
            # Show Language in it's own Language
            lang_name = represent_local(code)
            menu_lang(
                ML(lang_name, translate=False, lang_code=code, lang_name=lang_name)
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
                           m="login", vars={"_next": login_next}),
                        MP("Lost Password", c="default", f="user",
                           m="retrieve_password"),
                        menu_lang
            )
        else:
            has_role = auth.s3_has_role
            ADMIN = has_role("ADMIN")
            if not ADMIN and has_role("RDRT_MEMBER") and not has_role("RDRT_ADMIN"):
                db = current.db
                s3db = current.s3db
                person_id = auth.s3_logged_in_person()
                atable = s3db.deploy_application
                htable = s3db.hrm_human_resource
                query = (atable.human_resource_id == htable.id) & \
                        (htable.person_id == person_id)
                member = db(query).select(htable.id,
                                          cache = s3db.cache,
                                          limitby = (0, 1),
                                          ).first()
                if member:
                    profile = MP("Profile", c="deploy", f="human_resource", args=[member.id, "profile"])
                else:
                    profile = MP("Profile", c="default", f="person")
            else:
                profile = MP("Profile", c="default", f="person")
            is_org_admin = lambda i: not ADMIN and has_role("ORG_ADMIN")
            menu_personal = MP()(
                        MP("Administration", c="admin", f="index",
                           check=has_role("ADMIN")),
                        MP("Administration", c="admin", f="user",
                           check=is_org_admin),
                        profile,
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
    @staticmethod
    def cms():
        """ CMS / Content Management System """

        return M(c="cms")(
                    M("Series", f="series")(
                        M("Create", m="create"),
                        M("View as Pages", f="blog"),
                     ),
                    M("Posts", f="post")(
                        M("Create", m="create"),
                        M("View as Pages", f="page"),
                        M("Import", m="import"),
                     ),
                 )

    # -------------------------------------------------------------------------
    def dc(self):
        """ Data Collection """

        # Currently only used in HRM (by CCST Bangkok)
        return self.hrm()

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy():
        """ Surge Register (RDRT Alerting and Deployments) """

        auth = current.auth
        user = auth.user
        organisation_id = user and user.organisation_id or None
        if organisation_id:
            db = current.db
            s3db = current.s3db
            ortable = s3db.org_organisation_region
            rtable = s3db.org_region
            query = (ortable.organisation_id == organisation_id) & \
                    (ortable.region_id == rtable.id)
            region = db(query).select(rtable.name,
                                      cache = s3db.cache,
                                      limitby = (0, 1)
                                      ).first()
            if region and region.name in ("Asia Pacific", "East Asia", "Pacific", "South Asia", "South East Asia"):
                # Asia-Pacific

                # Is the user an RDRT Member?
                person_id = auth.s3_logged_in_person()
                atable = s3db.deploy_application
                htable = s3db.hrm_human_resource
                query = (atable.human_resource_id == htable.id) & \
                        (htable.person_id == person_id)
                member = db(query).select(htable.id,
                                          cache = s3db.cache,
                                          limitby = (0, 1)
                                          ).first()
                if member:
                    profile = M("My Surge Profile",
                                c="deploy", f="human_resource",
                                args = [member.id, "profile"],
                                )
                else:
                    profile = None

                if auth.s3_has_role("RDRT_ADMIN"):
                    #gtable = s3db.pr_group
                    #group = db(gtable.name == "RDRT Focal Points").select(gtable.id,
                    #                                                      cache = s3db.cache,
                    #                                                      limitby=(0, 1)
                    #                                                      ).first()
                    #if group:
                    #    args = [group.id, "group_membership"]
                    #else:
                    #    args = "create"
                    #focal_points = M("Focal Points",
                    #                 c="deploy", f="group",
                    #                 args = args,
                    #                 )
                    inbox = M("InBox",
                              c="deploy", f="email_inbox",
                              )
                    #training = M("Training",
                    #             c="deploy", f="training", m="summary")(
                    #                M("Create", m="create"),
                    #                M("Search Training", m="summary"),
                    #                M("Import Training Participants", m="import"),
                    #             )
                    members = M("Surge Members",
                                 c="deploy", f="human_resource", m="summary")(
                                    #M("Find RDRT"),
                                    #M("Add Member",
                                    #  c="deploy", f="application", m="select",
                                    #  p="create", t="deploy_application",
                                    #  ),
                                    M("Import Members", c="deploy", f="person", m="import"),
                                    M("Report by Region", c="deploy", f="human_resource", m="report",
                                      vars=Storage(rows = "organisation_id$organisation_region.region_id",
                                                   cols = "organisation_id",
                                                   fact = "count(person_id)",
                                                   ),
                                      ),
                                    M("Report by CCST / CO", c="deploy", f="human_resource", m="report",
                                      vars=Storage(rows = "organisation_id$root_organisation$supported_by.name",
                                                   cols = "organisation_id",
                                                   fact = "count(person_id)",
                                                   ),
                                      ),
                               )
                    ttable = s3db.dc_template
                    template = db(ttable.name == "Surge Member").select(ttable.id,
                                                                        limitby=(0,1))
                    if template:
                        template_id = template.first().id
                    else:
                        template_id = None
                    return M()(M("Alerts",
                                 c="deploy", f="alert")(
                                    M("Create", m="create"),
                                    inbox,
                                    #focal_points,
                                    M("Settings",
                                      c="deploy", f="email_channel",
                                      p="update", t="msg_email_channel",
                                      ),
                                 ),
                               profile,
                               M("Missions",
                                 c="deploy", f="mission", m="summary")(
                                    M("Create", m="create"),
                                    M("Active Missions", m="summary",
                                      vars={"~.status__belongs": "2"}),
                                    M("Closed Missions", m="summary",
                                      vars={"~.status__belongs": "1"}),
                                 ),
                               #training,
                               M("Deployments",
                                 c="deploy", f="assignment", m="summary"
                                 ),
                               members,
                               M("Questions",
                                 c="dc", f="template", args=[template_id, "question"]
                                 ),
                               #M("Sectors",
                               #  c="deploy", f="job_title", restrict=["ADMIN"],
                               #  ),
                               #M("Online Manual", c="deploy", f="index"),
                               )
                else:
                    return M()(profile)

        # Africa (Default)
        return M()(M("Missions",
                     c="deploy", f="mission", m="summary")(
                        M("Create", m="create"),
                        M("Active Missions", m="summary",
                          vars={"~.status__belongs": "2"}),
                   ),
                   M("Alerts",
                     c="deploy", f="alert")(
                        M("Create", m="create"),
                        M("InBox",
                          c="deploy", f="email_inbox",
                        ),
                        M("Settings",
                          c="deploy", f="email_channel",
                          p="update", t="msg_email_channel",
                          ),
                   ),
                   M("Deployments",
                     c="deploy", f="assignment", m="summary"
                   ),
                   M("Sectors",
                     c="deploy", f="job_title", restrict=["ADMIN"],
                   ),
                   M("RDRT Members",
                     c="deploy", f="human_resource", m="summary")(
                        M("Add Member",
                          c="deploy", f="application", m="select",
                          p="create", t="deploy_application",
                          ),
                        M("Import Members", c="deploy", f="person", m="import"),
                   ),
                   M("Online Manual", c="deploy", f="index"),
               )

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
        """ Event Management """

        return M()(
                    M("Events", c="event", f="event")(
                        M("Create", m="create"),
                    ),
                    M("Event Types", c="event", f="event_type")(
                        M("Create", m="create"),
                        #M("Import", m="import", p="create"),
                    ),
                    M("Incident Reports", c="event", f="incident_report", m="summary")(
                        M("Create", m="create"),
                    ),
                    M("Incident Types", c="event", f="incident_type")(
                        M("Create", m="create"),
                        #M("Import", m="import", p="create"),
                    ),
                )

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

        auth = current.auth
        has_role = auth.s3_has_role
        ADMIN = current.session.s3.system_roles.ADMIN

        if not has_role(ADMIN) and auth.s3_has_roles(("EVENT_MONITOR", "EVENT_ORGANISER", "EVENT_OFFICE_MANAGER")):
            if has_role("EVENT_OFFICE_MANAGER"):
                # Just their Dashboard
                return M()(M("Training Events", c="hrm", f="training_event", vars={"dashboard": 1})())

            return M()(
                        M("Training Events", c="hrm", f="training_event")(
                            M("Create", m="create"),
                            M("Dashboard", vars={"dashboard": 1}),
                            M("Search Training Participants", f="training"),
                            M("Import Participant List", f="training", m="import"),
                        ),
                        M("Reports", c="hrm", f="staff", m="report")(
                            M("Training Report", f="training", m="report"),
                        ),
                        M("Staff", c="hrm", f=("staff", "person"), m="summary")(
                            #M("Create", m="create"),
                            #M("Import", f="person", m="import",
                            #  vars={"group": "staff"}, p="create"),
                            M("EOs", f="staff", m=None, vars={"eo": 1}),
                        ),
                        M("National Societies", c="org",
                                                f="organisation",
                                                vars=red_cross_filter)(
                            #M("Create", m="create",
                            #  vars=red_cross_filter
                            #  ),
                            #M("Import", m="import", p="create", check=is_org_admin)
                        ),
                        M("Offices", c="org", f="office")(
                            #M("Create", m="create"),
                            #M("Import", m="import", p="create"),
                        ),
                        M("Event Types", c="hrm", f="event_type",
                          restrict=["EVENT_MONITOR"])(
                            #M("Create", m="create"),
                        ),
                        M("Surveys", c="dc", f="target")(
                            M("Templates", f="template"),
                            M("Surveys", f="target"),
                            M("Responses", f="respnse"),
                        ),
                        M("Training Course Catalog", c="hrm", f="course")(
                            #M("Create", m="create"),
                            #M("Import", m="import", p="create", check=is_org_admin),
                            #M("Course Certificates", f="course_certificate"),
                        ),
                        M("AoF/SFI", c="hrm", f="strategy",
                          restrict=["EVENT_MONITOR"])(
                            #M("Create", m="create"),
                        ),
                        M("Programmes", c="hrm", f="programme")(
                            #M("Create", m="create"),
                        ),
                        M("Projects", c="project", f="project")(
                            #M("Create", m="create"),
                        ),
                        M("Departments", c="hrm", f="department")(
                            #M("Create", m="create"),
                        ),
                        M("Job Titles", c="hrm", f="job_title")(
                            #M("Create", m="create"),
                            #M("Import", m="import", p="create", check=is_org_admin),
                        ),
                       )
        else:
            settings = current.deployment_settings
            is_org_admin = lambda i: has_role(ADMIN)
            is_super_editor = lambda i: has_role("staff_super") or \
                                        has_role("vol_super")
            use_certs = lambda i: settings.get_hrm_use_certificates()
        
            return M()(
                        M("Staff", c="hrm", f=("staff", "person"), m="summary")(
                            M("Create", m="create"),
                            M("Import", f="person", m="import",
                              vars={"group": "staff"}, p="create"),
                        ),
                        M("Staff & Volunteers (Combined)",
                          c="hrm", f="human_resource", m="summary",
                          check=is_super_editor),
                        M("Teams", c="hrm", f="group")(
                            M("Create", m="create"),
                            M("Search Members", f="group_membership"),
                            M("Import", f="group_membership", m="import"),
                        ),
                        M("National Societies", c="org",
                                                f="organisation",
                                                vars=red_cross_filter)(
                            M("Create", m="create",
                              vars=red_cross_filter
                              ),
                            M("Import", m="import", p="create", check=is_org_admin)
                        ),
                        M("Offices", c="org", f="office")(
                            M("Create", m="create"),
                            M("Import", m="import", p="create"),
                        ),
                        M("Department Catalog", c="hrm", f="department")(
                            M("Create", m="create"),
                        ),
                        M("Job Title Catalog", c="hrm", f="job_title")(
                            M("Create", m="create"),
                            M("Import", m="import", p="create", check=is_org_admin),
                        ),
                        #M("Skill Catalog", f="skill")(
                        #    M("Create", m="create"),
                        #    #M("Skill Provisions", f="skill_provision"),
                        #),
                        M("Training Events", c="hrm", f="training_event")(
                            M("Create", m="create"),
                            M("Search Training Participants", f="training"),
                            M("Import Participant List", f="training", m="import"),
                        ),
                        M("Reports", c="hrm", f="staff", m="report")(
                            M("Staff Report", m="report"),
                            M("Expiring Staff Contracts Report",
                              vars={"expiring": "1"}),
                            M("Training Report", f="training", m="report"),
                        ),
                        M("Training Course Catalog", c="hrm", f="course")(
                            M("Create", m="create"),
                            M("Import", m="import", p="create", check=is_org_admin),
                            M("Course Certificates", f="course_certificate"),
                        ),
                        M("Certificate Catalog", c="hrm", f="certificate",
                          check=use_certs)(
                            M("Create", m="create"),
                            M("Import", m="import", p="create", check=is_org_admin),
                            #M("Skill Equivalence", f="certificate_skill"),
                        ),
                        M("Organization Types", c="org", f="organisation_type",
                          restrict=[ADMIN])(
                            M("Create", m="create"),
                        ),
                        M("Office Types", c="org", f="office_type",
                          restrict=[ADMIN])(
                            M("Create", m="create"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def inv():
        """ INV / Inventory """

        auth = current.auth
        has_role = auth.s3_has_role
        system_roles = current.session.s3.system_roles
        ADMIN = system_roles.ADMIN
        ORG_ADMIN = system_roles.ORG_ADMIN

        s3db = current.s3db
        s3db.inv_recv_crud_strings()
        inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        settings = current.deployment_settings
        root_org = auth.root_org_name()
        def no_direct_stock_edits(i):
            if root_org in ("Australian Red Cross", CRMADA):
                # Australian & Malagasy RC use proper Logistics workflow
                return True
            else:
                # Others use simplified version
                return False
        #def use_facilities(i):
        #    if root_org == HNRC:
        #        # Honduran RC don't use Facilities
        #        return False
        #    else:
        #        return True
        #def basic_warehouse(i):
        #    if root_org == HNRC  and \
        #       not (has_role("hn_national_wh_manager") or \
        #            has_role(ORG_ADMIN)):
        #        # Hide menu entries which user shouldn't need access to
        #        return False
        #    else:
        #        return True
        #def multi_warehouse(i):
        #    if root_org == HNRC  and \
        #       not (has_role("hn_national_wh_manager") or \
        #            has_role(ORG_ADMIN)):
        #        # Only responsible for 1 warehouse so hide menu entries which should be accessed via Tabs on their warehouse
        #        # & other things that HNRC
        #        return False
        #    else:
        #        return True
        #def use_kits(i):
        #    if root_org == HNRC:
        #        # Honduran RC use Kits
        #        return True
        #    else:
        #        return False
        def use_types(i):
            if root_org == NRCS:
                # Nepal RC use Warehouse Types
                return True
            else:
                return False
        use_commit = lambda i: settings.get_req_use_commit()

        return M()(
                    #M("Home", f="index"),
                    #M("Warehouses", c="inv", f="warehouse", m="summary", check=multi_warehouse)(
                    M("Warehouses", c="inv", f="warehouse", m="summary")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Warehouse Stock", c="inv", f="inv_item", args="summary")(
                        M("Search Shipped Items", f="track_item"),
                        M("Adjust Stock Levels", f="adj", check=no_direct_stock_edits),
                        #M("Kitting", f="kitting", check=use_kits),
                        M("Import", f="inv_item", m="import", p="create"),
                    ),
                    M("Reports", c="inv", f="inv_item")(
                        M("Warehouse Stock", f="inv_item",m="report"),
                        M("Expiration Report", c="inv", f="track_item",
                          vars={"report": "exp"}),
                        # CRMADA want this - requires support in config.py atm (move that to core)
                        #M("Stock Movements", f="inv_item", m="grouped",
                        #  vars={"report": "movements"},
                        #  check=no_direct_stock_edits,
                        #  ),
                        #M("Monetization Report", c="inv", f="inv_item",
                        #  vars={"report": "mon"}),
                        #M("Utilization Report", c="inv", f="track_item",
                        #  vars={"report": "util"}),
                        #M("Summary of Incoming Supplies", c="inv", f="track_item",
                        #  vars={"report": "inc"}),
                        # M("Summary of Releases", c="inv", f="track_item",
                        #  vars={"report": "rel"}),
                    ),
                    #M(inv_recv_list, c="inv", f="recv", check=multi_warehouse)(
                    M(inv_recv_list, c="inv", f="recv")(
                        M("Create", m="create"),
                    ),
                    #M("Sent Shipments", c="inv", f="send", check=multi_warehouse)(
                    M("Sent Shipments", c="inv", f="send")(
                        M("Create", m="create"),
                        M("Search Shipped Items", f="track_item"),
                    ),
                    #M("Items", c="supply", f="item", m="summary", check=basic_warehouse)(
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
                    #M("Catalogs", c="supply", f="catalog", check=basic_warehouse)(
                    M("Catalogs", c="supply", f="catalog")(
                        M("Create", m="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    #M("Suppliers", c="inv", f="supplier", check=basic_warehouse)(
                    M("Suppliers", c="inv", f="supplier")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    #M("Facilities", c="inv", f="facility", check=basic_warehouse)(
                    M("Facilities", c="inv", f="facility")(
                        M("Create", m="create", t="org_facility"),
                    ),
                    M("Facility Types", c="inv", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Warehouse Types", c="inv", f="warehouse_type", check=use_types,
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Requests", c="req", f="req")(
                        M("Create", m="create"),
                        M("Requested Items", f="req_item"),
                    ),
                    M("Commitments", c="req", f="commit", check=use_commit)(
                    ),
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ Organisation Management """

        if current.request.function in ("capacity_assessment", "capacity_assessment_data"):
            # Use Survey
            return self.survey()
        else:
            # Use HRM
            return self.hrm()

    # -------------------------------------------------------------------------
    @staticmethod
    def po():
        """ PO / Population Outreach """

        due_followups = current.s3db.po_due_followups()
        DUE_FOLLOWUPS = current.T("Due Follow-ups")
        if due_followups:
            follow_up_label = "%s (%s)" % (DUE_FOLLOWUPS, due_followups)
        else:
            follow_up_label = DUE_FOLLOWUPS

        return M(c="po")(
                    M("Overview", f="index"),
                    M("Households", f="household", m="summary")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M(follow_up_label, f="due_followups",
                      translate=False,
                      ),
                    M("Areas", f="area")(
                        M("Create", m="create"),
                    ),
                    M("Referral Agencies", f="organisation")(
                        M("Create", m="create"),
                    ),
                    M("Emotional Needs", f="emotional_need")(
                        M("Create", m="create"),
                    ),
                    M("Practical Needs", f="practical_need")(
                        M("Create", m="create"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Tracking & Management """

        #root_org = current.auth.root_org_name()
        #def community_volunteers(i):
        #    if root_org == HNRC:
        #        return True
        #    else:
        #        return False

        #system_roles = current.session.s3.system_roles
        #ORG_ADMIN = system_roles.ORG_ADMIN

        menu = M(c="project")(
             M("Programs", f="programme")(
                M("Create", m="create"),
             ),
             M("Projects", f="project", m="summary")(
                M("Create", m="create"),
             ),
             M("Communities", f="location")(
                # Better created from tab (otherwise Activity Type filter won't work)
                #M("Create", m="create"),
                M("Map", m="map"),
                M("Community Contacts", f="location_contact"),
                #M("Community Volunteers", f="volunteer",
                #  check=community_volunteers),
             ),
            M("Reports", f="location", m="report")(
                M("3W", f="location", m="report"),
                M("Beneficiaries", f="beneficiary", m="report"),
                #M("Indicators", f="indicator", m="report",
                #  check=indicators,
                #  ),
                #M("Indicators over Time", f="indicator", m="timeplot",
                #  check=indicators,
                #  ),
                M("Funding", f="organisation", m="report"),
             ),
             M("Import", f="project", m="import", p="create"#, restrict=[ORG_ADMIN]
               )(
                M("Import Projects", m="import", p="create"),
                M("Import Project Organizations", f="organisation",
                  m="import", p="create"),
                M("Import Project Communities", f="location",
                  m="import", p="create"),
             ),
             M("Partner Organizations",  f="partners")(
                M("Create", m="create"),
                M("Import", m="import", p="create"),
             ),
             M("Activity Types", f="activity_type")(
                M("Create", m="create"),
             ),
             M("Beneficiary Types", f="beneficiary_type")(
                M("Create", m="create"),
             ),
             M("Demographics", f="demographic")(
                M("Create", m="create"),
             ),
             M("Hazards", f="hazard")(
                M("Create", m="create"),
             ),
             #M("Indicators", f="indicator",
             #  check=indicators)(
             #   M("Create", m="create"),
             #),
             M("Sectors", f="sector")(
                M("Create", m="create"),
             ),
             M("Themes", f="theme")(
                M("Create", m="create"),
             ),
            )

        return menu

    # -------------------------------------------------------------------------
    def req(self):
        """ Requests Management """

        # Same as Inventory
        return self.inv()

    # -------------------------------------------------------------------------
    @staticmethod
    def survey():
        """ SURVEY / Survey """

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
                    M("Branch Organization Capacity Assessments", c="org", f="capacity_assessment")(
                        M("Create", m="create"),
                        M("Report", f="capacity_assessment_data", m="custom_report"),
                    ),
                    M("Assessment Templates", f="template")(
                        M("Create", m="create"),
                    ),
                    #M("Section", f="section")(
                    #    M("Create", args="create"),
                    #),
                    M("Disaster Assessments", f="series")(
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
    @staticmethod
    def vol():
        """ Volunteer Management """

        auth = current.auth
        has_role = auth.s3_has_role
        ADMIN = current.session.s3.system_roles.ADMIN
        root_org = auth.root_org_name()

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        is_org_admin = lambda i: has_role(ADMIN)
        is_super_editor = lambda i: has_role("vol_super") or \
                                    has_role("staff_super")

        settings = current.deployment_settings
        use_certs = lambda i: settings.get_hrm_use_certificates()
        use_skills = lambda i: settings.get_hrm_use_skills()
        show_programmes = lambda i: settings.get_hrm_vol_experience() in ("programme", "both")
        show_program_reports = lambda i: root_org != IRCS and \
                                         settings.get_hrm_vol_experience() in ("programme", "both")
        show_tasks = lambda i: settings.has_module("project") and \
                               settings.get_project_mode_task()
        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams
        vol_roles = lambda i: settings.get_hrm_vol_roles() and root_org != "Viet Nam Red Cross"

        check_org_dependent_field = lambda tablename, fieldname: \
            settings.set_org_dependent_field(tablename, fieldname,
                                             enable_field = False)

        if root_org == IRCS:
            awards_label = "Recommendation Letter Types"
        else:
            awards_label = "Awards"

        use_activities = lambda i: True if root_org == CRMADA else False

        return M(c="vol")(
                    M("Volunteers", f="volunteer", m="summary")(
                        M("Create", m="create"),
                        M("Import", f="person", m="import",
                          vars={"group":"volunteer"}, p="create"),
                    ),
                    M("Staff & Volunteers (Combined)",
                      c="vol", f="human_resource", m="summary",
                      check=is_super_editor),
                    M(teams, f="group",
                      check=use_teams)(
                        M("Create", m="create"),
                        M("Search Members", f="group_membership"),
                        M("Import", f="group_membership", m="import"),
                    ),
                    #M("Department Catalog", f="department")(
                    #    M("Create", m="create"),
                    #),
                    M("Volunteer Role Catalog", f="job_title",
                      check=vol_roles)(
                        M("Create", m="create"),
                        M("Import", m="import", p="create", check=is_org_admin),
                    ),
                    M("Skill Catalog", f="skill",
                      check=use_skills)(
                        M("Create", m="create"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    M("Activities", f="activity",
                      check=use_activities)(
                        M("Create", m="create"),
                        M("Import Hours", f="activity_hours", m="import"),
                    ),
                    M("Activity Types", f="activity_type",
                      check=[use_activities, is_super_editor])(
                        M("Create", m="create"),
                        #M("Import", m="import"),
                    ),
                    M("Training Events", f="training_event")(
                        M("Create", m="create"),
                        M("Facilities", f="facility"),
                        M("Search Training Participants", f="training"),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Training Course Catalog", f="course")(
                        M("Create", m="create"),
                        #M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", f="certificate",
                      check=use_certs)(
                        M("Create", m="create"),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("Programs", f="programme",
                      check=show_programmes)(
                        M("Create", m="create"),
                        M("Import Hours", f="programme_hours", m="import"),
                    ),
                    M(awards_label, f="award",
                      check=is_org_admin)(
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
                    M("Reports", f="volunteer", m="report")(
                        M("Volunteer Report", m="report"),
                        M("Hours by Activity Type", f="activity_hours", m="report",
                          check=use_activities),
                        M("Hours by Role Report", f="programme_hours", m="report",
                          vars=Storage(rows="job_title_id",
                                       cols="month",
                                       fact="sum(hours)"),
                          check=show_program_reports),
                        M("Hours by Program Report", f="programme_hours", m="report",
                          vars=Storage(rows="programme_id",
                                       cols="month",
                                       fact="sum(hours)"),
                          check=show_program_reports),
                        M("Training Report", f="training", m="report"),
                    ),
                    #M("My Tasks", f="task",
                    #  check=[personal_mode, show_tasks],
                    #  vars={"access": "personal",
                    #        "mine": 1}),
                )

# END =========================================================================
