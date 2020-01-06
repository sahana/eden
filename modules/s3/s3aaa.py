# -*- coding: utf-8 -*-

""" Authentication, Authorization, Accounting

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2019 Sahana Software Foundation
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

__all__ = ("AuthS3",
           "S3Permission",
           "S3Audit",
           #"S3EntityRoleManager",
           "S3OrgRoleManager",
           "S3PersonRoleManager",
           )

import datetime
import json
#import re
import time

from collections import OrderedDict
from uuid import uuid4

#from gluon import *
from gluon import current, redirect, CRYPT, DAL, HTTP, SQLFORM, URL, \
                  A, DIV, INPUT, LABEL, OPTGROUP, OPTION, SELECT, SPAN, XML, \
                  IS_EMAIL, IS_EMPTY_OR, IS_EXPR, IS_IN_DB, IS_IN_SET, \
                  IS_LOWER, IS_NOT_EMPTY, IS_NOT_IN_DB

from gluon.sqlhtml import OptionsWidget
from gluon.storage import Storage
from gluon.tools import Auth, callback, DEFAULT, replace_id
from gluon.utils import web2py_uuid

from s3compat import basestring, reduce
from s3dal import Row, Rows, Query, Table, Field, original_tablename
from .s3datetime import S3DateTime
from .s3error import S3PermissionError
from .s3fields import S3MetaFields, S3Represent, s3_comments
from .s3rest import S3Method, S3Request
from .s3track import S3Tracker
from .s3utils import s3_addrow, s3_get_extension, s3_mark_required, s3_str
from .s3validators import IS_ISO639_2_LANGUAGE_CODE

# =============================================================================
class AuthS3(Auth):

    """
        S3 extensions of the gluon.tools.Auth class

        - override:
            - __init__
            - define_tables
            - login_bare
            - set_cookie
            - login
            - register
            - email_reset_password
            - verify_email
            - profile
            - has_membership
            - requires_membership

        - S3 extension for user registration:
            - s3_register_validation
            - s3_user_register_onaccept

        - S3 extension for user administration:
            - configure_user_fields
            - s3_verify_user
            - s3_approve_user
            - s3_link_user
            - s3_user_profile_onaccept
            - s3_link_to_person
            - s3_link_to_organisation
            - s3_link_to_human_resource
            - s3_link_to_member
            - s3_approver

        - S3 custom authentication methods:
            - s3_impersonate
            - s3_logged_in

        - S3 user role management:
            - get_system_roles
            - s3_set_roles
            - s3_create_role
            - s3_delete_role
            - s3_assign_role
            - s3_withdraw_role
            - s3_has_role
            - s3_group_members

        - S3 ACL management:
            - s3_update_acls

        - S3 user identification helpers:
            - s3_get_user_id
            - s3_user_pe_id
            - s3_logged_in_person
            - s3_logged_in_human_resource

        - S3 core authorization methods:
            - s3_has_permission
            - s3_accessible_query

        - S3 variants of web2py authorization methods:
            - s3_has_membership
            - s3_requires_membership

        - S3 record ownership methods:
            - s3_make_session_owner
            - s3_session_owns
            - s3_set_record_owner
    """

    # Configuration of UIDs for system roles
    S3_SYSTEM_ROLES = Storage(ADMIN = "ADMIN",
                              AUTHENTICATED = "AUTHENTICATED",
                              ANONYMOUS = "ANONYMOUS",
                              EDITOR = "EDITOR",
                              MAP_ADMIN = "MAP_ADMIN",
                              ORG_ADMIN = "ORG_ADMIN",
                              ORG_GROUP_ADMIN = "ORG_GROUP_ADMIN",
                              )

    def __init__(self):

        """ Initialise parent class & make any necessary modifications """

        Auth.__init__(self, current.db)

        self.settings.lock_keys = False
        self.settings.login_userfield = "email"
        self.settings.lock_keys = True

        messages = self.messages
        messages.lock_keys = False

        # @ToDo Move these to deployment_settings
        messages.approve_user = \
"""Your action is required to approve a New User for %(system_name)s:
%(first_name)s %(last_name)s
%(email)s
Please go to %(url)s to approve this user."""
        messages.email_approver_failed = "Failed to send mail to Approver - see if you can notify them manually!"
        messages.email_sent = "Verification Email sent - please check your email to validate. If you do not receive this email please check your junk email or spam filters"
        messages.email_verification_failed = "Unable to send verification email - either your email is invalid or our email server is down"
        messages.email_verified = "Email verified - you can now login"
        messages.duplicate_email = "This email address is already in use"
        messages.help_mobile_phone = "Entering a phone number is optional, but doing so allows you to subscribe to receive SMS messages."
        messages.help_organisation = "Entering an Organization is optional, but doing so directs you to the appropriate approver & means you automatically get the appropriate permissions."
        messages.help_image = "You can either use %(gravatar)s or else upload a picture here. The picture will be resized to 50x50."
        messages.label_image = "Profile Image"
        messages.label_organisation_id = "Organization"
        messages.label_org_group_id = "Coalition"
        messages.label_remember_me = "Remember Me"
        #messages.logged_in = "Signed In"
        #messages.logged_out = "Signed Out"
        #messages.submit_button = "Signed In"
        messages.new_user = \
"""A New User has registered for %(system_name)s:
%(first_name)s %(last_name)s
%(email)s
No action is required."""
        messages.password_reset_button = "Request password reset"
        messages.profile_save_button = "Apply changes"
        messages.registration_disabled = "Registration Disabled!"
        messages.registration_verifying = "You haven't yet Verified your account - please check your email"
        messages.reset_password = "Click on the link %(url)s to reset your password"
        messages.verify_email = "Click on the link %(url)s to verify your email"
        messages.verify_email_subject = "%(system_name)s - Verify Email"
        messages.welcome_email_subject = "Welcome to %(system_name)s"
        messages.welcome_email = \
"""Welcome to %(system_name)s
 - You can start using %(system_name)s at: %(url)s
 - To edit your profile go to: %(url)s%(profile)s
