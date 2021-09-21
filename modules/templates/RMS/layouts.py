# -*- coding: utf-8 -*-

from gluon import *
#from gluon.storage import Storage
from s3 import *
#from s3theme import NAV, SECTION

THEME = "RMS"

training_functions = ("certificate", "course", "course_certificate",
                      "facility", "training", "training_center",
                      "training_event", "trainee", "trainee_person",
                      )

# =============================================================================
class CIRCLE(DIV):
    """ <circle> element """

    tag = "circle"

# =============================================================================
class PATH(DIV):
    """ <path> element """

    tag = "path"

# =============================================================================
class SVG(DIV):
    """ <svg> element """

    tag = "svg"

# =============================================================================
class S3MainMenuLayout(S3NavigationItem):
    """ Custom Main Menu Layout """

    @staticmethod
    def layout(item):
        """ Custom Layout Method """

        T = current.T
        auth = current.auth
        has_role = auth.s3_has_role
        request = current.request
        c = request.controller
        f = request.function

        # Inject JavaScript
        s3 = current.response.s3
        s3.scripts.append("/%s/static/themes/RMS/js/nav.js" % request.application)
        # Use tooltip-f class to avoid clash with widgets.css
        # Remove nub
        s3.js_foundation = '''{tooltip:{tooltip_class:'.tooltip-f',tip_template:function(selector,content){var tooltipClass='';if(!$('div[data-selector="'+selector+'"]').hasClass('hd')){tooltipClass=' tooltip-m'};return '<span data-selector="'+selector+'" class="'+Foundation.libs.tooltip.settings.tooltip_class.substring(1)+tooltipClass+'">'+content+'</span>'}}}'''

        settings = ""

        len_roles = len(current.session.s3.roles)
        if (len_roles <= 2) or \
           (len_roles == 3 and has_role("RIT_MEMBER", include_admin=False)):
            # No specific Roles
            # Just show Profile on main menu
            apps = ""
            iframe = ""
            side_menu_control = ""
            module_logo = ""
        else:
            # Side-menu control
            if current.menu.options is None:
                # Don't show control as no side-menu
                side_menu_control = ""
            else:
                # Show control
                side_menu_control = DIV(A(SVG(PATH(_d = "M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z",
                                                   ),
                                              _fill = "#5f6368",
                                              _height = "24px",
                                              _width = "24px",
                                              ),
                                          _role = "button",
                                          ),
                                        _id = "menu-btn",
                                        _class = "hd",
                                        _title = T("Main menu"),
                                        )
                side_menu_control["_data-tooltip"] = ""
                side_menu_control["_aria-haspopup"] = "true"

            # Module Logo
            if c == "hrm":
                if f in training_functions:
                    image = "training.png"
                    module_name = T("Training")
                    module_href = URL(c="hrm", f="training_event")
                elif "profile" in request.get_vars:
                    image = None
                else:
                    image = "human_talent.png"
                    module_name = T("Human Talent")
                    module_href = URL(c="hrm", f="index")
            elif c == "org":
                image = "human_talent.png"
                module_name = T("Human Talent")
                module_href = URL(c="hrm", f="index")
            elif c in ("inv", "proc", "supply"):
                image = "warehouses.png"
                module_name = T("Warehouses")
                if auth.s3_has_roles(("ORG_ADMIN",
                                      "wh_operator",
                                      "logs_manager",
                                      )):
                    module_href = URL(c="inv", f="index")
                else:
                    module_href = URL(c="inv", f="req")
            elif c == "project":
                image = "projects.png"
                module_name = T("Projects")
                module_href = URL(c="project", f="project",
                                  args = "summary",
                                  )
            elif c == "deploy":
                image = "RIT.png"
                module_name = T("RIT")
                module_href = URL(c="deploy", f = "mission",
                                  args = "summary",
                                  vars = {"status__belongs": 2},
                                  )
            elif c == "member":
                image = "partners.png"
                module_name = T("Partners")
                module_href = URL(c="member", f="membership")
            else:
                image = None

            if image:
                module_logo = DIV(A(IMG(_src = URL(c="static", f="themes",
                                                   args = [THEME,
                                                           "img",
                                                           image,
                                                           ]),
                                         _class = "hi",
                                         _height = "36",
                                         _width = "36",
                                         ),
                                    _href = module_href,
                                    _role = "button",
                                    ),
                                  _class = "hdm",
                                  _title = module_name,
                                  )
                module_logo["_data-tooltip"] = ""
                module_logo["_aria-haspopup"] = "true"
            else:
                module_logo = ""

            # Applications switcher
            apps = DIV(A(SVG(PATH(_d = "M6,8c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM12,20c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM6,20c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM6,14c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM12,14c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM16,6c0,1.1 0.9,2 2,2s2,-0.9 2,-2 -0.9,-2 -2,-2 -2,0.9 -2,2zM12,8c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM18,14c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2zM18,20c1.1,0 2,-0.9 2,-2s-0.9,-2 -2,-2 -2,0.9 -2,2 0.9,2 2,2z",
                                  ),
                             _fill = "#5f6368",
                             _height = "24px",
                             _width = "24px",
                             ),
                         _href = "#",
                         _role = "button",
                         ),
                       _class = "hd",
                       _id = "apps-btn",
                       _title = T("RMS modules"),
                       )
            apps["_data-tooltip"] = ""
            apps["_aria-haspopup"] = "true"

            iframe = DIV(IFRAME(_role = "presentation",
                                _class = "hide",
                                _id = "apps-frame",
                                _frameborder = "0",
                                _scrolling = "no",
                                _src = URL(c="default", f="index",
                                           args = "apps",
                                           ),
                                _style = "height: 100%; width: 100%;",
                                ),
                         _class = "apps-frame",
                         )

            # Settings
            if has_role("ADMIN"):
                settings = URL(c="admin", f="index")
                if c == "admin":
                    settings_active = " active"
                else:
                    settings_active = ""
            elif has_role("ORG_ADMIN"):
                settings = URL(c="admin", f="user")
                if c == "admin":
                    settings_active = " active"
                else:
                    settings_active = ""
            elif auth.s3_has_roles(("hr_manager",
                                    "ns_training_manager",
                                    "training_coordinator",
                                    )):
                settings = URL(c="pr", f="forum")
                if c == "pr" and \
                   f == "forum":
                    settings_active = " active"
                else:
                    settings_active = ""
            elif has_role("logs_manager"):
                # WMS Module configuration
                # ▪ Labelling
                # ▪ Auto localisation
                # ▪ Sharing authorisation
                # ▪ Alerts
                # ▪ Email for notification    
                settings = URL(c="inv", f="req_approver")
                if c == "inv" and \
                   f == "req_approver":
                    settings_active = " active"
                else:
                    settings_active = ""

            if settings:
                settings = DIV(A(SVG(PATH(_d = "M13.85 22.25h-3.7c-.74 0-1.36-.54-1.45-1.27l-.27-1.89c-.27-.14-.53-.29-.79-.46l-1.8.72c-.7.26-1.47-.03-1.81-.65L2.2 15.53c-.35-.66-.2-1.44.36-1.88l1.53-1.19c-.01-.15-.02-.3-.02-.46 0-.15.01-.31.02-.46l-1.52-1.19c-.59-.45-.74-1.26-.37-1.88l1.85-3.19c.34-.62 1.11-.9 1.79-.63l1.81.73c.26-.17.52-.32.78-.46l.27-1.91c.09-.7.71-1.25 1.44-1.25h3.7c.74 0 1.36.54 1.45 1.27l.27 1.89c.27.14.53.29.79.46l1.8-.72c.71-.26 1.48.03 1.82.65l1.84 3.18c.36.66.2 1.44-.36 1.88l-1.52 1.19c.01.15.02.3.02.46s-.01.31-.02.46l1.52 1.19c.56.45.72 1.23.37 1.86l-1.86 3.22c-.34.62-1.11.9-1.8.63l-1.8-.72c-.26.17-.52.32-.78.46l-.27 1.91c-.1.68-.72 1.22-1.46 1.22zm-3.23-2h2.76l.37-2.55.53-.22c.44-.18.88-.44 1.34-.78l.45-.34 2.38.96 1.38-2.4-2.03-1.58.07-.56c.03-.26.06-.51.06-.78s-.03-.53-.06-.78l-.07-.56 2.03-1.58-1.39-2.4-2.39.96-.45-.35c-.42-.32-.87-.58-1.33-.77l-.52-.22-.37-2.55h-2.76l-.37 2.55-.53.21c-.44.19-.88.44-1.34.79l-.45.33-2.38-.95-1.39 2.39 2.03 1.58-.07.56a7 7 0 0 0-.06.79c0 .26.02.53.06.78l.07.56-2.03 1.58 1.38 2.4 2.39-.96.45.35c.43.33.86.58 1.33.77l.53.22.38 2.55z",
                                          ),
                                     CIRCLE(_cx = "12",
                                            _cy = "12",
                                            _r = "3.5",
                                            ),
                                     _fill = "#5f6368",
                                     _height = "24px",
                                     _width = "24px",
                                     ),
                                 _href = settings,
                                 _role = "button",
                                 ),
                               _class = "hd%s" % settings_active,
                               _title = T("Settings"),
                               )
                settings["_data-tooltip"] = ""
                settings["_aria-haspopup"] = "true"

        # Help Menu
        if c == "default" and \
           f == "help":
            help_active = " active"
        else:
            help_active = ""
        support = DIV(A(SVG(PATH(_fill = "none",
                                 _d = "M0 0h24v24H0z",
                                 ),
                            PATH(_d = "M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z",
                                 ),
                            _fill = "#5f6368",
                            _height = "24px",
                            _width = "24px",
                            ),
                        _href = URL(c = "default",
                                    f = "help",
                                    ),
                        _role = "button",
                        ),
                      _class = "hd%s" % help_active,
                      _title = T("Support"),
                      )
        support["_data-tooltip"] = ""
        support["_aria-haspopup"] = "true"

        # Logo
        name = "IFRC"
        logo = None

        # Lookup Root Organisation name & Logo
        root_org = auth.root_org()
        if root_org:
            db = current.db
            s3db = current.s3db
            language = current.session.s3.language
            if language == current.deployment_settings.get_L10n_default_language():
                l10n = None
            else:
                ltable = s3db.org_organisation_name
                query = (ltable.organisation_id == root_org) & \
                        (ltable.language == language)
                l10n = db(query).select(ltable.name_l10n,
                                        ltable.acronym_l10n,
                                        limitby = (0, 1),
                                        cache = s3db.cache,
                                        ).first()
            table = s3db.org_organisation
            record = db(table.id == root_org).select(table.name,
                                                     #table.acronym,
                                                     table.logo,
                                                     limitby = (0, 1),
                                                     cache = s3db.cache,
                                                     ).first()
            if l10n:
                #if l10n.acronym_l10n:
                    #name = _name = l10n.acronym_l10n
                #else:
                name = l10n.name_l10n

            if record:
                if not l10n:
                    #if record.acronym:
                        #name = _name = record.acronym
                    #else:
                    name = record.name

                if record.logo:
                    size = (60, None)
                    image = s3db.pr_image_library_represent(record.logo, size=size)
                    url_small = URL(c="default", f="download", args=image)
                    alt = "%s logo" % name
                    logo = IMG(_src = url_small,
                               _alt = alt,
                               _class = "hi",
                               _width = 60,
                               )

        if not logo:
            # Default to generic IFRC
            logo = IMG(_src = "/%s/static/themes/RMS/img/logo_small.png" %
                              request.application,
                       _alt = T("Red Cross/Red Crescent"),
                       _class = "hi",
                       _width = 60,
                       )

        # User Profile
        user_a = A(s3_avatar_represent(auth.user.id,
                                       _class = "hip",
                                       _height = 36,
                                       _width = 36,
                                       ),
                   _id = "user-btn",
                   _role = "button",
                   )
        user_menu = DIV(UL(LI(A(T("Profile"),
                                _href = URL(c="default", f="person"),
                                ),
                              ),
                           LI(A(T("Change Password"),
                                _href = URL(c="default", f="user",
                                            args = "change_password",
                                            ),
                                ),
                              ),
                           LI(A(T("Logout"),
                                _href = URL(c="default", f="user",
                                            args = "logout",
                                            ),
                                ),
                              ),
                           ),
                        _id = "user-menu",
                        _class = "hide",
                        )
        user_profile = DIV(user_a,
                           user_menu,
                           _class = "hdp",
                           _title = T("RMS Account"),
                           )
        user_profile["_data-tooltip"] = ""
        user_profile["_aria-haspopup"] = "true"

        # Overall menu
        divs = [DIV(side_menu_control,
                    module_logo,
                    _class = "large-2 medium-3 small-4 columns",
                    ),
                DIV(DIV(support,
                        settings,
                        apps,
                        DIV(logo,
                            _class = "hdl",
                            ),
                        user_profile,
                        iframe,
                        _class = "fright",
                        ),
                    _class = "large-4 medium-6 small-8 columns",
                    ),
                ]

        return TAG[""](*divs)

