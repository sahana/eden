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
        """ Main Menus """

        # Footer
        current.menu.about = cls.menu_about()

        if current.auth.is_logged_in():
            # Provide top-level Navigation bar
            return MM()
        else:
            # Blank top menu
            return ""

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
                 M("Request Approvers", c="req", f="approver"),
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
                       M("Request Approvers", c="req", f="approver")(
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
            return None

        auth = current.auth
        has_role = auth.s3_has_role
        s3 = current.session.s3

        len_roles = len(s3.roles)
        if (len_roles <= 2) or \
           (len_roles == 3 and has_role("RIT_MEMBER") and not has_role("ADMIN")):
            # No Side Menu
            return None

        #ADMIN = s3.system_roles.ADMIN
        ORG_ADMIN = s3.system_roles.ORG_ADMIN

        # training_functions imported from layouts
        if request.function in training_functions:
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
                            #  vars={"expiring": "1"}),
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
                        #  vars={"access": "personal"})
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

        if current.auth.s3_has_roles(("ORG_ADMIN",
                                      "wh_manager",
                                      "national_wh_manager",
                                      )):
            return M()(
                        M("Stock Management", c="inv", link=False)(
                            M("Stock Adjustments", f="adj"),
                            M("Kitting", f="kitting"),
                            M("Receive a new shipment", f="recv", m="create"),
                            M("Send a new shipment", f="send", m="create"),
                        ),
                        M("Purchases", c="proc", f="order_item",
                          restrict=["ORG_ADMIN",
                                    "national_wh_manager"])(
                        ),
                        M("Requests", c="req", f="req")(
                            M("My Requests",
                              vars = {"mine": 1},
                              ),
                        ),
                        M("Import Inventory", c="inv", f="inv_item", m="import",
                          restrict=["ORG_ADMIN",
                                    "national_wh_manager"]),
                        M("Parameters", c="inv", link=False,
                          restrict=["ORG_ADMIN",
                                    "national_wh_manager"])(
                            M("Warehouses", f="warehouse"),
                            M("Projects", f="project"),
                            M("Catalogs", c="supply", f="catalog"),
                            M("Item Categories", c="supply", f="item_category"),
                            M("Items", c="supply", f="item"),
                            M("Suppliers", f="supplier"),
                            M("Facilities", f="facility"),
                            M("Stock limit", link=False),
                        ),
                        M("Reports", c="inv", link=False)(
                            M("Short Inventory", f="inv_item", m="report"),
                            M("Detailed Inventory", f="inv_item"),
                            M("Stock Movements", f="inv_item", m="grouped",
                              vars = {"report": "movements"},
                              ),
                            M("Stock Organisation", f="inv_item", m="grouped",
                              vars = {"report": "default"},
                              ),
                        ),
                    )
        else:
            # Normal users see their own Requests & Inventory Reports
            return M()(
                        M("Requests", c="req", link=False)(
                            M("My Requests", f="req",
                              vars = {"mine": 1},
                              ),
                        ),
                        M("Reports", c="inv", link=False)(
                            M("Short Inventory", f="inv_item", m="report"),
                            M("Detailed Inventory", f="inv_item"),
                        ),
                    )
            

    # -------------------------------------------------------------------------
    def proc(self):
        """ Procurements """

        # Same as Inventory
        return self.inv()

    # -------------------------------------------------------------------------
    def req(self):
        """ Requests Management """

        if current.request.function == "approver":
            has_role = current.auth.s3_has_role
            if has_role("ADMIN"):
                return self.admin()
            elif has_role("ORG_ADMIN"):
                return self.pr()

            return None

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
