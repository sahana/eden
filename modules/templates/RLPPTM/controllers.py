# -*- coding: utf-8 -*-

import json
from uuid import uuid4

from gluon import A, BR, CRYPT, DIV, Field, H3, INPUT, \
                  IS_EMAIL, IS_EMPTY_OR, IS_EXPR, IS_INT_IN_RANGE, IS_IN_SET, \
                  IS_LENGTH, IS_LOWER, IS_NOT_EMPTY, IS_NOT_IN_DB, \
                  P, SQLFORM, URL, XML, current, redirect
from gluon.storage import Storage

from s3 import IS_ONE_OF, IS_PHONE_NUMBER_MULTI, IS_PHONE_NUMBER_SINGLE, \
               JSONERRORS, S3CustomController, S3GroupedOptionsWidget, \
               S3LocationSelector, S3MultiSelectWidget, S3WeeklyHoursWidget, \
               S3WithIntro, S3Represent, \
               s3_comments_widget, s3_date, s3_mark_required, s3_str

from .notifications import formatmap

THEME = "RLP"

DEFAULT_POOL = "Weitere Freiwillige"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T
        request = current.request
        response = current.response
        s3 = response.s3

        # Check logged in and permissions
        auth = current.auth
        settings = current.deployment_settings
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        AUTHENTICATED = system_roles.AUTHENTICATED

        # Login/Registration forms
        self_registration = current.deployment_settings.get_security_registration_visible()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None

        if AUTHENTICATED not in roles:

            login_buttons = DIV(A(T("Login"),
                                  _id = "show-login",
                                  _class = "tiny secondary button"),
                                _id = "login-buttons"
                                )
            script = '''
$('#show-mailform').click(function(e){
 e.preventDefault()
 $('#intro').slideDown(400, function() {
   $('#login_box').hide()
 });
})
$('#show-login').click(function(e){
 e.preventDefault()
 $('#login_form').show()
 $('#register_form').hide()
 $('#login_box').show()
 $('#intro').slideUp()
})'''
            s3.jquery_ready.append(script)

            # This user isn't yet logged-in
            if "registered" in request.cookies:
                # This browser has logged-in before
                registered = True

            if self_registration is True:
                # Provide a Registration box on front page
                login_buttons.append(A(T("Register"),
                                       _id = "show-register",
                                       _class = "tiny secondary button",
                                       _style = "margin-left:5px"))
                script = '''
$('#show-register').click(function(e){
 e.preventDefault()
 $('#login_form').hide()
 $('#register_form').show()
 $('#login_box').show()
 $('#intro').slideUp()
})'''
                s3.jquery_ready.append(script)

                register_form = auth.register()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to help, then please <b>sign up now</b>"))))
                register_script = '''
$('#register-btn').click(function(e){
 e.preventDefault()
 $('#register_form').show()
 $('#login_form').hide()
})
$('#login-btn').click(function(e){
 e.preventDefault()
 $('#register_form').hide()
 $('#login_form').show()
})'''
                s3.jquery_ready.append(register_script)

            # Provide a login box on front page
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)
            login_div = DIV(H3(T("Login")),
                            #P(XML(T("Registered users can <b>login</b> to access the system"))),
                            )
        else:
            login_buttons = ""

        output["login_buttons"] = login_buttons
        output["self_registration"] = self_registration
        output["registered"] = registered
        output["login_div"] = login_div
        output["login_form"] = login_form
        output["register_div"] = register_div
        output["register_form"] = register_form

        s3.stylesheets.append("../themes/%s/homepage.css" % THEME)
        self._view(settings.get_theme_layouts(), "index.html")

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

        self._view(THEME, "cmspage.html")
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

        self._view(THEME, "cmspage.html")
        return output

