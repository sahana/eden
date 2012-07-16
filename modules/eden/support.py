# -*- coding: utf-8 -*-

""" Sahana Eden Support Requests

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3SupportModel"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3SupportModel(S3Model):
    """
        Support Requests

        @ToDo: Should project_task not be used for this instead?
               - we could even sync between the on-instance tickets &
                 a central ticketing system
    """

    names = ["support_req"]

    def model(self):

        T = current.T
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # -------------------------------------------------------------------------
        support_request_types = {
            1 : T("Bug"),
            2 : T("Feature Request")
        }
        support_status_opts = {
            1 : T("Open"),
            2 : T("Closed")
        }

        tablename = "support_req"
        table = self.define_table(tablename,
                                  Field("name", notnull=True,
                                        label=T("Short Description")),
                                  Field("type", "integer",
                                        label=T("Type"),
                                        requires=IS_IN_SET(support_request_types,
                                                           zero="%s..." % T("Please select")),
                                        represent=lambda opt: \
                                            support_request_types.get(opt,
                                                                      UNKNOWN_OPT)),
                                  Field("details", "text",
                                        label = T("Details"),
                                        comment = "%s%s" % (T("Please provide the URL of the page you are referring to, a description of what you expected to happen & what actually happened."),
                                                            T("If a ticket was issued then please provide the Ticket ID."))),
                                  Field("status", "integer",
                                        label=T("Status"),
                                        default=1,
                                        requires=IS_IN_SET(support_status_opts),
                                        represent=lambda opt: \
                                            support_status_opts.get(opt, UNKNOWN_OPT)),
                                  Field("actions", "text",
                                        label = T("Actions"),
                                        comment = T("Actions taken as a result of this request.")),
                                  *s3_meta_fields())

        # CRUD strings
        ADD_REQUEST = T("New Support Request")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_REQUEST,
            title_display = T("Request Details"),
            title_list = T("Support Requests"),
            title_update = T("Edit Request"),
            title_search = T("Search Support Requests"),
            subtitle_create = T("Add New Request"),
            label_list_button = T("List Support Requests"),
            label_create_button = ADD_REQUEST,
            label_delete_button = T("Delete Request"),
            msg_record_created = T("Request added"),
            msg_record_modified = T("Request updated"),
            msg_record_deleted = T("Request deleted"),
            msg_list_empty = T("No Support Requests currently registered"))

        # ---------------------------------------------------------------------
        return Storage()

# END =========================================================================
