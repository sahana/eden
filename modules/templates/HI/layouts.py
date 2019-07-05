# -*- coding: utf-8 -*-

from gluon import *
from gluon.storage import Storage
from s3 import *
#from s3theme import NAV, SECTION

# Below is an example which you can base your own template's layout.py on
# - there are also other examples in the other templates folders
# - you will need to restart web2py after making changes to this file

# =============================================================================
#class S3MainMenuLayout(S3NavigationItem):
#    """
#        Application Main Menu Layout
#
#        The layout() function takes an S3NavigationItem instance as input
#        and renders it as an HTML helper class instance. If the item can
#        or shall not be rendered on the page, this method must return None.
#
#        S3NavigationItem instances provide a number of attributes and methods
#        to support context-sensisitve rendering (see modules/s3/s3navigation.py).
#
#        Note that individual items can override the layout method by explicitly
#        setting the layout-property in the item's constructor.
#    """
#
#    @staticmethod
#    def layout(item):
#        """ Custom Layout Method """
#
#    @staticmethod
#    def layout(item):
#        """ Layout Method (Item Renderer) """
#
#        # Manage flags: hide any disabled/unauthorized items
#        if not item.authorized and not item.opts.always_display:
#            item.enabled = False
#            item.visible = False
#        elif item.enabled is None or item.enabled:
#            item.enabled = True
#            item.visible = True
#
#        if item.enabled and item.visible:
#
#            items = item.render_components()
#            if item.parent is not None:
#
#                if item.attr._class:
#                    classes = item.attr._class.split(" ")
#                else:
#                    classes = []
#
#                if item.parent.parent is None:
#                    # Item at the top-level?
#                    toplevel = True
#                    if item.opts.right:
#                        classes.append("menu-right")
#                else:
#                    toplevel = False
#
#                if item.components:
#                    classes.append("has-dropdown not-click")
#                    _class = " ".join(classes)
#                    # Menu item with Dropdown
#                    if item.get_first(enabled=True):
#                        _href = item.url()
#                        return LI(A(item.label,
#                                    _href=_href,
#                                    _id=item.attr._id
#                                    ),
#                                  UL(items,
#                                     _class="dropdown"
#                                     ),
#                                  _class=_class,
#                                  )
#                else:
#                    # Menu item without Drop-Down
#                    if toplevel:
#                        item_url = item.url()
#                        if item_url == URL(c="default", f="index"):
#                            classes.append("menu-home")
#                        if item.selected:
#                            classes.append("active")
#                        _class = " ".join(classes)
#                        return LI(A(item.label,
#                                    _href=item_url,
#                                    _id=item.attr._id,
#                                    _target=item.attr._target,
#                                    ),
#                                  _class=_class,
#                                  )
#                    else:
#                        # Submenu item
#                        if isinstance(item.label, dict):
#                            if "id" in item.label:
#                                return S3MainMenuDefaultLayout.checkbox_item(item)
#                            elif "name" in item.label:
#                                label = item.label["name"]
#                            else:
#                                return None
#                        else:
#                            label = item.label
#                        link = A(label,
#                                 _href=item.url(),
#                                 _id=item.attr._id,
#                                 _target=item.attr._target,
#                                 )
#                        _class = " ".join(classes)
#                        return LI(link, _class=_class)
#            else:
#                # The main menu itself
#                T = current.T
#                settings = current.deployment_settings
#
#                if item.opts.title_area:
#                    # Custom override
#                    title_area = item.opts.title_area
#                else:
#                    # Standard: render a menu logo
#                    logo = settings.get_ui_menu_logo()
#                    if logo is None:
#                        # Render an icon
#                        logo = SPAN(settings.get_system_name_short(),
#                                    _class="logo",
#                                    )
#                    elif isinstance(logo, str):
#                        # Assume image-URL
#                        logo = IMG(_src = logo,
#                                   _class = "logo",
#                                   _alt = settings.get_system_name_short(),
#                                   )
#                    #else:
#                        # use as-is (assume HTML or T())
#                    title_area = A(logo,
#                                   _href = URL(c="default", f="index"),
#                                   _title = T("Homepage"),
#                                   )
#
#                # Arrange items left/right
#                right = []
#                left = []
#                for item in items:
#                    if "menu-right" in item["_class"]:
#                        item.remove_class("menu-right")
#                        right.append(item)
#                    else:
#                        left.append(item)
#                right.reverse()
#
#                # Reverse if right-to-left
#                if current.response.s3.rtl:
#                    right, left = left, right
#
#                # Build top-bar HTML
#                return NAV(UL(LI(title_area,
#                                 _class="name",
#                                 ),
#                              LI(A(SPAN(T("Menu"))),
#                                 _class="toggle-topbar menu-icon",
#                                 ),
#                              _class="title-area",
#                              ),
#                           SECTION(UL(right,
#                                      _class="right",
#                                      ),
#                                   UL(left,
#                                      _class="left",
#                                      ),
#                                   _class="top-bar-section",
#                                   ),
#                           _class = "top-bar",
#                           data = {"topbar": " "},
#                           )
#        else:
#            return None
#
#    # ---------------------------------------------------------------------
#    @staticmethod
#    def checkbox_item(item):
#        """ Render special active items """
#
#        name = item.label
#        link = item.url()
#        _id = name["id"]
#        if "name" in name:
#            _name = name["name"]
#        else:
#            _name = ""
#        if "value" in name:
#            _value = name["value"]
#        else:
#            _value = False
#        if "request_type" in name:
#            _request_type = name["request_type"]
#        else:
#            _request_type = "ajax"
#        if link:
#            if _request_type == "ajax":
#                _onchange='''var val=$('#%s:checked').length;$.getS3('%s'+'?val='+val,null,false,null,false,false)''' % \
#                          (_id, link)
#            else:
#                # Just load the page. Use this if the changed menu
#                # item should alter the contents of the page, and
#                # it's simpler just to load it.
#                _onchange="location.href='%s'" % link
#        else:
#            _onchange=None
#        return LI(A(INPUT(_type="checkbox",
#                          _id=_id,
#                          _onchange=_onchange,
#                          value=_value,
#                          ),
#                    "%s" % _name,
#                    _nowrap="nowrap",
#                    ),
#                  _class="menu-toggle",
#                  )
#
# =============================================================================
#class S3OptionsMenuLayout(S3NavigationItem):
#    """ Controller Options Menu Layout """
#
#    @staticmethod
#    def layout(item):
#        """ Custom Layout Method """
#
#        # Manage flags: hide any disabled/unauthorized items
#        if not item.authorized:
#            enabled = False
#            visible = False
#        elif item.enabled is None or item.enabled:
#            enabled = True
#            visible = True
#
#        if enabled and visible:
#            if item.parent is not None:
#                if item.enabled and item.authorized:
#
#                    if item.components:
#                        # Submenu
#                        _class = ""
#                        if item.parent.parent is None and item.selected:
#                            _class = "active"
#
#                        section = [LI(A(item.label,
#                                        _href=item.url(),
#                                        _id=item.attr._id,
#                                        ),
#                                      _class="heading %s" % _class,
#                                      ),
#                                   ]
#
#                        items = item.render_components()
#                        if items:
#                            section.append(UL(items))
#                        return section
#
#                    else:
#                        # Submenu item
#                        if item.parent.parent is None:
#                            _class = "heading"
#                        else:
#                            _class = ""
#
#                        return LI(A(item.label,
#                                    _href=item.url(),
#                                    _id=item.attr._id,
#                                    ),
#                                  _class=_class,
#                                  )
#            else:
#                # Main menu
#                items = item.render_components()
#                return DIV(NAV(UL(items, _id="main-sub-menu", _class="side-nav")), _class="sidebar")
#
#        else:
#            return None
#
# =============================================================================
#class S3MenuSeparatorLayout(S3NavigationItem):
#    """ Simple menu separator """
#
#    @staticmethod
#    def layout(item):
#        """ Custom Layout Method """
#
#        if item.parent is not None:
#            return LI(_class="divider hide-for-small")
#        else:
#            return None
#
# END =========================================================================
