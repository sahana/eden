"""
    Custom Menus for RLPPTM

    License: MIT
"""

from gluon import current, URL, TAG, SPAN
from core import IS_ISO639_2_LANGUAGE_CODE
from core.ui.layouts import MM, M, ML, MP, MA
try:
    from ..RLP.layouts import OM
except ImportError:
    pass
import core.ui.menus as default

from .requests import get_managed_requester_orgs

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
        """ Modules Menu """

        auth = current.auth
        settings = current.deployment_settings

        has_role = auth.s3_has_role
        has_roles = auth.s3_has_roles

        is_org_group_admin = lambda i: has_role("ORG_GROUP_ADMIN", include_admin=False)
        managed_requester_orgs = get_managed_requester_orgs()

        supply_coordinator = lambda i: has_role("SUPPLY_COORDINATOR")
        supply_distributor = lambda i: has_role("SUPPLY_DISTRIBUTOR", include_admin=False)
        supply_requester = lambda i: bool(managed_requester_orgs)

        order_access = lambda i: supply_coordinator(i) or supply_requester(i)
        supply_access = lambda i: order_access(i) or supply_distributor(i)

        if settings.get_custom("daycare_testing_data"):
            daycare_testing = MM("Daycare Testing", f="daycare_testing", restrict="ORG_GROUP_ADMIN")
        else:
            daycare_testing = None

        # ORG menu to match CMS for newsletter functions only
        request = current.request
        is_newsletter = request.controller == "cms" and \
                        request.function in ("newsletter", "read_newsletter")
        org_c = ("org", "hrm", "cms") if is_newsletter else ("org", "hrm")

        menu = [MM("Tests##disease", c="disease", link=False)(
                    MM("Test Results", f="case_diagnostics", restrict="TEST_PROVIDER"),
                    MM("Daily Reports", f="testing_report"),
                    daycare_testing,
                    ),
                MM("Equipment", c=("req", "inv", "supply"), link=False, check=supply_access)(
                    MM("Orders##delivery", f="req", vars={"type": 1}, check=order_access),
                    MM("Shipment##process", c="inv", f="send", restrict="SUPPLY_COORDINATOR"),
                    MM("Shipments", c="inv", f="send", check=supply_distributor),
                    MM("Deliveries", c="inv", f="recv", check=supply_requester),
                    MM("Items", c="supply", f="item", restrict="SUPPLY_COORDINATOR"),
                    ),
                MM("Organizations", c=org_c, link=False, restrict=("ORG_GROUP_ADMIN", "ORG_ADMIN"))(
                    MM("Organizations", c="org", f="organisation", vars = {"mine": 1} if not has_role("ORG_GROUP_ADMIN") else None),
                    MM("Staff", c="hrm", f="staff"),
                    MM("Newsletters", c="cms", f="read_newsletter", selectable=is_newsletter),
                    ),
                MM("Projects",
                   c = "project", f="project",
                   restrict = "ADMIN",
                   ),
                MM("Find Test Station", link=False)(
                    MM("Test Stations for Everybody",
                       c = "org", f = "facility", m = "summary", vars={"$$code": "TESTS-PUBLIC"},
                       ),
                    #MM("Test Stations for School and Child Care Staff",
                    #   c = "org", f = "facility", m = "summary", vars={"$$code": "TESTS-SCHOOLS"},
                    #   ),
                    MM("Test Stations to review",
                       c = "org", f = "facility", vars={"$$review": "1"}, restrict="ORG_GROUP_ADMIN",
                       ),
                    MM("Unapproved Test Stations",
                       c = "org", f = "facility", vars={"$$pending": "1"}, restrict="ORG_GROUP_ADMIN",
                       ),
                    ),
                MM("Pending Approvals", c="default", f="index", args=["approve"],
                   check = is_org_group_admin,
                   ),
                MM("Register Test Station",
                   c = "default", f = "index", args = ["register"],
                   check = lambda i: settings.get_custom("test_station_registration") and \
                                     not current.auth.s3_logged_in(),
                   ),
                ]

        # Link to voucher management
        if auth.s3_logged_in():
            label, f = None, None
            if has_roles(("PROGRAM_MANAGER", "PROGRAM_ACCOUNTANT")):
                label, f = "Voucher Programs", "voucher_program"
            elif has_roles(("VOUCHER_PROVIDER", "PROVIDER_ACCOUNTANT")):
                label, f = "Voucher Acceptance", "voucher_debit"
            elif has_role("VOUCHER_ISSUER"):
                label, f = "Voucher Issuance", "voucher"
            if f:
                menu.insert(0, MM(label, c="fin", f=f))

        return menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Organisation Logo and Name """

        #OM = OrgMenuLayout
        return OM()

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls, **attr):
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
            login_next = URL(args=request.args, vars=request.get_vars)
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
            is_org_admin = lambda i: s3_has_role("ORG_ADMIN", include_admin=False)
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

        menu_about = MA(c="default")(
            MA("Help", f="help"),
            MA("Contact", f="contact"),
            MA("Privacy", f="index", args=["privacy"]),
            MA("Legal Notice", f="index", args=["legal"]),
            MA("Version", f="about", restrict = ("ORG_GROUP_ADMIN")),
        )
        return menu_about

# =============================================================================
class OptionsMenu(default.OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def admin():
        """ ADMIN menu """

        if not current.auth.s3_has_role("ADMIN"):
            # OrgAdmin: No Side-menu
            return None

        settings = current.deployment_settings
        consent_tracking = lambda i: settings.get_auth_consent_tracking()
        has_cms = lambda i: settings.has_module("cms")

        # NB: Do not specify a controller for the main menu to allow
        #     re-use of this menu by other controllers
        return M()(
                    M("Users and Roles", c="admin", link=False)(
                        M("Manage Users", f="user"),
                        M("Manage Roles", f="role"),
                    ),
                    M("Announcements", c="admin", f="announcement", check=has_cms),
                    M("Consent Tracking", c="admin", link=False, check=consent_tracking)(
                        M("Processing Types", f="processing_type"),
                        M("Consent Options", f="consent_option"),
                        M("Consent##plural", f="consent"),
                        ),
                    M("Content Management", c="cms", f="post", check=has_cms),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Event Log", c="admin", f="event"),
                    M("Error Tickets", c="admin", f="errors"),
                    M("Scheduler", c="admin", f="task"),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def audit(cls):

        return cls.org()

    # -------------------------------------------------------------------------
    @classmethod
    def cms(cls):

        if current.request.function in ("newsletter", "read_newsletter"):
            return cls.org()

        return M(c="cms")(
                    M("Series", f="series")(
                        M("Create", m="create"),
                        M("View as Pages", f="blog"),
                        ),
                    M("Posts", f="post")(
                        M("Create", m="create"),
                        M("View as Pages", f="page"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def disease():

        has_role = current.auth.s3_has_role
        daily_report = lambda i: has_role("ORG_ADMIN") and \
                                 has_role("TEST_PROVIDER", include_admin=False)

        settings = current.deployment_settings
        if settings.get_disease_testing_report_by_demographic():
            report_function = "testing_demographic"
        else:
            report_function = "testing_report"

        if settings.get_custom("daycare_testing_data"):
            daycare_testing = M("Daycare Testing", f="daycare_testing", restrict="ORG_GROUP_ADMIN")(
                                M("Statistics", m="report"),
                                )
        else:
            daycare_testing = None

        return M(c="disease")(
                    M("Test Results", f="case_diagnostics", restrict="TEST_PROVIDER")(
                        M("Registrieren", m="register"),
                        M("Statistics", m="report"),
                        ),
                    M("Daily Reports", f="testing_report")(
                        M("Create", m="create", check=daily_report),
                        M("Statistics", f=report_function, m="report"),
                        ),
                    daycare_testing,
                    M("Administration", restrict="ADMIN")(
                        M("Diseases", f="disease"),
                        M("Demographics", f="demographic"),
                        M("Testing Devices", f="testing_device"),
                        )
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def fin():
        """ FIN / Finance """

        auth = current.auth
        s3db = current.s3db

        voucher_create = lambda i: s3db.get_config("fin_voucher", "insertable", True)
        voucher_accept = lambda i: s3db.get_config("fin_voucher_debit", "insertable", True)

        is_program_accountant = lambda i: auth.s3_has_role("PROGRAM_ACCOUNTANT",
                                                           include_admin = False,
                                                           )

        return M(c="fin")(
                    M("Voucher Programs", f="voucher_program")(
                        M("Create", m="create", restrict=("PROGRAM_MANAGER")),
                        ),
                    M("Vouchers", f="voucher")(
                        M("Create Voucher", m="create", restrict=("VOUCHER_ISSUER"),
                          check = voucher_create,
                          ),
                        M("Create Group Voucher", m="create", restrict=("VOUCHER_ISSUER"),
                          vars = {"g": "1"},
                          check = voucher_create,
                          ),
                        M("Statistics", m="report", restrict=("PROGRAM_MANAGER")),
                        ),
                    M("Accepted Vouchers", f="voucher_debit")(
                        M("Accept Voucher", m="create", restrict=("VOUCHER_PROVIDER"),
                          check = voucher_accept,
                          ),
                        M("Accept Group Voucher", m="create", restrict=("VOUCHER_PROVIDER"),
                          vars = {"g": "1"},
                          check = voucher_accept,
                          ),
                        M("Statistics", m="report"),
                        ),
                    M("Billing", link=False)(
                       M("Compensation Claims", f="voucher_claim"),
                       M("Invoices", f="voucher_invoice"),
                       M("My Work List", f="voucher_invoice", vars={"mine": "1"},
                         check = is_program_accountant,
                         ),
                       ),
                    )

    # -------------------------------------------------------------------------
    @classmethod
    def hrm(cls):
        """ HRM / Human Resources Management """

        return cls.org()

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        org_menu = M("Organizations", f="organisation")

        auth = current.auth

        ORG_GROUP_ADMIN = auth.get_system_roles().ORG_GROUP_ADMIN
        has_role = auth.s3_has_role

        if has_role(ORG_GROUP_ADMIN):
            gtable = current.s3db.org_group
            query = (gtable.deleted == False)
            realms = auth.user.realms[ORG_GROUP_ADMIN] \
                     if not has_role("ADMIN") else None
            if realms is not None:
                query = (gtable.pe_id.belongs(realms)) & query
            groups = current.db(query).select(gtable.id,
                                              gtable.name,
                                              orderby = gtable.name,
                                              )
            for group in groups:
                org_menu(M(group.name, f="organisation",
                           vars = {"g": group.id}, translate = False,
                           ))

        org_menu(
            M("My Organizations", vars={"mine": 1}, restrict="ORG_ADMIN"),
            M("Create Organization", m="create", restrict="ORG_GROUP_ADMIN"),
            )

        # Newsletter menu
        author = auth.s3_has_permission("create", "cms_newsletter", c="cms", f="newsletter")
        T = current.T

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

        return M(c=("org", "hrm", "cms", "audit"))(
                    org_menu,
                    M("Audit", c="audit", link=False, restrict="AUDITOR")(
                        M("Overview", f="organisation"),
                        ),
                    M("Test Stations", f="facility", link=False, restrict="ORG_GROUP_ADMIN")(
                        M("Test Stations to review", vars = {"$$review": "1"}),
                        M("Unapproved##actionable", vars = {"$$pending": "1"}),
                        M("Defunct", vars = {"$$obsolete": "1"}),
                        M("All Test Stations", vars={"$$all": "1"}),
                        ),
                    M("Statistics", link=False, restrict="ORG_GROUP_ADMIN")(
                        M("Organizations", f="organisation", m="report"),
                        M("Facilities", f="facility", m="report"),
                        ),
                    M("Staff", c="hrm", f=("staff", "person"),
                      restrict=("ORG_ADMIN", "ORG_GROUP_ADMIN"),
                      ),
                    cms_menu,
                    #M("Newsletters", c="cms", f="read_newsletter")(
                        #M("Inbox", f="read_newsletter",
                          #check = lambda this: this.following()[0].check_permission(),
                          #),
                        #M("Compose and Send", f="newsletter", p="create"),
                        #),
                    M("Administration", restrict=("ADMIN"))(
                        M("Facility Types", f="facility_type"),
                        M("Organization Types", f="organisation_type"),
                        M("Services", f="service"),
                        M("Service Modes", f="service_mode"),
                        M("Booking Modes", f="booking_mode"),
                        M("Job Titles", c="hrm", f="job_title"),
                        ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Management """

        return M(c="project") (
                    M("Projects", f="project")(
                        M("Create", m="create")
                        )
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def req():
        """ REQ / Request Management """

        has_role = current.auth.s3_has_role

        supply_coordinator = lambda i: has_role("SUPPLY_COORDINATOR")
        supply_distributor = lambda i: has_role("SUPPLY_DISTRIBUTOR",
                                                include_admin = False,
                                                )
        supply_requester = lambda i: bool(get_managed_requester_orgs())

        order_access = lambda i: supply_coordinator(i) or \
                                 supply_requester(i)

        return M()(
                M("Orders##delivery", c="req", f="req", vars={"type": 1}, check=order_access)(
                    M("Create", m="create", vars={"type": 1}, check=supply_requester),
                    ),
                M("Shipment##process", c="inv", f="send", restrict="SUPPLY_COORDINATOR"),
                M("Shipments", c="inv", f="send", check=supply_distributor),
                M("Deliveries", "inv", "recv", check=supply_requester),
                M("Statistics", link=False, restrict="SUPPLY_COORDINATOR")(
                    M("Orders##delivery", c="req", f="req_item", m="report"),
                    M("Shipments", c="inv", f="track_item", m="report"),
                    ),
                M("Items", c="supply", f="item")(
                    M("Create", m="create"),
                    ),
                M("Warehouses", c="inv", f="warehouse", restrict="ADMIN"),
                )

    # -------------------------------------------------------------------------
    def supply(self):
        """ SUPPLY / Supply Chain Management """

        return self.req()

    # -------------------------------------------------------------------------
    @classmethod
    def inv(cls):
        """ INV / Inventory Management """

        return cls.req()

# END =========================================================================
