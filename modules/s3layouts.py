# -*- coding: utf-8 -*-

""" Sahana Eden GUI Layouts (HTML Renderers)

    @copyright: 2012-14 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

    @todo: - complete layout implementations
           - render "selected" (flag in item)
"""

__all__ = ("S3MainMenuDefaultLayout",
           "S3OptionsMenuDefaultLayout",
           "S3MenuSeparatorDefaultLayout",
           "S3MainMenuLayout", "MM",
           "S3OptionsMenuLayout", "M",
           "S3MenuSeparatorLayout", "SEP",
           "S3BreadcrumbsLayout",
           "S3AddResourceLink",
           "homepage",
           )

from gluon import *
from s3 import *
from s3theme import NAV, SECTION

# =============================================================================
class S3MainMenuDefaultLayout(S3NavigationItem):
    """ Application Main Menu Layout """

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
                        item_url = item.url()
                        if item_url == URL(c="default", f="index"):
                            classes.append("menu-home")
                        if item.selected:
                            classes.append("active")
                        _class = " ".join(classes)
                        return LI(A(item.label,
                                    _href=item_url,
                                    _id=item.attr._id,
                                    ),
                                  _class=_class,
                                  )
                    else:
                        # Submenu item
                        if isinstance(item.label, dict):
                            if "id" in item.label:
                                return S3MainMenuLayout.checkbox_item(item)
                            elif "name" in item.label:
                                label = item.label["name"]
                            else:
                                return None
                        else:
                            label = item.label
                        link = A(label, _href=item.url(), _id=item.attr._id)
                        _class = " ".join(classes)
                        return LI(link, _class=_class)
            else:
                # Main menu

                if item.opts.title_area:
                    title_area = item.opts.title_area
                else:
                    title_area = A(" ",
                                   _href=URL(c="default", f="index"),
                                   _class="S3menulogo",
                                   )

                right = []
                left = []
                for item in items:
                    if "menu-right" in item["_class"]:
                        item.remove_class("menu-right")
                        right.append(item)
                    else:
                        left.append(item)
                right.reverse()
                if current.response.s3.rtl:
                    right, left = left, right
                return NAV(
                    UL(LI(title_area,
                          _class="name"
                          ),
                       LI(A(SPAN(current.T("Menu"))),
                          _class="toggle-topbar menu-icon",
                          ),
                       _class="title-area",
                       ),
                    SECTION(UL(right,
                               _class="right"),
                            UL(left,
                               _class="left"),
                            _class="top-bar-section"),
                    _class = "top-bar",
                    data = {"topbar": " "},
                )

        else:
            return None

    # ---------------------------------------------------------------------
    @staticmethod
    def checkbox_item(item):
        """ Render special active items """

        name = item.label
        link = item.url()
        _id = name["id"]
        if "name" in name:
            _name = name["name"]
        else:
            _name = ""
        if "value" in name:
            _value = name["value"]
        else:
            _value = False
        if "request_type" in name:
            _request_type = name["request_type"]
        else:
            _request_type = "ajax"
        if link:
            if _request_type == "ajax":
                _onchange='''var val=$('#%s:checked').length;$.getS3('%s'+'?val='+val,null,false,null,false,false)''' % \
                          (_id, link)
            else:
                # Just load the page. Use this if the changed menu
                # item should alter the contents of the page, and
                # it's simpler just to load it.
                _onchange="location.href='%s'" % link
        else:
            _onchange=None
        return LI(A(INPUT(_type="checkbox",
                          _id=_id,
                          _onchange=_onchange,
                          value=_value,
                          ),
                    "%s" % _name,
                    _nowrap="nowrap",
                    ),
                  _class="menu-toggle",
                  )

# =============================================================================
class S3OptionsMenuDefaultLayout(S3NavigationItem):
    """ Controller Options Menu Layout """

    @staticmethod
    def layout(item):
        """ Layout Method (Item Renderer) """

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

# =============================================================================
class S3MenuSeparatorDefaultLayout(S3NavigationItem):
    """ Simple menu separator """

    @staticmethod
    def layout(item):
        """ Layout Method (Item Renderer) """

        if item.parent is not None:
            return LI(_class="divider hide-for-small")
        else:
            return None

# =============================================================================
# Import menu layouts from template (if present)
#
S3MainMenuLayout = S3MainMenuDefaultLayout
S3OptionsMenuLayout = S3OptionsMenuDefaultLayout
S3MenuSeparatorLayout = S3MenuSeparatorDefaultLayout

