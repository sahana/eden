# -*- coding: utf-8 -*-

import json
from uuid import uuid4

from gluon import A, BR, CRYPT, DIV, Field, FORM, H3, INPUT, \
                  IS_EMAIL, IS_EMPTY_OR, IS_EXPR, IS_LOWER, IS_NOT_EMPTY, IS_NOT_IN_DB, \
                  P, SQLFORM, TABLE, TD, TR, URL, XML, current, redirect

from gluon.storage import Storage

from s3 import IS_PHONE_NUMBER_MULTI, JSONERRORS, S3CRUD, S3CustomController, \
               S3LocationSelector, S3Represent, S3Request, s3_get_extension, \
               s3_mark_required, s3_str

from .notifications import formatmap

THEME = "RLP"

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

        self._view(THEME, "cmspage.html")
        return output

# =============================================================================
class approve(S3CustomController):
    """ Custom Approval Page """

    def __call__(self):

        T = current.T
        auth = current.auth
        db = current.db
        s3db = current.s3db
        session = current.session

        ogtable = s3db.org_group
        org_group = db(ogtable.name == "COVID-19 Test Stations").select(ogtable.id,
                                                                        ogtable.pe_id,
                                                                        limitby = (0, 1)
                                                                        ).first()

        has_role = auth.s3_has_role
        if has_role("ORG_GROUP_ADMIN",
                    for_pe = org_group.pe_id):
            ORG_ADMIN = False
        elif has_role("ORG_ADMIN"):
            ORG_ADMIN = True
        else:
            session.error = T("Not Permitted!")
            redirect(URL(c = "default",
                         f = "index",
                         args = None,
                         ))

        utable = db.auth_user
        request = current.request
        response = current.response
        org_group_id = org_group.id

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
                                                   utable.link_user_to, # Needed for s3_approve_user
                                                   utable.site_id, # Needed for s3_link_to_human_resource (calledfrom s3_approve_user)
                                                   limitby = (0, 1)
                                                   ).first()

            if not user or user.org_group_id != org_group_id:
                session.error = T("Invalid Site!")
                redirect(URL(c = "default",
                             f = "index",
                             args = ["approve"],
                             ))

            otable = s3db.org_organisation
            organisation_id = user.organisation_id
            if organisation_id:
                org = db(otable.id == organisation_id).select(otable.name,
                                                              otable.pe_id,
                                                              limitby = (0, 1)
                                                              ).first()
            if ORG_ADMIN:
                if not organisation_id or \
                   not has_role("ORG_ADMIN",
                                for_pe = org.pe_id):
                    session.error = T("Site not within your Organisation!")
                    redirect(URL(c = "default",
                                 f = "index",
                                 args = ["approve"],
                                 ))

            person = "%(first_name)s %(last_name)s <%(email)s>" % {"first_name": user.first_name,
                                                                   "last_name": user.last_name,
                                                                   "email": user.email,
                                                                   }

            ttable = s3db.auth_user_temp
            temp = db(ttable.user_id == user_id).select(ttable.custom,
                                                        limitby = (0, 1)
                                                        ).first()

            try:
                custom = json.loads(temp.custom)
            except JSONERRORS:
                custom = {}

            custom_get = custom.get
            organisation = custom_get("organisation")
            if organisation:
                test_station = TR(TD("%s:" % T("Test Station")),
                                  TD(organisation),
                                  )
            else:
                test_station = None
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
            phone = custom_get("office_phone")
            opening_times = custom_get("opening_times")

            if user.registration_key is None:
                response.warning = T("Site has previously been Approved")
            elif user.registration_key == "rejected":
                response.warning = T("Site has previously been Rejected")
            elif user.registration_key != "pending":
                response.warning = T("Site hasn't verified their email")

            approve = FORM(INPUT(_value = T("Approve"),
                                 _type = "submit",
                                 _name = "approve-btn",
                                 _id = "approve-btn",
                                 _class = "button round",
                                 ))

            reject = FORM(INPUT(_value = T("Reject"),
                                _type = "submit",
                                _name = "reject-btn",
                                _id = "reject-btn",
                                _class = "button round",
                                ))

            form = TABLE(TR(approve,
                            reject,
                            ),
                         TR(TD("%s:" % T("Person")),
                            TD(person),
                            ),
                         test_station,
                         TR(TD("%s:" % T("Address")),
                            TD(address),
                            ),
                         TR(TD("%s:" % T("Telephone")),
                            TD(phone or ""),
                            ),
                         TR(TD("%s:" % T("Opening Hours")),
                            TD(opening_times or ""),
                            ),
                         )

            if approve.accepts(request.post_vars, session, formname="approve"):
                set_record_owner = auth.s3_set_record_owner
                s3db_onaccept = s3db.onaccept
                update_super = s3db.update_super
                if not organisation_id:
                    # Create Organisation
                    org = Storage(name = organisation,
                                  )
                    organisation_id = otable.insert(**org)
                    org.id = organisation_id
                    update_super(otable, org)
                    set_record_owner(otable, org, owned_by_user=user_id)
                    s3db_onaccept(otable, org, method="create")
                    # Link to Org_Group: "COVID-19 Test Stations"
                    s3db.org_group_membership.insert(group_id = org_group_id,
                                                     organisation_id = organisation_id,
                                                     )
                    # Update User
                    user.update_record(organisation_id = organisation_id,
                                       registration_key = None,
                                       )
                else:
                    # Update User
                    user.update_record(registration_key = None,
                                       )

                location_id = location_get("id")
                if not location_id:
                    # Create Location
                    ltable = s3db.gis_location
                    del location["wkt"] # Will get created during onaccept & we don't want the 'Source WKT has been cleaned by Shapely" warning
                    location_id = ltable.insert(**location)
                    location["id"] = location_id
                    set_record_owner(ltable, location, owned_by_user=user_id)
                    s3db_onaccept(ltable, location, method="create")

                # Create Facility
                ftable = s3db.org_facility
                facility = Storage(name = organisation or org.name,
                                   organisation_id = organisation_id,
                                   location_id = location_id,
                                   phone1 = phone,
                                   opening_times = opening_times,
                                   )
                facility.id = ftable.insert(**facility)
                update_super(ftable, facility)
                set_record_owner(ftable, facility, owned_by_user=user_id)
                s3db_onaccept(ftable, facility, method="create")
                # Assign Type
                fttable = s3db.org_facility_type
                facility_type = db(fttable.name == "Infection Test Station").select(fttable.id,
                                                                                    limitby = (0, 1)
                                                                                    ).first()
                if facility_type:
                    s3db.org_site_facility_type.insert(site_id = facility.site_id,
                                                       facility_type_id = facility_type.id,
                                                       )

                # Approve user
                auth.s3_approve_user(user)
                # Grant ORG_ADMIN if first
                auth.add_membership(user_id = user_id,
                                    role = "Organisation Admin",
                                    entity = org.pe_id)
                # Send welcome email
                # Done within s3_approve_user
                #auth.s3_send_welcome_email(form.vars)
                session.confirmation = T("Site approved")
                redirect(URL(c = "default",
                             f = "index",
                             args = ["approve"],
                             ))

            elif reject.accepts(request.post_vars, session, formname="reject"):
                user.update_record(registration_key = "rejected")
                # @ToDo: Delete Org & Fac, if created previously
                session.confirmation = T("Site rejected")
                redirect(URL(c = "default",
                             f = "index",
                             args = ["approve"],
                             ))

            output = {"form": form,
                      "title": T("Approve Test Station"),
                      }

            # Custom View
            self._view(THEME, "approve.html")

        else:
            # List View
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
                filter = (utable.organisation_id.belongs(organisation_id))
            else:
                # Filter to all for the ORG_GROUP
                filter = (utable.org_group_id == org_group_id)
            # Only include pending accounts
            filter &= (utable.registration_key == "pending")
                
            resource = s3db.resource("auth_user", filter=filter)

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
                dtargs["dt_base_url"] = URL(c="default", f="index", args="approve")
                dtargs["dt_permalink"] = URL(c="default", f="index", args="approve")
                datatable = dt.html(totalrows,
                                    displayrows,
                                    id = list_id,
                                    **dtargs)

                output = {"items": datatable,
                          "title": T("Test Stations to be Approved"),
                          }

                # Custom View
                self._view(THEME, "approve_list.html")

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
        title = T("Register Test Station")

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

            # Add Organisation, if existing
            organisation = formvars.get("organisation")
            otable = s3db.org_organisation
            org = db(otable.name == organisation).select(otable.id,
                                                         limitby = (0, 1)
                                                         ).first()
            if org:
                organisation_id = org.id
                formvars["organisation_id"] = organisation_id
            else:
                organisation_id = None

            # Create the user record
            user_id = utable.insert(**utable._filter_fields(formvars, id=False))
            formvars.id = user_id

            # Set org_group
            ogtable = s3db.org_group
            org_group = db(ogtable.name == "COVID-19 Test Stations").select(ogtable.id,
                                                                            limitby = (0, 1)
                                                                            ).first()
            db(utable.id == user_id).update(org_group_id = org_group.id)

            # Save temporary user fields in s3db.auth_user_temp
            temptable = s3db.auth_user_temp
            record  = {"user_id": user_id}

            record["consent"] = formvars.consent

            # Store Custom fields
            custom = {"location": formvars.location,
                      "office_phone": formvars.office_phone,
                      "opening_times": formvars.opening_times,
                      }
            if not organisation_id:
                custom["organisation"] = organisation
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

        s3db = current.s3db

        auth = current.auth
        auth_settings = auth.settings
        auth_messages = auth.messages

        utable = auth_settings.table_user
        passfield = auth_settings.password_field

        # Instantiate Consent Tracker
        consent = s3db.auth_Consent(processing_types=["SHARE"])

        # Last name is required
        utable.last_name.requires = IS_NOT_EMPTY(error_message=T("input required"))

        #ltable = s3db.gis_location

        # Form fields
        formfields = [utable.first_name,
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
                      # --------------------------------------------
                      Field("organisation",
                            label = T("Name"),
                            requires = IS_NOT_EMPTY(),
                            ),
                      Field("location", "json",
                            widget = S3LocationSelector(
                                        levels = ("L1", "L2", "L3", "L4"),
                                        required_levels = ("L1", "L2", "L3"),
                                        show_address = True,
                                        show_postcode = True,
                                        show_map = True,
                                        ),
                            ),
                      #Field("addr_street",
                      #      label = ltable.addr_street.label,
                      #      ),
                      #Field("addr_postcode",
                      #      label = ltable.addr_postcode.label,
                      #      requires = IS_NOT_EMPTY(),
                      #      ),

                      Field("office_phone",
                            label = T("Office Phone"),
                            requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                            ),
                      Field("opening_times",
                            label = T("Opening Hours"),
                            #requires = IS_NOT_EMPTY(),
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
        subheadings = ((0, T("User Account")),
                       (5, T("Test Station")),
                       (9, T("Privacy")),
                       )

        # Geocoder
        current.response.s3.scripts.append("/%s/static/themes/RLP/js/geocoderPlugin.js" % request.application)

        return formfields, required_fields, subheadings

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

            user_id = user.id
            db(utable.id == user_id).update(registration_key = "pending")
            auth.log_event(auth.messages.verify_email_log, user)

            # Lookup the Approver(s)
            gtable = db.auth_group
            mtable = db.auth_membership
            query = None

            # Is this an existing Org?
            organisation_id = user.organisation_id
            if organisation_id:
                otable = s3db.org_organisation
                org = db(otable.id == organisation_id).select(otable.name,
                                                              otable.pe_id,
                                                              limitby = (0, 1)
                                                              ).first()
                if org:
                    org_name = org.name
                    # send to ORG_ADMIN
                    query = (gtable.uuid == "ORG_ADMIN") & \
                            (mtable.group_id == gtable.id) & \
                            (mtable.pe_id == org.pe_id) & \
                            (mtable.user_id == utable.id)

            if not query:
                # Read org_name from auth_user_temp
                ttable= s3db.auth_user_temp
                temp = db(ttable.user_id == user_id).select(ttable.custom,
                                                            limitby = (0, 1)
                                                            ).first()
                try:
                    custom = json.loads(temp.custom)
                except JSONERRORS:
                    custom = {}
                org_name = custom.get("organisation")
                # send to ORG_GROUP_ADMIN(s) for "COVID-19 Test Stations"
                ogtable = s3db.org_group
                query = (gtable.uuid == "ORG_GROUP_ADMIN") & \
                        (mtable.group_id == gtable.id) & \
                        (mtable.pe_id == ogtable.pe_id) & \
                        (ogtable.name == "COVID-19 Test Stations") & \
                        (mtable.user_id == utable.id)

            approvers = db(query).select(utable.email,
                                         utable.language,
                                         )
            # Ensure that we send out the mails in the language that the approver(s) want
            languages = {}
            for approver in approvers:
                language = approver.language
                if language not in languages:
                    languages[language] = []
                languages[language].append(approver.email)

            subjects = {}
            messages = {}
            approve_user_message = \
"""Your action is required to approve a New Test Station for %(system_name)s:
%(org_name)s
Please go to %(url)s to approve this station."""
            base_url = response.s3.base_url
            system_name = settings.get_system_name()
            for language in languages:
                T.force(language)
                subjects[language] = \
                    s3_str(T("%(system_name)s - New Test Station Approval Pending") % \
                            {"system_name": system_name})
                messages[language] = \
                    s3_str(T(approve_user_message) % {"org_name": org_name,
                                                      "system_name": system_name,
                                                      "url": "%(base_url)s/default/index/approve/%(id)s" % \
                                                                {"base_url": base_url,
                                                                 "id": user_id,
                                                                 },
                                                      })

            # Restore language for UI
            T.force(session.s3.language)

            mailer = auth_settings.mailer
            if mailer.settings.server:
                send_email = mailer.send
                for approver in approvers:
                    language = approver["language"]
                    result = send_email(to = approver["email"],
                                        subject = subjects[language],
                                        message = messages[language]
                                        )
            else:
                # Email system not configured (yet)
                result = None

            if result:
                session = current.session
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
    @staticmethod
    def register_onaccept(user_id):
        """
            Process Registration

            @param user_id: the user ID
        """

        auth = current.auth
        assign_role = auth.s3_assign_role

        assign_role(user_id, "ORG_ADMIN")
        assign_role(user_id, "VOUCHER_ISSUER")

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

# =============================================================================
class geocode(S3CustomController):
    """
        Custom Geocoder
        - looks up Lat/Lon from Postcode &/or Address
        - looks up Lx from Lat/Lon
    """

    def __call__(self):

        gis = current.gis

        post_vars_get = current.request.post_vars.get
        postcode = post_vars_get("postcode")
        address = post_vars_get("address")
        if address:
            full_address = "%s %s" %(postcode, address)
        else:
            full_address = postcode

        latlon = gis.geocode(full_address)
        if not isinstance(latlon, dict):
            return None

        lat = latlon["lat"]
        lon = latlon["lon"]
        results = gis.geocode_r(lat, lon)

        results["lat"] = lat
        results["lon"] = lon

        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(results)

# END =========================================================================
