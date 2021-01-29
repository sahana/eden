# -*- coding: utf-8 -*-

""" S3 Theme Elements

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("formstyle_bootstrap",
           "formstyle_foundation",
           "formstyle_foundation_2col",
           "formstyle_foundation_inline",
           "formstyle_table",
           "formstyle_table_inline",
           "FORMSTYLES",
           )

from gluon import CAT, DIV, FIELDSET, INPUT, LABEL, SELECT, \
                  TABLE, TAG, TD, TEXTAREA, TR
from gluon.languages import lazyT

from s3compat import basestring

# =============================================================================
class NAV(DIV):
    """ <nav> element """

    tag = "nav"

# =============================================================================
class SECTION(DIV):
    """ <section> element """

    tag = "section"

# =============================================================================
def formstyle_bootstrap(form, fields, *args, **kwargs):
    """
        Formstyle for Bootstrap 2.x themes: http://getbootstrap.com/2.3.2/
    """

    def render_row(row_id, label, controls, comment, hidden=False):
        # Based on web2py/gluon/sqhtml.py
        # wrappers
        _help = DIV(comment, _class="help-block")
        # embed _help into _controls
        _controls = DIV(controls, _help, _class="controls")
        # submit unflag by default
        _submit = False

        element = None
        if isinstance(controls, INPUT):
            controls.add_class("span4")
            element = controls
        elif hasattr(controls, "element"):
            element = controls.element("input")
        if element:
            if element["_type"] == "submit":
                # flag submit button
                _submit = True
                element["_class"] = "btn btn-primary"
            elif element["_type"] == "file":
                element["_class"] = "input-file"

        # For password fields, which are wrapped in a CAT object.
        if isinstance(controls, CAT) and isinstance(controls[0], INPUT):
            controls[0].add_class("span4")

        if isinstance(controls, SELECT):
            controls.add_class("span4")

        if isinstance(controls, TEXTAREA):
            controls.add_class("span4")

        if isinstance(label, LABEL):
            label["_class"] = "control-label"

        _class = "hide " if hidden else ""

        if _submit:
            # submit button has unwrapped label and controls, different class
            return DIV(label, controls, _class="%sform-actions" % _class, _id=row_id)
        else:
            # unwrapped label
            return DIV(label, _controls, _class="%scontrol-group" % _class, _id=row_id)

    if args:
        row_id = form
        label = fields
        widget, comment = args
        if comment:
            comment = DIV(_class = "tooltip",
                          _title = "%s|%s" % (label, comment))
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        form.add_class("form-horizontal")
        parent = FIELDSET()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# =============================================================================
def formstyle_foundation(form, fields, *args, **kwargs):
    """
        Formstyle for Foundation 5 themes: http://foundation.zurb.com
        - Labels above the Inputs
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        if hasattr(widget, "element"):
            submit = widget.element("input", _type="submit")
            if submit:
                submit.add_class("small primary button")

        _class = "form-row row hide" if hidden else "form-row row"
        hints = DIV(render_tooltip(label, comment), _class="inline-tooltip")
        controls = DIV(label,
                       DIV(widget, hints, _class="controls"),
                       _class="small-12 columns",
                       )
        return DIV(controls, _class=_class, _id=row_id)

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# =============================================================================
def formstyle_foundation_2col(form, fields, *args, **kwargs):
    """
        Formstyle for Foundation 5 themes: http://foundation.zurb.com
        - Labels beside the Inputs
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        # Inspect widget
        columns = None
        if hasattr(widget, "element"):
            # Check for widget columns width override
            attr = widget.element().attributes
            if "s3cols" in attr:
                columns = attr["s3cols"] or columns
            # Set additional CSS classes for submit button
            submit = widget.element("input", _type="submit")
            if submit:
                submit.add_class("small primary button")

        # Render tooltip
        hints = render_tooltip(label, comment)

        # Wrap the label
        if isinstance(label, LABEL):
            label.add_class("right inline")
        else:
            label = LABEL(label, _class="right inline")
        label = DIV(label, _class="small-2 columns")

        # Wrap the controls
        if columns is None:
            _columns = "small-10 columns"
        else:
            _columns = "small-%s columns end" % columns
        controls = DIV(widget, hints, _class=_columns)

        # Render the row
        _class = "form-row row"
        if hidden:
            _class = "%s hide" % _class
        return DIV(label, controls, _class=_class, _id=row_id)

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# =============================================================================
def formstyle_foundation_inline(form, fields, *args, **kwargs):
    """
        Formstyle for Foundation 5 themes (In-Line Labels)
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        if hasattr(widget, "element"):
            submit = widget.element("input", _type="submit")
            if submit:
                submit.add_class("small primary button")

        controls_width = "medium-12" if label is False else "medium-10"
        controls_col = DIV(widget, _class="%s columns controls" % controls_width)

        if label:
            if isinstance(label, LABEL):
                label.add_class("left inline")
            label_col = DIV(label, _class="medium-2 columns")
        else:
            if label is not False:
                controls_col.add_class("medium-offset-2")
            label_col = ""

        if comment:
            comment = render_tooltip(label,
                                     comment,
                                     _class="inline-tooltip tooltip",
                                     )
            if hasattr(comment, "add_class"):
                comment.add_class("inline-tooltip")
            controls_col.append(comment)

        _class = "form-row row hide" if hidden else "form-row row"
        return DIV(label_col, controls_col, _class=_class, _id=row_id)

    if args:
        row_id = form
        label = fields
        widget, comment = args
        hidden = kwargs.get("hidden", False)
        return render_row(row_id, label, widget, comment, hidden)
    else:
        parent = TAG[""]()
        for row_id, label, widget, comment in fields:
            parent.append(render_row(row_id, label, widget, comment))
        return parent

