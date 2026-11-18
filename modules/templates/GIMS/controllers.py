"""
    Custom Controllers for GIMS

    License: MIT
"""

import json

from gluon import Field, HTTP, SQLFORM, URL, current, redirect, \
                  CRYPT, IS_EMAIL, IS_EXPR, IS_NOT_EMPTY, IS_NOT_IN_DB, IS_LOWER, \
                  A, BR, DIV, H3, H4, I, INPUT, LI, TAG, UL, XML

from gluon.storage import Storage

from s3dal import filter_fields

from core import ConsentTracking, CustomController, ICON, s3_mark_required, s3_str

from templates.RLPPTM.notifications import formatmap

TEMPLATE = "GIMS"
THEME = "RLP"

# =============================================================================
class index(CustomController):
    """ Custom Home Page """


    def __call__(self):

        output = {}

        T = current.T
        s3db = current.s3db
        auth = current.auth

        settings = current.deployment_settings

        # Defaults
        login_form = None
        login_div = None
        announcements = None
        announcements_title = None

        roles = current.session.s3.roles
        sr = auth.get_system_roles()
        if sr.AUTHENTICATED in roles:
            # Logged-in user
            # => display announcements
            from s3db.cms import cms_Announcements
            announcements = cms_Announcements().html()
            if announcements:
                announcements_title = T("Announcements")
        else:
            # Anonymous user
            # => provide a login box
            login_div = DIV(H3(T("Login")))
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)

        # Homepage action buttons
        buttons = DIV(A(ICON("book"), T("Guides & Videos"),
                        _href = URL(c="default", f="help"),
                        _class="info button",
                        ),
                      _class="button-group stacked-for-small",
                      )

        output = {"login_div": login_div,
                  "login_form": login_form,
                  "announcements": announcements,
                  "announcements_title": announcements_title,
                  "intro": current.s3db.cms_get_content("HomepageIntro",
                                                        module = "default",
                                                        resource = "index",
                                                        cmsxml = True,
                                                        ),
                  "buttons": buttons,
                  }

        # Custom view and homepage styles
        self._view(settings.get_theme_layouts(), "index.html")

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def announcements_item(header=None, body=None, date=None, priority=""):
        """
            Layout for announcement items

            Args:
                header: the header text
                body: the body text
                date: the date of the entry
                priority: priority "important"|"critical"|""
        """

        box = DIV(_class="announcement-box announcement-%s" % priority)

        if date:
            box.append(DIV(DIV(date, _class="announcement-date"),
                           _class = "fright",
                           ))

        text = DIV(_class="announcement-text")
        if header:
            icons = {"important": "fa-exclamation-circle",
                     "critical": "fa-exclamation-triangle",
                     }
            icon = icons.get(priority)
            if icon:
                header = TAG[""](I(_class="fa %s announcement-icon" % icon),
                                 header,
                                 )
            text.append(DIV(header, _class="announcement-header"))
        if body:
            text.append(DIV(body, _class="announcement-body"))
        box.append(text)

        return LI(box)

