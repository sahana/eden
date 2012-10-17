# -*- coding: utf-8 -*-

""" Authentication, Authorization, Accouting

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2012 Sahana Software Foundation
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

__all__ = ["AuthS3",
           "S3Permission",
           "S3Audit",
           "S3RoleManager",
           "S3OrgRoleManager",
           "S3PersonRoleManager",
           ]

import datetime
import re
from uuid import uuid4

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.dal import Row, Rows, Query, Set, Table, Expression
from gluon.storage import Storage, Messages
from gluon.sqlhtml import OptionsWidget
from gluon.tools import Auth, callback, addrow
from gluon.utils import web2py_uuid

from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3fields import s3_uid, s3_timestamp, s3_deletion_status, s3_comments
from s3rest import S3Method
from s3utils import s3_mark_required
from s3error import S3PermissionError

DEFAULT = lambda: None
table_field = re.compile("[\w_]+\.[\w_]+")

DEBUG = False
if DEBUG:
    import sys
    print >> sys.stderr, "S3AAA: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

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
            - verify_email
            - profile
            - has_membership
            - requires_membership

        - S3 extension for user registration:
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
            - s3_retract_role
            - s3_has_role
            - s3_group_members

        - S3 ACL management:
            - s3_update_acls
            - s3_update_acl

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
                              ORG_ADMIN = "ORG_ADMIN")

    def __init__(self):

        """ Initialise parent class & make any necessary modifications """

        Auth.__init__(self, current.db)

        deployment_settings = current.deployment_settings
        system_name = deployment_settings.get_system_name()

        self.settings.lock_keys = False
        self.settings.username_field = False
        self.settings.lock_keys = True

        self.messages.lock_keys = False

        # @ToDo Move these to deployment_settings
        self.messages.email_approver_failed = "Failed to send mail to Approver - see if you can notify them manually!"
        self.messages.email_verification_failed = "Unable to send verification email - either your email is invalid or our email server is down"
        self.messages.email_sent = "Verification Email sent - please check your email to validate. If you do not receive this email please check you junk email or spam filters"
        self.messages.email_verified = "Email verified - you can now login"
        self.messages.welcome_email_subject = "Welcome to %(system_name)s" % \
            dict(system_name=system_name)
        self.messages.welcome_email = \
"""Welcome to %(system_name)s
 - You can start using %(system_name)s at: %(url)s
 - To edit your profile go to: %(url)s%(profile)s
