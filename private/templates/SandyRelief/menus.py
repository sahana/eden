# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

class S3MainMenu(default.S3MainMenu):
    """
        Custom Application Main Menu:

        The main menu consists of several sub-menus, each of which can
        be customized separately as a method of this class. The overall
        composition of the menu is defined in the menu() method, which can
        be customized as well:

        Function        Sub-Menu                Access to (standard)

        menu_modules()  the modules menu        the Eden modules
        menu_gis()      the GIS menu            GIS configurations
        menu_admin()    the Admin menu          System/User Administration
        menu_lang()     the Language menu       Selection of the GUI locale
        menu_auth()     the User menu           Login, Logout, User Profile
        menu_help()     the Help menu           Contact page, About page

        The standard uses the MM layout class for main menu items - but you
        can of course use a custom layout class which you define in layouts.py.

        Additional sub-menus can simply be defined as additional functions in
        this class, and then be included in the menu() method.

        Each sub-menu function returns a list of menu items, only the menu()
        function must return a layout class instance.
    """
    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):
        """ Compose Menu """

        main_menu = MM()(

            # Modules-menu, align-left
            cls.menu_modules(),

            # Service menus, align-right
            # Note: always define right-hand items in reverse order!
            cls.menu_help(right=True),
            cls.menu_auth(right=True),
            cls.menu_lang(right=True),
            cls.menu_admin(right=True),
            cls.menu_gis(right=True)
        )
        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        return [
            homepage(),
            homepage("project"),
            homepage("req", f="req_item", m="search")(
                MM("Request Supplies", f="req", m="create", vars={"type": 1}),
                MM("Request People", f="req", m="create", vars={"type": 3})
            ),
            MM("Locations", c="gis")(
                MM("Facilities", c="org", f="facility", m="search"),
                MM("Warehouses", c="inv", f="warehouse", m="search"),
                MM("Create a Facility", c="org", f="facility", m="create")
            ),
            MM("Contacts", c="hrm", f="staff", m="search")(
                MM("Groups", c="hrm", f="group"),
                MM("Organizations", c="org", f="organisation", m="search"),
                MM("People Registry", c="pr", f="index")
            ),                
            MM("Resources", url="http://occupysandy.net/resources/coordination/")(
                MM("Assets", c="asset", f="asset", m="search"),
                MM("Inventory", c="inv", f="inv_item", m="search"),
                MM("Stock Counts", c="inv", f="adj"),
                MM("Shipments", c="inv", f="send")
            ),
             MM("Cases", c="assess", f="building", m="search")(
                MM("Building Assessments", f="building", m="search"),
                MM("Canvass", f="canvass"), 
            ),  
            MM("Survey", c="survey")(
                MM("Templates", f="template"),
                MM("Assessments", f="series"),
                MM("Import Templates", f="question_list", m="import"),
            ),
        ]

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """
        Custom Controller Menus

        The options menu (left-hand options menu) is individual for each
        controller, so each controller has its own options menu function
        in this class.

        Each of these option menu functions can be customized separately,
        by simply overriding (re-defining) the default function. The
        options menu function must return an instance of the item layout.

        The standard menu uses the M item layout class, but you can of
        course also use any other layout class which you define in
        layouts.py (can also be mixed).

        Make sure additional helper functions in this class don't match
        any current or future controller prefix (e.g. by using an
        underscore prefix).
    """

    # -------------------------------------------------------------------------
    def inv(self):
        """ INV / Inventory """

        ADMIN = current.session.s3.system_roles.ADMIN

        #current.s3db.inv_recv_crud_strings()
        #crud_strings = current.response.s3.crud_strings
        #inv_recv_list = crud_strings.inv_recv.title_list
        #inv_recv_search = crud_strings.inv_recv.title_search

        return M()(
                    M("Facilities", c="org", f="facility")(
                        M("New", m="create"),
                        M("List All"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                        M("Import", m="import")
                    ),
                    M("Warehouse Stock", c="inv", f="inv_item")(
                        M("Search", f="inv_item", m="search"),
                        #M("Search Shipped Items", f="track_item", m="search"),
                        M("Stock Count", f="adj"),
                        #M("Kitting", f="kit"),
                        M("Import", f="inv_item", m="import", p="create"),
                    ),
                    M("Reports", c="inv", f="inv_item")(
                        M("Warehouse Stock", f="inv_item",m="report"),
                        M("Expiration Report", c="inv", f="track_item",
                          m="search", vars=dict(report="exp")),
                        #M("Monetization Report", c="inv", f="inv_item",
                        #  m="search", vars=dict(report="mon")),
                        #M("Utilization Report", c="inv", f="track_item",
                        #  m="search", vars=dict(report="util")),
                        #M("Summary of Incoming Supplies", c="inv", f="track_item",
                        #  m="search", vars=dict(report="inc")),
                        #M("Summary of Releases", c="inv", f="track_item",
                        #  m="search", vars=dict(report="rel")),
                    ),
                    #M(inv_recv_list, c="inv", f="recv")(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    M("Search", m="search"),
                    #),
                    M("Sent Shipments", c="inv", f="send")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Search Shipped Items", f="track_item", m="search"),
                    ),
                    M("Items", c="supply", f="item")(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Report", m="report"),
                        M("Import", f="catalog_item", m="import", p="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[ADMIN])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                )

    # -------------------------------------------------------------------------
    def hrm(self):
        """ HRM / Human Resources Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        manager_mode = lambda i: s3.hrm.mode is None
        personal_mode = lambda i: s3.hrm.mode is not None
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 ADMIN in s3.roles
        settings = current.deployment_settings
        job_roles = lambda i: settings.get_hrm_job_roles()
        teams = settings.get_hrm_teams()
        use_teams = lambda i: teams

        return M(c="hrm")(
                    M(settings.get_hrm_staff_label(), f="staff",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", f="person", m="import",
                          vars={"group":"staff"}, p="create"),
                    ),
                    M(teams, f="group",
                      check=[manager_mode, use_teams])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Department Catalog", f="department",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Job Role Catalog", f="job_role",
                      check=[manager_mode, job_roles])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Job Title Catalog", f="job_title",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Skill Catalog", f="skill",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        #M("Skill Provisions", f="skill_provision"),
                    ),
                    #M("Training Events", f="training_event",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    M("Search", m="search"),
                    #    M("Search Training Participants", f="training",
                    #      m="search"),
                    #    M("Import Participant List", f="training", m="import"),
                    #),
                    #M("Training Course Catalog", f="course",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    #M("Course Certificates", f="course_certificate"),
                    #),
                    #M("Certificate Catalog", f="certificate",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    #M("Skill Equivalence", f="certificate_skill"),
                    #),
                    #M("Reports", f="staff", m="report",
                    #  check=manager_mode)(
                    #    M("Staff Report", m="report"),
                    #    M("Expiring Staff Contracts Report",
                    #      vars=dict(expiring=1)),
                    #    M("Training Report", f="training", m="report"),
                    #),
                    M("Personal Profile", f="person",
                      check=personal_mode, vars=dict(mode="personal")),
                    # This provides the link to switch to the manager mode:
                    M("Staff Management", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    M("Personal Profile", f="person",
                      check=manager_mode, vars=dict(mode="personal"))
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ ORG / Organization Registry """

        #ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="org")(
                    M("Facilities", f="facility")(
                        M("New", m="create"),
                        M("List All"),
                        #M("Review/Approve New", m="review"),
                        M("Map", m="map"),
                        M("Search", m="search"),
                        M("Import", m="import")
                    ),
                    M("Organizations", f="organisation")(
                        M("Add Organization", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import")
                    ),
                    M("Facility Types", f="facility_type",
                      #restrict=[ADMIN]
                      )(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Organization Types", f="organisation_type",
                      #restrict=[ADMIN]
                      )(
                        M("New", m="create"),
                        M("List All"),
                    ),
                )

    # -------------------------------------------------------------------------
    def req(self):
        """ REQ / Request Management """

        db = current.db
        SUPER = lambda i: \
            db(db.auth_group.uuid=="super").select(db.auth_group.id,
                                                   limitby=(0, 1),
                                                   cache=s3db.cache
                                                   ).first().id

        return M(c="req")(
                    M("Requests", f="req")(
                        M("Request Supplies", m="create", vars={"type": 1}),
                        M("Request People", m="create", vars={"type": 3}),
                        M("Search Requests", m="search"),
                        #M("List All"),
                        M("List Recurring Requests", f="req_template"),
                        #M("Search", m="search"),
                        #M("Map", m="map"),
                        M("Report", m="report"),
                        M("FEMA Items Required", f="fema", m="search",
                          restrict=[SUPER]),
                        M("Search All Requested Items", f="req_item", m="search"),
                        M("Search All Requested Skills", f="req_skill", m="search"),
                    ),
                    #M("Priority Items", f="summary_option")(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #),
                    M("Commitments", f="commit")(
                        M("List All")
                    ),
                    M("Sent Shipments", f="send")(
                        #M("New", m="create"),
                        M("List All"),
                        #M("Search Shipped Items", f="track_item", m="search"),
                    ),
                    M("Items", c="supply", f="item",
                      restrict=[SUPER])(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Report", m="report"),
                        M("Import", f="catalog_item", m="import", p="create"),
                    ),
                    M("Item Categories", c="supply", f="item_category",
                      restrict=[SUPER])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                )

# END =========================================================================
