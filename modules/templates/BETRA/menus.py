"""
    Custom menus for BETRA

    License: MIT
"""

from gluon import current, URL, TAG, SPAN
from core import IS_ISO639_2_LANGUAGE_CODE
from core.ui.layouts import MM, M, ML, MP, MA
try:
    from .layouts import OM
except ImportError:
    pass
import core.ui.menus as default

from .helpers import get_default_organisation

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
        """ Custom Modules Menu """

        # Single or multiple organisations?
        if current.auth.s3_has_permission("create", "org_organisation", c="org", f="organisation"):
            organisation_id = None
        else:
            organisation_id = get_default_organisation()

        # Organisation menu
        request = current.request
        is_newsletter = request.controller == "cms" and \
                        request.function in ("newsletter", "read_newsletter")
        c = ("org", "hrm", "cms") if is_newsletter else ("org", "hrm")
        f = ("organisation", "*")
        if organisation_id:
            org_menu = MM("Organization", c=c, f=f, args=[organisation_id], ignore_args=True)
        else:
            org_menu = MM("Organizations", c=c, f=f)

        return [
            MM("Beneficiaries", c=("dvr", "pr"), f=("person", "*")),
            # MM("Requests", c="req", f="req"),
            # MM("Assets", c="asset", f="asset"),
            org_menu,
            # MM("Map", c="gis", f="index"),
            MM("Internal Tasks", c="act", f=("my_open_tasks", "task", "issue")),
            ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_org(cls):
        """ Custom Organisation Menu """

        return OM()

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls, **attr):

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

        sr = current.auth.get_system_roles()
        ADMIN = sr.ADMIN

        if not auth.is_logged_in():
            request = current.request
            login_next = URL(args=request.args, vars=request.get_vars)
            if request.controller == "default" and request.function == "user":
                login_next = auth.get_vars_next() or login_next

            #self_registration = settings.get_security_self_registration()
            menu_personal = MP()(
                        #MP("Register", c="default", f="user",
                        #   m = "register",
                        #   check = self_registration,
                        #   ),
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
            has_role = auth.s3_has_role
            is_user_admin = lambda i: not has_role(ADMIN) and (
                                        has_role(sr.ORG_ADMIN, include_admin=False) or \
                                        has_role(sr.ORG_GROUP_ADMIN, include_admin=False)
                                        )

            menu_personal = MP()(
                        MP("Administration", c="admin", f="index",
                           restrict = ADMIN,
                           ),
                        MP("Administration", c="admin", f="user",
                           check = is_user_admin,
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

        ADMIN = current.auth.get_system_roles().ADMIN

        menu_about = MA(c="default")(
                MA("Help", f="help"),
                MA("Contact", f="index", args=["contact"]),
                MA("Privacy", f="index", args=["privacy"]),
                MA("Legal Notice", f="index", args=["legal"]),
                MA("Version", f="about", restrict = ADMIN),
                )

        return menu_about

# =============================================================================
class OptionsMenu(default.OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @classmethod
    def act(cls):

        if current.s3db.act_task_is_manager():
            tasks = M("Work Orders", link=False)(
                        M("Overview", f="task"),
                        M("My Work Orders", f="my_open_tasks"),
                        )
        else:
            tasks = M("My Work Orders", f="my_open_tasks")

        menu = M(c="act")(
                    tasks,
                    M("Issue Reports", f="issue")(
                        M("Create", m="create"),
                        ),
                    )

        return menu

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
    @classmethod
    def hrm(cls):

        return cls.org()

    # -------------------------------------------------------------------------
    @staticmethod
    def dvr():
        """ DVR / Disaster Victim Registry """

        sr = current.auth.get_system_roles()
        ADMIN = sr.ADMIN
        ORG_ADMIN = sr.ORG_ADMIN

        return M(c="dvr")(
                M("Current Cases", c=("dvr", "pr"), f="person")(
                    M("Create", m="create", t="pr_person", p="create"),
                    M("All Cases", vars = {"closed": "include"}),
                    M("Tasks", c="dvr", f="task"),
                    ),
                M("Current Needs", f="case_activity")(
                    # M("Emergencies", vars={"~.emergency": "True"}),
                    M("Report", m="report"),
                    ),
                M("Archive", link=False)(
                    M("Closed Cases", f="person",
                        restrict = (ADMIN, ORG_ADMIN, "CASE_ADMIN"),
                        vars={"closed": "only"},
                        ),
                    M("Invalid Cases", f="person",
                        vars={"archived": "1", "closed": "1"},
                        restrict = (ADMIN, ORG_ADMIN),
                        ),
                    ),
                M("Administration", link=False, restrict=ADMIN)(
                    # Global types
                    M("Case Status", f="case_status"),
                    M("Grant Types", f="grant_type")
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        T = current.T
        auth = current.auth

        ADMIN = current.session.s3.system_roles.ADMIN

        # Single or multiple organisations?
        if auth.s3_has_permission("create", "org_organisation", c="org", f="organisation"):
            organisation_id = None
        else:
            organisation_id = get_default_organisation()
        if organisation_id:
            org_menu = M("Organization", c="org", f="organisation", args=[organisation_id], ignore_args=True)
        else:
            org_menu = M("Organizations", c="org", f="organisation")(
                            M("Create", m="create"),
                            )

        # Newsletter menu
        author = auth.s3_has_permission("create", "cms_newsletter", c="cms", f="newsletter")
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

        return M(c=("org", "hrm", "cms"))(
                    org_menu,
                    M("Organization Groups", f="group")(
                        M("Create", m="create"),
                        ),
                    M("Staff", c="hrm", f="staff"),
                    cms_menu,
                    M("Administration", link=False, restrict=[ADMIN])(
                        M("Organization Types", c="org", f="organisation_type"),
                        M("Job Titles", c="hrm", f="job_title"),
                        ),
                    )

# END =========================================================================
