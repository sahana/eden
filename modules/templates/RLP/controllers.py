# -*- coding: utf-8 -*-

import json
import uuid

#from os import path

from gluon import current, Field, IS_EMPTY_OR, IS_EXPR, SQLFORM, redirect, IS_INT_IN_RANGE
from gluon.html import *
from gluon.storage import Storage

from s3 import S3CustomController, s3_mark_required, s3_phone_requires, s3_date, S3Represent, \
               IS_ONE_OF, S3MultiSelectWidget, S3GroupedOptionsWidget, s3_comments_widget, \
               S3LocationSelector, JSONERRORS

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
                                  _id="show-login",
                                  _class="tiny secondary button"),
                                _id="login-buttons"
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
                                       _id="show-register",
                                       _class="tiny secondary button",
                                       _style="margin-left:5px"))
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
class register(S3CustomController):
    """ Custom Registration Page """

    def __call__(self):

        auth = current.auth

        # Redirect if already logged-in
        if auth.s3_logged_in():
            redirect(URL(c="default", f="index"))

        auth_settings = auth.settings
        auth_messages = auth.messages

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
                   #A(T("Login"),
                   #  _href = URL(f = "user",
                   #              args = "login"),
                   #  _id = "login-btn",
                   #  _class = "action-lnk",
                   #  ),
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

        # Add Subheadings
        if subheadings:
            for pos, heading in subheadings[::-1]:
                form[0].insert(pos, DIV(heading, _class="subheading"))

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
                      "office_phone": formvars.office_phone,
                      "location_id": formvars.location_id,
                      "occupation_type_ids": formvars.occupation_type_ids,
                      "occupation": formvars.occupation,
                      #"start_date": formvars.start_date,
                      #"end_date": formvars.end_date,
                      "hours_per_week": formvars.hours_per_week,
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
                system = {"system_name": settings.get_system_name(),
                          "url": "%s/default/index/verify_email/%s" % (response.s3.base_url, key),
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

        # Custom View
        self._view(THEME, "register.html")

        return {"title": title,
                "form": form,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def formfields():
        """
            TODO docstring
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

        # Form fields
        formfields = [utable.first_name,
                      utable.last_name,
                      s3_date("date_of_birth",
                              label = T("Date of Birth"),
                              future = -96,
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
                      Field("mobile_phone",
                            label = T("Mobile Phone"),
                            requires = IS_EMPTY_OR(s3_phone_requires),
                            ),
                      Field("office_phone",
                            label = T("Office Phone"),
                            requires = IS_EMPTY_OR(s3_phone_requires),
                            ),
                      # --------------------------------------------
                      # TODO Fix location hierarchy: "Village" should be called "Locality"
                      s3db.gis_location_id("location_id",
                                           widget = S3LocationSelector(
                                                       show_address = True,
                                                       show_map = False,
                                                       ),
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
                                                              T("Specify your exact job designation"),
                                                              ),
                                          ),
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
                      s3db.hrm_multi_skill_id(
                            label = T("Skills / Resources"),
                            widget = S3GroupedOptionsWidget(cols = 1,
                                                            size = None,
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
                       (9, T("Occupation")),
                       (11, T("Availability and Resources")),
                       (15, T("Comments")),
                       (16, T("Privacy")),
                       )

        return formfields, required_fields, subheadings

    # -------------------------------------------------------------------------
    @staticmethod
    def get_default_pool():
        # TODO docstring

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
            set_record_owner(ltable, link)
            s3db_onaccept(ltable, link, method="create")

        # Register address
        location_id = custom.get("location_id")
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
        if hours_per_week:
            atable = s3db.pr_person_availability
            query = (atable.person_id == person_id) & \
                    (atable.deleted == False)
            availability = db(query).select(atable.id,
                                            atable.person_id,
                                            atable.hours_per_week,
                                            limitby = (0, 1),
                                            ).first()
            if availability:
                availability.update_record(hours_per_week = hours_per_week)
                s3db_onaccept(atable, availability, method="update")
            else:
                availability = {"person_id": person_id,
                                "hours_per_week": hours_per_week,
                                }
                availability["id"] = atable.insert(**availability)
                set_record_owner(atable, availability)
                s3db_onaccept(atable, availability, method="create")

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
            set_record_owner(ctable, link)
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

# =============================================================================
class verify_email(S3CustomController):
    """ Custom verify_email Page """

    def __call__(self):

        db = current.db
        s3db = current.s3db

        auth = current.auth
        auth_settings = auth.settings

        # Get registration key from URL
        key = current.request.args[-1]

        # Find the pending user account
        utable = auth_settings.table_user
        query = (utable.registration_key == key)
        user = db(query).select(limitby = (0, 1),
                                ).first()
        if not user:
            redirect(auth_settings.verify_email_next)

        # Configure callback to process custom fields
        s3db.configure("auth_user",
                       register_onaccept = register.register_onaccept,
                       )

        # Approve and link user
        auth.s3_approve_user(user)

        # Log them in
        user = Storage(utable._filter_fields(user, id=True))
        auth.login_user(user)

        auth_messages = auth.messages
        auth.log_event(auth_messages.verify_email_log, user)

        session = current.session
        session.confirmation = auth_messages.email_verified
        session.flash = auth_messages.registration_successful

        redirect(URL(c="default", f="person"))

# END =========================================================================
