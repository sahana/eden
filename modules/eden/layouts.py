# -*- coding: utf-8 -*-

""" Sahana Eden GUI Layouts (HTML Renderers)

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3MainMenuDefaultLayout",
           "S3OptionsMenuDefaultLayout",
           "S3MenuSeparatorDefaultLayout",
           "S3MainMenuLayout", "MM",
           "S3OptionsMenuLayout", "M",
           "S3MenuSeparatorLayout", "SEP",
           "S3BreadcrumbsLayout",
           "S3AddResourceLink",
           "homepage"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3MainMenuDefaultLayout(S3NavigationItem):
    """ Application Main Menu Layout """

    @staticmethod
    def layout(item):

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
                if item.opts.right:
                    _class = "fright"
                else:
                    _class = "fleft"
                if item.components:
                    # Submenu, render only if there's at list one active item
                    if item.get_first(enabled=True):
                        _href = item.url()
                        return LI(DIV(A(item.label,
                                        _href=_href,
                                        _id=item.attr._id),
                                        _class="hoverable"),
                                  UL(items,
                                     _class="submenu"),
                                  _class=_class)
                else:
                    # Menu item
                    if item.parent.parent is None:
                        # Top-level item
                        _href = item.url()
                        if item.is_first():
                            # 1st item, so display logo
                            link = DIV(SPAN(A("",
                                              _href=_href),
                                              _class="S3menulogo"),
                                       SPAN(A(item.label, _href=_href),
                                              _class="S3menuHome"),
                                       _class="hoverable")
                        else:
                            link = DIV(A(item.label,
                                         _href=item.url(),
                                         _id=item.attr._id),
                                       _class="hoverable")
                        return LI(link, _class=_class)
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
                        return LI(link)
            else:
                # Main menu
                return UL(items, _id="modulenav")

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
                _onchange="var val=$('#%s:checked').length;" \
                          "$.getS3('%s'+'?val='+val, null, false, null, false, false);" % \
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
                            value=_value,
                            _onchange=_onchange),
                    " %s" % _name,
                    _nowrap="nowrap"))

# =============================================================================
class S3OptionsMenuDefaultLayout(S3NavigationItem):
    """ Controller Options Menu Layout """

    @staticmethod
    def layout(item):

        # Manage flags: hide any disabled/unauthorized items
        if not item.authorized:
            enabled = False
            visible = False
        elif item.enabled is None or item.enabled:
            enabled = True
            visible = True

        if enabled and visible:

            items = item.render_components()
            if item.parent is not None:
                if item.components:
                    # Submenu
                    _href = item.url()
                    return LI(DIV(A(item.label,
                                    _href=_href,
                                    _id=item.attr._id),
                                  _class="hoverable"),
                              UL(items,
                                 _class="submenu"))
                else:
                    # Menu item
                    if item.parent.parent is None:
                        # Top level item
                        return LI(DIV(A(item.label,
                                        _href=item.url(),
                                        _id=item.attr._id),
                                      _class="hoverable"))
                    else:
                        # Submenu item
                        return LI(A(item.label,
                                    _href=item.url(),
                                    _id=item.attr._id))
            else:
                # Main menu
                return UL(items, _id="subnav")

        else:
            return None

# =============================================================================
class S3MenuSeparatorDefaultLayout(S3NavigationItem):
    """ Simple menu separator """

    @staticmethod
    def layout(item):

        if item.parent is not None:
            return LI(HR(), _class="menu_separator")
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
                 tooltip=None):
        """
            Constructor

            @param c: the target controller
            @param f: the target function
            @param t: the target table (defaults to c_f)
            @param vars: the request vars (format="popup" will be added automatically)
            @param label: the link label (falls back to label_create_button)
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
            # Fall back to label_create_button
            if t is None:
                t = "%s_%s" % (c, f)
            label = S3CRUD.crud_string(t, "label_create_button")

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

        popup_link = A(item.label,
                       _href=item.url(format="popup"),
                       _class="colorbox",
                       _target="top",
                       _title=item.opts.info)

        tooltip = item.opts.tooltip
        if tooltip is not None:
            ttip = DIV(_class="tooltip",
                       _title="%s|%s" % (item.opts.title, tooltip))
        else:
            ttip = ""

        return DIV(popup_link, ttip)

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

    return layout(name, c=c, f="index", **attr)

# END =========================================================================
