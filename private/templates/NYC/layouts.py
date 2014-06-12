# -*- coding: utf-8 -*-

from gluon import *
from s3 import *

# =============================================================================
class S3MainMenuOuterLayout(S3NavigationItem):
    """
        Main Menu Outer Layout for a Bootstrap-based theme
    """

    @staticmethod
    def layout(item):
        """ Custom Layout Method """

        # Menu Items
        items = item.render_components()

        # When the screen width is reduced, show a button to open the menu
        attr = {"_data-toggle": "collapse",
                "_data-target": ".nav-collapse",
                }
        button = BUTTON(SPAN(_class="icon-bar"),
                        SPAN(_class="icon-bar"),
                        SPAN(_class="icon-bar"),
                        _type="button",
                        _class="btn btn-navbar",
                        **attr
                        )

        return DIV(DIV(DIV(button,
                           DIV(items,
                               _class="nav-collapse collapse"
                               ),
                           _class="container"),
                       _class="navbar-inner"),
                   _class="navbar navbar-fixed-top")

# -----------------------------------------------------------------------------
# Shortcut
MMO = S3MainMenuOuterLayout

# =============================================================================
class S3MainMenuLayout(S3NavigationItem):
    """
        Main Menu Layout for a Bootstrap-based theme
    """

    @staticmethod
    def layout(item):
        """ Custom Layout Method """

        # Manage flags: hide any disabled/unauthorized items
        if not item.authorized:
            item.enabled = False
            item.visible = False
        elif item.enabled is None or item.enabled:
            item.enabled = True
            item.visible = True

        if item.enabled and item.visible:
            if isinstance(item.parent, S3MainMenuOuterLayout):
                # The main menu
                items = item.render_components()
                if item.opts.right:
                    _class = "nav pull-right"
                else:
                    _class = "nav"
                return UL(items, _class=_class)
            else:
                label = XML("&nbsp;%s" % item.label)
                if item.components:
                    # A submenu
                    items = item.render_components()
                    anch = {"data-toggle": "dropdown"}
                    attr = {"aria-labelledby": item.attr._id}
                    return LI([A([I(_class=item.opts.icon),
                                  label, B(_class="caret")],
                                 _href=item.url(),
                                 _id=item.attr._id,
                                 _class="dropdown-toggle disabled top-level",
                                 **anch),
                               UL(items,
                                  _class="dropdown-menu",
                                  _role="menu",
                                  **attr)],
                              _class="dropdown")
                elif item.parent.parent is None:
                    # A top-level item
                    return LI(A([I(_class=item.opts.icon), label],
                                _href=item.url()))
                else:
                    # A menu item
                    return LI(A([I(_class=item.opts.icon), label],
                                _href=item.url(),
                                _tabindex='-1',
                                _role="menuitem"))
        else:
            return None
            
# -----------------------------------------------------------------------------
# Shortcut
MM = S3MainMenuLayout

# =============================================================================
class S3HomeMenuLayout(S3NavigationItem):

    @staticmethod
    def layout(item):

        # @ToDo: Move image to CSS?
        home_menu = LI(A(IMG(_src=URL(c="static", f="img",
                                      args="sahanalarge_14.png"),
                             _alt="Sahana"),
                       _class="brand",
                       _href=URL(c="default", f="index"),
                       ))
        return home_menu

# -----------------------------------------------------------------------------
# Shortcut
HM = S3HomeMenuLayout

# =============================================================================
class S3MenuDividerLayout(S3NavigationItem):

    @staticmethod
    def layout(item):

        return LI(_class="divider")

# -----------------------------------------------------------------------------
# Shortcut
SEP = S3MenuDividerLayout

# =============================================================================
#class S3MenuEmptyLayout(S3NavigationItem):
#
#    @staticmethod
#    def layout(item):
#
#        items = item.render_components()
#        return TAG[""](items)

# -----------------------------------------------------------------------------
# Shortcut
#EMPTY = S3MenuEmptyLayout

# END =========================================================================