# =============================================================================
class register(S3CustomController):
    """ Custom Registration Page """

    def __call__(self):

        auth = current.auth

        # Redirect if already logged-in
        if auth.s3_logged_in():
            redirect(URL(c="default", f="index"))

        auth_settings = auth.settings
        auth_messages = auth.messages
        self.customise_auth_messages()

        T = current.T
        db = current.db
        s3db = current.s3db

        request = current.request
        response = current.response
        session = current.session
        settings = current.deployment_settings

        utable = auth_settings.table_user

        # Page title and intro text
        title = T("Volunteer Registration")

        # Get intro text from CMS
        db = current.db
        s3db = current.s3db

        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                        (ltable.module == "auth") & \
                        (ltable.resource == "user") & \
                        (ltable.deleted == False))

        query = (ctable.name == "SelfRegistrationIntro") & \
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
        labels["skill_id"] = DIV(labels["skill_id"],
                                 DIV("(%s)" % T("Select all that apply"),
                                     _class="sub-label",
                                     ),
                                 )

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
        utable.registration_key.default = self.keyhash(key, code)

        if form.accepts(request.vars,
                        session,
                        formname = "register",
                        onvalidation = auth_settings.register_onvalidation,
                        ):

            formvars = form.vars

            # Add default organisation
            organisation_id = formvars.get("organisation_id")
            if not organisation_id:
                formvars["organisation_id"] = settings.get_org_default_organisation

            # Add HR type
            link_user_to = formvars.get("link_user_to")
            if link_user_to is None:
                formvars["link_user_to"] = ["volunteer"]

            # Create the user record
            user_id = utable.insert(**utable._filter_fields(formvars, id=False))
            formvars.id = user_id

            # Save temporary user fields in s3db.auth_user_temp
            temptable = s3db.auth_user_temp
            record  = {"user_id": user_id}

            mobile = formvars.mobile_phone
            if mobile:
                record["mobile"] = mobile

            record["consent"] = formvars.consent

            # Store Custom fields
            custom = {#"date_of_birth": formvars.date_of_birth,
                      "home_phone": formvars.home_phone,
                      #"office_phone": formvars.office_phone,
                      "location_id": formvars.location_id,
                      "addr_street": formvars.addr_street,
                      "addr_postcode": formvars.addr_postcode,
                      "occupation_type_ids": formvars.occupation_type_ids,
                      "occupation": formvars.occupation,
                      #"start_date": formvars.start_date,
                      #"end_date": formvars.end_date,
                      "hours_per_week": formvars.hours_per_week,
                      "schedule_json": formvars.schedule_json,
                      "availability_sites": formvars.availability_sites,
                      "availability_comments": formvars.availability_comments,
                      "skill_id": formvars.skill_id,
                      "comments": formvars.comments,
                      }
            for datefield in ("date_of_birth", "start_date", "end_date"):
                value = formvars.get(datefield)
                if value:
                    value = value.isoformat()
                    custom[datefield] = value
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
                auth.s3_send_welcome_email(form.vars)

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
                          #"url": "%s/default/index/verify_email/%s" % (response.s3.base_url, key),
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
    @staticmethod
    def formfields():
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

        db = current.db
        s3db = current.s3db

        auth = current.auth
        auth_settings = auth.settings
        auth_messages = auth.messages

        utable = auth_settings.table_user
        passfield = auth_settings.password_field

        occupation_type_represent = S3Represent(lookup = "pr_occupation_type",
                                                multiple = True,
                                                )

        # Instantiate Consent Tracker
        consent = s3db.auth_Consent(processing_types=["SHARE"])

        # Last name is required
        utable.last_name.requires = IS_NOT_EMPTY(error_message=T("input required"))

        ltable = s3db.gis_location

        # Form fields
        formfields = [utable.first_name,
                      utable.last_name,
                      s3_date("date_of_birth",
                              label = T("Date of Birth"),
                              future = -156,
                              empty = False,
                              ),
                      # --------------------------------------------
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
                      # --------------------------------------------
                      Field("home_phone",
                            label = T("Phone"),
                            requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                            ),
                      Field("mobile_phone",
                            label = T("Mobile Phone"),
                            requires = IS_EMPTY_OR(IS_PHONE_NUMBER_SINGLE()),
                            ),
                      #Field("office_phone",
                      #      label = T("Office Phone"),
                      #      requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                      #      ),
                      # --------------------------------------------
                      s3db.gis_location_id("location_id",
                                           widget = S3LocationSelector(
                                                       levels = ("L1", "L2", "L3"),
                                                       required_levels = ("L1", "L2", "L3"),
                                                       show_address = False,
                                                       show_postcode = False,
                                                       show_map = False,
                                                       ),
                                           ),
                      Field("addr_street",
                            label = ltable.addr_street.label,
                            ),
                      Field("addr_postcode",
                            label = ltable.addr_postcode.label,
                            requires = IS_NOT_EMPTY(),
                            ),

                      # --------------------------------------------
                      Field("occupation_type_ids",
                            "list:reference pr_occupation_type",
                            label = T("Occupation Type"),
                            requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                          "pr_occupation_type.id",
                                          occupation_type_represent,
                                          multiple=True,
                                          )),
                            represent = occupation_type_represent,
                            widget = S3MultiSelectWidget(),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Occupation Type"),
                                                              T("Select all that apply"),
                                                              ),
                                          ),
                            ),
                      Field("occupation",
                            label = T("Occupation / Speciality"),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Occupation / Speciality"),
                                                              T("Specify your exact job designation (max 128 characters)"),
                                                              ),
                                          ),
                            requires = IS_EMPTY_OR(IS_LENGTH(128)),
                            ),

                      # --------------------------------------------
                      s3_date("start_date",
                              label = T("Available from"),
                              default = "now",
                              past = 0,
                              set_min = "#auth_user_start_date",
                              ),
                      s3_date("end_date",
                              label = T("Available until"),
                              past = 0,
                              set_max = "#auth_user_start_date",
                              ),
                      Field("hours_per_week", "integer",
                            label = T("Hours per Week"),
                            requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1, 60)),
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Hours per Week"),
                                                              T("Specify the maximum number of weekly hours"),
                                                              ),
                                          ),
                            ),
                      Field("schedule_json", "json",
                            label = T("Availability Schedule"),
                            widget = S3WithIntro(
                                        S3WeeklyHoursWidget(),
                                        # Widget intro from CMS
                                        intro = ("pr",
                                                 "person_availability",
                                                 "HoursMatrixIntro",
                                                 ),
                                        ),
                            ),
                      Field("availability_sites", "list:integer",
                            label = T("Possible Deployment Sites"),
                            requires = IS_EMPTY_OR(IS_IN_SET({}, #rlp_deployment_sites(),
                                                             multiple = True,
                                                             sort = False,
                                                             )),
                            widget = S3WithIntro(
                                        S3MultiSelectWidget(),
                                        # Widget intro from CMS
                                        intro = ("pr",
                                                 "person_availability_site",
                                                 "AvailabilitySitesIntro",
                                                 ),
                                        ),
                            ),
                      Field("availability_comments", "text",
                            label = T("Availability Comments"),
                            widget = s3_comments_widget,
                            comment = DIV(_class = "tooltip",
                                          _title = "%s|%s" % (T("Availability Comments"),
                                                              T("Use this field to indicate e.g. vacation dates or other information with regard to your availability to facilitate personnel planning"),
                                                              ),
                                         ),
                            ),
                      s3db.hrm_multi_skill_id(
                            label = T("Skills / Resources"),
                            widget = S3GroupedOptionsWidget(cols = 1,
                                                            size = None,
                                                            help_field = "comments",
                                                            ),
                            ),

                      # --------------------------------------------
                      Field("comments", "text",
                            label = T("Comments"),
                            widget = s3_comments_widget,
                            ),

                      # --------------------------------------------
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
        subheadings = ((3, T("User Account")),
                       (6, T("Contact Information")),
                       (8, T("Address")),
                       (11, T("Occupation")),
                       (13, T("Availability and Resources")),
                       (20, T("Comments")),
                       (21, T("Privacy")),
                       )

        # Geocoder
        # @ToDo: Either move Address into LocationSelector or make a variant of geocoder.js to match these IDs
        #s3 = current.response.s3
        #s3.scripts.append("/%s/static/themes/RLP/js/geocoder.js" % r.application)
        #s3.jquery_ready.append('''S3.rlp_GeoCoder("pr_address_location_id")''')
        #s3.js_global.append('''i18n.location_found="%s"
