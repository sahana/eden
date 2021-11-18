# -*- coding: utf-8 -*-

""" Resource Wizard Pages

    @copyright: 2013-2021 (c) Sahana Software Foundation
    @license: MIT

    @requires: U{B{I{gluon}} <http://web2py.com>}

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

from gluon import current
from gluon.html import *
from gluon.tools import redirect

from .s3rest import S3Method
from .s3utils import s3_redirect_default

__all__ = ("S3Wizard",
           "S3CrudWizard",
           )

# =============================================================================
class S3Wizard(S3Method):
    """ Resource Wizard Pages """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST interface

            @param r: the S3Request
            @param attr: controller attributes
        """

        wizard = r.resource.get_config("wizard")
        if not wizard:
            s3_redirect_default(r.url(method = ""))

        page = r.get_vars.get("page")
        if page == "cancel":
            # @ToDo: Do this directly, without a redirect
            url = wizard.cancel or r.url(method = "")
            redirect(url)
        elif not page:
            # Use the 1st page
            r.get_vars["page"] = wizard.pages[0]

        output = {"form": wizard.form(r),
                  "header": wizard.header(r),
                  }

        current.response.view = "wizard.html"

        return output

# =============================================================================
class S3CrudWizard:
    """
        Base Class

        Each Wizard should inherit from this & configure it's pages
    """

    # -------------------------------------------------------------------------
    def __init__(self):

        self.cancel = None # Page to go to upon 'Cancel'...defaults to List View for Resource
        self.pages = [#{"page": "recv", # visible to developers via r.get_vars, can be used by prep/customise
                      # "label": T("Basic info"), # visible to users via header
                      # },
                      ]

    # -------------------------------------------------------------------------
    def form(self, r):
        """
            Back/Next[|Finish]/Cancel buttons at bottom (Back/Next|Finish=Save, Cancel goes to list view for resource)
        """

        return FORM()

    # -------------------------------------------------------------------------
    def header(self, r):
        """
            Provide a visual of how many steps there are & which step we are on
        """

        # https://miro.medium.com/max/768/0*i6QpT_VgE352zKcH.jpg
        # |>>>    |
        # 'Step x' from the position in the list
        # label
        # highlight current step

        T = current.T

        current_page = r.get_vars.get("page")

        steps = []
        sappend = steps.append
        step = 1
        for page in self.pages:
            if page["page"] == current_page:
                _class = "active"
            sappend(DIV(DIV(T("Step %d") % step),
                        DIV(page["label"]),
                        ))
            step += 1

        return DIV(*steps)

# END =========================================================================
