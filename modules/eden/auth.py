# -*- coding: utf-8 -*-

""" Sahana Eden Auth Model

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

__all__ = ["S3AuthModel"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3AuthModel(S3Model):

    names = ["auth_organisation"]

    def model(self):

        T = current.T

        # =============================================================================
        # Domain table
        #
        # When users register their email address is checked against this list.
        # If the Domain matches, then they are automatically assigned to the
        # Organization.
        # If there is no Approvals email then the user is automatically approved.
        # If there is an Approvals email then the approval request goes to this
        # address
        # If a user registers for an Organization & the domain doesn't match (or
        # isn't listed) then the approver gets the request

        if current.deployment_settings.get_auth_registration_requests_organisation():
            ORG_HELP = T("If this field is populated then a user who specifies this Organization when signing up will be assigned as a Staff of this Organization unless their domain doesn't match the domain field.")
        else:
            ORG_HELP = T("If this field is populated then a user with the Domain specified will automatically be assigned as a Staff of this Organization")

        DOMAIN_HELP = T("If a user verifies that they own an Email Address with this domain, the Approver field is used to determine whether & by whom further approval is required.")
        APPROVER_HELP = T("The Email Address to which approval requests are sent (normally this would be a Group mail rather than an individual). If the field is blank then requests are approved automatically if the domain matches.")

        tablename = "auth_organisation"
        table = self.define_table(tablename,
                                  self.org_organisation_id(
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (current.messages.ORGANISATION,
                                                                      ORG_HELP))),
                                  Field("domain",
                                        label=T("Domain"),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Domain"),
                                                                      DOMAIN_HELP))),
                                  Field("approver",
                                        label=T("Approver"),
                                        requires=IS_NULL_OR(IS_EMAIL()),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Approver"),
                                                                      APPROVER_HELP))),
                                  s3_comments(),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()
       
# END =========================================================================
