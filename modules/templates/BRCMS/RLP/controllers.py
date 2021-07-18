# -*- coding: utf-8 -*-

import json
from uuid import uuid4

from gluon import Field, HTTP, SQLFORM, URL, current, redirect, \
                  CRYPT, IS_EMPTY_OR, IS_EXPR, IS_NOT_EMPTY, \
                  A, BR, DIV, H3, H4, I, INPUT, LI, TAG, UL, XML

from gluon.storage import Storage

from s3 import IS_PHONE_NUMBER_SINGLE, JSONERRORS, \
               S3CustomController, S3LocationSelector, \
               s3_mark_required, s3_str

from templates.RLPPTM.notifications import formatmap

TEMPLATE = "BRCMS/RLP"
THEME = "RLP"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T
        s3 = current.response.s3

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

            from s3 import S3DateTime
            dtrepr = lambda dt: S3DateTime.datetime_represent(dt, utc=True)

            filter_roles = roles if sr.ADMIN not in roles else None
            posts = self.get_announcements(roles=filter_roles)

            # Render announcements list
            announcements = UL(_class="announcements")
            if posts:
                announcements_title = T("Announcements")
                priority_classes = {2: "announcement-important",
                                    3: "announcement-critical",
                                    }
                priority_icons = {2: "fa-exclamation-circle",
                                  3: "fa-exclamation-triangle",
                                  }
                for post in posts:
                    # The header
                    header = H4(post.name)

                    # Priority
                    priority = post.priority
                    # Add icon to header?
                    icon_class = priority_icons.get(post.priority)
                    if icon_class:
                        header = TAG[""](I(_class="fa %s announcement-icon" % icon_class),
                                         header,
                                         )
                    # Priority class for the box
                    prio = priority_classes.get(priority, "")

                    row = LI(DIV(DIV(DIV(dtrepr(post.date),
                                        _class = "announcement-date",
                                        ),
                                    _class="fright",
                                    ),
                                 DIV(DIV(header,
                                         _class = "announcement-header",
                                         ),
                                     DIV(XML(post.body),
                                         _class = "announcement-body",
                                         ),
                                     _class="announcement-text",
                                    ),
                                 _class = "announcement-box %s" % prio,
                                 ),
                             )
                    announcements.append(row)
        else:
            # Anonymous user
            # => provide a login box
            login_div = DIV(H3(T("Login")),
                            )
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)

        output = {"login_div": login_div,
                  "login_form": login_form,
                  "announcements": announcements,
                  "announcements_title": announcements_title,
                  }

        # Custom view and homepage styles
        s3.stylesheets.append("../themes/%s/homepage.css" % THEME)
        self._view(settings.get_theme_layouts(), "index.html")

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def get_announcements(roles=None):
        """
            Get current announcements

            @param roles: filter announcement by these roles

            @returns: any announcements (Rows)
        """

        db = current.db
        s3db = current.s3db

        # Look up all announcements
        ptable = s3db.cms_post
        stable = s3db.cms_series
        join = stable.on((stable.id == ptable.series_id) & \
                         (stable.name == "Announcements") & \
                         (stable.deleted == False))
        query = (ptable.date <= current.request.utcnow) & \
                (ptable.expired == False) & \
                (ptable.deleted == False)

        if roles:
            # Filter posts by roles
            ltable = s3db.cms_post_role
            q = (ltable.group_id.belongs(roles)) & \
                (ltable.deleted == False)
            rows = db(q).select(ltable.post_id,
                                cache = s3db.cache,
                                groupby = ltable.post_id,
                                )
            post_ids = {row.post_id for row in rows}
            query = (ptable.id.belongs(post_ids)) & query

        posts = db(query).select(ptable.name,
                                 ptable.body,
                                 ptable.date,
                                 ptable.priority,
                                 join = join,
                                 orderby = (~ptable.priority, ~ptable.date),
                                 limitby = (0, 5),
                                 )

        return posts

