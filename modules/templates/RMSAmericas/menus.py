# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

RC = {"organisation_type.name" : "Red Cross / Red Crescent"}

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

        auth = current.auth
        has_role = auth.s3_has_role
        has_roles = auth.s3_has_roles
        s3 = current.session.s3

        len_roles = len(s3.roles)
        if (len_roles <= 2) or \
           (len_roles == 3 and has_role("RIT_MEMBER") and not has_role("ADMIN")):
            # No specific Roles
            # Just show Profile on main menu
            return [MM("Profile", c="hrm", f="person",
                       args=[str(auth.s3_logged_in_person())],
                       vars={"profile":1},
                       ),
                    ]

        #root_org = auth.root_org_name()
        system_roles = s3.system_roles
        #ADMIN = system_roles.ADMIN
        ORG_ADMIN = system_roles.ORG_ADMIN

        s3db = current.s3db
        s3db.inv_recv_crud_strings()
        inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        #def gis(item):
        #    root_org = auth.root_org_name()
        #    return root_org == "Honduran Red Cross"

        def hrm(item):
            return has_roles((ORG_ADMIN,
                              "hr_manager",
                              "hr_assistant",
                              "training_coordinator",
                              "training_assistant",
                              "surge_capacity_manager",
                              "disaster_manager",
                              ))

        def training(item):
            return has_roles((ORG_ADMIN,
                              "training_coordinator",
                              "training_assistant",
                              "ns_training_manager",
                              "ns_training_assistant",
                              "surge_capacity_manager",
                              "disaster_manager",
                              ))

        def inv(item):
            return has_roles((ORG_ADMIN,
                              "wh_manager",
                              "national_wh_manager",
                              ))

        def multi_warehouse(i):
            return has_roles((ORG_ADMIN,
                              "national_wh_manager",
                              ))

        def projects(item):
            return has_roles(("project_reader",
                              "project_manager",
                              "monitoring_evaluation",
                              ))

        menu= [homepage("gis")(),
               homepage("hrm", "org", name="Human Talent", check=hrm)(
                   MM("Human Talent", c="hrm", f="human_resource", m="summary"),
                   #MM("Teams", c="hrm", f="group"),
                   MM("National Societies", c="org", f="organisation",
                      vars = RC),
                   #MM("Offices", c="org", f="office"),
                   MM("Positions", c="hrm", f="job_title"),
                   MM("Programs", c="hrm", f="programme"),
               ),
               homepage("hrm", f="training_event", name="Training", check=training)(
                   MM("Training Centers", c="hrm", f="training_center"),
                   MM("Training Course Catalog", c="hrm", f="course"),
                   MM("Training Events", c="hrm", f="training_event"),
                   MM("External Trainees", c="hrm", f="trainee"),
               ),
               homepage("member", f="membership", name="Partners")(
               ),
               homepage("inv", "supply", "req", check=inv)(
                   MM("Warehouses", c="inv", f="warehouse", m="summary", check=multi_warehouse),
                   MM(inv_recv_list, c="inv", f="recv"),
                   MM("Sent Shipments", c="inv", f="send"),
                   MM("Items", c="supply", f="item", check=multi_warehouse),
                   #MM("Catalogs", c="supply", f="catalog", check=multi_warehouse),
                   #MM("Item Categories", c="supply", f="item_category"),
                   M("Suppliers", c="inv", f="supplier", check=multi_warehouse)(),
                   #M("Facilities", c="inv", f="facility", check=multi_warehouse)(),
                   M("Requests", c="req", f="req")(),
                   #M("Commitments", f="commit")(),
               ),
               #homepage("asset")(
               #    MM("Assets", c="asset", f="asset", m="summary"),
               #    MM("Items", c="asset", f="item", m="summary"),
               #),
               homepage("project", f="project", m="summary", check=projects)(
                   MM("Projects", c="project", f="project", m="summary"),
                   #MM("Locations", c="project", f="location"),
                   #MM("Outreach", c="po", f="index", check=outreach),
               ),
               ]

        # For some reason the deploy menu is displaying even if users have NONE access to deploy!
        # @ToDo: We will need to allow RIT members some basic access to the module
        if has_roles(("surge_capacity_manager",
                      "disaster_manager",
                      )):
            menu.append(
                homepage("deploy", name="RIT", f="mission", m="summary",
                         vars={"~.status__belongs": "2"})(
                    MM("Missions", c="deploy", f="mission", m="summary"),
                    MM("Members", c="deploy", f="human_resource", m="summary"),
                ))

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Custom Organisation Menu """

        OM = S3OrgMenuLayout
        return OM()

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls):

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
            has_role = auth.s3_has_role
            if has_role("ADMIN"):
                admin = MP("Administration", c="admin", f="index")
            elif has_role("ORG_ADMIN"):
                admin = MP("Administration", c="admin", f="user")
            elif auth.s3_has_roles(("hr_manager",
                                    "ns_training_manager",
                                    "training_coordinator",
                                    )):
                admin = MP("Administration", c="pr", f="forum")
            else:
                admin = None

            menu_personal = MP()(admin,
                                 MP("Profile", c="hrm", f="person",
                                    args=[str(auth.s3_logged_in_person())],
                                    vars={"profile":1},
                                    ),
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

        if current.auth.s3_has_role("ADMIN"):
            # Standard Admin Menu
            menu = super(S3OptionsMenu, self).admin()

            # Additional Items
            menu(M("Forums", c="pr", f="forum"),
                 M("Map Settings", c="gis", f="config"),
                 M("Content Management", c="cms", f="index"),
                 )

            return menu

        else:
            # OrgAdmin
            return self.pr()


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
    def pr(self):
        """ Person Registry """

        auth = current.auth
        has_role = auth.s3_has_role
        if has_role("ADMIN"):
            if current.request.function == "forum":
                return self.admin()
            return M(c="pr")(
                        M("Persons", f="person")(
                            M("Create", m="create"),
                        ),
                        #M("Groups", f="group")(
                        #    M("Create", m="create"),
                        #),
                        #M("Forums", f="forum")(
                        #    M("Create", m="create"),
                        #),
                        )

        elif has_role("ORG_ADMIN"):
            return M()(M("Users", c="admin", f="user")(
                        ),
                        M("Forums", c="pr", f="forum")(
                            M("Create", m="create"),
                        ),
                       )

        else:
            # Managers (HR or Training Center Coordinators)
            return M()(M("Forums", c="pr", f="forum")(
                        M("Create", m="create"),
                        ),
                       )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM Human Talent """

        request = current.request
        if "profile" in request.get_vars:
            # No Side Menu
            return

        auth = current.auth
        has_role = auth.s3_has_role
        s3 = current.session.s3

        len_roles = len(s3.roles)
        if (len_roles <= 2) or \
           (len_roles == 3 and has_role("RIT_MEMBER") and not has_role("ADMIN")):
            # No Side Menu
            return

        #ADMIN = s3.system_roles.ADMIN
        ORG_ADMIN = s3.system_roles.ORG_ADMIN

        if request.function in ("certificate", "course", "course_certificate",
                                "facility", "training", "training_center",
                                "training_event", "trainee", "trainee_person"):
            return M()( M("Training Centers", c="hrm", f="training_center")(
                        ),
                        M("Training Course Catalog", c="hrm", f="course")(
                            M("Create", m="create"),
                            M("Import", m="import", p="create",
                              restrict=(ORG_ADMIN,
                                        "ns_training_manager",
                                        "training_coordinator",
                                        )),
                            #M("Certificates", f="certificate"),
                            # Just access this via Tabs of Courses & Certificates
                            #M("Course Certificates", f="course_certificate"),
                        ),
                        M("Training Events", c="hrm", f="training_event")(
                            M("Create", m="create"),
                            M("Search Training Participants", f="training"),
                            M("Import Participant List", f="training", m="import",
                              restrict=(ORG_ADMIN,
                                        "ns_training_manager",
                                        "training_coordinator",
                                        "training_assistant",
                                        )),
                        ),
                        M("External Trainees", c="hrm", f="trainee")(
                            M("Create", m="create"),
                        ),
                        M("Report", c="hrm", f="training", m="report")(
                        ),
                    )
        else:
            return M()(
                        M("Human Talent", c="hrm", f="human_resource", m="summary")(
                            M("Create", m="create"),
                            M("Import", f="person", m="import",
                              restrict=(ORG_ADMIN,
                                        "hr_manager",
                                        )),
                        ),
                        M("Report", c="hrm", f="human_resource", m="report")(
                            #M("Staff Report", m="report"),
                            #M("Expiring Staff Contracts Report",
                            #  vars=dict(expiring="1")),
                            #M("Hours by Role Report", f="programme_hours", m="report",
                            #  vars=Storage(rows="job_title_id",
                            #               cols="month",
                            #               fact="sum(hours)"),
                            #  ),
                            M("Hours by Program Report", f="programme_hours", m="report",
                              vars=Storage(rows="programme_id",
                                           cols="month",
                                           fact="sum(hours)"),
                              ),
                        ),
                        #M("Teams", c="hrm", f="group")(
                        #    M("Create", m="create"),
                        #    M("Search Members", f="group_membership"),
                        #    M("Import", f="group_membership", m="import"),
                        #),
                        M("National Societies", c="org", f="organisation",
                          vars=RC)(
                            M("Create", m="create",
                              vars=RC
                              ),
                            M("Import", m="import", p="create",
                              restrict=[ORG_ADMIN])
                        ),
                        #M("Offices", c="org", f="office")(
                        #    M("Create", m="create"),
                        #    M("Import", m="import", p="create"),
                        #),
                        #M("Department Catalog", c="hrm", f="department")(
                        #    M("Create", m="create"),
                        #),
                        M("Position Catalog", c="hrm", f="job_title")(
                            M("Create", m="create"),
                            M("Import", m="import", p="create",
                              restrict=(ORG_ADMIN,
                                        "hr_manager",
                                        )),
                        ),
                        M("Programs", c="hrm", f="programme")(
                            M("Create", m="create"),
                            M("Import Hours", f="programme_hours", m="import"),
                        ),
                        #M("Organization Types", c="org", f="organisation_type",
                        #  restrict=[ADMIN])(
                        #    M("Create", m="create"),
                        #),
                        #M("Office Types", c="org", f="office_type",
                        #  restrict=[ADMIN])(
                        #    M("Create", m="create"),
                        #),
                        #M("Facility Types", c="org", f="facility_type",
                        #  restrict=[ADMIN])(
                        #    M("Create", m="create"),
                        #),
                        #M("Personal Profile", c="hrm", f="person",
                        #  vars=dict(access="personal"))
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def member():
        """ Membership Management """

        return M(c="member")(
                    M("Partners", f="membership", m="summary")(
                        M("Create", m="create"),
                        #M("Report", m="report"),
                        M("Import", f="person", m="import"),
                    ),
                    M("Partner Types", f="membership_type")(
                        M("Create", m="create"),
                        #M("Import", m="import"),
                    ),
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ Organisation Management """

        # Same as HRM
        return self.hrm()

    # -------------------------------------------------------------------------
    @staticmethod
    def inv():
        """ INV / Inventory """

        #auth = current.auth
        has_role = current.auth.s3_has_role
        system_roles = current.session.s3.system_roles
        ADMIN = system_roles.ADMIN
        ORG_ADMIN = system_roles.ORG_ADMIN

        s3db = current.s3db
        s3db.inv_recv_crud_strings()
        inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        settings = current.deployment_settings
        #use_adjust = lambda i: not settings.get_inv_direct_stock_edits()
        #root_org = auth.root_org_name()
        #def use_adjust(i):
        #    if root_org in ("Australian Red Cross", "Honduran Red Cross"):
        #        # Australian & Honduran RC use proper Logistics workflow
        #        return True
        #    else:
        #        # Others use simplified version
        #        return False
        #def use_facilities(i):
        #    if root_org == "Honduran Red Cross":
        #        # Honduran RC don't use Facilities
        #        return False
        #    else:
        #        return True
        def multi_warehouse(i):
            if not (has_role("national_wh_manager") or \
                    has_role(ORG_ADMIN)):
                # Only responsible for 1 warehouse so hide menu entries which should be accessed via Tabs on their warehouse
                # & other things that HNRC
                return False
            else:
                return True
        def basic_warehouse(i):
            if (has_role("national_wh_manager") or \
                has_role(ORG_ADMIN)):
                return False
            else:
                return True
        #def use_kits(i):
        #    if root_org == "Honduran Red Cross":
        #        # Honduran RC use Kits
        #        return True
        #    else:
        #        return False
        #def use_types(i):
        #    if root_org == "Nepal Red Cross Society":
        #        # Nepal RC use Warehouse Types
        #        return True
        #    else:
        #        return False
        use_commit = lambda i: settings.get_req_use_commit()

        return M()(
                    M("My Warehouse", c="inv", f="index", check=basic_warehouse)(), # Will redirect in customise_inv_home
                    M("Warehouses", c="inv", f="warehouse", m="summary", check=multi_warehouse)(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Warehouse Stock", c="inv", f="inv_item", args="summary")(
                        M("Search Shipped Items", f="track_item"),
                        M("Adjust Stock Levels", f="adj"#, check=use_adjust
                          ),
                        M("Kitting", f="kitting"#, check=use_kits
                          ),
                        M("Import", f="inv_item", m="import", p="create"),
                    ),
                    M("Reports", c="inv", f="inv_item")(
                        M("Warehouse Stock", f="inv_item", m="report"),
                        M("Stock Position", f="inv_item", m="grouped",
                          vars={"report": "default"},
                          ),
                        M("Weight and Volume", f="inv_item", m="grouped",
                          vars={"report": "weight_and_volume"},
                          ),
                        M("Stock Movements", f="inv_item", m="grouped",
                          vars={"report": "movements"},
                          ),
                        M("Expiration Report", c="inv", f="track_item",
                          vars=dict(report="exp")),
                        #M("Monetization Report", c="inv", f="inv_item",
                        #  vars=dict(report="mon")),
                        #M("Utilization Report", c="inv", f="track_item",
                        #  vars=dict(report="util")),
                        #M("Summary of Incoming Supplies", c="inv", f="track_item",
                        #  vars=dict(report="inc")),
                        # M("Summary of Releases", c="inv", f="track_item",
                        #  vars=dict(report="rel")),
                    ),
                    M(inv_recv_list, c="inv", f="recv", check=multi_warehouse)(
                        M("Create", m="create"),
                    ),
                    M("Sent Shipments", c="inv", f="send", check=multi_warehouse)(
                        M("Create", m="create"),
                        M("Search Shipped Items", f="track_item"),
                    ),
                    M("Items", c="supply", f="item", m="summary", check=multi_warehouse)(
                        M("Create", m="create"),
                        M("Import", f="catalog_item", m="import", p="create", restrict=[ORG_ADMIN]),
                    ),
                    # Catalog Items moved to be next to the Item Categories
                    #M("Catalog Items", c="supply", f="catalog_item")(
                    #   M("Create", m="create"),
                    #),
                    #M("Brands", c="supply", f="brand",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    M("Catalogs", c="supply", f="catalog", check=multi_warehouse)(
                        M("Create", m="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ORG_ADMIN])(
                        M("Create", m="create"),
                    ),
                    M("Suppliers", c="inv", f="supplier")(
                        M("Create", m="create"),
                        M("Import", m="import", p="create", restrict=[ORG_ADMIN]),
                    ),
                    M("Facilities", c="inv", f="facility")(
                        M("Create", m="create", t="org_facility"),
                    ),
                    M("Facility Types", c="inv", f="facility_type",
                      restrict=[ADMIN])(
                        M("Create", m="create"),
                    ),
                    #M("Warehouse Types", c="inv", f="warehouse_type", check=use_types,
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    M("Requests", c="req", f="req")(
                        M("Create", m="create"),
                        M("Requested Items", f="req_item"),
                    ),
                    M("Commitments", c="req", f="commit", check=use_commit)(
                    ),
                )

    # -------------------------------------------------------------------------
    def req(self):
        """ Requests Management """

        # Same as Inventory
        return self.inv()

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Tracking & Management """

        #root_org = current.auth.root_org_name()
        #def community_volunteers(i):
        #    if root_org == "Honduran Red Cross":
        #        return True
        #    else:
        #        return False

        system_roles = current.session.s3.system_roles
        ORG_ADMIN = system_roles.ORG_ADMIN

        menu = M(c="project")(
             M("Programs", f="programme")(
                M("Create", m="create"),
             ),
             M("Projects", f="project", m="summary")(
                M("Create", m="create"),
             ),
             M("Locations", f="location")(
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
                M("Global Report of Projects Status", f="project", m="grouped"),
             ),
             M("Import", f="project", m="import", p="create", restrict=[ORG_ADMIN])(
                M("Import Projects", m="import", p="create"),
                M("Import Project Organizations", f="organisation",
                  m="import", p="create"),
                M("Import Project Communities", f="location",
                  m="import", p="create"),
             ),
             M("National Societies",  c="org", f="organisation",
                                      vars=RC)(
                #M("Create", m="create", restrict=[ADMIN]),
                #M("Import", m="import", p="create", restrict=[ADMIN]),
             ),
             M("Partner Organizations",  f="partners")(
                M("Create", m="create", restrict=[ORG_ADMIN]),
                M("Import", m="import", p="create", restrict=[ORG_ADMIN]),
             ),
             #M("Activity Types", f="activity_type")(
             #   M("Create", m="create"),
             #),
             M("Beneficiary Types", f="beneficiary_type")(
                M("Create", m="create"),
             ),
             #M("Demographics", f="demographic")(
             #   M("Create", m="create"),
             #),
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
             M("Period of Time", f="window")()
            )

        return menu

    # -------------------------------------------------------------------------
    @staticmethod
    def deploy():
        """ RIT Alerting and Deployments """

        return M()(M("Missions",
                     c="deploy", f="mission", m="summary")(
                        M("Create", m="create"),
                        M("Active Missions", m="summary",
                          vars={"~.status__belongs": "2"}),
                   ),
                   M("Alerts",
                     c="deploy", f="alert")(
                        M("Create", m="create"),
                        #M("InBox",
                        #  c="deploy", f="email_inbox",
                        #),
                        M("Twitter Settings",
                          #c="deploy", f="email_channel",
                          #p="update", t="msg_email_channel",
                          c="deploy", f="twitter_channel",
                          p="update", t="msg_twitter_channel",
                          ),
                   ),
                   M("Deployments",
                     c="deploy", f="assignment", m="summary"
                   ),
                   #M("Sectors",
                   #  c="deploy", f="job_title", restrict=["ADMIN"],
                   #),
                   M("Disaster Types",
                     c="event", f="event_type", restrict=["ADMIN"],
                   ),
                   M("RIT Members",
                     c="deploy", f="human_resource", m="summary")(
                        M("Add Member",
                          c="deploy", f="application", m="select",
                          p="create", t="deploy_application",
                          ),
                        M("Import Members", c="deploy", f="person", m="import"),
                   ),
                   M("Online Manual", c="deploy", f="index"),
               )

# END =========================================================================
