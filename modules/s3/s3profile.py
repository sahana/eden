# -*- coding: utf-8 -*-

""" S3 Profile

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

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3crud import S3CRUD
from s3data import S3DataList

# =============================================================================
class S3Profile(S3CRUD):
    """ Interactive Method Handler for Profile Pages """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            API entry point

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        if r.http == "GET":
            if r.record:
                output = self.profile(r, **attr)
            else:
                # Redirect to the List View
                redirect(r.url(method=""))
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def profile(self, r, **attr):
        """
            Generate a Profile page

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        #T = current.T
        s3db = current.s3db
        tablename = self.tablename

        # Initialise Output
        output = dict(widgets=[])

        # Get the options
        widgets = s3db.get_config(tablename, "profile_widgets")
        if widgets:
            append = output["widgets"].append
        else:
            # @ToDo Some kind of 'Page not Configured'?
            widgets = []
        for widget in widgets:
            if widget == "map":
                append(self._map(r, **attr))
            elif widget == "comments":
                append(self._comments(r, **attr))
            else:
                # Resource (with Optional Filter)
                append(self._resource(r, widget, **attr))

        current.response.view = self._view(r, "profile.html")
        return output

    # -------------------------------------------------------------------------
    def _comments(self, r, **attr):
        """
            Generate a Comments widget

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        # Initialise Output
        output = DIV(_id="profile-comments")

        return output

    # -------------------------------------------------------------------------
    def _map(self, r, **attr):
        """
            Generate a Map widget

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        # Initialise Output
        output = DIV(_id="profile-map")

        return output

    # -------------------------------------------------------------------------
    def _resource(self, r, tablename, **attr):
        """
            Generate a Resource widget
            - defaults to a dataList

            @param r: the S3Request instance
            @param tablename: the table name
            @param attr: controller attributes for the request
        """

        # Can we automate filter through Tag to the primary resource?

        # Initialise Output
        output = DIV(_id="profile-list-%s" % tablename)

        return output

# END =========================================================================