# =============================================================================
class register_invited(CustomController):
    """ Custom Registration Page """

    def __call__(self):

        auth = current.auth

        # Redirect if already logged-in
        if auth.s3_logged_in():
            redirect(URL(c="default", f="index"))

        T = current.T

        settings = current.deployment_settings

        request = current.request
        response = current.response
        session = current.session

        # Get the registration key
        if len(request.args) > 1:
            key = request.args[-1]
            session.s3.invite_key = key
            redirect(URL(c="default", f="index", args = ["register_invited"]))
        else:
            key = session.s3.invite_key
        if not key:
            session.error = T("Missing registration key")
            redirect(URL(c="default", f="index"))

        # Page title and intro text
        title = T("Registration")

        # Get intro text from CMS
        db = current.db
        s3db = current.s3db

        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "auth") & \
                         (ltable.resource == "user") & \
                         (ltable.deleted == False))

        query = (ctable.name == "InvitedRegistrationIntro") & \
                (ctable.deleted == False)
        row = db(query).select(ctable.body,
                               join = join,
                               cache = s3db.cache,
                               limitby = (0, 1),
                               ).first()
        intro = row.body if row else None

        # Customise Auth Messages
        auth_settings = auth.settings
        auth_messages = auth.messages
        self.customise_auth_messages()

        # Form Fields
        formfields, required_fields = self.formfields()

        # Generate labels (and mark required fields in the process)
        labels, has_required = s3_mark_required(formfields,
                                                mark_required = required_fields,
                                                )
        response.s3.has_required = has_required

        # Form buttons
        REGISTER = T("Register")
        buttons = [INPUT(_type = "submit",
                         _value = REGISTER,
                         ),
                   # TODO cancel-button?
                   ]

        # Construct the form
        utable = auth_settings.table_user
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = utable._tablename,
                               record = None,
                               hidden = {"_next": auth.get_vars_next()},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = REGISTER,
                               delete_label = auth_messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Identify form for CSS & JS Validation
        form.add_class("auth_register")

        # Inject client-side Validation
        auth.s3_register_validation()

        if form.accepts(request.vars,
                        session,
                        formname = "register",
                        onvalidation = self.validate(key),
                        ):

            form_vars = form.vars

            # Get the account
            account = self.account(key, form_vars.code)
            account.update_record(**filter_fields(utable, form_vars, allow_id=False))

            del session.s3["invite_key"]

            # Post-process the new user record
            s3db.configure("auth_user",
                           register_onaccept = self.register_onaccept,
                           )

            # Store consent response (for approve_user to register it)
            consent = form_vars.consent
            if consent:
                ttable = s3db.auth_user_temp
                record  = {"user_id": account.id,
                           "consent": form_vars.consent
                           }
                ttable.insert(**record)

            # Approve and link user
            auth.s3_approve_user(account)

            # Send welcome email (custom)
            self.send_welcome_email(account)

            # Log them in
            user = Storage(filter_fields(utable, account, allow_id=True))
            auth.login_user(user)

            auth_messages = auth.messages
            auth.log_event(auth_messages.register_log, user)
            session.flash = auth_messages.registration_successful

            # TODO redirect to the org instead?
            redirect(URL(c="default", f="person"))

        elif form.errors:
            response.error = T("There are errors in the form, please check your input")

        # Custom View
        self._view(TEMPLATE, "register_invited.html")

        return {"title": title,
                "intro": intro,
                "form": form,
                }

    # -------------------------------------------------------------------------
    @classmethod
    def validate(cls, key):
        """
            Custom validation of registration form
            - check the registration code
            - check for duplicate email
        """

        T = current.T

        def register_onvalidation(form):

            code = form.vars.get("code")

            account = cls.account(key, code)
            if not account:
                form.errors["code"] = T("Invalid Registration Code")
                return

            email = form.vars.get("email")

            from gluon.validators import ValidationError
            auth = current.auth
            utable = auth.settings.table_user
            dbset = current.db(utable.id != account.id)
            requires = IS_NOT_IN_DB(dbset, "%s.email" % utable._tablename)
            try:
                requires.validate(email)
            except ValidationError:
                form.errors["email"] = auth.messages.duplicate_email
                return

            onvalidation = current.auth.settings.register_onvalidation
            if onvalidation:
                from gluon.tools import callback
                callback(onvalidation, form, tablename="auth_user")

        return register_onvalidation

    # -------------------------------------------------------------------------
    @staticmethod
    def register_onaccept(user_id):
        """
            Process Registration

            Args:
                user_id: the user ID
        """

        db = current.db
        s3db = current.s3db
        auth = current.auth

        assign_role = auth.s3_assign_role

        utable = auth.settings.table_user
        user = db(utable.id == user_id).select(utable.organisation_id,
                                               limitby = (0, 1),
                                               ).first()
        if not user:
            return

        # Look up the organisation
        otable = s3db.org_organisation
        gtable = s3db.org_group
        mtable = s3db.org_group_membership

        left = [gtable.on((mtable.organisation_id == otable.id) & \
                          (mtable.deleted == False) & \
                          (gtable.id == mtable.group_id)),
                ]
        query = (otable.id == user.organisation_id) & \
                (otable.deleted == False)
        row = db(query).select(otable.id,
                               otable.pe_id,
                               gtable.name,
                               left = left,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return

        pe_id = row.org_organisation.pe_id
        group_name = row.org_group.name

        from .config import DISTRICTS, AFAS
        from .customise.auth import update_commune_group_shelter_reader
        if group_name == DISTRICTS:
            # District user
            # => assign SHELTER_READER for district and corresponding communes
            assign_role(user_id, "SHELTER_READER", for_pe=pe_id)
            update_commune_group_shelter_reader(user_id)

        elif group_name == AFAS:
            # AfA-user
            # => assign AFA_MANAGER
            assign_role(user_id, "AFA_MANAGER", for_pe=pe_id)

        # All invited users:
        # => assign ORG_ADMIN and SHELTER_MANAGER
        assign_role(user_id, "ORG_ADMIN", for_pe=pe_id)
        assign_role(user_id, "SHELTER_MANAGER", for_pe=pe_id)

    # -------------------------------------------------------------------------
    @classmethod
    def send_welcome_email(cls, user):
        """
            Send a welcome email to the new user

            Args:
                user: the auth_user Row
        """

        cls.customise_auth_messages()
        auth_messages = current.auth.messages

        # Look up CMS template for welcome email
        try:
            recipient = user["email"]
        except (KeyError, TypeError):
            recipient = None
        if not recipient:
            current.response.error = auth_messages.unable_send_email
            return


        db = current.db
        s3db = current.s3db

        settings = current.deployment_settings

        # Define join
        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "auth") & \
                         (ltable.resource == "user") & \
                         (ltable.deleted == False))

        # Get message template
        query = (ctable.name == "WelcomeMessageInvited") & \
                (ctable.deleted == False)
        row = db(query).select(ctable.doc_id,
                               ctable.body,
                               join = join,
                               limitby = (0, 1),
                               ).first()
        if row:
            message_template = row.body
        else:
            # Disabled
            return

        # Look up attachments
        dtable = s3db.doc_document
        query = (dtable.doc_id == row.doc_id) & \
                (dtable.file != None) & (dtable.file != "") & \
                (dtable.deleted == False)
        rows = db(query).select(dtable.file)
        attachments = []
        for row in rows:
            filename, stream = dtable.file.retrieve(row.file)
            attachments.append(current.mail.Attachment(stream, filename=filename))

        # Default subject from auth.messages
        system_name = s3_str(settings.get_system_name())
        subject = s3_str(auth_messages.welcome_email_subject % \
                         {"system_name": system_name})

        # Custom message body
        data = {"system_name": system_name,
                "url": settings.get_base_public_url(),
                "profile": URL("default", "person", host=True),
                }
        message = formatmap(message_template, data)

        # Send email
        success = current.msg.send_email(to = recipient,
                                         subject = subject,
                                         message = message,
                                         attachments = attachments,
                                         )
        if not success:
            current.response.error = auth_messages.unable_send_email

    # -------------------------------------------------------------------------
    @classmethod
    def account(cls, key, code):
        """
            Find the account matching registration key and code

            Args:
                key: the registration key (from URL args)
                code: the registration code (from form)
        """

        if key and code:
            utable = current.auth.settings.table_user
            query = (utable.registration_key == cls.keyhash(key, code))
            account = current.db(query).select(utable.ALL, limitby=(0, 1)).first()
        else:
            account = None

        return account

    # -------------------------------------------------------------------------
    @staticmethod
    def formfields():
        """
            Generate the form fields for the registration form

            Returns:
                a tuple (formfields, required_fields)
                    - formfields = list of form fields
                    - required_fields = list of field names of required fields
        """

        T = current.T
        request = current.request

        auth = current.auth
        auth_settings = auth.settings
        auth_messages = auth.messages

        utable = auth_settings.table_user
        passfield = auth_settings.password_field

        # Last name is required
        utable.last_name.requires = IS_NOT_EMPTY(error_message=T("input required"))

        # Don't check for duplicate email (will be done in onvalidation)
        # => user might choose to use the current email address of the account
        # => if registration key or code are invalid, we don't want to give away
        #    any existing email addresses
        utable.email.requires = [IS_EMAIL(error_message = auth_messages.invalid_email),
                                 IS_LOWER(),
                                 ]

        # Instantiate Consent Tracker
        consent = ConsentTracking(processing_types=["STORE", "TOS_PUBADM"])

        # Form fields
        formfields = [utable.first_name,
                      utable.last_name,
                      utable.email,
                      utable[passfield],
                      Field("password_two", "password",
                            label = auth_messages.verify_password,
                            requires = IS_EXPR("value==%s" % \
                                               repr(request.vars.get(passfield)),
                                               error_message = auth_messages.mismatched_password,
                                               ),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (auth_messages.verify_password,
                                                              T("Enter the same password again"),
                                                              ),
                                          ),
                            ),
                      Field("code",
                            label = T("Registration Code"),
                            requires = IS_NOT_EMPTY(),
                            ),
                      Field("consent",
                            label = T("Consent"),
                            widget = consent.widget,
                            ),
                      ]


        # Required fields
        required_fields = ["first_name",
                           "last_name",
                           ]

        return formfields, required_fields

    # -------------------------------------------------------------------------
    @staticmethod
    def keyhash(key, code):
        """
            Generate a hash of the activation code using
            the registration key

            Args:
                key: the registration key
                code: the activation code

            Returns:
                the hash as string
        """

        crypt = CRYPT(key=key, digest_alg="sha512", salt=None)
        return str(crypt(code.upper())[0])

    # -------------------------------------------------------------------------
    @staticmethod
    def customise_auth_messages():
        """
            Customise auth messages:
            - welcome email subject
        """

        messages = current.auth.messages

        messages.welcome_email_subject = "Welcome to the %(system_name)s Portal"

