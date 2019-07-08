# -*- coding: utf-8 -*-

import uuid

from gluon import *
from s3 import IS_ONE_OF, S3CustomController, S3MultiSelectWidget, s3_mark_required

THEME = "CCC"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
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
        output["item"] = item

        self._view(THEME, "index.html")
        return output

# =============================================================================
class donate(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        system_roles = current.auth.get_system_roles()
        ADMIN = system_roles.ADMIN in current.session.s3.roles
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"

        resource = "Donate1"
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby=(0, 1)).first()
        if item:
            if ADMIN:
                item1 = DIV(XML(item.body),
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
                item1 = DIV(XML(item.body))
        elif ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item1 = A(current.T("Edit"),
                       _href = URL(c="cms", f="post", args="create",
                                  vars = {"module": module,
                                          "resource": resource,
                                          },
                                  ),
                      _class="%s cms-edit" % _class,
                      )
        else:
            item1 = ""
        output["item1"] = item1

        resource = "Donate2"
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby=(0, 1)).first()
        if item:
            if ADMIN:
                item2 = DIV(XML(item.body),
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
                item2 = DIV(XML(item.body))
        elif ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item2 = A(current.T("Edit"),
                     _href = URL(c="cms", f="post", args="create",
                                 vars = {"module": module,
                                         "resource": resource,
                                         },
                                 ),
                     _class="%s cms-edit" % _class,
                     )
        else:
            item2 = ""
        output["item2"] = item2

        resource = "Donate3"
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby=(0, 1)).first()
        if item:
            if ADMIN:
                item3 = DIV(XML(item.body),
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
                item3 = DIV(XML(item.body))
        elif ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item3 = A(current.T("Edit"),
                      _href = URL(c="cms", f="post", args="create",
                                  vars = {"module": module,
                                          "resource": resource,
                                          },
                                  ),
                      _class="%s cms-edit" % _class,
                      )
        else:
            item3 = ""
        output["item3"] = item3

        self._view(THEME, "donate.html")
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

        # Instantiate Consent Tracker
        # TODO: limit to relevant data processing types
        consent = s3db.auth_Consent()

        # Lookup Lists
        gtable = s3db.gis_location
        districts = db((gtable.level == "L2") & (gtable.L1 == "Cumbria")).select(gtable.id,
                                                                                 gtable.name)
        districts = {d.id:d.name for d in districts}

        # Check Type of Registration
        agency = existing = individual = group = donor = False

        def individual_formfields():
            """
                DRY Helper for individuals (whether with existing agency or not)
            """
            formfields = [utable.first_name,
                          utable.last_name,
                          Field("addr_L2",
                                label = T("Where Based (District)"),
                                requires = IS_EMPTY_OR(IS_IN_SET(districts)),
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
                          
                          # Skills
                          s3db.hrm_multi_skill_id(empty = False,
                                                  label = T("Volunteer Offer"),
                                                  ),
                          Field("skills_other",
                                label = T("If Other, please specify"),
                                ),
                          Field("free", "boolean",
                                label = T("Offering to Volunteer Free of Charge?"),
                                ),
                          Field("where_operate", "list:string",
                                label = T("Where would you be willing to operate?"),
                                requires = IS_EMPTY_OR(IS_IN_SET(districts, multiple=True)),
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("disability", "boolean",
                                label = T("Do you consider yourself to have a disability, illness or injury which could prevent you from carrying out particular tasks?"),
                                ),
                          Field("health", "boolean",
                                label = T("Do you have any significant health or medical requirements?"),
                                comment = T("such as asthma, allergies, diabetes, heart condition"),
                                ),
                          Field("emergency_contact",
                                label = T("Person to be contacted in case of an emergency"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("convicted", "boolean",
                                label = T("Have you ever been convicted of a criminal offence?"),
                                ),
                          Field("pending_prosecutions", "boolean",
                                label = T("Have you any prosecutions pending?"),
                                ),
                          # GDPR Consent
                          Field("consent",
                                label = T("Consent"),
                                widget = consent.widget,
                                ),
                          ]

            required_fields = ["first_name",
                               "last_name",
                               "addr_street",
                               "addr_postcode",
                               "mobile",
                               "free",
                               "disability",
                               "health",
                               "emergency_contact",
                               "convicted",
                               "pending_prosecutions",
                               ]

            return formfields, required_fields

        get_vars_get = current.request.get_vars.get
        org = get_vars_get("org")
        if org:
            # Volunteer for Existing Organisation
            existing = True
            otable = s3db.org_organisation
            row = db(otable.id == org).select(otable.name,
                                              limitby = (0, 1)
                                              ).first()
            if not row:
                current.session.error = T("Organization not found")
                redirect(URL(vars={}))
            title = T("Register as a Volunteer for %(org)s") % {"org": row.name}
            header = ""
            utable.organisation_id.default = org

            # Form Fields
            formfields, required_fields = individual_formfields()
            
        elif get_vars_get("agency"):
            # Organisation or Agency
            agency = True
            title = T("Register as an Organization or Agency")
            header = P("This is for known CEP/Flood Action Group etc based within Cumbria. Please use ",
                       A("Volunteer Group", _href=URL(args="register", vars={"vol_group": 1})),
                       " if you do not fall into these",
                       )

            # Form Fields
            formfields = [Field("organisation",
                                label = T("Organization Name"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          s3db.org_organisation_type_id(),
                          Field("addr_L2",
                                label = T("Where Based (District)"),
                                requires = IS_EMPTY_OR(IS_IN_SET(districts)),
                                ),
                          Field("addr_street",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode",
                                label = T("Postcode"),
                                ),
                          # Group Leader 1
                          utable.first_name,
                          utable.last_name,
                          Field("addr_street1",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode1",
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
                          # Group Leader 2
                          Field("first_name2",
                                label = T("First Name"),
                                ),
                          Field("last_name2",
                                label = T("Last Name"),
                                ),
                          Field("addr_street2",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode2",
                                label = T("Postcode"),
                                ),
                          Field("email2",
                                label = T("Email"),
                                requires = IS_EMPTY_OR(IS_EMAIL()),
                                ),
                          Field("mobile2",
                                label = T("Contact Number (Preferred)"),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                                  T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                              ),
                                ),
                          Field("home_phone2",
                                label = T("Contact Number (Secondary)"),
                                ),
                          # GDPR Consent
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
                               "free",
                               "disability",
                               "health",
                               "emergency_contact",
                               "convicted",
                               "pending_prosecutions",
                               ]

        elif get_vars_get("donor"):
            # Donor
            donor = True
            title = T("Register as a Donor")
            header = P("This is to register to Donate Goods / Services. If instead you wish to Volunteer your time, please ",
                       A("Register as a Volunteer", _href=URL(args="register", vars={})),
                       )

            # Form Fields
            formfields = [utable.first_name,
                          utable.last_name,
                          Field("organisation",
                                label = T("Name of Organization"),
                                ),
                          Field("addr_L2",
                                label = T("Where Based (District)"),
                                requires = IS_EMPTY_OR(IS_IN_SET(districts)),
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
                          Field("work_phone",
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
                          
                          # Goods / Services
                          Field("item_id", "list:reference supply_item",
                                label = T("Goods/ Services"),
                                ondelete = "SET NULL",
                                represent = s3db.supply_ItemRepresent(multiple=True),
                                requires = IS_ONE_OF(db, "supply_item.id",
                                                     s3db.supply_item_represent,
                                                     sort=True,
                                                     multiple=True
                                                     ),
                                sortby = "name",
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("items_other",
                                label = T("If Other, please specify"),
                                ),
                          Field("free", "boolean",
                                label = T("Is the offer Free of Charge?"),
                                ),
                          Field("delivery",
                                label = T("Delivery Options?"),
                                ),
                          Field("availability",
                                label = T("Length or time the offer is available?"),
                                ),
                          # GDPR Consent
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
                               "free",
                               "delivery",
                               "availability",
                               ]

        elif get_vars_get("vol_group"): # Can't be just 'group' without causing issues in HRM
            # Volunteer Group
            group = True
            title = T("Register as a Volunteer Group")
            header = P("This is for an established group from outside of Cumbria. If you are a known CEP/Flood Action Group etc based within Cumbria, please use ",
                       A("Organisation or Agency", _href=URL(args="register", vars={"agency": 1})),
                       )

            # Form Fields
            formfields = [Field("group",
                                label = T("Group Name"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          # Group Leader 1
                          utable.first_name,
                          utable.last_name,
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
                          # Group Leader 2
                          Field("first_name2",
                                label = T("First Name"),
                                ),
                          Field("last_name2",
                                label = T("Last Name"),
                                ),
                          Field("addr_street2",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode2",
                                label = T("Postcode"),
                                ),
                          Field("email2",
                                label = T("Email"),
                                requires = IS_EMPTY_OR(IS_EMAIL()),
                                ),
                          Field("mobile2",
                                label = T("Contact Number (Preferred)"),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                                  T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                              ),
                                ),
                          Field("home_phone2",
                                label = T("Contact Number (Secondary)"),
                                ),
                          Field("L2",
                                label = T("Where Based (District)"),
                                requires = IS_EMPTY_OR(IS_IN_SET(districts)),
                                ),
                          Field("vols", "integer",
                                label = T("Approximate Number of Volunteers"),
                                requires = IS_INT_IN_RANGE(1, 999),
                                ),
                          Field("transport",
                                label = T("Mode of Transport"),
                                comment = T("access can be an issue"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          # Skills
                          s3db.hrm_multi_skill_id(empty = False,
                                                  label = T("Volunteer Offer"),
                                                  ),
                          Field("skills_other",
                                label = T("If Other, please specify"),
                                ),
                          Field("free", "boolean",
                                label = T("Offering to Volunteer Free of Charge?"),
                                ),
                          Field("where_operate", "list:string",
                                label = T("Where would you be willing to operate?"),
                                requires = IS_EMPTY_OR(IS_IN_SET(districts, multiple=True)),
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("emergency_contact",
                                label = T("Person to be contacted in case of an emergency"),
                                comment = T("Contact must not be listed as a leader above"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          # GDPR Consent
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
                               "free",
                               ]

        else:
            # Individual Volunteer
            individual = True
            title = T("Register as a Volunteer")
            header = P("Please use ",
                       A("Volunteer Group", _href=URL(args="register", vars={"vol_group": 1})),
                       " if you are an established group.",
                       )

            # Form Fields
            formfields, required_fields = individual_formfields()

        # Generate labels (and mark required fields in the process)
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

        # Captcha, if configured
        #if auth_settings.captcha != None:
        #    form[0].insert(-1, DIV("", auth_settings.captcha, ""))

        # Identify form for CSS & JS Validation
        form.add_class("auth_register")

        if agency:
            # Add Subheadings
            form[0].insert(5, DIV("Group Leader 1",
                                  _class = "subheading",
                                  ))
            form[0].insert(15, DIV("Group Leader 2",
                                   _class = "subheading",
                                   ))

        elif group:
            # Add Subheadings
            form[0].insert(1, DIV("Group Leader 1",
                                  _class = "subheading",
                                  ))
            form[0].insert(11, DIV("Group Leader 2",
                                   _class = "subheading",
                                   ))

        # Inject client-side Validation
        auth.s3_register_validation()

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

# =============================================================================
class volunteer(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        system_roles = current.auth.get_system_roles()
        ADMIN = system_roles.ADMIN in current.session.s3.roles
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"

        resource = "Volunteer1"
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby=(0, 1)).first()
        if item:
            if ADMIN:
                item1 = DIV(XML(item.body),
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
                item1 = DIV(XML(item.body))
        elif ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item1 = A(current.T("Edit"),
                      _href = URL(c="cms", f="post", args="create",
                                  vars = {"module": module,
                                          "resource": resource,
                                          },
                                  ),
                      _class="%s cms-edit" % _class,
                      )
        else:
            item1 = ""
        output["item1"] = item1

        resource = "Volunteer2"
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        item = current.db(query).select(table.body,
                                        table.id,
                                        limitby=(0, 1)).first()
        if item:
            if ADMIN:
                item2 = DIV(XML(item.body),
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
                item2 = DIV(XML(item.body))
        elif ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item2 = A(current.T("Edit"),
                      _href = URL(c="cms", f="post", args="create",
                                  vars = {"module": module,
                                          "resource": resource,
                                          },
                                  ),
                      _class="%s cms-edit" % _class,
                      )
        else:
            item2 = ""
        output["item2"] = item2

        self._view(THEME, "volunteer.html")
        return output

# END =========================================================================
