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

        T = current.T
        auth = current.auth

        has_role = auth.s3_has_role
        root_org = auth.root_org_name()
        system_roles = current.session.s3.system_roles
        ADMIN = system_roles.ADMIN
        ORG_ADMIN = system_roles.ORG_ADMIN

        s3db = current.s3db
        s3db.inv_recv_crud_strings()
        inv_recv_list = current.response.s3.crud_strings.inv_recv.title_list

        def hrm(item):
            return root_org != "Honduran Red Cross" or \
                   has_role(ORG_ADMIN)

        def inv(item):
            return has_role("hn_wh_manager") or \
                   has_role("hn_national_wh_manager") or \
                   has_role(ORG_ADMIN)

        def basic_warehouse(i):
            if not (has_role("hn_national_wh_manager") or \
                    has_role(ORG_ADMIN)):
                # Hide menu entries which user shouldn't need access to
                return False
            else:
                return True

        def multi_warehouse(i):
            if not (has_role("hn_national_wh_manager") or \
                    has_role(ORG_ADMIN)):
                # Only responsible for 1 warehouse so hide menu entries which should be accessed via Tabs on their warehouse
                return False
            else:
                return True

        return [
            homepage("gis")(
            ),
            homepage("hrm", "org", name=T("Human Talent"), check=hrm)(
                MM("Human Talent", c="hrm", f="human_resource", m="summary"),
                #MM("Teams", c="hrm", f="group"),
                MM("National Societies", c="org", f="organisation",
                   vars = red_cross_filter),
                #MM("Offices", c="org", f="office"),
                MM("Positions", c="hrm", f="job_title"),
                #MM("Training Events", c="hrm", f="training_event"),
                #MM("Training Courses", c="hrm", f="course"),
            ),
            homepage("hrm", name=T("Training"), check=hrm)(
                MM("Training Centers", c="org", f="facility"),
                MM("Training Course Catalog", c="hrm", f="course"),
                MM("Training Events", c="hrm", f="training_event"),
            ),
            homepage("inv", "supply", "req", check=inv)(
                MM("Warehouses", c="inv", f="warehouse", m="summary", check=multi_warehouse),
                MM(inv_recv_list, c="inv", f="recv", check=multi_warehouse),
                MM("Sent Shipments", c="inv", f="send", check=multi_warehouse),
                MM("Items", c="supply", f="item", check=basic_warehouse),
                MM("Catalogs", c="supply", f="catalog", check=basic_warehouse),
                #MM("Item Categories", c="supply", f="item_category"),
                M("Suppliers", c="inv", f="supplier", check=basic_warehouse)(),
                M("Facilities", c="inv", f="facility", check=basic_warehouse)(),
                M("Requests", c="req", f="req")(),
                #M("Commitments", f="commit")(),
            ),
            #homepage("asset")(
            #    MM("Assets", c="asset", f="asset", m="summary"),
            #    MM("Items", c="asset", f="item", m="summary"),
            #),
            homepage("project", f="project", m="summary")(
                MM("Projects", c="project", f="project", m="summary"),
                #MM("Locations", c="project", f="location"),
                #MM("Outreach", c="po", f="index", check=outreach),
            ),
            homepage("deploy", name="RIT", f="mission", m="summary",
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
    def pr(self):
        """ Person Registry """

        if current.request.function == "person": 
            # Training Center access to external Trainees (not Staff/Volunteers) 
            return self.hrm()
        else:
            return super(S3OptionsMenu, self).pr()

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM Human Talent """

        has_role = current.auth.s3_has_role
        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN
        settings = current.deployment_settings

        if "hrm" not in s3:
            current.s3db.hrm_vars()
        hrm_vars = s3.hrm

        manager_mode = lambda i: hrm_vars.mode is None
        personal_mode = lambda i: hrm_vars.mode is not None
        is_org_admin = lambda i: hrm_vars.orgs and True or \
                                 has_role(ADMIN)

        use_certs = lambda i: settings.get_hrm_use_certificates()

        request = current.request
        if request.function in ("certificate", "course", "course_certificate",
                                "facility", "training", "training_event") or \
           request.controller == "pr":
            return M()(
                        M("Report", c="hrm", f="training", m="report",
                          check=manager_mode)(),
                        M("Training Centers", c="org", f="facility",
                          check=manager_mode)(
                        ),
                        M("Training Course Catalog", c="hrm", f="course",
                          check=manager_mode)(
                            M("Create", m="create"),
                            M("Import", m="import", p="create", check=is_org_admin),
                            M("Certificates", f="certificate"),
                            # Just access this via Tabs of Courses & Certificates
                            #M("Course Certificates", f="course_certificate"),
                        ),
                        M("Training Events", c="hrm", f="training_event",
                          check=manager_mode)(
                            M("Create", m="create"),
                            M("Search Training Participants", f="training"),
                            M("Import Participant List", f="training", m="import"),
                        ),
                        #M("Certificate Catalog", c="hrm", f="certificate",
                        #  check=[manager_mode, use_certs])(
                        #    M("Create", m="create"),
                        #    M("Import", m="import", p="create", check=is_org_admin),
                        #    #M("Skill Equivalence", f="certificate_skill"),
                        #),
                    )
        else:
            return M()(
                        M("Human Talent", c="hrm", f="human_resource", m="summary",
                          check=manager_mode)(
                            M("Create", m="create"),
                            M("Import", f="person", m="import", p="create"),
                        ),
                        M("Report", c="hrm", f="human_resource", m="report",
                          check=manager_mode)(
                            #M("Staff Report", m="report"),
                            #M("Expiring Staff Contracts Report",
                            #  vars=dict(expiring="1")),
                        ),
                        #M("Teams", c="hrm", f="group",
                        #  check=manager_mode)(
                        #    M("Create", m="create"),
                        #    M("Search Members", f="group_membership"),
                        #    M("Import", f="group_membership", m="import"),
                        #),
                        M("National Societies", c="org",
                                                f="organisation",
                                                vars=red_cross_filter,
                          check=manager_mode)(
                            M("Create", m="create",
                              vars=red_cross_filter
                              ),
                            M("Import", m="import", p="create", check=is_org_admin)
                        ),
                        #M("Offices", c="org", f="office",
                        #  check=manager_mode)(
                        #    M("Create", m="create"),
                        #    M("Import", m="import", p="create"),
                        #),
                        #M("Department Catalog", c="hrm", f="department",
                        #  check=manager_mode)(
                        #    M("Create", m="create"),
                        #),
                        M("Position Catalog", c="hrm", f="job_title",
                          check=manager_mode)(
                            M("Create", m="create"),
                            M("Import", m="import", p="create", check=is_org_admin),
                        ),
                        #M("Organization Types", c="org", f="organisation_type",
                        #  restrict=[ADMIN],
                        #  check=manager_mode)(
                        #    M("Create", m="create"),
                        #),
                        #M("Office Types", c="org", f="office_type",
                        #  restrict=[ADMIN],
                        #  check=manager_mode)(
                        #    M("Create", m="create"),
                        #),
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
        #use_adjust = lambda i: not settings.get_inv_direct_stock_edits()
        root_org = auth.root_org_name()
        def use_adjust(i):
            if root_org in ("Australian Red Cross", "Honduran Red Cross"):
                # Australian & Honduran RC use proper Logistics workflow
                return True
            else:
                # Others use simplified version
                return False
        #def use_facilities(i):
        #    if root_org == "Honduran Red Cross":
        #        # Honduran RC don't use Facilities
        #        return False
        #    else:
        #        return True
        def basic_warehouse(i):
            if root_org == "Honduran Red Cross"  and \
               not (has_role("hn_national_wh_manager") or \
                    has_role(ORG_ADMIN)):
                # Hide menu entries which user shouldn't need access to
                return False
            else:
                return True
        def multi_warehouse(i):
            if root_org == "Honduran Red Cross"  and \
               not (has_role("hn_national_wh_manager") or \
                    has_role(ORG_ADMIN)):
                # Only responsible for 1 warehouse so hide menu entries which should be accessed via Tabs on their warehouse
                # & other things that HNRC
                return False
            else:
                return True
        def use_kits(i):
            if root_org == "Honduran Red Cross":
                # Honduran RC use Kits
                return True
            else:
                return False
        def use_types(i):
            if root_org == "Nepal Red Cross Society":
                # Nepal RC use Warehouse Types
                return True
            else:
                return False
        use_commit = lambda i: settings.get_req_use_commit()

        return M()(
                    #M("Home", f="index"),
                    M("Warehouses", c="inv", f="warehouse", m="summary", check=multi_warehouse)(
                        M("Create", m="create"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Warehouse Stock", c="inv", f="inv_item", args="summary")(
                        M("Search Shipped Items", f="track_item"),
                        M("Adjust Stock Levels", f="adj", check=use_adjust),
                        M("Kitting", f="kitting", check=use_kits),
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
                    M("Items", c="supply", f="item", m="summary", check=basic_warehouse)(
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
                    M("Catalogs", c="supply", f="catalog", check=basic_warehouse)(
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
             ),
             M("Import", f="project", m="import", p="create", restrict=[ORG_ADMIN])(
                M("Import Projects", m="import", p="create"),
                M("Import Project Organizations", f="organisation",
                  m="import", p="create"),
                M("Import Project Communities", f="location",
                  m="import", p="create"),
             ),
             M("National Societies",  c="org", f="organisation",
                                      vars=red_cross_filter)(
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
                        M("Settings",
                          #c="deploy", f="email_channel",
                          #p="update", t="msg_email_channel",
                          c="deploy", f="twitter_channel",
                          p="update", t="msg_twitter_channel",
                          ),
                   ),
                   M("Deployments",
                     c="deploy", f="assignment", m="summary"
                   ),
                   M("Sectors",
                     c="deploy", f="job_title", restrict=["ADMIN"],
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