# =============================================================================
class privacy(CustomController):
    """ Custom Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        ADMIN = current.auth.s3_has_role("ADMIN")

        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module

        module = "default"
        resource = "Privacy"

        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby=(0, 1)).first()
        if item:
            if ADMIN:
                content = DIV(XML(item.body),
                              BR(),
                              A(current.T("Edit"),
                                _href = URL(c="cms", f="post",
                                            args = [item.id, "update"],
                                            vars = {"module": module,
                                                    "resource": resource,
                                                    },
                                            ),
                                _class="action-btn",
                                ),
                              )
            else:
                content = DIV(XML(item.body))
        elif ADMIN:
            content = A(current.T("Edit"),
                        _href = URL(c="cms", f="post", args="create",
                                    vars = {"module": module,
                                            "resource": resource,
                                            },
                                    ),
                        _class="action-btn cms-edit",
                        )
        else:
            content = ""

        output["item"] = content

        self._view(TEMPLATE, "cmspage.html")
        return output

# =============================================================================
class legal(CustomController):
    """ Custom Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        ADMIN = current.auth.s3_has_role("ADMIN")

        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module

        module = "default"
        resource = "Legal"

        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby = (0, 1)
                                        ).first()
        if item:
            if ADMIN:
                content = DIV(XML(item.body),
                              BR(),
                              A(current.T("Edit"),
                                _href = URL(c="cms", f="post",
                                            args = [item.id, "update"],
                                            vars = {"module": module,
                                                    "resource": resource,
                                                    },
                                            ),
                                _class="action-btn",
                                ),
                              )
            else:
                content = DIV(XML(item.body))
        elif ADMIN:
            content = A(current.T("Edit"),
                        _href = URL(c="cms", f="post", args="create",
                                    vars = {"module": module,
                                            "resource": resource,
                                            },
                                    ),
                        _class="action-btn cms-edit",
                        )
        else:
            content = ""

        output["item"] = content

        self._view(TEMPLATE, "cmspage.html")
        return output