application = current.request.application
theme = current.deployment_settings.get_theme()

layouts = "applications.%s.private.templates.%s.layouts" % (application, theme)
try:
    exec("import %s as deployment_layouts" % layouts)
except:
    pass
else:
    if "S3MainMenuLayout" in deployment_layouts.__dict__:
        S3MainMenuLayout = deployment_layouts.S3MainMenuLayout
    if "S3OptionsMenuLayout" in deployment_layouts.__dict__:
        S3OptionsMenuLayout = deployment_layouts.S3OptionsMenuLayout
    if "S3MenuSeparatorLayout" in deployment_layouts.__dict__:
        S3MenuSeparatorLayout = deployment_layouts.S3MenuSeparatorLayout

# =============================================================================
# Shortcuts for menu construction
#
M = S3OptionsMenuLayout
MM = S3MainMenuLayout
SEP = S3MenuSeparatorLayout

# =============================================================================
class S3BreadcrumbsLayout(S3NavigationItem):
    """ Breadcrumbs layout """

    @staticmethod
    def layout(item):

        if item.parent is None:
            items = item.render_components()
            return DIV(UL(items), _class='breadcrumbs')
        else:
            if item.is_last():
                _class = "highlight"
            else:
                _class = "ancestor"
            return LI(A(item.label, _href=item.url(), _class=_class))

# =============================================================================
class S3AddResourceLink(S3NavigationItem):
    """
        Links in form fields comments to show a form for adding
        a new foreign key record.
    """

    def __init__(self,
                 label=None,
                 c=None,
                 f=None,
                 t=None,
                 vars=None,
                 info=None,
                 title=None,
                 tooltip=None,
                 ):
        """
            Constructor

            @param c: the target controller
            @param f: the target function
            @param t: the target table (defaults to c_f)
            @param vars: the request vars (format="popup" will be added automatically)
            @param label: the link label (falls back to label_create)
            @param info: hover-title for the label
            @param title: the tooltip title
            @param tooltip: the tooltip text
        """

        if label is None:
            label = title
        if info is None:
            info = title

        if c is None:
            # Fall back to current controller
            c = current.request.controller

        if label is None:
            # Fall back to label_create
            if t is None:
                t = "%s_%s" % (c, f)
            label = S3CRUD.crud_string(t, "label_create")

        return super(S3AddResourceLink, self).__init__(label,
                                                       c=c, f=f, t=t,
                                                       m="create",
                                                       vars=vars,
                                                       info=info,
                                                       title=title,
                                                       tooltip=tooltip,
                                                       mandatory=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def layout(item):
        """ Layout for popup link """

        if not item.authorized:
            return None


        if current.deployment_settings.get_ui_use_button_icons():
            label = (I(" ", _class="icon-plus"),
                      item.label)
        else:
            label = item.label

        popup_link = A(label,
                       _href=item.url(format="popup"),
                       _class="s3_add_resource_link",
                       _id="%s_add" % item.function,
                       _target="top",
                       _title=item.opts.info,
                       )

        tooltip = item.opts.tooltip
        if tooltip is not None:
            ttip = DIV(_class="tooltip",
                       _title="%s|%s" % (item.opts.title, tooltip))
        else:
            ttip = ""

        return TAG[""](popup_link, ttip)

    # -------------------------------------------------------------------------
    @staticmethod
    def inline(item):
        """ Render this link for an inline component """

        if not item.authorized:
            return None

        popup_link = A(item.label,
                       _href=item.url(format="popup"),
                       _class="s3_add_resource_link action-lnk",
                       _id="%s_%s_add" % (item.vars["caller"], item.function),
                       _target="top",
                       _title=item.opts.info,
                       )

        return DIV(popup_link, _class="s3_inline_add_resource_link")

# =============================================================================
def homepage(module=None, *match, **attr):
    """
        Shortcut for module homepage menu items using the MM layout,
        retrieves the module's nice name.

        @param module: the module's prefix (controller)
        @param match: additional prefixes
        @param attr: attributes for the navigation item
    """

    settings = current.deployment_settings
    all_modules = settings.modules

    layout = S3MainMenuLayout
    c = [module] + list(match)

    if "name" in attr:
        name = attr["name"]
        attr.pop("name")
    else:
        if module is None:
            module = "default"
        if module in all_modules:
            m = all_modules[module]
            name = m.name_nice
        else:
            name = module

    if "f" in attr:
        f = attr["f"]
        del attr["f"]
    else:
        f = "index"

    return layout(name, c=c, f=f, **attr)

# END =========================================================================