# =============================================================================
class S3AboutMenuLayout(S3NavigationItem):

    @staticmethod
    def layout(item):

        if item.parent is None:
            # The menu
            items = item.render_components()
            if items:
                return UL(items, _class="sub-nav about-menu left")
            else:
                return "" # menu is empty
        else:
            # A menu item
            if item.enabled and item.authorized:
                return LI(A(item.label, _href=item.url()))
            else:
                return None

# -----------------------------------------------------------------------------
# Shortcut
MA = S3AboutMenuLayout

# =============================================================================
class S3OrgMenuLayout(S3NavigationItem):
    """
        Layout for the organisation-specific menu
        - used by the custom PDF Form for REQ
        - replace with s3db.org_organistion_logo()?
    """

    @staticmethod
    def layout(item):
        """
            @ToDo: Migrate to s3db.org_logo_represent
        """

        name = "IFRC"
        logo = None

        # Lookup Root Organisation name & Logo
        root_org = current.auth.root_org()
        if root_org:
            db = current.db
            s3db = current.s3db
            language = current.session.s3.language
            if language == current.deployment_settings.get_L10n_default_language():
                l10n = None
            else:
                ltable = s3db.org_organisation_name
                query = (ltable.organisation_id == root_org) & \
                        (ltable.language == language)
                l10n = db(query).select(ltable.name_l10n,
                                        ltable.acronym_l10n,
                                        limitby = (0, 1),
                                        cache = s3db.cache,
                                        ).first()
            table = s3db.org_organisation
            record = db(table.id == root_org).select(table.name,
                                                     #table.acronym,
                                                     table.logo,
                                                     limitby = (0, 1),
                                                     cache = s3db.cache,
                                                     ).first()
            if l10n:
                #if l10n.acronym_l10n:
                    #name = _name = l10n.acronym_l10n
                #else:
                name = l10n.name_l10n

            if record:
                if not l10n:
                    #if record.acronym:
                        #name = _name = record.acronym
                    #else:
                    name = record.name

                if record.logo:
                    size = (60, None)
                    image = s3db.pr_image_library_represent(record.logo, size=size)
                    url_small = URL(c="default", f="download", args=image)
                    alt = "%s logo" % name
                    logo = IMG(_src = url_small,
                               _alt = alt,
                               _width = 60,
                               )

        if not logo:
            # Default to generic IFRC
            logo = IMG(_src = "/%s/static/themes/RMS/img/logo_small.png" %
                              current.request.application,
                       _alt = current.T("Red Cross/Red Crescent"),
                       _width = 60,
                       )

        # Note: render using current.menu.org.render()[0] + current.menu.org.render()[1]
        return (name, logo)

# -----------------------------------------------------------------------------
# Shortcut
OM = S3OrgMenuLayout

# END =========================================================================
