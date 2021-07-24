# -*- coding: utf-8 -*-

import json
import os

from uuid import uuid4

from gluon import Field, HTTP, SQLFORM, URL, current, redirect, \
                  CRYPT, IS_EMAIL, IS_EMPTY_OR, IS_EXPR, IS_IN_SET, \
                  IS_LENGTH, IS_NOT_EMPTY, IS_URL, \
                  A, BR, DIV, FORM, H3, H4, H5, I, INPUT, LI, TABLE, \
                  TAG, TD, TR, UL, XML

from gluon.storage import Storage

from s3 import FS, IS_PHONE_NUMBER_MULTI, IS_PHONE_NUMBER_SINGLE, \
               JSONERRORS, S3CRUD, S3CustomController, S3LocationSelector, \
               S3Represent, S3Report, S3Request, S3WithIntro, \
               s3_comments_widget, s3_get_extension, s3_mark_required, \
               s3_str, s3_text_represent, s3_truncate

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
                  "intro": self.get_cms_intro(("default", "index", "HomepageIntro"), cmsxml=True),
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

    # -------------------------------------------------------------------------
    @staticmethod
    def get_cms_intro(intro, cmsxml=True):
        """
            Get intro from CMS

            @param intro: the intro spec as tuple (module, resource, postname)
        """

        # Get intro text from CMS
        db = current.db
        s3db = current.s3db

        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == intro[0]) & \
                         (ltable.resource == intro[1]) & \
                         (ltable.deleted == False))

        query = (ctable.name == intro[2]) & \
                (ctable.deleted == False)
        row = db(query).select(ctable.body,
                               join = join,
                               cache = s3db.cache,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return None

        return XML(row.body) if cmsxml else row.body

# =============================================================================
class overview(S3CustomController):
    """ Custom page to display site usage statistics """

    def __call__(self):

        s3 = current.response.s3

        request = current.request

        appname = request.application
        output = {"appname": appname,
                  }

        # Read latest usage statistics from file
        source = os.path.join(request.folder, "static", "data", "RLP", "rlpcm_usage.json")
        try:
            with open(source, "r") as s:
                data = json.load(s)
        except JSONERRORS:
            current.log.error("Overview data source: invalid JSON")
        except IOError:
            current.log.error("Overview data source: file not found or invalid")
        if data:
            output["data"] = data

        # TODO add CMS intro

        # Inject D3 scripts
        S3Report.inject_d3()

        # Inject charts-script
        scripts = s3.scripts
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.charts.js" % appname
            if script not in scripts:
                scripts.append(script)
        else:
            script = "/%s/static/scripts/S3/s3.ui.charts.min.js" % appname
            if script not in scripts:
                scripts.append(script)

        # Instantiate charts
        scriptopts = {
            # Standard color set:
            "colors": ['#0C9CD0', # blue
                       '#E03158', # red
                       '#FBA629', # amber
                       '#8ABC3F', # green
                       '#AFB8BF', # grey
                       ],
            }
        script = '''$('.homepage-chart').uiChart(%s)''' % json.dumps(scriptopts)
        s3.jquery_ready.append(script)

        self._view(TEMPLATE, "overview.html")

        return output

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
                       "mobile": formvars.mobile_phone,
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

        settings = current.deployment_settings

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
                                        filter_lx = settings.get_custom("regional"),
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

        settings = current.deployment_settings

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

        # Create case file
        ctable = s3db.br_case
        case = {"person_id": person_id,
                "status_id": s3db.br_case_default_status(),
                "organisation_id": settings.get_org_default_organisation(),
                }
        case["id"] = ctable.insert(**case)
        set_record_owner(ctable, case, owned_by_user=user_id)
        s3db_onaccept(ctable, case, method="create")

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

        # Assign site-wide CITIZEN role
        auth.s3_assign_role(user_id, "CITIZEN", for_pe=0)

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
        """

        messages = current.auth.messages

        messages.verify_email_subject = "%(system_name)s - Verify Email"
        messages.verify_email = \
"""Click on the link %(url)s to verify your email.

Your Activation Code: %(code)s
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
        query = (ctable.name == "WelcomeMessageCitizen") & \
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

# =============================================================================
class register_org(S3CustomController):
    """ Custom Registration Page """

    def __call__(self):

        auth = current.auth

        if auth.s3_logged_in():
            # Redirect if already logged-in
            redirect(URL(c="default", f="index"))

        auth_settings = auth.settings
        auth_messages = auth.messages
        register.customise_auth_messages()

        T = current.T
        db = current.db
        s3db = current.s3db

        request = current.request
        response = current.response
        session = current.session
        settings = current.deployment_settings

        if not settings.get_custom(key="org_registration"):
            session.error = T("Function not available")
            redirect(URL(c="default", f="index"))

        utable = auth_settings.table_user

        # Page title and intro text
        title = T("Register Organization")

        # Get intro text from CMS
        db = current.db
        s3db = current.s3db

        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "auth") & \
                         (ltable.resource == "user") & \
                         (ltable.deleted == False))
        query = (ctable.name == "RegistrationOrgIntro") & \
                (ctable.deleted == False)
        row = db(query).select(ctable.body,
                                join = join,
                                cache = s3db.cache,
                                limitby = (0, 1),
                                ).first()
        intro = row.body if row else None

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

        # Add Subheadings
        if subheadings:
            for pos, heading in subheadings[::-1]:
                form[0].insert(pos, DIV(heading, _class="subheading"))

        # Inject client-side Validation
        auth.s3_register_validation()

        # Set default registration key, so new users are prevented
        # from logging in until approved
        key = str(uuid4())
        code = uuid4().hex[-6:].upper()
        utable.registration_key.default = register.keyhash(key, code)

        if form.accepts(request.vars,
                        session,
                        formname = "register",
                        onvalidation = auth_settings.register_onvalidation,
                        ):

            formvars = form.vars

            organisation = formvars.get("organisation")

            # Check if organisation already exists
            organisation_id = self.lookup_organisation(formvars)
            if organisation_id:
                formvars["organisation_id"] = organisation_id

            # Create the user record
            user_id = utable.insert(**utable._filter_fields(formvars, id=False))
            formvars.id = user_id

            # Save temporary user fields in s3db.auth_user_temp
            temptable = s3db.auth_user_temp
            record  = {"user_id": user_id,
                       "consent": formvars.consent,
                       "mobile": formvars.mobile_phone,
                       }

            # Store Custom fields
            custom = {"location": formvars.location,
                      "office_phone": formvars.office_phone,
                      "office_email": formvars.office_email,
                      "website": formvars.website,
                      "comments": formvars.comments,
                      }
            if not organisation_id:
                custom["organisation"] = organisation
                custom["organisation_type"] = formvars.organisation_type
            record["custom"] = json.dumps(custom)

            temptable.insert(**record)

            # Request User Verify their Email
            # System Details for Verification Email
            verify_url = URL(c = "default",
                             f = "index",
                             args = ["verify_org", key],
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
        self._view(THEME, "register.html")

        return {"title": title,
                "intro": intro,
                "form": form,
                }

    # -------------------------------------------------------------------------
    @classmethod
    def formfields(cls):
        """
            Generate the form fields for the registration form

            @returns: a tuple (formfields, required_fields, subheadings)
                      - formfields = list of form fields
                      - required_fields = list of field names of required fields
                      - subheadings = list of tuples (position, heading) to
                                      insert into the form
        """

        T = current.T
        request = current.request

        #db = current.db
        s3db = current.s3db

        auth = current.auth
        auth_settings = auth.settings
        auth_messages = auth.messages

        utable = auth_settings.table_user
        passfield = auth_settings.password_field

        # Instantiate Consent Tracker
        consent = s3db.auth_Consent(processing_types=["TOS_CORPORATE", "STORE", "SHARE_OFFERS"])

        # Last name is required
        utable.last_name.requires = IS_NOT_EMPTY(error_message=T("input required"))

        # Representation for organisation types
        org_types = cls.get_org_types()

        # Form fields
        formfields = [# -- User account ---
                      utable.first_name,
                      utable.last_name,
                      utable.email,
                      utable[passfield],

                      # Password Verification Field
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
                      # -- Organisation --
                      Field("organisation",
                            label = T("Name"),
                            requires = [IS_NOT_EMPTY(), IS_LENGTH(60)],
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Organization Name"),
                                                              T("Specify the name of the organization (max 60 characters)"),
                                                              ),
                                          ),
                            ),
                      Field("organisation_type", "integer",
                            label = T("Organization Type"),
                            requires = IS_IN_SET(org_types, sort=True),
                            ),
                      Field("comments", "text",
                            label = T("Description"),
                            requires = IS_NOT_EMPTY(),
                            widget = S3WithIntro(widget = s3_comments_widget,
                                                 # Widget intro from CMS
                                                 intro = ("org",
                                                          "organisation",
                                                          "OrgSelfPresentationIntro",
                                                          ),
                                                 ),
                            ),
                      # -- Address --
                      Field("location", "json",
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
                      Field("office_phone",
                            label = T("Telephone"),
                            requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                            ),
                      Field("office_email",
                            label = T("Email"),
                            requires = IS_EMPTY_OR(IS_EMAIL()),
                            ),
                      Field("website",
                            label = T("Website"),
                            requires = IS_EMPTY_OR(
                                        IS_URL(mode = "generic",
                                               allowed_schemes = ["http", "https"],
                                               prepend_scheme = "http",
                                               )),
                            ),
                      # -- Privacy and Consent --
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
                       (5, T("Organisation")),
                       (8, T("Address")),
                       (9, T("Contact Information")),
                       (12, "%s / %s" % (T("Privacy"), T("Terms of Service"))),
                       )

        # Geocoder
        current.response.s3.scripts.append("/%s/static/themes/RLP/js/geocoderPlugin.js" % request.application)

        return formfields, required_fields, subheadings

    # -------------------------------------------------------------------------
    @staticmethod
    def get_org_types():
        """
            Look up applicable org types for registration

            @returns: a dict {org_type_id: org_type_name}
        """

        db = current.db
        s3db = current.s3db

        ttable = s3db.org_organisation_type
        rows = db(ttable.deleted==False).select(ttable.id, ttable.name)

        return {row.id: row.name for row in rows}

    # -------------------------------------------------------------------------
    @staticmethod
    def lookup_organisation(formvars):
        """
            Identify the organisation the user attempts to register for,
            by name, office Lx and if necessary office email address

            @param formvars: the FORM vars
            @returns: organisation_id if found, or None if this is a new
                      organisation
        """

        orgname = formvars.get("organisation")
        if not orgname:
            return None

        db = current.db
        s3db = current.s3db

        otable = s3db.org_organisation
        ftable = s3db.org_office
        ltable = s3db.gis_location

        # Search by name
        join = None
        query = (otable.name == orgname) & \
                (otable.deleted == False)
        # Do we have a selected location (should have since mandatory)
        location = formvars.get("location")
        if isinstance(location, str):
            try:
                location = json.loads(location)
            except JSONERRORS:
                location = None

        if location:
            # Include the Lx ancestor in the lookup
            ancestor = None
            for level in ("L4", "L3", "L2"):
                ancestor = location.get(level)
                if ancestor:
                    break
            if ancestor:
                join = [ftable.on(ftable.organisation_id == otable.id),
                        ltable.on((ltable.id == ftable.location_id) & \
                                  ((ltable.level == None) & \
                                   (ltable.parent == ancestor) | \
                                   (ltable.id == ancestor))
                                  ),
                        ]

        rows = db(query).select(otable.id, join=join)
        organisation_id = None
        if len(rows) > 1:
            # Multiple matches => try using facility email to reduce
            office_email = formvars.get("office_email")
            if office_email:
                candidates = {row.id for row in rows}
                query = (ftable.organisation_id.belongs(candidates)) & \
                        (ftable.email == office_email) & \
                        (ftable.deleted == False)
                match = db(query).select(ftable.organisation_id,
                                         limitby = (0, 2),
                                         )
                if len(match) == 1:
                    organisation_id = match.first().organisation_id
        elif rows:
            # Single match - this organisation already exists
            organisation_id = rows.first().id

        return organisation_id

