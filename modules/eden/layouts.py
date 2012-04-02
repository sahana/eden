# -*- coding: utf-8 -*-

""" Sahana-Eden GUI Layouts (HTML Renderers)

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

    @status: work in progress
    @todo: - complete layout implementations
           - render "selected" (flag in item)
"""

__all__ = ["S3MainMenuLayout", "MM",
           "S3OptionsMenuLayout", "M",
           "S3MenuSeparatorLayout", "SEP",
           "S3BreadcrumbsLayout",
           "homepage",
           "ForeignRecordFormPopup",]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3MainMenuLayout(S3NavigationItem):
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
                            link = DIV(SPAN(A(_href=_href),
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

# -----------------------------------------------------------------------------
# Shortcut
MM = S3MainMenuLayout

# =============================================================================
class S3OptionsMenuLayout(S3NavigationItem):
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
                                    _href=_href),
                                  _class="hoverable"),
                              UL(items,
                                 _class="submenu"))
                else:
                    # Menu item
                    if item.parent.parent is None:
                        # Top level item
                        return LI(DIV(A(item.label,
                                        _href=item.url()),
                                      _class="hoverable"))
                    else:
                        # Submenu item
                        return LI(A(item.label,
                                    _href=item.url()))
            else:
                # Main menu
                return UL(items, _id="subnav")

        else:
            return None

# -----------------------------------------------------------------------------
# Shortcut
M = S3OptionsMenuLayout

# =============================================================================
class S3MenuSeparatorLayout(S3NavigationItem):
    """ Simple menu separator """

    @staticmethod
    def layout(item):

        if item.parent is not None:
            return LI(HR(), _class="menu_separator")
        else:
            return None

# -----------------------------------------------------------------------------
# Shortcut
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

    if module is None:
        module = "default"
    if module in all_modules:
        m = all_modules[module]
        module = m.name_nice
    return layout(module, c=c, f="index", **attr)


class ForeignRecordFormPopup(S3NavigationItem):
    """
        Add a link to show a form for adding a new foreign key record.
    """

    def __init__(self, *args, **kwargs):
        super(ForeignRecordFormPopup, self).__init__(*args, **kwargs)
        self.vars['format'] = "popup"
        self.args.append("create")

    def check_active(self, request=None):
        return True

    @staticmethod
    def layout(item):
        if not item.authorized:
            return None

        link = A(item.label,
                 _href=item.url(),
                 _class="colorbox")
        tooltip = DIV(_class="tooltip",
                      _title="%s|%s" % (item.label, item.opts.tooltip))
        return DIV(link, tooltip)

# END =========================================================================