#i18n.location_not_found="%s"''' % (T("Location Found"),
        #                           T("Location NOT Found"),
        #                           ))

        return formfields, required_fields, subheadings

    # -------------------------------------------------------------------------
    @staticmethod
    def get_default_pool():
        """
            Get the record ID of the default volunteer pool

            @returns: the pr_group.id of the default pool
        """

        s3db = current.s3db
        auth = current.auth

        gtable = s3db.pr_group
        query = (gtable.name == DEFAULT_POOL) & \
                (gtable.group_type.belongs(21, 22)) & \
                (gtable.deleted == False)
        row = current.db(query).select(gtable.id,
                                       limitby = (0, 1),
                                       ).first()
        if not row:
            pool = {"name": DEFAULT_POOL, "group_type": 21}
            pool_id = pool["id"] = gtable.insert(**pool)
            s3db.update_super(gtable, pool)
            auth.s3_set_record_owner(gtable, pool)
            s3db.onaccept(gtable, pool, method="create")

            # Link pool to default organisation
            default_org = current.deployment_settings.get_org_default_organisation()
            if default_org:
                ltable = s3db.org_organisation_team
                link = {"organisation_id": default_org,
                        "group_id": pool_id,
                        }
                link["id"] = ltable.insert(**link)
                auth.s3_set_record_owner(ltable, link)
                s3db.onaccept(ltable, link, method="create")
        else:
            pool_id = row.id

        return pool_id

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

        # Customise resources
        from s3 import S3Request
        r = S3Request("auth", "user", args=[], get_vars={})
        customise_resource = current.deployment_settings.customise_resource
        for tablename in ("pr_person", "pr_group", "pr_group_membership"):
            customise = customise_resource(tablename)
            if customise:
                customise(r, tablename)

        try:
            custom = json.loads(record.custom)
        except JSONERRORS:
            return

        auth = current.auth
        set_record_owner = auth.s3_set_record_owner
        s3db_onaccept = s3db.onaccept

        parse_date = current.calendar.parse_date

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
                                  ptable.first_name,
                                  ptable.middle_name,
                                  ptable.last_name,
                                  limitby = (0, 1),
                                  ).first()
        if not person:
            current.log.error("Person record for user %s not found" % user_id)
            return
        person_id = person.id

        # Update person record
        person_update = {}
        dob = custom.get("date_of_birth")
        if dob:
            person_update["date_of_birth"] = parse_date(dob)
        if not person.pe_label:
            person_update["pe_label"] = "S-%07d" % person_id
        if person_update:
            person.update_record(**person_update)
            person_update["id"] = person_id
        set_record_owner(ptable, person_id, force_update=True)
        if person_update:
            s3db_onaccept(ptable, person_update, method="update")

        # Add/update person details
        details_update = {}
        occupation = custom.get("occupation")
        if occupation:
            details_update["occupation"] = occupation
        if details_update:
            dtable = s3db.pr_person_details
            query = (dtable.person_id == person_id) & \
                    (dtable.deleted == False)
            details = db(query).select(dtable.id,
                                       limitby = (0, 1),
                                       ).first()
            if details:
                details.update_record(**details_update)
                details_update["id"] = details.id
                s3db_onaccept(dtable, details_update, method="update")
            else:
                details_update["person_id"] = person_id
                details_update["id"] = dtable.insert(**details_update)
                set_record_owner(dtable, details_update)
                s3db_onaccept(dtable, details_update, method="create")

        # Link to occupation_types
        occupation_types = custom.get("occupation_type_ids")
        if occupation_types:
            occupation_types = set(occupation_types)
        else:
            occupation_types = set()
        ltable = s3db.pr_occupation_type_person
        query = (ltable.person_id == person_id) & \
                (ltable.deleted == False)
        links = db(query).select(ltable.occupation_type_id)
        linked = set(link.occupation_type_id for link in links)
        rmv = linked - occupation_types
        if rmv:
            db(query & ltable.occupation_type_id.belongs(rmv)).delete()
        for occupation_type_id in (occupation_types - linked):
            link = {"person_id": person_id,
                    "occupation_type_id": occupation_type_id,
                    }
            link["id"] = ltable.insert(**link)
            set_record_owner(ltable, link, owned_by_user=user_id)
            s3db_onaccept(ltable, link, method="create")

        # Register address
        addr_street = custom.get("addr_street")
        addr_postcode = custom.get("addr_postcode")
        location_id = custom.get("location_id")
        if addr_street or addr_postcode:
            # Generate individual location
            ltable = s3db.gis_location
            location = Storage(addr_street = addr_street,
                               addr_postcode = addr_postcode,
                               parent = location_id,
                               )
            location_id = location.id = ltable.insert(**location)
            set_record_owner(ltable, location, owned_by_user=user_id)
            s3db_onaccept(ltable, location, method="create")
        if location_id:
            atable = s3db.pr_address
            query = (atable.pe_id == person.pe_id) & \
                    (atable.location_id == location_id) & \
                    (atable.type == 1) & \
                    (atable.deleted == False)
            address = db(query).select(atable.id,
                                       limitby = (0, 1),
                                       ).first()
            if not address:
                address_data = {"pe_id": person.pe_id,
                                "location_id": location_id,
                                "type": 1,
                                }
                address_data["id"] = atable.insert(**address_data)
                set_record_owner(atable, address_data)
                s3db_onaccept(atable, address_data, method="create")

        # Register home phone
        home_phone = custom.get("home_phone")
        if home_phone:
            ctable = s3db.pr_contact
            query = (ctable.pe_id == person.pe_id) & \
                    (ctable.value == home_phone) & \
                    (ctable.contact_method == "HOME_PHONE") & \
                    (ctable.deleted == False)
            contact = db(query).select(ctable.id,
                                       limitby = (0, 1),
                                       ).first()
            if not contact:
                contact_data = {"pe_id": person.pe_id,
                                "value": home_phone,
                                "contact_method": "HOME_PHONE",
                                }
                contact_data["id"] = ctable.insert(**contact_data)
                set_record_owner(ctable, contact_data)
                s3db_onaccept(ctable, contact_data, method="create")

        # Register work phone
        office_phone = custom.get("office_phone")
        if office_phone:
            ctable = s3db.pr_contact
            query = (ctable.pe_id == person.pe_id) & \
                    (ctable.value == office_phone) & \
                    (ctable.contact_method == "WORK_PHONE") & \
                    (ctable.deleted == False)
            contact = db(query).select(ctable.id,
                                       limitby = (0, 1),
                                       ).first()
            if not contact:
                contact_data = {"pe_id": person.pe_id,
                                "value": office_phone,
                                "contact_method": "WORK_PHONE",
                                }
                contact_data["id"] = ctable.insert(**contact_data)
                set_record_owner(ctable, contact_data)
                s3db_onaccept(ctable, contact_data, method="create")

        # Register availability
        hours_per_week = custom.get("hours_per_week")
        schedule_json = custom.get("schedule_json")
        availability_comments = custom.get("availability_comments")

        atable = s3db.pr_person_availability
        query = (atable.person_id == person_id) & \
                (atable.deleted == False)
        availability = db(query).select(atable.id,
                                        limitby = (0, 1),
                                        ).first()
        if availability:
            availability.update_record(hours_per_week = hours_per_week,
                                       schedule_json = schedule_json,
                                       comments = availability_comments,
                                       owned_by_user = user_id,
                                       )
            s3db_onaccept(atable, availability, method="update")
        else:
            availability = {"person_id": person_id,
                            "hours_per_week": hours_per_week,
                            "schedule_json": schedule_json,
                            "comments": availability_comments,
                            }
            availability["id"] = atable.insert(**availability)
            set_record_owner(atable, availability, owned_by_user=user_id)
            s3db_onaccept(atable, availability, method="create")

        # Link to availability sites
        sites = custom.get("availability_sites")
        ltable = s3db.pr_person_availability_site
        if isinstance(sites, list):
            query = (ltable.person_id == person_id) & \
                    (ltable.deleted == False)
            for site_id in set(sites):
                q = (ltable.site_id == site_id) & query
                if not db(q).select(ltable.id, limitby = (0, 1)).first():
                    data = {"person_id": person_id,
                            "site_id": site_id,
                            }
                    data["id"] = ltable.insert(**data)
                    set_record_owner(ltable, data, owned_by_user=user_id)
                    s3db_onaccept(ltable, data, method="create")

        # Register skills
        skills = custom.get("skill_id")
        skills = set(skills) if skills else set()
        ctable = s3db.hrm_competency
        query = (ctable.person_id == person_id) & \
                (ctable.deleted == False)
        links = db(query).select(ctable.skill_id)
        linked = set(link.skill_id for link in links)
        rmv = linked - skills
        if rmv:
            db(query & ctable.skill_id.belongs(rmv)).delete()
        for skill_id in (skills - linked):
            link = {"person_id": person_id,
                    "skill_id": skill_id,
                    }
            link["id"] = ctable.insert(**link)
            set_record_owner(ctable, link, owned_by_user=user_id)
            s3db_onaccept(ctable, link, method="create")

        # Get the volunteer record
        htable = s3db.hrm_human_resource
        query = (htable.person_id == person_id) & \
                (htable.type == 2) & \
                (htable.deleted == False)
        volunteer = db(query).select(htable.id,
                                     limitby = (0, 1),
                                     ).first()
        if volunteer:
            # Update volunteer record
            volunteer_update = {"start_date": None,
                                "end_date": None,
                                }
            start_date = custom.get("start_date")
            if start_date:
                volunteer_update["start_date"] = parse_date(start_date)

            end_date = custom.get("end_date")
            if end_date:
                volunteer_update["end_date"] = parse_date(end_date)

            comments = custom.get("comments")
            if comments:
                volunteer_update["comments"] = comments
            volunteer.update_record(**volunteer_update)
            s3db_onaccept(htable, volunteer_update, method="update")

            # Add to default pool
            default_pool = cls.get_default_pool()
            if default_pool:
                gtable = s3db.pr_group
                mtable = s3db.pr_group_membership
                query = (mtable.person_id == person_id) & \
                        (mtable.group_id == gtable.id) & \
                        (mtable.deleted == False) & \
                        (gtable.group_type.belongs(21, 22))
                membership = db(query).select(mtable.id,
                                              limitby = (0, 1),
                                              ).first()
                if not membership:
                    data = {"person_id": person_id,
                            "group_id": default_pool,
                            }
                    data["id"] = mtable.insert(**data)
                    set_record_owner(mtable, data)
                    s3db_onaccept(mtable, data, method="create")

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

        settings = current.deployment_settings

        # Get the registration key
        if request.env.request_method == "POST":
            key = request.post_vars.registration_key
        elif len(request.args) > 1:
            key = request.args[-1]
        else:
            key = None
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
        query = (ctable.name == "WelcomeMessage") & \
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
class register_invited(S3CustomController):
    """ Custom Registration Page """

    def __call__(self):

        auth = current.auth

        # Redirect if already logged-in
        if auth.s3_logged_in():
            redirect(URL(c="default", f="index"))

        T = current.T
        db = current.db
        s3db = current.s3db

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
        # TODO add to CMS prepop
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

        if form.accepts(request.vars,
                        session,
                        formname = "register",
                        onvalidation = self.validate(key),
                        ):

            form_vars = form.vars

            # Get the account
            account = self.account(key, form_vars.code)
            account.update_record(**utable._filter_fields(form_vars, id=False))

            del session.s3["invite_key"]

            # Post-process the new user record
            s3db.configure("auth_user",
                           register_onaccept = self.register_onaccept,
                           )

            # Approve and link user
            auth.s3_approve_user(account)

            # Send welcome email (custom)
            self.send_welcome_email(account)

            # Log them in
            user = Storage(utable._filter_fields(account, id=True))
            auth.login_user(user)

            auth_messages = auth.messages
            auth.log_event(auth_messages.register_log, user)
            session.flash = auth_messages.registration_successful

            # TODO redirect to the org instead?
            redirect(URL(c="default", f="person"))

        elif form.errors:
            response.error = T("There are errors in the form, please check your input")

        # Custom View
        self._view("RLPPTM", "register_invited.html")

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
    @classmethod
    def register_onaccept(cls, user_id):
        """
            Process Custom Fields
        """

        # TODO set necessary user roles
        pass

    # -------------------------------------------------------------------------
    @classmethod
    def send_welcome_email(cls, user):
        """
            Send a welcome email to the new user

            @param user: the auth_user Row
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

            @param key: the registration key (from URL args)
            @param code: the registration code (from form)
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

            @returns: a tuple (formfields, required_fields)
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
            - welcome email subject
        """

        messages = current.auth.messages

        messages.welcome_email_subject = "Welcome to the %(system_name)s Portal"

# END =========================================================================
