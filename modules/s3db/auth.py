# -*- coding: utf-8 -*-

""" Sahana Eden Auth Model

    @copyright: 2009-2019 (c) Sahana Software Foundation
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

__all__ = ("AuthDomainApproverModel",
           "AuthUserOptionsModel",
           "AuthConsentModel",
           "auth_user_options_get_osm"
           )

from gluon import *
from gluon.storage import Storage

from ..s3 import *

# =============================================================================
class AuthDomainApproverModel(S3Model):

    names = ("auth_organisation",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Domain table:
        # When users register their email address is checked against this list.
        #   - If the Domain matches, then they are automatically assigned to the
        #     Organization.
        #   - If there is no Approvals email then the user is automatically approved.
        #   - If there is an Approvals email then the approval request goes to this
        #     address
        #   - If a user registers for an Organization & the domain doesn't match (or
        #     isn't listed) then the approver gets the request
        #
        if current.deployment_settings.get_auth_registration_requests_organisation():
            ORG_HELP = T("If this field is populated then a user who specifies this Organization when signing up will be assigned as a Staff of this Organization unless their domain doesn't match the domain field.")
        else:
            ORG_HELP = T("If this field is populated then a user with the Domain specified will automatically be assigned as a Staff of this Organization")

        DOMAIN_HELP = T("If a user verifies that they own an Email Address with this domain, the Approver field is used to determine whether & by whom further approval is required.")
        APPROVER_HELP = T("The Email Address to which approval requests are sent (normally this would be a Group mail rather than an individual). If the field is blank then requests are approved automatically if the domain matches.")

        tablename = "auth_organisation"
        self.define_table(tablename,
                          self.org_organisation_id(
                                comment=DIV(_class = "tooltip",
                                            _title = "%s|%s" % (current.messages.ORGANISATION,
                                                                ORG_HELP,
                                                                ),
                                            ),
                                ),
                          Field("domain",
                                label = T("Domain"),
                                comment=DIV(_class = "tooltip",
                                            _title = "%s|%s" % (T("Domain"),
                                                                DOMAIN_HELP,
                                                                ),
                                            ),
                                ),
                          Field("approver",
                                label = T("Approver"),
                                requires = IS_EMPTY_OR(IS_EMAIL()),
                                comment=DIV(_class = "tooltip",
                                            _title = "%s|%s" % (T("Approver"),
                                                                APPROVER_HELP,
                                                                ),
                                            ),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}


# =============================================================================
class AuthUserOptionsModel(S3Model):
    """ Model to store per-user configuration options """

    names = ("auth_user_options",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # User Options
        #
        OAUTH_KEY_HELP = "%s|%s|%s" % (T("OpenStreetMap OAuth Consumer Key"),
                                       T("In order to be able to edit OpenStreetMap data from within %(name_short)s, you need to register for an account on the OpenStreetMap server.") % \
                                            {"name_short": current.deployment_settings.get_system_name_short()},
                                       T("Go to %(url)s, sign up & then register your application. You can put any URL in & you only need to select the 'modify the map' permission.") % \
                                            {"url": A("http://www.openstreetmap.org",
                                                      _href="http://www.openstreetmap.org",
                                                      _target="blank",
                                                      ),
                                             },
                                       )

        self.define_table("auth_user_options",
                          self.super_link("pe_id", "pr_pentity"),
                          Field("user_id", current.auth.settings.table_user),
                          Field("osm_oauth_consumer_key",
                                label = T("OpenStreetMap OAuth Consumer Key"),
                                comment = DIV(_class="stickytip",
                                              _title=OAUTH_KEY_HELP,
                                              ),
                                ),
                          Field("osm_oauth_consumer_secret",
                                label = T("OpenStreetMap OAuth Consumer Secret"),
                                ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class AuthConsentModel(S3Model):
    """
        Model to track consent, e.g. to legitimise processing of personal
        data under GDPR rules.
    """

    names = ("auth_processing_type",
             "auth_consent_option",
             "auth_consent",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        define_table = self.define_table
        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Processing Types
        # - types of data processing consent is required for
        #
        tablename = "auth_processing_type"
        define_table(tablename,
                     Field("code", length=16, notnull=True, unique=True,
                           label = T("Type Code"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(16),
                                       IS_NOT_ONE_OF(db, "%s.code" % tablename),
                                       ],
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Type Code"),
                                                             T("A unique code to identify the type"),
                                                             ),
                                         ),
                           ),
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Representation
        type_represent = S3Represent(lookup=tablename)

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Processing Type"),
            title_display = T("Processing Type Details"),
            title_list = T("Processing Types"),
            title_update = T("Edit Processing Type"),
            label_list_button = T("List Processing Types"),
            label_delete_button = T("Delete Processing Type"),
            msg_record_created = T("Processing Type created"),
            msg_record_modified = T("Processing Type updated"),
            msg_record_deleted = T("Processing Type deleted"),
            msg_list_empty = T("No Processing Types currently defined"),
            )

        # ---------------------------------------------------------------------
        # Consent Option
        # - a description of the data processing consent is requested for
        # - multiple consecutive versions of a description for the same
        #   type of data processing can exist, but once a user has consented
        #   to a particular version of the description, it becomes a legal
        #   document that must not be changed or deleted
        #
        tablename = "auth_consent_option"
        define_table(tablename,
                     Field("type_id", "reference auth_processing_type",
                           represent = type_represent,
                           requires = IS_ONE_OF(db, "auth_processing_type.id",
                                                type_represent,
                                                ),
                           ),
                     Field("name",
                           label = T("Short Description"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("description", "text",
                           label = T("Explanations"),
                           represent = s3_text_represent,
                           ),
                     s3_date("valid_from",
                             label = T("Valid From"),
                             default = "now",
                             ),
                     s3_date("valid_until",
                             readable = False,
                             writable = False,
                             ),
                     Field("opt_out", "boolean",
                           default = False,
                           label = T("Preselected"),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Preselected"),
                                                             T("This option is preselected in consent question (explicit opt-out)"),
                                                             ),
                                         ),
                           ),
                     Field("mandatory", "boolean",
                           default = False,
                           label = T("Mandatory"),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Mandatory"),
                                                             T("This option is required for the consent question to succeed"),
                                                             ),
                                         ),
                           ),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Obsolete"),
                                                             T("This description of the data processing is obsolete"),
                                                             ),
                                         ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Consent Option"),
            title_display = T("Consent Option Details"),
            title_list = T("Consent Options"),
            title_update = T("Edit Consent Option"),
            label_list_button = T("List Consent Options"),
            label_delete_button = T("Delete Consent Option"),
            msg_record_created = T("Consent Option created"),
            msg_record_modified = T("Consent Option updated"),
            msg_record_deleted = T("Consent Option deleted"),
            msg_list_empty = T("No Consent Options currently defined"),
        )

        # ---------------------------------------------------------------------
        # Consent Question Responses
        #
        tablename = "auth_consent"
        define_table(tablename,
                     self.pr_person_id(),
                     Field("vsign"),
                     Field("vhash", "text"),
                     Field("option_id", "reference auth_consent_option.id",
                           ondelete = "RESTRICT",
                           ),
                     Field("consenting", "boolean",
                           default = False,
                           ),
                     s3_date(default = "now",
                             ),
                     s3_date("expires_on"),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
def auth_user_options_get_osm(pe_id):
    """
        Gets the OSM-related options for a pe_id
    """

    db = current.db
    table = current.s3db.auth_user_options
    query = (table.pe_id == pe_id)
    record = db(query).select(limitby=(0, 1)).first()
    if record:
        return record.osm_oauth_consumer_key, record.osm_oauth_consumer_secret
    else:
        return None

# END =========================================================================