Thank you"""
        messages.lock_keys = True

        # S3Permission
        self.permission = S3Permission(self)

        # Set to True to override any authorization
        self.override = False

        # Set to True to indicate that all current transactions
        # are to be rolled back (e.g. trial phase of interactive imports)
        self.rollback = False

        # Site types (for OrgAuth)
        T = current.T
        if current.deployment_settings.get_ui_label_camp():
            shelter = T("Camp")
        else:
            shelter = T("Shelter")
        self.org_site_types = Storage(transport_airport = T("Airport"),
                                      msg_basestation = T("Cell Tower"),
                                      cr_shelter = shelter,
                                      org_facility = T("Facility"), # @ToDo: Use deployment setting for label
                                      org_office = T("Office"),
                                      transport_heliport = T("Heliport"),
                                      hms_hospital = T("Hospital"),
                                      fire_station = T("Fire Station"),
                                      dvi_morgue = T("Morgue"),
                                      police_station = T("Police Station"),
                                      edu_school = T("School"),
                                      transport_seaport = T("Seaport"),
                                      inv_warehouse = T("Warehouse"),
                                      )

        # Name prefixes of tables which must not be manipulated from remote,
        # CLI can override with auth.override=True
        self.PROTECTED = ("admin",)

    # -------------------------------------------------------------------------
    def define_tables(self, migrate=True, fake_migrate=False):
        """
            to be called unless tables are defined manually

            usages::

                # defines all needed tables and table files
                # UUID + "_auth_user.table", ...
                auth.define_tables()

                # defines all needed tables and table files
                # "myprefix_auth_user.table", ...
                auth.define_tables(migrate="myprefix_")

                # defines all needed tables without migration/table files
                auth.define_tables(migrate=False)
        """

        db = current.db
        settings = self.settings
        messages = self.messages
        deployment_settings = current.deployment_settings
        define_table = db.define_table

        # User table
        utable = settings.table_user
        uname = settings.table_user_name
        if not utable:
            utable_fields = [
                Field("first_name", length=128, notnull=True,
                      default="",
                      requires = \
                      IS_NOT_EMPTY(error_message=messages.is_empty),
                      ),
                Field("last_name", length=128,
                      default=""),
                Field("email", length=255, unique=True,
                      default=""),
                # Used For chat in default deployment config
                Field("username", length=255, default="",
                      readable=False, writable=False),
                Field("language", length=16,
                      default = deployment_settings.get_L10n_default_language()),
                Field("organisation_id", "integer",
                      readable=False, writable=False),
                Field("org_group_id", "integer",
                      readable=False, writable=False),
                Field("site_id", "integer",
                      readable=False, writable=False),
                Field("link_user_to", "list:string",
                      readable=False, writable=False),
                Field("registration_key", length=512,
                      default="",
                      readable=False, writable=False),
                Field("reset_password_key", length=512,
                      default="",
                      readable=False, writable=False),
                Field("deleted", "boolean",
                      default=False,
                      readable=False, writable=False),
                Field("timestmp", "datetime",
                      default="",
                      readable=False, writable=False),
                s3_comments(readable=False, writable=False),
                # Additional meta fields required for sync:
                S3MetaFields.uuid(),
                #S3MetaFields.mci(),
                S3MetaFields.created_on(),
                S3MetaFields.modified_on(),
                ]

            userfield = settings.login_userfield
            if userfield != "email":
                # Use username (not used by default in Sahana)
                utable_fields.insert(2, Field(userfield,
                                              length = 128,
                                              default = "",
                                              unique = True,
                                              ))

            # Insert password field after either email or username
            passfield = settings.password_field
            utable_fields.insert(3, Field(passfield, "password", length=512,
                                          requires = CRYPT(key = settings.hmac_key,
                                                           min_length = deployment_settings.get_auth_password_min_length(),
                                                           digest_alg = "sha512"),
                                          readable = False,
                                          label = messages.label_password,
                                          ))

            define_table(uname,
                         migrate = migrate,
                         fake_migrate = fake_migrate,
                         *utable_fields)
            utable = settings.table_user = db[uname]

        # Group table (roles)
        gtable = settings.table_group
        gname = settings.table_group_name
        if not gtable:
            define_table(gname,
                # Group unique ID, must be notnull+unique:
                Field("uuid", length=64, notnull=True, unique=True,
                      readable=False, writable=False),
                # Group does not appear in the Role Manager:
                # (can neither assign, nor modify, nor delete)
                Field("hidden", "boolean",
                      readable=False, writable=False,
                      default=False),
                # Group cannot be modified in the Role Manager:
                # (can assign, but neither modify nor delete)
                Field("system", "boolean",
                      readable=False, writable=False,
                      default=False),
                # Group cannot be deleted in the Role Manager:
                # (can assign and modify, but not delete)
                Field("protected", "boolean",
                      readable=False, writable=False,
                      default=False),
                # Role name:
                Field("role", length=255, unique=True,
                      default="",
                      requires = IS_NOT_IN_DB(db, "%s.role" % gname),
                      label=messages.label_role),
                Field("description", "text",
                      label=messages.label_description),
                # Additional meta fields required for sync:
                S3MetaFields.created_on(),
                S3MetaFields.modified_on(),
                S3MetaFields.deleted(),
                #S3MetaFields.deleted_fk(),
                #S3MetaFields.deleted_rb(),
                migrate = migrate,
                fake_migrate=fake_migrate,
                )
            gtable = settings.table_group = db[gname]

        # Group membership table (user<->role)
        if not settings.table_membership:
            define_table(
                settings.table_membership_name,
                Field("user_id", utable,
                      requires = IS_IN_DB(db, "%s.id" % uname,
                                          "%(id)s: %(first_name)s %(last_name)s"),
                      label=messages.label_user_id),
                Field("group_id", gtable,
                      requires = IS_IN_DB(db, "%s.id" % gname,
                                          "%(id)s: %(role)s"),
                      represent = S3Represent(lookup=gname, fields=["role"]),
                      label=messages.label_group_id),
                # Realm
                Field("pe_id", "integer"),
                migrate = migrate,
                fake_migrate=fake_migrate,
                *S3MetaFields.sync_meta_fields())
            settings.table_membership = db[settings.table_membership_name]

        # Define Eden permission table
        self.permission.define_table(migrate=migrate,
                                     fake_migrate=fake_migrate)

        #security_policy = deployment_settings.get_security_policy()
        #if security_policy not in (1, 2, 3, 4, 5, 6, 7, 8) and \
        #   not settings.table_permission:
        #    # Permissions table (group<->permission)
        #    # NB This Web2Py table is deprecated / replaced in Eden by S3Permission
        #    settings.table_permission = define_table(
        #        settings.table_permission_name,
        #        Field("group_id", gtable,
        #              requires = IS_IN_DB(db, "%s.id" % gname,
        #                                  "%(id)s: %(role)s"),
        #              label=messages.label_group_id),
        #        Field("name", default="default", length=512,
        #              requires = IS_NOT_EMPTY(),
        #              label=messages.label_name),
        #        Field("table_name", length=512,
        #              # Needs to be defined after all tables created
        #              #requires = IS_IN_SET(db.tables),
        #              label=messages.label_table_name),
        #        Field("record_id", "integer",
        #              requires = IS_INT_IN_RANGE(0, 10 ** 9),
        #              label=messages.label_record_id),
        #        migrate = migrate,
        #        fake_migrate=fake_migrate)

        # Event table (auth_event)
        # Records Logins & ?
        # @ToDo: Move to s3db.auth to prevent it from being defined every request
        #        (lazy tables means no big issue for Production but helps Devs)
        # Deprecate?
        # - date of most recent login is the most useful thing recorded, which we already record in the main auth_user table
        if not settings.table_event:
            request = current.request
            define_table(
                settings.table_event_name,
                Field("time_stamp", "datetime",
                      default = request.utcnow,
                      #label = messages.label_time_stamp
                      ),
                Field("client_ip",
                      default = request.client,
                      #label=messages.label_client_ip
                      ),
                Field("user_id", utable,
                      default = None,
                      requires = IS_IN_DB(db, "%s.id" % uname,
                                          "%(id)s: %(first_name)s %(last_name)s"),
                      #label=messages.label_user_id
                      ),
                Field("origin", length=512,
                      default = "auth",
                      #label = messages.label_origin,
                      requires = IS_NOT_EMPTY(),
                      ),
                Field("description", "text",
                      default = "",
                      #label = messages.label_description,
                      requires = IS_NOT_EMPTY(),
                      ),
                migrate = migrate,
                fake_migrate=fake_migrate,
                *S3MetaFields.sync_meta_fields())
            settings.table_event = db[settings.table_event_name]

    # -------------------------------------------------------------------------
    def login_bare(self, username, password):
        """
            Logs user in
                - extended to understand session.s3.roles
        """

        settings = self.settings
        utable = settings.table_user
        userfield = settings.login_userfield
        passfield = settings.password_field
        query = (utable[userfield] == username)
        user = current.db(query).select(limitby=(0, 1)).first()
        password = utable[passfield].validate(password)[0]
        if user:
            if not user.registration_key and user[passfield] == password:
                user = Storage(utable._filter_fields(user, id=True))
                current.session.auth = Storage(user=user,
                                               last_visit=current.request.now,
                                               expiration=settings.expiration)
                self.user = user
                self.s3_set_roles()
                return user
        return False

    # -------------------------------------------------------------------------
    @staticmethod
    def set_cookie():
        """
            Set a Cookie to the client browser so that we know this user has
            registered & so we should present them with a login form instead
            of a register form
        """

        cookies = current.response.cookies

        cookies["registered"] = "yes"
        cookies["registered"]["expires"] = 365 * 24 * 3600 # 1 year
        cookies["registered"]["path"] = "/"

    # -------------------------------------------------------------------------
    def login(self,
              next = DEFAULT,
              onvalidation = DEFAULT,
              onaccept = DEFAULT,
              log = DEFAULT,
              inline = False, # Set to True to use an 'inline' variant of the style
              lost_pw_link = None,
              register_link = True,
              ):
        """
            Overrides Web2Py's login() to use custom flash styles & utcnow

            @return: a login form
        """

        T = current.T
        db = current.db
        messages = self.messages
        request = current.request
        response = current.response
        session = current.session
        settings = self.settings
        deployment_settings = current.deployment_settings

        utable = settings.table_user
        userfield = settings.login_userfield
        old_requires = utable[userfield].requires
        utable[userfield].requires = [IS_NOT_EMPTY(), IS_LOWER()]
        passfield = settings.password_field
        try:
            utable[passfield].requires[-1].min_length = 0
        except:
            pass
        if onvalidation is DEFAULT:
            onvalidation = settings.login_onvalidation
        if onaccept is DEFAULT:
            onaccept = settings.login_onaccept
        if log is DEFAULT:
            log = messages.login_log

        user = None # default

        response.title = T("Login")

        # Do we use our own login form, or from a central source?
        if settings.login_form == self:

            if inline:
                formstyle = deployment_settings.get_ui_inline_formstyle()
            else:
                formstyle = deployment_settings.get_ui_formstyle()

            buttons = []

            # Self-registration action link
            self_registration = deployment_settings.get_security_registration_visible()
            if self_registration and register_link:
                if self_registration == "index":
                    # Custom Registration page
                    controller = "index"
                else:
                    # Default Registration page
                    controller = "user"
                register_link = A(T("Register for Account"),
                                  _href=URL(f=controller, args="register"),
                                  _id="register-btn",
                                  _class="action-lnk",
                                  )
                buttons.append(register_link)

            # Lost-password action link
            if deployment_settings.get_auth_password_retrieval():
                if lost_pw_link is None:
                    lost_pw_link = deployment_settings.get_auth_password_changes()
                if lost_pw_link:
                    lost_pw_link = A(T("Lost Password"),
                                     _href=URL(f="user", args="retrieve_password"),
                                     _class="action-lnk",
                                     )
                    buttons.append(lost_pw_link)

            # Add submit button
            #if buttons:
            submit_button = INPUT(_type="submit", _value=T("Login"))
            buttons.insert(0, submit_button)

            form = SQLFORM(utable,
                           fields = [userfield, passfield],
                           hidden = dict(_next=request.vars._next),
                           showid = settings.showid,
                           submit_button = T("Login"),
                           delete_label = messages.delete_label,
                           formstyle = formstyle,
                           separator = settings.label_separator,
                           buttons = buttons,
                           )

            # Identify form for CSS
            form.add_class("auth_login")

            if settings.remember_me_form:
                # Add a new input checkbox "remember me for longer"
                s3_addrow(form,
                          "",
                          DIV(INPUT(_type="checkbox",
                                    _class="checkbox",
                                    _id="auth_user_remember",
                                    _name="remember",
                                    ),
                              LABEL(messages.label_remember_me,
                                    _for="auth_user_remember",
                                    ),
                              ),
                          "",
                          formstyle,
                          "auth_user_remember__row",
                          )

            if deployment_settings.get_auth_set_presence_on_login():
                s3_addrow(form,
                          "",
                          INPUT(_id="auth_user_clientlocation",
                                _name="auth_user_clientlocation",
                                _style="display:none",
                                ),
                          "",
                          formstyle,
                          "auth_user_client_location",
                          )
                response.s3.jquery_ready.append('''S3.getClientLocation($('#auth_user_clientlocation'))''')

            captcha = settings.login_captcha or \
                (settings.login_captcha != False and settings.captcha)
            if captcha:
                s3_addrow(form,
                          captcha.label,
                          captcha,
                          captcha.comment,
                          formstyle,
                          "captcha__row",
                          )

            accepted_form = False
            if form.accepts(request.post_vars, session,
                            formname="login", dbio=False,
                            onvalidation=onvalidation):
                accepted_form = True
                if userfield == "email":
                    # Check for Domains which can use Google's SMTP server for passwords
                    # @ToDo: an equivalent email_domains for other email providers
                    gmail_domains = deployment_settings.get_auth_gmail_domains()
                    office365_domains = deployment_settings.get_auth_office365_domains()
                    if gmail_domains or office365_domains:
                        from gluon.contrib.login_methods.email_auth import email_auth
                        domain = form.vars[userfield].split("@")[1]
                        if domain in gmail_domains:
                            settings.login_methods.append(
                                email_auth("smtp.gmail.com:587", "@%s" % domain))
                        elif domain in office365_domains:
                            settings.login_methods.append(
                                email_auth("smtp.office365.com:587", "@%s" % domain))

                # Check for username in db
                query = (utable[userfield] == form.vars[userfield])
                user = db(query).select(limitby=(0, 1)).first()
                if user:
                    # User in db, check if registration pending or disabled
                    temp_user = user
                    if temp_user.registration_key == "pending":
                        response.warning = deployment_settings.get_auth_registration_pending()
                        return form
                    elif temp_user.registration_key in ("disabled", "blocked"):
                        response.error = messages.login_disabled
                        return form
                    elif not temp_user.registration_key is None and \
                             temp_user.registration_key.strip():
                        response.warning = \
                            messages.registration_verifying
                        return form
                    # Try alternate logins 1st as these have the
                    # current version of the password
                    user = None
                    for login_method in settings.login_methods:
                        if login_method != self and \
                                login_method(request.vars[userfield],
                                             request.vars[passfield]):
                            if not self in settings.login_methods:
                                # do not store password in db
                                form.vars[passfield] = None
                            user = self.get_or_create_user(form.vars)
                            break
                    if not user:
                        # Alternates have failed, maybe because service inaccessible
                        if settings.login_methods[0] == self:
                            # Try logging in locally using cached credentials
                            if temp_user[passfield] == form.vars.get(passfield, ""):
                                # Success
                                user = temp_user
                else:
                    # User not in db
                    if not settings.alternate_requires_registration:
                        # We're allowed to auto-register users from external systems
                        for login_method in settings.login_methods:
                            if login_method != self and \
                                    login_method(request.vars[userfield],
                                                 request.vars[passfield]):
                                if not self in settings.login_methods:
                                    # Do not store password in db
                                    form.vars[passfield] = None
                                # Ensure new users go through their post registration tasks
                                register_onaccept = settings.register_onaccept
                                if register_onaccept:
                                    settings.register_onaccept = \
                                        [self.s3_register_onaccept,
                                         register_onaccept, # Used by DRRPP
                                         ]
                                else:
                                    settings.register_onaccept = self.s3_register_onaccept
                                user = self.get_or_create_user(form.vars)
                                break
                if not user:
                    self.log_event(settings.login_failed_log,
                                   request.post_vars)
                    # Invalid login
                    session.error = messages.invalid_login
                    if inline:
                        # If inline, stay on the same page
                        next_url = URL(args=request.args,
                                       vars=request.get_vars)
                    else:
                        # If not inline, return to configured login page
                        next_url = self.url(args=request.args,
                                            vars=request.get_vars)
                    redirect(next_url)
        else:
            # Use a central authentication server
            cas = settings.login_form
            cas_user = cas.get_user()
            if cas_user:
                cas_user[passfield] = None
                # Ensure new users go through their post registration tasks
                register_onaccept = settings.register_onaccept
                if register_onaccept:
                    settings.register_onaccept = \
                        [self.s3_register_onaccept,
                         register_onaccept, # Used by DRRPP
                         ]
                else:
                    settings.register_onaccept = self.s3_register_onaccept
                user = self.get_or_create_user(utable._filter_fields(cas_user))
            elif hasattr(cas, "login_form"):
                return cas.login_form()
            else:
                # We need to pass through login again before going on
                if next is DEFAULT:
                    next = request.vars._next or deployment_settings.get_auth_login_next()
                next = "%s?_next=%s" % (URL(r=request), next)
                redirect(cas.login_url(next))

        # Process authenticated users
        if user:
            user = Storage(utable._filter_fields(user, id=True))
            self.login_user(user)
        if log and self.user:
            self.log_event(log, self.user)

        # How to continue
        if next is DEFAULT:
            if deployment_settings.has_module("setup") and \
               deployment_settings.get_setup_wizard_questions() and \
               self.s3_has_role("ADMIN"):
                itable = current.s3db.setup_instance
                instance = db(itable.url == "https://%s" % request.env.HTTP_HOST).select(itable.id,
                                                                                         itable.deployment_id,
                                                                                         itable.configured,
                                                                                         limitby = (0, 1)
                                                                                         ).first()
                if instance and not instance.configured:
                    # Run Configuration Wizard
                    next = URL(c="setup", f="deployment",
                               args = [instance.deployment_id, "instance", instance.id, "wizard"])
            if next is DEFAULT:
                if deployment_settings.get_auth_login_next_always():
                    next = deployment_settings.get_auth_login_next()
                    if callable(next):
                        next = next()
                else:
                    next = request.vars.get("_next")
                    if not next:
                        next = deployment_settings.get_auth_login_next()
                        if callable(next):
                            next = next()
        if settings.login_form == self:
            if accepted_form:
                if onaccept:
                    onaccept(form)
                if isinstance(next, (list, tuple)):
                    # fix issue with 2.6/2.7
                    next = next[0]
                if next and not next[0] == "/" and next[:4] != "http":
                    next = self.url(next.replace("[id]", str(form.vars.id)))
                redirect(next)
            utable[userfield].requires = old_requires
            return form
        else:
            redirect(next)

    # -------------------------------------------------------------------------
    def change_password(self,
                        next=DEFAULT,
                        onvalidation=DEFAULT,
                        onaccept=DEFAULT,
                        log=DEFAULT,
                        ):
        """
            Returns a form that lets the user change password
        """

        if not self.is_logged_in():
            redirect(self.settings.login_url,
                     client_side=self.settings.client_side)

        messages = self.messages
        settings = self.settings
        utable = settings.table_user
        s = self.db(utable.id == self.user.id)

        request = current.request
        session = current.session
        if next is DEFAULT:
            next = self.get_vars_next() or settings.change_password_next
        if onvalidation is DEFAULT:
            onvalidation = settings.change_password_onvalidation
        if onaccept is DEFAULT:
            onaccept = settings.change_password_onaccept
        if log is DEFAULT:
            log = messages["change_password_log"]
        passfield = settings.password_field
        form = SQLFORM.factory(
            Field("old_password", "password",
                  label=messages.old_password,
                  requires=utable[passfield].requires),
            Field("new_password", "password",
                  label=messages.new_password,
                  requires=utable[passfield].requires),
            Field("new_password2", "password",
                  label=messages.verify_password,
                  requires=[IS_EXPR(
                    "value==%s" % repr(request.vars.new_password),
                              messages.mismatched_password)]),
            submit_button=messages.password_change_button,
            hidden=dict(_next=next),
            formstyle=current.deployment_settings.get_ui_formstyle(),
            separator=settings.label_separator
        )
        form.add_class("auth_change_password")

        if form.accepts(request, session,
                        formname="change_password",
                        onvalidation=onvalidation,
                        hideerror=settings.hideerror):

            if not form.vars["old_password"] == s.select(limitby=(0,1), orderby_on_limitby=False).first()[passfield]:
                form.errors["old_password"] = messages.invalid_password
            else:
                d = {passfield: str(form.vars.new_password)}
                s.update(**d)
                session.confirmation = messages.password_changed
                self.log_event(log, self.user)
                callback(onaccept, form)
                if not next:
                    next = self.url(args=request.args)
                else:
                    next = replace_id(next, form)
                redirect(next, client_side=settings.client_side)

        return form

    # -------------------------------------------------------------------------
    def reset_password(self,
                       next=DEFAULT,
                       onvalidation=DEFAULT,
                       onaccept=DEFAULT,
                       log=DEFAULT,
                       ):
        """
            Returns a form to reset the user password, overrides web2py's
            version of the method to not swallow the _next var.
        """

        table_user = self.table_user()
        request = current.request
        session = current.session

        messages = self.messages
        settings = self.settings

        if next is DEFAULT:
            next = self.get_vars_next() or settings.reset_password_next

        if settings.prevent_password_reset_attacks:
            key = request.vars.key
            if key:
                session._reset_password_key = key
                session._reset_password_next = next
                redirect(self.url(args = "reset_password"))
            else:
                key = session._reset_password_key
                next = session._reset_password_next
        else:
            key = request.vars.key

        try:
            t0 = int(key.split('-')[0])
            if time.time() - t0 > 60 * 60 * 24:
                raise Exception
            user = table_user(reset_password_key=key)
            if not user:
                raise Exception
        except Exception:
            session.flash = messages.invalid_reset_password
            redirect(next, client_side=settings.client_side)

        key = user.registration_key
        if key in ("pending", "disabled", "blocked") or (key or "").startswith("pending"):
            session.flash = messages.registration_pending
            redirect(next, client_side=settings.client_side)

        if onvalidation is DEFAULT:
            onvalidation = settings.reset_password_onvalidation
        if onaccept is DEFAULT:
            onaccept = settings.reset_password_onaccept

        passfield = settings.password_field
        form = SQLFORM.factory(
            Field("new_password", "password",
                  label = messages.new_password,
                  requires = table_user[passfield].requires,
                  ),
            Field("new_password2", "password",
                  label = messages.verify_password,
                  requires = [IS_EXPR("value==%s" % repr(request.vars.new_password),
                              messages.mismatched_password)
                              ],
                  ),
            submit_button = messages.password_reset_button,
            hidden = {"_next": next},
            formstyle = settings.formstyle,
            separator = settings.label_separator
            )
        if form.accepts(request, session, onvalidation=onvalidation,
                        hideerror=settings.hideerror):
            user.update_record(
                **{passfield: str(form.vars.new_password),
                   "registration_key": "",
                   "reset_password_key": "",
                   })
            session.flash = messages.password_changed
            if settings.login_after_password_change:
                self.login_user(user)
            callback(onaccept, form)
            redirect(next, client_side=settings.client_side)
        return form

    # -------------------------------------------------------------------------
    def request_reset_password(self,
                               next=DEFAULT,
                               onvalidation=DEFAULT,
                               onaccept=DEFAULT,
                               log=DEFAULT,
                               ):
        """
            Returns a form to reset the user password, overrides web2py's
            version of the method to apply Eden formstyles.

            @param next: URL to redirect to after successful form submission
            @param onvalidation: callback to validate password reset form
            @param onaccept: callback to post-process password reset request
            @param log: event description for the log (string)
        """

        messages = self.messages
        settings = self.settings
        if not settings.mailer:
            current.response.error = messages.function_disabled
            return ""

        utable = settings.table_user
        request = current.request
        session = current.session
        captcha = settings.retrieve_password_captcha or \
                  (settings.retrieve_password_captcha != False and settings.captcha)

        if next is DEFAULT:
            next = self.get_vars_next() or settings.request_reset_password_next
        if onvalidation is DEFAULT:
            onvalidation = settings.reset_password_onvalidation
        if onaccept is DEFAULT:
            onaccept = settings.reset_password_onaccept
        if log is DEFAULT:
            log = messages["reset_password_log"]
        userfield = settings.login_userfield
        if userfield == "email":
            utable.email.requires = [
                IS_EMAIL(error_message=messages.invalid_email),
                IS_IN_DB(self.db, utable.email,
                         error_message=messages.invalid_email)]
        else:
            utable[userfield].requires = [
                IS_IN_DB(self.db, utable[userfield],
                         error_message=messages.invalid_username)]
        form = SQLFORM(utable,
                       fields = [userfield],
                       hidden = dict(_next=next),
                       showid = settings.showid,
                       submit_button = messages.password_reset_button,
                       delete_label = messages.delete_label,
                       formstyle = current.deployment_settings.get_ui_formstyle(),
                       separator = settings.label_separator
                       )
        form.add_class("auth_reset_password")
        if captcha:
            s3_addrow(form, captcha.label, captcha,
                      captcha.comment, settings.formstyle, "captcha__row")
        if form.accepts(request, session if self.csrf_prevention else None,
                        formname="reset_password", dbio=False,
                        onvalidation=onvalidation,
                        hideerror=settings.hideerror):
            user = utable(**{userfield:form.vars.get(userfield)})
            if not user:
                session.error = messages["invalid_%s" % userfield]
                redirect(self.url(args=request.args),
                         client_side=settings.client_side)
            elif user.registration_key in ("pending", "disabled", "blocked"):
                session.warning = messages.registration_pending
                redirect(self.url(args=request.args),
                         client_side=settings.client_side)
            if self.email_reset_password(user):
                session.confirmation = messages.email_sent
            else:
                session.error = messages.unable_to_send_email
            self.log_event(log, user)
            callback(onaccept, form)
            if not next:
                next = self.url(args=request.args)
            else:
                next = replace_id(next, form)
            redirect(next, client_side=settings.client_side)
        # old_requires = utable.email.requires
        return form

    # -------------------------------------------------------------------------
    def login_user(self, user):
        """
            Log the user in
            - common function called by login() & register()
        """

        db = current.db
        deployment_settings = current.deployment_settings
        request = current.request
        session = current.session
        settings = self.settings
        req_vars = request.vars

        session.auth = Storage(
            user=user,
            last_visit=request.now,
            expiration = req_vars.get("remember", False) and \
                settings.long_expiration or settings.expiration,
            remember = "remember" in req_vars,
            hmac_key = web2py_uuid()
            )
        self.user = user
        self.s3_set_roles()

        # Set a Cookie to present user with login box by default
        self.set_cookie()

        # Read their language from the Profile
        language = user.language
        current.T.force(language)
        session.s3.language = language

        session.confirmation = self.messages.logged_in

        # Update the timestamp of the User so we know when they last logged-in
        utable = settings.table_user
        db(utable.id == self.user.id).update(timestmp = request.utcnow)

        # Set user's position
        # @ToDo: Per-User settings
        client_location = req_vars.get("auth_user_clientlocation")
        if deployment_settings.get_auth_set_presence_on_login() and client_location:
            position = client_location.split("|", 3)
            userlat = float(position[0])
            userlon = float(position[1])
            accuracy = float(position[2]) / 1000 # Ensures accuracy is in km
            closestpoint = 0
            closestdistance = 0
            gis = current.gis
            # @ToDo: Filter to just Sites & Home Addresses?
            locations = gis.get_features_in_radius(userlat, userlon, accuracy)

            ignore_levels_for_presence = deployment_settings.get_auth_ignore_levels_for_presence()
            greatCircleDistance = gis.greatCircleDistance
            for location in locations:
                if location.level not in ignore_levels_for_presence:
                    if closestpoint != 0:
                        currentdistance = greatCircleDistance(closestpoint.lat,
                                                              closestpoint.lon,
                                                              location.lat,
                                                              location.lon)
                        if currentdistance < closestdistance:
                            closestpoint = location
                            closestdistance = currentdistance
                    else:
                        closestpoint = location

            s3tracker = S3Tracker()
            person_id = self.s3_logged_in_person()
            if closestpoint == 0 and deployment_settings.get_auth_create_unknown_locations():
                # There wasn't any near-by location, so create one
                newpoint = {"lat": userlat,
                            "lon": userlon,
                            "name": "Waypoint"
                            }
                closestpoint = current.s3db.gis_location.insert(**newpoint)
                s3tracker(db.pr_person,
                          person_id).set_location(closestpoint,
                                                  timestmp=request.utcnow)
            elif closestpoint != 0:
                s3tracker(db.pr_person,
                          person_id).set_location(closestpoint,
                                                  timestmp=request.utcnow)

    # -------------------------------------------------------------------------
    def register(self,
                 next = DEFAULT,
                 onvalidation = DEFAULT,
                 onaccept = DEFAULT,
                 log = DEFAULT,
                 js_validation = True, # Set to False if using custom validation
                 ):
        """
            Overrides Web2Py's register() to add new functionality:
                - Checks whether registration is permitted
                - Custom Flash styles
                - Allow form to be embedded in other pages
                - Optional addition of Mobile Phone field to the Register form
                - Optional addition of Organisation field to the Register form

                - Lookup Domains/Organisations to check for Whitelists
                  &/or custom Approver

            @return: a registration form
        """

        T = current.T
        db = current.db
        settings = self.settings
        messages = self.messages
        request = current.request
        session = current.session
        deployment_settings = current.deployment_settings

        # Customise the resource
        customise = deployment_settings.customise_resource("auth_user")
        if customise:
            customise(request, "auth_user")

        utable = self.settings.table_user
        utablename = utable._tablename
        passfield = settings.password_field

        # S3: Don't allow registration if disabled
        if not deployment_settings.get_security_self_registration():
            session.error = messages.registration_disabled
            redirect(URL(args=["login"]))

        if self.is_logged_in() and request.function != "index":
            redirect(settings.logged_url)

        if next == DEFAULT:
            next = request.vars._next or settings.register_next
        if onvalidation == DEFAULT:
            onvalidation = settings.register_onvalidation
        if onaccept == DEFAULT:
            # Usually empty, other than DRRPP template or
            #                           registration via LDAP, OAuth
            onaccept = settings.register_onaccept
        if log == DEFAULT:
            log = messages.register_log

        labels = s3_mark_required(utable)[0]

        formstyle = deployment_settings.get_ui_formstyle()
        REGISTER = T("Register")
        buttons = [INPUT(_type="submit", _value=REGISTER),
                   A(T("Login"),
                     _href=URL(f="user", args="login"),
                     _id="login-btn",
                     _class="action-lnk",
                     ),
                   ]
        current.response.form_label_separator = ""
        form = SQLFORM(utable,
                       hidden = dict(_next=request.vars._next),
                       labels = labels,
                       separator = "",
                       showid = settings.showid,
                       submit_button = REGISTER,
                       delete_label = messages.delete_label,
                       formstyle = formstyle,
                       buttons = buttons,
                       )

        # Identify form for CSS & JS Validation
        form.add_class("auth_register")

        if js_validation:
            # Client-side Validation
            self.s3_register_validation()

        # Insert a Password-confirmation field
        for i, row in enumerate(form[0].components):
            item = row.element("input", _name=passfield)
            if item:
                field_id = "%s_password_two" % utablename
                s3_addrow(form,
                          LABEL(DIV("%s:" % messages.verify_password,
                                    SPAN("*", _class="req"),
                                    _for="password_two",
                                    _id=field_id + SQLFORM.ID_LABEL_SUFFIX,
                                    ),
                                ),
                          INPUT(_name="password_two",
                                _id=field_id,
                                _type="password",
                                requires=IS_EXPR("value==%s" % \
                                    repr(request.vars.get(passfield, None)),
                                error_message=messages.mismatched_password)
                                ),
                          "",
                          formstyle,
                          field_id + SQLFORM.ID_ROW_SUFFIX,
                          position = i + 1,
                          )

        # Add an opt in clause to receive emails depending on the deployment settings
        # @ToDo: Replace with Consent Tracking
        if deployment_settings.get_auth_opt_in_to_email():
            field_id = "%s_opt_in" % utablename
            comment = DIV(DIV(_class="tooltip",
                              _title="%s|%s" % (T("Mailing list"),
                                                T("By selecting this you agree that we may contact you."))))
            checked = deployment_settings.get_auth_opt_in_default() and "selected"
            s3_addrow(form,
                      LABEL("%s:" % T("Receive updates"),
                            _for="opt_in",
                            _id=field_id + SQLFORM.ID_LABEL_SUFFIX,
                            ),
                      INPUT(_name="opt_in", _id=field_id, _type="checkbox", _checked=checked),
                      comment,
                      formstyle,
                      field_id + SQLFORM.ID_ROW_SUFFIX,
                      )

        # S3: Insert Home phone field into form
        if deployment_settings.get_auth_registration_requests_home_phone():
            for i, row in enumerate(form[0].components):
                item = row.element("input", _name="email")
                if item:
                    field_id = "%s_home" % utablename
                    s3_addrow(form,
                              LABEL("%s:" % T("Home Phone"),
                                    _for="home",
                                    _id=field_id + SQLFORM.ID_LABEL_SUFFIX,
                                    ),
                              INPUT(_name="home", _id=field_id),
                              "",
                              formstyle,
                              field_id + SQLFORM.ID_ROW_SUFFIX,
                              position = i + 1,
                              )

        # S3: Insert Mobile phone field into form
        if deployment_settings.get_auth_registration_requests_mobile_phone():
            for i, row in enumerate(form[0].components):
                item = row.element("input", _name="email")
                if item:
                    field_id = "%s_mobile" % utablename
                    if deployment_settings.get_auth_registration_mobile_phone_mandatory():
                        mandatory = SPAN("*", _class="req")
                        comment = ""
                    else:
                        mandatory = ""
                        comment = DIV(_class="tooltip",
                                      _title="%s|%s" % (deployment_settings.get_ui_label_mobile_phone(),
                                                        messages.help_mobile_phone))
                    s3_addrow(form,
                              LABEL("%s:" % deployment_settings.get_ui_label_mobile_phone(),
                                    mandatory,
                                    _for="mobile",
                                    _id=field_id + SQLFORM.ID_LABEL_SUFFIX,
                                    ),
                              INPUT(_name="mobile", _id=field_id),
                              comment,
                              formstyle,
                              field_id + SQLFORM.ID_ROW_SUFFIX,
                              position = i + 1,
                              )

        # S3: Insert Photo widget into form
        if deployment_settings.get_auth_registration_requests_image():
            label = self.messages.label_image
            comment = DIV(_class="stickytip",
                          _title="%s|%s" % (label,
                                            self.messages.help_image % \
                                                dict(gravatar = A("Gravatar",
                                                                  _target="top",
                                                                  _href="http://gravatar.com"))))
            field_id = "%s_image" % utablename
            widget = SQLFORM.widgets["upload"].widget(current.s3db.pr_image.image, None)
            s3_addrow(form,
                      LABEL("%s:" % label,
                            _for="image",
                            _id=field_id + SQLFORM.ID_LABEL_SUFFIX,
                            ),
                      widget,
                      comment,
                      formstyle,
                      field_id + SQLFORM.ID_ROW_SUFFIX,
                      )

        # @ToDo: Replace with Consent Tracking
        if deployment_settings.get_auth_terms_of_service():
            field_id = "%s_tos" % utablename
            label = T("I agree to the %(terms_of_service)s") % \
                dict(terms_of_service=A(T("Terms of Service"),
                                        _href=URL(c="default", f="tos"),
                                        _target="_blank",
                                        ))
            label = XML("%s:" % label)
            s3_addrow(form,
                      LABEL(label,
                            _for="tos",
                            _id=field_id + SQLFORM.ID_LABEL_SUFFIX,
                            ),
                      INPUT(_name="tos",
                            _id=field_id,
                            _type="checkbox",
                            ),
                      "",
                      formstyle,
                      field_id + SQLFORM.ID_ROW_SUFFIX,
                      )

        if settings.captcha != None:
            form[0].insert(-1, DIV("", settings.captcha, ""))

        utable.registration_key.default = key = str(uuid4())

        if form.accepts(request.vars, session, formname="register",
                        onvalidation=onvalidation):

            # Save temporary user fields
            self.s3_user_register_onaccept(form)

            users = db(utable.id > 0).select(utable.id,
                                             limitby=(0, 2))
            if len(users) == 1:
                # 1st user to register doesn't need verification/approval
                self.s3_approve_user(form.vars)
                current.session.confirmation = self.messages.registration_successful

                # 1st user gets Admin rights
                admin_group_id = 1
                self.add_membership(admin_group_id, users.first().id)

                # Log them in
                if "language" not in form.vars:
                    # Was missing from login form
                    form.vars.language = T.accepted_language
                user = Storage(utable._filter_fields(form.vars, id=True))
                self.login_user(user)

                self.s3_send_welcome_email(form.vars)

            elif settings.registration_requires_verification:
                # Send the Verification email
                if not settings.mailer or \
                   not settings.mailer.settings.server or \
                   not settings.mailer.send(to=form.vars.email,
                                            subject=messages.verify_email_subject % \
    dict(system_name=deployment_settings.get_system_name()),
                                            message=messages.verify_email % \
            dict(url="%s/default/user/verify_email/%s" % \
                (current.response.s3.base_url, key))):
                    current.response.error = messages.email_verification_failed
                    return form
                # @ToDo: Deployment Setting?
                #session.confirmation = messages.email_sent
                next = URL(c="default", f="message",
                           args = ["verify_email_sent"],
                           vars = {"email": form.vars.email})

            else:
                # Does the user need to be approved?
                approved = self.s3_verify_user(form.vars)

                if approved:
                    # Log them in
                    if "language" not in form.vars:
                        # Was missing from login form
                        form.vars.language = T.accepted_language
                    user = Storage(utable._filter_fields(form.vars, id=True))
                    self.login_user(user)

            # Set a Cookie to present user with login box by default
            self.set_cookie()

            if log:
                self.log_event(log, form.vars)
            if onaccept:
                onaccept(form)
            if not next:
                next = self.url(args = request.args)
            elif isinstance(next, (list, tuple)):
                # fix issue with 2.6
                next = next[0]
            elif next and not next[0] == "/" and next[:4] != "http":
                next = self.url(next.replace("[id]", str(form.vars.id)))
            redirect(next)

        return form

    # -------------------------------------------------------------------------
    def email_reset_password(self, user):
        """
             Overrides Web2Py's email_reset_password() to modify the message
             structure

             @param user: the auth_user record (Row)
        """

        mailer = self.settings.mailer
        if not mailer or not mailer.settings.server:
            return False

        reset_password_key = str(int(time.time())) + '-' + web2py_uuid()
        reset_password_url = "%s/default/user/reset_password?key=%s" % \
                             (current.response.s3.base_url, reset_password_key)

        message = self.messages.reset_password % dict(url=reset_password_url)
        if mailer.send(to=user.email,
                       subject=self.messages.reset_password_subject,
                       message=message):
            user.update_record(reset_password_key=reset_password_key)
            return True

        return False

    # -------------------------------------------------------------------------
    def add_membership(self, group_id=None, user_id=None, role=None,
                       entity=None):
        """
            gives user_id membership of group_id or role
            if user is None than user_id is that of current logged in user
            S3: extended to support Entities
        """

        group_id = group_id or self.id_group(role)
        try:
            group_id = int(group_id)
        except:
            group_id = self.id_group(group_id) # interpret group_id as a role
        if not user_id and self.user:
            user_id = self.user.id
        membership = self.settings.table_membership
        record = membership(user_id=user_id, group_id=group_id, pe_id=entity)
        if record:
            return record.id
        else:
            membership_id = membership.insert(group_id = group_id,
                                              user_id = user_id,
                                              pe_id = entity)
        self.update_groups()
        self.log_event(self.messages.add_membership_log,
                       {"user_id": user_id,
                        "group_id": group_id,
                        })
        return membership_id

    # -------------------------------------------------------------------------
    def verify_email(self,
                     next=DEFAULT,
                     log=DEFAULT):
        """
            action user to verify the registration email, XXXXXXXXXXXXXXXX

            .. method:: Auth.verify_email([next=DEFAULT [, onvalidation=DEFAULT
                [, log=DEFAULT]]])
        """

        settings = self.settings
        request = current.request

        # Customise the resource
        customise = current.deployment_settings.customise_resource("auth_user")
        if customise:
            customise(request, "auth_user")

        key = request.args[-1]
        utable = settings.table_user
        query = (utable.registration_key == key)
        user = current.db(query).select(limitby=(0, 1)).first()
        if not user:
            redirect(settings.verify_email_next)

        if log == DEFAULT:
            log = self.messages.verify_email_log
        if next == DEFAULT:
            next = settings.verify_email_next

        approved = self.s3_verify_user(user)

        if approved:
            # Log them in
            user = Storage(utable._filter_fields(user, id=True))
            self.login_user(user)

        if log:
            self.log_event(log, user)

        redirect(next)

    # -------------------------------------------------------------------------
    def profile(self,
                next=DEFAULT,
                onvalidation=DEFAULT,
                onaccept=DEFAULT,
                log=DEFAULT,
                ):
        """
            returns a form that lets the user change his/her profile

            .. method:: Auth.profile([next=DEFAULT [, onvalidation=DEFAULT
                [, onaccept=DEFAULT [, log=DEFAULT]]]])

            Patched for S3 to use s3_mark_required and handle opt_in mailing lists
        """

        if not self.is_logged_in():
            redirect(self.settings.login_url)

        messages = self.messages
        settings = self.settings
        utable = settings.table_user

        passfield = settings.password_field
        utable[passfield].writable = False

        request = current.request
        session = current.session
        deployment_settings = current.deployment_settings

        # Users should not be able to change their Org affiliation
        # - also hide popup-link to create a new Org (makes
        #   no sense here if the field is read-only anyway)
        utable.organisation_id.writable = False
        utable.organisation_id.comment = None

        ## Only allowed to select Orgs that the user has update access to
        #utable.organisation_id.requires = \
        #    current.s3db.org_organisation_requires(updateable = True)

        if next == DEFAULT:
            next = request.get_vars._next \
                or request.post_vars._next \
                or settings.profile_next
        if onvalidation == DEFAULT:
            onvalidation = settings.profile_onvalidation
        if onaccept == DEFAULT:
            onaccept = settings.profile_onaccept
        if log == DEFAULT:
            log = messages.profile_log
        labels = s3_mark_required(utable)[0]

        # If we have an opt_in and some post_vars then update the opt_in value
        # @ToDo: Replace with an AuthConsent-integrated solution
        opt_in_to_email = deployment_settings.get_auth_opt_in_to_email()
        if opt_in_to_email:
            team_list = deployment_settings.get_auth_opt_in_team_list()
            if request.post_vars:
                removed = []
                selected = []
                for opt_in in team_list:
                    if opt_in in request.post_vars:
                        selected.append(opt_in)
                    else:
                        removed.append(opt_in)
                db = current.db
                s3db = current.s3db
                ptable = s3db.pr_person
                putable = s3db.pr_person_user
                query = (putable.user_id == request.post_vars.id) & \
                        (putable.pe_id == ptable.pe_id)
                person_id = db(query).select(ptable.id, limitby=(0, 1)).first().id
                db(ptable.id == person_id).update(opt_in = selected)

                g_table = s3db["pr_group"]
                gm_table = s3db["pr_group_membership"]
                # Remove them from any team they are a member of in the removed list
                for team in removed:
                    query = (g_table.name == team) & \
                            (gm_table.group_id == g_table.id) & \
                            (gm_table.person_id == person_id)
                    gm_rec = db(query).select(g_table.id, limitby=(0, 1)).first()
                    if gm_rec:
                        db(gm_table.id == gm_rec.id).delete()
                # Add them to the team (if they are not already a team member)
                for team in selected:
                    query = (g_table.name == team) & \
                            (gm_table.group_id == g_table.id) & \
                            (gm_table.person_id == person_id)
                    gm_rec = db(query).select(g_table.id, limitby=(0, 1)).first()
                    if not gm_rec:
                        query = (g_table.name == team)
                        team_rec = db(query).select(g_table.id,
                                                    limitby=(0, 1)).first()
                        # if the team doesn't exist then add it
                        if team_rec == None:
                            team_id = g_table.insert(name=team, group_type=5)
                        else:
                            team_id = team_rec.id
                        gm_table.insert(group_id = team_id,
                                        person_id = person_id)

        formstyle = deployment_settings.get_ui_formstyle()
        current.response.form_label_separator = ""
        form = SQLFORM(utable,
                       self.user.id,
                       fields = settings.profile_fields,
                       labels = labels,
                       hidden = dict(_next=next),
                       showid = settings.showid,
                       submit_button = messages.profile_save_button,
                       delete_label = messages.delete_label,
                       upload = settings.download_url,
                       formstyle = formstyle,
                       separator = ""
                       )

        form.add_class("auth_profile")

        if deployment_settings.get_auth_openid():
            from gluon.contrib.login_methods.openid_auth import OpenIDAuth
            openid_login_form = OpenIDAuth(self)
            form = DIV(form, openid_login_form.list_user_openids())
        if form.accepts(request, session,
                        formname="profile",
                        onvalidation=onvalidation,
                        hideerror=settings.hideerror):
            #self.s3_auth_user_register_onaccept(form.vars.email, self.user.id)
            self.user.update(utable._filter_fields(form.vars))
            session.flash = messages.profile_updated
            if log:
                self.log_event(log, self.user)
            callback(onaccept, form)
            if not next:
                next = self.url(args=request.args)
            elif isinstance(next, (list, tuple)): ### fix issue with 2.6
                next = next[0]
            elif next and not next[0] == "/" and next[:4] != "http":
                next = self.url(next.replace("[id]", str(form.vars.id)))
            redirect(next)

        if opt_in_to_email:
            T = current.T
            ptable = s3db.pr_person
            ltable = s3db.pr_person_user
            team_list = deployment_settings.get_auth_opt_in_team_list()
            query = (ltable.user_id == form.record.id) & \
                    (ltable.pe_id == ptable.pe_id)
            db_opt_in_list = db(query).select(ptable.opt_in,
                                              limitby=(0, 1)).first().opt_in
            for opt_in in team_list:
                field_id = "%s_opt_in_%s" % (utable, team_list)
                if opt_in in db_opt_in_list:
                    checked = "selected"
                else:
                    checked = None
                s3_addrow(form,
                          LABEL(T("Receive %(opt_in)s updates:") % \
                                                        dict(opt_in=opt_in),
                                _for="opt_in",
                                _id=field_id + SQLFORM.ID_LABEL_SUFFIX),
                          INPUT(_name=opt_in, _id=field_id,
                                           _type="checkbox", _checked=checked),
                          "",
                          formstyle,
                          field_id + SQLFORM.ID_ROW_SUFFIX,
                          )
        return form

    # -------------------------------------------------------------------------
    def configure_user_fields(self, pe_ids=None):
        """
            Configure User Fields - for registration & user administration

            pe_ids: an optional list of pe_ids for the Org Filter
                    i.e. org_admin coming from admin.py/user()
        """

        from .s3validators import IS_ONE_OF

        T = current.T
        db = current.db
        s3db = current.s3db
        request = current.request
        messages = self.messages
        cmessages = current.messages
        settings = self.settings
        deployment_settings = current.deployment_settings

        if deployment_settings.get_ui_multiselect_widget():
            from .s3widgets import S3MultiSelectWidget
            multiselect_widget = True
        else:
            multiselect_widget = False

        utable = self.settings.table_user

        utable.password.label = T("Password") #messages.label_password

        first_name = utable.first_name
        first_name.label = T("First Name") #messages.label_first_name
        first_name.requires = IS_NOT_EMPTY(error_message=messages.is_empty)

        last_name = utable.last_name
        last_name.label = T("Last Name") #messages.label_last_name
        if deployment_settings.get_L10n_mandatory_lastname():
            last_name.notnull = True
            last_name.requires = IS_NOT_EMPTY(error_message=messages.is_empty)

        userfield = settings.login_userfield
        if userfield != "email":
            utable[userfield].requires = \
                IS_NOT_IN_DB(db, "%s.%s" % (utable._tablename,
                                            userfield))

        email = utable.email
        email.label = T("Email") #messages.label_email
        email.requires = [IS_EMAIL(error_message=messages.invalid_email),
                          IS_LOWER(),
                          IS_NOT_IN_DB(db,
                                       "%s.email" % utable._tablename,
                                       error_message=messages.duplicate_email)
                          ]

        language = utable.language
        languages = deployment_settings.get_L10n_languages()
        if len(languages) > 1:
            language.label = T("Language")
            language.comment = DIV(_class="tooltip",
                                   _title="%s|%s" % (T("Language"),
                                                     T("The language you wish the site to be displayed in.")))
            requires = IS_ISO639_2_LANGUAGE_CODE(sort = True,
                                                 translate = True,
                                                 zero = None,
                                                 )
            language.represent = requires.represent
            language.requires = requires
            # Default the profile language to the one currently active
            language.default = T.accepted_language
            if multiselect_widget:
                language.widget = S3MultiSelectWidget(multiple=False)
        else:
            language.default = list(languages.keys())[0]
            language.readable = language.writable = False

        utable.registration_key.label = messages.label_registration_key
        #utable.reset_password_key.label = messages.label_registration_key

        # Organisation
        is_admin = self.s3_has_role("ADMIN")
        if is_admin:
            show_org = deployment_settings.get_auth_admin_sees_organisation()
        else:
            show_org = deployment_settings.get_auth_registration_requests_organisation()

        if show_org:
            if pe_ids and not is_admin:
                # Filter orgs to just those belonging to the Org Admin's Org
                # & Descendants (or realms for which they are Org Admin):
                filterby = "pe_id"
                filter_opts = pe_ids
                # If the current user can only register users for certain orgs,
                # then they must not leave this field empty:
                org_required = True
            else:
                filterby = None
                filter_opts = None
                org_required = deployment_settings.get_auth_registration_organisation_required()

            organisation_id = utable.organisation_id
            organisation_id.label = messages.label_organisation_id
            organisation_id.readable = organisation_id.writable = True
            organisation_id.default = deployment_settings.get_auth_registration_organisation_default()
            org_represent = s3db.org_organisation_represent
            organisation_id.represent = org_represent

            requires = IS_ONE_OF(db, "org_organisation.id",
                                 org_represent,
                                 filterby = filterby,
                                 filter_opts = filter_opts,
                                 orderby = "org_organisation.name",
                                 sort = True,
                                 )

            if org_required:
                organisation_id.requires = requires
            else:
                organisation_id.requires = IS_EMPTY_OR(requires)

            if deployment_settings.get_auth_registration_organisation_link_create():
                from s3layouts import S3PopupLink
                org_crud_strings = s3db.crud_strings["org_organisation"]
                organisation_id.comment = S3PopupLink(c = "org",
                                                      f = "organisation",
                                                      label = org_crud_strings.label_create,
                                                      title = org_crud_strings.title_list,
                                                      )
                #from .s3widgets import S3OrganisationAutocompleteWidget
                #organisation_id.widget = S3OrganisationAutocompleteWidget()
                #organisation_id.comment = DIV(_class="tooltip",
                #                              _title="%s|%s" % (T("Organization"),
                #                                                cmessages.AUTOCOMPLETE_HELP))
            if multiselect_widget:
                organisation_id.widget = S3MultiSelectWidget(multiple=False)

        # Organisation Group
        if deployment_settings.get_auth_registration_requests_organisation_group():
            org_group_id = utable.org_group_id
            org_group_id.label = messages.label_org_group_id
            org_group_id.readable = org_group_id.writable = True
            org_group_represent = s3db.org_group_represent
            org_group_id.represent = org_group_represent
            requires = IS_ONE_OF(db, "org_group.id",
                                 org_group_represent,
                                 # @ToDo: Filter org groups to just those belonging to the Org Admin's Org
                                 # @ToDo: Dynamically filter groups to just those that the selected Org is a member of
                                 #filterby=filterby,
                                 #filter_opts=filter_opts,
                                 orderby="org_group.name",
                                 sort=True)
            if deployment_settings.get_auth_registration_organisation_group_required():
                org_group_id.requires = requires
            else:
                org_group_id.requires = IS_EMPTY_OR(requires)
            #from s3layouts import S3PopupLink
            #ogroup_crud_strings = s3db.crud_strings["org_group"]
            #org_group_id.comment = S3PopupLink(c = "org",
            #                                   f = "group",
            #                                   label = ogroup_crud_strings.label_create,
            #                                   title = ogroup_crud_strings.title_list,
            #                                   )
            if multiselect_widget:
                org_group_id.widget = S3MultiSelectWidget(multiple=False)

        # Site
        if deployment_settings.get_auth_registration_requests_site():
            site_id = request.get_vars.get("site_id", None)
            field = utable.site_id
            field.label = deployment_settings.get_org_site_label()
            site_represent = s3db.org_site_represent
            field.represent = site_represent
            if site_id:
                field.default = site_id
                field.readable = True
            else:
                field.readable = field.writable = True
                #field.default = deployment_settings.get_auth_registration_site_id_default()
                site_required = deployment_settings.get_auth_registration_site_required()
                if show_org:
                    from .s3validators import IS_ONE_OF_EMPTY
                    requires = IS_ONE_OF_EMPTY(db, "org_site.site_id",
                                               site_represent,
                                               orderby="org_site.name",
                                               sort=True)
                    if site_required:
                        site_optional = ""
                    else:
                        site_optional = ''',
 'optional': true'''
                    current.response.s3.jquery_ready.append('''
$.filterOptionsS3({
 'trigger':'organisation_id',
 'target':'site_id',
 'lookupField':'site_id',
 'lookupResource':'site',
 'lookupURL':S3.Ap.concat('/org/sites_for_org.json/')%s
})''' % site_optional)
                else:
                    requires = IS_ONE_OF(db, "org_site.site_id",
                                         site_represent,
                                         orderby="org_site.name",
                                         sort=True)
                #from .s3widgets import S3SiteAutocompleteWidget
                #field.widget = S3SiteAutocompleteWidget()
                field.comment = DIV(_class="tooltip",
                                    _title="%s|%s" % (T("Facility"),
                                                      T("Select the default site.")))
                if site_required:
                    field.requires = requires
                else:
                    field.requires = IS_EMPTY_OR(requires)

        # Link User to Organisation (as staff, volunteer, or member)
        if any(m in request.args for m in ("profile", "user_profile")):
            # Irrelevant in personal profile
            link_user_to_opts = False
        else:
            link_user_to_opts = deployment_settings.get_auth_registration_link_user_to()

        if link_user_to_opts:
            link_user_to = utable.link_user_to
            link_user_to_default = deployment_settings.get_auth_registration_link_user_to_default()
            req_vars = request.vars
            for hrtype in ["staff", "volunteer", "member"]:
                if "link_user_to_%s" % hrtype in req_vars:
                    link_user_to_default.append(hrtype)
            if link_user_to_default:
                link_user_to.default = link_user_to_default
            else:
                link_user_to.readable = link_user_to.writable = True
                link_user_to.label = T("Register As")
                link_user_to.requires = IS_IN_SET(link_user_to_opts,
                                                  multiple = True
                                                  )
                link_user_to.represent = lambda ids: \
                    ids and ", ".join([str(link_user_to_opts[id]) for id in ids]) or cmessages["NONE"]
                #if multiselect_widget:
                #    link_user_to.widget = S3MultiSelectWidget()
                #else:
                link_user_to.widget = SQLFORM.widgets.checkboxes.widget
                link_user_to.comment = DIV(_class="tooltip",
                                           _title="%s|%s" % (link_user_to.label,
                                                             T("Will create and link your user account to the following records")))

    # -------------------------------------------------------------------------
    def s3_import_prep(self, data):
        """
            Called when users are imported from CSV

            Lookups Pseudo-reference Integer fields from Names
            e.g.:
            auth_membership.pe_id from org_organisation.name=<Org Name>
        """

        db = current.db
        s3db = current.s3db
        set_record_owner = self.s3_set_record_owner
        update_super = s3db.update_super
        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        tree = data[1]

        ORG_ADMIN = not self.s3_has_role("ADMIN")
        TRANSLATE = current.deployment_settings.get_L10n_translate_org_organisation()
        if TRANSLATE:
            ltable = s3db.org_organisation_name

        def add_org(name, parent=None):
            """ Helper to add a New Organisation """
            organisation_id = otable.insert(name = name)
            record = Storage(id = organisation_id)
            update_super(otable, record)
            set_record_owner(otable, organisation_id)
            # @ToDo: Call onaccept?
            if parent:
                records = db(otable.name == parent).select(otable.id)
                if len(records) == 1:
                    # Add branch link
                    link_id = btable.insert(organisation_id = records.first().id,
                                            branch_id = organisation_id)
                    onaccept = s3db.get_config("org_organisation_branch", "onaccept")
                    callback(onaccept, Storage(vars = Storage(id = link_id)))
                elif len(records) > 1:
                    # Ambiguous
                    current.log.debug("Cannot set branch link for new Organisation %s as there are multiple matches for parent %s" % (name, parent))
                else:
                    # Create Parent
                    parent_id = otable.insert(name = parent)
                    update_super(otable, Storage(id = parent_id))
                    set_record_owner(otable, parent_id)
                    # @ToDo: Call onaccept?
                    # Create link
                    link_id = btable.insert(organisation_id = parent_id,
                                            branch_id = organisation_id)
                    onaccept = s3db.get_config("org_organisation_branch", "onaccept")
                    callback(onaccept, Storage(vars = Storage(id = link_id)))
            return (organisation_id, record.pe_id)

        def org_lookup(org_full):
            """ Helper to lookup an Organisation """
            if "+BRANCH+" in org_full:
                parent, org = org_full.split("+BRANCH+")
            else:
                parent = None
                org = org_full

            query = (otable.name.lower() == org.lower()) & \
                    (otable.deleted != True)
            if parent:
                btable = s3db.org_organisation_branch
                ptable = db.org_organisation.with_alias("org_parent_organisation")
                query &= (ptable.name == parent) & \
                         (btable.organisation_id == ptable.id) & \
                         (btable.branch_id == otable.id)

            records = db(query).select(otable.id,
                                       otable.pe_id,
                                       limitby = (0, 2))
            if len(records) == 1:
                record = records.first()
                organisation_id = record.id
                pe_id = record.pe_id
            elif len(records) > 1:
                # Ambiguous
                current.log.debug("Cannot set Organisation %s for user as there are multiple matches" % org)
                organisation_id = ""
                pe_id = ""
            elif TRANSLATE:
                # Search by local name
                query = (ltable.name_l10n.lower() == org.lower()) & \
                        (ltable.organisation_id == otable.id) & \
                        (ltable.deleted != True)
                records = db(query).select(otable.id,
                                           otable.pe_id,
                                           limitby = (0, 2))
                if len(records) == 1:
                    record = records.first()
                    organisation_id = record.id
                    pe_id = record.pe_id
                elif len(records) > 1:
                    # Ambiguous
                    current.log.debug("Cannot set Organisation %s for user as there are multiple matches" % org)
                    organisation_id = ""
                    pe_id = ""
                elif ORG_ADMIN:
                    # NB ORG_ADMIN has the list of permitted pe_ids already in filter_opts
                    current.log.debug("Cannot create new Organisation %s as ORG_ADMIN cannot create new Orgs during User Imports" % org)
                    organisation_id = ""
                    pe_id = ""
                else:
                    # Add a new record
                    (organisation_id, pe_id) = add_org(org, parent)

            elif ORG_ADMIN:
                # NB ORG_ADMIN has the list of permitted pe_ids already in filter_opts
                current.log.debug("Cannot create new Organisation %s as ORG_ADMIN cannot create new Orgs during User Imports" % org)
                organisation_id = ""
                pe_id = ""
            else:
                # Add a new record
                (organisation_id, pe_id) = add_org(org, parent)

            return (organisation_id, pe_id)

        def person_lookup(details):
            """ Helper to lookup a Person """
            first_name, last_name, email = details.split("+")

            # Rare edge case to set realm as individuals so not defining in top-scope
            ctable = s3db.pr_contact
            ptable = s3db.pr_person
            query = (ptable.first_name.lower() == first_name.lower()) & \
                    (ptable.last_name.lower() == last_name.lower()) & \
                    (ptable.deleted != True) & \
                    (ctable.pe_id == ptable.pe_id) & \
                    (ctable.contact_method == "EMAIL") & \
                    (ctable.value == email)

            records = db(query).select(ptable.id,
                                       ptable.pe_id,
                                       limitby = (0, 2))
            if len(records) == 1:
                record = records.first()
                person_id = record.id
                pe_id = record.pe_id
            elif len(records) > 1:
                # Ambiguous
                current.log.debug("Cannot set Person %s for user as there are multiple matches" % details)
                person_id = ""
                pe_id = ""
            else:
                # Add a new Person
                person_id = ptable.insert(first_name = first_name,
                                          last_name = last_name,
                                          )
                record = Storage(id = person_id)
                update_super(ptable, record)
                pe_id = record.pe_id
                # Persons need Email defining otherwise they won't match in s3_link_to_person
                ctable.insert(pe_id = pe_id,
                              contact_method = "EMAIL",
                              value = email,
                              )

            return (person_id, pe_id)

        # Memberships
        elements = tree.getroot().xpath("/s3xml//resource[@name='auth_membership']/data[@field='pe_id']")
        looked_up = {"org_organisation": {}} # Most common, so added outside loop
        for element in elements:
            pe_string = element.text

            if pe_string and "=" in pe_string:
                pe_type, pe_value =  pe_string.split("=")
                pe_tablename, pe_field =  pe_type.split(".")
                if pe_tablename in looked_up and \
                   pe_value in looked_up[pe_tablename]:
                    # Replace string with pe_id
                    element.text = looked_up[pe_tablename][pe_value]["pe_id"]
                    # Don't check again
                    continue

                if pe_tablename == "org_organisation" and pe_field == "name":
                    # This is a non-integer, so must be 1st or only phase
                    (record_id, pe_id) = org_lookup(pe_value)
                elif pe_tablename == "pr_person" and pe_field == "details":
                    # This is a non-integer, so must be 1st or only phase
                    if pe_tablename not in looked_up:
                        looked_up[pe_tablename] = {}
                    # Persons need Email defining otherwise they won't match in s3_link_to_person
                    (record_id, pe_id) = person_lookup(pe_value)
                else:
                    table = s3db[pe_tablename]
                    if pe_tablename not in looked_up:
                        looked_up[pe_tablename] = {}
                    record = db(table[pe_field] == pe_value).select(table.id, # Stored for Org/Groups later
                                                                    table.pe_id,
                                                                    limitby = (0, 1)
                                                                    ).first()
                    if record:
                        record_id = record.id
                    else:
                        # Add a new record
                        record_id = table.insert(**{pe_field: pe_value})
                        record = Storage(id = record_id)
                        update_super(table, record)
                        set_record_owner(table, record_id)
                    pe_id = record.pe_id

                new_value = str(pe_id)
                # Replace string with pe_id
                element.text = new_value
                # Store in case we get called again with same value
                looked_up[pe_tablename][pe_value] = {"pe_id": new_value,
                                                     "id": str(record_id),
                                                     }

        # No longer required since we can use references in the import CSV
        # Organisations
        #elements = tree.getroot().xpath("/s3xml//resource[@name='auth_user']/data[@field='organisation_id']")
        #if elements:
        #    orgs = looked_up["org_organisation"]
        #    for element in elements:
        #        org_full = element.text
        #        if org_full in orgs:
        #            # Replace string with id
        #            element.text = orgs[org_full]["id"]
        #            # Don't check again
        #            continue
        #        try:
        #            # Is this the 2nd phase of a 2-phase import & hence values have already been replaced?
        #            int(org_full)
        #        except ValueError:
        #            # This is a non-integer, so must be 1st or only phase
        #            (organisation_id, pe_id) = org_lookup(org_full)

        #            # Replace string with id
        #            organisation_id = str(organisation_id)
        #            element.text = organisation_id
        #            # Store in case we get called again with same value
        #            orgs[org_full] = {"id": organisation_id}
        #        else:
        #            # Store in case we get called again with same value
        #            orgs[org_full] = {"id": org_full}

        # Organisation Groups
        #elements = tree.getroot().xpath("/s3xml//resource[@name='auth_user']/data[@field='org_group_id']")
        #if elements:
        #    gtable = s3db.org_group
        #    org_groups = looked_up.get("org_organisation_group", {})
        #    for element in elements:
        #        name = element.text
        #        if name in org_groups:
        #            # Replace string with id
        #            element.text = org_groups[name]["id"]
        #            # Don't check again
        #            continue

        #        try:
        #            # Is this the 2nd phase of a 2-phase import & hence values have already been replaced?
        #            int(name)
        #        except ValueError:
        #            # This is a non-integer, so must be 1st or only phase
        #            record = db(gtable.name == name).select(gtable.id,
        #                                                    limitby = (0, 1)
        #                                                    ).first()
        #            if record:
        #                org_group_id = record.id
        #            else:
        #                # Add a new record
        #                org_group_id = gtable.insert(name = name)
        #                update_super(gtable, Storage(id = org_group_id))
        #            # Replace string with id
        #            org_group_id = str(org_group_id)
        #            element.text = org_group_id
        #            # Store in case we get called again with same value
        #            org_groups[name] = {"id": org_group_id}
        #        else:
        #            # Store in case we get called again with same value
        #            org_groups[name] = {"id": name}

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_register_validation():
        """
            JavaScript client-side validation for Registration / User profile
            - needed to check for passwords being same, etc
        """

        T = current.T
        request = current.request
        appname = request.application
        settings = current.deployment_settings
        s3 = current.response.s3

        # Static Scripts
        scripts_append = s3.scripts.append
        if s3.debug:
            scripts_append("/%s/static/scripts/jquery.validate.js" % appname)
            scripts_append("/%s/static/scripts/jquery.pstrength.2.1.0.js" % appname)
            scripts_append("/%s/static/scripts/S3/s3.register_validation.js" % appname)
        else:
            scripts_append("/%s/static/scripts/jquery.validate.min.js" % appname)
            scripts_append("/%s/static/scripts/jquery.pstrength.2.1.0.min.js" % appname)
            scripts_append("/%s/static/scripts/S3/s3.register_validation.min.js" % appname)

        # Configuration
        js_global = []
        js_append = js_global.append

        if settings.get_auth_registration_mobile_phone_mandatory():
            js_append('''S3.auth_registration_mobile_phone_mandatory=1''')

        if settings.get_auth_registration_organisation_required():
            js_append('''S3.auth_registration_organisation_required=1''')
            js_append('''i18n.enter_your_organisation="%s"''' % T("Enter your organization"))

        if settings.get_auth_terms_of_service():
            js_append('''S3.auth_terms_of_service=1''')
            js_append('''i18n.tos_required="%s"''' % T("You must agree to the Terms of Service"))

        if request.controller != "admin":
            if settings.get_auth_registration_organisation_hidden():
                js_append('''S3.auth_registration_hide_organisation=1''')

            # Check for Whitelists
            table = current.s3db.auth_organisation
            query = (table.organisation_id != None) & \
                    (table.domain != None)
            whitelists = current.db(query).select(table.organisation_id,
                                                  table.domain)
            if whitelists:
                domains = []
                domains_append = domains.append
                for whitelist in whitelists:
                    domains_append("'%s':%s" % (whitelist.domain,
                                                whitelist.organisation_id))
                domains = ''','''.join(domains)
                domains = '''S3.whitelists={%s}''' % domains
                js_append(domains)

        js_append('''i18n.enter_first_name="%s"''' % T("Enter your first name"))
        js_append('''i18n.provide_password="%s"''' % T("Provide a password"))
        js_append('''i18n.repeat_your_password="%s"''' % T("Repeat your password"))
        js_append('''i18n.enter_same_password="%s"''' % T("Enter the same password as above"))
        js_append('''i18n.please_enter_valid_email="%s"''' % T("Please enter a valid email address"))

        js_append('''S3.password_min_length=%i''' % settings.get_auth_password_min_length())
        js_append('''i18n.password_min_chars="%s"''' % T("You must enter a minimum of %d characters"))
        js_append('''i18n.weak="%s"''' % T("Weak"))
        js_append('''i18n.normal="%s"''' % T("Normal"))
        js_append('''i18n.medium="%s"''' % T("Medium"))
        js_append('''i18n.strong="%s"''' % T("Strong"))
        js_append('''i18n.very_strong="%s"''' % T("Very Strong"))

        script = '''\n'''.join(js_global)
        s3.js_global.append(script)

        # Call script after Global config done
        s3.jquery_ready.append('''s3_register_validation()''')

    # -------------------------------------------------------------------------
    def s3_auth_user_register_onaccept(self, email, user_id):
        """
            S3 framework function

            Allows customisation of the process for creating/updating users
            - called by s3_approve_user when new users are created or approved
            - (was called by 'profile' method for updates, but no longer)
        """

        # Check for any custom functionality
        onaccept = current.s3db.get_config("auth_user", "register_onaccept")
        if callable(onaccept):
            onaccept(user_id)

        # Default functionality

        # Handle any OpenFire Chat Server integration
        if self.settings.login_userfield != "username":
            deployment_settings = current.deployment_settings
            chat_server = deployment_settings.get_chat_server()
            if chat_server:
                chat_username = email.replace("@", "_")
                db = current.db
                db(db.auth_user.id == user_id).update(username = chat_username)
                chatdb = DAL(deployment_settings.get_chatdb_string(), migrate=False)
                # Using RawSQL as table not created in web2py
                sql_query="insert into ofGroupUser values (\'%s\',\'%s\' ,0);" % (chat_server["groupname"], chat_username)
                chatdb.executesql(sql_query)

    # -------------------------------------------------------------------------
    def s3_register_onaccept(self, form):
        """
            S3 framework function

            Designed to be called when a user is created through:
                - registration via OAuth, LDAP, etc

            Does the following:
                - Sets session.auth.user for authorstamp, etc
                - Approves user (to set registration groups, such as AUTHENTICATED, link to Person)
        """

        user = form.vars
        current.session.auth = Storage(user=user)
        self.s3_approve_user(user)

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_user_register_onaccept(form):
        """
            S3 framework function

            Designed to be called when a user is created through:
                - registration

            Does the following:
                - Stores the user's email & profile image in auth_user_temp
                  to be added to their person record when created on approval

            @ToDo: If these fields are implemented with the InlineForms functionality,
            this function may become redundant
        """
        temptable = current.s3db.auth_user_temp

        form_vars = form.vars
        user_id = form_vars.id

        if not user_id:
            return

        record  = {"user_id": user_id}

        # Store the home_phone ready to go to pr_contact
        home = form_vars.home
        if home:
            record["home"] = home

        # Store the mobile_phone ready to go to pr_contact
        mobile = form_vars.mobile
        if mobile:
            record["mobile"] = mobile

        # Store Consent Question Response
        consent = form_vars.consent
        if consent:
            record["consent"] = consent

        # Store the profile picture ready to go to pr_image
        image = form_vars.image
        if image != None and  hasattr(image, "file"):
            # @ToDo: DEBUG!!!
            source_file = image.file
            original_filename = image.filename

            field = temptable.image
            newfilename = field.store(source_file,
                                      original_filename,
                                      field.uploadfolder)
            if isinstance(field.uploadfield, str):
                form_vars[field.uploadfield] = source_file.read()
            record["image"] = newfilename

        if len(record) > 1:
            temptable.update_or_insert(**record)

    # -------------------------------------------------------------------------
    def s3_verify_user(self, user):
        """"
            Designed to be called when a user is verified through:
                - responding to their verification email
                - if verification isn't required

            Does the following:
                - Sends a message to the approver to notify them if a user needs approval
                - If deployment_settings.auth.always_notify_approver = True,
                    send them notification regardless
                - If approval isn't required - calls s3_approve_user

            @returns boolean - if the user has been approved
        """

        db = current.db
        deployment_settings = current.deployment_settings
        session = current.session
        auth_messages = self.messages
        utable = self.settings.table_user

        user_id = user.id

        # Lookup the Approver
        approver, organisation_id = self.s3_approver(user)

        if deployment_settings.get_auth_registration_requires_approval() and approver:
            approved = False
            db(utable.id == user_id).update(registration_key = "pending")

            if user.registration_key:
                # User has just been verified
                session.information = deployment_settings.get_auth_registration_pending_approval()
            else:
                # No Verification needed
                session.information = deployment_settings.get_auth_registration_pending()
            message = "approve_user"

        else:
            approved = True
            if organisation_id and not user.get("organisation_id", None):
                # Use the whitelist
                user["organisation_id"] = organisation_id
                db(utable.id == user_id).update(organisation_id = organisation_id)
                link_user_to = deployment_settings.get_auth_registration_link_user_to_default()
                if link_user_to and not user.get("link_user_to", None):
                    user["link_user_to"] = link_user_to
                self.s3_link_user(user)
            self.s3_approve_user(user)
            session.confirmation = auth_messages.email_verified
            session.flash = auth_messages.registration_successful

            if not deployment_settings.get_auth_always_notify_approver():
                return approved

            message = "new_user"

        # Ensure that we send out the mails in the language that the approver(s) want
        if "@" in approver:
            # Look up language of the user
            record = db(utable.email == approver).select(utable.language,
                                                         limitby=(0, 1)
                                                         ).first()
            if record:
                language = record.language
            else:
                language = deployment_settings.get_L10n_default_language()
            approvers = [{"email": approver,
                          "language": language,
                          }]
            languages = [language]
        else:
            approvers = []
            aappend = approvers.append
            languages = []
            for each_approver in approver:
                language = each_approver["language"]
                if language not in languages:
                    languages.append(language)
                aappend(each_approver)

        T = current.T
        subjects = {}
        messages = {}
        first_name = user.first_name
        last_name = user.last_name
        email = user.email
        base_url = current.response.s3.base_url
        system_name = deployment_settings.get_system_name()
        for language in languages:
            T.force(language)
            if message == "approve_user":
                subjects[language] = \
                    s3_str(T("%(system_name)s - New User Registration Approval Pending") % \
                            {"system_name": system_name})
                messages[language] = s3_str(auth_messages.approve_user % \
                            {"system_name": system_name,
                             "first_name": first_name,
                             "last_name": last_name,
                             "email": email,
                             "url": "%(base_url)s/admin/user/%(id)s" % \
                                    {"base_url": base_url,
                                     "id": user_id,
                                     },
                             })
            elif message == "new_user":
                subjects[language] = \
                    s3_str(T("%(system_name)s - New User Registered") % \
                            {"system_name": system_name})
                messages[language] = \
                    s3_str(auth_messages.new_user % {"system_name": system_name,
                                                     "first_name": first_name,
                                                     "last_name": last_name,
                                                     "email": email
                                                     })

        # Restore language for UI
        T.force(session.s3.language)

        mailer = self.settings.mailer
        if mailer.settings.server:
            for approver in approvers:
                language = approver["language"]
                result = mailer.send(to = approver["email"],
                                     subject = subjects[language],
                                     message = messages[language])
        else:
            # Email system not configured (yet)
            result = None
        if not result:
            # Don't prevent registration just because email not configured
            #db.rollback()
            current.response.error = auth_messages.email_send_failed
            return False

        return approved

    # -------------------------------------------------------------------------
    def s3_approve_user(self, user, password=None):
        """
            S3 framework function

            Designed to be called when a user is created through:
                - prepop
                - approved automatically during registration
                - approved by admin
                - added by admin
                - updated by admin

            Does the following:
                - Adds user to the 'Authenticated' role
                - Adds any default roles for the user
                - @ToDo: adds them to the Org_x Access role

            @param user: the user Storage() or Row
            @param password: optional password to include in a custom welcome_email
        """

        user_id = user.id
        if not user_id:
            return

        db = current.db
        s3db = current.s3db
        deployment_settings = current.deployment_settings
        settings = self.settings

        utable = settings.table_user

        # Add to 'Authenticated' role
        authenticated = self.id_group("Authenticated")
        add_membership = self.add_membership
        add_membership(authenticated, user_id)

        organisation_id = user.organisation_id

        # Add User to required registration roles
        entity_roles = deployment_settings.get_auth_registration_roles()
        link_user_to = user.link_user_to or utable.link_user_to.default or []
        if entity_roles:
            gtable = settings.table_group
            get_pe_id = s3db.pr_get_pe_id
            for entity, roles in entity_roles.items():

                if entity is None and \
                   not organisation_id or "staff" not in link_user_to:
                    # No default realm => do not assign default realm roles
                    continue

                # Get User's Organisation or Site pe_id
                if entity in ("organisation_id", "org_group_id", "site_id"):
                    tablename = "org_%s" % entity.split("_")[0]
                    entity = get_pe_id(tablename, user[entity])
                    if not entity:
                        continue

                rows = db(gtable.uuid.belongs(roles)).select(gtable.id)
                for role in rows:
                    add_membership(role.id, user_id, entity=entity)

        if organisation_id and \
           deployment_settings.get_auth_org_admin_to_first():
            # If this is the 1st user to register for an Org, give them ORG_ADMIN for that Org
            entity = s3db.pr_get_pe_id("org_organisation", organisation_id)
            gtable = settings.table_group
            ORG_ADMIN = db(gtable.uuid == "ORG_ADMIN").select(gtable.id,
                                                              limitby=(0, 1)
                                                              ).first().id
            mtable = settings.table_membership
            query = (mtable.group_id == ORG_ADMIN) & \
                    (mtable.pe_id == entity)
            exists = db(query).select(mtable.id,
                                      limitby=(0, 1))
            if not exists:
                add_membership(ORG_ADMIN, user_id, entity=entity)

        if deployment_settings.has_module("delphi"):
            # Add user as a participant of the default problem group
            table = s3db.delphi_group
            group = db(table.uuid == "DEFAULT").select(table.id,
                                                       limitby=(0, 1)).first()
            if group:
                table = s3db.delphi_membership
                table.insert(group_id = group.id,
                             user_id = user_id,
                             status = 3,
                             )

        self.s3_link_user(user)

        # Track consent
        if deployment_settings.get_auth_consent_tracking():
            s3db.auth_Consent.register_consent(user_id)

        user_email = db(utable.id == user_id).select(utable.email,
                                                     ).first().email
        self.s3_auth_user_register_onaccept(user_email, user_id)

        if current.response.s3.bulk is True:
            # Non-interactive imports should stop here
            return

        # Allow them to login
        db(utable.id == user_id).update(registration_key = "")

        # Approve User's Organisation
        if organisation_id and \
           "org_organisation" in \
           deployment_settings.get_auth_record_approval_required_for():
            org_resource = s3db.resource("org_organisation",
                                         organisation_id,
                                         # Do not re-approve (would
                                         # overwrite original approver)
                                         approved = False,
                                         unapproved = True,
                                         )
            approved = org_resource.approve()
            if not approved:
                # User is verifying their email and is not yet
                # logged-in, so approve by system authority
                org_resource.approve(approved_by = 0)

        # Send Welcome mail
        self.s3_send_welcome_email(user, password)

    # -------------------------------------------------------------------------
    def s3_link_user(self, user):
        """
            S3 framework function

            Designed to be called when a user is created & approved through:
                - prepop
                - approved automatically during registration
                - approved by admin
                - added by admin
                - updated by admin

            Does the following:
                - Calls s3_link_to_organisation:
                  Creates (if not existing) User's Organisation and links User
                - Calls s3_link_to_person:
                  Creates (if not existing) User's Person Record and links User
                - Calls s3_link_to_human_resource:
                  Creates (if not existing) User's Human Resource Record and links User
                - Calls s3_link_to_member
        """

        # Create/Update/Link to organisation,
        organisation_id = self.s3_link_to_organisation(user)

        # Add to user Person Registry and Email/Mobile to pr_contact
        person_id = self.s3_link_to_person(user, organisation_id)

        if user.org_group_id:
            self.s3_link_to_org_group(user, person_id)

        utable = self.settings.table_user

        link_user_to = user.link_user_to or utable.link_user_to.default

        if link_user_to:
            if "staff" in link_user_to:
                # Add Staff Record
                self.s3_link_to_human_resource(user, person_id, hr_type=1)
            if "volunteer" in link_user_to:
                # Add Volunteer Record
                self.s3_link_to_human_resource(user, person_id, hr_type=2)
            if "member" in link_user_to:
                # Add Member Record
                self.s3_link_to_member(user, person_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_user_profile_onaccept(form):
        """ Update the UI locale from user profile """

        if form.vars.language:
            current.session.s3.language = form.vars.language

    # -------------------------------------------------------------------------
    def s3_link_to_person(self,
                          user = None,
                          organisation_id = None
                          ):
        """
            Links user accounts to person registry entries

            @param user: the user record
            @param organisation_id: the user's organisation_id
                                    to get the person's realm_entity

            Policy for linking to pre-existing person records:

            If this user is already linked to a person record with a different
            first_name, last_name, email or realm_entity these will be
            updated to those of the user.

            If a person record with exactly the same first name and
            last name exists, which has a contact information record
            with exactly the same email address as used in the user
            account, and is not linked to another user account, then
            this person record will be linked to this user account.

            Otherwise, a new person record is created, and a new email
            contact record with the email address from the user record
            is registered for that person.
        """

        db = current.db
        s3db = current.s3db

        utable = self.settings.table_user

        ttable = s3db.auth_user_temp
        ptable = s3db.pr_person
        ctable = s3db.pr_contact
        ltable = s3db.pr_person_user

        # Organisation becomes the realm entity of the person record
        # (unless deployment settings specify something else)
        if organisation_id:
            org_pe_id = s3db.pr_get_pe_id("org_organisation",
                                          organisation_id)
        else:
            org_pe_id = None

        left = [ltable.on(ltable.user_id == utable.id),
                ptable.on(ptable.pe_id == ltable.pe_id),
                ttable.on(utable.id == ttable.user_id),
                ]

        if user is not None:
            if not isinstance(user, (list, tuple)):
                user = [user]
            user_ids = [u.id for u in user]
            query = (utable.id.belongs(user_ids))
        else:
            query = (utable.id != None)

        fields = [utable.id,
                  utable.first_name,
                  utable.last_name,
                  utable.email,
                  ltable.pe_id,
                  ptable.id,
                  ptable.first_name,
                  ttable.home,
                  ttable.mobile,
                  ttable.image,
                  ]
        middle_name = current.deployment_settings.get_L10n_mandatory_middlename()
        if middle_name:
            # e.g. Hispanic names' Apellido Paterno
            fields.append(ptable.middle_name)
        else:
            fields.append(ptable.last_name)

        rows = db(query).select(*fields,
                                left=left, distinct=True)

        person_ids = [] # Collect the person IDs

        if current.request.vars.get("opt_in", None):
            opt_in = current.deployment_settings.get_auth_opt_in_team_list()
        else:
            opt_in = []

        for row in rows:

            # The user record
            user = row.auth_user

            # The temporary user record
            tuser = row.auth_user_temp

            # The person record
            person = row.pr_person

            # The link table record
            link = row.pr_person_user

            pe_id = link.pe_id
            if pe_id is not None:
                # There is an existing person record linked to this user account
                # => update it

                # Update the person names if changed
                if user.first_name != person.first_name or \
                   (not middle_name and user.last_name != person.last_name) or \
                   (middle_name and user.last_name != person.middle_name):
                    query = (ptable.pe_id == pe_id)
                    if middle_name:
                        db(query).update(first_name = user.first_name,
                                         middle_name = user.last_name,
                                         )
                    else:
                        db(query).update(first_name = user.first_name,
                                         last_name = user.last_name,
                                         )

                # Add the user's email address to the person record if missing
                query = (ctable.pe_id == pe_id) & \
                        (ctable.contact_method == "EMAIL") & \
                        (ctable.value == user.email)
                item = db(query).select(ctable.id,
                                        limitby=(0, 1)).first()
                if item is None:
                    ctable.insert(pe_id = pe_id,
                                  contact_method = "EMAIL",
                                  value = user.email,
                                  )

                # Add the user's mobile_phone to the person record if missing
                if tuser.mobile:
                    query = (ctable.pe_id == pe_id) & \
                            (ctable.contact_method == "SMS") & \
                            (ctable.value == tuser.mobile)
                    item = db(query).select(ctable.id,
                                            limitby=(0, 1)).first()
                    if item is None:
                        ctable.insert(pe_id = pe_id,
                                      contact_method = "SMS",
                                      value = tuser.mobile,
                                      )

                #@ToDo: Also update home phone? profile image? Groups?

                person_ids.append(person.id)

            else:
                # This user account isn't yet linked to a person record
                # => try to find a person record with same first name,
                # other name and email address

                first_name = user.first_name
                last_name = user.last_name
                email = user.email.lower()
                if email:
                    if middle_name:
                        mquery = (ptable.middle_name == last_name)
                    else:
                        mquery = (ptable.last_name == last_name)
                    query = (ptable.first_name == first_name) & \
                             mquery & \
                            (ctable.pe_id == ptable.pe_id) & \
                            (ctable.contact_method == "EMAIL") & \
                            (ctable.value.lower() == email)
                    person = db(query).select(ptable.id,
                                              ptable.pe_id,
                                              limitby = (0, 1)
                                              ).first()
                else:
                    # Can't find a match without an email address
                    person = None

                # Users own their person records
                owner = Storage(owned_by_user = user.id)

                if person:
                    other = db(ltable.pe_id == person.pe_id).select(ltable.id,
                                                                    limitby=(0, 1),
                                                                    ).first()

                if person and not other:
                    # Match found, and it isn't linked to another user account
                    # => link to this person record (+update it)
                    pe_id = person.pe_id
                    person_id = person.id

                    # Get the realm entity
                    realm_entity = self.get_realm_entity(ptable, person)
                    if not realm_entity:
                        # Default to organisation
                        realm_entity = org_pe_id
                    owner.realm_entity = realm_entity

                    # Insert a link
                    ltable.insert(user_id = user.id,
                                  pe_id = pe_id,
                                  )

                    # Assign ownership of the Person record
                    person.update_record(**owner)

                    # Assign ownership of the Contact record(s)
                    db(ctable.pe_id == pe_id).update(**owner)

                    # Assign ownership of the Address record(s)
                    atable = s3db.pr_address
                    db(atable.pe_id == pe_id).update(**owner)

                    # Assign ownership of the Details record
                    dtable = s3db.pr_person_details
                    db(dtable.person_id == person_id).update(**owner)

                    # Assign ownership of the GIS Config record(s)
                    gctable = s3db.gis_config
                    db(gctable.pe_id == pe_id).update(**owner)

                    # Set pe_id if this is the current user
                    if self.user and self.user.id == user.id:
                        self.user.pe_id = pe_id

                    person_ids.append(person_id)

                else:
                    # There is no match or it is linked to another user account
                    # => create a new person record (+link to it)

                    # Create a new person record
                    if middle_name:
                        person_id = ptable.insert(first_name = first_name,
                                                  middle_name = last_name,
                                                  opt_in = opt_in,
                                                  modified_by = user.id,
                                                  **owner)
                    else:
                        person_id = ptable.insert(first_name = first_name,
                                                  last_name = last_name,
                                                  opt_in = opt_in,
                                                  modified_by = user.id,
                                                  **owner)
                    if person_id:

                        # Update the super-entities
                        person = Storage(id = person_id)
                        s3db.update_super(ptable, person)
                        pe_id = person.pe_id

                        # Get the realm entity
                        realm_entity = self.get_realm_entity(ptable, person)
                        if not realm_entity:
                            # Default to organisation
                            realm_entity = org_pe_id
                        self.set_realm_entity(ptable, person,
                                              entity=realm_entity,
                                              )
                        owner.realm_entity = realm_entity

                        # Insert a link
                        ltable.insert(user_id=user.id, pe_id=pe_id)

                        # Add the email to pr_contact
                        ctable.insert(pe_id = pe_id,
                                      contact_method = "EMAIL",
                                      priority = 1,
                                      value = email,
                                      **owner)

                        # Add the user to each team if they have chosen to opt-in
                        gtable = s3db.pr_group
                        mtable = s3db.pr_group_membership

                        for team in opt_in:
                            team_rec = db(gtable.name == team).select(gtable.id,
                                                                      limitby=(0, 1)
                                                                      ).first()
                            # if the team doesn't exist then add it
                            if team_rec == None:
                                team_id = gtable.insert(name = team,
                                                        group_type = 5)
                            else:
                                team_id = team_rec.id
                            mtable.insert(group_id = team_id,
                                          person_id = person_id,
                                          )

                        person_ids.append(person_id)

                    else:
                        pe_id = None

                if pe_id is not None:
                    # Insert data from the temporary user data record
                    tuser = row.auth_user_temp

                    # Add the mobile phone number from the temporary
                    # user data into pr_contact
                    mobile = tuser.mobile
                    if mobile:
                        ctable.insert(pe_id = pe_id,
                                      contact_method = "SMS",
                                      priority = 2,
                                      value = mobile,
                                      **owner)

                    # Add the home phone number from the temporary
                    # user data into pr_contact
                    home = tuser.home
                    if home:
                        ctable.insert(pe_id = pe_id,
                                      contact_method = "HOME_PHONE",
                                      priority = 3,
                                      value = home,
                                      **owner)

                    # Insert the profile picture from the temporary
                    # user data into pr_image
                    image = tuser.image
                    if image: # and hasattr(image, "file"):
                        itable = s3db.pr_image
                        url = URL(c="default", f="download", args=image)
                        itable.insert(pe_id = pe_id,
                                      profile = True,
                                      image = image,
                                      url = url,
                                      description = current.T("Profile Picture"),
                                      )

                    # Set pe_id if this is the current user
                    if self.user and self.user.id == user.id:
                        self.user.pe_id = pe_id

        if len(person_ids) == 1:
            return person_ids[0]
        else:
            return person_ids

    # -------------------------------------------------------------------------
    def s3_link_to_organisation(self, user):
        """
            Link a user account to an organisation

            @param user: the user account record
        """

        db = current.db
        s3db = current.s3db

        user_id = user.id

        # Lookup the organisation_id for the domain of this email address
        organisation_id = self.s3_approver(user)[1]
        if organisation_id:
            user.organisation_id = organisation_id
        else:
            # Use what the user has specified
            organisation_id = user.organisation_id
            # @ToDo: Is it correct to override the organisation entered by the user?
            #        Ideally (if the deployment_settings.auth.registration_requests_organisation = True)
            #        the org could be selected based on the email and the user could then override

        if not organisation_id:
            # Create a new Organisation
            name = user.get("organisation_name", None)
            if name:
                # Create new organisation
                acronym = user.get("organisation_acronym", None)
                otable = s3db.org_organisation
                record = Storage(name=name,
                                 acronym=acronym)
                organisation_id = otable.insert(**record)

                # Callbacks
                if organisation_id:
                    record["id"] = organisation_id
                    s3db.update_super(otable, record)
                    s3db.onaccept(otable, record, method="create")
                    self.s3_set_record_owner(otable, organisation_id)

                # Update user record
                user.organisation_id = organisation_id
                utable = self.settings.table_user
                db(utable.id == user_id).update(organisation_id = organisation_id)

        if not organisation_id:
            return None

        # Update link to Organisation
        ltable = s3db.org_organisation_user

        # Update if the User's Organisation has changed
        query = (ltable.user_id == user_id)
        rows = db(query).select(ltable.organisation_id,
                                limitby = (0, 2))
        if len(rows) == 1:
            # We know which record to update - this should always be 1
            if rows.first().organisation_id != organisation_id:
                db(query).update(organisation_id=organisation_id)
            # No more action required
            return organisation_id
        else:
            # Create link (if it doesn't exist)
            query = (ltable.user_id == user_id) & \
                    (ltable.organisation_id == organisation_id)
            row = db(query).select(ltable.id, limitby=(0, 1)).first()
            if not row:
                ltable.insert(user_id = user_id,
                              organisation_id = organisation_id)

        return organisation_id

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_link_to_org_group(user, person_id):
        """
            Link a user account to an organisation group

            @param user: the user account record
            @param person_id: the person record ID associated with this user
        """

        db = current.db
        s3db = current.s3db

        org_group_id = user.get("org_group_id")
        if not org_group_id or not person_id:
            return None

        # Default status to "Member"
        stable = s3db.org_group_person_status
        query = (stable.name.lower() == "member") & \
                (stable.deleted != True)
        row = db(query).select(stable.id, limitby=(0, 1)).first()
        if row:
            status_id = row.id
        else:
            status_id = None

        # Check if link exists
        ltable = s3db.org_group_person
        query = (ltable.person_id == person_id) & \
                (ltable.org_group_id == org_group_id) & \
                (ltable.deleted != True)
        row = db(query).select(ltable.id, limitby=(0, 1)).first()
        if not row:
            # Make sure person record and org_group record exist
            ptable = s3db.pr_person
            gtable = s3db.org_group
            if ptable[person_id] and gtable[org_group_id]:
                ltable.insert(person_id = person_id,
                              org_group_id = org_group_id,
                              status_id = status_id,
                              )
        return org_group_id

    # -------------------------------------------------------------------------
    def s3_link_to_human_resource(self,
                                  user,
                                  person_id,
                                  hr_type,
                                  ):
        """
            Take ownership of the HR records of the person record
            @ToDo: Add user to the Org Access role.
        """

        db = current.db
        s3db = current.s3db
        settings = current.deployment_settings

        user_id = user.id
        organisation_id = user.organisation_id

        htablename = "hrm_human_resource"
        htable = s3db.table(htablename)

        if not htable or (not organisation_id and \
                          settings.get_hrm_org_required()):
            # Module disabled or no user organisation set
            return None

        def customise(hr_id):
            """ Customise hrm_human_resource """
            customise = settings.customise_resource(htablename)
            if customise:
                request = S3Request("hrm", "human_resource",
                                    current.request,
                                    args = [str(hr_id)] if hr_id else [],
                                    )
                customise(request, htablename)

        # Determine the site ID
        site_id = user.site_id if hr_type == 1 else None

        # Get existing active HR record for this user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (ltable.user_id == user_id) & \
                (ptable.pe_id == ltable.pe_id) & \
                (htable.person_id == ptable.id) & \
                (htable.type == hr_type) & \
                (htable.status == 1) & \
                (htable.deleted == False)
        rows = db(query).select(htable.id, limitby=(0, 2))

        accepted = None
        if len(rows) == 1:
            # Single active HR record of this type
            # => update organisation and site
            record = rows.first()
            hr_id = record.id

            # Update the record
            customise(hr_id)
            db(htable.id == hr_id).update(organisation_id = organisation_id,
                                          site_id = site_id,
                                          )
            accepted = "update"

            # Update or create site link
            hstable = s3db.hrm_human_resource_site
            query = (hstable.human_resource_id == hr_id)
            hstable.update_or_insert(query,
                                     site_id = site_id,
                                     human_resource_id = hr_id,
                                     owned_by_user = user_id,
                                     )
        else:
            # Multiple or no HR records of this type

            if rows:
                # Multiple records
                # => check if there is one for this organisation and site
                if type(person_id) is list:
                    person_id = person_id[0]
                query = (htable.person_id == person_id) & \
                        (htable.organisation_id == organisation_id) & \
                        (htable.type == hr_type) & \
                        (htable.site_id == site_id) & \
                        (htable.deleted == False)
                row = db(query).select(htable.id, limitby=(0, 1)).first()
            else:
                # No HR record exists at all
                row = None

            if row:
                # At least one record for this organisation and site exists
                # => pass
                hr_id = row.id

            else:
                # Create new HR record
                customise(hr_id = None)
                record = Storage(person_id = person_id,
                                 organisation_id = organisation_id,
                                 site_id = site_id,
                                 type = hr_type,
                                 owned_by_user = user_id,
                                 )
                hr_id = htable.insert(**record)
                record["id"] = hr_id
                accepted = "create"

        if hr_id and accepted:

            # Update any super-records
            s3db.update_super(htable, record)

            # Set or update the record owner and realm entity
            # (enforce update to change realm if organisation changed)
            self.s3_set_record_owner(htable, hr_id, force_update=True)

            # Run onaccept
            s3db.onaccept(htablename, record, method=accepted)

        return hr_id

    # -------------------------------------------------------------------------
    def s3_link_to_member(self,
                          user,
                          person_id = None
                          ):
        """
            Link to a member Record
        """

        db = current.db
        s3db = current.s3db

        user_id = user.id
        organisation_id = user.organisation_id

        mtablename = "member_membership"
        mtable = s3db.table(mtablename)

        if not mtable or not organisation_id:
            return None

        # Update existing Member record for this user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (mtable.deleted == False) & \
                (mtable.person_id == ptable.id) & \
                (ptable.pe_id == ltable.pe_id) & \
                (ltable.user_id == user_id)
        rows = db(query).select(mtable.id,
                                limitby=(0, 2))
        if len(rows) == 1:
            # Only update if there is a single member Record
            member_id = rows.first().id
            db(mtable.id == member_id).update(organisation_id = organisation_id)
            # Update record ownership
            self.s3_set_record_owner(mtable, member_id, force_update=True)

        # Create a Member record, if one doesn't already exist
        if isinstance(person_id, list):
            person_ids = person_id
        else:
            person_ids = [person_id]
        query = (mtable.person_id.belongs(person_ids)) & \
                (mtable.organisation_id == organisation_id)
        row = db(query).select(mtable.id, limitby=(0, 1)).first()

        if row:
            member_id = row.id
        else:
            record = Storage(person_id = person_ids[0],
                             organisation_id = organisation_id,
                             owned_by_user = user_id,
                             )
            member_id = mtable.insert(**record)
            if member_id:
                record["id"] = member_id
                # Customise the resource
                customise = current.deployment_settings.customise_resource(mtablename)
                if customise:
                    request = S3Request("member", "membership",
                                        current.request,
                                        args = [str(member_id)])
                    customise(request, mtablename)

                self.s3_set_record_owner(mtable, member_id)
                s3db.onaccept(mtablename, record, method="create")

        return member_id

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_approver(user):
        """
            Returns the Approver for a new Registration &
            the organisation_id field

            @param: user - the user record (form.vars when done direct)
            @ToDo: Support multiple approvers per Org - via Org Admin (or specific Role?)
                   Split into separate functions to returning approver & finding users' org from auth_organisations

            @returns approver, organisation_id - if approver = False, user is automatically approved by whitelist
        """

        db = current.db

        approver = None
        organisation_id = user.get("organisation_id")

        table = current.s3db.auth_organisation
        if organisation_id:
            # Check for an Organisation-specific Approver
            query = (table.organisation_id == organisation_id) & \
                    (table.deleted == False)
            record = db(query).select(table.approver,
                                      limitby=(0, 1)).first()
        elif "email" in user and user["email"] and "@" in user["email"]:
            # Check for Domain: Whitelist or specific Approver
            domain = user.email.split("@", 1)[-1]
            query = (table.domain == domain) & \
                    (table.deleted == False)
            record = db(query).select(table.organisation_id,
                                      table.approver,
                                      limitby=(0, 1)).first()
        else:
            record = None

        if record:
            if not organisation_id:
                organisation_id = record.organisation_id
            approver = record.approver

        if not approver:
            # Default Approver
            approver = current.deployment_settings.get_mail_approver()
            if "@" not in approver:
                # Must be the UUID of a Group
                utable = db.auth_user
                mtable = db.auth_membership
                gtable = db.auth_group
                query = (gtable.uuid == approver) & \
                        (gtable.id == mtable.group_id) & \
                        (mtable.user_id == utable.id)
                rows = db(query).select(utable.email,
                                        utable.language,
                                        distinct=True)
                approver = rows.as_list()

        return approver, organisation_id

    # -------------------------------------------------------------------------
    def s3_send_welcome_email(self, user, password=None):
        """
            Send a welcome mail to newly-registered users
            - especially suitable for users from Facebook/Google who don't
              verify their emails

            @param user: the user dict, must contain "email", and can
                         contain "language" for translation of the message
            @param password: optional password to include in a custom welcome_email
        """

        settings = current.deployment_settings
        if not settings.get_auth_registration_welcome_email():
            # Welcome-email disabled
            return

        messages = self.messages
        if not settings.get_mail_sender():
            current.response.error = messages.unable_send_email
            return

        # Ensure that we send out the mails in the language that
        # the recipient wants (if we know it)
        T = current.T
        language = user.get("language")
        if language:
            T.force(language)

        # Compose the message
        system_name = s3_str(settings.get_system_name())
        subject = s3_str(messages.welcome_email_subject % \
                        {"system_name": system_name})
        message = s3_str(messages.welcome_email % \
                        {"system_name": system_name,
                         "url": settings.get_base_public_url(),
                         "profile": URL("default", "person"),
                         "password": password,
                         })

        # Restore language for UI
        T.force(current.session.s3.language)

        recipient = user["email"]
        if settings.has_module("msg"):
            results = current.msg.send_email(recipient,
                                             subject = subject,
                                             message = message,
                                             )
        else:
            results = current.mail.send(recipient,
                                        subject = subject,
                                        message = message,
                                        )
        if not results:
            current.response.error = messages.unable_send_email

    # -------------------------------------------------------------------------
    # S3-specific authentication methods
    # -------------------------------------------------------------------------
    def s3_impersonate(self, user_id):
        """
            S3 framework function

            Designed to be used within tasks, which are run in a separate
            request & hence don't have access to current.auth

            @param user_id: auth.user.id or auth.user.email
        """

        settings = self.settings
        utable = settings.table_user
        query = None
        if not user_id:
            # Anonymous
            user = None
        elif isinstance(user_id, basestring) and not user_id.isdigit():
            query = (utable[settings.login_userfield] == user_id)
        else:
            query = (utable.id == user_id)

        if query is not None:
            user = current.db(query).select(limitby=(0, 1)).first()
            if not user:
                # Invalid user ID
                raise ValueError("User not found")
            else:
                user = Storage(utable._filter_fields(user, id=True))

        self.user = user
        session = current.session
        session.auth = Storage(user=user,
                               last_visit=current.request.now,
                               expiration=settings.expiration)
        self.s3_set_roles()

        if user:
            # Set the language from the Profile
            language = user.language
            current.T.force(language)
            session.s3.language = language

        return user

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_masterkey_login():
        """
            Master Key Authentication

            @returns: None if master key authentication is disabled or
                      wasn't attempted, otherwise True|False whether it
                      succeeded
        """

        success = None

        s3 = current.response.s3
        if s3.masterkey_auth_failed:
            # Already failed during this request cycle, no point trying again
            success = False
        else:
            from s3.s3masterkey import S3MasterKey
            access_key = S3MasterKey.get_access_key()
            if access_key is not None:
                success = S3MasterKey.authenticate(access_key)
                if not success:
                    s3.masterkey_auth_failed = True

        return success

    # -------------------------------------------------------------------------
    def s3_logged_in(self):
        """
            Check whether the user is currently logged-in
            - tries Basic if not
        """

        if self.override:
            return True

        if not self.is_logged_in():
            # NB MUST NOT send an HTTP-401 challenge here because otherwise,
            #    negative tests (e.g. if not auth.s3_logged_in()) would always
            #    challenge, and never succeed
            #    => omit basic_auth_realm
            #    => send the challenge in permission.fail() instead

            # Probe for Master Key Auth
            if current.deployment_settings.get_auth_masterkey():
                success = self.s3_masterkey_login()
                if success is not None:
                    return success

            # Basic Auth (default)
            basic = self.basic()
            try:
                return basic[2]
            except TypeError:
                # old web2py
                return basic
            except:
                return False

        return True

    # -------------------------------------------------------------------------
    # Role Management
    # -------------------------------------------------------------------------
    def get_system_roles(self):
        """
            Get the IDs of the session roles by their UIDs, and store them
            in the current session, as these IDs should never change.
        """

        s3 = current.session.s3
        try:
            system_roles = s3.system_roles
        except:
            s3 = Storage()
        else:
            if system_roles:
                return system_roles

        gtable = self.settings.table_group
        if gtable is not None:
            S3_SYSTEM_ROLES = self.S3_SYSTEM_ROLES
            query = (gtable.deleted != True) & \
                     gtable.uuid.belongs(set(S3_SYSTEM_ROLES.values()))
            rows = current.db(query).select(gtable.id, gtable.uuid)
            system_roles = Storage([(role.uuid, role.id) for role in rows])
        else:
            system_roles = Storage([(uid, None) for uid in S3_SYSTEM_ROLES])

        s3.system_roles = system_roles
        return system_roles

    # -------------------------------------------------------------------------
    def get_managed_orgs(self):
        """
            Get the pe_ids of all managed organisations (to authorize
            role assignments)

            TODO use this in admin/user controller
        """

        user = self.user
        if not user:
            return None

        has_role = self.s3_has_role
        sr = self.get_system_roles()

        if has_role(sr.ADMIN):
            return True

        elif has_role(sr.ORG_ADMIN):
            if not self.permission.entity_realm:
                organisation_id = user.organisation_id
                if not organisation_id:
                    return None
                s3db = current.s3db
                table = s3db.org_organisation
                pe_id = current.db(table.id == organisation_id).select(table.pe_id,
                                                                       limitby=(0, 1),
                                                                       cache = s3db.cache,
                                                                       ).first().pe_id
                pe_ids = s3db.pr_get_descendants(pe_id,
                                                 entity_types="org_organisation",
                                                 )
                pe_ids.append(pe_id)
            else:
                pe_ids = self.user.realms[sr.ORG_ADMIN]
                if pe_ids is None:
                    return True
            return pe_ids

        else:
            return None

    # -------------------------------------------------------------------------
    def s3_set_roles(self):
        """ Update pe_id, roles and realms for the current user """

        session = current.session

        s3 = current.response.s3
        if "restricted_tables" in s3:
            del s3["restricted_tables"]

        permission = self.permission
        permission.clear_cache()

        system_roles = self.get_system_roles()
        ANONYMOUS = system_roles.ANONYMOUS
        if ANONYMOUS:
            session.s3.roles = [ANONYMOUS]
        else:
            session.s3.roles = []

        if self.user:
            db = current.db
            s3db = current.s3db

            user_id = self.user.id

            # Set pe_id for current user
            ltable = s3db.table("pr_person_user")
            if ltable is not None:
                query = (ltable.user_id == user_id)
                row = db(query).select(ltable.pe_id,
                                       limitby=(0, 1),
                                       cache=s3db.cache).first()
                if row:
                    self.user["pe_id"] = row.pe_id
            else:
                self.user["pe_id"] = None

            # Get all current auth_memberships of the user
            mtable = self.settings.table_membership
            query = (mtable.deleted != True) & \
                    (mtable.user_id == user_id) & \
                    (mtable.group_id != None)
            rows = db(query).select(mtable.group_id, mtable.pe_id,
                                    cacheable=True)

            # Add all group_ids to session.s3.roles
            session.s3.roles.extend(row.group_id for row in rows)

            # Realms:
            # Permissions of a group apply only for records owned by any of
            # the entities which belong to the realm of the group membership

            if not permission.entity_realm:
                # Group memberships have no realms (policy 5 and below)
                self.user["realms"] = Storage([(row.group_id, None) for row in rows])
                self.user["delegations"] = Storage()

            else:
                # Group memberships are limited to realms (policy 6 and above)
                realms = {}
                delegations = {}

                # These roles can't be realm-restricted:
                unrestrictable = (system_roles.ADMIN,
                                  system_roles.ANONYMOUS,
                                  system_roles.AUTHENTICATED,
                                  )

                default_realm = s3db.pr_realm(self.user["pe_id"])

                # Store the realms:
                for row in rows:
                    group_id = row.group_id
                    if group_id in realms and realms[group_id] is None:
                        continue
                    if group_id in unrestrictable:
                        realms[group_id] = None
                        continue
                    if group_id not in realms:
                        realms[group_id] = []
                    realm = realms[group_id]
                    pe_id = row.pe_id
                    if pe_id is None:
                        if default_realm:
                            realm.extend([e for e in default_realm
                                            if e not in realm])
                        if not realm:
                            del realms[group_id]
                    elif pe_id == 0:
                        # Site-wide
                        realms[group_id] = None
                    elif pe_id not in realm:
                        realms[group_id].append(pe_id)

                if permission.entity_hierarchy:
                    # Realms include subsidiaries of the realm entities

                    # Get all entities in realms
                    all_entities = []
                    append = all_entities.append
                    for realm in realms.values():
                        if realm is not None:
                            for entity in realm:
                                if entity not in all_entities:
                                    append(entity)

                    # Lookup all delegations to any OU ancestor of the user
                    if permission.delegations and self.user.pe_id:

                        ancestors = s3db.pr_get_ancestors(self.user.pe_id)

                        dtable = s3db.pr_delegation
                        rtable = s3db.pr_role
                        atable = s3db.pr_affiliation

                        dn = dtable._tablename
                        rn = rtable._tablename
                        an = atable._tablename

                        query = (dtable.deleted != True) & \
                                (atable.role_id == dtable.role_id) & \
                                (atable.pe_id.belongs(ancestors)) & \
                                (rtable.id == dtable.role_id)
                        rows = db(query).select(rtable.pe_id,
                                                dtable.group_id,
                                                atable.pe_id,
                                                cacheable=True)

                        extensions = []
                        partners = []
                        for row in rows:
                            extensions.append(row[rn].pe_id)
                            partners.append(row[an].pe_id)
                    else:
                        rows = []
                        extensions = []
                        partners = []

                    # Lookup the subsidiaries of all realms and extensions
                    entities = all_entities + extensions + partners
                    descendants = s3db.pr_descendants(entities)

                    pmap = {}
                    for p in partners:
                        if p in all_entities:
                            pmap[p] = [p]
                        elif p in descendants:
                            d = descendants[p]
                            pmap[p] = [e for e in all_entities if e in d] or [p]

                    # Add the subsidiaries to the realms
                    for group_id in realms:
                        realm = realms[group_id]
                        if realm is None:
                            continue
                        append = realm.append
                        for entity in list(realm):
                            if entity in descendants:
                                for subsidiary in descendants[entity]:
                                    if subsidiary not in realm:
                                        append(subsidiary)

                    # Process the delegations
                    if permission.delegations:
                        for row in rows:

                            # owner == delegates group_id to ==> partner
                            owner = row[rn].pe_id
                            partner = row[an].pe_id
                            group_id = row[dn].group_id

                            if group_id in delegations and \
                               owner in delegations[group_id]:
                                # Duplicate
                                continue
                            if partner not in pmap:
                                continue

                            # Find the realm
                            if group_id not in delegations:
                                delegations[group_id] = Storage()
                            groups = delegations[group_id]

                            r = [owner]
                            if owner in descendants:
                                r.extend(descendants[owner])

                            for p in pmap[partner]:
                                if p not in groups:
                                    groups[p] = []
                                realm = groups[p]
                                realm.extend(r)

                self.user["realms"] = realms
                self.user["delegations"] = delegations

            if ANONYMOUS:
                # Anonymous role has no realm
                self.user["realms"][ANONYMOUS] = None

    # -------------------------------------------------------------------------
    def s3_create_role(self, role, description=None, *acls, **args):
        """
            Back-end method to create roles with ACLs

            @param role: display name for the role
            @param description: description of the role (optional)
            @param acls: list of initial ACLs to assign to this role
            @param args: keyword arguments (see below)
            @keyword name: a unique name for the role
            @keyword hidden: hide this role completely from the RoleManager
            @keyword system: role can be assigned, but neither modified nor
                             deleted in the RoleManager
            @keyword protected: role can be assigned and edited, but not
                                deleted in the RoleManager
        """

        table = self.settings.table_group

        hidden = args.get("hidden")
        system = args.get("system")
        protected = args.get("protected")

        if isinstance(description, dict):
            acls = [description] + acls
            description = None

        uid = args.get("uid", None)
        if uid:
            record = current.db(table.uuid == uid).select(table.id,
                                                          limitby=(0, 1)
                                                          ).first()
        else:
            record = None
            uid = uuid4()

        system_data = {}
        if hidden is not None:
            system_data["hidden"] = hidden
        if protected is not None:
            system_data["protected"] = protected
        if system is not None:
            system_data["system"] = system

        if record:
            role_id = record.id
            record.update_record(deleted = False,
                                 role = role,
                                 description = description,
                                 **system_data)
        else:
            role_id = table.insert(uuid = uid,
                                   role = role,
                                   description = description,
                                   **system_data)
        if role_id:
            update_acl = self.permission.update_acl
            for acl in acls:
                update_acl(role_id, **acl)

        return role_id

    # -------------------------------------------------------------------------
    def s3_delete_role(self, role_id):
        """
            Remove a role from the system.

            @param role_id: the ID or UID of the role

            @note: protected roles cannot be deleted with this function,
                   need to reset the protected-flag first to override
        """

        db = current.db
        table = self.settings.table_group

        if isinstance(role_id, str) and not role_id.isdigit():
            query = (table.uuid == role_id)
        else:
            role_id = int(role_id)
            query = (table.id == role_id)

        role = db(query).select(table.id,
                                table.uuid,
                                table.protected,
                                limitby=(0, 1),
                                ).first()

        if role and not role.protected:

            group_id = role.id
            data = {"deleted": True,
                    "group_id": None,
                    "deleted_fk": '{"group_id": %s}' % group_id,
                    }

            # Remove all memberships for this role
            mtable = self.settings.table_membership
            db(mtable.group_id == group_id).update(**data)

            # Remove all permission rules for this role
            ptable = self.permission.table
            db(ptable.group_id == group_id).update(**data)

            # Remove the role
            deleted_uuid = "%s-deleted-%s" % (uuid4().hex[-12:], role.uuid[:40])
            role.update_record(uuid = deleted_uuid,
                               role = None,
                               deleted = True,
                               )

    # -------------------------------------------------------------------------
    def s3_assign_role(self, user_id, group_id, for_pe=None):
        """
            Assigns a role to a user (add the user to a user group)

            @param user_id: the record ID of the user account
            @param group_id: the record ID(s)/UID(s) of the group
            @param for_pe: the person entity (pe_id) to restrict the group
                           membership to, possible values:

                           - None: use default realm (entities the user is
                             affiliated with)
                           - 0: site-wide realm (no entity-restriction)
                           - X: restrict to records owned by entity X

            @note: strings are assumed to be group UIDs
            @note: for_pe will be ignored for ADMIN, ANONYMOUS and AUTHENTICATED
        """

        db = current.db
        gtable = self.settings.table_group
        mtable = self.settings.table_membership

        # Find the group IDs
        query = None
        uuids = None
        if isinstance(group_id, (list, tuple)):
            if isinstance(group_id[0], str):
                uuids = group_id
                query = (gtable.uuid.belongs(group_id))
            else:
                group_ids = group_id
        elif isinstance(group_id, str) and not group_id.isdigit():
            uuids = [group_id]
            query = (gtable.uuid == group_id)
        else:
            group_ids = [group_id]
        if query is not None:
            query = (gtable.deleted != True) & query
            groups = db(query).select(gtable.id, gtable.uuid)
            group_ids = [g.id for g in groups]
            missing = [uuid for uuid in uuids
                       if uuid not in [g.uuid for g in groups]]
            for m in missing:
                group_id = self.s3_create_role(m, uid=m)
                if group_id:
                    group_ids.append(group_id)

        # Find the assigned groups
        query = (mtable.deleted != True) & \
                (mtable.user_id == user_id) & \
                (mtable.group_id.belongs(group_ids) & \
                (mtable.pe_id == for_pe))
        assigned = db(query).select(mtable.group_id)
        assigned_groups = [g.group_id for g in assigned]

        # Add missing memberships
        sr = self.get_system_roles()
        unrestrictable = [str(sr.ADMIN),
                          str(sr.ANONYMOUS),
                          str(sr.AUTHENTICATED)]
        for group_id in group_ids:
            if group_id not in assigned_groups:
                membership = {"user_id": user_id,
                              "group_id": group_id}
                if for_pe is not None and str(group_id) not in unrestrictable:
                    membership["pe_id"] = for_pe
                #membership_id = mtable.insert(**membership)
                mtable.insert(**membership)

        # Update roles for current user if required
        if self.user and str(user_id) == str(self.user.id):
            self.s3_set_roles()

    # -------------------------------------------------------------------------
    def s3_withdraw_role(self, user_id, group_id, for_pe=None):
        """
            Removes a role assignment from a user account

            @param user_id: the record ID of the user account
            @param group_id: the record ID(s)/UID(s) of the role
            @param for_pe: only remove the group membership for this
                           realm, possible values:

                           - None: only remove for the default realm
                           - 0: only remove for the site-wide realm
                           - X: only remove for entity X
                           - []: remove for any realms

            @note: strings are assumed to be role UIDs
        """

        if not group_id:
            return

        db = current.db
        gtable = self.settings.table_group
        mtable = self.settings.table_membership

        # Find the group IDs
        query = None
        if isinstance(group_id, (list, tuple)):
            if isinstance(group_id[0], str):
                query = (gtable.uuid.belongs(group_id))
            else:
                group_ids = group_id
        elif isinstance(group_id, str):
            query = (gtable.uuid == group_id)
        else:
            group_ids = [group_id]
        if query is not None:
            query = (gtable.deleted != True) & query
            groups = db(query).select(gtable.id)
            group_ids = [g.id for g in groups]

        # Get the assigned groups
        query = (mtable.deleted != True) & \
                (mtable.user_id == user_id) & \
                (mtable.group_id.belongs(group_ids))

        sr = self.get_system_roles()
        unrestrictable = [str(sr.ADMIN),
                          str(sr.ANONYMOUS),
                          str(sr.AUTHENTICATED)]
        if for_pe != []:
            query &= ((mtable.pe_id == for_pe) | \
                      (mtable.group_id.belongs(unrestrictable)))
        memberships = db(query).select()

        # Archive the memberships
        for m in memberships:
            deleted_fk = {"user_id": m.user_id,
                          "group_id": m.group_id}
            if for_pe:
                deleted_fk["pe_id"] = for_pe
            deleted_fk = json.dumps(deleted_fk)
            m.update_record(deleted = True,
                            deleted_fk = deleted_fk,
                            user_id = None,
                            group_id = None)

        # Update roles for current user if required
        if self.user and str(user_id) == str(self.user.id):
            self.s3_set_roles()

    # -------------------------------------------------------------------------
    def s3_get_roles(self, user_id, for_pe=DEFAULT):
        """
            Lookup all roles which have been assigned to user for an entity

            @param user_id: the user_id
            @param for_pe: the entity (pe_id) or list of entities
        """

        if not user_id:
            return []

        mtable = self.settings.table_membership
        query = (mtable.deleted != True) & \
                (mtable.user_id == user_id)
        if isinstance(for_pe, (list, tuple)):
            if len(for_pe):
                query &= (mtable.pe_id.belongs(for_pe))
        elif for_pe is not DEFAULT:
            query &= (mtable.pe_id == for_pe)
        rows = current.db(query).select(mtable.group_id)
        return list({row.group_id for row in rows})

    # -------------------------------------------------------------------------
    def s3_has_role(self, role, for_pe=None, include_admin=True):
        """
            Check whether the currently logged-in user has a certain role
            (auth_group membership).

            @param role: the record ID or UID of the role
            @param for_pe: check for this particular realm, possible values:

                           - None: for any entity
                           - 0: site-wide
                           - X: for entity X

            @param include_admin: ADMIN matches all Roles
        """

        # Allow override
        if self.override:
            return True

        system_roles = self.get_system_roles()
        if role == system_roles.ANONYMOUS:
            # All users have the anonymous role
            return True

        s3 = current.session.s3

        # Trigger HTTP basic auth
        self.s3_logged_in()

        # Get the realms
        if not s3:
            return False
        realms = None
        if self.user:
            realms = self.user.realms
        elif s3.roles:
            realms = Storage([(r, None) for r in s3.roles])
        if not realms:
            return False

        # Administrators have all roles
        if include_admin and system_roles.ADMIN in realms:
            return True

        # Resolve role ID/UID
        if isinstance(role, str):
            if role.isdigit():
                role = int(role)
            elif role in system_roles:
                role = system_roles[role]
            else:
                gtable = self.settings.table_group
                query = (gtable.uuid == role) & \
                        (gtable.deleted != True)
                row = current.db(query).select(gtable.id,
                                               cache = (current.cache.ram, 600),
                                               limitby = (0, 1),
                                               ).first()
                if row:
                    role = row.id
                else:
                    return False

        # Check the realm
        if role in realms:
            realm = realms[role]
            if realm is None or for_pe is None or for_pe in realm:
                return True

        return False

    # -------------------------------------------------------------------------
    def s3_has_roles(self, roles, for_pe=None, all=False):
        """
            Check whether the currently logged-in user has at least one
            out of a set of roles (or all of them, with all=True)

            @param roles: list|tuple|set of role IDs or UIDs
            @param for_pe: check for this particular realm, possible values:
                               None - for any entity
                               0 - site-wide
                               X - for entity X
            @param all: check whether the user has all of the roles
        """

        # Override
        if self.override or not roles:
            return True

        # Get the realms
        session_s3 = current.session.s3
        if not session_s3:
            return False
        realms = None
        if self.user:
            realms = self.user.realms
        elif session_s3.roles:
            realms = Storage([(r, None) for r in session_s3.roles])
        if not realms:
            return False

        # Administrators have all roles (no need to check)
        system_roles = self.get_system_roles()
        if system_roles.ADMIN in realms:
            return True

        # Resolve any role UIDs
        if not isinstance(roles, (tuple, list, set)):
            roles = [roles]

        check = set()
        resolve = set()
        for role in roles:
            if isinstance(role, basestring):
                resolve.add(role)
            else:
                check.add(role)

        if resolve:
            gtable = self.settings.table_group
            query = (gtable.uuid.belongs(resolve)) & \
                    (gtable.deleted != True)
            rows = current.db(query).select(gtable.id,
                                            cache = (current.cache.ram, 600),
                                            )
            for row in rows:
                check.add(row.id)

        # Check each role
        for role in check:

            if role == system_roles.ANONYMOUS:
                # All users have the anonymous role
                has_role = True
            elif role in realms:
                realm = realms[role]
                has_role = realm is None or for_pe is None or for_pe in realm
            else:
                has_role = False

            if has_role:
                if not all:
                    return True
            elif all:
                return False

        return bool(all)

    # -------------------------------------------------------------------------
    def s3_group_members(self, group_id, for_pe=DEFAULT):
        """
            Get a list of members of a group

            @param group_id: the group record ID
            @param for_pe: show only group members for this PE

            @return: a list of the user_ids for members of a group
        """

        mtable = self.settings.table_membership

        query = (mtable.deleted != True) & \
                (mtable.group_id == group_id)
        if for_pe is None:
            query &= (mtable.pe_id == None)
        elif for_pe is not DEFAULT:
            query &= (mtable.pe_id == for_pe)
        members = current.db(query).select(mtable.user_id)
        return [m.user_id for m in members]

    # -------------------------------------------------------------------------
    def s3_delegate_role(self,
                         group_id,
                         entity,
                         receiver=None,
                         role=None,
                         role_type=None):
        """
            Delegate a role (auth_group) from one entity to another

            @param group_id: the role ID or UID (or a list of either)
            @param entity: the delegating entity
            @param receiver: the pe_id of the receiving entity (or a list of pe_ids)
            @param role: the affiliation role
            @param role_type: the role type for the affiliation role (default=9)

            @note: if role is None, a new role of role_type 0 will be created
                   for each entity in receiver and used for the delegation
                   (1:1 delegation)
            @note: if both receiver and role are specified, the delegation will
                   add all receivers to this role and create a 1:N delegation to
                   this role. If the role does not exist, it will be created (using
                   the given role type)
        """

        if not self.permission.delegations:
            return False

        db = current.db
        s3db = current.s3db
        dtable = s3db.table("pr_delegation")
        rtable = s3db.table("pr_role")
        atable = s3db.table("pr_affiliation")
        if dtable is None or \
           rtable is None or \
           atable is None:
            return False
        if not group_id or not entity or not receiver and not role:
            return False

        # Find the group IDs
        gtable = self.settings.table_group
        query = None
        uuids = None
        if isinstance(group_id, (list, tuple)):
            if isinstance(group_id[0], str):
                uuids = group_id
                query = (gtable.uuid.belongs(group_id))
            else:
                group_ids = group_id
        elif isinstance(group_id, str) and not group_id.isdigit():
            uuids = [group_id]
            query = (gtable.uuid == group_id)
        else:
            group_ids = [group_id]
        if query is not None:
            query = (gtable.deleted != True) & query
            groups = db(query).select(gtable.id, gtable.uuid)
            group_ids = [g.id for g in groups]
            missing = [u for u in uuids if u not in [g.uuid for g in groups]]
            for m in missing:
                group_id = self.s3_create_role(m, uid=m)
                if group_id:
                    group_ids.append(group_id)
        if not group_ids:
            return False

        if receiver is not None:
            if not isinstance(receiver, (list, tuple)):
                receiver = [receiver]
            query = (dtable.deleted != True) & \
                    (dtable.group_id.belongs(group_ids)) & \
                    (dtable.role_id == rtable.id) & \
                    (rtable.deleted != True) & \
                    (atable.role_id == rtable.id) & \
                    (atable.deleted != True) & \
                    (atable.pe_id.belongs(receiver))
            rows = db(query).select(atable.pe_id)
            assigned = [row.pe_id for row in rows]
            receivers = [r for r in receiver if r not in assigned]
        else:
            receivers = None

        if role_type is None:
            role_type = 9 # Other

        roles = []
        if role is None:
            if receivers is None:
                return False
            for pe_id in receivers:
                role_name = "__DELEGATION__%s__%s__" % (entity, pe_id)
                query = (rtable.role == role_name)
                role = db(query).select(limitby=(0, 1)).first()
                if role is not None:
                    if role.deleted:
                        role.update_record(deleted=False,
                                           role_type=0)
                    role_id = role.id
                else:
                    role_id = s3db.pr_add_affiliation(entity, pe_id,
                                                      role=role_name,
                                                      role_type=0)
                if role_id:
                    roles.append(role_id)
        else:
            query = (rtable.deleted != True) & \
                    (rtable.pe_id == entity) & \
                    (rtable.role == role)
            row = db(query).select(rtable.id, limitby=(0, 1)).first()
            if row is None:
                role_id = rtable.insert(pe_id = entity,
                                        role = role,
                                        role_type = role_type)
            else:
                role_id = row.id
            if role_id:
                if receivers is not None:
                    pr_rebuild_path = s3db.pr_rebuild_path
                    for pe_id in receivers:
                        atable.insert(role_id = role_id,
                                      pe_id = pe_id)
                        pr_rebuild_path(pe_id, clear=True)
                roles.append(role_id)

        for role_id in roles:
            for group_id in group_ids:
                dtable.insert(role_id=role_id, group_id=group_id)

        # Update roles for current user if required
        self.s3_set_roles()

        return True

    # -------------------------------------------------------------------------
    def s3_remove_delegation(self,
                             group_id,
                             entity,
                             receiver=None,
                             role=None):
        """
            Remove a delegation.

            @param group_id: the auth_group ID or UID (or a list of either)
            @param entity: the delegating entity
            @param receiver: the receiving entity
            @param role: the affiliation role

            @note: if receiver is specified, only 1:1 delegations (to role_type 0)
                   will be removed, but not 1:N delegations => to remove for 1:N
                   you must specify the role instead of the receiver
            @note: if both receiver and role are None, all delegations with this
                   group_id will be removed for the entity
        """

        if not self.permission.delegations:
            return False

        db = current.db
        s3db = current.s3db
        dtable = s3db.table("pr_delegation")
        rtable = s3db.table("pr_role")
        atable = s3db.table("pr_affiliation")
        if dtable is None or \
           rtable is None or \
           atable is None:
            return False
        if not group_id or not entity or not receiver and not role:
            return False

        # Find the group IDs
        gtable = self.settings.table_group
        query = None
        #uuids = None
        if isinstance(group_id, (list, tuple)):
            if isinstance(group_id[0], str):
                #uuids = group_id
                query = (gtable.uuid.belongs(group_id))
            else:
                group_ids = group_id
        elif isinstance(group_id, str) and not group_id.isdigit():
            #uuids = [group_id]
            query = (gtable.uuid == group_id)
        else:
            group_ids = [group_id]
        if query is not None:
            query = (gtable.deleted != True) & query
            groups = db(query).select(gtable.id, gtable.uuid)
            group_ids = [g.id for g in groups]
        if not group_ids:
            return False

        # Get all delegations
        query = (dtable.deleted != True) & \
                (dtable.group_id.belongs(group_ids)) & \
                (dtable.role_id == rtable.id) & \
                (rtable.pe_id == entity) & \
                (atable.role_id == rtable.id)
        if receiver:
            if not isinstance(receiver, (list, tuple)):
                receiver = [receiver]
            query &= (atable.pe_id.belongs(receiver))
        elif role:
            query &= (rtable.role == role)
        rows = db(query).select(dtable.id,
                                dtable.group_id,
                                rtable.id,
                                rtable.role_type)

        # Remove properly
        rmv = Storage()
        for row in rows:
            if not receiver or row[rtable.role_type] == 0:
                deleted_fk = {"role_id": row[rtable.id],
                              "group_id": row[dtable.group_id]}
                rmv[row[dtable.id]] = json.dumps(deleted_fk)
        for record_id in rmv:
            query = (dtable.id == record_id)
            data = {"role_id": None,
                    "group_id": None,
                    "deleted_fk": rmv[record_id]}
            db(query).update(**data)

        # Maybe update the current user's delegations?
        if len(rmv):
            self.s3_set_roles()
        return True

    # -------------------------------------------------------------------------
    def s3_get_delegations(self, entity, role_type=0, by_role=False):
        """
            Lookup delegations for an entity, ordered either by
            receiver (by_role=False) or by affiliation role (by_role=True)

            @param entity: the delegating entity (pe_id)
            @param role_type: limit the lookup to this affiliation role type,
                              (can use 0 to lookup 1:1 delegations)
            @param by_role: group by affiliation roles

            @return: a Storage {<receiver>: [group_ids]}, or
                      a Storage {<rolename>: {entities:[pe_ids], groups:[group_ids]}}
        """

        if not entity or not self.permission.delegations:
            return None
        s3db = current.s3db
        dtable = s3db.pr_delegation
        rtable = s3db.pr_role
        atable = s3db.pr_affiliation
        if None in (dtable, rtable, atable):
            return None

        query = (rtable.deleted != True) & \
                (dtable.deleted != True) & \
                (atable.deleted != True) & \
                (rtable.pe_id == entity) & \
                (dtable.role_id == rtable.id) & \
                (atable.role_id == rtable.id)
        if role_type is not None:
            query &= (rtable.role_type == role_type)
        rows = current.db(query).select(atable.pe_id,
                                        rtable.role,
                                        dtable.group_id)
        delegations = Storage()
        for row in rows:
            receiver = row[atable.pe_id]
            role = row[rtable.role]
            group_id = row[dtable.group_id]
            if by_role:
                if role not in delegations:
                    delegations[role] = Storage(entities=[], groups=[])
                delegation = delegations[role]
                if receiver not in delegation.entities:
                    delegation.entities.append(receiver)
                if group_id not in delegation.groups:
                    delegation.groups.append(group_id)
            else:
                if receiver not in delegations:
                    delegations[receiver] = [group_id]
                else:
                    delegations[receiver].append(group_id)
        return delegations

    # -------------------------------------------------------------------------
    # ACL management
    # -------------------------------------------------------------------------
    def s3_update_acls(self, role, *acls):
        """ Wrapper for permission.update_acl to allow batch updating """

        for acl in acls:
            self.permission.update_acl(role, **acl)

    # -------------------------------------------------------------------------
    # User Identity
    # -------------------------------------------------------------------------
    def s3_get_user_id(self, person_id=None, pe_id=None):
        """
            Get the user_id for a person_id

            @param person_id: the pr_person record ID, or a user email address
            @param pe_id: the person entity ID, alternatively
        """

        result = None

        if isinstance(person_id, basestring) and not person_id.isdigit():
            # User email address
            utable = self.settings.table_user
            query = (utable.email == person_id)
            user = current.db(query).select(utable.id,
                                            limitby=(0, 1),
                                            ).first()
            if user:
                result = user.id
        else:
            # Person/PE ID
            s3db = current.s3db
            ltable = s3db.pr_person_user
            if person_id:
                ptable = s3db.pr_person
                query = (ptable.id == person_id) & \
                        (ptable.pe_id == ltable.pe_id)
            else:
                query = (ltable.pe_id == pe_id)
            link = current.db(query).select(ltable.user_id,
                                            limitby=(0, 1),
                                            ).first()
            if link:
                result = link.user_id

        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_user_pe_id(user_id):
        """
            Get the person pe_id for a user ID

            @param user_id: the user ID
        """

        table = current.s3db.pr_person_user
        row = current.db(table.user_id == user_id).select(table.pe_id,
                                                          limitby=(0, 1),
                                                          ).first()
        return row.pe_id if row else None

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_bulk_user_pe_id(user_ids):
        """
            Get the list of person pe_id for list of user_ids

            @param user_id: list of user IDs
        """

        table = current.s3db.pr_person_user
        if not isinstance(user_ids, list):
            user_ids = [user_ids]
        rows = current.db(table.user_id.belongs(user_ids)).select(table.pe_id,
                                                                  table.user_id,
                                                                  )
        if rows:
            return {row.user_id: row.pe_id for row in rows}
        return None

    # -------------------------------------------------------------------------
    def s3_logged_in_person(self):
        """
            Get the person record ID for the current logged-in user
        """

        row = None

        if self.s3_logged_in():
            ptable = current.s3db.pr_person
            try:
                query = (ptable.pe_id == self.user.pe_id)
            except AttributeError:
                # Prepop (auth.override, self.user is None)
                pass
            else:
                row = current.db(query).select(ptable.id,
                                               limitby=(0, 1),
                                               ).first()

        return row.id if row else None

    # -------------------------------------------------------------------------
    def s3_logged_in_human_resource(self):
        """
            Get the first HR record ID for the current logged-in user
        """

        row = None

        if self.s3_logged_in():
            s3db = current.s3db
            ptable = s3db.pr_person
            htable = s3db.hrm_human_resource
            try:
                query = (htable.person_id == ptable.id) & \
                        (ptable.pe_id == self.user.pe_id)
            except AttributeError:
                # Prepop (auth.override, self.user is None)
                pass
            else:
                row = current.db(query).select(htable.id,
                                               orderby = ~htable.modified_on,
                                               limitby = (0, 1),
                                               ).first()

        return row.id if row else None

    # -------------------------------------------------------------------------
    # Core Authorization Methods
    # -------------------------------------------------------------------------
    def s3_has_permission(self, method, table, record_id=None, c=None, f=None):
        """
            S3 framework function to define whether a user can access a record
            in manner "method". Designed to be called from the RESTlike
            controller.

            @param method: the access method as string, one of
                           "create", "read", "update", "delete"
            @param table: the table or tablename
            @param record_id: the record ID (if any)
            @param c: the controller name (overrides current.request)
            @param f: the function name (overrides current.request)
        """

        if self.override:
            return True

        sr = self.get_system_roles()

        if not hasattr(table, "_tablename"):
            tablename = table
            table = current.s3db.table(tablename, db_only=True)
            if table is None:
                current.log.warning("Permission check on Table %s failed as couldn't load table. Module disabled?" % tablename)
                # Return a different Falsy value
                return None

        policy = current.deployment_settings.get_security_policy()

        # Simple policy
        if policy == 1:
            # Anonymous users can Read.
            if method == "read":
                authorised = True
            else:
                # Authentication required for Create/Update/Delete.
                authorised = self.s3_logged_in()

        # Editor policy
        elif policy == 2:
            # Anonymous users can Read.
            if method == "read":
                authorised = True
            elif method == "create":
                # Authentication required for Create.
                authorised = self.s3_logged_in()
            elif record_id == 0 and method == "update":
                # Authenticated users can update at least some records
                authorised = self.s3_logged_in()
            else:
                # Editor role required for Update/Delete.
                authorised = self.s3_has_role(sr.EDITOR)
                if not authorised and self.user and "owned_by_user" in table:
                    # Creator of Record is allowed to Edit
                    query = (table.id == record_id)
                    record = current.db(query).select(table.owned_by_user,
                                                      limitby=(0, 1)).first()
                    if record and self.user.id == record.owned_by_user:
                        authorised = True

        # Use S3Permission ACLs
        elif policy in (3, 4, 5, 6, 7, 8):
            authorised = self.permission.has_permission(method,
                                                        c = c,
                                                        f = f,
                                                        t = table,
                                                        record = record_id)

        # Web2py default policy
        else:
            if self.s3_logged_in():
                # Administrators are always authorised
                if self.s3_has_role(sr.ADMIN):
                    authorised = True
                else:
                    # Require records in auth_permission to specify access
                    # (default Web2Py-style)
                    authorised = self.has_permission(method, table, record_id)
            else:
                # No access for anonymous
                authorised = False

        return authorised

    # -------------------------------------------------------------------------
    def s3_accessible_query(self, method, table, c=None, f=None):
        """
            Returns a query with all accessible records for the currently
            logged-in user

            @param method: the access method as string, one of:
                           "create", "read", "update" or "delete"
            @param table: the table or table name
            @param c: the controller name (overrides current.request)
            @param f: the function name (overrides current.request)

            @note: This method does not work on GAE because it uses JOIN and IN
        """

        if self.override:
            return table.id > 0

        sr = self.get_system_roles()

        if not hasattr(table, "_tablename"):
            table = current.s3db[table]

        policy = current.deployment_settings.get_security_policy()

        if policy == 1:
            # "simple" security policy: show all records
            return table.id > 0
        elif policy == 2:
            # "editor" security policy: show all records
            return table.id > 0
        elif policy in (3, 4, 5, 6, 7, 8):
            # ACLs: use S3Permission method
            query = self.permission.accessible_query(method, table, c=c, f=f)
            return query

        # "Full" security policy
        if self.s3_has_role(sr.ADMIN):
            # Administrators can see all data
            return table.id > 0

        # If there is access to the entire table then show all records
        try:
            user_id = self.user.id
        except:
            user_id = 0
        if self.has_permission(method, table, 0, user_id):
            return table.id > 0

        # Filter Records to show only those to which the user has access
        current.session.warning = current.T("Only showing accessible records!")
        membership = self.settings.table_membership
        permission = self.settings.table_permission
        query = (membership.user_id == user_id) & \
                (membership.group_id == permission.group_id) & \
                (permission.name == method) & \
                (permission.table_name == table)
        return table.id.belongs(current.db(query)._select(permission.record_id))

    # -------------------------------------------------------------------------
    # S3 Variants of web2py Authorization Methods
    # -------------------------------------------------------------------------
    def s3_has_membership(self, group_id=None, user_id=None, role=None):
        """
            Checks if user is member of group_id or role

            Extends Web2Py's requires_membership() to add new functionality:
                - Custom Flash style
                - Uses s3_has_role()
        """

        # Allow override
        if self.override:
            return True

        group_id = group_id or self.id_group(role)
        try:
            group_id = int(group_id)
        except:
            group_id = self.id_group(group_id) # interpret group_id as a role

        has_role = self.s3_has_role(group_id)

        log = self.messages.has_membership_log
        if log:
            if not user_id and self.user:
                user_id = self.user.id
            self.log_event(log, {"user_id": user_id,
                                 "group_id": group_id,
                                 "check": has_role,
                                 })
        return has_role

    # Override original method
    has_membership = s3_has_membership

    # -------------------------------------------------------------------------
    def s3_requires_membership(self, role):
        """
            Decorator that prevents access to action if not logged in or
            if user logged in is not a member of group_id. If role is
            provided instead of group_id then the group_id is calculated.

            Extends Web2Py's requires_membership() to add new functionality:
                - Custom Flash style
                - Uses s3_has_role()
                - Administrators (id=1) are deemed to have all roles
        """

        def decorator(action):

            def f(*a, **b):

                if self.override:
                    return action(*a, **b)

                ADMIN = self.get_system_roles().ADMIN
                if not self.s3_has_role(role) and not self.s3_has_role(ADMIN):
                    self.permission.fail()

                return action(*a, **b)

            f.__doc__ = action.__doc__

            return f

        return decorator

    # Override original method
    requires_membership = s3_requires_membership

    # -------------------------------------------------------------------------
    # Record Ownership
    # -------------------------------------------------------------------------
    def s3_make_session_owner(self, table, record_id):
        """
            Makes the current session owner of a record

            @param table: the table or table name
            @param record_id: the record ID
        """

        if hasattr(table, "_tablename"):
            tablename = original_tablename(table)
        else:
            tablename = table

        if not self.user:

            session = current.session
            if "owned_records" not in session:
                session.owned_records = {}

            records = session.owned_records.get(tablename, [])
            record_id = str(record_id)
            if record_id not in records:
                records.append(record_id)

            session.owned_records[tablename] = records

    # -------------------------------------------------------------------------
    def s3_session_owns(self, table, record_id):
        """
            Checks whether the current session owns a record

            @param table: the table or table name
            @param record_id: the record ID
        """

        session = current.session
        if self.user or not record_id or "owned_records" not in session:
            return False

        if hasattr(table, "_tablename"):
            tablename = original_tablename(table)
        else:
            tablename = table

        records = session.owned_records.get(tablename)
        if records:
            return str(record_id) in records

        return False

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_clear_session_ownership(table=None, record_id=None):
        """
            Removes session ownership for a record

            @param table: the table or table name (default: all tables)
            @param record_id: the record ID (default: all records)
        """

        session = current.session
        if "owned_records" not in session:
            return

        if table is not None:

            if hasattr(table, "_tablename"):
                tablename = original_tablename(table)
            else:
                tablename = table

            if tablename in session.owned_records:

                if record_id:
                    # Remove just this record ID
                    record_id = str(record_id)
                    records = session.owned_records[tablename]
                    if record_id in records:
                        records.remove(record_id)
                else:
                    # Remove all record IDs for this table
                    del session.owned_records[tablename]
        else:
            # Remove all session ownerships
            session.owned_records = {}

    # -------------------------------------------------------------------------
    def s3_update_record_owner(self, table, record, update=False, **fields):
        """
            Update ownership fields in a record (DRY helper method for
            s3_set_record_owner and set_realm_entity)

            @param table: the table
            @param record: the record or record ID
            @param update: True to update realm_entity in all realm-components
            @param fields: dict of {ownership_field:value}
        """

        # Ownership fields
        OUSR = "owned_by_user"
        OGRP = "owned_by_group"
        REALM = "realm_entity"

        ownership_fields = (OUSR, OGRP, REALM)

        pkey = table._id.name
        if isinstance(record, (Row, dict)) and pkey in record:
            record_id = record[pkey]
        else:
            record_id = record

        data = dict((key, fields[key]) for key in fields
                                       if key in ownership_fields)
        if not data:
            return

        db = current.db

        # Update record
        q = (table._id == record_id)
        success = db(q).update(**data)

        if success and update and REALM in data:

            # Update realm-components
            # Only goes down 1 level: doesn't do components of components
            s3db = current.s3db
            realm_components = s3db.get_config(table, "realm_components")

            if realm_components:
                resource = s3db.resource(table,
                                         components = realm_components,
                                         )
                components = resource.components
                realm = {REALM: data[REALM]}
                for alias in realm_components:
                    component = components.get(alias)
                    if not component:
                        continue
                    ctable = component.table
                    if REALM not in ctable.fields:
                        continue
                    query = component.get_join() & q
                    rows = db(query).select(ctable._id)
                    ids = set(row[ctable._id] for row in rows)
                    if ids:
                        ctablename = component.tablename
                        if ctable._tablename != ctablename:
                            # Component with table alias => switch to
                            # original table for update:
                            ctable = db[ctablename]
                        db(ctable._id.belongs(ids)).update(**realm)

        # Update super-entity
        self.update_shared_fields(table, record, **data)

    # -------------------------------------------------------------------------
    def s3_set_record_owner(self,
                            table,
                            record,
                            force_update=False,
                            **fields):
        """
            Set the record owned_by_user, owned_by_group and realm_entity
            for a record (auto-detect values).

            To be called by CRUD and Importer during record creation.

            @param table: the Table (or table name)
            @param record: the record (or record ID)
            @param force_update: True to update all fields regardless of
                                 the current value in the record, False
                                 to only update if current value is None
            @param fields: override auto-detected values, see keywords
            @keyword owned_by_user: the auth_user ID of the owner user
            @keyword owned_by_group: the auth_group ID of the owner group
            @keyword realm_entity: the pe_id of the realm entity, or a tuple
                                   (instance_type, instance_id) to lookup the
                                   pe_id, e.g. ("org_organisation", 2)

            @note: Only use with force_update for deliberate owner changes (i.e.
                   with explicit owned_by_user/owned_by_group) - autodetected
                   values can have undesirable side-effects. For mere realm
                   updates use set_realm_entity instead.

            @note: If used with force_update, this will also update the
                   realm_entity in all configured realm_components, i.e.
                   no separate call to set_realm_entity required.
        """

        s3db = current.s3db

        # Ownership fields
        OUSR = "owned_by_user"
        OGRP = "owned_by_group"
        REALM = "realm_entity"

        ownership_fields = (OUSR, OGRP, REALM)

        # Entity reference fields
        EID = "pe_id"
        OID = "organisation_id"
        SID = "site_id"
        GID = "group_id"
        PID = "person_id"
        entity_fields = (EID, OID, SID, GID, PID)

        # Find the table
        if hasattr(table, "_tablename"):
            tablename = original_tablename(table)
        else:
            tablename = table
            table = s3db.table(tablename)
        if not table:
            return

        # Get the record ID
        pkey = table._id.name
        if isinstance(record, (Row, dict)):
            if pkey not in record:
                return
            else:
                record_id = record[pkey]
        else:
            record_id = record
            record = Storage()

        # Find the available fields
        fields_in_table = [f for f in ownership_fields if f in table.fields]
        if not fields_in_table:
            return
        fields_in_table += [f for f in entity_fields if f in table.fields]

        # Get all available fields for the record
        fields_missing = [f for f in fields_in_table if f not in record]
        if fields_missing:
            fields_to_load = [table._id] + [table[f] for f in fields_in_table]
            query = (table._id == record_id)
            row = current.db(query).select(limitby=(0, 1),
                                           *fields_to_load).first()
        else:
            row = record
        if not row:
            return

        # Prepare the update
        data = Storage()

        # Find owned_by_user
        if OUSR in fields_in_table:
            pi = ("pr_person",
                  "pr_identity",
                  "pr_education",
                  "pr_contact",
                  "pr_address",
                  "pr_contact_emergency",
                  "pr_person_details",
                  "pr_physical_description",
                  "pr_group_membership",
                  "pr_image",
                  "hrm_training",
                  )
            if OUSR in fields:
                data[OUSR] = fields[OUSR]
            elif not row[OUSR] or tablename in pi:
                user_id = None
                # Records in PI tables should be owned by the person
                # they refer to (if that person has a user account)
                if tablename == "pr_person":
                    user_id = self.s3_get_user_id(person_id = row[table._id])
                elif PID in row and tablename in pi:
                    user_id = self.s3_get_user_id(person_id = row[PID])
                elif EID in row and tablename in pi:
                    user_id = self.s3_get_user_id(pe_id = row[EID])
                if not user_id and self.s3_logged_in() and self.user:
                    # Fallback to current user
                    user_id = self.user.id
                if user_id:
                    data[OUSR] = user_id

        # Find owned_by_group
        if OGRP in fields_in_table:
            # Check for type-specific handler to find the owner group
            handler = s3db.get_config(tablename, "owner_group")
            if handler:
                if callable(handler):
                    data[OGRP] = handler(table, row)
                else:
                    data[OGRP] = handler
            # Otherwise, only set if explicitly specified
            elif OGRP in fields:
                data[OGRP] = fields[OGRP]

        # Find realm entity
        if REALM in fields_in_table:
            if REALM in row and row[REALM] and not force_update:
                pass
            else:
                if REALM in fields:
                    entity = fields[REALM]
                else:
                    entity = 0
                realm_entity = self.get_realm_entity(table, row,
                                                     entity=entity)
                data[REALM] = realm_entity

        self.s3_update_record_owner(table, row, update=force_update, **data)

    # -------------------------------------------------------------------------
    def set_realm_entity(self, table, records, entity=0, force_update=False):
        """
            Update the realm entity for records, will also update the
            realm in all configured realm-entities, see:

            http://eden.sahanafoundation.org/wiki/S3AAA/OrgAuth#Realms1

            To be called by CRUD and Importer during record update.

            @param table: the Table (or tablename)
            @param records: - a single record
                            - a single record ID
                            - a list of records, or a Rows object
                            - a list of record IDs
                            - a query to find records in table
            @param entity: - an entity ID
                           - a tuple (table, instance_id)
                           - 0 for default lookup
        """

        db = current.db
        s3db = current.s3db

        REALM = "realm_entity"

        EID = "pe_id"
        OID = "organisation_id"
        SID = "site_id"
        GID = "group_id"
        entity_fields = (EID, OID, SID, GID)

        # Find the table
        if hasattr(table, "_tablename"):
            tablename = original_tablename(table)
        else:
            tablename = table
            table = s3db.table(tablename)
        if not table or REALM not in table.fields:
            return

        # Find the available fields
        fields_in_table = [table._id.name, REALM] + \
                          [f for f in entity_fields if f in table.fields]
        fields_to_load = [table[f] for f in fields_in_table]

        # Realm entity specified by call?
        realm_entity = entity
        if isinstance(realm_entity, tuple):
            realm_entity = s3db.pr_get_pe_id(realm_entity)
            if not realm_entity:
                return

        if isinstance(records, Query):
            query = records
        else:
            query = None

        # Bulk update?
        if realm_entity != 0 and force_update and query is not None:
            data = {REALM:realm_entity}
            db(query).update(**data)
            self.update_shared_fields(table, query, **data)
            return

        # Find the records
        if query is not None:
            if not force_update:
                query &= (table[REALM] == None)
            records = db(query).select(*fields_to_load)
        elif not isinstance(records, (list, Rows)):
            records = [records]
        if not records:
            return

        # Update record by record
        get_realm_entity = self.get_realm_entity
        s3_update_record_owner = self.s3_update_record_owner
        for record in records:

            if not isinstance(record, (Row, Storage)):
                record_id = record
                row = Storage()
            else:
                row = record
                if table._id.name not in record:
                    continue
                record_id = row[table._id.name]
            q = (table._id == record_id)

            # Do we need to reload the record?
            fields_missing = [f for f in fields_in_table if f not in row]
            if fields_missing:
                row = db(q).select(*fields_to_load, limitby = (0, 1)).first()
                if not row:
                    continue

            # Do we need to update the record at all?
            if row[REALM] and not force_update:
                continue

            _realm_entity = get_realm_entity(table, row,
                                             entity=realm_entity)
            data = {REALM:_realm_entity}
            s3_update_record_owner(table, row,
                                   update=force_update, **data)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def get_realm_entity(table, record, entity=0):
        """
            Lookup the realm entity for a record

            @param table: the Table
            @param record: the record (as Row or dict)
            @param entity: the entity (pe_id)
        """

        if "realm_entity" not in table:
            return None

        s3db = current.s3db

        # Entity specified by call?
        if isinstance(entity, tuple):
            realm_entity = s3db.pr_get_pe_id(entity)
        else:
            realm_entity = entity

        # See if there is a deployment-global method to determine the realm entity
        if realm_entity == 0:
            handler = current.deployment_settings.get_auth_realm_entity()
            if callable(handler):
                realm_entity = handler(table, record)

        # Fall back to table-specific method
        if realm_entity == 0:
            handler = s3db.get_config(table, "realm_entity")
            if callable(handler):
                realm_entity = handler(table, record)

        # Fall back to standard lookup cascade
        if realm_entity == 0:
            tablename = original_tablename(table)
            if "pe_id" in record and \
               tablename not in ("pr_person", "dvi_body"):
                realm_entity = record["pe_id"]
            elif "organisation_id" in record:
                realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                 record["organisation_id"])
            elif "site_id" in record:
                realm_entity = s3db.pr_get_pe_id("org_site",
                                                 record["site_id"])
            elif "group_id" in record:
                realm_entity = s3db.pr_get_pe_id("pr_group",
                                                 record["group_id"])
            else:
                realm_entity = None

        return realm_entity

    # -------------------------------------------------------------------------
    @staticmethod
    def update_shared_fields(table, record, **data):
        """
            Update the shared fields in data in all super-entity rows linked
            with this record.

            @param table: the table
            @param record: a record, record ID or a query
            @param data: the field/value pairs to update
        """

        db = current.db
        s3db = current.s3db

        super_entities = s3db.get_config(table, "super_entity")
        if not super_entities:
            return
        if not isinstance(super_entities, (list, tuple)):
            super_entities = [super_entities]

        tables = {}
        load = s3db.table
        super_key = s3db.super_key
        for se in super_entities:
            supertable = load(se)
            if not supertable or \
               not any([f in supertable.fields for f in data]):
                continue
            tables[super_key(supertable)] = supertable

        if not isinstance(record, (Row, dict)) or \
           any([f not in record for f in tables]):
            if isinstance(record, Query):
                query = record
                limitby = None
            elif isinstance(record, (Row, dict)):
                query = table._id == record[table._id.name]
                limitby = (0, 1)
            else:
                query = table._id == record
                limitby = (0, 1)
            fields = [table[f] for f in tables]
            records = db(query).select(limitby=limitby, *fields)
        else:
            records = [record]
        if not records:
            return

        for record in records:
            for skey in tables:
                supertable = tables[skey]
                if skey in record:
                    query = (supertable[skey] == record[skey])
                else:
                    continue
                updates = dict((f, data[f])
                               for f in data if f in supertable.fields)
                if not updates:
                    continue
                db(query).update(**updates)

    # -------------------------------------------------------------------------
    def permitted_facilities(self,
                             table=None,
                             error_msg=None,
                             redirect_on_error=True,
                             facility_type=None):
        """
            If there are no facilities that the user has permission for,
            prevents create & update of records in table & gives a
            warning if the user tries to.

            @param table: the table or table name
            @param error_msg: error message
            @param redirect_on_error: whether to redirect on error
            @param facility_type: restrict to this particular type of
                                  facilities (a tablename)
        """

        T = current.T
        ERROR = T("You do not have permission for any facility to perform this action.")
        HINT = T("Create a new facility or ensure that you have permissions for an existing facility.")

        if not error_msg:
            error_msg = ERROR

        s3db = current.s3db
        site_ids = []
        if facility_type is None:
            site_types = self.org_site_types
        else:
            if facility_type not in self.org_site_types:
                return site_ids
            site_types = [s3db[facility_type]]
        for site_type in site_types:
            try:
                ftable = s3db[site_type]
                if not "site_id" in ftable.fields:
                    continue
                query = self.s3_accessible_query("update", ftable)
                if "deleted" in ftable:
                    query &= (ftable.deleted != True)
                rows = current.db(query).select(ftable.site_id)
                site_ids += [row.site_id for row in rows]
            except:
                # Module disabled
                pass

        if site_ids:
            return site_ids

        args = current.request.args
        if "update" in args or "create" in args:
            if redirect_on_error:
                # Trying to create or update
                # If they do no have permission to any facilities
                current.session.error = "%s %s" % (error_msg, HINT)
                redirect(URL(c="default", f="index"))
        elif table is not None:
            if hasattr(table, "_tablename"):
                tablename = original_tablename(table)
            else:
                tablename = table
            s3db.configure(tablename, insertable=False)

        return site_ids # Will be []

    # -------------------------------------------------------------------------
    def permitted_organisations(self,
                                table=None,
                                error_msg=None,
                                redirect_on_error=True):
        """
            If there are no organisations that the user has update
            permission for, prevents create & update of a record in
            table & gives an warning if the user tries to.

            @param table: the table or table name
            @param error_msg: error message
            @param redirect_on_error: whether to redirect on error
        """

        T = current.T
        ERROR = T("You do not have permission for any organization to perform this action.")
        HINT = T("Create a new organization or ensure that you have permissions for an existing organization.")

        if not error_msg:
            error_msg = ERROR

        s3db = current.s3db
        org_table = s3db.org_organisation
        query = self.s3_accessible_query("update", org_table)
        query &= (org_table.deleted == False)
        rows = current.db(query).select(org_table.id)
        if rows:
            return [org.id for org in rows]
        request = current.request
        if "update" in request.args or "create" in request.args:
            if redirect_on_error:
                current.session.error = error_msg + " " + HINT
                redirect(URL(c="default", f="index"))
        elif table is not None:
            if hasattr(table, "_tablename"):
                tablename = original_tablename(table)
            else:
                tablename = table
            s3db.configure(tablename, insertable=False)

        return []

    # -------------------------------------------------------------------------
    def root_org(self):
        """
            Return the current user's root organisation ID or None
        """

        if not self.user:
            return None
        org_id = self.user.organisation_id
        if not org_id:
            return None
        if not current.deployment_settings.get_org_branches():
            return org_id
        return current.cache.ram(
                    # Common key for all users of this org & vol_service_record() & hrm_training_event_realm_entity()
                    "root_org_%s" % org_id,
                    lambda: current.s3db.org_root_organisation(org_id),
                    time_expire=120
                )

    # -------------------------------------------------------------------------
    def root_org_name(self):
        """
            Return the current user's root organisation name or None
        """

        if not self.user:
            return None
        org_id = self.user.organisation_id
        if not org_id:
            return None
        if not current.deployment_settings.get_org_branches():
            s3db = current.s3db
            table = s3db.org_organisation
            row = current.db(table.id == org_id).select(table.name,
                                                        cache = s3db.cache,
                                                        limitby=(0, 1)).first()
            try:
                return row.name
            except:
                # Org not found!
                return None
        return current.cache.ram(
                    # Common key for all users of this org
                    "root_org_name_%s" % org_id,
                    lambda: current.s3db.org_root_organisation_name(org_id),
                    time_expire=120
                )

    # -------------------------------------------------------------------------
    def filter_by_root_org(self, table):
        """
            Function to return a query to filter a table to only display results
            for the user's root org OR record with no root org
            @ToDo: Restore Realms and add a role/functionality support for Master Data
                   Then this function is redundant
        """

        root_org = self.root_org()
        if root_org:
            return (table.organisation_id == root_org) | (table.organisation_id == None)
        else:
            return (table.organisation_id == None)

# =============================================================================
class S3Permission(object):
    """ S3 Class to handle permissions """

    TABLENAME = "s3_permission"

    CREATE = 0x0001     # Permission to create new records
    READ = 0x0002       # Permission to read records
    UPDATE = 0x0004     # Permission to update records
    DELETE = 0x0008     # Permission to delete records
    REVIEW = 0x0010     # Permission to review unapproved records
    APPROVE = 0x0020    # Permission to approve records
    PUBLISH = 0x0040    # Permission to publish records outside of Eden

    ALL = CREATE | READ | UPDATE | DELETE | REVIEW | APPROVE | PUBLISH
    NONE = 0x0000 # must be 0!

    PERMISSION_OPTS = OrderedDict([
        [CREATE, "CREATE"],
        [READ, "READ"],
        [UPDATE, "UPDATE"],
        [DELETE, "DELETE"],
        [REVIEW, "REVIEW"],
        [APPROVE, "APPROVE"],
        #[PUBLISH, "PUBLISH"],   # currently unused
    ])

    # Method <-> required permission
    METHODS = Storage({
        "create": CREATE,
        "read": READ,
        "update": UPDATE,
        "delete": DELETE,
        "map": READ,
        "report": READ,
        #"search": READ,
        "timeplot": READ,
        "import": CREATE,
        "review": REVIEW,
        "approve": APPROVE,
        "reject": APPROVE,
        "publish": PUBLISH,
    })

    # Lambda expressions for ACL handling
    required_acl = lambda self, methods: \
                          reduce(lambda a, b: a | b,
                                 [self.METHODS[m]
                                  for m in methods if m in self.METHODS],
                                 self.NONE)
    most_permissive = lambda self, acl: \
                             reduce(lambda x, y: (x[0]|y[0], x[1]|y[1]),
                                    acl, (self.NONE, self.NONE))
    most_restrictive = lambda self, acl: \
                              reduce(lambda x, y: (x[0]&y[0], x[1]&y[1]),
                                     acl, (self.ALL, self.ALL))

    # -------------------------------------------------------------------------
    def __init__(self, auth, tablename=None):
        """
            Constructor, invoked by AuthS3.__init__

            @param auth: the AuthS3 instance
            @param tablename: the name for the permissions table
        """

        db = current.db

        # Instantiated once per request, but before Auth tables
        # are defined and authentication is checked, thus no use
        # to check permissions in the constructor

        # Store auth reference in self because current.auth is not
        # available at this point yet, but needed in define_table.
        self.auth = auth

        self.error = S3PermissionError

        settings = current.deployment_settings

        # Policy: which level of granularity do we want?
        self.policy = settings.get_security_policy()
        # ACLs to control access per controller:
        self.use_cacls = self.policy in (3, 4, 5, 6, 7, 8)
        # ACLs to control access per function within controllers:
        self.use_facls = self.policy in (4, 5, 6, 7, 8)
        # ACLs to control access per table:
        self.use_tacls = self.policy in (5, 6, 7, 8)
        # Authorization takes realm entity into account:
        self.entity_realm = self.policy in (6, 7, 8)
        # Permissions shared along the hierarchy of entities:
        self.entity_hierarchy = self.policy in (7, 8)
        # Permission sets can be delegated:
        self.delegations = self.policy == 8

        # Permissions table
        self.tablename = tablename or self.TABLENAME
        if self.tablename in db:
            self.table = db[self.tablename]
        else:
            self.table = None

        # Error messages
        T = current.T
        self.INSUFFICIENT_PRIVILEGES = T("Insufficient Privileges")
        self.AUTHENTICATION_REQUIRED = T("Authentication Required")

        # Request information
        request = current.request
        self.controller = request.controller
        self.function = request.function

        # Request format
        self.format = s3_get_extension()

        # Settings
        self.record_approval = settings.get_auth_record_approval()
        self.strict_ownership = settings.get_security_strict_ownership()

        # Clear cache
        self.clear_cache()

        # Pages which never require permission:
        # Make sure that any data access via these pages uses
        # accessible_query explicitly!
        self.unrestricted_pages = ("default/index",
                                   "default/user",
                                   "default/contact",
                                   "default/about")

        # Default landing pages
        _next = URL(args=request.args, vars=request.get_vars)
        self.homepage = URL(c="default", f="index")
        self.loginpage = URL(c="default", f="user", args="login",
                             vars=dict(_next=_next))

    # -------------------------------------------------------------------------
    def clear_cache(self):
        """ Clear any cached permissions or accessible-queries """

        self.permission_cache = {}
        self.query_cache = {}

    # -------------------------------------------------------------------------
    def check_settings(self):
        """
            Check whether permission-relevant settings have changed
            during the request, and clear the cache if so.
        """

        clear_cache = False
        settings = current.deployment_settings

        record_approval = settings.get_auth_record_approval()
        if record_approval != self.record_approval:
            clear_cache = True
            self.record_approval = record_approval

        strict_ownership = settings.get_security_strict_ownership()
        if strict_ownership != self.strict_ownership:
            clear_cache = True
            self.strict_ownership = strict_ownership

        if clear_cache:
            self.clear_cache()

    # -------------------------------------------------------------------------
    def define_table(self, migrate=True, fake_migrate=False):
        """
            Define permissions table, invoked by AuthS3.define_tables()
        """

        table_group = self.auth.settings.table_group
        if table_group is None:
            table_group = "integer" # fallback (doesn't work with requires)

        if not self.table:
            db = current.db
            db.define_table(self.tablename,
                            Field("group_id", table_group),
                            Field("controller", length=64),
                            Field("function", length=512),
                            Field("tablename", length=512),
                            Field("record", "integer"),
                            Field("oacl", "integer", default=self.ALL),
                            Field("uacl", "integer", default=self.READ),
                            # apply this ACL only to records owned
                            # by this entity
                            Field("entity", "integer"),
                            # apply this ACL to all records regardless
                            # of the realm entity
                            Field("unrestricted", "boolean",
                                  default=False),
                            migrate=migrate,
                            fake_migrate=fake_migrate,
                            *S3MetaFields.sync_meta_fields())
            self.table = db[self.tablename]

    # -------------------------------------------------------------------------
    # ACL Management
    # -------------------------------------------------------------------------
    def update_acl(self, group,
                   c=None,
                   f=None,
                   t=None,
                   record=None,
                   oacl=None,
                   uacl=None,
                   entity=None,
                   delete=False):
        """
            Update an ACL

            @param group: the ID or UID of the auth_group this ACL applies to
            @param c: the controller
            @param f: the function
            @param t: the tablename
            @param record: the record (as ID or Row with ID)
            @param oacl: the ACL for the owners of the specified record(s)
            @param uacl: the ACL for all other users
            @param entity: restrict this ACL to the records owned by this
                           entity (pe_id), specify "any" for any entity
            @param delete: delete the ACL instead of updating it
        """

        ANY = "any"

        unrestricted = entity == ANY
        if unrestricted:
            entity = None

        table = self.table
        if not table:
            # ACLs not relevant to this security policy
            return None

        s3 = current.response.s3
        if "restricted_tables" in s3:
            del s3["restricted_tables"]
        self.clear_cache()

        if c is None and f is None and t is None:
            return None
        if t is not None:
            c = f = None
        else:
            record = None

        if uacl is None:
            uacl = self.NONE
        if oacl is None:
            oacl = uacl

        success = False
        if group:
            group_id = None
            acl = dict(group_id=group_id,
                       deleted=False,
                       controller=c,
                       function=f,
                       tablename=t,
                       record=record,
                       oacl=oacl,
                       uacl=uacl,
                       unrestricted=unrestricted,
                       entity=entity)

            if isinstance(group, basestring) and not group.isdigit():
                gtable = self.auth.settings.table_group
                query = (gtable.uuid == group) & \
                        (table.group_id == gtable.id)
            else:
                query = (table.group_id == group)
                group_id = group

            query &= ((table.controller == c) & \
                      (table.function == f) & \
                      (table.tablename == t) & \
                      (table.record == record) & \
                      (table.unrestricted == unrestricted) & \
                      (table.entity == entity))
            record = current.db(query).select(table.id,
                                              table.group_id,
                                              limitby=(0, 1)).first()
            if record:
                if delete:
                    acl = dict(
                        group_id = None,
                        deleted = True,
                        deleted_fk = '{"group_id": %d}' % record.group_id
                    )
                else:
                    acl["group_id"] = record.group_id
                record.update_record(**acl)
                success = record.id
            elif group_id:
                acl["group_id"] = group_id
                success = table.insert(**acl)
            else:
                # Lookup the group_id
                record = current.db(gtable.uuid == group).select(gtable.id,
                                                                 limitby=(0, 1)
                                                                 ).first()
                if record:
                    acl["group_id"] = group_id
                    success = table.insert(**acl)

        return success

    # -------------------------------------------------------------------------
    def delete_acl(self, group,
                   c=None,
                   f=None,
                   t=None,
                   record=None,
                   entity=None):
        """
            Delete an ACL
            @param group: the ID or UID of the auth_group this ACL applies to
            @param c: the controller
            @param f: the function
            @param t: the tablename
            @param record: the record (as ID or Row with ID)
            @param entity: restrict this ACL to the records owned by this
                           entity (pe_id), specify "any" for any entity
        """

        return self.update_acl(group,
                               c=c,
                               f=f,
                               t=t,
                               record=record,
                               entity=entity,
                               delete=True)

    # -------------------------------------------------------------------------
    # Record Ownership
    # -------------------------------------------------------------------------
    @staticmethod
    def get_owners(table, record):
        """
            Get the entity/group/user owning a record

            @param table: the table
            @param record: the record ID (or the Row, if already loaded)

            @note: if passing a Row, it must contain all available ownership
                   fields (id, owned_by_user, owned_by_group, realm_entity),
                   otherwise the record will be re-loaded by this function.

            @return: tuple of (realm_entity, owner_group, owner_user)
        """

        realm_entity = None
        owner_group = None
        owner_user = None

        record_id = None

        DEFAULT = (None, None, None)

        # Load the table, if necessary
        if table and not hasattr(table, "_tablename"):
            table = current.s3db.table(table)
        if not table:
            return DEFAULT

        # Check which ownership fields the table defines
        ownership_fields = ("realm_entity",
                            "owned_by_group",
                            "owned_by_user")
        fields = [f for f in ownership_fields if f in table.fields]
        if not fields:
            # Ownership is not defined for this table
            return DEFAULT

        if isinstance(record, Row):
            # Check if all necessary fields are present
            missing = [f for f in fields if f not in record]
            if missing:
                # Have to reload the record :(
                if table._id.name in record:
                    record_id = record[table._id.name]
                record = None
        else:
            # Record ID given, must load the record anyway
            record_id = record
            record = None

        if not record and record_id:
            # Get the record
            fs = [table[f] for f in fields] + [table.id]
            query = (table._id == record_id)
            record = current.db(query).select(limitby=(0, 1), *fs).first()
        if not record:
            # Record does not exist
            return DEFAULT

        if "realm_entity" in record:
            realm_entity = record["realm_entity"]
        if "owned_by_group" in record:
            owner_group = record["owned_by_group"]
        if "owned_by_user" in record:
            owner_user = record["owned_by_user"]
        return (realm_entity, owner_group, owner_user)

    # -------------------------------------------------------------------------
    def is_owner(self, table, record, owners=None, strict=False):
        """
            Check whether the current user owns the record

            @param table: the table or tablename
            @param record: the record ID (or the Row if already loaded)
            @param owners: override the actual record owners by a tuple
                           (realm_entity, owner_group, owner_user)

            @return: True if the current user owns the record, else False
        """

        auth = self.auth
        user_id = None
        sr = auth.get_system_roles()

        if auth.user is not None:
            user_id = auth.user.id

        session = current.session
        roles = [sr.ANONYMOUS]
        if session.s3 is not None:
            roles = session.s3.roles or roles

        if sr.ADMIN in roles:
            # Admin owns all records
            return True
        elif owners is not None:
            realm_entity, owner_group, owner_user = owners
        elif record:
            realm_entity, owner_group, owner_user = \
                    self.get_owners(table, record)
        else:
            # All users own no records
            return True

        # Session ownership?
        if not user_id:
            if isinstance(record, (Row, dict)):
                record_id = record[table._id.name]
            else:
                record_id = record
            return auth.s3_session_owns(table, record_id)

        # Individual record ownership
        if owner_user and owner_user == user_id:
            return True

        # Public record?
        if not any((realm_entity, owner_group, owner_user)) and not strict:
            return True
        elif strict:
            return False

        # OrgAuth: apply only group memberships within the realm
        if self.entity_realm and realm_entity:
            realms = auth.user.realms
            roles = [sr.ANONYMOUS]
            append = roles.append
            for r in realms:
                realm = realms[r]
                if realm is None or realm_entity in realm:
                    append(r)

        # Ownership based on user role
        return bool(owner_group and owner_group in roles)

    # -------------------------------------------------------------------------
    def owner_query(self,
                    table,
                    user,
                    use_realm=True,
                    realm=None,
                    no_realm=None):
        """
            Returns a query to select the records in table owned by user

            @param table: the table
            @param user: the current auth.user (None for not authenticated)
            @param use_realm: use realms
            @param realm: limit owner access to these realms
            @param no_realm: don't include these entities in role realms
            @return: a web2py Query instance, or None if no query can be
                      constructed
        """

        OUSR = "owned_by_user"
        OGRP = "owned_by_group"
        OENT = "realm_entity"

        if realm is None:
            realm = []

        no_realm = set() if no_realm is None else set(no_realm)

        query = None
        if user is None:
            # Session ownership?
            if hasattr(table, "_tablename"):
                tablename = original_tablename(table)
            else:
                tablename = table
            session = current.session
            if "owned_records" in session and \
               tablename in session.owned_records:
                query = (table._id.belongs(session.owned_records[tablename]))
        else:
            use_realm = use_realm and \
                        OENT in table.fields and self.entity_realm

            # Individual owner query
            if OUSR in table.fields:
                user_id = user.id
                query = (table[OUSR] == user_id)
                if use_realm:
                    # Limit owner access to permitted realms
                    if realm:
                        realm_query = self.realm_query(table, realm)
                        if realm_query:
                            query &= realm_query
                    else:
                        query = None

            if not self.strict_ownership:

                # Any authenticated user owns all records with no owner
                public = None
                if OUSR in table.fields:
                    public = (table[OUSR] == None)
                if OGRP in table.fields:
                    q = (table[OGRP] == None)
                    if public:
                        public &= q
                    else:
                        public = q
                if use_realm:
                    q = (table[OENT] == None)
                    if public:
                        public &= q
                    else:
                        public = q

                if public is not None:
                    if query is not None:
                        query |= public
                    else:
                        query = public

            # Group ownerships
            if OGRP in table.fields:
                any_entity = set()
                g = None
                user_realms = user.realms
                for group_id in user_realms:

                    role_realm = user_realms[group_id]

                    if role_realm is None or not use_realm:
                        any_entity.add(group_id)
                        continue

                    role_realm = set(role_realm) - no_realm

                    if role_realm:
                        q = (table[OGRP] == group_id) & (table[OENT].belongs(role_realm))
                        if g is None:
                            g = q
                        else:
                            g |= q
                if any_entity:
                    q = (table[OGRP].belongs(any_entity))
                    if g is None:
                        g = q
                    else:
                        g |= q
                if g is not None:
                    if query is None:
                        query = g
                    else:
                        query |= g

        return query

    # -------------------------------------------------------------------------
    @staticmethod
    def realm_query(table, entities):
        """
            Returns a query to select the records owned by one of the entities.

            @param table: the table
            @param entities: list of entities
            @return: a web2py Query instance, or None if no query can be
                      constructed
        """

        OENT = "realm_entity"

        query = None

        if entities and "ANY" not in entities and OENT in table.fields:
            public = (table[OENT] == None)
            if len(entities) == 1:
                query = (table[OENT] == entities[0]) | public
            else:
                query = (table[OENT].belongs(entities)) | public

        return query

    # -------------------------------------------------------------------------
    def permitted_realms(self, tablename, method="read"):
        """
            Returns a list of the realm entities which a user can access for
            the given table.

            @param tablename: the tablename
            @param method: the method
            @return: a list of pe_ids or None (for no restriction)
        """

        if not self.entity_realm:
            # Security Policy doesn't use Realms, so unrestricted
            return None

        auth = self.auth
        sr = auth.get_system_roles()
        user = auth.user
        if auth.is_logged_in():
            realms = user.realms
            if sr.ADMIN in realms:
                # ADMIN can see all Realms
                return None
            delegations = user.delegations
        else:
            realms = Storage({sr.ANONYMOUS:None})
            delegations = Storage()

        racl = self.required_acl([method])
        request = current.request
        acls = self.applicable_acls(racl,
                                    realms=realms,
                                    delegations=delegations,
                                    c=request.controller,
                                    f=request.function,
                                    t=tablename)
        if "ANY" in acls:
            # User is permitted access for all Realms
            return None

        entities = []
        for entity in acls:
            acl = acls[entity]
            if acl[0] & racl == racl:
                entities.append(entity)

        return entities

    # -------------------------------------------------------------------------
    # Record approval
    # -------------------------------------------------------------------------
    def approved(self, table, record, approved=True):
        """
            Check whether a record has been approved or not

            @param table: the table
            @param record: the record or record ID
            @param approved: True = check if approved,
                             False = check if unapproved
        """

        if "approved_by" not in table.fields or \
           not self.requires_approval(table):
            return approved

        if isinstance(record, (Row, dict)):
            if "approved_by" not in record:
                record_id = record[table._id]
                record = None
        else:
            record_id = record
            record = None

        if record is None and record_id:
            record = current.db(table._id == record_id).select(table.approved_by,
                                                               limitby=(0, 1)
                                                               ).first()
            if not record:
                return False

        if approved and record["approved_by"] is not None:
            return True
        elif not approved and record["approved_by"] is None:
            return True
        else:
            return False

    # -------------------------------------------------------------------------
    def unapproved(self, table, record):
        """
            Check whether a record has not been approved yet

            @param table: the table
            @param record: the record or record ID
        """

        return self.approved(table, record, approved=False)

    # -------------------------------------------------------------------------
    @classmethod
    def requires_approval(cls, table):
        """
            Check whether record approval is required for a table

            @param table: the table (or tablename)
        """

        settings = current.deployment_settings

        if settings.get_auth_record_approval():

            if type(table) is Table:
                tablename = original_tablename(table)
            else:
                tablename = table

            tables = settings.get_auth_record_approval_required_for()
            if tables is not None:
                return tablename in tables

            elif current.s3db.get_config(tablename, "requires_approval"):
                return True

            else:
                return False
        else:
            return False

    # -------------------------------------------------------------------------
    @classmethod
    def set_default_approver(cls, table, force=False):
        """
            Set the default approver for new records in table

            @param table: the table
            @param force: whether to force approval for tables which
                          require manual approval
        """

        APPROVER = "approved_by"
        if APPROVER in table:
            approver = table[APPROVER]
        else:
            return

        settings = current.deployment_settings
        auth = current.auth

        tablename = original_tablename(table)

        if not settings.get_auth_record_approval():
            if auth.s3_logged_in() and auth.user:
                approver.default = auth.user.id
            else:
                approver.default = 0
        elif force or \
             tablename not in settings.get_auth_record_approval_manual():
            if auth.override:
                approver.default = 0
            elif auth.s3_logged_in() and \
                 auth.s3_has_permission("approve", table):
                approver.default = auth.user.id
            else:
                approver.default = None

    # -------------------------------------------------------------------------
    # Authorization
    # -------------------------------------------------------------------------
    def has_permission(self, method, c=None, f=None, t=None, record=None):
        """
            Check permission to access a record with method

            @param method: the access method (string)
            @param c: the controller name (falls back to current request)
            @param f: the function name (falls back to current request)
            @param t: the table or tablename
            @param record: the record or record ID (None for any record)
        """

        # Auth override, system roles and login
        auth = self.auth
        if auth.override:
            #_debug("==> auth.override")
            #_debug("*** GRANTED ***")
            return True

        # Multiple methods?
        if isinstance(method, (list, tuple)):
            for m in method:
                if self.has_permission(m, c=c, f=f, t=t, record=record):
                    return True
            return False
        else:
            method = [method]

        if record == 0:
            record = None

        #_debug("\nhas_permission('%s', c=%s, f=%s, t=%s, record=%s)",
        #       "|".join(method),
        #       c or current.request.controller,
        #       f or current.request.function,
        #       t,
        #       record,
        #       )

        sr = auth.get_system_roles()
        logged_in = auth.s3_logged_in()
        self.check_settings()

        # Required ACL
        racl = self.required_acl(method)
        #_debug("==> required ACL: %04X", racl)

        # Get realms and delegations
        if not logged_in:
            realms = Storage({sr.ANONYMOUS:None})
            delegations = Storage()
        else:
            realms = auth.user.realms
            delegations = auth.user.delegations

        # Administrators have all permissions
        if sr.ADMIN in realms:
            #_debug("==> user is ADMIN")
            #_debug("*** GRANTED ***")
            return True

        # Fall back to current request
        c = c or self.controller
        f = f or self.function

        if not self.use_cacls:
            #_debug("==> simple authorization")
            # Fall back to simple authorization
            if logged_in:
                #_debug("*** GRANTED ***")
                return True
            else:
                if self.page_restricted(c=c, f=f):
                    permitted = racl == self.READ
                else:
                    #_debug("==> unrestricted page")
                    permitted = True
                #if permitted:
                #    _debug("*** GRANTED ***")
                #else:
                #    _debug("*** DENIED ***")
                return permitted

        # Do we need to check the owner role (i.e. table+record given)?
        if t is not None and record is not None:
            owners = self.get_owners(t, record)
            is_owner = self.is_owner(t, record, owners=owners)
            entity = owners[0]
        else:
            owners = []
            is_owner = True
            entity = None

        permission_cache = self.permission_cache
        if permission_cache is None:
            permission_cache = self.permission_cache = {}
        key = "%s/%s/%s/%s/%s" % (method, c, f, t, record)
        if key in permission_cache:
            #permitted = permission_cache[key]
            #if permitted is None:
            #    pass
            #elif permitted:
            #    _debug("*** GRANTED (cached) ***")
            #else:
            #    _debug("*** DENIED (cached) ***")
            return permission_cache[key]

        # Get the applicable ACLs
        acls = self.applicable_acls(racl,
                                    realms=realms,
                                    delegations=delegations,
                                    c=c,
                                    f=f,
                                    t=t,
                                    entity=entity)

        permitted = None
        if acls is None:
            #_debug("==> no ACLs defined for this case")
            permitted = True
        elif not acls:
            #_debug("==> no applicable ACLs")
            permitted = False
        else:
            if entity:
                if entity in acls:
                    uacl, oacl = acls[entity]
                elif "ANY" in acls:
                    uacl, oacl = acls["ANY"]
                else:
                    #_debug("==> Owner entity outside realm")
                    permitted = False
            else:
                uacl, oacl = self.most_permissive(acls.values())

            #_debug("==> uacl: %04X, oacl: %04X", uacl, oacl)

            if permitted is None:
                if uacl & racl == racl:
                    permitted = True
                elif oacl & racl == racl:
                    #if is_owner and record:
                    #    _debug("==> User owns the record")
                    #elif record:
                    #    _debug("==> User does not own the record")
                    permitted = is_owner
                else:
                    permitted = False

        if permitted is None:
            raise self.error("Cannot determine permission.")

        elif permitted and \
             t is not None and record is not None and \
             self.requires_approval(t):

            # Approval possible for this table?
            if not hasattr(t, "_tablename"):
                table = current.s3db.table(t)
                if not table:
                    raise AttributeError("undefined table %s" % t)
            else:
                table = t
            if "approved_by" in table.fields:

                approval_methods = ("approve", "review", "reject")
                access_approved = not all([m in approval_methods for m in method])
                access_unapproved = any([m in method for m in approval_methods])

                if access_unapproved:
                    if not access_approved:
                        permitted = self.unapproved(table, record)
                        #if not permitted:
                        #    _debug("==> Record already approved")
                else:
                    permitted = self.approved(table, record) or \
                                self.is_owner(table, record, owners, strict=True) or \
                                self.has_permission("review", t=table, record=record)
                    #if not permitted:
                    #    _debug("==> Record not approved")
                    #    _debug("==> is owner: %s", is_owner)
            else:
                # Approval not possible for this table => no change
                pass

        #if permitted:
        #    _debug("*** GRANTED ***")
        #else:
        #    _debug("*** DENIED ***")

        # Remember the result for subsequent checks
        permission_cache[key] = permitted

        return permitted

    # -------------------------------------------------------------------------
    def accessible_query(self, method, table, c=None, f=None, deny=True):
        """
            Returns a query to select the accessible records for method
            in table.

            @param method: the method as string or a list of methods (AND)
            @param table: the database table or table name
            @param c: controller name (falls back to current request)
            @param f: function name (falls back to current request)
        """

        # Get the table
        if not hasattr(table, "_tablename"):
            tablename = table
            error = AttributeError("undefined table %s" % tablename)
            table = current.s3db.table(tablename,
                                       db_only = True,
                                       default = error,
                                       )

        if not isinstance(method, (list, tuple)):
            method = [method]

        #_debug("\naccessible_query(%s, '%s')", table, ",".join(method))

        # Defaults
        ALL_RECORDS = (table._id > 0)
        NO_RECORDS = (table._id == 0) if deny else None

        # Record approval required?
        if self.requires_approval(table) and \
           "approved_by" in table.fields:
            requires_approval = True
            APPROVED = (table.approved_by != None)
            UNAPPROVED = (table.approved_by == None)
        else:
            requires_approval = False
            APPROVED = ALL_RECORDS
            UNAPPROVED = NO_RECORDS

        # Approval method?
        approval_methods = ("review", "approve", "reject")
        unapproved = any([m in method for m in approval_methods])
        approved = not all([m in approval_methods for m in method])

        # What does ALL RECORDS mean?
        ALL_RECORDS = ALL_RECORDS if approved and unapproved \
                                  else UNAPPROVED if unapproved \
                                  else APPROVED

        # Auth override, system roles and login
        auth = self.auth
        if auth.override:
            #_debug("==> auth.override")
            #_debug("*** ALL RECORDS ***")
            return ALL_RECORDS

        sr = auth.get_system_roles()
        logged_in = auth.s3_logged_in()
        self.check_settings()

        # Get realms and delegations
        user = auth.user
        if not logged_in:
            realms = Storage({sr.ANONYMOUS:None})
            delegations = Storage()
        else:
            realms = user.realms
            delegations = user.delegations

        # Don't filter out unapproved records owned by the user
        if requires_approval and not unapproved and \
           "owned_by_user" in table.fields:
            ALL_RECORDS = (table.approved_by != None)
            if user:
                owner_query = (table.owned_by_user == user.id)
            else:
                owner_query = self.owner_query(table, None)
            if owner_query is not None:
                ALL_RECORDS |= owner_query

        # Administrators have all permissions
        if sr.ADMIN in realms:
            #_debug("==> user is ADMIN")
            #_debug("*** ALL RECORDS ***")
            return ALL_RECORDS

        # Multiple methods?
        if len(method) > 1:
            query = None
            for m in method:
                q = self.accessible_query(m, table, c=c, f=f, deny=False)
                if q is not None:
                    if query is None:
                        query = q
                    else:
                        query |= q
            if query is None:
                query = NO_RECORDS
            return query

        key = "%s/%s/%s/%s/%s" % (method, table, c, f, deny)
        query_cache = self.query_cache
        if key in query_cache:
            query = query_cache[key]
            return query

        # Required ACL
        racl = self.required_acl(method)
        #_debug("==> required permissions: %04X", racl)

        # Use ACLs?
        if not self.use_cacls:
            #_debug("==> simple authorization")
            # Fall back to simple authorization
            if logged_in:
                #_debug("*** ALL RECORDS ***")
                return ALL_RECORDS
            else:
                permitted = racl == self.READ
                if permitted:
                    #_debug("*** ALL RECORDS ***")
                    return ALL_RECORDS
                else:
                    #_debug("*** ACCESS DENIED ***")
                    return NO_RECORDS

        # Fall back to current request
        c = c or self.controller
        f = f or self.function

        # Get the applicable ACLs
        acls = self.applicable_acls(racl,
                                    realms=realms,
                                    delegations=delegations,
                                    c=c,
                                    f=f,
                                    t=table)

        if acls is None:
            #_debug("==> no ACLs defined for this case")
            #_debug("*** ALL RECORDS ***")
            query = query_cache[key] = ALL_RECORDS
            return query
        elif not acls:
            #_debug("==> no applicable ACLs")
            #_debug("*** ACCESS DENIED ***")
            query = query_cache[key] = NO_RECORDS
            return query

        oacls = []
        uacls = []
        for entity in acls:
            acl = acls[entity]
            if acl[0] & racl == racl:
                uacls.append(entity)
            elif acl[1] & racl == racl and entity not in uacls:
                oacls.append(entity)

        query = None
        no_realm = []
        check_owner_acls = True

        if "ANY" in uacls:
            #_debug("==> permitted for any records")
            query = ALL_RECORDS
            check_owner_acls = False

        elif uacls:
            query = self.realm_query(table, uacls)
            if query is None:
                #_debug("==> permitted for any records")
                query = ALL_RECORDS
                check_owner_acls = False
            else:
                #_debug("==> permitted for records owned by entities %s", str(uacls))
                no_realm = uacls

        if check_owner_acls:

            use_realm = "ANY" not in oacls
            owner_query = self.owner_query(table,
                                           user,
                                           use_realm=use_realm,
                                           realm=oacls,
                                           no_realm=no_realm,
                                           )

            if owner_query is not None:
                #_debug("==> permitted for owned records (limit to realms=%s)", use_realm)
                if query is not None:
                    query |= owner_query
                else:
                    query = owner_query
            elif use_realm:
                #_debug("==> permitted for any records owned by entities %s", str(uacls+oacls))
                query = self.realm_query(table, uacls+oacls)

            if query is not None and requires_approval:
                base_filter = None if approved and unapproved else \
                              UNAPPROVED if unapproved else APPROVED
                if base_filter is not None:
                    query = base_filter & query

        # Fallback
        if query is None:
            query = NO_RECORDS

        #_debug("*** Accessible Query ***")
        #_debug(str(query))
        query_cache[key] = query
        return query

    # -------------------------------------------------------------------------
    def accessible_url(self,
                       c=None,
                       f=None,
                       p=None,
                       t=None,
                       a=None,
                       args=None,
                       vars=None,
                       anchor="",
                       extension=None,
                       env=None):
        """
            Return a URL only if accessible by the user, otherwise False
            - used for Navigation Items

            @param c: the controller
            @param f: the function
            @param p: the permission (defaults to READ)
            @param t: the tablename (defaults to <c>_<f>)
            @param a: the application name
            @param args: the URL arguments
            @param vars: the URL variables
            @param anchor: the anchor (#) of the URL
            @param extension: the request format extension
            @param env: the environment
        """

        if args is None:
            args = []
        if vars is None:
            vars = {}

        if c != "static":
            # Hide disabled modules
            settings = current.deployment_settings
            if not settings.has_module(c):
                return False

        if t is None:
            t = "%s_%s" % (c, f)
            table = current.s3db.table(t)
            if not table:
                t = None
        if not p:
            p = "read"

        permitted = self.has_permission(p, c=c, f=f, t=t)
        if permitted:
            return URL(a=a,
                       c=c,
                       f=f,
                       args=args,
                       vars=vars,
                       anchor=anchor,
                       extension=extension,
                       env=env)
        else:
            return False

    # -------------------------------------------------------------------------
    def fail(self):
        """ Action upon insufficient permissions """

        if self.format == "html":
            # HTML interactive request => flash message + redirect
            if self.auth.s3_logged_in():
                current.session.error = self.INSUFFICIENT_PRIVILEGES
                redirect(self.homepage)
            else:
                current.session.error = self.AUTHENTICATION_REQUIRED
                redirect(self.loginpage)
        else:
            # Non-HTML request => raise HTTP status
            if self.auth.s3_logged_in():
                raise HTTP(403, body=self.INSUFFICIENT_PRIVILEGES)

            # RFC1945/2617 compliance:
            # Must raise an HTTP Auth challenge with status 401
            headers = {"WWW-Authenticate":
                       "Basic realm=\"%s\"" % current.request.application,
                       }

            # Add Master Key Auth token if enabled + requested
            if current.deployment_settings.get_auth_masterkey():
                from s3.s3masterkey import S3MasterKey
                S3MasterKey.challenge(headers)

            raise HTTP(401, body=self.AUTHENTICATION_REQUIRED, **headers)

    # -------------------------------------------------------------------------
    # ACL Lookup
    # -------------------------------------------------------------------------
    def applicable_acls(self, racl,
                        realms=None,
                        delegations=None,
                        c=None,
                        f=None,
                        t=None,
                        entity=None):
        """
            Find all applicable ACLs for the specified situation for
            the specified realms and delegations

            @param racl: the required ACL
            @param realms: the realms
            @param delegations: the delegations
            @param c: the controller name, falls back to current request
            @param f: the function name, falls back to current request
            @param t: the tablename
            @param entity: the realm entity

            @return: None for no ACLs defined (allow),
                      [] for no ACLs applicable (deny),
                      or list of applicable ACLs
        """

        if not self.use_cacls:
            # We do not use ACLs at all (allow all)
            return None
        else:
            acls = {}

        # Get all roles
        if realms:
            roles = set(realms.keys())
            if delegations:
                for role in delegations:
                    roles.add(role)
        else:
            # No roles available (deny all)
            return acls

        db = current.db
        table = self.table

        c = c or self.controller
        f = f or self.function
        page_restricted = self.page_restricted(c=c, f=f)

        # Base query
        query = (table.deleted != True) & \
                (table.group_id.belongs(roles))

        # Page ACLs
        if page_restricted:
            q = (table.function == None)
            if f and self.use_facls:
                q |= (table.function == f)
            q &= (table.controller == c)
        else:
            q = None

        # Table ACLs
        if t and self.use_tacls:
            # Be sure to use the original table name
            if hasattr(t, "_tablename"):
                t = original_tablename(t)
            tq = (table.controller == None) & \
                 (table.function == None) & \
                 (table.tablename == t)
            q = tq if q is None else q | tq
            table_restricted = self.table_restricted(t)
        else:
            table_restricted = False

        # Retrieve the ACLs
        if q is not None:
            query &= q
            rows = db(query).select(table.group_id,
                                    table.controller,
                                    table.function,
                                    table.tablename,
                                    table.unrestricted,
                                    table.entity,
                                    table.uacl,
                                    table.oacl,
                                    cacheable=True)
        else:
            rows = []

        # Cascade ACLs
        ANY = "ANY"

        ALL = (self.ALL, self.ALL)
        NONE = (self.NONE, self.NONE)

        use_facls = self.use_facls
        def rule_type(r):
            if r.controller is not None:
                if r.function is None:
                    return "c"
                elif use_facls:
                    return "f"
            elif r.tablename is not None:
                return "t"
            return None

        most_permissive = lambda x, y: (x[0] | y[0], x[1] | y[1])
        most_restrictive = lambda x, y: (x[0] & y[0], x[1] & y[1])

        # Realms
        delegation_rows = []
        append_delegation = delegation_rows.append

        use_realms = self.entity_realm
        for row in rows:

            # Get the assigning entities
            group_id = row.group_id
            if group_id in delegations:
                append_delegation(row)
            if group_id not in realms:
                continue
            rtype = rule_type(row)
            if rtype is None:
                continue

            if use_realms:
                if row.unrestricted:
                    entities = [ANY]
                elif row.entity is not None:
                    entities = [row.entity]
                else:
                    entities = realms[group_id]
                if entities is None:
                    entities = [ANY]
            else:
                entities = [ANY]

            # Merge the ACL
            acl = (row["uacl"], row["oacl"])
            for e in entities:
                if e in acls:
                    eacls = acls[e]
                    if rtype in eacls:
                        eacls[rtype] = most_permissive(eacls[rtype], acl)
                    else:
                        eacls[rtype] = acl
                else:
                    acls[e] = {rtype: acl}

        if ANY in acls:
            default = dict(acls[ANY])
        else:
            default = None

        # Delegations
        if self.delegations:
            for row in delegation_rows:

                # Get the rule type
                rtype = rule_type(row)
                if rtype is None:
                    continue

                # Get the delegation realms
                group_id = row.group_id
                if group_id not in delegations:
                    continue
                else:
                    drealms = delegations[group_id]

                acl = (row["uacl"], row["oacl"])

                # Resolve the delegation realms
                # @todo: optimize
                for receiver in drealms:
                    drealm = drealms[receiver]

                    # Skip irrelevant delegations
                    if entity:
                        if entity not in drealm:
                            continue
                        else:
                            drealm = [entity]

                    # What ACLs do we have for the receiver?
                    if receiver in acls:
                        dacls = dict(acls[receiver])
                    elif default is not None:
                        dacls = default
                    else:
                        continue

                    # Filter the delegated ACLs
                    if rtype in dacls:
                        dacls[rtype] = most_restrictive(dacls[rtype], acl)
                    else:
                        dacls[rtype] = acl

                    # Add/extend the new realms (e=entity, t=rule type)
                    # @todo: optimize
                    for e in drealm:
                        if e in acls:
                            for acltype in ("c", "f", "t"):
                                if acltype in acls[e]:
                                    if acltype in dacls:
                                        dacls[acltype] = most_restrictive(
                                                            dacls[acltype],
                                                            acls[e][acltype],
                                                            )
                                    else:
                                        dacls[acltype] = acls[e][acltype]
                        acls[e] = dacls

        acl = acls.get(ANY, {})

        # Default page ACL
        if "c" in acl:
            default_page_acl = acl["f"] if "f" in acl else acl["c"]
        elif page_restricted:
            default_page_acl = NONE
        else:
            default_page_acl = ALL

        # Default table ACL
        if "t" in acl:
            # If we have a table rule, apply it
            default_table_acl = acl["t"]
        elif self.use_tacls and table_restricted:
            # A restricted table is not accessible on any page without an
            # explicit table rule (once explicit => always explicit!)
            default_table_acl = NONE
        else:
            # An unrestricted table is accessible under the page rule
            default_table_acl = default_page_acl if page_restricted else ALL

        # No ACLs inevitably causes a "no applicable ACLs" permission failure,
        # so for unrestricted pages or tables, we must create a default ACL
        # here in order to have the default apply:
        if not acls:
            if t and self.use_tacls:
                if not table_restricted:
                    acls[ANY] = {"t": default_table_acl}
            elif not page_restricted:
                acls[ANY] = {"c": default_page_acl}

        # Order by precedence
        s3db = current.s3db
        ancestors = set()
        if entity and self.entity_hierarchy and \
           s3db.pr_instance_type(entity) == "pr_person":
            # If the realm entity is a person, then we apply the ACLs
            # for the immediate OU ancestors, for two reasons:
            # a) it is not possible to assign roles for personal realms anyway
            # b) looking up OU ancestors of a person (=a few) is much more
            #    efficient than looking up pr_person OU descendants of the
            #    role realm (=could be tens or hundreds of thousands)
            ancestors = set(s3db.pr_realm(entity))

        result = {}
        for e in acls:
            # Skip irrelevant ACLs
            if entity and e != entity and e != ANY:
                if e in ancestors:
                    key = entity
                else:
                    continue
            else:
                key = e

            acl = acls[e]

            # Get the page ACL
            if "f" in acl:
                page_acl = most_permissive(default_page_acl, acl["f"])
            elif "c" in acl:
                page_acl = most_permissive(default_page_acl, acl["c"])
            elif page_restricted:
                page_acl = default_page_acl
            else:
                page_acl = ALL

            # Get the table ACL
            if "t" in acl:
                table_acl = most_permissive(default_table_acl, acl["t"])
            elif table_restricted:
                table_acl = default_table_acl
            else:
                table_acl = ALL

            # Merge
            acl = most_restrictive(page_acl, table_acl)

            # Include ACL if relevant
            if acl[0] & racl == racl or acl[1] & racl == racl:
                result[key] = acl

        #for pe in result:
        #    sys.stderr.write("ACL for PE %s: %04X %04X\n" %
        #                        (pe, result[pe][0], result[pe][1]))

        return result

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    def page_restricted(self, c=None, f=None):
        """
            Checks whether a page is restricted (=whether ACLs
            are to be applied)

            @param c: controller name
            @param f: function name
        """


        page = "%s/%s" % (c, f)
        if page in self.unrestricted_pages:
            restricted = False
        elif c != "default" or f not in ("tables", "table"):
            modules = current.deployment_settings.modules
            restricted = c in modules and modules[c].restricted
        else:
            restricted = True

        return restricted

    # -------------------------------------------------------------------------
    def table_restricted(self, t=None):
        """
            Check whether access to a table is restricted

            @param t: the table name or Table
        """

        s3 = current.response.s3

        if not "restricted_tables" in s3:
            table = self.table
            query = (table.deleted != True) & \
                    (table.controller == None) & \
                    (table.function == None)
            rows = current.db(query).select(table.tablename,
                                            groupby=table.tablename)
            s3.restricted_tables = [row.tablename for row in rows]

        return str(t) in s3.restricted_tables

    # -------------------------------------------------------------------------
    def hidden_modules(self):
        """ List of modules to hide from the main menu """

        hidden_modules = []
        if self.use_cacls:
            sr = self.auth.get_system_roles()
            modules = current.deployment_settings.modules
            restricted_modules = [m for m in modules
                                    if modules[m].restricted]
            roles = []
            if current.session.s3 is not None:
                roles = current.session.s3.roles or []
            if sr.ADMIN in roles:   # or sr.EDITOR in roles:
                return []
            if not roles:
                hidden_modules = restricted_modules
            else:
                t = self.table
                query = (t.deleted != True) & \
                        (t.controller.belongs(restricted_modules)) & \
                        (t.tablename == None)
                if roles:
                    query = query & (t.group_id.belongs(roles))
                else:
                    query = query & (t.group_id == None)
                rows = current.db(query).select()
                acls = dict()
                for acl in rows:
                    if acl.controller not in acls:
                        acls[acl.controller] = self.NONE
                    acls[acl.controller] |= acl.oacl | acl.uacl
                hidden_modules = [m for m in restricted_modules
                                    if m not in acls or not acls[m]]
        return hidden_modules

    # -------------------------------------------------------------------------
    def ownership_required(self, method, table, c=None, f=None):
        """
            Checks whether ownership can be required to access records in
            this table (this may not apply to every record in this table).

            @param method: the method as string or a list of methods (AND)
            @param table: the database table or table name
            @param c: controller name (falls back to current request)
            @param f: function name (falls back to current request)
        """

        if not self.use_cacls:
            if self.policy in (1, 2):
                return False
            else:
                return True

        if not hasattr(table, "_tablename"):
            tablename = table
            table = current.s3db.table(tablename)
            if not table:
                raise AttributeError("undefined table %s" % tablename)

        # If the table doesn't have any ownership fields, then no
        if "owned_by_user" not in table.fields and \
           "owned_by_group" not in table.fields and \
           "realm_entity" not in table.fields:
            return False

        if not isinstance(method, (list, tuple)):
            method = [method]

        # Auth override, system roles and login
        auth = self.auth
        if self.auth.override or not self.use_cacls:
            return False
        sr = auth.get_system_roles()
        logged_in = auth.s3_logged_in()

        # Required ACL
        racl = self.required_acl(method)

        # Get realms and delegations
        user = auth.user
        if not logged_in:
            realms = Storage({sr.ANONYMOUS:None})
            delegations = Storage()
        else:
            realms = user.realms
            delegations = user.delegations

        # Admin always owns all records
        if sr.ADMIN in realms:
            return False

        # Fall back to current request
        c = c or self.controller
        f = f or self.function

        # Get the applicable ACLs
        acls = self.applicable_acls(racl,
                                    realms=realms,
                                    delegations=delegations,
                                    c=c,
                                    f=f,
                                    t=table)
        acls = [entity for entity in acls if acls[entity][0] & racl == racl]

        # If we have a UACL and it is not limited to any realm, then no
        if "ANY" in acls or acls and "realm_entity" not in table.fields:
            return False

        # In all other cases: yes
        return True

    # -------------------------------------------------------------------------
    def forget(self, table=None, record_id=None):
        """
            Remove any cached permissions for a record. This can be
            necessary in methods which change the status of the record
            (e.g. approval).

            @param table: the table
            @param record_id: the record ID
        """

        if table is None:
            self.permission_cache = {}
            return
        permissions = self.permission_cache
        if not permissions:
            return

        if hasattr(table, "_tablename"):
            tablename = original_tablename(table)
        else:
            tablename = table

        for key in list(permissions.keys()):
            r = key.split("/")
            if len(r) > 1 and r[-2] == tablename:
                if record_id is None or \
                   record_id is not None and r[-1] == str(record_id):
                    del permissions[key]

# =============================================================================
class S3Audit(object):
    """ S3 Audit Trail Writer Class """

    def __init__(self,
                 tablename="s3_audit",
                 migrate=True,
                 fake_migrate=False):
        """
            Constructor

            @param tablename: the name of the audit table
            @param migrate: migration setting

            @note: this defines the audit table
        """

        settings = current.deployment_settings
        audit_read = settings.get_security_audit_read()
        audit_write = settings.get_security_audit_write()
        if not audit_read and not audit_write:
            # Auditing is Disabled
            self.table = None
            return

        db = current.db
        if tablename not in db:
            db.define_table(tablename,
                            Field("timestmp", "datetime",
                                  represent = S3DateTime.datetime_represent,
                                  ),
                            Field("user_id", db.auth_user),
                            Field("method"),
                            Field("tablename"),
                            Field("record_id", "integer"),
                            Field("representation"),
                            # List of Key:Values
                            Field("old_value", "text"),
                            # List of Key:Values
                            Field("new_value", "text"),
                            Field("repository_id", "integer"),
                            migrate=migrate,
                            fake_migrate=fake_migrate,
                            )
        self.table = db[tablename]

        user = current.auth.user
        if user:
            self.user_id = user.id
        else:
            self.user_id = None

    # -------------------------------------------------------------------------
    def __call__(self, method, prefix, name,
                 form=None,
                 record=None,
                 representation="unknown"):
        """
            Audit

            @param method: Method to log, one of
                "create", "update", "read", "list" or "delete"
            @param prefix: the module prefix of the resource
            @param name: the name of the resource (without prefix)
            @param form: the form
            @param record: the record ID
            @param representation: the representation format
        """

        table = self.table
        if not table:
            # Don't Audit
            return True

        #if DEBUG:
        #    _debug("Audit %s: %s_%s record=%s representation=%s",
        #           method,
        #           prefix,
        #           name,
        #           record,
        #           representation,
        #           )

        if method in ("list", "read"):
            audit = current.deployment_settings.get_security_audit_read()
        elif method in ("create", "update", "delete"):
            audit = current.deployment_settings.get_security_audit_write()
        else:
            # Don't Audit
            return True

        if not audit:
            # Don't Audit
            return True

        tablename = "%s_%s" % (prefix, name)

        if record:
            if isinstance(record, Row):
                record = record.get("id", None)
                if not record:
                    return True
            try:
                record = int(record)
            except ValueError:
                record = None
        elif form:
            try:
                record = form.vars["id"]
            except:
                try:
                    record = form["id"]
                except:
                    record = None
            if record:
                try:
                    record = int(record)
                except ValueError:
                    record = None
        else:
            record = None

        if callable(audit):
            audit = audit(method, tablename, form, record, representation)
            if not audit:
                # Don't Audit
                return True

        if method in ("list", "read"):
            table.insert(timestmp = datetime.datetime.utcnow(),
                         user_id = self.user_id,
                         method = method,
                         tablename = tablename,
                         record_id = record,
                         representation = representation,
                         repository_id = current.response.s3.repository_id,
                         )

        elif method == "create":
            if form:
                form_vars = form.vars
                if not record:
                    record = form_vars["id"]
                new_value = ["%s:%s" % (var, str(form_vars[var]))
                             for var in form_vars if form_vars[var]]
            else:
                new_value = []
            table.insert(timestmp = datetime.datetime.utcnow(),
                         user_id = self.user_id,
                         method = method,
                         tablename = tablename,
                         record_id = record,
                         representation = representation,
                         new_value = new_value,
                         repository_id = current.response.s3.repository_id,
                         )

        elif method == "update":
            if form:
                rvars = form.record
                if rvars:
                    old_value = ["%s:%s" % (var, str(rvars[var]))
                                 for var in rvars]
                else:
                    old_value = []
                fvars = form.vars
                if not record:
                    record = fvars["id"]
                new_value = ["%s:%s" % (var, str(fvars[var]))
                             for var in fvars]
            else:
                new_value = []
                old_value = []
            table.insert(timestmp = datetime.datetime.utcnow(),
                         user_id = self.user_id,
                         method = method,
                         tablename = tablename,
                         record_id = record,
                         representation = representation,
                         old_value = old_value,
                         new_value = new_value,
                         repository_id = current.response.s3.repository_id,
                         )

        elif method == "delete":
            db = current.db
            query = (db[tablename].id == record)
            row = db(query).select(limitby=(0, 1)).first()
            old_value = []
            if row:
                old_value = ["%s:%s" % (field, row[field])
                             for field in row]
            table.insert(timestmp = datetime.datetime.utcnow(),
                         user_id = self.user_id,
                         method = method,
                         tablename = tablename,
                         record_id = record,
                         representation = representation,
                         old_value = old_value,
                         repository_id = current.response.s3.repository_id,
                         )

        return True

    # -------------------------------------------------------------------------
    def represent(self, records):
        """
            Provide a Human-readable representation of Audit records
            - currently unused

            @param record: the record IDs
        """

        table = self.table
        # Retrieve the records
        if isinstance(records, int):
            limit = 1
            query = (table.id == records)
        else:
            limit = len(records)
            query = (table.id.belongs(records))
        records = current.db(query).select(table.tablename,
                                           table.method,
                                           table.user_id,
                                           table.old_value,
                                           table.new_value,
                                           limitby=(0, limit)
                                           )

        # Convert to Human-readable form
        s3db = current.s3db
        output = []
        oappend = output.append
        for record in records:
            table = s3db[record.tablename]
            method = record.method
            if method == "create":
                new_value = record.new_value
                if not new_value:
                    continue
                diff = []
                dappend = diff.append
                for v in new_value:
                    fieldname, value = v.split(":", 1)
                    represent = table[fieldname].represent
                    if represent:
                        value = represent(value)
                    label = table[fieldname].label or fieldname
                    dappend("%s is %s" % (label, value))

            elif method == "update":
                old_values = record.old_value
                new_values = record.new_value
                if not new_value:
                    continue
                changed = {}
                for v in new_values:
                    fieldname, new_value = v.split(":", 1)
                    old_value = old_values.get(fieldname, None)
                    if new_value != old_value:
                        ftype = table[fieldname].type
                        if ftype == "integer" or \
                           ftype.startswith("reference"):
                            if new_value:
                                new_value = int(new_value)
                            if new_value == old_value:
                                continue
                        represent = table[fieldname].represent
                        if represent:
                            new_value = represent(new_value)
                        label = table[fieldname].label or fieldname
                        if old_value:
                            if represent:
                                old_value = represent(old_value)
                            changed[fieldname] = "%s changed from %s to %s" % \
                                (label, old_value, new_value)
                        else:
                            changed[fieldname] = "%s changed to %s" % \
                                (label, new_value)
                diff = []
                dappend = diff.append
                for fieldname in changed:
                    dappend(changed[fieldname])

            elif method == "delete":
                old_value = record.old_value
                if not old_value:
                    continue
                diff = []
                dappend = diff.append
                for v in old_value:
                    fieldname, value = v.split(":", 1)
                    represent = table[fieldname].represent
                    if represent:
                        value = represent(value)
                    label = table[fieldname].label or fieldname
                    dappend("%s was %s" % (label, value))

            oappend("\n".join(diff))

        return output

# =============================================================================
class S3GroupedOptionsWidget(OptionsWidget):
    """
        A custom Field widget to create a SELECT element with grouped options.
    """

    @classmethod
    def widget(cls, field, value, options, **attributes):
        """
            Generates a SELECT tag, with OPTIONs grouped by OPTGROUPs

            @param field: the field needing the widget
            @param value: value
            @param options: list
            @param options: a list of tuples, each either (label, value) or (label, {options})
            @param attributes: any other attributes to be applied

            @return: SELECT object
        """

        default = dict(value=value)
        attr = cls._attributes(field, default, **attributes)
        select_items = []

        for option in options:
            if isinstance(option[1], dict):
                items = [(v, k) for k, v in option[1].items()]
                if not items:
                    continue
                items.sort()
                opts = [OPTION(v, _value=k) for v, k in items]
                select_items.append(OPTGROUP(*opts, _label=option[0]))
            else:
                select_items.append(OPTION(option[1], _label=option[0]))

        return SELECT(select_items, **attr)

# =============================================================================
class S3EntityRoleManager(S3Method):
    """ Entity/User role manager """

    ENTITY_TYPES = ["org_organisation",
                    "org_office",
                    "inv_warehouse",
                    "hms_hospital",
                    #"po_area",
                    "pr_group",
                    ]

    def __init__(self, *args, **kwargs):
        """ Constructor """

        super(S3EntityRoleManager, self).__init__(*args, **kwargs)

        # Dictionary of pentities this admin can manage
        self.realm = self.get_realm()

        # The list of user accounts linked to pentities in this realm
        self.realm_users = current.s3db.pr_realm_users(self.realm)

        # Create the dictionary of roles
        self.roles = {}

        self.modules = self.get_modules()
        self.acls = self.get_access_levels()

        for module_uid, module_label in self.modules.items():
            for acl_uid, acl_label in self.acls.items():
                role_uid = "%s_%s" % (module_uid, acl_uid)

                self.roles[role_uid] = {
                    "module": {
                        "uid": module_uid,
                        "label": module_label
                    },
                    "acl": {
                        "uid": acl_uid,
                        "label": acl_label
                    }
                }

    # -------------------------------------------------------------------------
    @classmethod
    def set_method(cls, r, entity=None, record_id=None):
        """
            Plug-in OrgAdmin Role Managers when appropriate

            @param r: the S3Request
            @param entity: override target entity (default: r.tablename)
            @param record_id: specify target record ID (only for OU's)
        """

        s3db = current.s3db
        auth = current.auth

        if not current.deployment_settings.get_auth_entity_role_manager() or \
           auth.user is None:
            return False

        sr = auth.get_system_roles()
        realms = auth.user.realms or Storage()

        ORG_ADMIN = sr.ORG_ADMIN

        admin = sr.ADMIN in realms
        org_admin = ORG_ADMIN in realms

        if admin or org_admin:

            if entity is not None:
                tablename = entity
                record = None
            else:
                tablename = r.tablename
                record = r.record

            all_entities = admin or org_admin and realms[ORG_ADMIN] is None

            if not all_entities and tablename in cls.ENTITY_TYPES:

                if not record and record_id is not None:

                    # Try to load the record and check pe_id
                    table = s3db.table(tablename)
                    if table and "pe_id" in table.fields:
                        record = current.db(table._id==record_id).select(table.pe_id,
                                                                         limitby = (0, 1)).first()

                if record and record.pe_id not in realms[ORG_ADMIN]:
                    return False

            if entity is not None:
                # Configure as custom method for this resource
                prefix, name = tablename.split("_", 1)
                s3db.set_method(prefix, name, method="roles", action=cls)

            elif tablename in cls.ENTITY_TYPES:
                # Configure as method handler for this request
                r.set_handler("roles", cls)

            else:
                # Unsupported entity
                return False

        return True

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
        """

        if self.method == "roles" and \
           (r.tablename in self.ENTITY_TYPES + ["pr_person"]):
            context = self.get_context_data(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        # Set the default view
        current.response.view = "admin/manage_roles.html"

        return context

    # -------------------------------------------------------------------------
    def get_context_data(self, r, **attr):
        """
            @todo: description?

            @return: dictionary for the view

            {
                # All the possible roles
                "roles": {
                    "staff_reader": {
                        "module": {
                            "uid": "staff",
                            "label": "Staff"
                        },
                        ...
                    },
                    ...
                },

                # The roles currently assigned to users for entit(y/ies)
                "assigned_roles": {
                    "1": [
                        "staff_reader",
                        "project_editor",
                        ...
                    ],
                    ...
                },

                "pagination_list": [
                    (
                        "User One",
                        "1"
                    ),
                    ...
                ],

                # The object (user/entity) we are assigning roles for
                "foreign_object": {
                    "id": "1",
                    "name": "User One"
                }
                or
                "foreign_object": {
                    "id": "70",
                    "name": "Organisation Seventy"
                }
            }
        """

        T = current.T

        # organisation or site entity
        self.entity = self.get_entity()

        # user account to assigned roles to
        self.user = self.get_user()

        # roles already assigned to a user or users
        self.assigned_roles = self.get_assigned_roles()

        # The foreign object is the one selected in the role form
        # for a person this is the entity
        # for an entity (organisation or office) this is a user
        self.foreign_object = self.get_foreign_object()

        form = self.get_form()

        # if we are editing roles, set those assigned roles as initial values
        # for the form
        form.vars.update(self.get_form_vars())

        if form.accepts(r.post_vars, current.session):
            before = self.assigned_roles[self.foreign_object["id"]] if self.foreign_object else []
            after = ["%s_%s" % (mod_uid, acl_uid) for mod_uid, acl_uid
                                                  in form.vars.items()
                                                  if mod_uid in self.modules.keys()
                                                  and acl_uid in self.acls.keys()]

            # either both values will have been specified or one will
            # be supplied by the form (for roles on new objects)
            user_id = self.user["id"] if self.user else form.vars.foreign_object
            entity_id = self.entity["id"] if self.entity else form.vars.foreign_object

            self.update_roles(user_id, entity_id, before, after)
            current.session.confirmation = T("Roles updated")
            redirect(r.url(vars={}))

        context = {"roles": self.roles,
                   "foreign_object": self.foreign_object,
                   "form": form,
                   "title": T("Roles"),
                   }

        if not self.foreign_object:
            # how many assigned roles to show per page
            pagination_size = int(r.get_vars.get("page_size", 4))
            # what page of assigned roles to view
            pagination_offset = int(r.get_vars.get("page_offset", 0))
            # the number of pages of assigned roles
            import math
            pagination_pages = int(math.ceil(len(self.assigned_roles) / float(pagination_size)))
            # the list of objects to show on this page sorted by name
            pagination_list = [(self.objects[gid], gid) for gid in self.assigned_roles]
            pagination_list = sorted(pagination_list)[pagination_offset * pagination_size:pagination_offset * pagination_size + pagination_size]

            context.update({"assigned_roles": self.assigned_roles,
                            "pagination_size": pagination_size,
                            "pagination_offset": pagination_offset,
                            "pagination_list": pagination_list,
                            "pagination_pages": pagination_pages,
                            })

        return context

    # -------------------------------------------------------------------------
    def get_realm(self):
        """
            Returns the realm (list of pe_ids) that this user can manage
            or raises a permission error if the user is not logged in
        """

        auth = current.auth
        system_roles = auth.get_system_roles()
        ORG_ADMIN = system_roles.ORG_ADMIN
        ADMIN = system_roles.ADMIN

        if auth.user:
            realms = auth.user.realms
        else:
            # User is not logged in
            auth.permission.fail()

        # Get the realm from the current realms
        if ADMIN in realms:
            realm = realms[ADMIN]
        elif ORG_ADMIN in realms:
            realm = realms[ORG_ADMIN]
        else:
            # raise an error here - user is not permitted
            # to access the role matrix
            auth.permission.fail()

        return realm

    # -------------------------------------------------------------------------
    def get_modules(self):
        """
            This returns an OrderedDict of modules with their uid as the key,
            e.g., {hrm: "Human Resources",}

            @return: OrderedDict
        """
        return current.deployment_settings.get_auth_role_modules()

    # -------------------------------------------------------------------------
    def get_access_levels(self):
        """
            This returns an OrderedDict of access levels and their uid as
            the key, e.g., {reader: "Reader",}

            @return: OrderedDict
        """
        return current.deployment_settings.get_auth_access_levels()

    # -------------------------------------------------------------------------
    def get_assigned_roles(self, entity_id=None, user_id=None):
        """
            If an entity ID is provided, the dict will be the users
            with roles assigned to that entity. The key will be the user IDs.

            If a user ID is provided, the dict will be the entities the
            user has roles for. The key will be the entity pe_ids.

            If both an entity and user ID is provided, the dict will be
            the roles assigned to that user for that entity. The key will be
            the user ID.

            @type entity_id: int
            @param entity_id: the pe_id of the entity
            @type user_id: int
            @param user_id: id of the user account

            @return: dict
            {
                1: [
                    "staff_reader",
                    "project_reader",
                    ...
                ]
                2: [
                    ...
                ],
                ...
            }
        """

        if not entity_id and not user_id:
            raise RuntimeError("Not enough arguments")

        mtable = current.auth.settings.table_membership
        gtable = current.auth.settings.table_group
        utable = current.auth.settings.table_user

        query = (mtable.deleted != True) & \
                (gtable.deleted != True) & \
                (gtable.id == mtable.group_id) & \
                (utable.deleted != True) & \
                (utable.id == mtable.user_id)

        if user_id:
            field = mtable.pe_id
            query &= (mtable.user_id == user_id) & \
                     (mtable.pe_id != None)

        if entity_id:
            field = utable.id
            query &= (mtable.pe_id == entity_id)

        rows = current.db(query).select(utable.id,
                                        gtable.uuid,
                                        mtable.pe_id)

        assigned_roles = OrderedDict()
        roles = self.roles
        for row in rows:
            object_id = row[field]
            role_uid = row[gtable.uuid]

            if role_uid in roles:
                if object_id not in assigned_roles:
                    assigned_roles[object_id] = []
                assigned_roles[object_id].append(role_uid)

        return assigned_roles

    # -------------------------------------------------------------------------
    def get_form(self):
        """
            Contructs the role form

            @return: SQLFORM
        """

        fields = self.get_form_fields()
        form = SQLFORM.factory(*fields,
                               table_name="roles",
                               _id="role-form",
                               _action="",
                               _method="POST")
        return form

    # -------------------------------------------------------------------------
    def get_form_fields(self):
        """
            @todo: description?

            @return: list of Fields
        """

        fields = []
        requires = IS_EMPTY_OR(IS_IN_SET(self.acls))
        for module_uid, module_label in self.modules.items():
            field = Field(module_uid,
                          label=module_label,
                          requires=requires)
            fields.append(field)
        return fields

    # -------------------------------------------------------------------------
    def get_form_vars(self):
        """
            Get the roles currently assigned for a user/entity and put it
            into a Storage object for the form

            @return: Storage() to pre-populate the role form
        """

        form_vars = Storage()

        fo = self.foreign_object
        roles = self.roles
        if fo and fo["id"] in self.assigned_roles:
            for role in self.assigned_roles[fo["id"]]:
                mod_uid = roles[role]["module"]["uid"]
                acl_uid = roles[role]["acl"]["uid"]
                form_vars[mod_uid] = acl_uid

        return form_vars

    # -------------------------------------------------------------------------
    def update_roles(self, user_id, entity_id, before, after):
        """
            Update the users roles on entity based on the selected roles
            in before and after

            @param user_id: id (pk) of the user account to modify
            @param entity_id: id of the pentity to modify roles for
            @param before: list of role_uids (current values for the user)
            @param after: list of role_uids (new values from the admin)
        """

        auth = current.auth
        assign_role = auth.s3_assign_role
        withdraw_role = auth.s3_withdraw_role

        for role_uid in before:
            # If role_uid is not in after,
            # the access level has changed.
            if role_uid not in after:
                withdraw_role(user_id, role_uid, entity_id)

        for role_uid in after:
            # If the role_uid is not in before,
            # the access level has changed
            if role_uid != "None" and role_uid not in before:
                assign_role(user_id, role_uid, entity_id)

# =============================================================================
class S3OrgRoleManager(S3EntityRoleManager):

    def __init__(self, *args, **kwargs):
        """
            Constructor
        """

        super(S3OrgRoleManager, self).__init__(*args, **kwargs)

        # dictionary {id: name, ...} of user accounts
        self.objects = current.s3db.pr_realm_users(None)

    # -------------------------------------------------------------------------
    def get_context_data(self, r, **attr):
        """
            Override to set the context from the perspective of an entity

            @return: dictionary for view
        """

        context = super(S3OrgRoleManager, self).get_context_data(r, **attr)
        context["foreign_object_label"] = current.T("Users")
        return context

    # -------------------------------------------------------------------------
    def get_entity(self):
        """
            We are on an entity (org/office) so we can fetch the entity
            details from the request record.

            @return: dictionary containing the ID and name of the entity
        """

        entity_id = int(self.request.record.pe_id)

        entity = {"id": entity_id,
                  "name": current.s3db.pr_get_entities(
                                          pe_ids = [entity_id],
                                          types = self.ENTITY_TYPES,
                                          )[entity_id],
                  }

        return entity

    # -------------------------------------------------------------------------
    def get_user(self):
        """
            The edit parameter

            @return: dictionary containing the ID and username/email of
                     the user account.
        """

        user = self.request.get_vars.get("edit", None)
        if user:
            user = {"id": int(user),
                    "name": self.objects.get(int(user), None),
                    }
        return user

    # -------------------------------------------------------------------------
    def get_foreign_object(self):
        """
            We are on an entity so our target is a user account.

            @return: dictionary with ID and username/email of user account
        """

        return self.user

    # -------------------------------------------------------------------------
    def get_assigned_roles(self, entity_id=None, user_id=None):
        """
            Override to get assigned roles for this entity

            @return: dictionary with user IDs as the keys.
        """

        assigned_roles = super(S3OrgRoleManager, self).get_assigned_roles

        return assigned_roles(entity_id=self.entity["id"])

    # -------------------------------------------------------------------------
    def get_form_fields(self):
        """
            Override the standard method so we can add the user-selection
            field to the list.

            @return: list of Fields
        """

        T = current.T

        fields = super(S3OrgRoleManager, self).get_form_fields()

        if not self.user:
            assigned_roles = self.assigned_roles

            realm_users = {k: v for k, v in self.realm_users.items()
                                if k not in assigned_roles}

            other_users = {k: v for k, v in self.objects.items()
                                if k not in assigned_roles and \
                                   k not in self.realm_users}

            options = [("", ""),
                       (T("Users in my Organizations"), realm_users),
                       (T("Other Users"), other_users),
                       ]

            widget = lambda field, value: \
                            S3GroupedOptionsWidget.widget(field,
                                                          value,
                                                          options=options,
                                                          )

            object_field = Field("foreign_object",
                                 label = T("User"),
                                 requires = IS_IN_SET(self.objects),
                                 widget = widget,
                                 )
            fields.insert(0, object_field)

        return fields

# =============================================================================
class S3PersonRoleManager(S3EntityRoleManager):
    """ Role Manager for Person Records """

    def __init__(self, *args, **kwargs):
        """ Constructor """

        super(S3PersonRoleManager, self).__init__(*args, **kwargs)

        # dictionary {id: name, ...} of pentities
        self.objects = current.s3db.pr_get_entities(types=self.ENTITY_TYPES)

    # -------------------------------------------------------------------------
    def get_context_data(self, r, **attr):
        """
            Override to set the context from the perspective of a person

            @return: dictionary for view
        """

        context = super(S3PersonRoleManager, self).get_context_data(r, **attr)
        context["foreign_object_label"] = current.T("Organizations / Teams / Facilities")
        return context

    # -------------------------------------------------------------------------
    def get_entity(self):
        """
            An entity needs to be specified with the "edit" query string
            parameter.

            @return: dictionary with pe_id and name of the org/office.
        """

        entity = self.request.get_vars.get("edit", None)
        if entity:
            entity = {"id": int(entity),
                      "name": self.objects.get(int(entity), None),
                      }
        return entity

    # -------------------------------------------------------------------------
    def get_user(self):
        """
            We are on a person record so we need to find the associated user
            account.

            @return: dictionary with ID and username/email of the user account
        """

        settings = current.auth.settings
        utable = settings.table_user
        ptable = current.s3db.pr_person_user

        pe_id = int(self.request.record.pe_id)

        userfield = settings.login_userfield

        query = (ptable.pe_id == pe_id) & \
                (ptable.user_id == utable.id)
        record = current.db(query).select(utable.id,
                                          utable[userfield],
                                          limitby=(0, 1)).first()

        return {"id": record.id,
                "name": record[utable[userfield]],
                } if record else None

    # -------------------------------------------------------------------------
    def get_foreign_object(self):
        """
            We are on a user/person so we want to target an entity (org/office)
        """

        return self.entity

    # -------------------------------------------------------------------------
    def get_assigned_roles(self, entity_id=None, user_id=None):
        """
            @todo: description?

            @return: dictionary of assigned roles with entity pe_id as the keys
        """

        assigned_roles = super(S3PersonRoleManager, self).get_assigned_roles

        return assigned_roles(user_id=self.user["id"])

    # -------------------------------------------------------------------------
    def get_form_fields(self):
        """
            Return a list of fields, including a field for selecting
            a realm entity (such as an organisation or office).

            @return: list of Fields
        """

        s3db = current.s3db
        fields = super(S3PersonRoleManager, self).get_form_fields()

        if not self.entity:
            options = s3db.pr_get_entities(pe_ids=self.realm,
                                           types=self.ENTITY_TYPES,
                                           group=True)

            nice_name = s3db.table("pr_pentity").instance_type.represent

            # filter out options that already have roles assigned
            filtered_options = []
            for entity_type, entities in options.items():
                entities = Storage([(entity_id, entity_name)
                                    for entity_id, entity_name
                                        in entities.items()
                                    if entity_id not in self.assigned_roles])
                filtered_options.append((nice_name(entity_type), entities))

            widget = lambda field, value: \
                     S3GroupedOptionsWidget.widget(field,
                                                   value,
                                                   options=filtered_options,
                                                   )

            object_field = Field("foreign_object",
                                 label = current.T("Entity"),
                                 requires = IS_IN_SET(self.objects),
                                 widget = widget,
                                 )
            fields.insert(0, object_field)

        return fields

# END =========================================================================
