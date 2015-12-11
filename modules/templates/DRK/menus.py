# -*- coding: utf-8 -*-

from gluon import current
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

        default_site = current.deployment_settings.get_org_default_site()
        if default_site:
            args = [default_site, "profile"]
        else:
            args = None

        has_role = current.auth.s3_has_role
        if has_role("SECURITY") and not has_role("ADMIN"):
            return [
                MM("Residents", c="security", f="person"),
                #MM("ToDo", c="project", f="task"),
                MM("Check-In / Check-Out", c="cr", f="shelter", args=[default_site, "check-in"]),
            ]
        else:
            return [
                MM("Residents", c=("dvr", "pr")),
                MM("ToDo", c="project", f="task"),
                #homepage("req"),
                homepage("inv"),
                MM("Dashboard", c="cr", f="shelter", args=args),
                MM("Housing Units", c="cr", f="shelter", args=[default_site, "shelter_unit"]), # @ToDO: Move to Dashboard Widget?
                homepage("vol"),
                homepage("hrm"),
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
            MA("About", f="about"),
            MA("Contact", f="contact"),
            MA("Help", f="help"),
            #MA("Privacy", f="privacy"),
        )
        return menu_about

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def dvr():
        """ DVR / Disaster Victim Registry """

        due_followups = current.s3db.dvr_due_followups() or "0"
        follow_up_label = "%s (%s)" % (current.T("Due Follow-ups"),
                                       due_followups,
                                       )

        ADMIN = current.auth.get_system_roles().ADMIN

        return M(c="dvr")(
                    M("Cases", c=("dvr", "pr"), f="person")(
                        M("Create", m="create"),
                        M("Suspended Cases", vars={"case_flag.name": "Suspended"}),
                        M("Archived Cases", vars={"archived": "1"}),
                    ),
                    M("Activities", f="case_activity")(
                        M("Emergencies", vars = {"~.emergency": "True"}),
                        M(follow_up_label, f="due_followups"),
                        M("All Activities"),
                        M("Report", m="report"),
                    ),
                    M("Appointments", f="case_appointment")(
                        M("Bulk Status Update", m="manage"),
                    ),
                    M("Allowances", f="allowance")(
                    ),
                    M("Administration", restrict=ADMIN)(
                        M("Flags", f="case_flag"),
                        M("Case Status", f="case_status"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project/Task Management """

        return M(c="project")(
                 M("Tasks", f="task")(
                    M("Create", m="create"),
                    M("My Open Tasks", vars={"mine":1}),
                 ),
                )

# END =========================================================================
