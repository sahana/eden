# -*- coding: utf-8 -*-

from gluon import *
from gluon.storage import Storage
from s3 import *
from s3theme import NAV, SECTION

# =============================================================================
class S3MainMenuLayout(S3NavigationItem):
    """
        Application Main Menu Layout

        The layout() function takes an S3NavigationItem instance as input
        and renders it as an HTML helper class instance. If the item can
        or shall not be rendered on the page, this method must return None.

        S3NavigationItem instances provide a number of attributes and methods
        to support context-sensisitve rendering (see modules/s3/s3navigation.py).

        Note that individual items can override the layout method by explicitly
        setting the layout-property in the item's constructor.
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
            
            items = item.render_components()
            if item.parent is not None:

                classes = []

                if item.parent.parent is None:
                    # Item at the top-level?
                    toplevel = True
                    if item.opts.right:
                        classes.append("menu-right")
                else:
                    toplevel = False

                if item.components:
                    classes.append("has-dropdown not-click")
                    _class = " ".join(classes)
                    # Menu item with Dropdown
                    if item.get_first(enabled=True):
                        _href = item.url()
                        return LI(A(item.label,
                                    _href=_href,
                                    _id=item.attr._id
                                    ),
                                  UL(items,
                                     _class="dropdown"
                                     ),
                                  _class=_class,
                                  )
                else:
                    # Menu item without Drop-Down
                    if toplevel:
                        if item.selected:
                            classes.append("active")
                        _href = item.url()
                        _class = " ".join(classes)
                        return LI(A(item.label,
                                    _href=item.url(),
                                    _id=item.attr._id,
                                    ),
                                  _class=_class,
                                  )
                    else:
                        # Submenu item
                        if isinstance(item.label, dict):
                            if "name" in item.label:
                                label = item.label["name"]
                            else:
                                return None
                        else:
                            label = item.label
                        link = A(label, _href=item.url(), _id=item.attr._id)
                        return LI(link)
            else:
                # Main menu

                right = []
                left = []
                for item in items:
                    if "menu-right" in item["_class"]:
                        item.remove_class("menu-right")
                        right.append(item)
                    else:
                        left.append(item)
                right.reverse()
                return NAV(
                    UL(LI(A(" ",
                            _href=URL(c="default", f="index"),
                            _class="S3menulogo"
                            ),
                          _class="name"
                          ),
                       LI(A(SPAN(current.T("Menu"))),
                          _class="toggle-topbar menu-icon",
                          ),
                       _class="title-area"),
                    SECTION(UL(right,
                               _class="right"),
                            UL(left,
                               _class="left"),
                            _class="top-bar-section"),
                    _class = "top-bar",
                    data = {"topbar": ""},
                )

        else:
            return None

# =============================================================================
class S3MenuSeparatorLayout(S3NavigationItem):
    """ Simple menu separator """

    @staticmethod
    def layout(item):
        
        if item.parent is not None:
            return LI(_class="divider hide-for-small")
        else:
            return None

# =============================================================================
class S3OptionsMenuLayout(S3NavigationItem):
    """
        Controller Options Menu Layout
    """

    @staticmethod
    def layout(item):
        """ Custom Layout Method """

        # Manage flags: hide any disabled/unauthorized items
        if not item.authorized:
            enabled = False
            visible = False
        elif item.enabled is None or item.enabled:
            enabled = True
            visible = True

        if enabled and visible:
            if item.parent is not None:
                if item.enabled and item.authorized:
                    
                    if item.components:
                        # Submenu
                        _class = ""
                        if item.parent.parent is None and item.selected:
                            _class = "active"

                        section = [LI(A(item.label,
                                        _href=item.url(),
                                        _id=item.attr._id,
                                        ),
                                      _class="heading %s" % _class,
                                      ),
                                   ]
                                   
                        items = item.render_components()
                        if items:
                            section.append(UL(items))
                        return section

                    else:
                        # Submenu item
                        if item.parent.parent is None:
                            _class = "heading"
                        else:
                            _class = ""

                        return LI(A(item.label,
                                    _href=item.url(),
                                    _id=item.attr._id,
                                    ), 
                                  _class=_class,
                                  )
            else:
                # Main menu
                items = item.render_components()
                return DIV(NAV(UL(items, _id="main-sub-menu", _class="side-nav")), _class="sidebar")

        else:
            return None

# END =========================================================================
