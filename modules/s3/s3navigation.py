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

__all__ = ["S3Menu"]

from gluon import *

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
class MENUS3(DIV):

    """
        !! Unused, kept for temp reference !!

        S3 extensions of the gluon.html.MENU class

        Used to build modules menu
        Each list has 3 options: Name, Right & Link
        (NB In Web2Py's MENU, the 2nd option is 'Active')
        Right=True means that menu item floats right

        The Name option can be replaced by a dict to add features to the menu
        item. Currently only a checkbox is supported. The dict should contain:
        "name" -- label for the menu item
        "id" -- a unique id for the input field
        "value" -- True (checked) or False (unchecked)
        "request_type" -- "ajax" to send the link as an ajax call or
                          "load" to do a page load -- appropriate if checking the
                          box is supposed to change the page contents

        Optional arguments
            _class: defaults to 'S3menuInner'
            ul_main_class: defaults to 'S3menuUL'
            ul_sub_class: defaults to 'S3menuSub'
            li_class: defaults to 'S3menuLI'
            a_class: defaults to 'S3menuA'

        Example:
            menu = MENUS3([["name", False, URL(...), [submenu]], ...])
            {{=menu}}

        Example menu item for a checkbox:
            Ajax: See models/01_menu.py, look for "Rapid Data Entry"
            Load: See models/zzz_last.py, look for regions_menu

        @author: Fran Boon
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
                                _class=class_)
                else:
                    if (i == 0) and (self.attributes["_id"] == "modulenav"):
                        # 1st item, so display logo
                        in_ul = LI(DIV(A(SPAN(_class="S3menulogo"),
                                         _href=link),
                                       SPAN(A(name,
                                              _href=link,
                                              _class="S3menuHome")),
                                       _class="hoverable"),
                                   _class=class_)
                    else:
                        in_ul = LI(DIV(A(name, _href=link),
                                       _class="hoverable"),
                                   _class=class_)
                div.append(in_ul)
        else:
            # Submenu
            div = UL(_class="submenu")
            for item in data:
                (name, right, link) = item[:3]
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

# END =========================================================================
