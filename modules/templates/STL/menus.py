# -*- coding: utf-8 -*-

from gluon import *
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

        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        return [
            MM("Beneficiaries", c=("dvr", "pr"), f=("person", "index")),
            MM("Organizations", c=("org", "project"), f=("organisation", "index")),
            MM("Staff", c="hrm", f=("staff", "index")),
            MM("Distributions", c="supply", f=("distribution_item", "index")),
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
                        )
            if settings.get_auth_password_retrieval():
                menu_personal(MP("Lost Password", c="default", f="user",
                                 m = "retrieve_password",
                                 ),
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

        ADMIN = current.auth.get_system_roles().ADMIN

        menu_about = MA(c="default")(
            MA("Help", f="help"),
            #MA("Contact", f="contact"),
            MA("Version", f="about", restrict = ADMIN),
        )
        return menu_about

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Application Side Menu """

    # -------------------------------------------------------------------------
    @staticmethod
    def dvr():
        """ DVR / Disaster Victim Registry """

        # Not scalable:
        #due_followups = current.s3db.dvr_due_followups() or "0"
        #follow_up_label = "%s (%s)" % (current.T("Due Follow-ups"),
        #                               due_followups,
        #                               )

        follow_up_label = current.T("Due Follow-ups")

        ADMIN = current.auth.get_system_roles().ADMIN

        return M(c=("dvr", "pr"))(
                    M("Current Beneficiaries", c=("dvr", "pr"), f="person",
                      vars = {"closed": "0"})(
                        M("Create", m="create"),
                        M("All Beneficiaries", vars = {}),
                        M("Beneficiary Report", m="report"),
                        ),
                    M("Protection Response",
                      c="dvr", f="case_activity", link=False)(
                          M("Overview", m="summary", p="read"),
                          M(follow_up_label, f="due_followups"),
                      ),
                    M("Activities", link=False,
                      restrict = ("ORG_ADMIN", "GROUP_ACTIVITIES", "MENTAL_HEALTH"))(
                        M("Group Activities", f="activity",
                          vars = {"service_type": "PSS"},
                          restrict = ("ORG_ADMIN", "GROUP_ACTIVITIES",),
                          ),
                        M("Mental Health Support", f="activity",
                          vars = {"service_type": "MH"},
                          restrict = ("ORG_ADMIN", "MENTAL_HEALTH",),
                          ),
                        ),
                    M("Archive", link=False)(
                        M("Former Beneficiaries", f="person",
                          vars = {"closed": "1"},
                          ),
                        M("Invalid Cases", f="person",
                          vars = {"archived": "1"},
                          ),
                        ),
                    M("Administration", c="dvr", link=False,
                      restrict = (ADMIN, "ORG_ADMIN"))(
                        M("Education Levels", c="pr", f="education_level"),
                        M("Occupation Types", c="pr", f="occupation_type"),
                        M("Beneficiary Types", f="beneficiary_type"),
                        #M("Evaluation Questions", f="evaluation_question"),
                        M("Housing Types", f="housing_type"),
                        M("Income Sources", f="income_source"),
                        SEP(),
                        M("Intervention Types", f="response_type"),
                        M("Need Types", f="need", m="hierarchy"),
                        M("Protection Assessment", f="vulnerability_type", m="hierarchy"),
                        M("Provider Types", f="provider_type"),
                        M("Referral Types", f="referral_type"),
                        M("Termination Types", f="termination_type"),
                        SEP(),
                        M("Activity Age Groups", f="activity_age_group"),
                        M("Activity Group Types", f="activity_group_type"),
                        M("Activity Focuses", f="activity_focus"),
                        ),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def pr(cls):
        """ PR - use DVR menu """

        return cls.dvr()

    # -------------------------------------------------------------------------
    @classmethod
    def project(cls):
        """ PROJECT - use ORG menu """

        return cls.org()

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        ADMIN = current.auth.get_system_roles().ADMIN

        return M(c=("org", "project"))(
                    M("Organizations", f="organisation")(
                        M("Create", m="create"),
                        #M("Import", m="import")
                    ),
                    #M("Offices", f="office")(
                    #    M("Create", m="create"),
                    #    M("Map", m="map"),
                    #    M("Import", m="import")
                    #),
                    M("Facilities", f="facility")(
                       M("Create", m="create"),
                       #M("Import", m="import"),
                    ),
                    M("Administration", c=("org", "project"), link=False,
                      restrict = (ADMIN, "ORG_ADMIN"))(
                        M("Organization Types", f="organisation_type"),
                        M("Service Types", f="service", m="hierarchy"),
                        M("Facility Types", f="facility_type"),
                        M("Projects", c="project", f="project"),
                    ),
                    #M("Office Types", f="office_type",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM / Human Resources Management """

        settings = current.deployment_settings
        ADMIN = current.auth.get_system_roles().ADMIN

        return M(c="hrm")(
                    M(settings.get_hrm_staff_label(), f="staff")(
                        M("Create", m="create"),
                        M("Import", f="person", m="import", p="create",
                          vars = {"group": "staff"},
                          ),
                      ),
                    M("Job Title Catalog", f="job_title", restrict=[ADMIN])(
                        M("Create", m="create"),
                      ),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def supply():
        """ SUPPLY / Supply Item Distribution """

        ADMIN = current.auth.get_system_roles().ADMIN

        return M(c="supply")(
                    M("Distribution Items", f="distribution_item")(
                        M("Create", m="create"),
                        ),
                    M("Administration", link=False,
                      restrict = (ADMIN, "ORG_ADMIN"))(
                        M("Items", f="item"),
                        M("Catalogs", f="catalog"),
                        M("Item Categories", f="item_category"),
                        )
                    )

# END =========================================================================
