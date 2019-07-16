# -*- coding: utf-8 -*-

import json
import uuid

from gluon import *
from gluon.storage import Storage
from s3 import IS_ONE_OF, S3CustomController, S3MultiSelectWidget, \
               s3_mark_required, s3_phone_requires, s3_str

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
class donor(S3CustomController):
    """ Custom Page """

    def __call__(self):

        output = {}

        # Allow editing of page content from browser using CMS module
        system_roles = current.auth.get_system_roles()
        ADMIN = system_roles.ADMIN in current.session.s3.roles
        s3db = current.s3db
        table = s3db.cms_post
        ltable = s3db.cms_post_module
        module = "default"

        resource = "Donor"
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
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

        self._view(THEME, "donor.html")
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
        districts = db((gtable.level == "L3") & (gtable.L2 == "Cumbria")).select(gtable.id,
                                                                                 gtable.name)
        districts = {d.id:d.name for d in districts}

        # Check Type of Registration
        agency = donor = existing = group = False

        def individual_formfields():
            """
                DRY Helper for individuals (whether with existing agency or not)
            """
            formfields = [utable.first_name,
                          utable.last_name,
                          Field("addr_L3",
                                label = T("District (if in Cumbria)"),
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
                                requires = s3_phone_requires,
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                                  T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                              ),
                                ),
                          Field("home",
                                label = T("Contact Number (Secondary)"),
                                requires = IS_EMPTY_OR(s3_phone_requires),
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
                          Field("skills_details",
                                label = T("Please specify details"),
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
                          Field("convicted", "boolean",
                                label = T("Have you ever been convicted of a criminal offence?"),
                                ),
                          Field("pending_prosecutions", "boolean",
                                label = T("Have you any prosecutions pending?"),
                                ),
                          Field("emergency_contact_name",
                                label = T("Contact Name"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("emergency_contact_number",
                                label = T("Contact Number"),
                                requires = s3_phone_requires,
                                ),
                          Field("emergency_contact_relationship",
                                label = T("Relationship"),
                                requires = IS_NOT_EMPTY(),
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
                               "disability",
                               "health",
                               "emergency_contact",
                               "convicted",
                               "pending_prosecutions",
                               ]

            return formfields, required_fields

        get_vars_get = request.get_vars.get
        org = get_vars_get("org")
        if org:
            # Volunteer for Existing Organisation
            existing = True
            otable = s3db.org_organisation
            row = db(otable.id == org).select(otable.name,
                                              limitby = (0, 1)
                                              ).first()
            if not row:
                session.error = T("Organization not found")
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
                          Field("addr_L3", "reference gis_location",
                                label = T("Where Based (District)"),
                                requires = IS_EMPTY_OR(IS_IN_SET(districts)),
                                ),
                          Field("addr_street",
                                label = T("Street Address"),
                                ),
                          Field("addr_postcode",
                                label = T("Postcode"),
                                ),
                          Field("where_operate", "list:reference gis_location",
                                label = T("Where would you be willing to operate?"),
                                requires = IS_EMPTY_OR(IS_IN_SET(districts, multiple=True)),
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
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
                          Field("home",
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
                          Field("home2",
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
                          Field("organisation_type",
                                label = T("Type of Organization"),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET([T("Business Donor"),
                                                       T("Individual Donor"),
                                                       T("Public Sector Organization"),
                                                       T("Voluntary Sector Organization"),
                                                       ])),
                                ),
                          Field("addr_L3", "reference gis_location",
                                label = T("District"),
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
                          Field("items_details",
                                label = T("Please specify details"),
                                ),
                          Field("delivery", "boolean",
                                label = T("Are you able to Deliver?"),
                                ),
                          Field("availability",
                                label = T("Length of time the offer is available?"),
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
                          Field("home",
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
                          Field("password2", "password", length=512,
                                label = T("Password"),
                                requires = IS_EMPTY_OR(
                                            CRYPT(key=auth.settings.hmac_key,
                                                  min_length=settings.get_auth_password_min_length(),
                                                  digest_alg="sha512")),
                                ),
                          Field("password2_two", "password",
                                label = auth_messages.verify_password,
                                requires = IS_EMPTY_OR(
                                            IS_EXPR("value==%s" % \
                                                    repr(request.vars.get("password2")),
                                                    error_message = auth_messages.mismatched_password,
                                                    )),
                                ),
                          Field("mobile2",
                                label = T("Contact Number (Preferred)"),
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Contact Number (Preferred)"),
                                                                  T("Ideally a Mobile Number, so that we can send you Text Messages.")),
                                              ),
                                ),
                          Field("home2",
                                label = T("Contact Number (Secondary)"),
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
                          Field("skills_details",
                                label = T("Please specify details"),
                                ),
                          Field("where_operate", "list:reference gis_location",
                                label = T("Where would you be willing to operate?"),
                                requires = IS_EMPTY_OR(IS_IN_SET(districts, multiple=True)),
                                widget = S3MultiSelectWidget(header="",
                                                             selectedList=3),
                                ),
                          Field("emergency_contact_name",
                                label = T("Contact Name"),
                                comment = T("Contact must not be listed as a leader above"),
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("emergency_contact_number",
                                label = T("Contact Number"),
                                requires = s3_phone_requires,
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
                               ]

        else:
            # Individual Volunteer
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

        # Add Subheadings
        if agency:
            form[0].insert(5, DIV("Group Leader 1",
                                  _class = "subheading",
                                  ))
            form[0].insert(15, DIV("Group Leader 2",
                                   _class = "subheading",
                                   ))
            form[0].insert(23, DIV(_class = "subheading",
                                   ))

        elif donor:
            pass
        elif group:
            form[0].insert(1, DIV("Group Leader 1",
                                  _class = "subheading",
                                  ))
            form[0].insert(11, DIV("Group Leader 2",
                                   _class = "subheading",
                                   ))
            form[0].insert(19, DIV(_class = "subheading",
                                   ))
            form[0].insert(-4, DIV("Person to be contacted in case of an emergency",
                                   _class = "subheading",
                                   ))
            form[0].insert(-2, DIV(_class = "subheading",
                                   ))
        else:
            # Individual / Existing
            form[0].insert(2, DIV("Home Address",
                                  _class = "subheading",
                                  ))
            form[0].insert(6, DIV(_class = "subheading",
                                  ))
            # Volunteer Offer
            form[0].insert(11, DIV(_class = "subheading",
                                   ))
            form[0].insert(13, DIV(_class = "subheading",
                                   ))
            form[0].insert(-5, DIV("Person to be contacted in case of an emergency",
                                   _class = "subheading",
                                   ))
            form[0].insert(-2, DIV(_class = "subheading",
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

            form_vars = form.vars

            # Create the user record
            user_id = utable.insert(**utable._filter_fields(form_vars, id=False))
            form_vars.id = user_id

            # Save temporary user fields in db.auth_user_temp
            # Default just handles mobile, home, consent
            #auth.s3_user_register_onaccept(form)

            temptable = db.auth_user_temp
            record  = {"user_id": user_id}

            # Store the mobile_phone ready to go to pr_contact
            mobile = form_vars.mobile
            record["mobile"] = mobile

            # Store Consent Question Response
            consent = form_vars.consent
            record["consent"] = consent

            # Store the home_phone ready to go to pr_contact
            home = form_vars.home
            if home:
                record["home"] = home

            # Store Custom fields
            if agency:
                custom = {"registration_type": "agency",
                          "addr_L3": form_vars.addr_L3,
                          "addr_street": form_vars.addr_street,
                          "addr_postcode": form_vars.addr_postcode,
                          }
            elif donor:
                custom = {"registration_type": "donor",
                          "organisation": form_vars.organisation,
                          "organisation_type": form_vars.organisation_type,
                          "addr_L3": form_vars.addr_L3,
                          "addr_street": form_vars.addr_street,
                          "addr_postcode": form_vars.addr_postcode,
                          "item_id": form_vars.item_id,
                          "items_details": form_vars.items_details,
                          }
            elif existing:
                custom = {"registration_type": "existing",
                          "addr_L3": form_vars.addr_L3,
                          "addr_street": form_vars.addr_street,
                          "addr_postcode": form_vars.addr_postcode,
                          "skill_id": form_vars.skill_id,
                          "skills_details": form_vars.skills_details,
                          "emergency_contact_name": form_vars.emergency_contact_name,
                          "emergency_contact_number": form_vars.emergency_contact_number,
                          "emergency_contact_relationship": form_vars.emergency_contact_relationship,
                          }
            elif group:
                custom = {"registration_type": "group",
                          "group": form_vars.group,
                          # Assume outside Cumbria
                          #"addr_L3": form_vars.addr_L3,
                          "addr_street": form_vars.addr_street,
                          "addr_postcode": form_vars.addr_postcode,
                          "skill_id": form_vars.skill_id,
                          "skills_details": form_vars.skills_details,
                          "emergency_contact_name": form_vars.emergency_contact_name,
                          "emergency_contact_number": form_vars.emergency_contact_number,
                          #"emergency_contact_relationship": form_vars.emergency_contact_relationship,
                          }
            else:
                custom = {"registration_type": "individual",
                          "addr_L3": form_vars.addr_L3,
                          "addr_street": form_vars.addr_street,
                          "addr_postcode": form_vars.addr_postcode,
                          "skill_id": form_vars.skill_id,
                          "skills_details": form_vars.skills_details,
                          "emergency_contact_name": form_vars.emergency_contact_name,
                          "emergency_contact_number": form_vars.emergency_contact_number,
                          "emergency_contact_relationship": form_vars.emergency_contact_relationship,
                          }
            record["custom"] = json.dumps(custom)

            temptable.update_or_insert(**record)

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
                # Verify User Email
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
                            "header": header,
                            "form": form,
                            }

                # Redirect to Verification Info page
                register_next = URL(c = "default",
                                    f = "message",
                                    args = ["verify_email_sent"],
                                    vars = {"email": form.vars.email},
                                    )

            # Log action
            #if log:
            auth.log_event(auth_messages.register_log, form.vars)

            # Run custom onaccept for registration form
            #onaccept = auth_settings.register_onaccept
            #if onaccept:
            #    onaccept(form)

            # Redirect
            redirect(register_next)

        # Custom View
        self._view(THEME, "register.html")

        return {"title": title,
                "header": header,
                "form": form,
                }

# =============================================================================
class verify_email(S3CustomController):
    """ Custom verify_email Page """

    def __call__(self):

        db = current.db
        auth = current.auth
        auth_settings = auth.settings

        key = current.request.args[-1]
        utable = auth_settings.table_user
        query = (utable.registration_key == key)
        user = db(query).select(limitby=(0, 1)).first()
        if not user:
            redirect(auth_settings.verify_email_next)

        auth_messages = auth.messages

        session = current.session
        settings = current.deployment_settings

        user_id = user.id

        # Determine registration type & read custom fields
        temptable = db.auth_user_temp
        record = db(temptable.user_id == user_id).select(temptable.custom,
                                                         limitby = (0, 1),
                                                         ).first()
        custom = json.loads(record.custom)

        organisation_id = user.organisation_id
        if not organisation_id:
            # Donor/Individual/Group, so doesn't need approval
            # Calls s3_link_user() which calls s3_link_to_person() which applies 'normal' data from db.auth_user_temp (home_phone, mobile_phone, consent)
            auth.s3_approve_user(user)# Would make agency user ORG_ADMIN automatically, however they take a different path

            registration_type = custom["registration_type"]

            s3db = current.s3db
            get_config = s3db.get_config

            # Apply custom fields & Assign correct Roles
            if registration_type == "donor":
                # Donor

                # Create Home Address
                gtable = s3db.gis_location
                record = {"parent": custom["addr_L3"],
                          "addr_street": custom["addr_street"],
                          "addr_postcode": custom["addr_postcode"],
                          }
                location_id = gtable.insert(**record)
                record["id"] = location_id
                onaccept = get_config("gis_location", "create_onaccept") or \
                           get_config("gis_location", "onaccept")
                if callable(onaccept):
                    gform = Storage(vars = record)
                    onaccept(gform)

                pe_id = auth.s3_user_pe_id(user_id)
                atable = s3db.pr_address
                record = {"pe_id": pe_id,
                          "location_id": location_id,
                          }
                address_id = atable.insert(**record)
                record["id"] = address_id
                onaccept = get_config("pr_address", "create_onaccept") or \
                           get_config("pr_address", "onaccept")
                if callable(onaccept):
                    aform = Storage(vars = record)
                    onaccept(aform)

                # Assign correct Role
                ftable = s3db.pr_forum
                forum = db(ftable.name == "Donors").select(ftable.pe_id,
                                                           limitby = (0, 1)
                                                           ).first()
                auth.add_membership(user_id = user_id,
                                    role = "Donor",
                                    entity = forum.pe_id,
                                    )

            elif registration_type == "group":
                # Group

                # Create Group
                gtable = s3db.pr_group
                group = {"name": custom["group"]}
                group_id = gtable.insert(**group)
                group["id"] = group_id
                s3db.update_super(gtable, group)

                # Create Home Address
                gtable = s3db.gis_location
                record = {# Assume outside Cumbria
                          #"parent": custom["addr_L3"],
                          "addr_street": custom["addr_street"],
                          "addr_postcode": custom["addr_postcode"],
                          }
                location_id = gtable.insert(**record)
                record["id"] = location_id
                onaccept = get_config("gis_location", "create_onaccept") or \
                           get_config("gis_location", "onaccept")
                if callable(onaccept):
                    gform = Storage(vars = record)
                    onaccept(gform)

                pe_id = auth.s3_user_pe_id(user_id)
                atable = s3db.pr_address
                record = {"pe_id": pe_id,
                          "location_id": location_id,
                          }
                address_id = atable.insert(**record)
                record["id"] = address_id
                onaccept = get_config("pr_address", "create_onaccept") or \
                           get_config("pr_address", "onaccept")
                if callable(onaccept):
                    aform = Storage(vars = record)
                    onaccept(aform)

                # Add Leader(s) to Group
                ptable = s3db.pr_person
                person = db(ptable.pe_id == pe_id).select(ptable.id,
                                                          limitby = (0, 1),
                                                          ).first()
                mtable = s3db.pr_group_membership
                record = {"group_id": group_id,
                          "person_id": person.id,
                          "group_head": True,
                          }
                membership_id = mtable.insert(**record)
                record["id"] = membership_id
                onaccept = get_config("pr_group_membership", "create_onaccept") or \
                           get_config("pr_group_membership", "onaccept")
                if callable(onaccept):
                    mform = Storage(vars = record)
                    onaccept(mform)

                # Create 2nd Leader
                # @ToDo

                # Create Skills
                ctable = s3db.pr_group_competency
                for skill_id in custom["skill_id"]
                    record = {"group_id": group_id,
                              "skill_id": skill_id,
                              }
                    ctable.insert(**record)

                ttable = s3db.pr_group_tag
                record = {"group_id": group_id,
                          "tag": "skills_details",
                          "value": custom["skills_details"],
                          }
                ttable.insert(**record)

                # Emergency Contact
                record = {"group_id": group_id,
                          "tag": "contact_name",
                          "value": custom["emergency_contact_name"],
                          }
                ttable.insert(**record)
                record = {"group_id": group_id,
                          "tag": "contact_number",
                          "value": custom["emergency_contact_number"],
                          }
                ttable.insert(**record)

                # Assign correct Role
                auth.add_membership(user_id = user_id,
                                    role = "Volunteer Group Leader",
                                    entity = group["pe_id"],
                                    )

            else:
                # Individual
                get_config = s3db.get_config

                # Create Home Address
                gtable = s3db.gis_location
                record = {"parent": custom["addr_L3"],
                          "addr_street": custom["addr_street"],
                          "addr_postcode": custom["addr_postcode"],
                          }
                location_id = gtable.insert(**record)
                record["id"] = location_id
                onaccept = get_config("gis_location", "create_onaccept") or \
                           get_config("gis_location", "onaccept")
                if callable(onaccept):
                    gform = Storage(vars = record)
                    onaccept(gform)

                pe_id = auth.s3_user_pe_id(user_id)
                atable = s3db.pr_address
                record = {"pe_id": pe_id,
                          "location_id": location_id,
                          }
                address_id = atable.insert(**record)
                record["id"] = address_id
                onaccept = get_config("pr_address", "create_onaccept") or \
                           get_config("pr_address", "onaccept")
                if callable(onaccept):
                    aform = Storage(vars = record)
                    onaccept(aform)

                # Create Skills
                ctable = s3db.hrm_competency
                for skill_id in custom["skill_id"]
                    record = {"group_id": group_id,
                              "skill_id": skill_id,
                              }
                    ctable.insert(**record)

                # @ToDo
                #ttable = s3db.pr_person_tag
                #record = {"person_id": person_id,
                #          "tag": "skills_details",
                #          "value": custom["skills_details"],
                #          }
                #ttable.insert(**record)

                # Health/Criminal
                # @ToDo

                # Emergency Contact
                etable = s3db.pr_emergency_contact
                record = {"pe_id": pe_id,
                          "name": custom["emergency_contact_name"],
                          "phone": custom["emergency_contact_number"],
                          "relationship": custom["emergency_contact_relationship"],
                          }
                etable.insert(**record)

                # Assign correct Role
                ftable = s3db.pr_forum
                forum = db(ftable.name == "Reserves").select(ftable.pe_id,
                                                             limitby = (0, 1)
                                                             ).first()
                auth.add_membership(user_id = user_id,
                                    role = "Reserve Volunteer",
                                    entity = forum.pe_id,
                                    )

            # Log them in
            user = Storage(utable._filter_fields(user, id=True))
            auth.login_user(user)

            #if log:
            auth.log_event(auth_messages.verify_email_log, user)

            session.confirmation = auth_messages.email_verified
            session.flash = auth_messages.registration_successful

            if registration_type == "donor":
                # Show General Information for Donors
                _next = URL(c="default", f="index", args="donor")
            else:
                # Individual / Group
                # Show General Information & Advice
                _next = URL(c="cms", f="post", args="datalist")
            redirect(_next)

        db(utable.id == user_id).update(registration_key = "pending")
        session.information = settings.get_auth_registration_pending_approval()

        # Lookup the Approvers
        gtable = db.auth_group
        mtable = db.auth_membership
        if custom["registration_type"] == "agency":
            # Agencies are approved by ADMIN(s)
            query = (gtable.uuid == "ADMIN") & \
                    (gtable.id == mtable.group_id) & \
                    (mtable.user_id == utable.id)
            approvers = db(query).select(utable.email)
        else:
            # Existing, so approved by ORG_ADMIN(s)
            query = (gtable.uuid == "ORG_ADMIN") & \
                    (gtable.id == mtable.group_id) & \
                    (mtable.user_id == utable.id) & \
                    (utable.organisation_id == organisation_id)
            approvers = db(query).select(utable.email)

        # Mail the Approver(s)
        first_name = user.first_name
        last_name = user.last_name
        email = user.email
        base_url = current.response.s3.base_url
        system_name = settings.get_system_name()
        # NB This is a cut-down version of the original which doesn't support multi-lingual
        subject = "%(system_name)s - New User Registration Approval Pending" % \
                    {"system_name": system_name}
        message = s3_str(auth_messages.approve_user % \
                    {"system_name": system_name,
                     "first_name": first_name,
                     "last_name": last_name,
                     "email": email,
                     "url": "%(base_url)s/admin/user/%(id)s" % \
                            {"base_url": base_url,
                             "id": user_id,
                             },
                     })

        mailer = auth_settings.mailer
        if mailer.settings.server:
            for approver in approvers:
                result = mailer.send(to = approver,
                                     subject = subject,
                                     message = message,
                                     )
        else:
            # Email system not configured (yet)
            result = None
        if not result:
            # Don't prevent registration just because email not configured
            #db.rollback()
            session.error = auth_messages.email_send_failed

        redirect(auth_settings.verify_email_next)

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

        resource = "Volunteer3"
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

        self._view(THEME, "volunteer.html")
        return output

# END =========================================================================
