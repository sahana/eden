# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from eden.layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import eden.menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """ Custom Application Main Menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):
        """ Compose Menu (example) """

        main_menu = MM()(
            cls.menu_modules(),
        )

        # Have an additional separate personal menu
        current.menu.personal = cls.menu_personal()

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
                #MM("Teams", c="hrm", f="group"),
                MM("Organizations", c="org", f="organisation"),
                MM("Offices", c="org", f="office"),
                MM("Job Roles", c="hrm", f="job_role"),
                #MM("Skill List", c="hrm", f="skill"),
                MM("Training Events", c="hrm", f="training_event"),
                MM("Training Courses", c="hrm", f="course"),
                MM("Certificate List", c="hrm", f="certificate"),
            ),
            homepage("vol", name=T("Volunteers"))(
                MM("Volunteers", c="vol", f="volunteer"),
                #MM("Teams", c="vol", f="group"),
                MM("Job Roles", c="vol", f="job_role"),
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
                MM("Reports", c="project", f="report"),
            ),
            #homepage("event", "irs")(
            #    MM("Events", c="event", f="event"),
            #    MM("Incident Reports", c="irs", f="ireport"),
            #)
        ]

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
                        MP("Logout", c="default", f="user",
                           m="logout"),
                        MP("Change Password", c="default", f="user",
                           m="change_password"),
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
        volunteers = {"group":"volunteer"}

        return M()(
                    M("Staff", c="hrm", f=("staff", "person"),
                      check=manager_mode)(
                        M("New Staff Member", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Report", m="report",
                          vars=Storage(rows="course",
                                       cols="L1",
                                       fact="person_id",
                                       aggregate="count")),
                        M("Report Expiring Contracts",
                          vars=dict(expiring=1)),
                        M("Import", f="person", m="import",
                          vars=staff, p="create"),
                    ),
                    # M("Teams", c="hrm", f="group",
                      # check=manager_mode)(
                        # M("New Team", m="create"),
                        # M("List All"),
                    # ),
                    M("Organizations", c="org", f="organisation",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        #M("Import", m="import", p="create")
                    ),
                    M("Offices", c="org", f="office",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", m="import", p="create"),
                    ),
                    M("Job Role Catalog", c="hrm", f="job_role",
                      check=manager_mode)(
                        M("New Job Role", m="create"),
                        M("List All"),
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
                        M("Training Report", f="training", m="report",
                          vars=dict(rows="training_event_id$course_id",
                                    cols="month",
                                    fact="person_id",
                                    aggregate="count")),
                        M("Import Participant List", f="training", m="import"),
                    ),
                    M("Training Course Catalog", c="hrm", f="course",
                      check=manager_mode)(
                        M("New Training Course", m="create"),
                        M("List All"),
                        M("Course Certificates", f="course_certificate"),
                    ),
                    M("Certificate Catalog", c="hrm", f="certificate",
                      check=manager_mode)(
                        M("New Certificate", m="create"),
                        M("List All"),
                        #M("Skill Equivalence", f="certificate_skill"),
                    ),
                    M("My Profile", c="hrm", f="person",
                      check=personal_mode, vars=dict(mode="personal")),
                    # This provides the link to switch to the manager mode:
                    M("Human Resources", c="hrm", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    M("Personal Profile", c="hrm", f="person",
                      check=manager_mode, vars=dict(mode="personal"))
                )

    # -------------------------------------------------------------------------
    def irs(self):
        """ IRS Incident Reporting """

        s3_has_role = current.auth.s3_has_role

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
                        M("Report", m="report",
                          vars=dict(rows="L1",
                                    cols="category",
                                    fact="datetime",
                                    aggregate="count"))
                    ),
                    M("Incident Categories", c="irs", f="icategory",
                      check=s3_has_role(ADMIN))(
                        M("New", m="create"),
                        M("List All"),
                    ),
                )

    # -------------------------------------------------------------------------
    def org(self):
        """ Organisation Management """

        # Same as HRM
        return self.hrm()

    # -------------------------------------------------------------------------
    def event(self):
        """ Event Management """

        # Same as IRS
        return self.irs()

# END =========================================================================

