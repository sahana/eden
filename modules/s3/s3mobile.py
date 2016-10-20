# -*- coding: utf-8 -*-

""" S3 Mobile Forms API

    @copyright: 2016 (c) Sahana Software Foundation
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

    @todo: integrate S3XForms API
"""

__all__ = ("S3MobileFormList",
           "S3MobileForm",
           "S3MobileCRUD",
           )

import json

from gluon import *
from s3forms import S3SQLDefaultForm, S3SQLField
from s3rest import S3Method
from s3utils import s3_str

SEPARATORS = (",", ":")

# =============================================================================
class S3MobileFormList(object):
    """
        Form List Generator
    """

    def __init__(self):
        """
            Constructor
        """

        T = current.T
        s3db = current.s3db
        settings = current.deployment_settings

        formlist = []

        forms = settings.get_mobile_forms()
        if forms:
            keys = set()
            for item in forms:

                options = {}
                if isinstance(item, (tuple, list)):

                    if len(item) == 2:
                        title, tablename = item
                        if isinstance(tablename, dict):
                            tablename, options = title, tablename
                            title = None
                    elif len(item) == 3:
                        title, tablename, options = item
                    else:
                        continue
                else:
                    title, tablename = None, item

                # Make sure table exists
                table = s3db.table(tablename)
                if not table:
                    current.log.warning("Mobile forms: non-existent resource %s" % tablename)
                    continue

                # Determine controller and function
                c, f = tablename.split("_", 1)
                c = options.get("c") or c
                f = options.get("f") or f

                # Only expose if target module is enabled
                if not settings.has_module(c):
                    continue

                # Stringify URL query vars
                url_vars = options.get("vars")
                if url_vars:
                    items = []
                    for k in url_vars:
                        v = s3_str(url_vars[k])
                        url_vars[k] = v
                        items.append("%s=%s" % (k, v))
                    query = "&".join(sorted(items))
                else:
                    query = ""

                # Deduplicate by target URL
                key = (c, f, query)
                if key in keys:
                    continue
                keys.add(key)

                # Determine form title
                if title is None:
                    title = " ".join(w.capitalize() for w in f.split("_"))
                if isinstance(title, basestring):
                    title = T(title)

                # Append to form list
                url = {"c": c, "f": f}
                if url_vars:
                    url["v"] = url_vars
                formlist.append({"n": s3_str(title), "t": tablename, "r": url})

        self.formlist = formlist

    # -------------------------------------------------------------------------
    def json(self):
        """
            Serialize the form list as JSON (EdenMobile)

            @returns: a JSON string
        """

        return json.dumps(self.formlist, separators=SEPARATORS)

# =============================================================================
class S3MobileForm(object):
    """
        Mobile representation of an S3SQLForm
    """

    def __init__(self, resource, form=None):
        """
            Constructor

            @param resource: the S3Resource
            @param form: an S3SQLForm instance to override settings
        """

        self.resource = resource
        self._form = form

    # -------------------------------------------------------------------------
    @property
    def form(self):
        """
            The form configuration (lazy property), fallback cascade:
                1. the form specified in constructor
                2. "mobile_form" config
                3. "crud_form" config
                4. all readable fields

            @returns: an S3SQLForm instance
        """

        form = self._form
        if form is None:

            resource = self.resource
            form = resource.get_config("mobile_form")

            if form is None:
                form = resource.get_config("crud_form")

            if form is None:
                # Construct a custom form from all readable fields
                readable_fields = self.resource.readable_fields()
                fields = [field.name for field in readable_fields]
                form = S3SQLCustomForm(*fields)

            self._form = form

        return form

    # -------------------------------------------------------------------------
    def schema(self):
        """
            Convert the form configuration into an EdenMobile schema dict

            @returns: a JSON-serializable dict with the schema definition
        """

        form = self.form
        resource = self.resource

        schema = {}
        form_fields = []

        for element in form.elements:
            if isinstance(element, S3SQLField):

                # Resolve the selector
                rfield = resource.resolve_selector(element.selector)

                if rfield.tname == resource.tablename:

                    description = self.describe(rfield)
                    if description:
                        fname = rfield.fname
                        schema[fname] = description
                        form_fields.append(fname)
                else:
                    # Subtable field
                    # => skip until implemented @todo
                    continue
            else:
                # Inline component or other form element
                # => skip until implemented @todo
                continue

        if form_fields:
            schema["_form"] = form_fields

        return schema

    # -------------------------------------------------------------------------
    def describe(self, rfield):
        """
            Generate a description of a resource field (for mobile schemas)

            @param rfield: the S3ResourceField

            @returns: a JSON-serializable dict describing the field
        """

        field = rfield.field
        if not field:
            # Virtual field
            return None

        # Basic field description
        description = {"type": rfield.ftype,
                       "label": s3_str(field.label),
                       }

        # Field settings
        if field.notnull:
            description["notnull"] = True
        if not field.readable:
            description["readable"] = False
        if not field.writable:
            description["writable"] = False

        # @todo: options
        # @todo: minimum
        # @todo: maximum
        # @todo: default value
        # @todo: readable, writable
        # @todo: placeholder?
        # @todo: required

        return description

# =============================================================================
class S3MobileCRUD(S3Method):
    """
        Mobile Data Handler

        responds to GET /prefix/name/mdata.json     (Data download)
                    POST /prefix/name/mdata.json    (Data upload)
                    GET /prefix/name/mform.json     (Schema download)
                    GET /prefix/name/xform.xml      (XForms analogously, later...)
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        http = r.http
        method = r.method
        representation = r.representation

        output = {}

        if method == "mdata":

            if representation == "json":
                if http == "GET":
                    # Data download
                    # @todo: implement this
                    r.error(501, current.ERROR.NOT_IMPLEMENTED)

                elif http == "POST":
                    # Data upload
                    # @todo: implement this
                    r.error(501, current.ERROR.NOT_IMPLEMENTED)

                else:
                    r.error(405, current.ERROR.BAD_METHOD)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)

        elif method == "mform":

            if representation == "json":

                if http == "GET":
                    # Form download
                    output = self.mobile_form(r, **attr)
                else:
                    r.error(405, current.ERROR.BAD_METHOD)

            else:
                r.error(415, current.ERROR.BAD_FORMAT)

        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def mobile_form(self, r, **attr):
        """
            Get the schema definition (as JSON)

            @param r: the S3Request instance
            @param attr: controller attributes

            @returns: a JSON string
        """

        resource = r.resource

        form = S3MobileForm(resource)

        schema = form.schema()
        schema["_controller"] = r.controller
        schema["_function"] = r.function

        name = resource.tablename
        output = json.dumps({name: schema})

        current.response.headers = {"Content-Type": "application/json"}
        return output


# END =========================================================================