# =============================================================================
class verify_org(S3CustomController):
    """ Custom verify_email Page """

    def __call__(self):

        T = current.T

        request = current.request
        response = current.response
        session = current.session

        settings = current.deployment_settings

        # Get the registration key
        if len(request.args) > 1:
            key = request.args[-1]
            session.s3.registration_key = key
            redirect(URL(c="default", f="index", args = ["verify_org"]))
        else:
            key = session.s3.registration_key
        if not key:
            session.error = T("Missing registration key")
            redirect(URL(c="default", f="index"))

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

            user_id = user.id
            db(utable.id == user_id).update(registration_key = "pending")
            auth.log_event(auth.messages.verify_email_log, user)

            # Lookup the Approver(s)
            gtable = db.auth_group
            mtable = db.auth_membership
            pe_id = None

            # Is this an existing Org?
            organisation_id = user.organisation_id
            if organisation_id:
                role_required = "ORG_ADMIN"

                # Get org_name and pe_id from organisation
                otable = s3db.org_organisation
                row = db(otable.id == organisation_id).select(otable.name,
                                                              otable.pe_id,
                                                              limitby = (0, 1)
                                                              ).first()
                if row:
                    org_name = row.name
                    pe_id = row.pe_id

                subject = """%(system_name)s - New User Approval Pending"""
                message = """Your action is required to approve a New User for %(org_name)s:
%(user_name)s
Please go to %(url)s to approve this user."""

            if not pe_id:
                role_required = "ORG_GROUP_ADMIN"

                subject = """%(system_name)s - New Organisation Approval Pending"""
                message = """Your action is required to approve a New Organisation for %(system_name)s:
%(org_name)s
Please go to %(url)s to approve this station."""

                # Get org_name from auth_user_temp
                ttable= s3db.auth_user_temp
                temp = db(ttable.user_id == user_id).select(ttable.custom,
                                                            limitby = (0, 1)
                                                            ).first()
                try:
                    custom = json.loads(temp.custom)
                except JSONERRORS:
                    custom = {}
                org_name = custom.get("organisation")

            query = (mtable.pe_id == 0)
            if pe_id:
                query |= (mtable.pe_id == pe_id)
            join = [mtable.on((mtable.user_id == utable.id) & \
                              (mtable.deleted == False)),
                    gtable.on((gtable.id == mtable.group_id) & \
                              (gtable.uuid == role_required)),
                    ]
            approvers = db(query).select(utable.email,
                                         utable.language,
                                         join = join,
                                         )

            # Ensure that we send out the mails in the language that the approver(s) want
            languages = {}
            for approver in approvers:
                language = approver.language
                if language not in languages:
                    languages[language] = [approver.email]
                else:
                    languages[language].append(approver.email)

            subjects = {}
            messages = {}
            system_name = settings.get_system_name()

            base_url = response.s3.base_url
            url = "%s/default/index/approve_org/%s" % (base_url, user_id)

            for language in languages:
                subjects[language] = s3_str(T(subject, language=language) %
                                            {"system_name": system_name,
                                             })
                messages[language] = s3_str(T(message, language=language) %
                                            {"org_name": org_name,
                                             "system_name": system_name,
                                             "user_name": user.email,
                                             "url": url,
                                             })

            result = None
            mailer = auth_settings.mailer
            if mailer.settings.server:
                send_email = mailer.send
                for approver in approvers:
                    language = approver["language"]
                    result = send_email(to = approver["email"],
                                        subject = subjects[language],
                                        message = messages[language]
                                        )

            session = current.session
            if result:
                session.confirmation = settings.get_auth_registration_pending_approval()
            else:
                # Don't prevent registration just because email not configured
                #db.rollback()
                session.error = auth.messages.email_send_failed

            redirect(URL(c="default", f="index"))

        self._view(THEME, "register.html")

        return {"title": T("Confirm Registration"),
                "form": form,
                }

