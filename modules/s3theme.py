# -*- coding: utf-8 -*-

""" S3 Theme Elements

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2013 (c) Sahana Software Foundation
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

from gluon.html import *

# =============================================================================
class NAV(DIV):
    """ <nav> element """

    tag = "nav"

# =============================================================================
class SECTION(DIV):
    """ <section> element """

    tag = "section"

# =============================================================================
def formstyle_default(form, fields, *args, **kwargs):
    """
        Default Eden Form Style (Labels above the Inputs)
    """

    def render_row(row_id, label, controls, comment, hidden=False):
        
        row = []
        _class = "hide" if hidden else None
            
        # Label on the 1st row
        row.append(TR(TD(label, _class = "w2p_fl"),
                      TD(""),
                      _id = row_id + "1",
                      _class = _class))
                      
        # Widget & Comment on the 2nd Row
        row.append(TR(controls,
                      TD(comment, _class = "w2p_fc"),
                      _id = row_id,
                      _class = _class))
                      
        return tuple(row)

    if args:
        # Old-style, single-row call:
        hidden = kwargs.get("hidden", False)
        return render_row(form, fields, args[0], args[1], hidden=hidden)
    else:
        # New-style, all-rows call:
        parent = TABLE()
        for row_id, label, controls, comment in fields:
            rows = render_row(row_id, label, controls, comment)
            parent.append(rows[0])
            parent.append(rows[1])
        return parent

# =============================================================================
def formstyle_default_inline(form, fields, *args, **kwargs):
    """
        Default Eden Form Style (In-Line Labels)
    """

    def render_row(row_id, label, controls, comment, hidden=False):

        _class = "hide" if hidden else None

        row = TR(TD(label, _class = "w2p_fl"),
                 TD(controls),
                 _id = row_id,
                 _class = _class)

        if comment:
            row.append(TD(DIV(_class = "tooltip",
                              _title = "%s|%s" % (label, comment)),
                          _class="w2p_fc"))
        return row

    if args:
        # Old-style, single-row call:
        hidden = kwargs.get("hidden", False)
        return render_row(form, fields, args[0], args[1], hidden=hidden)
    else:
        # New-style, all-rows call:
        parent = TABLE()
        for row_id, label, controls, comment in fields:
            row = render_row(row_id, label, controls, comment)
            parent.append(row)
        return parent

# =============================================================================
def formstyle_foundation(form, fields, *args, **kwargs):
    """
        Formstyle for foundation themes (Labels above Inputs)
    """

    def render_row(row_id, label, controls, helptext):
        if isinstance(controls, INPUT):
            if controls['_type'] == 'submit':
                controls['_class'] = 'small primary button'
        controls = DIV(label,
                       DIV(controls,
                           _class="controls",
                           ),
                       _class="small-6 columns",
                       )
        comment = DIV(helptext,
                      _class="small-6 columns",
                      )
        return DIV(controls, comment, _class="form-row row", _id=row_id)

    if args:
        row_id = form
        label = fields
        controls, helptext = args
        return render_row(row_id, label, controls, helptext)
    else:
        parent = TAG[""]()
        for row_id, label, controls, helptext in fields:
            parent.append(render_row(row_id, label, controls, helptext))
        return parent

# =============================================================================
def formstyle_foundation_inline(form, fields, *args, **kwargs):
    """
        Formstyle for foundation themes (In-Line Labels)
    """

    def render_row(row_id, label, controls, helptext):
        
        if isinstance(controls, INPUT):
            if controls['_type'] == 'submit':
                controls['_class'] = 'small primary button'

        if isinstance(label, LABEL):
            label.add_class("left inline")
                
        label_col = DIV(label, _class="small-2 columns")
        controls_col = DIV(controls, _class="small-6 columns")
        comments_col = DIV(helptext, _class="small-4 columns")

        return DIV(label_col, controls_col, comments_col, _class="form-row row", _id=row_id)

    if args:
        row_id = form
        label = fields
        controls, helptext = args
        return render_row(row_id, label, controls, helptext)
    else:
        parent = TAG[""]()
        for row_id, label, controls, helptext in fields:
            parent.append(render_row(row_id, label, controls, helptext))
        return parent

# END =========================================================================
