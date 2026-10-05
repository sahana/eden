# =============================================================================
#   Common Utilities run most requests
# =============================================================================

# -----------------------------------------------------------------------------
# Special local requests (e.g. from scheduler)
#
#if request.is_local:
#    # This is a request made from the local server
#    pass

# -----------------------------------------------------------------------------
# Check Permissions & fail as early as we can
#
# Set user roles
# - requires access to tables
auth.s3_set_roles()

# Check access to this controller
# - skip for scheduler as it never runs the controller
if not request.is_scheduler and not auth.permission.has_permission("read"):
    auth.permission.fail()

# -----------------------------------------------------------------------------
# Initialize Date/Time Settings
#
s3base.s3_get_tzinfo()

# -----------------------------------------------------------------------------
# Menus
#
from core.ui.layouts import *
import core.ui.menus as default_menus

MainMenu = default_menus.MainMenu
OptionsMenu = default_menus.OptionsMenu

current.menu = Storage(oauth="", options=None, override={})
if auth.permission.format in ("html"):

    # NB cascading templates:
    #
    # - uses the last of MainMenu/OptionsMenu definition in the
    #   template cascade
    # - templates can override just one of MainMenu/OptionsMenu,
    #   while "inheriting" the other one from the cascade
    # - final fallback is the default menu
    # - layouts.py is always loaded from the *theme* location, so that
    #   the HTML matches the theme's CSS.
    #
    # Example:
    #
    # - have an MainMenu in templates/MY/SUB/menus.py
    # - settings.template = ["MY", "MY.SUB"]
    # - settings.theme = "MY"
    # => will use:
    # - Layouts from templates/MYTEMPLATE/layouts.py
    # - MainMenu from templates/MY/SUB/menus.py
    # - OptionsMenu from templates/MY/menus.py

    menu_locations = []
    template = settings.get_template()
    if template != "default":
        if isinstance(template, (tuple, list)):
            menu_locations.extend(template[::-1])
        else:
            menu_locations.append(template)

    if menu_locations:
        custom_main_menu = custom_options_menu = False

        package = "applications.%s.modules.templates.%%s.menus" % appname
        for name in menu_locations:
            if name == "default":
                continue
            try:
                deployment_menus = __import__(package % name,
                                              fromlist=["MainMenu",
                                                        "OptionsMenu",
                                                        ],
                                              )
            except ImportError:
                # No menus.py (using except is faster than os.stat)
                continue
            else:
                if not custom_main_menu and \
                   hasattr(deployment_menus, "MainMenu"):
                    MainMenu = deployment_menus.MainMenu
                    custom_main_menu = True
                if not custom_options_menu and \
                   hasattr(deployment_menus, "OptionsMenu"):
                    OptionsMenu = deployment_menus.OptionsMenu
                    custom_options_menu = True
                if custom_main_menu and custom_options_menu:
                    break

    # Instantiate main menu
    main = MainMenu.menu()
else:
    main = None

menu = current.menu
menu["main"] = main

# Override controller menus
# @todo: replace by current.menu.override
s3_menu_dict = {}

# Enable access to this function from modules
from core import crud_controller
current.crud_controller = crud_controller

# END =========================================================================