# =============================================================================
class geocode(CustomController):
    """
        Custom Geocoder
        - looks up Lat/Lon from Postcode &/or Address
        - looks up Lx from Lat/Lon
    """

    def __call__(self):

        vars_get = current.request.post_vars.get

        # Validate the formkey
        formkey = vars_get("k")
        keyname = "_formkey[geocode]"
        if not formkey or formkey not in current.session.get(keyname, []):
            status = 403
            message = current.ERROR.NOT_PERMITTED
            headers = {"Content-Type": "application/json"}
            current.log.error(message)
            raise HTTP(status,
                       body = current.xml.json_message(success = False,
                                                       statuscode = status,
                                                       message = message),
                       web2py_error = message,
                       **headers)

        gis = current.gis

        postcode = vars_get("postcode")
        address = vars_get("address")
        if address:
            full_address = "%s %s" %(postcode, address)
        else:
            full_address = postcode

        latlon = gis.geocode(full_address)
        if not isinstance(latlon, dict):
            output = "{}"
        else:
            lat = latlon["lat"]
            lon = latlon["lon"]
            results = gis.geocode_r(lat, lon)

            results["lat"] = lat
            results["lon"] = lon

            from core import JSONSEPARATORS
            output = json.dumps(results, separators=JSONSEPARATORS)

        current.response.headers["Content-Type"] = "application/json"
        return output

# END =========================================================================
