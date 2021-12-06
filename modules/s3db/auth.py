# -*- coding: utf-8 -*-

""" Sahana Eden Auth Model

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

__all__ = ("AuthConsentModel",
           "AuthDomainApproverModel",
           "AuthMasterKeyModel",
           "AuthUserNotificationModel",
           "AuthUserTempModel",
           "auth_consent_option_hash_fields",
           "auth_Consent",
           "auth_UserRepresent",
           )

import datetime

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from ..s3dal import original_tablename
from ..s3layouts import S3PopupLink

# Read-only hash fields (enabled in controller if permissible)
auth_consent_option_hash_fields = ("name", "description")

# =============================================================================
class AuthConsentModel(S3Model):
    """
        Model to track consent, e.g. to legitimise processing of personal
        data under GDPR rules.
    """

    names = ("auth_processing_type",
             "auth_consent_option",
             "auth_consent",
             "auth_consent_assertion",
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
                           label = T("Code"),
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
                           label = T("Description"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table configuration
        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("code",),
                                                 secondary = ("name",),
                                                 ),
                       )

        # Representation
        type_represent = S3Represent(lookup = tablename)

        # CRUD Strings
        ADD_TYPE = T("Create Processing Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
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
                           label = T("Processing Type"),
                           represent = type_represent,
                           requires = IS_ONE_OF(db, "auth_processing_type.id",
                                                type_represent,
                                                ),
                           ondelete = "RESTRICT",
                           comment = S3PopupLink(c = "admin",
                                                 f = "processing_type",
                                                 title = ADD_TYPE,
                                                 tooltip = T("Choose a type from the drop-down, or click the link to create a new type"),
                                                 vars = {"parent": "consent_option",
                                                         "child": "type_id",
                                                         },
                                                 ),
                           ),
                     Field("name",
                           label = T("Short Description"),
                           requires = IS_NOT_EMPTY(),
                           writable = False,
                           ),
                     Field("description", "text",
                           label = T("Explanations"),
                           represent = s3_text_represent,
                           writable = False,
                           ),
                     s3_date("valid_from",
                             label = T("Valid From"),
                             default = "now",
                             ),
                     s3_date("valid_until",
                             # Automatically set onaccept
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
                     Field("validity_period", "integer",
                           default = None,
                           label = T("Consent valid for (days)"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1, None)),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Period of Validity"),
                                                             T("Consent to this option expires after this many days"),
                                                             ),
                                         ),
                           ),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Obsolete"),
                                                             T("This description of the data processing is obsolete"),
                                                             ),
                                         ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # List fields
        list_fields = ["id",
                       "type_id",
                       "name",
                       "valid_from",
                       "obsolete",
                       ]

        # Table Configuration
        self.configure(tablename,
                       # NB must not deduplicate! (invalid operation + breaks vhash chain)
                       list_fields = list_fields,
                       onaccept = self.consent_option_onaccept,
                       )

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
                     Field("option_id", "reference auth_consent_option",
                           ondelete = "RESTRICT",
                           represent = S3Represent(lookup = "auth_consent_option"),
                           ),
                     Field("consenting", "boolean",
                           default = False,
                           ),
                     s3_date(default = "now",
                             ),
                     s3_date("expires_on"),
                     *s3_meta_fields())

        # Table Configuration
        self.configure(tablename,
                       onaccept = self.consent_onaccept,
                       )

        # ---------------------------------------------------------------------
        # Consent Assertion
        # - when a local user asserts that a non-local entity has consented
        #   to a transaction (e.g. a person who is not registered locally)
        # - differs from auth_consent in that it assigns liability to obtain
        #   consent rather than being proof of consent itself
        # - the respective consent option should therefore be worded as
        #   testimony - not as declaration - of consent
        #
        tablename = "auth_consent_assertion"
        define_table(tablename,
                     self.pr_person_id(), # the person asserting consent
                     Field("context", "text"),
                     Field("option_id", "reference auth_consent_option",
                           ondelete = "RESTRICT",
                           represent = S3Represent(lookup = "auth_consent_option"),
                           ),
                     Field("consented", "boolean",
                           default = False,
                           ),
                     s3_datetime(default = "now",
                                 ),
                     Field("vhash", "text"),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def consent_option_onaccept(form):
        """
            Onaccept-routine for consent options:
                - set valid_until date when obsolete (or otherwise remove it)
        """

        db = current.db
        s3db = current.s3db

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        # Retrieve record (id and obsolete)
        table = s3db.auth_consent_option
        row = db(table.id == record_id).select(table.id,
                                               table.obsolete,
                                               table.valid_until,
                                               limitby = (0, 1),
                                               ).first()
        if not row:
            return

        if row.obsolete:
            if not row.valid_until:
                row.update_record(valid_until = current.request.utcnow.date())
        else:
            row.update_record(valid_until = None)

    # -------------------------------------------------------------------------
    @staticmethod
    def consent_onaccept(form):
        """
            Onaccept-routine for consent:
                - automatically expire all previous consent to the same
                  processing type
        """

        db = current.db
        s3db = current.s3db

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        # Retrieve record
        ctable = s3db.auth_consent
        otable = s3db.auth_consent_option
        ttable = s3db.auth_processing_type

        join = [otable.on(otable.id == ctable.option_id),
                ttable.on(ttable.id == otable.type_id),
                ]
        query = (ctable.id == record_id)
        row = db(query).select(ctable.id,
                               ctable.person_id,
                               ttable.id,
                               join = join,
                               limitby = (0, 1)
                               ).first()
        if not row:
            return

        # Expire all previous consent records for the same
        # processing type and person
        today = current.request.utcnow.date()

        consent = row.auth_consent
        processing_type_id = row.auth_processing_type.id

        query = (ctable.person_id == consent.person_id) & \
                ((ctable.expires_on == None) | (ctable.expires_on > today)) & \
                (otable.id == ctable.option_id) & \
                (otable.type_id == processing_type_id) & \
                (ctable.id != consent.id) & \
                (ctable.deleted == False)
        rows = db(query).select(ctable.id)

        query = ctable.id.belongs(set(row.id for row in rows))
        db(query).update(expires_on = today)

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
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (current.messages.ORGANISATION,
                                                                  ORG_HELP,
                                                                  ),
                                              ),
                                ),
                          Field("domain",
                                label = T("Domain"),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Domain"),
                                                                  DOMAIN_HELP,
                                                                  ),
                                              ),
                                ),
                          Field("approver",
                                label = T("Approver"),
                                requires = IS_EMPTY_OR(IS_EMAIL()),
                                comment = DIV(_class = "tooltip",
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
        return None

# =============================================================================
class AuthMasterKeyModel(S3Model):
    """
        Model to store Master Keys
        - used for Authentication from Mobile App to e.g. Surveys
    """

    names = ("auth_masterkey",
             "auth_masterkey_id",
             "auth_masterkey_token",
             )

    def model(self):

        #T = current.T
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Master Keys
        #
        tablename = "auth_masterkey"
        define_table(tablename,
                     Field("name", length=254, unique=True,
                           #label = T("Master Key"),
                           requires = IS_LENGTH(254),
                           ),
                     # Which 'dummy' user this master key links to:
                     Field("user_id", current.auth.settings.table_user),
                     *s3_meta_fields())

        represent = S3Represent(lookup = tablename)

        masterkey_id = S3ReusableField("masterkey_id", "reference %s" % tablename,
                                       #label = T("Master Key"),
                                       ondelete = "CASCADE",
                                       represent = represent,
                                       requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(current.db, "auth_masterkey.id",
                                                              represent,
                                                              )),
                                       )

        # ---------------------------------------------------------------------
        # Single-use tokens for master key authentication
        #
        tablename = "auth_masterkey_token"
        define_table(tablename,
                     Field("token", length=64, unique=True),
                     s3_datetime("expires_on"),
                     )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"auth_masterkey_id": masterkey_id,
                }

# =============================================================================
class AuthUserNotificationModel(S3Model):
    """ Model for System Notifications """

    names = ("auth_user_notification",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # System Notifications
        #
        tablename = "auth_user_notification"
        self.define_table(tablename,
                          Field("user_id", current.auth.settings.table_user),
                          # Text to present to the User
                          Field("name"),
                          # Link to allow the User to handle it
                          Field("url",
                                requires = IS_EMPTY_OR(IS_URL()),
                                ),
                          #Field("priority"),
                          # Way of being able to remove the Notification if it gets handled:
                          Field("type"),
                          Field("tablename"),
                          Field("record_id", "integer"),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return None

# =============================================================================
class AuthUserTempModel(S3Model):
    """
        Model to store complementary data for pending user accounts
        after self-registration
    """

    names = ("auth_user_temp",
             )

    def model(self):

        utable = current.auth.settings.table_user

        # ---------------------------------------------------------------------
        # Temporary User Table
        # - interim storage of registration data that can be used to
        #   create complementary records about a user once their account
        #   is approved
        #
        self.define_table("auth_user_temp",
                          Field("user_id", utable),
                          Field("home"),
                          Field("mobile"),
                          Field("image", "upload",
                                length = current.MAX_FILENAME_LENGTH,
                                ),
                          Field("consent"),
                          Field("custom", "json",
                                requires = IS_EMPTY_OR(IS_JSONS3()),
                                ),
                          S3MetaFields.uuid(),
                          S3MetaFields.created_on(),
                          S3MetaFields.modified_on(),
                          )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

# =============================================================================
class auth_Consent:
    """ Helper class to track consent """

    def __init__(self, processing_types=None):
        """
            Args:
                processing_types: the processing types (default: all types
                                  for which there is a valid consent option)
        """

        self.processing_types = processing_types

    # -------------------------------------------------------------------------
    def widget(self, field, value, **attributes):
        """
            Produce a form widget to request consent, for embedding of consent
            questions in other forms

            Args:
                field: the Field (to hold the response)
                value: the current or default value
                attributes: HTML attributes for the widget
        """

        T = current.T
        fieldname = field.name

        # Consent options to ask
        opts = self.extract()

        # Current consent status (from form)
        selected = self.parse(value)
        value = {}

        # Widget ID
        widget_id = attributes.get("_id")
        if not widget_id:
            widget_id = "%s-consent" % fieldname

        # The widget
        widget = DIV(_id = widget_id,
                     _class = "consent-widget",
                     )

        # Construct the consent options
        has_mandatory_opts = False
        if self.processing_types:
            # Preserve order
            items = ((k, opts[k]) for k in self.processing_types if k in opts)
        else:
            items = opts.items()
        for code, spec in items:

            # Title
            title = spec.get("name")
            if not title:
                continue

            # Current selected-status of this option
            status = selected.get(code)
            v = status[1] if status is not None else spec.get("default", False)

            # The question for this option
            question = LABEL(INPUT(_type="checkbox",
                                   _class = "consent-checkbox",
                                   value = v,
                                   data = {"code": code},
                                   ),
                             SPAN(title,
                                 _class = "consent-title",
                                 ),
                             _class = "consent-question",
                             )

            if spec.get("mandatory"):
                has_mandatory_opts = True
                question.append(SPAN("*", _class="req"))

            # The option
            option = DIV(question, _class="consent-option")

            # Optional explanation
            description = spec.get("description")
            if description:
                option.append(P(XML(description), _class="consent-explanation"))

            # Append to widget
            widget.append(option)

            # Add selected-status to hidden input
            # JSON format: {"code": [id, consenting]}
            value[code] = [spec.get("id"), v]

        # Mandatory options advice
        if has_mandatory_opts:
            widget.append(P("* %s" % T("Consent required"), _class="req_key"))

        # The hidden input
        hidden_input = INPUT(_type = "hidden",
                             _name = attributes.get("_name", fieldname),
                             _id = "%s-response" % widget_id,
                             _value = json.dumps(value),
                             requires = self.validate,
                             )
        widget.append(hidden_input)

        # Inject client-side script and instantiate UI widget
        self.inject_script(widget_id, {})

        return widget

    # -------------------------------------------------------------------------
    def extract(self):
        """ Extract the current consent options """

        db = current.db
        s3db = current.s3db

        ttable = s3db.auth_processing_type
        otable = s3db.auth_consent_option

        left = ttable.on((ttable.id == otable.type_id) & \
                         (ttable.deleted == False))
        today = current.request.utcnow.date()
        query = (otable.valid_from <= today) & \
                (otable.obsolete == False) & \
                (otable.deleted == False)
        if self.processing_types:
            query = (ttable.code.belongs(self.processing_types)) & query

        rows = db(query).select(otable.id,
                                ttable.code,
                                otable.name,
                                otable.description,
                                otable.opt_out,
                                otable.mandatory,
                                left = left,
                                orderby = (~otable.valid_from, ~otable.created_on),
                                )
        options = {}
        for row in rows:
            code = row.auth_processing_type.code
            if code in options:
                continue
            option = row.auth_consent_option
            options[code] = {"id": option.id,
                             "name": option.name,
                             "description": option.description,
                             "default": True if option.opt_out else False,
                             "mandatory": option.mandatory,
                             }
        return options

    # -------------------------------------------------------------------------
    @classmethod
    def parse(cls, value):
        """
            Parse the JSON string returned by the widget

            Args:
                value: the JSON string

            Returns:
                dict with consent question responses,
                format {code: [id, consenting], ...}
        """

        parsed = {}
        if value is not None:
            try:
                parsed = json.loads(value)
            except JSONERRORS:
                pass
        return parsed

    # -------------------------------------------------------------------------
    @classmethod
    def validate(cls, value, record_id=None):
        """
            Validate a consent response (for use with Field.requires)

            Args:
                value: the value returned from the widget
        """

        T = current.T
        invalid = T("Invalid value")

        error = None
        parsed = cls.parse(value)
        if not parsed or not isinstance(parsed, dict):
            error = invalid
        else:
            try:
                option_ids = {v[0] for v in parsed.values()}
            except (TypeError, IndexError):
                error = invalid
            else:
                # Retrieve the relevant consent options
                s3db = current.s3db
                ttable = s3db.auth_processing_type
                otable = s3db.auth_consent_option
                join = ttable.on(ttable.id == otable.type_id)
                query = otable.id.belongs(option_ids)
                rows = current.db(query).select(otable.id,
                                                otable.obsolete,
                                                otable.mandatory,
                                                ttable.code,
                                                join = join,
                                                )
                options = {}
                for row in rows:
                    processing = row.auth_processing_type
                    option = row.auth_consent_option
                    options[option.id] = (processing.code, option.obsolete, option.mandatory)

                # Validate each response
                for code, spec in parsed.items():
                    option_id, consenting = spec
                    option = options.get(option_id)

                    if not option or option[0] != code:
                        # Option does not exist or does not match the code
                        error = invalid
                        break
                    if option[1]:
                        # Option is obsolete
                        error = T("Obsolete option: %(code)s") % {"code": code}
                        break
                    if option[2] and not consenting:
                        # Required consent has not been given
                        error = T("Required consent not given")
                        break

        return (None, error) if error else (value, None)

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(widget_id, options):
        """
            Inject static JS and instantiate client-side UI widget

            Args:
                widget_id: the widget ID
                options: JSON-serializable dict with UI widget options
        """

        request = current.request
        s3 = current.response.s3

        # Static script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.consent.js" % \
                     request.application
        else:
            script = "/%s/static/scripts/S3/s3.ui.consent.min.js" % \
                     request.application
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)

        # Widget options
        opts = {}
        if options:
            opts.update(options)

        # Widget instantiation
        script = '''$('#%(widget_id)s').consentQuestion(%(options)s)''' % \
                 {"widget_id": widget_id,
                  "options": json.dumps(opts),
                  }
        jquery_ready = s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

    # -------------------------------------------------------------------------
    @classmethod
    def track(cls, person_id, value, timestmp=None, allow_obsolete=True):
        """
            Record response to consent question

            Args:
                person_id: the person consenting
                value: the value returned from the widget
                timestmp: the date/time when the consent was given
                allow_obsolete: allow tracking of obsolete consent options
        """

        db = current.db
        s3db = current.s3db
        request = current.request

        today = timestmp.date() if timestmp else request.utcnow.date()
        vsign = request.env.remote_addr

        # Parse the value
        parsed = cls.parse(value)

        # Get all current+valid options matching the codes
        ttable = s3db.auth_processing_type
        otable = s3db.auth_consent_option

        option_fields = {"id", "validity_period"} | set(auth_consent_option_hash_fields)
        fields = [ttable.code] + [otable[fn] for fn in option_fields]

        join = ttable.on(ttable.id == otable.type_id)
        query = (ttable.code.belongs(set(parsed.keys()))) & \
                (otable.deleted == False)
        if not allow_obsolete:
            query &= (otable.obsolete == False)
        rows = db(query).select(join=join, *fields)

        valid_options = {}
        for row in rows:
            option = row.auth_consent_option
            context = [(fn, option[fn]) for fn in auth_consent_option_hash_fields]
            valid_options[option.id] = {"code": row.auth_processing_type.code,
                                        "hash": cls.get_hash(context),
                                        "valid_for": option.validity_period,
                                        }

        ctable = s3db.auth_consent
        record_ids = []
        for code, response in parsed.items():

            option_id, consenting = response

            # Verify option_id
            option = valid_options.get(option_id)
            if not option or option["code"] != code:
                raise ValueError("Invalid consent option: %s#%s" % (code, option_id))

            consent = (("date", today.isoformat()),
                       ("option_id", option_id),
                       ("person_id", person_id),
                       ("vsign", vsign),
                       ("consenting", consenting),
                       ("ohash", option["hash"]),
                       )

            # Store the hash for future verification
            consent = dict(consent[:5])
            consent["vhash"] = cls.get_hash(consent)

            # Update data
            consent["date"] = today
            valid_for = option["valid_for"]
            if valid_for:
                consent["expires_on"] = today + datetime.timedelta(days=valid_for)

            # Create new consent record
            record_id = ctable.insert(**consent)
            if record_id:
                consent["id"] = record_id
                s3db.onaccept(ctable, consent)
                record_ids.append(record_id)

        return record_ids

    # -------------------------------------------------------------------------
    @classmethod
    def register_consent(cls, user_id):
        """
            Track consent responses given during user self-registration

            Args:
                user_id: the auth_user ID
        """

        db = current.db
        s3db = current.s3db

        ltable = s3db.pr_person_user
        ptable = s3db.pr_person

        # Look up the person ID
        join = ptable.on(ptable.pe_id == ltable.pe_id)
        person = db(ltable.user_id == user_id).select(ptable.id,
                                                      join = join,
                                                      limitby = (0, 1),
                                                      ).first()
        if person:
            person_id = person.id

            # Look up the consent response from temp user record
            ttable = s3db.auth_user_temp
            row = db(ttable.user_id == user_id).select(ttable.id,
                                                       ttable.consent,
                                                       ttable.created_on,
                                                       limitby = (0, 1),
                                                       ).first()
            if row and row.consent:
                # Track consent
                cls.track(person_id, row.consent,
                          timestmp = row.created_on,
                          )

                # Reset consent response in temp user record
                row.update_record(consent = None)

    # -------------------------------------------------------------------------
    @classmethod
    def assert_consent(cls,
                       context,
                       code,
                       value,
                       person_id = None,
                       timestmp = None,
                       allow_obsolete = False,
                       ):
        """
            Assert consent of a non-local entity

            Args:
                context: string specifying the transaction to which
                         consent was to be obtained
                code: the processing type code
                value: the value returned from the consent widget
                person_id: the person asserting consent (defaults to
                           the current user)
                timestmp: datetime when consent was obtained (defaults
                          to current time)
                allow_obsolete: allow recording assertions for obsolete
                                consent options

            Returns:
                the consent assertion record ID

            Raises:
                TypeError: for invalid parameter types
                ValueError: for invalid input data                   
        """

        if not context:
            raise ValueError("Context is required")
        context = str(context)

        now = current.request.utcnow
        if not timestmp:
            timestmp = now
        elif not isinstance(timestmp, datetime.datetime):
            raise TypeError("Invalid timestmp type, expected datetime but got %s" % type(timestmp))
        elif timestmp > now:
            raise ValueError("Future timestmp not permitted")
        timestmp = timestmp.replace(microsecond = 0)

        if not person_id:
            person_id = current.auth.s3_logged_in_person()
        if not person_id:
            raise ValueError("Must be logged in or specify a person_id")

        # Parse the value and extract the option_id
        parsed = cls.parse(value)
        consent = parsed.get(code)
        if not consent:
            raise ValueError("Invalid JSON, or no response for processing type found")
        option_id, response = consent

        # Get all current+valid options matching the codes
        db = current.db
        s3db = current.s3db

        ttable = s3db.auth_processing_type
        otable = s3db.auth_consent_option

        option_fields = {"id"} | set(auth_consent_option_hash_fields)
        fields = [otable[fn] for fn in option_fields]

        join = ttable.on((ttable.id == otable.type_id) & \
                         (ttable.code == code))
        query = (otable.id == option_id) & \
                (otable.deleted == False)
        if not allow_obsolete:
            query &= (otable.obsolete == False)
        option = db(query).select(*fields,
                                  join = join,
                                  limitby = (0, 1),
                                  ).first()
        if not option:
            raise ValueError("Invalid consent option for processing type")

        ohash = cls.get_hash([(fn, option[fn]) for fn in auth_consent_option_hash_fields])
        consent = (("person_id", person_id),
                   ("context", context),
                   ("date", timestmp.isoformat()),
                   ("option_id", option.id),
                   ("consented", bool(response)),
                   ("ohash", ohash),
                   )
        # Generate verification hash
        vhash = cls.get_hash(consent)

        consent = dict(consent[:5])
        consent["vhash"] = vhash
        consent["date"] = timestmp

        atable = s3db.auth_consent_assertion
        record_id = atable.insert(**consent)
        if record_id:
            consent["id"] = record_id
            s3db.onaccept(atable, consent)

        return record_id

    # -------------------------------------------------------------------------
    @classmethod
    def verify(cls, record_id):
        """
            Verify a consent record (checks the hash, not expiry)

            Args:
                record_id: the consent record ID
        """

        db = current.db
        s3db = current.s3db

        # Load consent record and referenced option
        otable = s3db.auth_consent_option
        ctable = s3db.auth_consent

        join = otable.on(otable.id == ctable.option_id)
        query = (ctable.id == record_id) & (ctable.deleted == False)

        fields = [otable.id,
                  ctable.date,
                  ctable.person_id,
                  ctable.option_id,
                  ctable.vsign,
                  ctable.vhash,
                  ctable.consenting,
                  ] + [otable[fn] for fn in auth_consent_option_hash_fields]

        row = db(query).select(join = join,
                               limitby = (0, 1),
                               *fields
                               ).first()
        if not row:
            return False

        option = row.auth_consent_option
        context =[(fn, option[fn]) for fn in auth_consent_option_hash_fields]

        consent = row.auth_consent
        verify = (("date", consent.date.isoformat()),
                  ("option_id", consent.option_id),
                  ("person_id", consent.person_id),
                  ("vsign", consent.vsign),
                  ("consenting", consent.consenting),
                  ("ohash", cls.get_hash(context)),
                  )

        return consent.vhash == cls.get_hash(verify)

    # -------------------------------------------------------------------------
    @staticmethod
    def get_hash(data):
        """
            Produce a hash for JSON-serializable data

            Args:
                data: the JSON-serializable data (normally a dict)

            Returns:
                the hash as string
        """

        inp = json.dumps(data, separators=SEPARATORS)

        crypt = CRYPT(key = current.deployment_settings.hmac_key,
                      digest_alg = "sha512",
                      salt = False,
                      )
        return str(crypt(inp)[0])

    # -------------------------------------------------------------------------
    @staticmethod
    def get_consent_options(code):
        """
            Get all currently valid consent options for a processing type

            Args:
                code: the processing type code

            Returns:
                set of record IDs
        """

        s3db = current.s3db

        today = current.request.utcnow.date()

        ttable = s3db.auth_processing_type
        otable = s3db.auth_consent_option
        join = ttable.on((ttable.id == otable.type_id) & \
                         (ttable.deleted == False))
        query = (ttable.code == code) & \
                (otable.valid_from <= today) & \
                (otable.obsolete == False) & \
                (otable.deleted == False)
        rows = current.db(query).select(otable.id,
                                        join = join,
                                        )

        return set(row.id for row in rows)

    # -------------------------------------------------------------------------
    @classmethod
    def has_consented(cls, person_id, code):
        """
            Check valid+current consent for a particular processing type

            Args:
                person_id: the person to check consent for
                code: the data processing type code

            Returns:
                True|False whether or not the person has consented
                to this type of data processing and consent has not
                expired

            Example:
                consent = s3db.auth_Consent()
                if consent.has_consented(auth.s3_logged_in_person(), "PIDSHARE"):
                    # perform PIDSHARE...
        """

        # Get all current consent options for the code
        option_ids = cls.get_consent_options(code)
        if not option_ids:
            return False

        # Check if there is a positive consent record for this person
        # for any of these consent options that has not expired
        today = current.request.utcnow.date()

        ctable = current.s3db.auth_consent
        query = (ctable.person_id == person_id) & \
                (ctable.option_id.belongs(option_ids)) & \
                ((ctable.expires_on == None) | (ctable.expires_on > today)) & \
                (ctable.consenting == True) & \
                (ctable.deleted == False)
        row = current.db(query).select(ctable.id,
                                       limitby = (0, 1),
                                       ).first()

        return row is not None

    # -------------------------------------------------------------------------
    def pending_responses(self, person_id):
        """
            Identify all processing types for which a person has not
            responded to the updated consent questions, or where their
            previously given consent has expired

            Args:
                person_id: the person ID

            Returns:
                list of processing type codes
        """

        # Get all current consent options for the given processing types
        options = self.extract()
        option_ids = {spec["id"] for spec in options.values()}

        # Find all responses of this person to these options
        today = current.request.utcnow.date()
        ctable = current.s3db.auth_consent
        query = (ctable.person_id == person_id) & \
                (ctable.option_id.belongs(option_ids)) & \
                ((ctable.consenting == False) | \
                 (ctable.expires_on == None) | \
                 (ctable.expires_on > today)) & \
                (ctable.deleted == False)
        rows = current.db(query).select(ctable.option_id)

        # Identify any pending responses
        responded = {row.option_id for row in rows}
        pending = []
        for code, spec in options.items():
            if spec["id"] not in responded:
                pending.append(code)

        return pending

    # -------------------------------------------------------------------------
    @classmethod
    def consent_query(cls, table, code, field=None):
        """
            Get a query for table for records where the person identified
            by field has consented to a certain type of data processing.

            - useful to limit background processing that requires consent

            Args:
                table: the table to query
                code: the processing type code to check
                field: the field in the table referencing pr_person.id

            Returns:
                Query

            Example:
                consent = s3db.auth_Consent()
                query = consent.consent_query(table, "PIDSHARE") & (table.deleted == False)
                # Perform PIDSHARE with query result...
                rows = db(query).select(*fields)
        """

        if field is None:
            if original_tablename(table) == "pr_person":
                field = table.id
            else:
                field = table.person_id
        elif isinstance(field, str):
            field = table[field]

        option_ids = cls.get_consent_options(code)
        today = current.request.utcnow.date()

        ctable = current.s3db.auth_consent
        query = (ctable.person_id == field) & \
                (ctable.option_id.belongs(option_ids)) & \
                ((ctable.expires_on == None) | (ctable.expires_on > today)) & \
                (ctable.consenting == True) & \
                (ctable.deleted == False)

        return query

    # -------------------------------------------------------------------------
    @classmethod
    def consent_filter(cls, code, selector=None):
        """
            Filter resource for records where the person identified by
            selector has consented to a certain type of data processing.

            - useful to limit REST methods that require consent

            Args:
                code: the processing type code to check
                selector: a field selector (string) that references
                          pr_person.id; if not specified pr_person is
                          assumed to be the master resource

            Returns:
                S3ResourceQuery

            Example:
                consent = s3db.auth_Consent()
                resource.add_filter(consent.consent_filter("PIDSHARE", "~.person_id"))

            Note:
                only one consent filter can be used for the same resource;
                if multiple consent options must be checked and/or multiple
                person_id references apply independently, then either aliased
                auth_consent components can be used to construct a filter, or
                the query must be split (the latter typically performs better).
                Ideally, however, the consent decision for a single operation
                should not be complex or second-guessing.
        """

        option_ids = cls.get_consent_options(code)
        today = current.request.utcnow.date()

        # Construct sub-selectors
        if selector and selector not in ("id", "~.id"):
            consent = "%s$person_id:auth_consent" % selector
        else:
            # Assume pr_person is master
            consent = "person_id:auth_consent"
        option_id = FS("%s.option_id" % consent)
        expires_on = FS("%s.expires_on" % consent)
        consenting = FS("%s.consenting" % consent)

        query = (option_id.belongs(option_ids)) & \
                ((expires_on == None) | (expires_on > today)) & \
                (consenting == True)

        return query

# =============================================================================
class auth_UserRepresent(S3Represent):
    """
        Representation of User IDs to include 1 or more of
            * Name
            * Phone Number
            * Email address
        using the highest-priority contact info available (and permitted)
    """

    def __init__(self,
                 labels = None,
                 linkto = None,
                 show_name = True,
                 show_email = True,
                 show_phone = False,
                 show_org = False,
                 access = None,
                 show_link = True,
                 ):
        """
            Constructor

            @param labels: callable to render the name part
                           (defaults to s3_fullname)
            @param linkto: a URL (as string) to link representations to,
                           with "[id]" as placeholder for the key
                           (defaults see pr_PersonRepresent)

            @param show_name: include name in representation
            @param show_email: include email address in representation
            @param show_phone: include phone number in representation

            @param access: access level for contact details,
                           None = ignore access level
                           1 = show private only
                           2 = show public only

            @param show_link: render as HTML hyperlink
        """

        if labels is None:
            labels = s3_fullname

        super(auth_UserRepresent, self).__init__(lookup = "auth_user",
                                                 fields = ["id"],
                                                 labels = labels,
                                                 linkto = linkto,
                                                 show_link = show_link,
                                                 )

        self.show_name = show_name
        self.show_email = show_email
        self.show_phone = show_phone
        self.show_org = show_org
        self.access = access

        self._phone = {}

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        if self.show_name:
            repr_str = self.labels(row.get("pr_person"))
            if repr_str == "":
                # Fallback to using auth_user name
                # (Need to extra elements as otherwise the pr_person LazySet in the row is queried by s3_fullname)
                user_row = row.get("auth_user")
                repr_str = self.labels(Storage(first_name = user_row.first_name,
                                               last_name = user_row.last_name,
                                               ))
        else:
            repr_str = ""

        if self.show_org:
            organisation_id = row.get("auth_user.organisation_id")
            if organisation_id:
                org = current.s3db.org_OrganisationRepresent()(organisation_id)
                repr_str = "%s (%s)" % (repr_str, org)

        if self.show_email:
            email = row.get("auth_user.email")
            if email:
                if repr_str:
                    repr_str = "%s <%s>" % (repr_str, email)
                else:
                    repr_str = email

        if self.show_phone:
            phone = self._phone.get(row.get("pr_person.pe_id"))
            if phone:
                repr_str = "%s %s" % (repr_str, s3_phone_represent(phone))

        return repr_str

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        # Lookup pe_ids and name fields
        db = current.db
        s3db = current.s3db

        table = self.table

        show_name = self.show_name
        show_phone = self.show_phone

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        if show_name or show_phone:
            ptable = s3db.pr_person
            ltable = s3db.pr_person_user
            left = [ltable.on(table.id == ltable.user_id),
                    ptable.on(ltable.pe_id == ptable.pe_id),
                    ]
        else:
            left = None

        fields = [table.id]
        if self.show_email:
            fields.append(table.email)
        if show_phone:
            fields.append(ptable.pe_id)
        if self.show_org:
            fields.append(table.organisation_id)
        if show_name:
            fields += [table.first_name,
                       table.last_name,
                       ptable.first_name,
                       ptable.middle_name,
                       ptable.last_name,
                       ]

        rows = db(query).select(*fields,
                                left = left,
                                limitby = (0, count)
                                )
        self.queries += 1

        if show_phone:
            lookup_phone = set()
            phone = self._phone
            for row in rows:
                pe_id = row["pr_person.pe_id"]
                if pe_id not in phone:
                    lookup_phone.add(pe_id)

            if lookup_phone:
                ctable = s3db.pr_contact
                base = current.auth.s3_accessible_query("read", ctable)
                query = base & \
                          (ctable.pe_id.belongs(lookup_phone)) & \
                          (ctable.contact_method == "SMS") & \
                          (ctable.deleted == False)
                access = self.access
                if access:
                    query &= (ctable.access == access)
                contacts = db(query).select(ctable.pe_id,
                                            ctable.value,
                                            orderby = ctable.priority,
                                            )
                self.queries += 1
                for contact in contacts:
                    pe_id = contact.pe_id
                    if not phone.get(pe_id):
                        phone[pe_id] = contact.value

        return rows

# END =========================================================================
