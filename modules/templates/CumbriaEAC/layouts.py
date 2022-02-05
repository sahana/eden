# -*- coding: utf-8 -*-

__all__ = ("S3AboutMenuLayout",
           "MA",
           "S3MainMenuLayout",
           "MM",
           "S3PersonalMenuLayout",
           "MP",
           )
from gluon import A, DIV, LABEL, LI, UL
from s3 import S3NavigationItem, ICON
from s3layouts import S3MainMenuDefaultLayout
from s3theme import NAV

# =============================================================================
class S3AboutMenuLayout(S3NavigationItem):
    """
        Footer menu

        Classes use Foundation's Menu component
            https://get.foundation/sites/docs/menu.html
    """

    @staticmethod
    def layout(item):

        if item.parent is None:
            # The menu
            items = item.render_components()
            if items:
                return UL(items,
                          _class = "menu", # https://get.foundation/sites/docs/menu.html
                          )
            else:
                return "" # menu is empty
        else:
            # A menu item
            if item.enabled and item.authorized:
                return LI(A(item.label,
                            _href = item.url(),
                            ))
            else:
                return None

# -----------------------------------------------------------------------------
# Shortcut
MA = S3AboutMenuLayout

# =============================================================================
class S3MainMenuLayout(S3MainMenuDefaultLayout):
    """
        Application Main Menu Layout
            - no menu logo (as this is in the header instead)
            - no right menu (as this is in the header instead)

        Classes use Foundation's Top-Bar Component, which wraps
                    Foundation's Menu component
            https://get.foundation/sites/docs/menu.html
            https://get.foundation/sites/docs/top-bar.html
    """

    # Use the layout method of this class in templates/<theme>/layouts.py
    # if it is available at runtime (otherwise fallback to this layout):
    OVERRIDE = "S3MainMenuLayout"

    @staticmethod
    def layout(item):
        """ Layout Method (Item Renderer) """

        # Manage flags: hide any disabled/unauthorized items
        if not item.authorized and not item.opts.always_display:
            item.enabled = False
            item.visible = False
        elif item.enabled is None or item.enabled:
            item.enabled = True
            item.visible = True

        if item.enabled and item.visible:

            items = item.render_components()
            if item.parent is not None:

                if item.attr._class:
                    classes = item.attr._class.split(" ")
                else:
                    classes = []

                if item.parent.parent is None:
                    # Item at the top-level?
                    toplevel = True
                    #if item.opts.right:
                    #    classes.append("menu-right")
                else:
                    toplevel = False

                if item.components:
                    # Menu item with Dropdown
                    if item.get_first(enabled = True):
                        classes.append("is-dropdown-submenu-parent") # Prevent FoUC
                        _class = " ".join(classes)
                        return LI(A(item.label,
                                    _href = item.url(),
                                    _id = item.attr._id,
                                    ),
                                  UL(items,
                                     _class = "menu",
                                     ),
                                  _class = _class,
                                  )
                else:
                    # Menu item without Drop-Down
                    if toplevel:
                        item_url = item.url()
                        #if item_url == URL(c="default", f="index"):
                        #    classes.append("menu-home")
                        if item.selected:
                            classes.append("active")
                        _class = " ".join(classes)
                        icon = item.opts.icon
                        if icon:
                            label = LABEL(ICON(icon), item.label)
                        else:
                            label = item.label
                        return LI(A(label,
                                    _href = item_url,
                                    _id = item.attr._id,
                                    _target = item.attr._target,
                                    ),
                                  _class = _class,
                                  )
                    else:
                        # Submenu item
                        if isinstance(item.label, dict):
                            if "id" in item.label:
                                return S3MainMenuDefaultLayout.checkbox_item(item)
                            elif "name" in item.label:
                                label = item.label["name"]
                            else:
                                return None
                        else:
                            label = item.label
                        link = A(label,
                                 _href = item.url(),
                                 _id = item.attr._id,
                                 _target = item.attr._target,
                                 )
                        _class = " ".join(classes)
                        return LI(link,
                                  _class = _class,
                                  )
            else:
                # The main menu itself

                # Arrange items left/right
                #right = []
                #left = []
                #for item in items:
                #    if "menu-right" in item["_class"]:
                #        item.remove_class("menu-right")
                #        right.append(item)
                #    else:
                #        left.append(item)
                #right.reverse()

                # Reverse if right-to-left
                #if current.response.s3.rtl:
                #    right, left = left, right

                left = UL(items,
                          _class = "menu dropdown",
                          )
                left["_data-dropdown-menu"] = ""
                #right = UL(right,
                #           _class = "menu dropdown",
                #           )
                #right["_data-dropdown-menu"] = ""

                # Build top-bar HTML
                return NAV(DIV(left,
                               _class = "top-bar-left",
                               ),
                           #DIV(right,
                           #    _class = "top-bar-right",
                           #    ),
                           _class = "top-bar",
                           )
        else:
            return None

# -----------------------------------------------------------------------------
# Shortcut
MM = S3MainMenuLayout

# =============================================================================
class S3PersonalMenuLayout(S3NavigationItem):

    @staticmethod
    def layout(item):

        if item.parent is None:
            # The menu
            items = item.render_components()
            if items:
                return UL(items,
                          _class = "menu personal-menu",
                          )
            else:
                return "" # menu is empty
        else:
            # A menu item
            if item.enabled and item.authorized:
                return LI(A(item.label,
                            _href = item.url(),
                            _title = item.label or "",
                            ))
            else:
                return None

# -----------------------------------------------------------------------------
# Shortcut
MP = S3PersonalMenuLayout

# END =========================================================================
