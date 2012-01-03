# -*- coding: utf-8 -*-

"""
    S3 Navigation Module

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2011 (c) Sahana Software Foundation
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

"""

__all__ = ["S3Menu", "s3_rheader_tabs"]

from gluon import *
from gluon.storage import Storage

# =============================================================================
class S3Menu(DIV):
    """
        MENUS3 reimplementation -
            * Currently a copy of existing MENUS3
            * breadcrumbs support
            * greater control / flexibility
            * future - side menu
    """
    tag = "div"

    def __init__(self, data, **args):
        self.data = data
        self.attributes = args

    def serialize(self, data, level=0):
        if level == 0:
            # Top-level menu
            div = UL(**self.attributes)
            for i in range(len(data)):
                (name, right, link) = data[i][:3]
                if link == False:
                    continue
                if not link:
                    link = "#null"
                if right:
                    class_ = "fright"
                else:
                    class_ = "fleft"
                if len(data[i]) > 3 and data[i][3]:
                    # Submenu
                    ul_inner = self.serialize(data[i][3], level+1)
                    in_ul = LI(DIV(A(name,
                                     _href=link),
                                   _class="hoverable"),
                                ul_inner,
                                _class=class_ if ("" or self.attributes["_id"]) != "subnav" else " ")
                else:
                    if (i == 0) and (self.attributes["_id"] == "modulenav"):
                        # 1st item, so display logo
                        in_ul = LI(DIV(SPAN(A(_href=link),
                                            _class="S3menulogo"),
                                       SPAN(A(name,
                                              _href=link),
                                              _class="S3menuHome"),
                                       _class="hoverable"),
                                   _class=class_)
                    else:
                        in_ul = LI(DIV(A(name, _href=link),
                                       _class="hoverable"),
                                   _class=class_ if ("" or self.attributes["_id"]) != "subnav" else " ")
                div.append(in_ul)
        else:
            # Submenu
            div = UL(_class="submenu")
            for item in data:
                (name, right, link) = item[:3]
                # Eval link if meant to be lazily evaluated. Needed by hrm menu definition
                if type(link) == type(lambda:None):
                    link = link()

                if link == False:
                    continue
                elif not link:
                    link = "#null"
                if name == "----":
                    # Horizontal line as separator
                    li = LI(HR(), _class="menu_separator")
                elif isinstance(name, dict) and "id" in name:
                    if "name" in name:
                        _name = name["name"]
                    else:
                        _name = ""
                    _id = name["id"]
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
                            _onchange="var val=$('#%s:checked').length; $.getS3('%s'+'?val='+val, null, false, null, false, false);" % (_id, link)
                        else:
                            # Just load the page. Use this if the changed menu
                            # item should alter the contents of the page, and
                            # it's simpler just to load it.
                            _onchange="location.href='%s'" % link
                    else:
                        _onchange=None
                    li = LI(A(INPUT(_type="checkbox",
                                    _id=_id,
                                    value=_value,
                                    _onchange=_onchange),
                              " %s" % _name, _nowrap="nowrap"))
                else:
                        li = LI(A(name, _href=link))
                div.append(li)
        return div

    def xml(self):
        return self.serialize(self.data, 0).xml()

# =============================================================================
def s3_rheader_tabs(r, tabs=[]):
    """
        Constructs a DIV of component links for a S3RESTRequest

        @param tabs: the tabs as list of tuples (title, component_name, vars),
            where vars is optional
        @param paging: add paging buttons previous/next to the tabs
    """

    rheader_tabs = S3ComponentTabs(tabs)
    return rheader_tabs.render(r)

# =============================================================================
class S3ComponentTabs:

    def __init__(self, tabs=[]):

        self.tabs = [S3ComponentTab(t) for t in tabs]

    # -------------------------------------------------------------------------
    def render(self, r):

        rheader_tabs = []

        tablist = []

        tabs = [t for t in self.tabs if t.active(r)]

        # Check whether there is a tab for this resource method (no component)
        mtab = r.component is None and \
               [t.component for t in tabs if t.component == r.method] and True or False

        record_id = r.id

        for i in xrange(len(tabs)):

            tab = tabs[i]
            title = tab.title
            component = tab.component

            vars_match = tab.vars_match(r)
            if vars_match:
                _vars = Storage(r.get_vars)
            else:
                _vars = Storage(tab.vars)
                if "viewing" in r.get_vars:
                    _vars.viewing = r.get_vars.viewing

            if i == len(tabs)-1:
                _class = "tab_last"
            else:
                _class = "tab_other"

            here = False
            if tab.function is None:
                if "viewing" in _vars:
                    tablename, record_id = _vars.viewing.split(".", 1)
                    function = tablename.split("_", 1)[1]
                else:
                    function = r.function
            else:
                function = tab.function
            if function == r.name or \
               (function == r.function and "viewing" in _vars):
                   here = r.method == component or not mtab
            if component:
                if r.component and r.component.alias == component and vars_match:
                    here = True
                elif r.custom_action and r.method == component:
                    here = True
                else:
                    here = False
            else:
                if r.component or not vars_match:
                    here = False
            if here:
                _class = "tab_here"

            if component:
                if record_id:
                    args = [record_id, component]
                else:
                    args = [component]
                if "viewing" in _vars:
                    del _vars["viewing"]
                _href = URL(function, args=args, vars=_vars)
            else:
                args = []
                if function != r.name:
                    if "viewing" not in _vars and r.id:
                        _vars.update(viewing="%s.%s" % (r.tablename, r.id))
                    elif not tab.component and not tab.function:
                        if "viewing" in _vars:
                            del _vars["viewing"]
                        args = [record_id]
                else:
                    if "viewing" not in _vars and record_id:
                        args = [record_id]
                _href = URL(function, args=args, vars=_vars)

            rheader_tabs.append(SPAN(A(tab.title, _href=_href), _class=_class))

        if rheader_tabs:
            rheader_tabs = DIV(rheader_tabs, _class="tabs")
        else:
            rheader_tabs = ""
        return rheader_tabs

# =============================================================================
class S3ComponentTab:

    def __init__(self, tab):

        title, component = tab[:2]
        if component and component.find("/") > 0:
            function, component = component.split("/", 1)
        else:
            function = None

        self.title = title

        if function:
            self.function = function
        else:
            self.function = None

        if component:
            self.component = component
        else:
            self.component = None

        if len(tab) > 2:
            self.vars = Storage(tab[2])
        else:
            self.vars = None

    # -------------------------------------------------------------------------
    def active(self, r):

        manager = current.manager
        model = manager.model

        resource = r.resource
        component = self.component
        if component:
            clist = model.get_components(resource.table, names=[component])
            if component in clist:
                return True
            handler = model.get_method(resource.prefix,
                                       resource.name,
                                       method=component)
            if handler is None:
                handler = r.get_handler(component)
            if handler is None:
                return component in ("create", "read", "update", "delete")
        return True

    # -------------------------------------------------------------------------
    def vars_match(self, r):

        get_vars = r.get_vars
        if self.vars is None:
            return True
        for k, v in self.vars.iteritems():
            if k in get_vars and get_vars.get(k) != v:
                return False
        return True

# END =========================================================================