Thank you
""" % \
            dict(system_name = system_name,
                 url = deployment_settings.get_base_public_url(),
                 profile = URL("default", "user", args=["profile"])
                 )
        self.messages.duplicate_email = "This email address is already in use"
        self.messages.registration_disabled = "Registration Disabled!"
        self.messages.registration_verifying = "You haven't yet Verified your account - please check your email"
        self.messages.label_organisation_id = "Organization"
        self.messages.label_utc_offset = "UTC Offset"
        self.messages.label_image = "Profile Image"
        self.messages.help_utc_offset = "The time difference between UTC and your timezone, specify as +HHMM for eastern or -HHMM for western timezones."
        self.messages.help_mobile_phone = "Entering a phone number is optional, but doing so allows you to subscribe to receive SMS messages."
        self.messages.help_organisation = "Entering an Organization is optional, but doing so directs you to the appropriate approver & means you automatically get the appropriate permissions."
        self.messages.help_image = "You can either use %(gravatar)s or else upload a picture here. The picture will be resized to 50x50."
        #self.messages.logged_in = "Signed In"
        #self.messages.submit_button = "Signed In"
        #self.messages.logged_out = "Signed Out"
        self.messages.lock_keys = True

        # S3Permission
        self.permission = S3Permission(self)

        # Set to True to override any authorization
        self.override = False

        # Site types (for OrgAuth)
        T = current.T
        if deployment_settings.get_ui_camp():
            shelter = T("Camp")
        else:
            shelter = T("Shelter")
        self.org_site_types = Storage(
                                      transport_airport = T("Airport"),
                                      cr_shelter = shelter,
                                      org_facility = T("Facility"),
                                      #org_facility = T("Site"),
                                      org_office = T("Office"),
                                      hms_hospital = T("Hospital"),
                                      #fire_station = T("Fire Station"),
                                      dvi_morgue = T("Morgue"),
                                      transport_seaport = T("Seaport"),
                                      inv_warehouse = T("Warehouse"),
                                      )

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
        label_user_id = messages.label_user_id
        if not utable:
            passfield = settings.password_field
            # @ToDo - remove duplicate of table definitions
            if settings.username_field:
                # with username (not used by default in Sahana)
                utable = define_table(uname,
                    Field("first_name", length=128, notnull=True,
                          default=""),
                    Field("last_name", length=128,
                          default="",
                          label=messages.label_last_name),
                    Field("username", length=128,
                          default="",
                          unique=True),
                    Field(passfield, "password", length=512,
                          requires = [ CRYPT( key = settings.hmac_key,
                                     min_length = settings.password_min_length,
                                     digest_alg = "sha512") ],
                          readable=False, label=messages.label_password),
                    Field("email", length=512,
                          default="",
                          label=messages.label_email),
                    Field("language", length=16,
                          default = deployment_settings.get_L10n_default_language()),
                    Field("utc_offset", length=16,
                          readable=False, writable=False),
                    Field("organisation_id", "integer",
                          readable=False, writable=False,
                          label=messages.label_organisation_id),
                    Field("site_id", "integer",
                          readable=False, writable=False,
                          label=deployment_settings.get_org_site_label()),
                    Field("registration_key", length=512,
                          default="",
                          readable=False, writable=False,
                          label=messages.label_registration_key),
                    Field("reset_password_key", length=512,
                          default="",
                          readable=False, writable=False,
                          label=messages.label_registration_key),
                    Field("deleted", "boolean",
                          default=False,
                          readable=False, writable=False),
                    Field("timestmp", "datetime",
                          default="",
                          readable=False, writable=False),
                    s3_comments(readable=False, writable=False),
                    migrate = migrate,
                    fake_migrate=fake_migrate,
                    *(s3_uid()+s3_timestamp()))
            else:
                # with email-address (Sahana default)
                utable = define_table(uname,
                    Field("first_name", length=128, notnull=True,
                          default="",
                          label=messages.label_first_name,
                          requires = \
                          IS_NOT_EMPTY(error_message=messages.is_empty),
                          ),
                    Field("last_name", length=128,
                          default="",
                          label=messages.label_last_name),
                    Field("email", length=512,
                          default="",
                          label=messages.label_email,
                          unique=True),
                    Field(passfield, "password", length=512,
                          requires = [ CRYPT( key = settings.hmac_key,
                                     min_length = settings.password_min_length,
                                     digest_alg = "sha512") ],
                          readable=False,
                          label=messages.label_password),
                    Field("language", length=16,
                          default = deployment_settings.get_L10n_default_language()),
                    Field("utc_offset", length=16,
                          readable=False, writable=False,
                          label=messages.label_utc_offset),
                    Field("organisation_id", "integer",
                          readable=False, writable=False,
                          label=messages.label_organisation_id),
                    Field("site_id", "integer",
                          readable=False, writable=False,
                          label=deployment_settings.get_org_site_label()),
                    Field("registration_key", length=512,
                          default="",
                          readable=False, writable=False,
                          label=messages.label_registration_key),
                    Field("reset_password_key", length=512,
                          default="",
                          readable=False, writable=False,
                          label=messages.label_registration_key),
                    Field("deleted", "boolean",
                          default=False,
                          readable=False, writable=False),
                    Field("timestmp", "datetime",
                          default="",
                          readable=False, writable=False),
                    s3_comments(readable=False, writable=False),
                    migrate = migrate,
                    fake_migrate=fake_migrate,
                    *(s3_uid()+s3_timestamp()))
            settings.table_user = utable

        # Fields configured in configure_user_fields

        # Temporary User Table
        # for storing User Data that will be used to create records for
        # the user once they are approved
        define_table("auth_user_temp",
                     Field("user_id", utable),
                     Field("mobile"),
                     Field("image", "upload"),
                     *(s3_uid()+s3_timestamp()))

        # Group table (roles)
        gtable = settings.table_group
        gname = settings.table_group_name
        label_group_id = messages.label_group_id
        if not gtable:
            gtable = define_table(gname,
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
                Field("role", length=512, unique=True,
                      default="",
                      requires = IS_NOT_IN_DB(db, "%s.role" % gname),
                      label=messages.label_role),
                Field("description", "text",
                      label=messages.label_description),
                migrate = migrate,
                fake_migrate=fake_migrate,
                *(s3_timestamp()+s3_deletion_status()))
            settings.table_group = gtable

        # Group membership table (user<->role)
        if not settings.table_membership:
            settings.table_membership = define_table(
                settings.table_membership_name,
                Field("user_id", utable,
                      requires = IS_IN_DB(db, "%s.id" % uname,
                                          "%(id)s: %(first_name)s %(last_name)s"),
                      label=label_user_id),
                Field("group_id", gtable,
                      requires = IS_IN_DB(db, "%s.id" % gname,
                                          "%(id)s: %(role)s"),
                      label=label_group_id),
                Field("pe_id", "integer"),
                migrate = migrate,
                fake_migrate=fake_migrate,
                *(s3_uid()+s3_timestamp()+s3_deletion_status()))

        security_policy = deployment_settings.get_security_policy()
        # Define Eden permission table
        self.permission.define_table(migrate=migrate,
                                     fake_migrate=fake_migrate)

        if security_policy not in (1, 2, 3, 4, 5, 6, 7, 8) and \
           not settings.table_permission:
            # Permissions table (group<->permission)
            # NB This Web2Py table is deprecated / replaced in Eden by S3Permission
            settings.table_permission = define_table(
                settings.table_permission_name,
                Field("group_id", gtable,
                      requires = IS_IN_DB(db, "%s.id" % gname,
                                          "%(id)s: %(role)s"),
                      label=label_group_id),
                Field("name", default="default", length=512,
                      requires = IS_NOT_EMPTY(),
                      label=messages.label_name),
                Field("table_name", length=512,
                      # Needs to be defined after all tables created
                      #requires = IS_IN_SET(db.tables),
                      label=messages.label_table_name),
                Field("record_id", "integer",
                      requires = IS_INT_IN_RANGE(0, 10 ** 9),
                      label=messages.label_record_id),
                migrate = migrate,
                fake_migrate=fake_migrate)

        # Event table (auth_event)
        # Records Logins & ?
        # @ToDo: Deprecate? At least make it configurable?
        if not settings.table_event:
            request = current.request
            settings.table_event = define_table(
                settings.table_event_name,
                Field("time_stamp", "datetime",
                      default=request.utcnow,
                      label=messages.label_time_stamp),
                Field("client_ip",
                      default=request.client,
                      label=messages.label_client_ip),
                Field("user_id", utable, default=None,
                      requires = IS_IN_DB(db, "%s.id" % uname,
                                          "%(id)s: %(first_name)s %(last_name)s"),
                      label=label_user_id),
                Field("origin", default="auth", length=512,
                      label=messages.label_origin,
                      requires = IS_NOT_EMPTY()),
                Field("description", "text", default="",
                      label=messages.label_description,
                      requires = IS_NOT_EMPTY()),
                migrate = migrate,
                fake_migrate=fake_migrate,
                *(s3_uid()+s3_timestamp()+s3_deletion_status()))

    # -------------------------------------------------------------------------
    def login_bare(self, username, password):
        """
            Logs user in
                - extended to understand session.s3.roles
        """

        utable = self.settings.table_user
        table_membership = self.settings.table_membership

        if self.settings.login_userfield:
            userfield = self.settings.login_userfield
        elif "username" in utable.fields:
            userfield = "username"
        else:
            userfield = "email"
        passfield = self.settings.password_field
        query = (utable[userfield] == username)
        user = current.db(query).select(limitby=(0, 1)).first()
        password = utable[passfield].validate(password)[0]
        if user:
            user_id = user.id
            if not user.registration_key and user[passfield] == password:
                user = Storage(utable._filter_fields(user, id=True))
                current.session.auth = Storage(user=user,
                                               last_visit=current.request.now,
                                               expiration=self.settings.expiration)
                self.user = user
                self.s3_set_roles()
                return user
        return False

    # -------------------------------------------------------------------------
    def set_cookie(self):
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
              next=DEFAULT,
              onvalidation=DEFAULT,
              onaccept=DEFAULT,
              log=DEFAULT):
        """
            Overrides Web2Py's login() to use custom flash styles & utcnow

            @returns: a login form
        """

        db = current.db
        T = current.T

        utable = self.settings.table_user
        if self.settings.login_userfield:
            username = self.settings.login_userfield
        elif "username" in utable.fields:
            username = "username"
        else:
            username = "email"
        old_requires = utable[username].requires
        utable[username].requires = [IS_NOT_EMPTY(), IS_LOWER()]
        request = current.request
        response = current.response
        session = current.session
        passfield = self.settings.password_field
        try:
            utable[passfield].requires[-1].min_length = 0
        except:
            pass
        if next is DEFAULT:
            next = request.vars._next or self.settings.login_next
        if onvalidation is DEFAULT:
            onvalidation = self.settings.login_onvalidation
        if onaccept is DEFAULT:
            onaccept = self.settings.login_onaccept
        if log is DEFAULT:
            log = self.messages.login_log

        user = None # default

        # Do we use our own login form, or from a central source?
        if self.settings.login_form == self:
            form = SQLFORM(
                utable,
                fields=[username, passfield],
                hidden=dict(_next=request.vars._next),
                showid=self.settings.showid,
                submit_button=T("Login"),
                delete_label=self.messages.delete_label,
                formstyle=self.settings.formstyle,
                separator=self.settings.label_separator
                )
            if self.settings.remember_me_form:
                # Add a new input checkbox "remember me for longer"
                addrow(form, XML("&nbsp;"),
                       DIV(XML("&nbsp;"),
                           INPUT(_type='checkbox',
                                 _class='checkbox',
                                 _id="auth_user_remember",
                                 _name="remember",
                                 ),
                           XML("&nbsp;&nbsp;"),
                           LABEL(self.messages.label_remember_me,
                                 _for="auth_user_remember",
                                 )), "",
                       self.settings.formstyle,
                       "auth_user_remember__row")

            captcha = self.settings.login_captcha or \
                (self.settings.login_captcha!=False and self.settings.captcha)
            if captcha:
                addrow(form, captcha.label, captcha, captcha.comment,
                       self.settings.formstyle,'captcha__row')

            accepted_form = False
            if form.accepts(request.vars, session,
                            formname="login", dbio=False,
                            onvalidation=onvalidation):
                accepted_form = True
                if username == "email":
                    # Check for Domains which can use Google's SMTP server for passwords
                    # @ToDo: an equivalent email_domains for other email providers
                    gmail_domains = current.deployment_settings.get_auth_gmail_domains()
                    if gmail_domains:
                        from gluon.contrib.login_methods.email_auth import email_auth
                        domain = form.vars[username].split("@")[1]
                        if domain in gmail_domains:
                            self.settings.login_methods.append(
                                email_auth("smtp.gmail.com:587", "@%s" % domain))
                # Check for username in db
                query = (utable[username] == form.vars[username])
                user = db(query).select(limitby=(0, 1)).first()
                if user:
                    # user in db, check if registration pending or disabled
                    temp_user = user
                    if temp_user.registration_key == "pending":
                        response.warning = self.messages.registration_pending
                        return form
                    elif temp_user.registration_key in ("disabled", "blocked"):
                        response.error = self.messages.login_disabled
                        return form
                    elif not temp_user.registration_key is None and \
                             temp_user.registration_key.strip():
                        response.warning = \
                            self.messages.registration_verifying
                        return form
                    # Try alternate logins 1st as these have the
                    # current version of the password
                    user = None
                    for login_method in self.settings.login_methods:
                        if login_method != self and \
                                login_method(request.vars[username],
                                             request.vars[passfield]):
                            if not self in self.settings.login_methods:
                                # do not store password in db
                                form.vars[passfield] = None
                            user = self.get_or_create_user(form.vars)
                            break
                    if not user:
                        # Alternates have failed, maybe because service inaccessible
                        if self.settings.login_methods[0] == self:
                            # Try logging in locally using cached credentials
                            if temp_user[passfield] == form.vars.get(passfield, ""):
                                # Success
                                user = temp_user
                else:
                    # User not in db
                    if not self.settings.alternate_requires_registration:
                        # We're allowed to auto-register users from external systems
                        for login_method in self.settings.login_methods:
                            if login_method != self and \
                                    login_method(request.vars[username],
                                                 request.vars[passfield]):
                                if not self in self.settings.login_methods:
                                    # Do not store password in db
                                    form.vars[passfield] = None
                                user = self.get_or_create_user(form.vars)
                                break
                if not user:
                    self.log_event(self.settings.login_failed_log,
                                   request.post_vars)
                    # Invalid login
                    session.error = self.messages.invalid_login
                    redirect(self.url(args=request.args,
                                      vars=request.get_vars))
        else:
            # Use a central authentication server
            cas = self.settings.login_form
            cas_user = cas.get_user()
            if cas_user:
                cas_user[passfield] = None
                user = self.get_or_create_user(utable._filter_fields(cas_user))
                form = Storage()
                form.vars = user
                self.s3_register(form)
            elif hasattr(cas, "login_form"):
                return cas.login_form()
            else:
                # we need to pass through login again before going on
                next = "%s?_next=%s" % (URL(r=request), next)
                redirect(cas.login_url(next))

        # Process authenticated users
        if user:
            user = Storage(utable._filter_fields(user, id=True))
            self.login_user(user)
        if log and self.user:
            self.log_event(log % self.user)

        # How to continue
        if self.settings.login_form == self:
            if accepted_form:
                if onaccept:
                    onaccept(form)
                if isinstance(next, (list, tuple)):
                    # fix issue with 2.6
                    next = next[0]
                if next and not next[0] == "/" and next[:4] != "http":
                    next = self.url(next.replace("[id]", str(form.vars.id)))
                redirect(next)
            utable[username].requires = old_requires
            return form
        else:
            redirect(next)

    # -------------------------------------------------------------------------
    def login_user(self, user):
        """
            Log the user in
            - common function called by login() & register()
        """

        request = current.request
        session = current.session
        settings = self.settings
        vars = request.vars

        # If the user hasn't set a personal UTC offset,
        # then read the UTC offset from the form:
        if not user.utc_offset:
            user.utc_offset = session.s3.utc_offset

        session.auth = Storage(
            user=user,
            last_visit=request.now,
            expiration = vars.get("remember", False) and \
                settings.long_expiration or settings.expiration,
            remember = vars.has_key("remember"),
            hmac_key = web2py_uuid()
            )
        self.user = user
        self.s3_set_roles()

        # Read their language from the Profile
        language = user.language
        current.T.force(language)
        session.s3.language = language

        session.confirmation = self.messages.logged_in

        # Set a Cookie to present user with login box by default
        self.set_cookie()

        # Update the timestamp of the User so we know when they last logged-in
        utable = settings.table_user
        current.db(utable.id == self.user.id).update(timestmp = request.utcnow)

    # -------------------------------------------------------------------------
    def register(self,
                 next=DEFAULT,
                 onvalidation=DEFAULT,
                 onaccept=DEFAULT,
                 log=DEFAULT):
        """
            Overrides Web2Py's register() to add new functionality:
                - Checks whether registration is permitted
                - Custom Flash styles
                - Allow form to be embedded in other pages
                - Optional addition of Mobile Phone field to the Register form
                - Optional addition of Organisation field to the Register form

                - Lookup Domains/Organisations to check for Whitelists
                  &/or custom Approver

            @returns: a registration form
        """

        db = current.db
        settings = self.settings
        messages = self.messages
        request = current.request
        session = current.session
        deployment_settings = current.deployment_settings
        T = current.T

        utable = self.settings.table_user
        passfield = settings.password_field

        # S3: Don't allow registration if disabled
        self_registration = deployment_settings.get_security_self_registration()
        if not self_registration:
            session.error = messages.registration_disabled
            redirect(URL(args=["login"]))

        if self.is_logged_in() and request.function != "index":
            redirect(settings.logged_url)

        if next == DEFAULT:
            next = request.vars._next or settings.register_next
        if onvalidation == DEFAULT:
            onvalidation = settings.register_onvalidation
        if onaccept == DEFAULT:
            onaccept = settings.register_onaccept
        if log == DEFAULT:
            log = messages.register_log

        labels, required = s3_mark_required(utable)

        if deployment_settings.get_terms_of_service():
            submit_button = T("I accept. Create my account.")
        else:
            submit_button = T("Register")

        #formstyle = current.manager.s3.crud.formstyle
        form = SQLFORM(utable, hidden=dict(_next=request.vars._next),
                       labels = labels,
                       separator = "",
                       showid=settings.showid,
                       submit_button=submit_button,
                       delete_label=messages.delete_label,
                       #formstyle = formstyle
                       )
        for i, row in enumerate(form[0].components):
            item = row.element("input", _name=passfield)
            if item:
                field_id = "%s_password_two" % utable._tablename
                #row = formstyle(...)
                form[0].insert(i + 1,
                    TR( TD( LABEL("%s:" % messages.verify_password,
                                  _for="password_two",
                                  _id=field_id + SQLFORM.ID_LABEL_SUFFIX),
                            SPAN("*", _class="req"),
                            _class="w2p_fl"),
                        INPUT( _name="password_two",
                               _id=field_id,
                               _type="password",
                               requires=IS_EXPR("value==%s" % \
                               repr(request.vars.get(passfield, None)),
                               error_message=messages.mismatched_password)
                              ),
                        "",
                        _id=field_id + SQLFORM.ID_ROW_SUFFIX))
                #form[0].insert(i + 1, row)
        # Add an opt in clause to receive emails depending on the deployment settings
        if deployment_settings.get_auth_opt_in_to_email():
            field_id = "%s_opt_in" % utable._tablename
            comment = DIV(DIV(_class="tooltip",
                              _title="%s|%s" % (T("Mailing list"),
                                                T("By selecting this you agree that we may contact you."))))
            checked = deployment_settings.get_auth_opt_in_default() and "selected"
            form[0].insert(-1,
                           TR(TD(LABEL("%s:" % T("Receive updates"),
                                       _for="opt_in",
                                       _id=field_id + SQLFORM.ID_LABEL_SUFFIX),
                                 _class="w2p_fl"),
                                 INPUT(_name="opt_in", _id=field_id, _type="checkbox", _checked=checked),
                              TD(comment,
                                 _class="w2p_fc"),
                           _id=field_id + SQLFORM.ID_ROW_SUFFIX))

        # S3: Insert Mobile phone field into form
        if deployment_settings.get_auth_registration_requests_mobile_phone():
            field_id = "%s_mobile" % utable._tablename
            if deployment_settings.get_auth_registration_mobile_phone_mandatory():
                comment = SPAN("*", _class="req")
            else:
                comment = DIV(_class="tooltip",
                              _title="%s|%s" % (deployment_settings.get_ui_label_mobile_phone(),
                                                messages.help_mobile_phone))
            form[0].insert(-1,
                           TR(TD(LABEL("%s:" % deployment_settings.get_ui_label_mobile_phone(),
                                       _for="mobile",
                                       _id=field_id + SQLFORM.ID_LABEL_SUFFIX),
                                 _class="w2p_fl"),
                                 INPUT(_name="mobile", _id=field_id),
                              TD(comment,
                                 _class="w2p_fc"),
                           _id=field_id + SQLFORM.ID_ROW_SUFFIX))

        # S3: Insert Photo widget into form
        if deployment_settings.get_auth_registration_requests_image():
            label = self.messages.label_image
            comment = DIV(_class="stickytip",
                          _title="%s|%s" % (label,
                                            self.messages.help_image % \
                                                dict(gravatar = A("Gravatar",
                                                                  _target="top",
                                                                  _href="http://gravatar.com"))))
            field_id = "%s_image" % utable._tablename
            widget = SQLFORM.widgets["upload"].widget(current.s3db.pr_image.image, None)
            form[0].insert(-1,
                           TR(TD(LABEL("%s:" % label,
                                       _for="image",
                                       _id=field_id + SQLFORM.ID_LABEL_SUFFIX),
                                 _class="w2p_fl"),
                                 widget,
                              TD(comment,
                                 _class="w2p_fc"),
                           _id=field_id + SQLFORM.ID_ROW_SUFFIX))

        if settings.captcha != None:
            form[0].insert(-1, TR("", settings.captcha, ""))

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
                #user = utable[form.vars.id]
                user = Storage(utable._filter_fields(form.vars, id=True))
                self.login_user(user)

                self.s3_send_welcome_email(form.vars)

            elif settings.registration_requires_verification:
                # Send the Verification email
                if not settings.mailer or \
                   not settings.mailer.send(to=form.vars.email,
                                            subject=messages.verify_email_subject,
                                            message=messages.verify_email % dict(key=key)):
                    db.rollback()
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
                    #user = utable[form.vars.id]
                    user = Storage(utable._filter_fields(form.vars, id=True))
                    self.login_user(user)

            if log:
                self.log_event(log % form.vars)
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
            id = membership.insert(group_id=group_id, user_id=user_id, pe_id=entity)
        self.update_groups()
        self.log_event(self.messages.add_membership_log,
                       dict(user_id=user_id, group_id=group_id))
        return id

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
        messages = self.messages
        deployment_settings = current.deployment_settings

        key = current.request.args[-1]
        utable = settings.table_user
        query = (utable.registration_key == key)
        user = current.db(query).select(limitby=(0, 1)).first()
        if not user:
            redirect(settings.verify_email_next)

        if log == DEFAULT:
            log = messages.verify_email_log
        if next == DEFAULT:
            next = settings.verify_email_next

        self.s3_verify_user(user)

        if log:
            self.log_event(log % user)

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

        utable = self.settings.table_user

        utable.utc_offset.readable = True
        utable.utc_offset.writable = True

        if not self.is_logged_in():
            redirect(self.settings.login_url)
        passfield = self.settings.password_field
        utable[passfield].writable = False

        request = current.request
        session = current.session
        settings = current.deployment_settings

        if next == DEFAULT:
            next = request.get_vars._next \
                or request.post_vars._next \
                or self.settings.profile_next
        if onvalidation == DEFAULT:
            onvalidation = self.settings.profile_onvalidation
        if onaccept == DEFAULT:
            onaccept = self.settings.profile_onaccept
        if log == DEFAULT:
            log = self.messages.profile_log
        labels, required = s3_mark_required(utable)

        # If we have an opt_in and some post_vars then update the opt_in value
        if settings.get_auth_opt_in_to_email() and request.post_vars:
            opt_list = settings.get_auth_opt_in_team_list()
            removed = []
            selected = []
            for opt_in in opt_list:
                if opt_in in request.post_vars:
                    selected.append(opt_in)
                else:
                    removed.append(opt_in)
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
        if settings.get_auth_openid():
            form = DIV(form, openid_login_form.list_user_openids())
        else:
            form = SQLFORM(
                utable,
                self.user.id,
                fields = self.settings.profile_fields,
                labels = labels,
                hidden = dict(_next=next),
                showid = self.settings.showid,
                submit_button = self.messages.profile_save_button,
                delete_label = self.messages.delete_label,
                upload = self.settings.download_url,
                formstyle = self.settings.formstyle,
                separator = ""
                )
            if form.accepts(request, session,
                            formname="profile",
                            onvalidation=onvalidation,
                            hideerror=self.settings.hideerror):
                self.user.update(utable._filter_fields(form.vars))
                session.flash = self.messages.profile_updated
                if log:
                    self.log_event(log % self.user)
                callback(onaccept, form)
                if not next:
                    next = self.url(args=request.args)
                elif isinstance(next, (list, tuple)): ### fix issue with 2.6
                    next = next[0]
                elif next and not next[0] == "/" and next[:4] != "http":
                    next = self.url(next.replace("[id]", str(form.vars.id)))
                redirect(next)

        if settings.get_auth_opt_in_to_email():
            ptable = s3db.pr_person
            ltable = s3db.pr_person_user
            opt_list = settings.get_auth_opt_in_team_list()
            query = (ltable.user_id == form.record.id) & \
                    (ltable.pe_id == ptable.pe_id)
            db_opt_in_list = db(query).select(ptable.opt_in,
                                              limitby=(0, 1)).first().opt_in
            for opt_in in opt_list:
                field_id = "%s_opt_in_%s" % (_table_user, opt_list)
                if opt_in in db_opt_in_list:
                    checked = "selected"
                else:
                    checked = None
                form[0].insert(-1,
                               TR(TD(LABEL(T("Receive %(opt_in)s updates:") % \
                                                dict(opt_in=opt_in),
                                           _for="opt_in",
                                           _id=field_id + SQLFORM.ID_LABEL_SUFFIX),
                                     _class="w2p_fl"),
                                     INPUT(_name=opt_in, _id=field_id,
                                           _type="checkbox", _checked=checked),
                               _id=field_id + SQLFORM.ID_ROW_SUFFIX))
        return form

    # -------------------------------------------------------------------------
    def configure_user_fields(self):
        """
            Configure User Fields - for registration & user administration
        """

        messages = self.messages
        settings = self.settings
        deployment_settings = current.deployment_settings
        T = current.T
        db = current.db
        s3db = current.s3db

        utable = self.settings.table_user

        first_name = utable.first_name
        first_name.label = T("First Name")
        first_name.requires = IS_NOT_EMPTY(error_message=messages.is_empty),

        last_name = utable.last_name
        last_name.label = T("Last Name")
        if deployment_settings.get_L10n_mandatory_lastname():
            last_name.notnull = True
            last_name.requires = IS_NOT_EMPTY(error_message=messages.is_empty)

        if settings.username_field:
            table.username.requires = IS_NOT_IN_DB(db,
                                                   "%s.username" %
                                                   utable._tablename)

        email = utable.email
        email.label = T("E-mail")
        email.requires = [IS_EMAIL(error_message=messages.invalid_email),
                          IS_LOWER(),
                          IS_NOT_IN_DB(db,
                                       "%s.email" % utable._tablename,
                                       error_message=messages.duplicate_email)
                          ]

        language = utable.language
        language.label = T("Language")
        language.comment = DIV(_class="tooltip",
                               _title="%s|%s" % (T("Language"),
                                                 T("The language you wish the site to be displayed in.")))
        languages = current.deployment_settings.get_L10n_languages()
        language.represent = lambda opt: \
            languages.get(opt, current.messages.UNKNOWN_OPT)
        # Default the profile language to the one currently active
        language.default = T.accepted_language

        utc_offset = utable.utc_offset
        utc_offset.comment = DIV(_class="tooltip",
                                 _title="%s|%s" % (messages.label_utc_offset,
                                                   messages.help_utc_offset)
                                 )
        try:
            from s3validators import IS_UTC_OFFSET
            utc_offset.requires = IS_EMPTY_OR(IS_UTC_OFFSET())
        except:
            pass

        if deployment_settings.get_auth_registration_requests_organisation():
            organisation_id = utable.organisation_id
            organisation_id.writable = True
            organisation_id.readable = True
            from s3validators import IS_ONE_OF
            organisation_id.requires = IS_ONE_OF(db, "org_organisation.id",
                                                s3db.org_organisation_represent,
                                                orderby="org_organisation.name",
                                                sort=True)
            organisation_id.represent = s3db.org_organisation_represent
            organisation_id.default = deployment_settings.get_auth_registration_organisation_id_default()
            #from s3widgets import S3OrganisationAutocompleteWidget
            #organisation_id.widget = S3OrganisationAutocompleteWidget()
            # no permissions for autocomplete on registration page
            organisation_id.comment = DIV(_class="tooltip",
                              _title="%s|%s" % (T("Organization"),
                                                   T("Enter some characters to bring up a list of possible matches")))

            if not deployment_settings.get_auth_registration_organisation_required():
                organisation_id.requires = IS_NULL_OR(organisation_id.requires)

        if deployment_settings.get_auth_registration_requests_site():
            site_id = utable.site_id
            site_id.writable = True
            site_id.readable = True
            from s3validators import IS_ONE_OF
            site_id.requires = IS_ONE_OF( db, "org_site.site_id",
                                          s3db.org_site_represent,
                                          orderby="org_site.name",
                                          sort=True )
            site_id.represent = s3db.org_site_represent
            site_id.default = deployment_settings.get_auth_registration_organisation_id_default()
            #from s3widgets import S3SiteAutocompleteWidget
            #site_id.widget = S3SiteAutocompleteWidget()
            # no permissions for autocomplete on registration page
            site_id.comment = DIV(_class="tooltip",
                              _title="%s|%s" % (deployment_settings.get_org_site_label(),
                                                T("Enter some characters to bring up a list of possible matches")))

            if not deployment_settings.get_auth_registration_site_required():
                site_id.requires = IS_NULL_OR(site_id.requires)

    # -------------------------------------------------------------------------
    def s3_membership_import_prep(self, data, group=None):
        """
            S3 framework function

            Designed to be called when a user is imported.
            Because the auth.membership.pe_id fields is an
            integer not reference this function is used to lookup
            the pe_id

            Does the following:
                - Looks up auth.membership.pe_id

            organisation.name=<Org Name>
        """

        db = current.db
        s3db = current.s3db

        resource, tree = data
        xml = current.xml
        tag = xml.TAG
        att = xml.ATTRIBUTE

        elements = tree.getroot().xpath("/s3xml//resource[@name='auth_membership']/data[@field='pe_id']")
        for element in elements:
            pe_string = element.text

            if pe_string:
                pe_type, pe_value =  pe_string.split("=")
                pe_tablename, pe_field =  pe_type.split(".")

                table = s3db[pe_tablename]
                query = (table[pe_field] == pe_value)
                record = db(query).select(table.pe_id).first()
                if record:
                    element.text = str(record.pe_id)
                else:
                    # Add a new record
                    id = table.insert(**{pe_field: pe_value})
                    s3db.update_super(table, table[id])
                    element.text = str(table[id].pe_id)

    # -------------------------------------------------------------------------
    def s3_user_register_onaccept(self, form):
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

        db = current.db
        s3db = current.s3db
        session = current.session

        utable = self.settings.table_user
        temptable = s3db.auth_user_temp

        vars = form.vars
        user_id = vars.id

        if not user_id:
            return None

        # If the user hasn't set a personal UTC offset,
        # then read the UTC offset from the form:
        if not vars.utc_offset:
            db(utable.id == user_id).update(utc_offset = session.s3.utc_offset)

        record  = dict(user_id = user_id)

        # Add the mobile to pr_contact
        mobile = vars.mobile
        if mobile:
            record["mobile"] = mobile

        # Insert the profile picture
        image = vars.image
        if image != None and  hasattr(image, "file"):
            # @ToDo: DEBUG!!!
            source_file = image.file
            original_filename = image.filename

            field = temptable.image
            newfilename = field.store(source_file,
                                      original_filename,
                                      field.uploadfolder)
            if isinstance(field.uploadfield, str):
                fields[field.uploadfield] = source_file.read()
            record["image"] = newfilename

        if len(record) > 1:
            temptable.update_or_insert( **record )

    # -------------------------------------------------------------------------
    def s3_verify_user(self, user):
        """"
            S3 framework function

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

        deployment_settings = current.deployment_settings

        # Lookup the Approver
        approver, organisation_id = self.s3_approver(user)

        if deployment_settings.get_auth_registration_requires_approval() and approver:
            approved = False
            utable = self.settings.table_user
            current.db(utable.id == user.id).update(registration_key = "pending")

            if user.registration_key:
                # User has just been verified
                current.session.information = deployment_settings.get_auth_registration_pending_approval()
            else:
                #No Verification needed
                current.session.information = deployment_settings.get_auth_registration_pending()
            # @ToDo: include link to user
            subject = current.T("%(system_name)s - New User Registration Approval Pending") % \
                        {"system_name": deployment_settings.get_system_name()}
            message = self.messages.approve_user % \
                        dict(first_name = user.first_name,
                             last_name = user.last_name,
                             email = user.email)
        else:
            approved = True
            self.s3_approve_user(user)
            self.s3_send_welcome_email(user)
            session = current.session
            session.confirmation = self.messages.email_verified
            session.flash = self.messages.registration_successful

            if not deployment_settings.get_auth_always_notify_approver():
                return True
            subject = current.T("%(system_name)s - New User Registered") % \
                      {"system_name": deployment_settings.get_system_name()}
            message = self.messages.new_user % dict(first_name = user.first_name,
                                                    last_name = user.last_name,
                                                    email = user.email)

        result = self.settings.mailer.send(to = approver,
                                           subject = subject,
                                           message = message)
        if not result:
            # Don't prevent registration just because email not configured
            #db.rollback()
            current.response.error = self.messages.email_send_failed
            return False

        return approved

    # -------------------------------------------------------------------------
    def s3_approve_user(self, user):
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
        """

        user_id = user.id
        if not user_id:
            return None

        db = current.db
        s3db = current.s3db
        session = current.session
        deployment_settings = current.deployment_settings

        utable = self.settings.table_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user

        # Add to 'Authenticated' role
        authenticated = self.id_group("Authenticated")
        self.add_membership(authenticated, user_id)

        # Add User to required registration roles
        entity_roles = deployment_settings.get_auth_registration_roles()
        if entity_roles:
            gtable = self.settings.table_group
            mtable = self.settings.table_membership
            for entity in entity_roles.keys():
                roles = entity_roles[entity]

                # Get User's Organisation or Site pe_id
                if entity in ["organisation_id", "site_id"]:
                    tablename = "org_%s" % entity.split("_")[0]
                    entity = s3db.pr_get_pe_id(tablename, user[entity])
                    if not entity:
                        continue

                query = (gtable.uuid.belongs(roles))
                rows = db(query).select(gtable.id)
                for role in rows:
                    self.add_membership(role.id, user_id, entity=entity)

        if deployment_settings.has_module("delphi"):
            # Add user as a participant of the default problem group
            table = s3db.delphi_group
            query = (table.uuid == "DEFAULT")
            group = db(query).select(table.id,
                                     limitby=(0, 1)).first()
            if group:
                table = s3db.delphi_membership
                table.insert(group_id=group.id,
                             user_id=user_id,
                             status=3)

        self.s3_link_user(user)

        if current.response.s3.bulk is True:
            # Non-interactive imports should stop here
            return

        # Allow them to login
        db(utable.id == user_id).update(registration_key = "")

        return

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
        """

        # Create/Update/Link to organisation,
        organisation_id = self.s3_link_to_organisation(user)

        # Add to user Person Registry and Email/Mobile to pr_contact
        person_id = self.s3_link_to_person(user, organisation_id)

        human_resource_id = self.s3_link_to_human_resource(user, person_id)

        return

    # -----------------------------------------------------------------------------
    @staticmethod
    def s3_user_profile_onaccept(form):
        """ Update the UI locale from user profile """

        if form.vars.language:
            current.session.s3.language = form.vars.language

    # -------------------------------------------------------------------------
    def s3_link_to_person(self,
                          user=None,
                          organisation_id=None):
        """
            Links user accounts to person registry entries

            @param user: the user record
            @param organisation_id: the user's orgnaisation_id
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
        atable = s3db.pr_address
        etable = s3db.pr_pentity
        gtable = s3db.gis_config
        ltable = s3db.pr_person_user

        # Organisation becomes the realm entity of the person record
        if organisation_id:
            realm_entity = s3db.pr_get_pe_id("org_organisation",
                                             organisation_id)
        else:
            realm_entity = None

        left = [ltable.on(ltable.user_id == utable.id),
                ptable.on(ptable.pe_id == ltable.pe_id),
                ttable.on(utable.id == ttable.user_id)]

        if user is not None:
            if not isinstance(user, (list, tuple)):
                user = [user]
            user_ids = [u.id for u in user]
            query = (utable.id.belongs(user_ids))
        else:
            query = (utable.id != None)

        rows = db(query).select(utable.id,
                                utable.first_name,
                                utable.last_name,
                                utable.email,
                                ltable.pe_id,
                                ptable.id,
                                ptable.first_name,
                                ptable.last_name,
                                ttable.mobile,
                                ttable.image,
                                left=left, distinct=True)

        person_ids = [] # Collect the person IDs

        for row in rows:

            # The user record
            user = row.auth_user

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
                   user.last_name != person.first_name:

                    query = (ptable.pe_id == pe_id)
                    db(query).update(first_name = user.first_name,
                                     last_name = user.last_name)

                # Add the user's email address to the person record if missing
                query = (ctable.pe_id == pe_id) & \
                        (ctable.contact_method == "EMAIL") & \
                        (ctable.value == user.email)
                item = db(query).select(limitby=(0, 1)).first()
                if item is None:
                    ctable.insert(pe_id = pe_id,
                                  contact_method = "EMAIL",
                                  value = user.email)

                #@ToDo: Also update mobile phone? profile image? Groups?

                person_ids.append(person.id)

            else:
                # This user account isn't yet linked to a person record
                # => try to find a person record with same first name,
                # last name and email address

                first_name = user.first_name
                last_name = user.last_name
                email = user.email.lower()
                if email:
                    query = (ptable.first_name == first_name) & \
                            (ptable.last_name == last_name) & \
                            (ctable.pe_id == ptable.pe_id) & \
                            (ctable.contact_method == "EMAIL") & \
                            (ctable.value.lower() == email)
                    person = db(query).select(ptable.id,
                                              ptable.pe_id,
                                              limitby=(0, 1)).first()
                else:
                    # Can't find a match without an email address
                    person = None

                # Default record owner/realm
                owner = Storage(owned_by_user=user.id,
                                realm_entity=realm_entity)

                if person:
                    query = ltable.pe_id == person.pe_id
                    other = db(query).select(ltable.id, limitby=(0, 1)).first()
                if person and not other:
                    # Match found, and it isn't linked to another user account
                    # => link to this person record (+update it)

                    pe_id = person.pe_id

                    # Insert a link
                    ltable.insert(user_id=user.id, pe_id=pe_id)

                    # Assign ownership of the Person record
                    person.update_record(**owner)

                    # Assign ownership of the Contact record(s)
                    query = (ctable.pe_id == pe_id)
                    db(query).update(**owner)

                    # Assign ownership of the Address record(s)
                    query = (atable.pe_id == pe_id)
                    db(query).update(**owner)

                    # Assign ownership of the Config record(s)
                    query = (gtable.pe_id == pe_id)
                    db(query).update(**owner)

                    # Set pe_id if this is the current user
                    if self.user and self.user.id == user.id:
                        self.user.pe_id = pe_id

                    person_ids.append(person.id)

                else:
                    # There is no match or it is linked to another user account
                    # => create a new person record (+link to it)

                    if current.request.vars.get("opt_in", None):
                        opt_in = current.deployment_settings.get_auth_opt_in_team_list()
                    else:
                        opt_in = []

                    # Create a new person record
                    person_id = ptable.insert(first_name = first_name,
                                              last_name = last_name,
                                              opt_in = opt_in,
                                              modified_by = user.id,
                                              **owner)
                    if person_id:

                        # Update the super-entities
                        person = Storage(id=person_id)
                        s3db.update_super(ptable, person)

                        pe_id = person.pe_id

                        # Insert a link
                        ltable.insert(user_id=user.id, pe_id=pe_id)

                        # Add the email to pr_contact
                        ctable.insert(pe_id = pe_id,
                                      contact_method = "EMAIL",
                                      priority = 1,
                                      value = email,
                                      **owner)

                        # Add the user to each team if they have chosen to opt-in
                        g_table = s3db["pr_group"]
                        m_table = s3db["pr_group_membership"]

                        for team in opt_in:
                            query = (g_table.name == team)
                            team_rec = db(query).select(g_table.id,
                                                        limitby=(0, 1)).first()

                            # if the team doesn't exist then add it
                            if team_rec == None:
                                team_id = g_table.insert(name = team,
                                                         group_type = 5)
                            else:
                                team_id = team_rec.id
                            gm_table.insert(group_id = team_id,
                                            person_id = person_id)

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

                    # Insert the profile picture from the temporary
                    # user data into pr_image
                    image = tuser.image
                    if image: # and hasattr(image, "file"):
                        itable = s3db.pr_image
                        url = URL(c="default", f="download", args=image)
                        itable.insert(pe_id=pe_id,
                                      profile=True,
                                      image=image,
                                      url = url,
                                      description=current.T("Profile Picture"))

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
        approver, organisation_id = self.s3_approver(user)
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
            acronym = user.get("organisation_acronym", None)
            if name:
                # Create new organisation
                otable = s3db.org_organisation
                record = Storage(name=name,
                                 acronym=acronym)
                organisation_id = otable.insert(**record)

                # Callbacks
                if organisation_id:
                    record["id"] = organisation_id
                    s3db.update_super(otable, record)
                    current.manager.onaccept(otable, record, method="create")
                    self.s3_set_record_owner(otable, organisation_id)

                # Update user record
                user.organisation_id = organisation_id
                query = (utable.id == user_id)
                db(query).update(organisation_id=organisation_id)

        if not organisation_id:
            return None

        # Update link to Organisation
        ltable = s3db.org_organisation_user

        # Update if the User's Organisation has changed
        query = (ltable.user_id == user_id)
        rows = db(query).select(ltable.organisation_id,
                                limitby=(0, 2))
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
                ltable.insert(user_id=user_id,
                              organisation_id=organisation_id)

        return organisation_id

    # -------------------------------------------------------------------------
    def s3_link_to_human_resource(self,
                                  user,
                                  person_id = None
                                  ):
        """
            Take ownership of the HR records of the person record
            @ToDo: Add user to the Org Access role.
        """

        db = current.db
        s3db = current.s3db

        user_id = user.id
        organisation_id = user.organisation_id

        htablename = "hrm_human_resource"
        htable = s3db.table(htablename)

        if not htable or not organisation_id:
            return None

        # Update existing HR record for this user
        site_id = user.site_id
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (htable.deleted == False) & \
                (htable.status == 1) & \
                (htable.person_id == ptable.id) & \
                (ptable.pe_id == ltable.pe_id) & \
                (ltable.user_id == user_id)
        rows = db(query).select(htable.id,
                                limitby=(0, 2))
        if len(rows) == 1:
            # Only update if there is a single HR Record
            hr_id = rows.first().id
            db(htable.id == hr_id).update(organisation_id = organisation_id,
                                          site_id = site_id)
            # Update record ownership
            self.s3_set_record_owner(htable, hr_id, force_update=True)

            # Update Site link
            hstable = s3db.hrm_human_resource_site
            query = (hstable.human_resource_id == hr_id)
            row = db(query).select(hstable.id,
                                    limitby=(0, 1)).first()
            if row:
                db(query).update(site_id = site_id,
                                 human_resource_id = hr_id,
                                 owned_by_user = user_id)
            else:
                hstable.insert(site_id=site_id,
                               human_resource_id=hr_id,
                               owned_by_user=user_id)

        # Create an HR record, if one doesn't already exist
        if isinstance(person_id, list):
            person_ids = person_id
        else:
            person_ids = [person_id]
        query = (htable.person_id.belongs(person_ids)) & \
                (htable.organisation_id == organisation_id) & \
                (htable.site_id == site_id)
        row = db(query).select(htable.id, limitby=(0, 1)).first()

        if row:
            hr_id = row.id
        else:
            # @ToDo: Separate deployment setting
            if current.deployment_settings.get_hrm_show_staff():
                type = 1 # Staff
            else:
                type = 2 # Volunteer
            record = Storage(person_id=person_ids[0],
                             organisation_id=organisation_id,
                             site_id = site_id,
                             type=type,
                             owned_by_user=user_id,
                             )
            hr_id = htable.insert(**record)
            if hr_id:
                record["id"] = hr_id
                s3db.update_super(htable, record)
                current.manager.onaccept(htablename, record,
                                         method="create")

        return hr_id

    # -------------------------------------------------------------------------
    def s3_approver(self, user):
        """
            Returns the Approver for a new Registration &
            the organisation_id field

            @param: user - the user record (form.vars when done direct)
            @ToDo: Support multiple approvers per Org - via Org Admin (or specific Role?)
                   Split into separate functions to returning approver & finding users' org from auth_organisations

            @returns approver, organisation_id - if approver = False, user is automatically approved by whitelist
        """

        db = current.db
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        approver = None
        organisation_id = None

        # Check for Domain: Whitelist or specific Approver
        table = s3db.auth_organisation
        if "email" in user and user["email"] and "@" in user["email"]:
            domain = user.email.split("@", 1)[-1]
            query = (table.domain == domain)
            record = db(query).select(table.organisation_id,
                                      table.approver,
                                      limitby=(0, 1)).first()
        else:
            record = None

        if record:
            organisation_id = record.organisation_id
            approver = record.approver
        elif deployment_settings.get_auth_registration_requests_organisation():
            # Check for an Organization-specific Approver
            organisation_id = user.get("organisation_id", None)
            if organisation_id:
                query = (table.organisation_id == organisation_id)
                record = db(query).select(table.approver,
                                          limitby=(0, 1)).first()
                if record and record.approver:
                    approver = record.approver

        if not approver:
            # Default Approver
            approver = deployment_settings.get_mail_approver()

        return approver, organisation_id

    # -------------------------------------------------------------------------
    def s3_send_welcome_email(self, user):
        """
            Send a welcome mail to newly-registered users
            - especially suitable for users from Facebook/Google who don't
              verify their emails
        """

        if "name" in user:
            user["first_name"] = user["name"]
        if "family_name" in user:
            # Facebook
            user["last_name"] = user["family_name"]

        subject = self.messages.welcome_email_subject
        message = self.messages.welcome_email

        results = self.settings.mailer.send(user["email"], subject=subject, message=message)
        if not results:
            current.response.error = self.messages.unable_send_email
        return

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

        utable = self.settings.table_user
        query = None
        if not user_id:
            # Anonymous
            user = None
        elif isinstance(user_id, basestring) and not user_id.isdigit():
            if self.settings.username_field:
                query = (utable.username == user_id)
            else:
                query = (utable.email == user_id)
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
                               expiration=self.settings.expiration)
        self.s3_set_roles()

        if user:
            # Set the language from the Profile
            language = user.language
            current.T.force(language)
            session.s3.language = language

        return user

    # -------------------------------------------------------------------------
    def s3_logged_in(self):
        """
            Check whether the user is currently logged-in
            - tries Basic if not
        """

        if self.override:
            return True

        if not self.is_logged_in():
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
                     gtable.uuid.belongs(S3_SYSTEM_ROLES.values())
            rows = current.db(query).select(gtable.id, gtable.uuid)
            system_roles = Storage([(role.uuid, role.id) for role in rows])
        else:
            system_roles = Storage([(uid, None) for uid in S3_SYSTEM_ROLES])

        s3.system_roles = system_roles
        return system_roles

    # -------------------------------------------------------------------------
    def s3_set_roles(self):
        """ Update pe_id, roles and realms for the current user """

        session = current.session
        settings = current.deployment_settings

        if "permissions" in current.response.s3:
            del current.response.s3["permissions"]

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
            rows = db(query).select(mtable.group_id, mtable.pe_id)

            # Add all group_ids to session.s3.roles
            session.s3.roles.extend(list(set([row.group_id for row in rows])))

            # Realms:
            # Permissions of a group apply only for records owned by any of
            # the entities which belong to the realm of the group membership

            if not self.permission.entity_realm:
                # Group memberships have no realms (policy 5 and below)
                self.user["realms"] = Storage([(row.group_id, None) for row in rows])
                self.user["delegations"] = Storage()

            else:
                # Group memberships are limited to realms (policy 6 and above)
                realms = {}
                delegations = {}

                # These roles can't be realm-restricted:
                unrestrictable = [system_roles.ADMIN,
                                  system_roles.ANONYMOUS,
                                  system_roles.AUTHENTICATED]

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
                    elif pe_id is 0:
                        # Site-wide
                        realms[group_id] = None
                    elif pe_id not in realm:
                        realms[group_id].append(pe_id)

                if self.permission.entity_hierarchy:
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
                    if self.permission.delegations and self.user.pe_id:

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
                                                atable.pe_id)

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
                    if self.permission.delegations:
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

        return

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

        hidden = args.get("hidden", False)
        system = args.get("system", False)
        protected = args.get("protected", False)

        if isinstance(description, dict):
            acls = [description] + acls
            description = None

        uid = args.get("uid", None)
        if uid:
            query = (table.uuid == uid)
            record = current.db(query).select(limitby=(0, 1)).first()
        else:
            record = None
            uid = uuid4()

        if record:
            role_id = record.id
            record.update_record(deleted=False,
                                 role=role,
                                 description=description,
                                 hidden=hidden,
                                 system=system,
                                 protected=protected)
        else:
            role_id = table.insert(uuid=uid,
                                   role=role,
                                   description=description,
                                   hidden=hidden,
                                   system=system,
                                   protected=protected)
        if role_id:
            for acl in acls:
                self.permission.update_acl(role_id, **acl)

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
            gquery = (table.uuid == role_id)
        else:
            role_id = int(role_id)
            gquery = (table.id == role_id)

        role = db(gquery).select(limitby=(0, 1)).first()
        if role and not role.protected:
            # Remove all memberships for this role
            mtable = self.settings.table_membership
            mquery = (mtable.group_id == role.id)
            db(mquery).update(deleted=True)
            # Remove all ACLs for this role
            ptable = self.permission.table
            pquery = (ptable.group_id == role.id)
            db(pquery).update(deleted=True)
            # Remove the role
            db(gquery).update(role=None, deleted=True)

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
                membership_id = mtable.insert(**membership)

        # Update roles for current user if required
        if self.user and str(user_id) == str(self.user.id):
            self.s3_set_roles()

        return

    # -------------------------------------------------------------------------
    def s3_retract_role(self, user_id, group_id, for_pe=None):
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
        import gluon.contrib.simplejson as json
        for m in memberships:
            deleted_fk = {"user_id": m.user_id,
                          "group_id": m.group_id}
            if for_pe:
                deleted_fk["pe_id"] = for_pe
            deleted_fk = json.dumps(deleted_fk)
            m.update_record(deleted=True,
                            deleted_fk=deleted_fk,
                            user_id=None,
                            group_id=None)

        # Update roles for current user if required
        if self.user and str(user_id) == str(self.user.id):
            self.s3_set_roles()

        return

    # -------------------------------------------------------------------------
    def s3_get_roles(self, user_id, for_pe=[]):
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
        else:
            query &= (mtable.pe_id == for_pe)
        rows = current.db(query).select(mtable.group_id)
        return list(set([row.group_id for row in rows]))

    # -------------------------------------------------------------------------
    def s3_has_role(self, role, for_pe=None):
        """
            Check whether the currently logged-in user has a certain role
            (auth_group membership).

            @param role: the record ID or UID of the role
            @param for_pe: check for this particular realm, possible values:

                           None - for any entity
                           0 - site-wide
                           X - for entity X
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
        if system_roles.ADMIN in realms:
            return True

        # Resolve role ID/UID
        if isinstance(role, str):
            if role.isdigit():
                role = int(role)
            else:
                gtable = self.settings.table_group
                query = (gtable.deleted != True) & \
                        (gtable.uuid == role)
                row = current.db(query).select(gtable.id,
                                               limitby=(0, 1)).first()
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
    def s3_group_members(self, group_id, for_pe=[]):
        """
            Get a list of members of a group

            @param group_id: the group record ID
            @param for_pe: show only group members for this PE

            @returns: a list of the user_ids for members of a group
        """

        mtable = self.settings.table_membership

        query = (mtable.deleted != True) & \
                (mtable.group_id == group_id)
        if for_pe is None:
            query &= (mtable.pe_id == None)
        elif for_pe:
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
                    for pe_id in receivers:
                        atable.insert(role_id=role_id,
                                      pe_id=pe_id)
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

            @returns: a Storage {<receiver>: [group_ids]}, or
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

            @param person_id: the pr_person record ID
            @param pe_id: the person entity ID, alternatively
        """

        if isinstance(person_id, basestring) and not person_id.isdigit():
            utable = self.settings.table_user
            query = (utable.email == person_id)
            user = current.db(query).select(utable.id,
                                            limitby=(0, 1)).first()
            if user:
                return user.id
        else:
            s3db = current.s3db
            ltable = s3db.pr_person_user
            if not ltable:
                return None
            if person_id:
                ptable = s3db.pr_person
                if not ptable:
                    return None
                query = (ptable.id == person_id) & \
                        (ptable.pe_id == ltable.pe_id)
            else:
                query = (ltable.pe_id == pe_id)
            link = current.db(query).select(ltable.user_id,
                                            limitby=(0, 1)).first()
            if link:
                return link.user_id
        return None

    # -------------------------------------------------------------------------
    def s3_user_pe_id(self, user_id):
        """
            Get the person pe_id for a user ID

            @param user_id: the user ID
        """

        table = current.s3db.pr_person_user
        row = current.db(table.user_id == user_id).select(table.pe_id,
                                                          limitby=(0, 1)).first()
        if row:
            return row.pe_id
        return None

    # -------------------------------------------------------------------------
    def s3_logged_in_person(self):
        """
            Get the person record ID for the current logged-in user
        """

        if self.s3_logged_in():
            ptable = current.s3db.pr_person
            try:
                query = (ptable.pe_id == self.user.pe_id)
            except AttributeError:
                # Prepop
                pass
            else:
                record = current.db(query).select(ptable.id,
                                                  limitby=(0, 1)).first()
                if record:
                    return record.id
        return None

    # -------------------------------------------------------------------------
    def s3_logged_in_human_resource(self):
        """
            Get the first HR record ID for the current logged-in user
        """

        if self.s3_logged_in():
            s3db = current.s3db
            ptable = s3db.pr_person
            htable = s3db.hrm_human_resource

            try:
                query = (htable.person_id == ptable.id) & \
                        (ptable.pe_id == self.user.pe_id)
            except AttributeError:
                # Prepop
                pass
            else:
                record = current.db(query).select(htable.id,
                                                  orderby =~htable.modified_on,
                                                  limitby=(0, 1)).first()
                if record:
                    return record.id
        return None

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
            s3db = current.s3db
            table = s3db[table]

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
            s3db = current.s3db
            table = s3db[table]

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

        if self.s3_has_role(group_id):
            r = True
        else:
            r = False

        log = self.messages.has_membership_log
        if log:
            if not user_id and self.user:
                user_id = self.user.id
            self.log_event(log % dict(user_id=user_id,
                                      group_id=group_id, check=r))
        return r

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

                if not self.s3_logged_in():
                    import urllib
                    request = current.request
                    next = URL(args=request.args, vars=request.get_vars)
                    redirect("%s?_next=%s" % (self.settings.login_url,
                                              urllib.quote(next)))

                system_roles = self.get_system_roles()
                ADMIN = system_roles.ADMIN
                if not self.s3_has_role(role) and not self.s3_has_role(ADMIN):
                    current.session.error = self.messages.access_denied
                    next = self.settings.on_failed_authorization
                    redirect(next)

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
            table = table._tablename
        if not self.user:
            session = current.session
            if "owned_records" not in session:
                session.owned_records = Storage()
            records = session.owned_records.get(table, [])
            record_id = str(record_id)
            if record_id not in records:
                records.append(record_id)
            session.owned_records[table] = records
        return

    # -------------------------------------------------------------------------
    def s3_session_owns(self, table, record_id):
        """
            Checks whether the current session owns a record

            @param table: the table or table name
            @param record_id: the record ID
        """

        session = current.session
        if "owned_records" not in session:
            return False
        if hasattr(table, "_tablename"):
            table = table._tablename
        if record_id and not self.user:
            try:
                records = session.owned_records.get(table, [])
            except:
                records = []
            if str(record_id) in records:
                return True
        return False

    # -------------------------------------------------------------------------
    def s3_clear_session_ownership(self, table=None, record_id=None):
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
                table = table._tablename
            if table in session.owned_records:
                records = session.owned_records[table]
                if record_id is not None:
                    if str(record_id) in records:
                        records.remove(str(record_id))
                else:
                    del session.owned_records[table]
        else:
            session.owned_records = Storage()
        return

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
        data = Storage()
        for key in fields:
            if key in ownership_fields:
                data[key] = fields[key]
        if data:
            s3db = current.s3db
            db = current.db

            # Update record
            q = (table._id == record_id)
            success = db(q).update(**data)

            # Update realm-components
            if success and update and REALM in data:
                rc = s3db.get_config(table, "realm_components", [])
                resource = s3db.resource(table, components=rc)
                realm = {REALM:data[REALM]}
                for component in resource.components.values():
                    ctable = component.table
                    if REALM not in ctable.fields:
                        continue
                    query = component.get_join() & q
                    rows = db(query).select(ctable._id)
                    ids = list(set([row[ctable._id] for row in rows]))
                    if ids:
                        db(ctable._id.belongs(ids)).update(**realm)

            # Update super-entity
            self.update_shared_fields(table, record, **data)
        else:
            return None

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
            tablename = table._tablename
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

        # Prepare the udpate
        data = Storage()

        # Find owned_by_user
        if OUSR in fields_in_table:
            pi = ("pr_person",
                  "pr_identity",
                  "pr_education",
                  "pr_contact",
                  "pr_address",
                  "pr_contact_emergency",
                  "pr_physical_description",
                  "pr_group_membership",
                  "pr_image",
                  "hrm_training")
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
        return

    # -------------------------------------------------------------------------
    def set_realm_entity(self, table, records, entity=0, force_update=False):
        """
            Update the realm entity for records, will also update the
            realm in all configured realm-entities, see:

            http://eden.sahanafoundation.org/wiki/S3AAA/OrgAuth#Realms1

            To be called by CRUD and Importer during record update.

            @param table: the table (or tablename)
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
            tablename = table._tablename
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

            realm_entity = self.get_realm_entity(table, row,
                                                 entity=realm_entity)
            data = {REALM:realm_entity}
            self.s3_update_record_owner(table, row,
                                        update=force_update, **data)

        return

    # -------------------------------------------------------------------------
    def get_realm_entity(self, table, record, entity=0):
        """
            Lookup the realm entity for a record

            @param table: the table
            @param record: the record (as Row or dict)
            @param entity: the entity (pe_id)
        """

        s3db = current.s3db

        REALM = "realm_entity"

        EID = "pe_id"
        OID = "organisation_id"
        SID = "site_id"
        GID = "group_id"

        otablename = "org_organisation"
        stablename = "org_site"
        gtablename = "pr_group"

        if REALM not in table:
            return None

        # Entity specified by call?
        realm_entity = entity
        if isinstance(entity, tuple):
            realm_entity = s3db.pr_get_pe_id(entity)

        # Fall back to deployment-global method to determine the realm entity
        if realm_entity == 0:
            handler = current.deployment_settings.get_auth_realm_entity()
            if callable(handler):
                realm_entity = handler(table, record)
            else:
                realm_entity = 0

        # Fall back to table-specific method
        if realm_entity == 0:
            handler = s3db.get_config(table, "realm_entity")
            if callable(handler):
                realm_entity = handler(table, record)

        # Fall back to standard lookup cascade
        if realm_entity == 0:
            get_pe_id = s3db.pr_get_pe_id
            if EID in record and \
               table._tablename not in ("pr_person", "dvi_body"):
                realm_entity = record[EID]
            elif OID in record:
                realm_entity = get_pe_id(otablename, record[OID])
            elif SID in record:
                realm_entity = get_pe_id(stablename, record[SID])
            elif GID in record:
                realm_entity = get_pe_id(gtablename, record[GID])
            else:
                realm_entity = None

        return realm_entity

    # -------------------------------------------------------------------------
    def update_shared_fields(self, table, record, **data):
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

        tables = dict()
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
                updates = dict([(f, data[f])
                                for f in data if f in supertable.fields])
                if not updates:
                    continue
                db(query).update(**updates)
        return

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
                return
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
                tablename = table._tablename
            else:
                tablename = table
            s3db.configure(tablename, insertable = False)

        return []

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
                tablename = table._tablename
            else:
                tablename = table
            s3db.configure(tablename, insertable = False)

        return []

    # -------------------------------------------------------------------------
    def root_org(self):
        """
            Return the current user's root organisation or None
        """

        if not self.user:
            return None
        org_id = self.user.organisation_id
        if not org_id:
            return None
        return current.cache.ram(
                    # Common key for all users of this org
                    "root_org_%s" % org_id,
                    lambda: current.s3db.org_root_organisation(organisation_id=org_id)[0],
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

    CREATE = 0x0001
    READ = 0x0002
    UPDATE = 0x0004
    DELETE = 0x0008
    REVIEW = 0x0010
    APPROVE = 0x0020

    ALL = CREATE | READ | UPDATE | DELETE | REVIEW | APPROVE
    NONE = 0x0000 # must be 0!

    PERMISSION_OPTS = OrderedDict([
        #(NONE, "NONE"),
        [CREATE, "CREATE"],
        [READ, "READ"],
        [UPDATE, "UPDATE"],
        [DELETE, "DELETE"],
        [REVIEW, "REVIEW"],
        [APPROVE, "APPROVE"]])

    # Method string <-> required permission
    METHODS = Storage({
        "create": CREATE,
        "read": READ,
        "update": UPDATE,
        "delete": DELETE,

        "search": READ,
        "report": READ,
        "map": READ,

        "import": CREATE,

        "review": REVIEW,
        "approve": APPROVE,
        "reject": APPROVE,
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
        self.use_cacls = self.policy in (3, 4, 5, 6, 7 ,8)
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
        # @todo: move this into s3utils.py:
        self.format = request.extension
        if "format" in request.get_vars:
            ext = request.get_vars.format
            if isinstance(ext, list):
                ext = ext[-1]
            self.format = ext.lower() or self.format
        else:
            ext = [a for a in request.args if "." in a]
            if ext:
                self.format = ext[-1].rsplit(".", 1)[1].lower()

        if request.function == "ticket" and \
           request.controller == "admin":
            # Error tickets need an override
            self.format = "html"

        # Page permission cache
        self.page_acls = Storage()
        self.table_acls = Storage()

        # Pages which never require permission:
        # Make sure that any data access via these pages uses
        # accessible_query explicitly!
        self.unrestricted_pages = ("default/index",
                                   "default/user",
                                   "default/contact",
                                   "default/about")

        # Default landing pages
        _next = URL(args=request.args, vars=request.vars)
        self.homepage = URL(c="default", f="index")
        self.loginpage = URL(c="default", f="user", args="login",
                             vars=dict(_next=_next))

    # -------------------------------------------------------------------------
    def define_table(self, migrate=True, fake_migrate=False):
        """
            Define permissions table, invoked by AuthS3.define_tables()
        """

        db = current.db

        table_group = self.auth.settings.table_group
        if table_group is None:
            table_group = "integer" # fallback (doesn't work with requires)

        if not self.table:
            self.table = db.define_table(self.tablename,
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
                            # apply this ACL to all record regardless
                            # of the realm entity
                            Field("unrestricted", "boolean",
                                  default=False),
                            migrate=migrate,
                            fake_migrate=fake_migrate,
                            *(s3_uid()+s3_timestamp()+s3_deletion_status()))

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

        if "permissions" in current.response.s3:
            del current.response.s3["permissions"]

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
    def get_owners(self, table, record):
        """
            Get the entity/group/user owning a record

            @param table: the table
            @param record: the record ID (or the Row, if already loaded)

            @note: if passing a Row, it must contain all available ownership
                   fields (id, owned_by_user, owned_by_group, realm_entity),
                   otherwise the record will be re-loaded by this function.

            @returns: tuple of (realm_entity, owner_group, owner_user)
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

            @returns: True if the current user owns the record, else False
        """

        user_id = None
        sr = self.auth.get_system_roles()

        if self.auth.user is not None:
            user_id = self.auth.user.id

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
            if self.auth.s3_session_owns(table, record_id):
                # Session owns record
                return True
            else:
                return False

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
            realms = self.auth.user.realms
            roles = [sr.ANONYMOUS]
            append = roles.append
            for r in realms:
                realm = realms[r]
                if realm is None or realm_entity in realm:
                    append(r)

        # Ownership based on user role
        if owner_group and owner_group in roles:
            return True
        else:
            return False

    # -------------------------------------------------------------------------
    def owner_query(self, table, user, use_realm=True, no_realm=[]):
        """
            Returns a query to select the records in table owned by user

            @param table: the table
            @param user: the current auth.user (None for not authenticated)
            @param use_realm: use realms
            @param no_realm: don't include these entities in role realms
            @returns: a web2py Query instance, or None if no query
                      can be constructed
        """

        OUSR = "owned_by_user"
        OGRP = "owned_by_group"
        OENT = "realm_entity"

        query = None
        if user is None:
            # Session ownership?
            if hasattr(table, "_tablename"):
                tablename = table._tablename
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

            # Public record query
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

            if query is not None and public is not None:
                query |= public

            # Group ownerships
            if OGRP in table.fields:
                any_entity = []
                g = None
                for group_id in user.realms:
                    realm = user.realms[group_id]
                    if realm is None or not use_realm:
                        any_entity.append(group_id)
                        continue
                    realm = [e for e in realm if e not in no_realm]
                    if realm:
                        q = (table[OGRP] == group_id) & (table[OENT].belongs(realm))
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
    def realm_query(self, table, entities):
        """
            Returns a query to select the records owned by one of the
            entities.

            @param table: the table
            @param entities: list of entities
            @returns: a web2py Query instance, or None if no query
                      can be constructed
        """

        ANY = "ANY"
        OENT = "realm_entity"

        if ANY in entities:
            return None
        elif not entities:
            return None
        elif OENT in table.fields:
            public = (table[OENT] == None)
            if len(entities) == 1:
                return (table[OENT] == entities[0]) | public
            else:
                return (table[OENT].belongs(entities)) | public
        return None

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
            tables = settings.get_auth_record_approval_required_for()
            if tables is not None:
                table = table._tablename if type(table) is Table else table
                if table in tables:
                    return True
                else:
                    return False
            elif current.s3db.get_config(table, "requires_approval"):
                return True
            else:
                return False
        else:
            return False

    # -------------------------------------------------------------------------
    @classmethod
    def set_default_approver(cls, table):
        """
            Set the default approver for new records in table

            @param table: the table
        """

        auth = current.auth
        APPROVER = "approved_by"

        if APPROVER in table:
            approver = table[APPROVER]
            if auth.override:
                approver.default = 0
            elif auth.s3_logged_in() and \
                 auth.s3_has_permission("approve", table):
                approver.default = auth.user.id
            else:
                approver.default = None
        return

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

        # Multiple methods?
        if isinstance(method, (list, tuple)):
            query = None
            for m in method:
                if self.has_permission(m, c=c, f=f, t=t, record=record):
                    return True
            return False
        else:
            method = [method]

        if record == 0:
            record = None
        _debug("\nhas_permission('%s', c=%s, f=%s, t=%s, record=%s)" % \
               ("|".join(method),
                c or current.request.controller,
                f or current.request.function,
                t, record))

        # Auth override, system roles and login
        auth = self.auth
        if self.auth.override:
            _debug("==> auth.override")
            _debug("*** GRANTED ***")
            return True
        sr = auth.get_system_roles()
        logged_in = auth.s3_logged_in()

        # Required ACL
        racl = self.required_acl(method)
        _debug("==> required ACL: %04X" % racl)

        # Get realms and delegations
        if not logged_in:
            realms = Storage({sr.ANONYMOUS:None})
            delegations = Storage()
        else:
            realms = auth.user.realms
            delegations = auth.user.delegations

        # Administrators have all permissions
        if sr.ADMIN in realms:
            _debug("==> user is ADMIN")
            _debug("*** GRANTED ***")
            return True

        if not self.use_cacls:
            _debug("==> simple authorization")
            # Fall back to simple authorization
            if logged_in:
                _debug("*** GRANTED ***")
                return True
            else:
                if self.page_restricted(c=c, f=f):
                    permitted = racl == self.READ
                else:
                    _debug("==> unrestricted page")
                    permitted = True
                if permitted:
                    _debug("*** GRANTED ***")
                else:
                    _debug("*** DENIED ***")
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

        # Fall back to current request
        c = c or self.controller
        f = f or self.function

        response = current.response
        key = "%s/%s/%s/%s/%s" % (method, c, f, t, record)
        if "permissions" not in response.s3:
            response.s3.permissions = Storage()
        if key in response.s3.permissions:
            permitted = response.s3.permissions[key]
            if permitted is None:
                pass
            elif permitted:
                _debug("*** GRANTED (cached) ***")
            else:
                _debug("*** DENIED (cached) ***")
            return response.s3.permissions[key]

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
            _debug("==> no ACLs defined for this case")
            permitted = True
        elif not acls:
            _debug("==> no applicable ACLs")
            permitted = False
        else:
            if entity:
                if entity in acls:
                    uacl, oacl = acls[entity]
                elif "ANY" in acls:
                    uacl, oacl = acls["ANY"]
                else:
                    _debug("==> Owner entity outside realm")
                    permitted = False
            else:
                uacl, oacl = self.most_permissive(acls.values())

            _debug("==> uacl: %04X, oacl: %04X" % (uacl, oacl))

            if permitted is None:
                if uacl & racl == racl:
                    permitted = True
                elif oacl & racl == racl:
                    if is_owner and record:
                        _debug("==> User owns the record")
                    elif record:
                        _debug("==> User does not own the record")
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
                    raise AttributeError("undefined table %s" % tablename)
            else:
                table = t
            if "approved_by" in table.fields:

                approval_methods = ("approve", "review", "reject")
                access_approved = not all([m in approval_methods for m in method])
                access_unapproved = any([m in method for m in approval_methods])

                if access_unapproved:
                    if not access_approved:
                        permitted = self.unapproved(table, record)
                        if not permitted:
                            _debug("==> Record already approved")
                else:
                    permitted = self.approved(table, record) or \
                                self.is_owner(table, record, owners, strict=True)
                    if not permitted:
                        _debug("==> Record not approved")
                        _debug("==> is owner: %s" % is_owner)
            else:
                # Approval not possible for this table => no change
                pass

        if permitted:
            _debug("*** GRANTED ***")
        else:
            _debug("*** DENIED ***")

        response.s3.permissions[key] = permitted
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
                                       default = error)

        if not isinstance(method, (list, tuple)):
            method = [method]

        _debug("\naccessible_query(%s, '%s')" % (table, ",".join(method)))

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
            _debug("==> auth.override")
            _debug("*** ALL RECORDS ***")
            return ALL_RECORDS

        sr = auth.get_system_roles()
        logged_in = auth.s3_logged_in()

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
            user_id = user.id if user is not None else None
            ALL_RECORDS = ((table.approved_by != None) | \
                           (table.owned_by_user == user_id))

        # Administrators have all permissions
        if sr.ADMIN in realms:
            _debug("==> user is ADMIN")
            _debug("*** ALL RECORDS ***")
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

        # Required ACL
        racl = self.required_acl(method)
        _debug("==> required permissions: %04X" % racl)

        # Use ACLs?
        if not self.use_cacls:
            _debug("==> simple authorization")
            # Fall back to simple authorization
            if logged_in:
                _debug("*** ALL RECORDS ***")
                return ALL_RECORDS
            else:
                permitted = racl == self.READ
                if permitted:
                    _debug("*** ALL RECORDS ***")
                    return ALL_RECORDS
                else:
                    _debug("*** ACCESS DENIED ***")
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
            _debug("==> no ACLs defined for this case")
            _debug("*** ALL RECORDS ***")
            return ALL_RECORDS
        elif not acls:
            _debug("==> no applicable ACLs")
            _debug("*** ACCESS DENIED ***")
            return NO_RECORDS

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

        OENT = "realm_entity"

        if "ANY" in uacls:
            _debug("==> permitted for any records")
            query = ALL_RECORDS
            check_owner_acls = False

        elif uacls:
            query = self.realm_query(table, uacls)
            if query is None:
                _debug("==> permitted for any records")
                query = ALL_RECORDS
                check_owner_acls = False
            else:
                _debug("==> permitted for records owned by entities %s" % str(uacls))
                no_realm = uacls

        if check_owner_acls:

            use_realm = "ANY" not in oacls
            owner_query = self.owner_query(table, user, use_realm=use_realm, no_realm=no_realm)

            if owner_query is not None:
                _debug("==> permitted for owned records (limit to realms=%s)" % use_realm)
                if query is not None:
                    query |= owner_query
                else:
                    query = owner_query
            elif use_realm:
                _debug("==> permitted for any records owned by entities %s" % str(uacls+oacls))
                query = self.realm_query(table, uacls+oacls)

            if query is not None and requires_approval:
                base_filter = None if approved and unapproved else \
                              UNAPPROVED if unapproved else APPROVED
                if base_filter is not None:
                    query = base_filter & query

        # Fallback
        if query is None:
            query = NO_RECORDS

        _debug("*** Accessible Query ***")
        _debug(str(query))
        return query

    # -------------------------------------------------------------------------
    def accessible_url(self,
                       c=None,
                       f=None,
                       p=None,
                       t=None,
                       a=None,
                       args=[],
                       vars={},
                       anchor="",
                       extension=None,
                       env=None):
        """
            Return a URL only if accessible by the user, otherwise False

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
            # non-HTML request => raise proper HTTP error
            if self.auth.s3_logged_in():
                raise HTTP(403, body=self.INSUFFICIENT_PRIVILEGES)
            else:
                raise HTTP(401, body=self.AUTHENTICATION_REQUIRED)

    # -------------------------------------------------------------------------
    # ACL Lookup
    # -------------------------------------------------------------------------
    def applicable_acls(self, racl,
                        realms=None,
                        delegations=None,
                        c=None,
                        f=None,
                        t=None,
                        entity=[]):
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

            @returns: None for no ACLs defined (allow),
                      [] for no ACLs applicable (deny),
                      or list of applicable ACLs
        """

        db = current.db
        table = self.table

        gtable = self.auth.settings.table_group

        if not self.use_cacls:
            # We do not use ACLs at all (allow all)
            return None
        else:
            acls = Storage()

        c = c or self.controller
        f = f or self.function
        if self.page_restricted(c=c, f=f):
            page_restricted = True
        else:
            page_restricted = False

        # Get all roles
        if realms:
            roles = realms.keys()
            if delegations:
                roles += [d for d in delegations if d not in roles]
        else:
            # No roles available (deny all)
            return acls

        # Base query
        query = (table.deleted != True) & \
                (table.group_id.belongs(roles))

        # Page ACLs
        if page_restricted:
            q = (table.function == None)
            if f and self.use_facls:
                q = (q | (table.function == f))
            q &= (table.controller == c)
        else:
            q = None

        # Table ACLs
        table_restricted = False
        if t and self.use_tacls:
            tq = (table.controller == None) & \
                 (table.function == None) & \
                 (table.tablename == t)
            if q:
                q = q | tq
            else:
                q = tq
            any_acl = db((table.deleted != True) & tq).select(limitby=(0, 1))
            table_restricted = len(any_acl) > 0

        # Retrieve the ACLs
        if q:
            query &= q
            query &= (table.group_id == gtable.id)
            rows = db(query).select(gtable.id, table.ALL)
        else:
            rows = []

        # Cascade ACLs
        ANY = "ANY"

        ALL = (self.ALL, self.ALL)
        NONE = (self.NONE, self.NONE)

        atn = table._tablename
        gtn = gtable._tablename

        use_facls = self.use_facls
        def rule_type(r):
            if rule.controller is not None:
                if rule.function is None:
                    return "c"
                elif use_facls:
                    return "f"
            elif rule.tablename is not None:
                return "t"
            return None

        most_permissive = lambda x, y: (x[0] | y[0], x[1] | y[1])
        most_restrictive = lambda x, y: (x[0] & y[0], x[1] & y[1])

        # Realms
        delegation_rows = []
        append_delegation = delegation_rows.append
        for row in rows:

            # Get the assigning entities
            group_id = row[gtn].id
            if group_id in delegations:
                append_delegation(row)
            if group_id not in realms:
                continue
            elif self.entity_realm:
                entities = realms[group_id]
            else:
                entities = None

            # Get the rule type
            rule = row[atn]
            rtype = rule_type(rule)
            if rtype is None:
                continue

            # Resolve the realm
            if rule.unrestricted:
                entities = [ANY]
            elif entities is None:
                if rule.entity is not None:
                    entities = [rule.entity]
                else:
                    entities = [ANY]

            # Merge the ACL
            acl = (rule["uacl"], rule["oacl"])
            for e in entities:
                if e not in acls:
                    acls[e] = Storage({rtype:acl})
                elif rtype in acls[e]:
                    acls[e][rtype] = most_permissive(acls[e][rtype], acl)
                else:
                    acls[e][rtype] = acl

        if ANY in acls:
            default = Storage(acls[ANY])
        else:
            default = None

        # Delegations
        if self.delegations:
            for row in delegation_rows:

                # Get the rule type
                rule = row[atn]
                rtype = rule_type(rule)
                if rtype is None:
                    continue

                # Get the delegation realms
                group_id = row[gtn].id
                if group_id not in delegations:
                    continue
                else:
                    drealms = delegations[group_id]

                acl = (rule["uacl"], rule["oacl"])

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
                        dacls = Storage(acls[receiver])
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
                            for t in ("c", "f", "t"):
                                if t in acls[e]:
                                    if t in dacls:
                                        dacls[t] = most_restrictive(dacls[t], acls[e][t])
                                    else:
                                        dacls[t] = acls[e][t]
                        acls[e] = dacls

        acl = acls[ANY] or Storage()

        # Default page ACL
        if "c" in acl:
            if "f" in acl:
                default_page_acl = acl["f"]
            else:
                default_page_acl = acl["c"]
        elif page_restricted:
            default_page_acl = NONE
        else:
            default_page_acl = ALL

        # Default table ACL
        if "t" in acl:
            default_table_acl = acl["t"]
        elif table_restricted:
            default_table_acl = default_page_acl
        else:
            default_table_acl = ALL

        # Fall back to default page acl
        if not acls and not (t and self.use_tacls):
            acls[ANY] = Storage(c=default_page_acl)


        # Order by precedence
        result = Storage()
        for e in acls:
            # Skip irrelevant ACLs
            if entity and e != entity and e != ANY:
                continue

            acl = acls[e]

            # Get the page ACL
            if "f" in acl:
                page_acl = acl["f"]
            elif "c" in acl:
                page_acl = acl["c"]
            elif page_restricted:
                page_acl = NONE
            else:
                page_acl = ALL
            page_acl = most_permissive(default_page_acl, page_acl)

            # Get the table ACL
            if "t" in acl:
                table_acl = acl["t"]
            elif table_restricted:
                table_acl = page_acl
            else:
                table_acl = ALL
            table_acl = most_permissive(default_table_acl, table_acl)

            # Merge
            acl = most_restrictive(page_acl, table_acl)

            # Include ACL if relevant
            if acl[0] & racl == racl or acl[1] & racl == racl:
                result[e] = acl

        #for pe in result:
            #print "ACL for PE %s: %04X %04X" % (pe, result[pe][0], result[pe][1])

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

        modules = current.deployment_settings.modules

        page = "%s/%s" % (c, f)
        if page in self.unrestricted_pages:
            return False
        elif c not in modules or \
             c in modules and not modules[c].restricted:
            return False
        return True

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
            if sr.ADMIN in roles or sr.EDITOR in roles:
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
            current.response.s3.permissions = Storage()
            return
        try:
            permissions = current.response.s3.permissions
        except:
            return
        if not permissions:
            return

        if hasattr(table, "_tablename"):
            tablename = table._tablename
        else:
            tablename = table

        for key in list(permissions.keys()):
            r = key.split("/")
            if len(r) > 1 and r[-2] == tablename:
                if record_id is None or \
                   record_id is not None and r[-1] == str(record_id):
                    del permissions[key]
        return

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

        db = current.db
        if tablename in db:
            self.table = db[tablename]
        else:
            self.table = None
        if not self.table:
            self.table = db.define_table(tablename,
                            Field("timestmp", "datetime"),
                            Field("person", "integer"),
                            Field("operation"),
                            Field("tablename"),
                            Field("record", "integer"),
                            Field("representation"),
                            Field("old_value", "text"),
                            Field("new_value", "text"),
                            migrate=migrate,
                            fake_migrate=fake_migrate)
        session = current.session
        self.auth = session.auth
        if session.auth and session.auth.user:
            self.user = session.auth.user.id
        else:
            self.user = None

        self.diff = None

    # -------------------------------------------------------------------------
    def __call__(self, operation, prefix, name,
                 form=None,
                 record=None,
                 representation="unknown"):
        """
            Audit

            @param operation: Operation to log, one of
                "create", "update", "read", "list" or "delete"
            @param prefix: the module prefix of the resource
            @param name: the name of the resource (without prefix)
            @param form: the form
            @param record: the record ID
            @param representation: the representation format
        """

        settings = current.deployment_settings

        audit_read = settings.get_security_audit_read()
        audit_write = settings.get_security_audit_write()

        if not audit_read and not audit_write:
            return True

        #import sys
        #print >> sys.stderr, "Audit %s: %s_%s record=%s representation=%s" % \
                             #(operation, prefix, name, record, representation)

        now = datetime.datetime.utcnow()
        db = current.db
        table = self.table
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

        if operation in ("list", "read"):
            if audit_read:
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation)

        elif operation in ("create", "update"):
            if audit_write:
                if form:
                    record = form.vars.id
                    new_value = ["%s:%s" % (var, str(form.vars[var]))
                                 for var in form.vars]
                else:
                    new_value = []
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation,
                             new_value = new_value)
                self.diff = None

        elif operation == "delete":
            if audit_write:
                query = db[tablename].id == record
                row = db(query).select(limitby=(0, 1)).first()
                old_value = []
                if row:
                    old_value = ["%s:%s" % (field, row[field])
                                 for field in row]
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation,
                             old_value = old_value)
                self.diff = None

        return True