# =============================================================================
class approve_org(S3CustomController):
    """ Custom Approval Page """

    def __call__(self):

        T = current.T
        auth = current.auth
        db = current.db
        s3db = current.s3db
        session = current.session

        # Must be global ORG_GROUP_ADMIN or ORG_ADMIN
        has_role = auth.s3_has_role
        if has_role("ORG_GROUP_ADMIN", for_pe=0):
            ORG_ADMIN = False
        elif has_role("ORG_ADMIN"):
            ORG_ADMIN = True
        else:
            session.error = T("Not Permitted!")
            redirect(URL(c="default", f="index", args=None))

        utable = db.auth_user
        request = current.request
        response = current.response

        # Single User or List?
        if len(request.args) > 1:
            user_id = request.args[1]
            user = db(utable.id == user_id).select(utable.id,
                                                   utable.first_name,
                                                   utable.last_name,
                                                   utable.email,
                                                   utable.organisation_id,
                                                   utable.org_group_id,
                                                   utable.registration_key,
                                                   utable.link_user_to,
                                                   utable.site_id,
                                                   limitby = (0, 1)
                                                   ).first()

            otable = s3db.org_organisation
            organisation_id = user.organisation_id
            if organisation_id:
                org = db(otable.id == organisation_id).select(otable.name,
                                                              otable.pe_id,
                                                              limitby = (0, 1)
                                                              ).first()
            if ORG_ADMIN:
                if not organisation_id or \
                   not has_role("ORG_ADMIN", for_pe=org.pe_id):
                    session.error = T("Account not within your Organisation!")
                    redirect(URL(c="default", f="index", args=["approve"]))

            person = "%(first_name)s %(last_name)s <%(email)s>" % {"first_name": user.first_name,
                                                                   "last_name": user.last_name,
                                                                   "email": user.email,
                                                                   }
            ttable = s3db.auth_user_temp
            temp = db(ttable.user_id == user_id).select(ttable.id,
                                                        ttable.custom,
                                                        limitby = (0, 1),
                                                        ).first()
            try:
                custom = json.loads(temp.custom)
            except JSONERRORS:
                custom = {}

            from gluon.sqlhtml import BooleanWidget, OptionsWidget, TextWidget

            # Organisation Name
            custom_get = custom.get
            organisation = custom_get("organisation")
            if organisation:
                orgname = TR(TD("%s:" % T("Organization / Company")),
                             TD(organisation),
                             )
            else:
                orgname = None

            # Org type selector
            selected_type = custom_get("organisation_type")
            org_types = register_org.get_org_types()
            if selected_type:
                try:
                    selected_type = int(selected_type)
                except (ValueError, TypeError):
                    selected_type = None
            if selected_type and selected_type not in org_types:
                selected_type = None
            field = Field("organisation_type", "integer",
                          label = T("Organization Type"),
                          requires = IS_IN_SET(org_types),
                          )
            field.tablename = "approve"
            type_selector = OptionsWidget.widget(field, selected_type)

            # Org Description
            comments = custom_get("comments")

            # Address
            location = custom_get("location")
            location_get = location.get
            addr_street = location_get("addr_street")
            addr_postcode = location_get("addr_postcode")
            L1 = location_get("L1")
            L2 = location_get("L2")
            L3 = location_get("L3")
            L4 = location_get("L4")
            represent = S3Represent(lookup = "gis_location")
            address = TABLE(TR(addr_street or ""),
                            TR(addr_postcode or ""),
                            TR(represent(L4) if L4 else ""),
                            TR(represent(L3) if L3 else ""),
                            TR(represent(L2) if L2 else ""),
                            TR(represent(L1) if L1 else ""),
                            )

            # Contact and Appointments
            office_phone = custom_get("office_phone")
            office_email = custom_get("office_email")
            website = custom_get("website")

            # Rejection Message
            field = Field("reject_notify", "boolean",
                          default = False,
                          requires = None,
                          )
            field.tablename = "approve"
            reject_notify = BooleanWidget.widget(field, False)
            field = Field("reject_message", "text",
                          requires = None,
                          )
            field.tablename = "approve"
            reject_message = TextWidget.widget(field, "")
            field = Field("reject_block", "boolean",
                          default = True,
                          requires = None,
                          )
            field.tablename = "approve"
            reject_block = BooleanWidget.widget(field, True)

            if user.registration_key is None:
                response.warning = T("Registration has previously been Approved")
            elif user.registration_key == "rejected":
                response.warning = T("Registration has previously been Rejected")
            elif user.registration_key != "pending":
                response.warning = T("User hasn't verified their email")

            approve = INPUT(_value = T("Approve"),
                            _type = "submit",
                            _name = "approve-btn",
                            _id = "approve-btn",
                            _class = "small primary button",
                            )

            reject = INPUT(_value = T("Reject"),
                           _type = "submit",
                           _name = "reject-btn",
                           _id = "reject-btn",
                           _class = "small alert button",
                           )

            strrepr = lambda v: v if v else "-"
            form = FORM(TABLE(TR(approve,
                                 reject,
                                 ),

                              TR(TD("%s:" % T("Person")),
                                 TD(person),
                                 ),

                              orgname,
                              TR(TD("%s:" % T("Organization Type")),
                                 TD(type_selector),
                                 ),
                              TR(TD("%s:" % T("Description")),
                                 TD(s3_text_represent(strrepr(comments))),
                                 ),

                              TR(TD("%s:" % T("Address")),
                                 TD(address),
                                 ),

                              TR(TD("%s:" % T("Telephone")),
                                 TD(strrepr(office_phone)),
                                 ),
                              TR(TD("%s:" % T("Email")),
                                 TD(strrepr(office_email)),
                                 ),
                              TR(TD("%s:" % T("Website")),
                                 TD(strrepr(website)),
                                 ),
                              TR(TD(H5("%s:" % T("Upon Rejection")), _colspan="2"),
                                 ),
                              TR(TD("%s:" % T("Notify about Rejection")),
                                 TD(reject_notify),
                                 ),
                              TR(TD("%s:" % T("Message")),
                                 TD(reject_message),
                                 ),
                              TR(TD("%s:" % T("Block Email-Address")),
                                 TD(reject_block),
                                 ),
                              ),
                        _class = "approve-form",
                        )

            if form.accepts(request.post_vars, session, formname="approve"):

                form_vars = form.vars

                rejected = bool(form_vars.get("reject-btn"))
                approved = bool(form_vars.get("approve-btn")) and not rejected

                if approved:

                    set_record_owner = auth.s3_set_record_owner
                    s3db_onaccept = s3db.onaccept
                    update_super = s3db.update_super

                    if not organisation_id:

                        # Create organisation
                        org = {"name": organisation,
                               "phone": office_phone,
                               "website": website,
                               "comments": comments,
                               }
                        org["id"] = organisation_id = otable.insert(**org)
                        update_super(otable, org)
                        set_record_owner(otable, org, owned_by_user=user_id)
                        s3db_onaccept(otable, org, method="create")

                        # Add email contact
                        if office_email:
                            ctable = s3db.pr_contact
                            contact = {"pe_id": org["pe_id"],
                                       "contact_method": "EMAIL",
                                       "value": office_email,
                                       }
                            ctable = s3db.pr_contact
                            contact["id"] = ctable.insert(**contact)
                            set_record_owner(ctable, contact, owned_by_user=user_id)
                            s3db_onaccept(ctable, contact, method="create")

                        # Link organisation to selected organisation type
                        type_id = form_vars.get("organisation_type")
                        if type_id:
                            ltable = s3db.org_organisation_organisation_type
                            type_id = int(type_id)
                            link = {"organisation_id": organisation_id,
                                    "organisation_type_id": type_id,
                                    }
                            link["id"] = ltable.insert(**link)
                            set_record_owner(ltable, link)
                            s3db_onaccept(ltable, link, method="create")

                        # Update user
                        user.update_record(organisation_id = organisation_id,
                                           registration_key = None,
                                           )

                        # Grant ORG_ADMIN and PROVIDER_ACCOUNTANT
                        auth.s3_assign_role(user_id, "ORG_ADMIN", for_pe=org["pe_id"])
                    else:
                        # Update user
                        user.update_record(registration_key = None)

                    # Grant RELIEF_PROVIDER
                    auth.s3_assign_role(user_id, "RELIEF_PROVIDER")

                    location_id = location_get("id")
                    if not location_id:
                        # Create location
                        ltable = s3db.gis_location
                        del location["wkt"] # Will get created during onaccept & we don't want the 'Source WKT has been cleaned by Shapely" warning
                        location["id"] = location_id = ltable.insert(**location)
                        set_record_owner(ltable, location, owned_by_user=user_id)
                        s3db_onaccept(ltable, location, method="create")

                    # Create office
                    ftable = s3db.org_office
                    office_name = organisation if organisation else org.name
                    office = {"name": s3_truncate(office_name),
                              "organisation_id": organisation_id,
                              "location_id": location_id,
                              "phone1": office_phone,
                              "email": office_email,
                              "website": website,
                              }
                    office["id"] = ftable.insert(**office)
                    update_super(ftable, office)
                    set_record_owner(ftable, office, owned_by_user=user_id)
                    s3db_onaccept(ftable, office, method="create")

                    # Approve user
                    auth.s3_approve_user(user)

                    # Send welcome email
                    settings = current.deployment_settings
                    from templates.RLPPTM.notifications import CMSNotifications
                    error = CMSNotifications.send(user.email,
                                                  "WelcomeProvider",
                                                  {"name": organisation or org.name,
                                                   "homepage": settings.get_base_public_url(),
                                                   "profile": URL("default", "person", host=True),
                                                   },
                                                  module = "auth",
                                                  resource = "user",
                                                  )
                    if error:
                        session.warning = "%s: %s" % (T("Welcome Email NOT sent"), error)

                    session.confirmation = T("Registration approved")
                    redirect(URL(c = "default", f = "index", args = ["approve_org"]))

                elif rejected:
                    if form_vars.get("reject_notify"):
                        # Notify the applicant about the rejection and reasons
                        message = form_vars.get("reject_message")
                        if message and user.email:
                            from templates.RLPPTM.notifications import CMSNotifications
                            error = CMSNotifications.send(user.email,
                                                          "RejectProvider",
                                                          {"reason": message,
                                                           },
                                                          module = "auth",
                                                          resource = "user",
                                                          )
                            if error:
                                session.warning = "%s: %s" % (T("Rejection Notification NOT sent"), error)

                    if form_vars.get("reject_block"):
                        # Keep email to prevent another attempt
                        email = user.email
                    else:
                        # Drop email address from rejected account to allow another attempt
                        email = None

                    # Drop the temp record
                    if temp:
                        temp.delete_record()
                    # Mark the user account as rejected and deleted, remove names
                    user.update_record(first_name = "",
                                       last_name = "",
                                       email = email,
                                       password = uuid4().hex,
                                       deleted = True,
                                       registration_key = "rejected",
                                       )
                    session.confirmation = T("Registration rejected")
                    redirect(URL(c="default", f="index", args=["approve_org"]))

            output = {"form": form,
                      "title": T("Approve Organization"),
                      }

            # Custom View
            self._view("RLPPTM", "approve.html")

        else:
            # List View

            # Only include pending accounts
            accounts_filter = FS("registration_key") == "pending"
            if ORG_ADMIN:
                # Filter to just their users
                gtable = db.auth_group
                mtable = db.auth_membership
                query = (mtable.user_id == auth.user.id) & \
                        (mtable.group_id == gtable.id) & \
                        (gtable.uuid == "ORG_ADMIN")
                memberships = db(query).select(mtable.pe_id)
                pe_id = [m.pe_id for m in memberships]
                otable = s3db.org_organisation
                orgs = db(otable.pe_id.belongs(pe_id)).select(otable.id)
                organisation_id = [org.id for org in orgs]
                accounts_filter &= FS("organisation_id").belongs(organisation_id)
            else:
                accounts_filter &= FS("organisation_id") == None

            resource = s3db.resource("auth_user", filter=accounts_filter)

            list_id = "datatable"

            # List fields
            list_fields = resource.list_fields()

            orderby = None

            s3 = response.s3
            representation = s3_get_extension(request) or \
                             S3Request.DEFAULT_REPRESENTATION

            # Pagination
            get_vars = request.get_vars
            if representation == "aadata":
                start, limit = S3CRUD._limits(get_vars)
            else:
                # Initial page request always uses defaults (otherwise
                # filtering and pagination would have to be relative to
                # the initial limits, but there is no use-case for that)
                start = None
                limit = None if s3.no_sspag else 0

            left = []
            distinct = False
            dtargs = {}

            if representation in S3Request.INTERACTIVE_FORMATS:

                # How many records per page?
                if s3.dataTable_pageLength:
                    display_length = s3.dataTable_pageLength
                else:
                    display_length = 25

                # Server-side pagination?
                if not s3.no_sspag:
                    dt_pagination = "true"
                    if not limit:
                        limit = 2 * display_length
                    session.s3.filter = get_vars
                    if orderby is None:
                        dt_sorting = {"iSortingCols": "1",
                                      "sSortDir_0": "asc"
                                      }

                        if len(list_fields) > 1:
                            dt_sorting["bSortable_0"] = "false"
                            dt_sorting["iSortCol_0"] = "1"
                        else:
                            dt_sorting["bSortable_0"] = "true"
                            dt_sorting["iSortCol_0"] = "0"

                        orderby, left = resource.datatable_filter(list_fields,
                                                                  dt_sorting,
                                                                  )[1:3]
                else:
                    dt_pagination = "false"

                # Disable exports
                s3.no_formats = True

                # Get the data table
                dt, totalrows = resource.datatable(fields = list_fields,
                                                   start = start,
                                                   limit = limit,
                                                   left = left,
                                                   orderby = orderby,
                                                   distinct = distinct,
                                                   )
                displayrows = totalrows

                # Always show table, otherwise it can't be Ajax-filtered
                # @todo: need a better algorithm to determine total_rows
                #        (which excludes URL filters), so that datatables
                #        shows the right empty-message (ZeroRecords instead
                #        of EmptyTable)
                dtargs["dt_pagination"] = dt_pagination
                dtargs["dt_pageLength"] = display_length
                dtargs["dt_base_url"] = URL(c="default", f="index", args="approve_org")
                dtargs["dt_permalink"] = URL(c="default", f="index", args="approve_org")
                datatable = dt.html(totalrows,
                                    displayrows,
                                    id = list_id,
                                    **dtargs)

                # Action Buttons
                s3.actions = [{"label": s3_str(T("Review")),
                               "url": URL(args = ["approve_org", "[id]"],
                                          ),
                               "_class": "action-btn",
                               },
                              ]

                output = {"items": datatable,
                          "title": T("Organizations to be Approved"),
                          }

                # Custom View
                self._view(TEMPLATE, "approve_list.html")

            elif representation == "aadata":

                # Apply datatable filters
                searchq, orderby, left = resource.datatable_filter(list_fields,
                                                                   get_vars)
                if searchq is not None:
                    totalrows = resource.count()
                    resource.add_filter(searchq)
                else:
                    totalrows = None

                # Get a data table
                if totalrows != 0:
                    dt, displayrows = resource.datatable(fields = list_fields,
                                                         start = start,
                                                         limit = limit,
                                                         left = left,
                                                         orderby = orderby,
                                                         distinct = distinct,
                                                         )
                else:
                    dt, displayrows = None, 0
                if totalrows is None:
                    totalrows = displayrows

                # Echo
                draw = int(get_vars.get("draw", 0))

                # Representation
                if dt is not None:
                    output = dt.json(totalrows,
                                     displayrows,
                                     list_id,
                                     draw,
                                     **dtargs)
                else:
                    output = '{"recordsTotal":%s,' \
                             '"recordsFiltered":0,' \
                             '"dataTable_id":"%s",' \
                             '"draw":%s,' \
                             '"data":[]}' % (totalrows, list_id, draw)
            else:
                S3Request("auth", "user").error(415, current.ERROR.BAD_FORMAT)

        return output

# END =========================================================================
