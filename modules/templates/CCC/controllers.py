# -*- coding: utf-8 -*-

import uuid

from gluon import *
from s3 import S3CustomController, s3_mark_required

THEME = "CCC"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        if current.deployment_settings.has_module("cms"):
            system_roles = current.auth.get_system_roles()
            ADMIN = system_roles.ADMIN in current.session.s3.roles
            s3db = current.s3db
            table = s3db.cms_post
            ltable = s3db.cms_post_module
            module = "default"
            resource = "index"
            query = (ltable.module == module) & \
                    ((ltable.resource == None) | \
                     (ltable.resource == resource)) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            item = current.db(query).select(table.body,
                                            table.id,
                                            limitby=(0, 1)).first()
            if item:
                if ADMIN:
                    item = DIV(XML(item.body),
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
                    item = DIV(XML(item.body))
            elif ADMIN:
                if current.response.s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                item = A(current.T("Edit"),
                         _href = URL(c="cms", f="post", args="create",
                                     vars = {"module": module,
                                             "resource": resource,
                                             },
                                     ),
                         _class="%s cms-edit" % _class,
                         )
            else:
                item = ""
        else:
            item = ""
        output["item"] = item

        self._view(THEME, "index.html")
        return output

# =============================================================================
class register(S3CustomController):
    """ Custom Registration Page """

    def __call__(self):

        auth = current.auth
        auth_settings = auth.settings

        # Redirect if already logged-in
        if auth.is_logged_in():
            redirect(auth_settings.logged_url)

        T = current.T
        db = current.db
        s3db = current.s3db

        request = current.request
        response = current.response
        session = current.session
        settings = current.deployment_settings

        auth_messages = auth.messages

        utable = auth_settings.table_user
        passfield = auth_settings.password_field

        # Check Type of Registration
        individual = group = existing = False

        get_vars_get = current.request.get_vars.get
        if get_vars_get("individual"):
            # Individual Volunteer
            individual = True
            title = T("Register as a Volunteer")
            header = ""
            f = utable.organisation_id
            f.readable = f.writable = False

        elif get_vars_get("group"):
            # Volunteer Group
            group = True
            title = T("Register as a Volunteer Group")
            header = ""
            f = utable.organisation_id
            f.readable = f.writable = False

        elif get_vars_get("existing"):
            # Volunteer for Existing Organisation
            existing = True
            title = T("Register as a Volunteer for an existing Organisation")
            header = ""
            # Cannot create a new Org here
            f = utable.organisation_id
            f.comment = None
            # @ToDo: Filter dropdown to just those who are accepting volunteers

        else:
            # Organisation or Agency
            title = T("Register as an Organisation or Agency")
            header = P("This is for known CEP/Flood Action Group etc based within Cumbria. Please use ",
                       A("Volunteer Group", _href=URL(args="register", vars={"group": 1})),
                       " if you do not fall into these",
                       )
            # @ToDo: Filter dropdown to just those who are accepting volunteers
            #f = utable.organisation_id
            #f.comment = None
            # @ToDo: Filter out all existing Orgs, ut allow creation of new one
            #f.requires = IS_ONE_OF()


        # Instantiate Consent Tracker
        # TODO: limit to relevant data processing types
        consent = s3db.auth_Consent()

        # Form Fields

        #mobile_label = settings.get_ui_label_mobile_phone()

        gtable = s3db.gis_location
        districts = db((gtable.level == "L2") & (gtable.L1 == "Cumbria")).select(gtable.id,
                                                                                 gtable.name)
        districts = {d.id:d.name for d in districts}

        formfields = [utable.first_name,
                      utable.last_name,
                      utable.organisation_id,
                      Field("addr_L2",
                            label = T("Where Based (District)"),
                            requires = IS_IN_SET(districts),
                            ),
                      Field("addr_street",
                            label = T("Street Address"),
                            ),
                      Field("addr_postcode",
                            label = T("Postcode"),
                            ),
                      Field("mobile",
                            label = T("Contact Number (Preferred)"),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                              T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                          ),
                            ),
                      Field("home_phone",
                            label = T("Contact Number (Secondary)"),
                            ),
                      utable.email,
                      utable[passfield],
                      # Password Verification Field
                      Field("password_two", "password",
                            label = auth_messages.verify_password,
                            requires = IS_EXPR("value==%s" % \
                                               repr(request.vars.get(passfield)),
                                               error_message = auth_messages.mismatched_password,
                                               ),
                            ),
                      # Consent Question
                      Field("consent",
                            label = T("Consent"),
                            widget = consent.widget,
                            ),
                      ]

        # Generate labels (and mark required fields in the process)
        required_fields = ["first_name",
                           "last_name",
                           "addr_street",
                           "addr_postcode",
                           "mobile",
                           ]
        labels = s3_mark_required(formfields, mark_required=required_fields)[0]

        # Form buttons
        REGISTER = T("Register")
        buttons = [INPUT(_type="submit", _value=REGISTER),
                   A(T("Login"),
                     _href=URL(f="user", args="login"),
                     _id="login-btn",
                     _class="action-lnk",
                     ),
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

        # Inject client-side Validation
        auth.s3_register_validation()

        # Captcha, if configured
        #if auth_settings.captcha != None:
        #    form[0].insert(-1, DIV("", auth_settings.captcha, ""))

        # Set default registration key, so new users are prevented
        # from logging in until approved
        utable.registration_key.default = key = str(uuid.uuid4())

        if form.accepts(request.vars,
                        session,
                        formname = "register",
                        onvalidation = auth_settings.register_onvalidation,
                        ):

            # Create the user record
            user_id = utable.insert(**utable._filter_fields(form.vars, id=False))
            form.vars.id = user_id

            # Save temporary user fields
            auth.s3_user_register_onaccept(form)

            # Where to go next?
            register_next = request.vars._next or auth_settings.register_next

            # Post-process the new user record
            users = db(utable.id > 0).select(utable.id, limitby=(0, 2))
            if len(users) == 1:
                # 1st user to register doesn't need verification/approval
                auth.s3_approve_user(form.vars)
                current.session.confirmation = auth_messages.registration_successful

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
                auth.s3_send_welcome_email(form.vars)

            elif auth_settings.registration_requires_verification:
                # System Details for Verification Email
                system = {"system_name": settings.get_system_name(),
                          "url": "%s/default/user/verify_email/%s" % (response.s3.base_url, key),
                          }

                # Try to send the Verification Email
                if not auth_settings.mailer or \
                   not auth_settings.mailer.settings.server or \
                   not auth_settings.mailer.send(to = form.vars.email,
                                                 subject = auth_messages.verify_email_subject % system,
                                                 message = auth_messages.verify_email % system,
                                                 ):
                    response.error = auth_messages.email_verification_failed
                    return form

                # Redirect to Verification Info page
                register_next = URL(c = "default",
                                    f = "message",
                                    args = ["verify_email_sent"],
                                    vars = {"email": form.vars.email},
                                    )

            else:
                # Does the user need to be approved?
                approved = auth.s3_verify_user(form.vars)

                if approved:
                    # Log them in
                    if "language" not in form.vars:
                        # Was missing from login form
                        form.vars.language = T.accepted_language
                    user = Storage(utable._filter_fields(form.vars, id=True))
                    auth.login_user(user)

            # Set a Cookie to present user with login box by default
            #auth.set_cookie()

            # Log action
            log = auth_messages.register_log
            if log:
                auth.log_event(log, form.vars)

            # Run onaccept for registration form
            onaccept = auth_settings.register_onaccept
            if onaccept:
                onaccept(form)

            # Redirect
            if not register_next:
                register_next = auth.url(args = request.args)
            elif isinstance(register_next, (list, tuple)):
                # fix issue with 2.6
                register_next = register_next[0]
            elif register_next and not register_next[0] == "/" and register_next[:4] != "http":
                register_next = auth.url(register_next.replace("[id]", str(form.vars.id)))
            redirect(register_next)

        # Custom View
        self._view(THEME, "register.html")

        return {"title": title,
                "header": header,
                "form": form,
                }

# END =========================================================================