# =============================================================================
class S3RoleManager(S3Method):
    """ REST Method to manage ACLs (Role Manager UI for administrators) """

    # Controllers to hide from the permissions matrix
    HIDE_CONTROLLER = ("admin", "default")

    # Roles to hide from the permissions matrix
    # @todo: deprecate
    HIDE_ROLES = []

    # Undeletable roles
    # @todo: deprecate
    PROTECTED_ROLES = (1, 2, 3, 4, 5)

    controllers = Storage()

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply role manager
        """

        method = self.method
        manager = current.manager

        if method == "list":
            output = self._list(r, **attr)
        elif method in ("read", "create", "update"):
            output = self._edit(r, **attr)
        elif method == "delete":
            output = self._delete(r, **attr)
        elif method == "roles" and r.name == "user":
            output = self._roles(r, **attr)
        elif method == "users":
            output = self._users(r, **attr)
        else:
            r.error(405, manager.ERROR.BAD_METHOD)

        if r.http == "GET" and method not in ("create", "update", "delete"):
            current.session.s3.cancel = r.url()
        return output

    # -------------------------------------------------------------------------
    def _list(self, r, **attr):
        """
            List roles/permissions
        """

        if r.id:
            return self._edit(r, **attr)

        output = dict()

        if r.interactive:

            T = current.T
            db = current.db
            response = current.response
            resource = self.resource
            manager = current.manager
            auth = manager.auth
            options = auth.permission.PERMISSION_OPTS
            NONE = auth.permission.NONE
            vars = self.request.get_vars
            table = self.table

            # Show permission matrix?
            show_matrix = vars.get("matrix", False) and True

            # Title and subtitle
            output.update(title = T("List of Roles"))

            # System roles
            query = ((table.deleted != True) & \
                     (table.system == True))
            rows = db(query).select(table.id)
            system_roles = [row.id for row in rows]

            # Protected roles
            query = ((table.deleted != True) & \
                     (table.protected == True))
            rows = db(query).select(table.id)
            protected_roles = [row.id for row in rows]

            # Filter out hidden roles
            resource.add_filter((~(table.id.belongs(self.HIDE_ROLES))) &
                                (table.hidden != True))
            resource.load()

            # Get active controllers
            controllers = [c for c in self.controllers.keys()
                             if c not in self.HIDE_CONTROLLER]

            # ACLs
            acl_table = auth.permission.table
            query = resource.get_query()
            query = query & \
                    (acl_table.group_id == self.table.id) & \
                    (acl_table.deleted != True)
            records = db(query).select(acl_table.ALL)

            any = "ANY"
            acls = Storage({any: Storage()})
            for acl in records:
                c = acl.controller
                f = acl.function
                if not f:
                    f = any
                role_id = acl.group_id
                if f not in acls:
                    acls[f] = Storage()
                if c not in acls[f]:
                    acls[f][c] = Storage()
                acls[f][c][str(role_id)] = Storage(oacl = acl.oacl,
                                                   uacl = acl.uacl)
            for c in controllers:
                if c not in acls[any]:
                    acls[any][c] = Storage()
                if any not in acls[any][c]:
                    acls[any][c][any] = Storage(oacl = NONE,
                                                uacl = NONE)

            # Table header
            columns = []
            headers = [TH("ID"), TH(T("Role"))]
            if show_matrix:
                for c in controllers:
                    if c in acls[any]:
                        headers.append(TH(self.controllers[c].name_nice))
                        columns.append((c, any))
                    for f in acls:
                        if f != any and c in acls[f]:
                            headers.append(TH(self.controllers[c].name_nice,
                                              BR(), f))
                            columns.append((c, f))
            else:
                headers += [TH(T("Description"))]
            thead = THEAD(TR(headers))

            # Table body
            trows = []
            i = 1
            for role in resource:

                role_id = role.id
                role_name = role.role
                role_desc = role.description

                edit_btn = A(T("Edit"),
                             _href=URL(c="admin", f="role",
                                       args=[role_id], vars=vars),
                             _class="action-btn")

                users_btn = A(T("Users"),
                              _href=URL(c="admin", f="role",
                                        args=[role_id, "users"]),
                              _class="action-btn")

                if role.protected:
                    tdata = [TD(edit_btn,
                                XML("&nbsp;"),
                                users_btn),
                                TD(role_name)]
                else:
                    delete_btn = A(T("Delete"),
                                _href=URL(c="admin", f="role",
                                          args=[role_id, "delete"],
                                          vars=vars),
                                _class="delete-btn")
                    tdata = [TD(edit_btn,
                                XML("&nbsp;"),
                                users_btn,
                                XML("&nbsp;"),
                                delete_btn),
                             TD(role_name)]

                if show_matrix:
                    # Display the permission matrix
                    for c, f in columns:
                        if f in acls and c in acls[f] and \
                           str(role_id) in acls[f][c]:
                            oacl = acls[f][c][str(role_id)].oacl
                            uacl = acls[f][c][str(role_id)].uacl
                        else:
                            oacl = acls[any][c][any].oacl
                            uacl = acls[any][c][any].oacl

                        oaclstr = ""
                        uaclstr = ""
                        for o in options:
                            if o == NONE and oacl == NONE:
                                oaclstr = "%s%s" % (oaclstr, options[o][0])
                            elif oacl and oacl & o:
                                oaclstr = "%s%s" % (oaclstr, options[o][0])
                            else:
                                oaclstr = "%s-" % oaclstr
                            if o == NONE and uacl == NONE:
                                uaclstr = "%s%s" % (uaclstr, options[o][0])
                            elif uacl and uacl & o:
                                uaclstr = "%s%s" % (uaclstr, options[o][0])
                            else:
                                uaclstr = "%s-" % uaclstr

                        values = "%s (%s)" % (uaclstr, oaclstr)
                        tdata += [TD(values, _nowrap="nowrap")]
                else:
                    # Display role descriptions
                    tdata += [TD(role_desc)]

                _class = i % 2 and "even" or "odd"
                trows.append(TR(tdata, _class=_class))
            tbody = TBODY(trows)

            # Aggregate list
            items = TABLE(thead, tbody, _id="list", _class="dataTable display")
            output.update(items=items, sortby=[[1, "asc"]])

            # Add-button
            add_btn = A(T("Add Role"), _href=URL(c="admin", f="role",
                                                 args=["create"]),
                                                 _class="action-btn")
            output.update(add_btn=add_btn)

            response.view = "admin/role_list.html"
            s3 = response.s3
            s3.actions = []
            s3.no_sspag = True

        elif r.representation == "xls":
            # Not implemented yet
            r.error(501, manager.ERROR.BAD_FORMAT)

        else:
            r.error(501, manager.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def _edit(self, r, **attr):
        """
            Create/update role
        """

        output = dict()

        request = self.request
        session = current.session
        manager = current.manager
        db = current.db
        T = current.T

        crud_settings = manager.s3.crud

        CACL = T("Application Permissions")
        FACL = T("Function Permissions")
        TACL = T("Table Permissions")

        CANCEL = T("Cancel")

        auth = manager.auth
        permission = auth.permission
        acl_table = permission.table
        NONE = permission.NONE

        if r.interactive:

            # Get the current record (if any)
            if r.record:
                output.update(title=T("Edit Role"))
                role_id = r.record.id
                role_name = r.record.role
                role_desc = r.record.description
            else:
                output.update(title=T("New Role"))
                role_id = None
                role_name = None
                role_desc = None

            # Form helpers ----------------------------------------------------
            mandatory = lambda l: DIV(l, XML("&nbsp;"),
                                      SPAN("*", _class="req"))
            from s3validators import IS_ACL
            acl_table.oacl.requires = IS_ACL(permission.PERMISSION_OPTS)
            acl_table.uacl.requires = IS_ACL(permission.PERMISSION_OPTS)
            from s3widgets import S3ACLWidget
            acl_widget = lambda f, n, v: \
                            S3ACLWidget.widget(acl_table[f], v, _id=n, _name=n,
                                               _class="acl-widget")
            formstyle = crud_settings.formstyle


            using_default = SPAN(T("using default"), _class="using-default")
            delete_acl = lambda _id: _id is not None and \
                                     A(T("Delete"),
                                       _href = URL(c="admin", f="acl",
                                                   args=[_id, "delete"],
                                                   vars=dict(_next=r.url())),
                                       _class = "delete-btn") or using_default
            new_acl = SPAN(T("new ACL"), _class="new-acl")

            # Role form -------------------------------------------------------
            form_rows = formstyle("role_name",
                                  mandatory("%s:" % T("Role Name")),
                                  INPUT(value=role_name,
                                        _name="role_name",
                                        _type="text",
                                        requires=IS_NOT_IN_DB(db,
                                            "auth_group.role",
                                            allowed_override=[role_name])),
                                  "") + \
                        formstyle("role_desc",
                                  "%s:" % T("Description"),
                                  TEXTAREA(value=role_desc,
                                           _name="role_desc",
                                           _rows="4"),
                                  "")
            key_row = DIV(T("* Required Fields"), _class="red")
            role_form = DIV(TABLE(form_rows), key_row, _id="role-form")

            # Prepare ACL forms -----------------------------------------------
            any = "ANY"
            controllers = [c for c in self.controllers.keys()
                             if c not in self.HIDE_CONTROLLER]
            ptables = []
            query = (acl_table.deleted != True) & \
                    (acl_table.group_id == role_id)
            records = db(query).select()

            acl_forms = []

            # Relevant ACLs
            acls = Storage()
            for acl in records:
                if acl.controller in controllers:
                    if acl.controller not in acls:
                        acls[acl.controller] = Storage()
                    if not acl.function:
                        f = any
                    else:
                        if permission.use_facls:
                            f = acl.function
                        else:
                            continue
                    acls[acl.controller][f] = acl

            # Controller ACL table --------------------------------------------

            # Table header
            thead = THEAD(TR(TH(T("Application")),
                             TH(T("All Records")),
                             TH(T("Owned Records")),
                             TH()))

            # Rows for existing ACLs
            form_rows = []
            i = 0
            for c in controllers:
                default = Storage(id = None,
                                  controller = c,
                                  function = any,
                                  tablename = None,
                                  uacl = NONE,
                                  oacl = NONE)
                if c in acls:
                    acl_list = acls[c]
                    if any not in acl_list:
                        acl_list[any] = default
                else:
                    acl_list = Storage(ANY=default)
                acl = acl_list[any]
                _class = i % 2 and "even" or "odd"
                i += 1
                uacl = NONE
                oacl = NONE
                if acl.oacl is not None:
                    oacl = acl.oacl
                if acl.uacl is not None:
                    uacl = acl.uacl
                _id = acl.id
                delete_btn = delete_acl(_id)
                n = "%s_%s_ANY_ANY" % (_id, c)
                uacl = acl_widget("uacl", "acl_u_%s" % n, uacl)
                oacl = acl_widget("oacl", "acl_o_%s" % n, oacl)
                cn = self.controllers[c].name_nice
                form_rows.append(TR(TD(cn),
                                    TD(uacl),
                                    TD(oacl),
                                    TD(delete_btn),
                                    _class=_class))

            # Tabs
            tabs = [SPAN(A(CACL), _class="tab_here")]
            if permission.use_facls:
                _class = permission.use_tacls and \
                         "tab_other" or "tab_last"
                tabs.append(SPAN(A(FACL, _class="facl-tab"), _class=_class))
            if permission.use_tacls:
                tabs.append(SPAN(A(TACL, _class="tacl-tab"),
                                 _class="tab_last"))

            acl_forms.append(DIV(DIV(tabs, _class="tabs"),
                                     TABLE(thead, TBODY(form_rows)),
                                     _id="controller-acls"))

            # Function ACL table ----------------------------------------------
            if permission.use_facls:

                # Table header
                thead = THEAD(TR(TH(T("Application")),
                                 TH(T("Function")),
                                 TH(T("All Records")),
                                 TH(T("Owned Records")),
                                 TH()))

                # Rows for existing ACLs
                form_rows = []
                i = 0
                for c in controllers:
                    if c in acls:
                        acl_list = acls[c]
                    else:
                        continue
                    keys = acl_list.keys()
                    keys.sort()
                    for f in keys:
                        if f == any:
                            continue
                        acl = acl_list[f]
                        _class = i % 2 and "even" or "odd"
                        i += 1
                        uacl = NONE
                        oacl = NONE
                        if acl.oacl is not None:
                            oacl = acl.oacl
                        if acl.uacl is not None:
                            uacl = acl.uacl
                        _id = acl.id
                        delete_btn = delete_acl(_id)
                        n = "%s_%s_%s_ANY" % (_id, c, f)
                        uacl = acl_widget("uacl", "acl_u_%s" % n, uacl)
                        oacl = acl_widget("oacl", "acl_o_%s" % n, oacl)
                        cn = self.controllers[c].name_nice
                        form_rows.append(TR(TD(cn),
                                            TD(f),
                                            TD(uacl),
                                            TD(oacl),
                                            TD(delete_btn),
                                            _class=_class))

                # Row to enter a new controller ACL
                _class = i % 2 and "even" or "odd"
                c_opts = [OPTION("", _value=None, _selected="selected")] + \
                         [OPTION(self.controllers[c].name_nice,
                                 _value=c) for c in controllers]
                c_select = SELECT(_name="new_controller", *c_opts)

                form_rows.append(TR(
                    TD(c_select),
                    TD(INPUT(_type="text", _name="new_function")),
                    TD(acl_widget("uacl", "new_c_uacl", NONE)),
                    TD(acl_widget("oacl", "new_c_oacl", NONE)),
                    TD(new_acl), _class=_class))

                # Tabs to change to the other view
                tabs = [SPAN(A(CACL, _class="cacl-tab"),
                             _class="tab_other"),
                        SPAN(A(FACL), _class="tab_here")]
                if permission.use_tacls:
                    tabs.append(SPAN(A(TACL, _class="tacl-tab"),
                                     _class="tab_last"))

                acl_forms.append(DIV(DIV(tabs, _class="tabs"),
                                         TABLE(thead, TBODY(form_rows)),
                                         _id="function-acls"))

            # Table ACL table -------------------------------------------------

            if permission.use_tacls:
                query = (acl_table.deleted != True) & \
                        (acl_table.tablename != None)
                tacls = db(query).select(acl_table.tablename, distinct=True)
                if tacls:
                    ptables = [acl.tablename for acl in tacls]
                # Relevant ACLs
                acls = dict([(acl.tablename, acl) for acl in records
                                                if acl.tablename in ptables])

                # Table header
                thead = THEAD(TR(TH(T("Tablename")),
                                 TH(T("All Records")),
                                 TH(T("Owned Records")),
                                 TH()))

                # Rows for existing table ACLs
                form_rows = []
                i = 0
                for t in ptables:
                    _class = i % 2 and "even" or "odd"
                    i += 1
                    uacl = NONE
                    oacl = NONE
                    _id = None
                    if t in acls:
                        acl = acls[t]
                        if acl.uacl is not None:
                            uacl = acl.uacl
                        if acl.oacl is not None:
                            oacl = acl.oacl
                        _id = acl.id
                    delete_btn = delete_acl(_id)
                    n = "%s_ANY_ANY_%s" % (_id, t)
                    uacl = acl_widget("uacl", "acl_u_%s" % n, uacl)
                    oacl = acl_widget("oacl", "acl_o_%s" % n, oacl)
                    form_rows.append(TR(TD(t),
                                        TD(uacl),
                                        TD(oacl),
                                        TD(delete_btn),
                                        _class=_class))

                # Row to enter a new table ACL
                _class = i % 2 and "even" or "odd"
                # @todo: find a better way to provide a selection of tables
                #all_tables = [t._tablename for t in current.db]
                form_rows.append(TR(
                    TD(INPUT(_type="text", _name="new_table")),
                            # @todo: doesn't work with conditional models
                            #requires=IS_EMPTY_OR(IS_IN_SET(all_tables,
                                                           #zero=None,
                                        #error_message=T("Undefined Table"))))),
                    TD(acl_widget("uacl", "new_t_uacl", NONE)),
                    TD(acl_widget("oacl", "new_t_oacl", NONE)),
                    TD(new_acl), _class=_class))

                # Tabs
                tabs = [SPAN(A(CACL, _class="cacl-tab"),
                             _class="tab_other")]
                if permission.use_facls:
                    tabs.append(SPAN(A(FACL, _class="facl-tab"),
                                     _class="tab_other"))
                tabs.append(SPAN(A(TACL), _class="tab_here"))
                acl_forms.append(DIV(DIV(tabs, _class="tabs"),
                                     TABLE(thead, TBODY(form_rows)),
                                     _id="table-acls"))

            # Aggregate ACL Form ----------------------------------------------
            acl_form = DIV(acl_forms, _id="table-container")

            # Action row
            if session.s3.cancel:
                cancel = session.s3.cancel
            else:
                cancel = URL(c="admin", f="role",
                             vars=request.get_vars)
            action_row = DIV(INPUT(_type="submit", _value=T("Save")),
                             A(CANCEL, _href=cancel, _class="action-lnk"),
                             _id="action-row")

            # Complete form
            form = FORM(role_form, acl_form, action_row)

            # Append role_id
            if role_id:
                form.append(INPUT(_type="hidden",
                                  _name="role_id",
                                  value=role_id))

            # Process the form ------------------------------------------------
            if form.accepts(request.post_vars, session):
                vars = form.vars

                # Update the role
                role = Storage(role=vars.role_name, description=vars.role_desc)
                if r.record:
                    r.record.update_record(**role)
                    role_id = form.vars.role_id
                    session.confirmation = '%s "%s" %s' % (T("Role"),
                                                           role.role,
                                                           T("updated"))
                else:
                    role.uuid = uuid4()
                    role_id = self.table.insert(**role)
                    session.confirmation = '%s "%s" %s' % (T("Role"),
                                                           role.role,
                                                           T("created"))

                if role_id:
                    # Collect the ACLs
                    acls = Storage()
                    for v in vars:
                        if v[:4] == "acl_":
                            acl_type, name = v[4:].split("_", 1)
                            n = name.split("_", 3)
                            i, c, f, t = map(lambda item: \
                                             item != any and item or None, n)
                            if i.isdigit():
                                i = int(i)
                            else:
                                i = None
                            name = "%s_%s_%s" % (c, f, t)
                            if name not in acls:
                                acls[name] = Storage()
                            acls[name].update({"id": i,
                                               "group_id": role_id,
                                               "controller": c,
                                               "function": f,
                                               "tablename": t,
                                               "%sacl" % acl_type: vars[v]})
                    for v in ("new_controller", "new_table"):
                        if v in vars and vars[v]:
                            c = v == "new_controller" and \
                                     vars.new_controller or None
                            f = v == "new_controller" and \
                                     vars.new_function or None
                            t = v == "new_table" and vars.new_table or None
                            name = "%s_%s_%s" % (c, f, t)
                            x = v == "new_table" and "t" or "c"
                            uacl = vars["new_%s_uacl" % x]
                            oacl = vars["new_%s_oacl" % x]
                            if name not in acls:
                                acls[name] = Storage()
                            acls[name].update(group_id=role_id,
                                              controller=c,
                                              function=f,
                                              tablename=t,
                                              oacl=oacl,
                                              uacl=uacl)

                    # Save the ACLs
                    for acl in acls.values():
                        _id = acl.pop("id", None)
                        if _id:
                            query = (acl_table.deleted != True) & \
                                    (acl_table.id == _id)
                            db(query).update(**acl)
                        elif acl.oacl or acl.uacl:
                            _id = acl_table.insert(**acl)

                redirect(URL(f="role", vars=request.get_vars))

            output.update(form=form)
            if form.errors:
                if "new_table" in form.errors:
                    output.update(acl="table")
                elif "new_controller" in form.errors:
                    output.update(acl="function")
            current.response.view = "admin/role_edit.html"

        else:
            r.error(501, manager.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def _delete(self, r, **attr):
        """
            Delete role
        """

        session = current.session
        manager = current.manager
        request = self.request
        T = current.T

        auth = manager.auth

        if r.interactive:

            if r.record:
                role = r.record
                role_id = role.id
                role_name = role.role

                if role_id in self.PROTECTED_ROLES or \
                   role.protected or role.system:
                    session.error = '%s "%s" %s' % (T("Role"),
                                                    role_name,
                                                    T("cannot be deleted."))
                    redirect(URL(c="admin", f="role",
                                 vars=request.get_vars))
                else:
                    db = current.db
                    # Delete all ACLs for this role:
                    acl_table = auth.permission.table
                    query = (acl_table.deleted != True) & \
                            (acl_table.group_id == role_id)
                    db(query).update(deleted=True)
                    # Remove all memberships:
                    membership_table = db.auth_membership
                    query = (membership_table.deleted != True) & \
                            (membership_table.group_id == role_id)
                    db(query).update(deleted=True)
                    # Update roles in session:
                    session.s3.roles = [role
                                        for role in session.s3.roles
                                        if role != role_id]
                    # Remove role:
                    query = (self.table.deleted != True) & \
                            (self.table.id == role_id)
                    db(query).update(role=None,
                                     deleted=True)
                    # Confirmation:
                    session.confirmation = '%s "%s" %s' % (T("Role"),
                                                           role_name,
                                                           T("deleted"))
            else:
                session.error = T("No role to delete")
        else:
            r.error(501, manager.BAD_FORMAT)

        redirect(URL(c="admin", f="role", vars=request.get_vars))

    # -------------------------------------------------------------------------
    def _roles(self, r, **attr):

        T = current.T
        db = current.db
        auth = current.auth

        request = current.request
        session = current.session

        if auth.settings.username:
            username = "username"
        else:
            username = "email"

        output = dict()

        # Unrestrictable roles
        sr = auth.get_system_roles()
        unrestrictable = [sr.ADMIN, sr.ANONYMOUS, sr.AUTHENTICATED]

        if r.record:
            user = r.record
            user_id = r.id
            user_name = user[username]

            use_realms = auth.permission.entity_realm
            unassignable = [sr.ANONYMOUS, sr.AUTHENTICATED]
            if user_id == auth.user.id:
                # Users cannot remove their own ADMIN permission
                unassignable.append(sr.ADMIN)

            if r.representation == "html":

                arrow = TD(IMG(_src="/%s/static/img/arrow-turn.png" % request.application),
                           _style="text-align:center; vertical-align:middle; width:48px;")

                # Get current memberships
                mtable = auth.settings.table_membership
                gtable = auth.settings.table_group
                query = (mtable.deleted != True) & \
                        (mtable.user_id == user_id) & \
                        (gtable.deleted != True) & \
                        (mtable.group_id == gtable.id)
                rows = db(query).select(mtable.id,
                                        mtable.pe_id,
                                        gtable.id,
                                        gtable.role)
                entities = [row[mtable.pe_id] for row in rows]
                entity_repr = self._entity_represent(entities)
                assigned = [row[gtable.id] for row in rows]

                # Page Title
                title = "%s: %s" % (T("Roles of User"), user_name)

                # Remove-Form -------------------------------------------------

                # Subtitle
                rmvtitle = T("Roles currently assigned")
                trow = TR(TH(), TH("Role"))
                if use_realms:
                    trow.append(TH(T("For Entity")))
                thead = THEAD(trow)

                # Rows
                if rows:
                    i = 0
                    trows = []
                    remove = False
                    for row in rows:
                        group_id = row[gtable.id]
                        _class = i % 2 and "even" or "odd"
                        i += 1
                        trow = TR(_class=_class)

                        # Row selector
                        if group_id in unassignable:
                            trow.append(TD())
                        else:
                            trow.append(TD(INPUT(_type="checkbox",
                                                _name="d_%s" % row[mtable.id],
                                                _class="remove_item")))
                            remove = True

                        # Role
                        name = row[gtable.role]
                        trow.append(TD(name))

                        # Entity
                        if use_realms:
                            if row[gtable.id] in unrestrictable:
                                pe_id = 0
                            else:
                                pe_id = row[mtable.pe_id]
                            pe_repr = entity_repr[pe_id] or T("unknown")
                            trow.append(TD(pe_repr))
                        trows.append(trow)

                    # Remove button
                    if remove:
                        submit_row = TR(arrow,
                                        TD(INPUT(_id="submit_delete_button",
                                                _type="submit",
                                                _value=T("Remove"))))
                        if use_realms:
                            submit_row.append(TD())
                        trows.append(submit_row)

                    # Assemble form
                    tbody = TBODY(trows)
                    rmvform = FORM(DIV(TABLE(thead, tbody,
                                            _class="dataTable display"),
                                    _id="table-container"))
                else:
                    rmvform = FORM(DIV(T("No roles currently assigned to this user.")))

                # Process Remove-Form
                if rmvform.accepts(request.post_vars, session,
                                   formname="rmv_user_%s_roles" % user_id):
                    removed = 0
                    for opt in rmvform.vars:
                        if rmvform.vars[opt] == "on" and opt.startswith("d_"):
                            membership_id = opt[2:]
                            query = mtable.id == membership_id
                            row = db(query).select(mtable.user_id,
                                                   mtable.group_id,
                                                   mtable.pe_id,
                                                   limitby=(0, 1)).first()
                            if row:
                                if use_realms:
                                    pe_id = row.pe_id
                                else:
                                    pe_id = []
                                auth.s3_retract_role(row.user_id,
                                                     row.group_id,
                                                     for_pe=pe_id)
                                removed += 1
                    if removed:
                        session.confirmation = T("%s Roles of the user removed" % removed)
                        redirect(r.url())

                # Add form ----------------------------------------------------

                # Subtitle
                addtitle = T("Assign another Role")
                if use_realms:
                    help_txt = "(%s)" % T("Default Realm = All Entities the User is a Staff Member of")
                else:
                    help_txt = ""

                trow = TR(TH("Role", _colspan="2"))
                if use_realms:
                    trow.append(TH(T("For Entity")))
                thead = THEAD(trow)

                # Roles selector
                gtable = auth.settings.table_group
                query = (gtable.deleted != True) & \
                        (~(gtable.id.belongs(unassignable)))
                rows = db(query).select(gtable.id, gtable.role)
                select_grp = SELECT(OPTION(_value=None, _selected="selected"),
                                    _name="group_id")
                options = [(row.role, row.id)
                           for row in rows
                            if row.id not in unrestrictable or \
                               row.id not in assigned]
                options.sort()
                [select_grp.append(OPTION(role, _value=gid))
                 for role, gid in options]

                # Entity Selector
                if use_realms:
                    select_ent = self._entity_select()

                # Add button
                submit_btn = INPUT(_id="submit_add_button",
                                   _type="submit",
                                   _value=T("Add"))

                # Assemble form
                trow = TR(TD(select_grp, _colspan="2"), _class="odd")
                srow = TR(arrow, TD(submit_btn))
                if use_realms:
                    trow.append(TD(select_ent))
                    srow.append(TD())
                addform = FORM(DIV(TABLE(thead, TBODY(trow, srow),
                                         _class="dataTable display")))

                # Process Add-Form
                if addform.accepts(request.post_vars, session,
                                   formname="add_user_%s_roles" % user_id):
                    try:
                        group_id = int(addform.vars.group_id)
                    except ValueError:
                        group_id = None
                    pe_id = addform.vars.pe_id
                    if pe_id == "__NONE__" or not use_realms:
                        pe_id = None
                    if group_id in unrestrictable:
                        pe_id = 0
                    if group_id:
                        auth.s3_assign_role(user_id, group_id, for_pe=pe_id)
                        session.confirmation = T("Role assigned to User")
                        redirect(r.url())

                # Action links
                list_btn = A(T("Back to Users List"),
                             _href=URL(c="admin", f="user"),
                             _class="action-btn")
                add_btn = A(T("Create New Role"),
                            _href=URL(c="admin", f="role",
                                      args="create"),
                            _class="action-lnk")

                output = dict(title=title,
                              rmvtitle=rmvtitle,
                              rmvform=rmvform,
                              addtitle=addtitle,
                              help_txt=help_txt,
                              addform=addform,
                              list_btn=list_btn,
                              add_btn=add_btn)

                current.response.view = "admin/membership_manage.html"
            else:
                r.error(501, manager.BAD_FORMAT)

        else:
            r.error(404, self.resource.ERROR.BAD_RECORD)

        return output

    # -------------------------------------------------------------------------
    def _users(self, r, **attr):

        T = current.T
        db = current.db
        auth = current.auth

        request = current.request
        session = current.session

        if auth.settings.username:
            username = "username"
        else:
            username = "email"

        output = dict()

        # Unrestrictable roles
        sr = auth.get_system_roles()
        unrestrictable = [sr.ADMIN, sr.ANONYMOUS, sr.AUTHENTICATED]

        if r.record:
            group = r.record
            group_id = r.id
            group_role = group.role

            use_realms = auth.permission.entity_realm and \
                         group_id not in unrestrictable
            assignable = group_id not in [sr.ANONYMOUS, sr.AUTHENTICATED]

            if r.representation == "html":

                arrow = TD(IMG(_src="/%s/static/img/arrow-turn.png" % request.application),
                           _style="text-align:center; vertical-align:middle; width:48px;")

                # Get current memberships
                mtable = auth.settings.table_membership
                utable = auth.settings.table_user
                query = (mtable.deleted != True) & \
                        (mtable.group_id == group_id) & \
                        (utable.deleted != True) & \
                        (mtable.user_id == utable.id)
                if not use_realms:
                    query &= ((mtable.pe_id == None) | (mtable.pe_id == 0))
                rows = db(query).select(mtable.id,
                                        mtable.pe_id,
                                        utable.id,
                                        utable.first_name,
                                        utable.last_name,
                                        utable[username])
                entities = [row[mtable.pe_id] for row in rows]
                if use_realms:
                    entity_repr = self._entity_represent(entities)
                else:
                    entity_repr = Storage()
                assigned = [row[utable.id] for row in rows]

                # Page title
                title = "%s: %s" % (T("User with Role"), group_role)

                # Remove-Form -------------------------------------------------
                rmvtitle = T("Users with this Role")

                if assigned:

                    # Table Header
                    trow = TR()
                    if assignable:
                        trow.append(TH())
                    trow.append(TH(T("Name")))
                    trow.append(TH(T("Username")))
                    if use_realms:
                        trow.append(TH(T("For Entity")))
                    thead = THEAD(trow)

                    # Rows
                    i = 0
                    trows = []
                    remove = False
                    for row in rows:
                        _class = i % 2 and "even" or "odd"
                        i += 1
                        trow = TR(_class=_class)

                        # User cannot remove themselves from the ADMIN role
                        if row[utable.id] == auth.user.id and \
                           group_id == sr.ADMIN:
                            removable = False
                        else:
                            removable = True

                        # Row selector
                        if assignable and removable:
                            remove = True
                            trow.append(TD(INPUT(_type="checkbox",
                                                 _name="d_%s" % row[mtable.id],
                                                 _class="remove_item")))
                        else:
                            trow.append(TD())
                        # Name
                        name = "%s %s" % (row[utable.first_name],
                                          row[utable.last_name])
                        trow.append(TD(name))

                        # Username
                        uname = row[utable[username]]
                        trow.append(TD(uname))

                        # Entity
                        if use_realms:
                            pe_id = row[mtable.pe_id]
                            pe_repr = entity_repr[pe_id] or T("unknown")
                            trow.append(TD(pe_repr))

                        trows.append(trow)

                    # Remove button
                    if assignable and remove:
                        submit_row = TR(arrow,
                                        TD(INPUT(_id="submit_delete_button",
                                                _type="submit",
                                                _value=T("Remove"))),
                                        TD())
                        if use_realms:
                            submit_row.append(TD())
                        trows.append(submit_row)

                    # Assemble form
                    tbody = TBODY(trows)
                    rmvform = FORM(DIV(TABLE(thead, tbody,
                                             _class="dataTable display")))
                else:
                    rmvform = FORM(DIV(T("No users with this role at the moment.")))

                # Process Remove-Form
                if rmvform.accepts(request.post_vars, session,
                                   formname="rmv_role_%s_users" % group_id):
                    removed = 0
                    for opt in rmvform.vars:
                        if rmvform.vars[opt] == "on" and opt.startswith("d_"):
                            membership_id = opt[2:]
                            query = mtable.id == membership_id
                            row = db(query).select(mtable.user_id,
                                                   mtable.group_id,
                                                   mtable.pe_id,
                                                   limitby=(0, 1)).first()
                            if row:
                                auth.s3_retract_role(row.user_id,
                                                     row.group_id,
                                                     for_pe=row.pe_id)
                                removed += 1
                    if removed:
                        session.confirmation = T("%s Users removed from Role" % removed)
                        redirect(r.url())

                # Add-Form ----------------------------------------------------

                # Subtitle and help text
                addtitle = T("Assign Role to a User")
                if use_realms and assignable:
                    help_txt = "(%s)" % T("Default Realm = All Entities the User is a Staff Member of")
                else:
                    help_txt = ""

                # Form header
                trow = TR(TH(T("User"), _colspan="2"))
                if use_realms:
                    trow.append(TH(T("For Entity")))
                thead = THEAD(trow)

                # User selector
                utable = auth.settings.table_user
                query = (utable.deleted != True)
                if group_id in unrestrictable and assigned:
                    query &= (~(utable.id.belongs(assigned)))
                rows = db(query).select(utable.id,
                                        utable.first_name,
                                        utable.last_name,
                                        utable[username])
                if rows and assignable:
                    select_usr = SELECT(OPTION("",
                                            _value=None,
                                            _selected="selected"),
                                        _name="user_id")
                    options = [("%s (%s %s)" % (row[username],
                                                row.first_name,
                                                row.last_name),
                                row.id) for row in rows]
                    options.sort()
                    [select_usr.append(OPTION(name, _value=uid)) for name, uid in options]

                    # Entity selector
                    if use_realms:
                        select_ent = self._entity_select()

                    # Add button
                    submit_btn = INPUT(_id="submit_add_button",
                                       _type="submit",
                                       _value=T("Add"))



                    # Assemble form
                    trow = TR(TD(select_usr, _colspan="2"), _class="odd")
                    srow = TR(arrow,
                              TD(submit_btn))
                    if use_realms:
                        trow.append(TD(self._entity_select()))
                        srow.append(TD())
                    addform = FORM(DIV(TABLE(thead, TBODY(trow, srow),
                                             _class="dataTable display")))
                elif not assignable:
                    addform = FORM(DIV(T("This role can not be assigned to users.")))
                else:
                    addform = FORM(DIV(T("No further users can be assigned.")))

                # Process Add-form
                if addform.accepts(request.post_vars, session,
                                   formname="add_role_%s_users" % group_id):
                    pe_id = addform.vars.pe_id
                    if pe_id == "__NONE__":
                        pe_id = None
                    if group_id in unrestrictable:
                        pe_id = 0
                    user_id = addform.vars.user_id
                    if user_id:
                        auth.s3_assign_role(user_id, group_id, for_pe=pe_id)
                        session.confirmation = T("User added to Role")
                        redirect(r.url())

                # Action links
                list_btn = A(T("Back to Roles List"),
                             _href=URL(c="admin", f="role"),
                             _class="action-btn")
                if group_id != sr.ADMIN:
                    edit_btn = A(T("Edit Permissions for %s" % group_role),
                                 _href=URL(c="admin", f="role",
                                           args=[group_id]),
                                 _class="action-lnk")
                else:
                    edit_btn = ""
                add_btn = A(T("Create New User"),
                            _href=URL(c="admin", f="user",
                                      args="create"),
                            _class="action-lnk")

                # Assemble output
                output = dict(title=title,
                              rmvtitle=rmvtitle,
                              rmvform=rmvform,
                              addtitle=addtitle,
                              help_txt=help_txt,
                              addform=addform,
                              list_btn=list_btn,
                              edit_btn=edit_btn,
                              add_btn=add_btn)
                current.response.view = "admin/membership_manage.html"
            else:
                r.error(501, manager.BAD_FORMAT)
        else:
            r.error(404, self.resource.ERROR.BAD_RECORD)

        return output

    # -------------------------------------------------------------------------
    def _entity_select(self):
        """ Get a SELECT of person entities for realm assignment """

        T = current.T
        s3db = current.s3db

        select = SELECT(
                    OPTGROUP(
                        OPTION(T("Default Realm"), _value="__NONE__", _selected="selected"),
                        OPTION(T("All Entities"), _value=0),
                        _label=T("Multiple")),
                    _name="pe_id")

        table = s3db.table("pr_pentity")
        if table is None:
            return select
        instance_type_nice = table.instance_type.represent

        types = ("org_organisation", "org_office", "inv_warehouse", "pr_group")
        entities = s3db.pr_get_entities(types=types, group=True)

        for instance_type in types:
            if instance_type in entities:
                optgroup = OPTGROUP(_label=instance_type_nice(instance_type))
                items = [(n, i) for i, n in entities[instance_type].items()]
                items.sort()
                for name, pe_id in items:
                    optgroup.append(OPTION(name, _value=pe_id))
                select.append(optgroup)

        return select

    # -------------------------------------------------------------------------
    def _entity_represent(self, entities):
        """
            Get a representation dict for a list of pe_ids

            @param entities: the pe_ids of the entities
        """
        T = current.T

        pe_ids = [e for e in entities if e is not None and e != 0]
        if pe_ids:
            representation = current.s3db.pr_get_entities(pe_ids=pe_ids)
        else:
            representation = Storage()
        representation[None] = T("Default Realm")
        representation[0] = T("All Entities")
        return representation

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

            @returns: SELECT object
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
                    "pr_group"]

    def __init__(self, *args, **kwargs):
        """ Constructor """

        super(S3EntityRoleManager, self).__init__(*args, **kwargs)

        # Set the default view
        current.response.view = "admin/manage_roles.html"

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
    def apply_method(self, r, **attr):
        """
        """

        if self.method == "roles" and \
           (r.tablename in self.ENTITY_TYPES + ["pr_person"]):
            context = self.get_context_data(r, **attr)
        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)
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

        # organisation or office entity
        self.entity = self.get_entity()

        # user account to assigned roles to
        self.user = self.get_user()

        # roles already assigned to a user or users
        self.assigned_roles = self.get_assigned_roles()

        # the foreign object is the one selected in the role form
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
                   "title": T("Roles")}

        if not self.foreign_object:
            # how many assigned roles to show per page
            pagination_size = int(r.get_vars.get("page_size", 4))
            # what page of assigned roles to view
            pagination_offset = int(r.get_vars.get("page_offset", 0))
            # the number of pages of assigned roles
            import math
            pagination_pages = int(math.ceil(len(self.assigned_roles) / float(pagination_size)))
            # the list of objects to show on this page sorted by name
            pagination_list = [(self.objects[id], id) for id in self.assigned_roles]
            pagination_list = sorted(pagination_list)[pagination_offset * pagination_size:pagination_offset * pagination_size + pagination_size]

            context.update({"assigned_roles": self.assigned_roles,
                            "pagination_size": pagination_size,
                            "pagination_offset": pagination_offset,
                            "pagination_list": pagination_list,
                            "pagination_pages": pagination_pages})

        return context

    # -------------------------------------------------------------------------
    def get_realm(self):
        """
            Returns the realm (list of pe_ids) that this user can manage
            or raises a permission error if the user is not logged in

            @todo: avoid multiple lookups in current.auth
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
            return realms[ADMIN]
        elif ORG_ADMIN in realms:
            return realms[ORG_ADMIN]
        else:
            # raise an error here - user is not permitted
            # to access the role matrix
            auth.permission.fail()

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
        requires = IS_NULL_OR(IS_IN_SET(self.acls.keys(),
                                        labels=self.acls.values()))
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
        retract_role = auth.s3_retract_role

        for role_uid in before:
            # If role_uid is not in after,
            # the access level has changed.
            if role_uid not in after:
                retract_role(user_id, role_uid, entity_id)

        for role_uid in after:
            # If the role_uid is not in before,
            # the access level has changed
            if role_uid != "None" and role_uid not in before:
                assign_role(user_id, role_uid, entity_id)

