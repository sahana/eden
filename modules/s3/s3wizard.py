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
from gluon.storage import Storage
from gluon.tools import redirect

from .s3forms import S3SQLDefaultForm
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

        wizard = r.resource.get_config("wizard") # Should be a sub-class of S3CrudWizard
        if not wizard:
            s3_redirect_default(r.url(method = ""))

        page = r.get_vars.get("page")
        if not page:
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

        _config = self._config
        resource = r.resource

        sqlform = _config("crud_form", S3SQLDefaultForm())

        record_id = r.id
        if record_id:
            update = True
        else:
            update = False

        # Component join
        link = None
        if r.component:
            record = r.record
            if not update:
                defaults = r.component.get_defaults(record)

            if resource.link is None:
                if not update:
                    # Apply component defaults
                    linked = resource.linked
                    ctable = linked.table if linked else table
                    for (k, v) in defaults.items():
                        ctable[k].default = v

                # Configure post-process for S3EmbeddedComponentWidget
                link = self._embed_component(resource, record=r.id)

                # Set default value for parent key (fkey)
                pkey = resource.pkey
                fkey = resource.fkey
                field = table[fkey]
                value = r.record[pkey]
                field.default = field.update = value

                # Add parent key to POST vars so that callbacks can see it
                if r.http == "POST":
                    r.post_vars.update({fkey: value})

                # Hide the parent link in component forms
                field.comment = None
                field.readable = False
                field.writable = False

            else:
                if not update:
                    # Apply component defaults
                    for (k, v) in defaults.items():
                        table[k].default = v

                # Configure post-process to add a link table entry
                link = Storage(resource = resource.link,
                               master = record,
                               )

        if update:
            # Update form
            if not _config("editable", True) or \
               not self._permitted("update"):
                r.unauthorised()
            record_id = self.record_id
            message = self.crud_string(self.tablename, "msg_record_modified")
            onvalidation = _config("update_onvalidation") or \
                           _config("onvalidation")
            onaccept = _config("update_onaccept") or \
                       _config("onaccept")
        else:
            # Create form
            if not _config("insertable", True) or \
               not self._permitted("create"):
                r.unauthorised()
            record_id = None
            message = self.crud_string(self.tablename, "msg_record_created")
            onvalidation = _config("create_onvalidation") or \
                           _config("onvalidation")
            onaccept = _config("create_onaccept") or \
                       _config("onaccept")

        s3 = current.response.s3
        settings = s3.crud
        s3.cancel = self.cancel or r.url(method = "")
        settings.submit_button = "Next" # or "Finish"
        #settings.custom_submit = [(name, label, _class)] # Back

        form = sqlform(request = self.request,
                       resource = resource,
                       record_id = self.record_id,
                       onvalidation = onvalidation,
                       onaccept = onaccept,
                       link = link,
                       message = message,
                       subheadings = _config("subheadings"),
                       format = r.representation,
                       )

        return form

    # -------------------------------------------------------------------------
    def header(self, r):
        """
            Provide a visual of how many steps there are & which step we are on

            Uses visual ideas from https://codepen.io/audreyfeldroy/pen/tvxAz
        """

        T = current.T

        current_page = r.get_vars.get("page")

        steps = []
        sappend = steps.append
        step = 1
        _next = None
        past = True
        for page in self.pages:
            if page["page"] == current_page:
                _class = "current"
                past = False
            elif past:
                _class = "past"
            else:
                _class = "future"
                if not _next:
                    get_vars = dict(r.get_vars)
                    get_vars.update(page = page["page"])
                    _next = r.url(vars = get_vars)
            sappend(LI(SPAN(STRONG(T("Step %d") % step)),
                       page["label"],
                       I(),
                       _class = _class,
                       ))
            step += 1

        self.next = _next # @ToDo: This needs to vary whether Back or Next selected!

        return UL(*steps,
                  _class = "steps",
                  )

# END =========================================================================