# =============================================================================
def formstyle_table(form, fields, *args, **kwargs):
    """
        Old Default Eden Form Style (TRs not DIVs, Labels above the Inputs)
        - still used by IFRC
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        row = []
        _class = "hide" if hidden else None

        # Label on the 1st row
        row.append(TR(TD(label, _class="w2p_fl"),
                      TD(""),
                      _id = row_id + "1",
                      _class=_class))

        # Widget & Comment on the 2nd Row
        row.append(TR(widget,
                      TD(comment, _class="w2p_fc"),
                      _id=row_id,
                      _class=_class))

        return tuple(row)

    if args:
        # Old-style, single-row call:
        hidden = kwargs.get("hidden", False)
        return render_row(form, fields, args[0], args[1], hidden=hidden)
    else:
        # New-style, all-rows call:
        parent = TABLE()
        for row_id, label, widget, comment in fields:
            rows = render_row(row_id, label, widget, comment)
            parent.append(rows[0])
            parent.append(rows[1])
        return parent

# =============================================================================
def formstyle_table_inline(form, fields, *args, **kwargs):
    """
        Old Default Eden Form Style (In-Line Labels)
        - still used by IFRC
    """

    def render_row(row_id, label, widget, comment, hidden=False):

        _class = "hide" if hidden else None

        row = TR(TD(label, _class="w2p_fl"),
                 TD(widget),
                 _id=row_id,
                 _class=_class)

        if comment:
            row.append(TD(DIV(_class="tooltip",
                              _title="%s|%s" % (label, comment)),
                          _class="w2p_fc"))
        return row

    if args:
        # Old-style, single-row call:
        hidden = kwargs.get("hidden", False)
        return render_row(form, fields, args[0], args[1], hidden=hidden)
    else:
        # New-style, all-rows call:
        parent = TABLE()
        for row_id, label, widget, comment in fields:
            row = render_row(row_id, label, widget, comment)
            parent.append(row)
        return parent

# =============================================================================
def render_tooltip(label, comment, _class="tooltip"):
    """ Render a tooltip for a form field """

    if not comment:
        tooltip = ""
    elif isinstance(comment, (lazyT, basestring)):
        if label is False:
            label = ""
        elif hasattr(label, "flatten"):
            label = label.flatten().strip("*")
        tooltip = DIV(_class = _class,
                      _title = "%s|%s" % (label, comment))
    else:
        tooltip = comment
    return tooltip

# =============================================================================
# All formstyles
#
FORMSTYLES = {"default": formstyle_foundation,
              "default_inline": formstyle_foundation_inline,
              "bootstrap": formstyle_bootstrap,
              "foundation": formstyle_foundation,
              "foundation_2col": formstyle_foundation_2col,
              "foundation_inline": formstyle_foundation_inline,
              "table": formstyle_table,
              "table_inline": formstyle_table_inline,
              }

# END =========================================================================