# =============================================================================
class S3OrgRoleManager(S3EntityRoleManager):

    def __init__(self, *args, **kwargs):
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

        entity = dict(id=int(self.request.record.pe_id))
        entity["name"] = current.s3db.pr_get_entities(pe_ids=[entity["id"]],
                                                      types=self.ENTITY_TYPES)[entity["id"]]
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
            user = dict(id=int(user), name=self.objects.get(int(user), None))
        return user

    # -------------------------------------------------------------------------
    def get_foreign_object(self):
        """
            We are on an entity so our target is a user account.

            @return: dictionary with ID and username/email of user account
        """
        return self.user

    # -------------------------------------------------------------------------
    def get_assigned_roles(self):
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
            realm_users = Storage([(k, v)
                                    for k, v in self.realm_users.items()
                                    if k not in assigned_roles])

            nonrealm_users = Storage([(k, v)
                                       for k, v in self.objects.items()
                                       if k not in assigned_roles and \
                                          k not in self.realm_users])

            options = [("", ""),
                       (T("Users in my Organisations"), realm_users),
                       (T("Other Users"), nonrealm_users)]

            object_field = Field("foreign_object",
                                 T("User"),
                                 requires=IS_IN_SET(self.objects),
                                 widget=lambda field, value:
                                     S3GroupedOptionsWidget.widget(field,
                                                                 value,
                                                                 options=options))
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
            entity = dict(id=int(entity),
                          name=self.objects.get(int(entity), None))
        return entity

    # -------------------------------------------------------------------------
    def get_user(self):
        """
            We are on a person account so we need to find the associated user
            account.

            @return: dictionary with ID and username/email of the user account
        """
        utable = current.auth.settings.table_user
        ptable = current.s3db.pr_person_user

        pe_id = int(self.request.record.pe_id)

        if current.auth.settings.username:
            username = utable.username
        else:
            username = utable.email

        query = (ptable.pe_id == pe_id) & \
                (ptable.user_id == utable.id)
        record = current.db(query).select(utable.id,
                                          username,
                                          limitby=(0, 1)).first()

        return dict(id=record.id,
                    name=record[username]) if record else None

    # -------------------------------------------------------------------------
    def get_foreign_object(self):
        """
            We are on a user/person so we want to target an entity (org/office)
        """
        return self.entity

    # -------------------------------------------------------------------------
    def get_assigned_roles(self):
        """
            @todo: description?

            @return: dictionary of assigned roles with entity pe_id as the keys
        """
        user_id = self.user["id"]
        return super(S3PersonRoleManager, self).get_assigned_roles(user_id=user_id)

    # -------------------------------------------------------------------------
    def get_form_fields(self):
        """
            Return a list of fields, including a field for selecting
            an organisation or office.

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

            object_field = Field("foreign_object",
                                 current.T("Entity"),
                                 requires=IS_IN_SET(self.objects),
                                 widget=lambda field, value:
                                     S3GroupedOptionsWidget.widget(field,
                                                                   value,
                                                                   options=filtered_options))
            fields.insert(0, object_field)

        return fields

# END =========================================================================
