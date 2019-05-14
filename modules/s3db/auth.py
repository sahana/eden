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
           "auth_Consent",
           "auth_user_options_get_osm"
           )

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from ..s3layouts import S3PopupLink

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
             "auth_consent_option_hash_fields",
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

        # Representation
        type_represent = S3Represent(lookup=tablename)

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

        # Read-only hash fields (enabled in controller if permissible)
        hash_fields = ("name", "description")

        # List fields
        list_fields = ["id",
                       "type_id",
                       "name",
                       "valid_from",
                       "obsolete",
                       ]

        # Table Configuration
        self.configure(tablename,
                       list_fields = list_fields,
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
        return {"auth_consent_option_hash_fields": hash_fields,
                }

# =============================================================================
class auth_Consent(object):
    """ Helper class to track consent """

    def __init__(self, processing_types=None):
        """
            Constructor

            @param processing_types: the processing types (default: all types
                                     for which there is a valid consent option)
        """

        self.processing_types = processing_types

    # -------------------------------------------------------------------------
    def widget(self, field, value, **attributes):
        """
            Produce a form widget to request consent, for embedding of consent
            questions in other forms

            @param field: the Field (to hold the response)
            @param value: the current or default value
            @param attributes: HTML attributes for the widget
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
        for code, spec in opts.items():

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
                option.append(P(description, _class="consent-explanation"))

            # Append to widget
            widget.append(option)

            # Add selected-status to hidden input
            # JSON format: {"code": [id, consenting]}
            value[code] = [spec.get("id"), v]

        # Mandatory options advice
        if has_mandatory_opts:
            widget.append(P("* %s" % T("Consent required"), _class="req_key"))

        # The hidden input
        requires = field.requires
        hidden_input = INPUT(_type = "hidden",
                             _name = attributes.get("_name", fieldname),
                             _id = "%s-response" % widget_id,
                             _value = json.dumps(value),
                             requires = requires if requires else self.validate,
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

            @param value: the JSON string
            @returns: dict with consent question responses,
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
    def validate(cls, value):
        """
            Validate a consent response (for use with Field.requires)

            @param value: the value returned from the widget
        """

        # TODO verify mandatory options have been consented to
        #      - JSON format: {code:[id,consenting]}
        #      - Check that id matches type code
        #      - Check that consenting=true if mandatory

        return value, None

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(widget_id, options):
        """
            Inject static JS and instantiate client-side UI widget

            @param widget_id: the widget ID
            @param options: JSON-serializable dict with UI widget options
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
    def track(cls, person_id, value):
        """
            Record response to consent question

            @param person_id: the person consenting
            @param value: the value returned from the widget
        """

        db = current.db
        s3db = current.s3db
        request = current.request

        now = request.utcnow.date()
        vsign = request.env.remote_addr

        # Consent option hash fields
        hash_fields = s3db.auth_consent_option_hash_fields

        # Parse the value
        parsed = cls.parse(value)

        # Get all current+valid options matching the codes
        ttable = s3db.auth_processing_type
        otable = s3db.auth_consent_option
        ctable = s3db.auth_consent
        fields = [ttable.code, otable.id] + [otable[fn] for fn in hash_fields]
        left = ttable.on(ttable.id == otable.type_id)
        query = (ttable.code.belongs(parsed.keys())) & \
                (otable.obsolete == False) & \
                (otable.deleted == False)
        rows = db(query).select(left=left, *fields)
        valid_options = {}
        for row in rows:
            option = row.auth_consent_option
            context = {fn: option[fn] for fn in hash_fields}
            valid_options[option.id] = {"code": row.auth_processing_type.code,
                                        "hash": cls.get_hash(context),
                                        }

        record_ids = []
        for code, response in parsed.items():

            option_id, consenting = response

            # Verify option_id
            option = valid_options.get(option_id)
            if not option or option["code"] != code:
                raise ValueError("Invalid consent option: %s#%s" % (code, option_id))

            # Generate consent record
            consent = {"date": now.isoformat(),
                       "option_id": option_id,
                       "person_id": person_id,
                       "vsign": vsign,
                       "ohash": option["hash"],
                       "consenting": consenting,
                       }

            # Store the hash for future verification
            consent["vhash"] = cls.get_hash(consent)

            # Update data
            # TODO automatic expiry
            consent["date"] = now
            del consent["ohash"]

            # Save consent record
            record_id = ctable.insert(**consent)
            if record_id:
                record_ids.append(record_id)

        return record_ids

    # -------------------------------------------------------------------------
    @classmethod
    def verify(cls, record_id):
        """
            Verify a consent record (checks the hash, not expiry)

            @param record_id: the consent record ID
        """

        db = current.db
        s3db = current.s3db

        # Consent option hash fields
        hash_fields = s3db.auth_consent_option_hash_fields

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
                  ] + [otable[fn] for fn in hash_fields]

        row = db(query).select(join=join, limitby=(0, 1), *fields).first()
        if not row:
            return False

        option = row.auth_consent_option
        context = {fn: option[fn] for fn in hash_fields}

        consent = row.auth_consent
        verify = {"date": consent.date.isoformat(),
                  "option_id": consent.option_id,
                  "person_id": consent.person_id,
                  "vsign": consent.vsign,
                  "ohash": cls.get_hash(context),
                  "consenting": consent.consenting,
                  }

        return consent.vhash == cls.get_hash(verify)

    # -------------------------------------------------------------------------
    @staticmethod
    def get_hash(data):
        """
            Produce a hash for JSON-serializable data

            @param data: the JSON-serializable data (normally a dict)

            @returns: the hash as string
        """

        inp = json.dumps(data, separators=SEPARATORS)

        crypt = CRYPT(key = current.deployment_settings.hmac_key,
                      digest_alg = "sha512",
                      salt = False,
                      )
        return str(crypt(inp)[0])

    # -------------------------------------------------------------------------
    @classmethod
    def has_consented(cls, person_id, code):
        """
            Check valid+current consent for a particular processing type

            @param person_id: the person to check consent for
            @param code: the data processing type code

            @returns: True|False whether or not the person has consented
                      to this type of data processing and consent has not
                      expired

            @example:
                consent = s3db.auth_Consent()
                if consent.has_consented(auth.s3_logged_in_person(), "PIDSHARE"):
                    # perform PIDSHARE...
        """

        db = current.db
        s3db = current.s3db

        today = current.request.utcnow.date()

        ttable = s3db.auth_processing_type
        otable = s3db.auth_consent_option

        # Get all current consent options for the code
        join = ttable.on((ttable.id == otable.type_id) & \
                         (ttable.deleted == False))
        query = (ttable.code == code) & \
                (otable.valid_from <= today) & \
                (otable.obsolete == False) & \
                (otable.deleted == False)
        rows = db(query).select(otable.id, join=join)
        if not rows:
            return False

        ctable = s3db.auth_consent

        # Get the newest response to any of these options
        option_ids = set(row.id for row in rows)
        query = (ctable.person_id == person_id) & \
                (ctable.option_id.belongs(option_ids)) & \
                (ctable.deleted == False)
        row = db(query).select(ctable.consenting,
                               ctable.expires_on,
                               limitby = (0, 1),
                               orderby = ~ctable.date,
                               ).first()
        if not row:
            # No consent record at all
            return False

        # Result is positive if consent record was positive and has not expired
        expires = row.expires_on
        return row.consenting if expires is None or expires > today else False

    # -------------------------------------------------------------------------
    @staticmethod
    def consent_query(table, code, field=None):
        """
            Get a query for table for records where the person identified
            by field has consented to a certain type of data processing.

            - useful to limit background processing that requires consent
        """

        # TODO implement this
        pass

    # -------------------------------------------------------------------------
    @staticmethod
    def consent_filter(resource, selector, code):
        """
            Filter resource for records where the person identified by
            selector has consented to a certain type of data processing.

            - useful to limit REST methods that require consent
        """

        # TODO implement this
        pass

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