# =============================================================================
class privacy(S3CustomController):
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
class legal(S3CustomController):
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
class register(S3CustomController):
    """ Registration page for private citizens """

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

        # Page title and intro text
        title = T("Register as Private Citizen")

        # Get intro text from CMS
        db = current.db
        s3db = current.s3db

        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                        (ltable.module == "auth") & \
                        (ltable.resource == "user") & \
                        (ltable.deleted == False))

        query = (ctable.name == "RegistrationCitizenIntro") & \
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
        formfields, required_fields, subheadings = self.formfields()

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
                               hidden = {"_next": request.vars._next},
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

        # Add Subheadings
        if subheadings:
            for pos, heading in subheadings[::-1]:
                form[0].insert(pos, DIV(heading, _class="subheading"))

        # Set default registration key, so new users are prevented
        # from logging in until approved
        key = str(uuid4())
        code = uuid4().hex[-6:].upper()
        utable.registration_key.default = self.keyhash(key, code)

        if form.accepts(request.vars,
                        session,
                        formname = "register",
                        onvalidation = self.validate(),
                        ):

            formvars = form.vars

            # Create the user record (will be initially disabled by registration key)
            user_id = utable.insert(**utable._filter_fields(formvars, id=False))
            formvars.id = user_id

            # Save temporary user fields in s3db.auth_user_temp
            temptable = s3db.auth_user_temp
            record  = {"user_id": user_id,
                       "consent": formvars.consent,
                       }

            # Store Custom fields
            custom = {"location": formvars.location,
                      }
            record["custom"] = json.dumps(custom)
            temptable.insert(**record)

            # Post-process the new user record
            users = db(utable.id > 0).select(utable.id, limitby=(0, 2))
            if len(users) == 1:
                # 1st user to register doesn't need verification/approval
                auth.s3_approve_user(form.vars)
                session.confirmation = auth_messages.registration_successful

                # 1st user gets Admin rights
                admin_group_id = 1
                auth.add_membership(admin_group_id, users.first().id)

                # Log them in
                if "language" not in form.vars:
                    # Was missing from login form
                    form.vars.language = T.accepted_language
                user = Storage(utable._filter_fields(form.vars, id=True))
                auth.login_user(user)

                # Send welcome email
                verify_email.send_welcome_email(user)

                # Where to go next?
                register_next = request.vars._next or auth_settings.register_next

            else:
                # Request User Verify their Email
                # System Details for Verification Email
                verify_url = URL(c = "default",
                                 f = "index",
                                 args = ["verify_email", key],
                                 scheme = "https" if request.is_https else "http",
                                 )
                system = {"system_name": settings.get_system_name(),
                          "url": verify_url,
                          "code": code,
                          }

                # Try to send the Verification Email
                if not auth_settings.mailer or \
                   not auth_settings.mailer.settings.server or \
                   not auth_settings.mailer.send(to = form.vars.email,
                                                 subject = auth_messages.verify_email_subject % system,
                                                 message = auth_messages.verify_email % system,
                                                 ):
                    response.error = auth_messages.email_verification_failed

                    # Custom View
                    self._view(THEME, "register.html")

                    return {"title": title,
                            "form": form,
                            }

                # Redirect to Verification Info page
                register_next = URL(c = "default",
                                    f = "message",
                                    args = ["verify_email_sent"],
                                    vars = {"email": form.vars.email},
                                    )

            # Log action
            auth.log_event(auth_messages.register_log, form.vars)

            # Redirect
            redirect(register_next)

        elif form.errors:
            response.error = T("There are errors in the form, please check your input")

        # Custom View
        self._view(TEMPLATE, "register.html")

        return {"title": title,
                "intro": intro,
                "form": form,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def formfields():
        """
            Generate the form fields for the registration form

            @returns: a tuple (formfields, required_fields)
                      - formfields = list of form fields
                      - required_fields = list of field names of required fields
        """

        T = current.T
        request = current.request

        s3db = current.s3db
        auth = current.auth
        auth_settings = auth.settings
        auth_messages = auth.messages

        utable = auth_settings.table_user
        passfield = auth_settings.password_field

        # Last name is required
        utable.last_name.requires = IS_NOT_EMPTY(error_message=T("input required"))

        # Instantiate Consent Tracker
        consent = s3db.auth_Consent(processing_types=["TOS_PRIVATE", "STORE", "SHARE_OFFERS"])

        # Form fields
        formfields = [# -- User Account --
                      utable.first_name,
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
                      # -- Address --
                      Field("location", "json",
                            label = T("Address"),
                            widget = S3LocationSelector(
                                        levels = ("L1", "L2", "L3", "L4"),
                                        required_levels = ("L1", "L2", "L3"),
                                        show_address = True,
                                        address_required = True,
                                        show_postcode = True,
                                        postcode_required = True,
                                        show_map = True,
                                        ),
                            ),
                      # -- Contact Information --
                      Field("mobile_phone",
                            label = T("Mobile Phone"),
                            requires = IS_EMPTY_OR(IS_PHONE_NUMBER_SINGLE()),
                            ),
                      # -- Privacy and Terms --
                      Field("consent",
                            label = T("Consent"),
                            widget = consent.widget,
                            ),
                      ]


        # Required fields
        required_fields = ["first_name",
                           "last_name",
                           ]

        # Subheadings
        subheadings = ((0, T("User Account")),
                       (5, T("Address")),
                       (6, T("Contact Information")),
                       (7, "%s / %s" % (T("Privacy"), T("Terms of Service"))),
                       )

        # Geocoder
        current.response.s3.scripts.append("/%s/static/themes/RLP/js/geocoderPlugin.js" % request.application)

        return formfields, required_fields, subheadings

    # -------------------------------------------------------------------------
    @classmethod
    def validate(cls):
        """
            Custom validation of registration form
            - currently doing nothing except standard onvalidation

            @returns: callback function
        """

        def register_onvalidation(form):

            onvalidation = current.auth.settings.register_onvalidation
            if onvalidation:
                from gluon.tools import callback
                callback(onvalidation, form, tablename="auth_user")

        return register_onvalidation

    # -------------------------------------------------------------------------
    @classmethod
    def register_onaccept(cls, user_id):
        """
            Process Custom Fields
        """

        db = current.db
        s3db = current.s3db

        # Get custom field data from DB
        temptable = s3db.auth_user_temp
        record = db(temptable.user_id == user_id).select(temptable.custom,
                                                         limitby = (0, 1),
                                                         ).first()
        if not record:
            return
        try:
            custom = json.loads(record.custom)
        except JSONERRORS:
            return

        auth = current.auth
        set_record_owner = auth.s3_set_record_owner
        s3db_onaccept = s3db.onaccept

        # Get the person record
        ltable = s3db.pr_person_user
        ptable = s3db.pr_person
        query = (ltable.user_id == user_id) & \
                (ltable.deleted == False) & \
                (ptable.pe_id == ltable.pe_id) & \
                (ptable.deleted == False)
        person = db(query).select(ptable.id,
                                  ptable.pe_id,
                                  ptable.pe_label,
                                  limitby = (0, 1),
                                  ).first()
        if not person:
            current.log.error("Person record for user %s not found" % user_id)
            return
        person_id = person.id

        # Update person record
        person_update = {}
        if not person.pe_label:
            person_update["pe_label"] = "C-%07d" % person_id
        if person_update:
            person.update_record(**person_update)
            person_update["id"] = person_id
        set_record_owner(ptable, person_id, force_update=True)
        if person_update:
            s3db_onaccept(ptable, person_update, method="update")

        # Register address
        location = custom.get("location")
        if location:
            location_id = location.get("id")
            if not location_id:
                # Create new location
                ltable = s3db.gis_location
                del location["wkt"] # Will get created during onaccept & we don't want the 'Source WKT has been cleaned by Shapely" warning
                location["id"] = location_id = ltable.insert(**location)
                set_record_owner(ltable, location, owned_by_user=user_id)
                s3db_onaccept(ltable, location, method="create")
            if location_id:
                # Link location to person record
                atable = s3db.pr_address
                query = (atable.pe_id == person.pe_id) & \
                        (atable.location_id == location_id) & \
                        (atable.type == 1) & \
                        (atable.deleted == False)
                address = db(query).select(atable.id, limitby=(0, 1)).first()
                if not address:
                    address_data = {"pe_id": person.pe_id,
                                    "location_id": location_id,
                                    "type": 1,
                                    }
                    address_data["id"] = atable.insert(**address_data)
                    set_record_owner(atable, address_data)
                    s3db_onaccept(atable, address_data, method="create")

    # -------------------------------------------------------------------------
    @staticmethod
    def keyhash(key, code):
        """
            Generate a hash of the activation code using
            the registration key

            @param key: the registration key
            @param code: the activation code

            @returns: the hash as string
        """

        crypt = CRYPT(key=key, digest_alg="sha512", salt=None)
        return str(crypt(code.upper())[0])

    # -------------------------------------------------------------------------
    @staticmethod
    def customise_auth_messages():
        """
            Customise auth messages:
            - verification email
            - welcome email
        """

        messages = current.auth.messages

        messages.verify_email_subject = "%(system_name)s - Verify Email"
        messages.verify_email = \
"""Click on the link %(url)s to verify your email.

Your Activation Code: %(code)s
"""

        messages.welcome_email_subject = "Welcome to the %(system_name)s Portal"
        messages.welcome_email = \
"""Welcome to the %(system_name)s Portal
 - To edit your profile go to: %(url)s%(profile)s

Thank you
"""

# =============================================================================
class verify_email(S3CustomController):
    """ Custom verify_email Page """

    def __call__(self):

        T = current.T

        request = current.request
        response = current.response
        session = current.session

        # Get the registration key
        if len(request.args) > 1:
            key = request.args[-1]
            session.s3.registration_key = key
            redirect(URL(c="default", f="index", args = ["verify_email"]))
        else:
            key = session.s3.registration_key
        if not key:
            session.error = T("Missing registration key")
            redirect(URL(c="default", f="index"))

        settings = current.deployment_settings
        formfields = [Field("activation_code",
                            label = T("Please enter your Activation Code"),
                            requires = IS_NOT_EMPTY(),
                            ),
                      ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = "auth_user",
                               record = None,
                               hidden = {"_next": request.vars._next,
                                         "registration_key": key,
                                         },
                               separator = ":",
                               showid = False,
                               submit_button = T("Submit"),
                               formstyle = settings.get_ui_formstyle(),
                               #buttons = buttons,
                               *formfields)

        if form.accepts(request.vars,
                        session,
                        formname = "register_confirm",
                        ):

            db = current.db
            s3db = current.s3db

            auth = current.auth
            auth_settings = auth.settings
            register.customise_auth_messages()

            # Get registration key from URL
            code = form.vars.activation_code

            # Find the pending user account
            utable = auth_settings.table_user
            query = (utable.registration_key == register.keyhash(key, code))
            user = db(query).select(limitby = (0, 1),
                                    ).first()
            if not user:
                session.error = T("Registration not found")
                redirect(auth_settings.verify_email_next)

            # Configure callback to process custom fields
            s3db.configure("auth_user",
                           register_onaccept = register.register_onaccept,
                           )

            # Approve and link user
            auth.s3_approve_user(user)

            # Send welcome email (custom)
            self.send_welcome_email(user)

            # Log them in
            user = Storage(utable._filter_fields(user, id=True))
            auth.login_user(user)

            auth_messages = auth.messages
            auth.log_event(auth_messages.verify_email_log, user)

            session = current.session
            session.confirmation = auth_messages.email_verified
            session.flash = auth_messages.registration_successful

            # Redirect to personal profile
            redirect(URL(c="default", f="person"))

        self._view(THEME, "register.html")

        return {"title": T("Confirm Registration"),
                "form": form,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def send_welcome_email(user):
        """
            Send a welcome email to the new user

            @param user: the auth_user Row
        """

        register.customise_auth_messages()
        auth_messages = current.auth.messages

        try:
            recipient = user["email"]
        except (KeyError, TypeError):
            recipient = None
        if not recipient:
            current.response.error = auth_messages.unable_send_email
            return

        # Look up CMS template for welcome email
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
        query = (ctable.name == "WelcomeMessagePrivate") & \
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

# =============================================================================
class geocode(S3CustomController):
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

            from s3.s3xml import SEPARATORS
            output = json.dumps(results, separators=SEPARATORS)

        current.response.headers["Content-Type"] = "application/json"
        return output

# END =========================================================================
